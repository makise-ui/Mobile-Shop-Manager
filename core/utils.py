import json
import os
import shutil
import datetime
from pathlib import Path

class SafeJsonWriter:
    @staticmethod
    def write(file_path, data):
        """
        Writes JSON data to a file atomically.
        1. Write to .tmp file
        2. Rename .tmp to actual file
        """
        path = Path(file_path)
        tmp_path = path.with_suffix('.tmp')
        
        try:
            with open(tmp_path, 'w') as f:
                json.dump(data, f, indent=4)
                f.flush()
                os.fsync(f.fileno()) # Ensure write to disk
                
            # Atomic rename (on POSIX) or Replace (Windows)
            if tmp_path.exists():
                tmp_path.replace(path)
            return True
        except Exception as e:
            print(f"SafeWrite Error: {e}")
            if tmp_path.exists():
                try:
                    os.remove(tmp_path)
                except:
                    pass
            return False

def backup_excel_file(file_path):
    """
    Creates a timestamped backup of an Excel file.
    Returns the backup path if successful, None otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        return None
        
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.parent / f"{path.stem}_{ts}.bak{path.suffix}"
    
    try:
        shutil.copy2(path, backup_path)
        return str(backup_path)
    except Exception as e:
        print(f"Backup Error: {e}")
        return None
