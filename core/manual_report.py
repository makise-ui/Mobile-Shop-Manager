import json
import datetime
import pandas as pd
from pathlib import Path
from .utils import SafeJsonWriter

class ManualReportSession:
    def __init__(self, config_manager):
        self.config_dir = config_manager.get_config_dir()
        self.session_file = self.config_dir / "manual_report_session.json"
        self.scanned_items = self._load()

    def _load(self):
        """Loads the list of scanned items from disk."""
        if not self.session_file.exists():
            return []
        try:
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Migration: Convert old list of strings to dicts
                    cleaned = []
                    for item in data:
                        if isinstance(item, str):
                            cleaned.append({
                                'unique_id': item,
                                'timestamp': '',
                                'model': 'Unknown',
                                'imei': ''
                            })
                        elif isinstance(item, dict):
                            cleaned.append(item)
                    return cleaned
                return []
        except Exception as e:
            print(f"Error loading manual session: {e}")
            return []

    def _make_serializable(self, data):
        """Recursively converts datetimes/Timestamps to strings."""
        if isinstance(data, dict):
            return {k: self._make_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._make_serializable(v) for v in data]
        elif isinstance(data, (datetime.datetime, datetime.date, pd.Timestamp)):
            return str(data)
        return data

    def save(self):
        """Saves the current list to disk."""
        serializable_items = self._make_serializable(self.scanned_items)
        SafeJsonWriter.write(self.session_file, serializable_items)

    def add_item(self, item_dict):
        """
        Adds an item to the session.
        item_dict must have 'unique_id'.
        """
        uid = item_dict.get('unique_id')
        
        # Check duplicate
        for existing in self.scanned_items:
            if existing.get('unique_id') == uid:
                return False

        # Add timestamp if missing
        if 'timestamp' not in item_dict:
            item_dict['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        self.scanned_items.append(item_dict)
        self.save()
        return True

    def remove_id(self, unique_id):
        """Removes an item by ID."""
        original_len = len(self.scanned_items)
        self.scanned_items = [i for i in self.scanned_items if str(i.get('unique_id')) != str(unique_id)]
        if len(self.scanned_items) < original_len:
            self.save()
            return True
        return False

    def clear(self):
        """Clears the session."""
        self.scanned_items = []
        self.save()

    def get_items(self):
        """Returns the list of scanned item dicts."""
        return self.scanned_items
        
    def get_ids(self):
        """Returns just the IDs (for compatibility)."""
        return [i.get('unique_id') for i in self.scanned_items]
