import json
import os
from pathlib import Path

# Determine App Data Directory (Documents/4BrosManager/config)
# This is safer than the executable folder
APP_DIR = Path.home() / "Documents" / "4BrosManager"
CONFIG_DIR = APP_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = CONFIG_DIR / "config.json"
MAPPINGS_FILE = CONFIG_DIR / "file_mappings.json"

DEFAULT_CONFIG = {
    "label_width_mm": 50,
    "label_height_mm": 22,
    "printer_type": "windows",  # or 'escpos'
    "gst_default_percent": 18.0,
    "price_markup_percent": 0.0,
    "store_name": "4bros Mobile Point",
    "store_address": "123 Mobile Street, India",
    "store_gstin": "",
    "output_folder": str(APP_DIR),
    "auto_unique_id_prefix": "4BM"
}

class ConfigManager:
    def __init__(self):
        self.config_path = CONFIG_FILE
        self.mappings_path = MAPPINGS_FILE
        self.config = self.load_config()
        self.mappings = self.load_mappings()

    def load_config(self):
        if not self.config_path.exists():
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except:
            return DEFAULT_CONFIG

    def save_config(self, config=None):
        if config:
            self.config = config
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def load_mappings(self):
        if not self.mappings_path.exists():
            return {}
        try:
            with open(self.mappings_path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_mappings(self, mappings=None):
        if mappings:
            self.mappings = mappings
        with open(self.mappings_path, 'w') as f:
            json.dump(self.mappings, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def get_file_mapping(self, file_path):
        return self.mappings.get(str(file_path))

    def set_file_mapping(self, file_path, mapping_data):
        self.mappings[str(file_path)] = mapping_data
        self.save_mappings()

    def remove_file_mapping(self, file_path):
        if str(file_path) in self.mappings:
            del self.mappings[str(file_path)]
            self.save_mappings()
