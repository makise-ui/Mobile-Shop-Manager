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

    def _save_registry(self):
        SafeJsonWriter.write(self.file_path, self.registry)

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
