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

def rotate_backups(original_filename, backup_dir, max_backups=5):
    """
    Keeps only the last N backups for a specific file.
    """
    try:
        backup_dir = Path(backup_dir)
        # Filter files that start with the original filename stem
        # Format is: {stem}_{ts}{suffix}.bak
        stem = Path(original_filename).stem
        suffix = Path(original_filename).suffix
        
        candidates = []
        for p in backup_dir.glob(f"*{suffix}.bak"):
            if p.name.startswith(stem + "_"):
                candidates.append(p)
        
        # Sort by modification time (Newest first)
        candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove old ones
        if len(candidates) > max_backups:
            for old_file in candidates[max_backups:]:
                try:
                    old_file.unlink()
                    print(f"Cleanup: Removed old backup {old_file.name}")
                except Exception as del_err:
                    print(f"Cleanup Error: {del_err}")
                    
    except Exception as e:
        print(f"Rotation Error: {e}")

def backup_excel_file(file_path):
    """
    Creates a timestamped backup of an Excel file.
    Returns the backup path if successful, None otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        return None
        
    # Store in Documents/4BrosManager/backups
    backup_dir = Path.home() / "Documents" / "4BrosManager" / "backups"
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Failed to create backup dir: {e}")
        return None
        
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Clean filename to avoid issues
    safe_name = f"{path.stem}_{ts}{path.suffix}.bak"
    backup_path = backup_dir / safe_name
    
    try:
        shutil.copy2(path, backup_path)
        
        # Trigger Rotation
        rotate_backups(path.name, backup_dir, max_backups=5)
        
        return str(backup_path)
    except Exception as e:
        print(f"Backup Error: {e}")
        return None