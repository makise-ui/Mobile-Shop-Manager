import json
import os
from pathlib import Path

# Use same config dir
APP_DIR = Path.home() / "Documents" / "4BrosManager"
CONFIG_DIR = APP_DIR / "config"
COLOR_FILE = CONFIG_DIR / "colors.json"

DEFAULT_COLORS = ["Black", "White", "Blue", "Red", "Green", "Gold", "Silver", "Grey", "Purple"]

class ColorRegistry:
    def __init__(self):
        self.colors = self._load()

    def _load(self):
        if not COLOR_FILE.exists():
            return sorted(DEFAULT_COLORS)
        try:
            with open(COLOR_FILE, 'r') as f:
                data = json.load(f)
                return sorted(data)
        except:
            return sorted(DEFAULT_COLORS)

    def save(self):
        with open(COLOR_FILE, 'w') as f:
            json.dump(self.colors, f, indent=4)

    def add_color(self, color):
        if color not in self.colors:
            self.colors.append(color)
            self.colors.sort()
            self.save()

    def remove_color(self, color):
        if color in self.colors:
            self.colors.remove(color)
            self.save()
            
    def get_all(self):
        return self.colors
