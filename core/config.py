import json
import os
from pathlib import Path
from .utils import SafeJsonWriter

# Determine App Data Directory
# We use a clean version of the default app name: MobileShopManager
# Migration: If old '4BrosManager' exists, rename it to ensure no data loss.
DOCS_DIR = Path.home() / "Documents"
OLD_APP_DIR = DOCS_DIR / "4BrosManager"
APP_DIR = DOCS_DIR / "MobileShopManager"

if not APP_DIR.exists() and OLD_APP_DIR.exists():
    try:
        OLD_APP_DIR.rename(APP_DIR)
        print(f"✓ Configuration migrated from {OLD_APP_DIR} to {APP_DIR}")
    except Exception as e:
        # Log migration failure but continue
        print(f"⚠️  WARNING: Configuration migration failed: {e}")
        print(f"   Falling back to old directory: {OLD_APP_DIR}")
        # Fallback to old dir if rename fails
        APP_DIR = OLD_APP_DIR

CONFIG_DIR = APP_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = CONFIG_DIR / "config.json"
MAPPINGS_FILE = CONFIG_DIR / "file_mappings.json"
ID_REGISTRY_FILE = CONFIG_DIR / "id_registry.json"

DEFAULT_CONFIG = {
    "label_width_mm": 50,
    "label_height_mm": 22,
    "printer_type": "windows",  # or 'escpos'
    "gst_default_percent": 18.0,
    "price_markup_percent": 0.0,
    "enable_buyer_tracking": True,
    "store_name": "My Mobile Shop",
    "app_display_name": "Mobile Shop Manager",
    "store_address": "123 Mobile Street, India",
    "store_gstin": "",
    "store_contact": "",
    "invoice_terms": "Goods once sold will not be taken back.",
    "output_folder": str(APP_DIR),
    "auto_unique_id_prefix": "MSM",
    "theme_name": "cosmo",    # Default Theme
    "theme_color": "#007acc", # Added customization
    "font_size_ui": 10        # Added customization
}

class ConfigManager:
    def __init__(self):
        self.config_path = CONFIG_FILE
        self.mappings_path = MAPPINGS_FILE
        self.config = self.load_config()
        self.mappings = self.load_mappings()

    def get_invoices_dir(self):
        d = APP_DIR / "Invoices"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_config_dir(self):
        return CONFIG_DIR

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
        SafeJsonWriter.write(self.config_path, self.config)

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
        SafeJsonWriter.write(self.mappings_path, self.mappings)

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
