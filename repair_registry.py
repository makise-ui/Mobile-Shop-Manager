import json
import os
from pathlib import Path

# Path to the new config location
CONFIG_DIR = Path.home() / "Documents" / "MobileShopManager" / "config"
REGISTRY_FILE = CONFIG_DIR / "id_registry.json"

def repair():
    if not REGISTRY_FILE.exists():
        print(f"File not found: {REGISTRY_FILE}")
        # Try legacy path just in case
        OLD_DIR = Path.home() / "Documents" / "4BrosManager" / "config"
        REGISTRY_FILE_OLD = OLD_DIR / "id_registry.json"
        if REGISTRY_FILE_OLD.exists():
            print(f"Found in legacy path: {REGISTRY_FILE_OLD}")
            repair_file(REGISTRY_FILE_OLD)
        else:
            print("No registry found to repair.")
        return

    repair_file(REGISTRY_FILE)

def repair_file(path):
    print(f"Scanning {path}...")
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load JSON: {e}")
        return

    metadata = data.get('metadata', {})
    fixed_count = 0
    
    for uid, meta in metadata.items():
        # Check for Self-Merge
        if meta.get('is_hidden') and str(meta.get('merged_into')) == str(uid):
            print(f"Fixing Self-Merged ID: {uid}")
            
            # Un-hide
            meta['is_hidden'] = False
            
            # Remove merge fields
            if 'merged_into' in meta: del meta['merged_into']
            if 'merge_reason' in meta: del meta['merge_reason']
            
            # Log the repair
            if 'history' not in meta: meta['history'] = []
            meta['history'].append({
                "ts": "2026-01-09 00:00:00",
                "action": "REPAIR",
                "details": "Fixed Self-Merge Loop"
            })
            
            fixed_count += 1

    if fixed_count > 0:
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"SUCCESS: Repaired {fixed_count} items. Please restart the app.")
    else:
        print("Scan complete. No issues found.")

if __name__ == "__main__":
    repair()
