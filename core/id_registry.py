import json
import os
import hashlib
import threading
from pathlib import Path
from .utils import SafeJsonWriter
from .config import CONFIG_DIR

ID_REGISTRY_FILE = CONFIG_DIR / "id_registry.json"

# IMEIs that are clearly placeholder text, not real identifiers.
# All comparisons are done case-insensitively.
PLACEHOLDER_IMEIS = {
    "not on", "n/a", "na", "none", "nil", "unknown", "no imei",
    "noimei", "no", "test", "temp", "dummy", "missing",
    "not available", "not applicable", "-", "--", "---",
}

class IDRegistry:
    def __init__(self):
        self.file_path = ID_REGISTRY_FILE
        self._lock = threading.Lock()
        self.registry = self._load_registry()
        self.auto_save = True
        self._migrate_duplicate_keys()  # Auto-fix old duplicates on startup

    def _load_registry(self):
        if not self.file_path.exists():
            return {"next_id": 1, "items": {}, "metadata": {}}
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                if "next_id" not in data: data["next_id"] = 1
                if "items" not in data: data["items"] = {}
                if "metadata" not in data: data["metadata"] = {}
                return data
        except:
            return {"next_id": 1, "items": {}, "metadata": {}}

    def commit(self):
        """Manually save the registry to disk."""
        with self._lock:
            SafeJsonWriter.write(self.file_path, self.registry)

    def _save_registry(self):
        if self.auto_save:
            # NOTE: caller must NOT hold _lock here, or use _save_registry_unlocked
            self.commit()

    def _save_registry_unlocked(self):
        """Save without acquiring the lock (caller must hold it)."""
        if self.auto_save:
            SafeJsonWriter.write(self.file_path, self.registry)

    def get_ids_batch(self, keys):
        """
        Returns a list of IDs for a list of keys, creating new ones if necessary.
        """
        with self._lock:
            ids = []
            for key in keys:
                if key in self.registry['items']:
                    ids.append(self.registry['items'][key])
                else:
                    new_id = self.registry['next_id']
                    self.registry['next_id'] += 1
                    self.registry['items'][key] = new_id
                    ids.append(new_id)
            
            self._save_registry_unlocked()
            return ids

    @staticmethod
    def _is_valid_imei(imei_str):
        """Check if the string looks like a real numeric IMEI (14-16 digits)."""
        digits_only = imei_str.replace(' ', '').replace('-', '')
        return digits_only.isdigit() and 14 <= len(digits_only) <= 16

    def _make_key(self, row_data):
        """Build the registry key for an item row."""
        imei = str(row_data.get('imei', '')).strip()
        model = str(row_data.get('model', '')).strip()
        ram_rom = str(row_data.get('ram_rom', '')).strip()
        supplier = str(row_data.get('supplier', '')).strip()

        # Case 1: Valid numeric IMEI → direct key (stable across sessions)
        if imei and self._is_valid_imei(imei):
            return f"IMEI:{imei}", False

        # Case 2: Text-based IMEI that isn't a known placeholder
        #         Hash it WITH model info so different phones stay unique
        if imei and imei.lower() not in PLACEHOLDER_IMEIS and len(imei) > 2:
            raw_str = f"{imei}|{model}|{ram_rom}|{supplier}"
            return f"TEXT_IMEI:{hashlib.md5(raw_str.encode()).hexdigest()}", False

        # Case 3: Placeholder or missing IMEI
        # Include ALL available fields to minimize collisions
        color = str(row_data.get('color', '')).strip()
        price = str(row_data.get('price', '')).strip()
        price_orig = str(row_data.get('price_original', '')).strip()
        grade = str(row_data.get('grade', '')).strip()
        condition = str(row_data.get('condition', '')).strip()
        notes = str(row_data.get('notes', '')).strip()

        raw_str = f"{model}|{ram_rom}|{supplier}|{color}|{price}|{price_orig}|{grade}|{condition}|{notes}"
        base_key = f"HASH:{hashlib.md5(raw_str.encode()).hexdigest()}"
        # Return True to signal this key needs collision handling
        return base_key, True

    def get_or_create_id(self, row_data):
        """
        Returns a stable integer ID for the given row.
        If the item has no IMEI and all fields match an existing item,
        a unique counter suffix is appended to prevent collisions.
        """
        base_key, needs_collision_check = self._make_key(row_data)

        with self._lock:
            if not needs_collision_check:
                # Direct or text-IMEI key — no collision possible
                if base_key in self.registry['items']:
                    return self.registry['items'][base_key]
                new_id = self.registry['next_id']
                self.registry['next_id'] += 1
                self.registry['items'][base_key] = new_id
                self._save_registry_unlocked()
                return new_id

            # For placeholder-IMEI items: find a free slot
            # Check base_key first, then base_key#2, base_key#3, etc.
            if not hasattr(self, '_claimed_keys'):
                self._claimed_keys = set()

            key = base_key
            if key not in self.registry['items']:
                # First item with this hash — use it directly
                new_id = self.registry['next_id']
                self.registry['next_id'] += 1
                self.registry['items'][key] = new_id
                self._claimed_keys.add(key)  # Mark as claimed
                self._save_registry_unlocked()
                return new_id

            # Key exists: check if this is the SAME item being reloaded
            # (we track which keys were claimed this load cycle)
            if key not in self._claimed_keys:
                # First time seeing this key in current load → it's the same item
                self._claimed_keys.add(key)
                return self.registry['items'][key]

            # Collision! Find the next free numbered slot
            counter = 2
            while True:
                numbered_key = f"{base_key}#{counter}"
                if numbered_key not in self.registry['items']:
                    new_id = self.registry['next_id']
                    self.registry['next_id'] += 1
                    self.registry['items'][numbered_key] = new_id
                    self._claimed_keys.add(numbered_key)
                    self._save_registry_unlocked()
                    return new_id
                if numbered_key not in self._claimed_keys:
                    self._claimed_keys.add(numbered_key)
                    return self.registry['items'][numbered_key]
                counter += 1

    def reset_load_cycle(self):
        """Call at the start of reload_all() to reset collision tracking."""
        self._claimed_keys = set()

    def _migrate_duplicate_keys(self):
        """
        Auto-fix: detect old-style IMEI keys that used placeholder text
        (e.g. 'IMEI:NOT ON') and re-key them so each gets a unique ID.
        Runs once on startup; skips if nothing to fix.
        """
        with self._lock:
            items = self.registry['items']
            keys_to_fix = []

            for key in list(items.keys()):
                if not key.startswith('IMEI:'):
                    continue
                imei_part = key[5:]  # strip 'IMEI:' prefix
                if not self._is_valid_imei(imei_part):
                    # This is a text-based IMEI stored with the old format
                    keys_to_fix.append(key)

            if not keys_to_fix:
                return  # Nothing to migrate

            for key in keys_to_fix:
                old_id = items.pop(key)
                # We can't recover model info for old keys, so give them
                # a unique migrated key that won't collide again.
                migrated_key = f"MIGRATED:{old_id}:{key}"
                items[migrated_key] = old_id

            self._save_registry_unlocked()
            print(f"[IDRegistry] Auto-migrated {len(keys_to_fix)} placeholder IMEI key(s).")

    def set_date_added_if_empty(self, item_id, date_str):
        """Sets 'added_date' in metadata only if not already present."""
        with self._lock:
            iid_str = str(item_id)
            if iid_str not in self.registry['metadata']:
                self.registry['metadata'][iid_str] = {}
            
            if 'added_date' not in self.registry['metadata'][iid_str]:
                self.registry['metadata'][iid_str]['added_date'] = date_str
                self._save_registry_unlocked()

    def update_metadata(self, item_id, data):
        """Stores app-level changes (status, notes) for an ID."""
        with self._lock:
            iid_str = str(item_id)
            if iid_str not in self.registry['metadata']:
                self.registry['metadata'][iid_str] = {}
            self.registry['metadata'][iid_str].update(data)
            self._save_registry_unlocked()

    def add_history_log(self, item_id, action, details):
        """Adds a timestamped history entry for an item."""
        import datetime
        with self._lock:
            iid_str = str(item_id)
            if iid_str not in self.registry['metadata']:
                self.registry['metadata'][iid_str] = {}
            
            if 'history' not in self.registry['metadata'][iid_str]:
                self.registry['metadata'][iid_str]['history'] = []
            
            entry = {
                "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action": action,
                "details": details
            }
            self.registry['metadata'][iid_str]['history'].append(entry)
            self._save_registry_unlocked()

    def get_metadata(self, item_id):
        with self._lock:
            return self.registry['metadata'].get(str(item_id), {}).copy()

    def get_all_buyers(self):
        """
        Scans all item metadata to find unique buyers.
        Returns a dict: { 'Buyer Name': 'Contact Number', ... }
        """
        buyers = {}
        meta = self.registry.get('metadata', {})
        
        for iid, data in meta.items():
            # Check current status/buyer info
            b_name = data.get('buyer', '').strip()
            b_contact = data.get('buyer_contact', '').strip()
            
            if b_name:
                # Store/Update contact (preferring non-empty)
                if b_name not in buyers or (b_contact and not buyers[b_name]):
                    buyers[b_name] = b_contact
                    
        return buyers
