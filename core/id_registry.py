import json
import os
import hashlib
from pathlib import Path
from .utils import SafeJsonWriter
from .config import CONFIG_DIR

ID_REGISTRY_FILE = CONFIG_DIR / "id_registry.json"

class IDRegistry:
    def __init__(self):
        self.file_path = ID_REGISTRY_FILE
        self.registry = self._load_registry()
        self.auto_save = True # Default behavior
        # registry structure:
        # {
        #   "next_id": 1,
        #   "items": {
        #       "hash_key": 1,
        #       "hash_key_2": 2
        #   }
        # }

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
        SafeJsonWriter.write(self.file_path, self.registry)

    def _save_registry(self):
        if self.auto_save:
            self.commit()

    def get_ids_batch(self, keys):
        """
        Returns a list of IDs for a list of keys, creating new ones if necessary.
        """
        ids = []
        for key in keys:
            if key in self.registry['items']:
                ids.append(self.registry['items'][key])
            else:
                new_id = self.registry['next_id']
                self.registry['next_id'] += 1
                self.registry['items'][key] = new_id
                ids.append(new_id)
        
        if self.auto_save:
            self.commit()
        return ids

    def get_or_create_id(self, row_data):
        """
        Returns a stable integer ID for the given row.
        """
        imei = str(row_data.get('imei', '')).strip()
        model = str(row_data.get('model', '')).strip()
        ram_rom = str(row_data.get('ram_rom', '')).strip()
        
        if imei and len(imei) > 4:
            key = f"IMEI:{imei}"
        else:
            raw_str = f"{model}|{ram_rom}|{row_data.get('supplier','')}"
            key = f"HASH:{hashlib.md5(raw_str.encode()).hexdigest()}"

        if key in self.registry['items']:
            return self.registry['items'][key]

        new_id = self.registry['next_id']
        self.registry['next_id'] += 1
        self.registry['items'][key] = new_id
        self._save_registry()
        
        return new_id

    def set_date_added_if_empty(self, item_id, date_str):
        """Sets 'added_date' in metadata only if not already present."""
        iid_str = str(item_id)
        if iid_str not in self.registry['metadata']:
            self.registry['metadata'][iid_str] = {}
            
        if 'added_date' not in self.registry['metadata'][iid_str]:
            self.registry['metadata'][iid_str]['added_date'] = date_str
            self._save_registry()

    def update_metadata(self, item_id, data):
        """Stores app-level changes (status, notes) for an ID."""
        iid_str = str(item_id)
        if iid_str not in self.registry['metadata']:
            self.registry['metadata'][iid_str] = {}
        self.registry['metadata'][iid_str].update(data)
        self._save_registry()

    def add_history_log(self, item_id, action, details):
        """Adds a timestamped history entry for an item."""
        import datetime
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
        self._save_registry()

    def get_metadata(self, item_id):
        return self.registry['metadata'].get(str(item_id), {})

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
