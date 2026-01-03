import json
import os
from pathlib import Path
from .utils import SafeJsonWriter

# Use same config dir
APP_DIR = Path.home() / "Documents" / "4BrosManager"
CONFIG_DIR = APP_DIR / "config"
DATA_FILE = CONFIG_DIR / "app_data.json"

DEFAULT_COLORS = ["Black", "White", "Blue", "Red", "Green", "Gold", "Silver", "Grey", "Purple"]
DEFAULT_BUYERS = ["Walk-in Customer", "Dealer A", "Dealer B"]

class DataRegistry:
    def __init__(self):
        self.data = self._load()
        # Ensure structure
        if "colors" not in self.data: self.data["colors"] = sorted(DEFAULT_COLORS)
        if "buyers" not in self.data: self.data["buyers"] = sorted(DEFAULT_BUYERS)

    def _load(self):
        # Migration: Check if old colors.json exists
        old_color_file = CONFIG_DIR / "colors.json"
        
        if not DATA_FILE.exists():
            # Try to migrate old colors
            initial_colors = sorted(DEFAULT_COLORS)
            if old_color_file.exists():
                try:
                    with open(old_color_file, 'r') as f:
                        initial_colors = sorted(json.load(f))
                except:
                    pass
            
            return {"colors": initial_colors, "buyers": sorted(DEFAULT_BUYERS)}
            
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"colors": sorted(DEFAULT_COLORS), "buyers": sorted(DEFAULT_BUYERS)}

    def save(self):
        SafeJsonWriter.write(DATA_FILE, self.data)

    # --- Colors ---
    def add_color(self, color):
        if color not in self.data["colors"]:
            self.data["colors"].append(color)
            self.data["colors"].sort()
            self.save()

    def remove_color(self, color):
        if color in self.data["colors"]:
            self.data["colors"].remove(color)
            self.save()
            
    def get_colors(self):
        return self.data["colors"]

    # --- Buyers ---
    def add_buyer(self, buyer):
        if buyer not in self.data["buyers"]:
            self.data["buyers"].append(buyer)
            self.data["buyers"].sort()
            self.save()

    def remove_buyer(self, buyer):
        if buyer in self.data["buyers"]:
            self.data["buyers"].remove(buyer)
            self.save()
            
    def get_buyers(self):
        return self.data["buyers"]
