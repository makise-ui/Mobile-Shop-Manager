import shutil
import datetime
import os
import sqlite3
import pandas as pd
import json
import zipfile
from pathlib import Path
from .config import APP_DIR, CONFIG_DIR
from .database import DB_FILE

class BackupManager:
    def __init__(self):
        self.backup_dir = APP_DIR / "Backups"
        self.backup_dir.mkdir(exist_ok=True)

    def create_full_system_backup(self, target_path=None):
        """
        Creates a ZIP of the entire APP_DIR (excluding backups and temp files).
        Useful for migrating to another PC.
        """
        if not target_path:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            target_path = self.backup_dir / f"MSM_Backup_{ts}.zip"
        
        try:
            with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(APP_DIR):
                    # Filter directories
                    dirs[:] = [d for d in dirs if d not in ["Backups", "__pycache__", "temp"]]
                        
                    for file in files:
                        if file.endswith(('.lock', '.log', '.tmp')): continue
                        if "journal" in file: continue
                        
                        file_path = Path(root) / file
                        # Don't zip the target file itself if it's somehow inside
                        if file_path == Path(target_path): continue
                        
                        arcname = file_path.relative_to(APP_DIR)
                        zipf.write(file_path, arcname)
            return True, str(target_path)
        except Exception as e:
            return False, str(e)

    def export_data_to_excel(self, output_path):
        """Exports DB items and history to a multi-sheet Excel file."""
        try:
            conn = sqlite3.connect(DB_FILE)
            
            # 1. Fetch Items
            df = pd.read_sql_query("SELECT * FROM items", conn)
            
            # Process Metadata JSON into columns
            meta_rows = []
            for idx, row in df.iterrows():
                d = row.to_dict()
                if d.get('metadata'):
                    try:
                        meta = json.loads(d['metadata'])
                        # Prefix meta keys if collision? No, merge is usually intended.
                        d.update(meta)
                    except: pass
                # Remove blob
                del d['metadata']
                meta_rows.append(d)
                
            df_export = pd.DataFrame(meta_rows)
            
            # 2. Fetch History
            df_hist = pd.read_sql_query("SELECT * FROM history", conn)
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df_export.to_excel(writer, sheet_name='Inventory_Master', index=False)
                df_hist.to_excel(writer, sheet_name='History_Logs', index=False)
                
            conn.close()
            return True, output_path
        except Exception as e:
            return False, str(e)

    def restore_from_zip(self, zip_path):
        """
        Restores APP_DIR from a zip. 
        WARNING: Overwrites everything.
        """
        try:
            # 1. Verify Zip
            if not zipfile.is_zipfile(zip_path):
                return False, "Invalid Zip File"

            # 2. Extract
            # We extract to a temp folder first to verify?
            # Or just overwrite?
            # Overwriting 'in-place' while app is running is risky for open files (like DB).
            # But we can try.
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(APP_DIR)
                
            return True, "Restore Successful. Please restart the application immediately."
        except Exception as e:
            return False, f"Restore Failed: {e}"
