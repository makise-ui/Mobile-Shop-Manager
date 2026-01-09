import json
import os
from pathlib import Path
from .utils import SafeJsonWriter
from .config import CONFIG_DIR

DATA_FILE = CONFIG_DIR / "app_data.json"

DEFAULT_COLORS = ["Black", "White", "Blue", "Red", "Green", "Gold", "Silver", "Grey", "Purple"]
DEFAULT_BUYERS = ["Walk-in Customer", "Dealer A", "Dealer B"]
DEFAULT_GRADES = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "D", "E"]

class DataRegistry:
    def __init__(self):
        self.data = self._load()
        # Ensure structure
        if "colors" not in self.data: self.data["colors"] = sorted(DEFAULT_COLORS)
        if "buyers" not in self.data: self.data["buyers"] = sorted(DEFAULT_BUYERS)
        if "grades" not in self.data: self.data["grades"] = list(DEFAULT_GRADES)

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
            
            return {
                "colors": initial_colors, 
                "buyers": sorted(DEFAULT_BUYERS),
                "grades": list(DEFAULT_GRADES)
            }
            
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {
                "colors": sorted(DEFAULT_COLORS), 
                "buyers": sorted(DEFAULT_BUYERS),
                "grades": list(DEFAULT_GRADES)
            }

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

    # --- Grades ---
    def add_grade(self, grade):
        if grade not in self.data.get("grades", []):
            self.data.setdefault("grades", []).append(grade)
            self.save()

    def remove_grade(self, grade):
        if grade in self.data.get("grades", []):
            self.data["grades"].remove(grade)
            self.save()
            
    def get_grades(self):
        return self.data.get("grades", DEFAULT_GRADES)
