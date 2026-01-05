import json
import datetime
from pathlib import Path

class ActivityLogger:
    def __init__(self, config_manager):
        self.config = config_manager
        # Log file in Documents/4BrosManager/logs/activity.json
        # Handle case where output_folder might be string
        out = self.config.get('output_folder')
        if isinstance(out, str):
            out = Path(out)
            
        self.log_dir = out / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "activity.json"
        
    def log(self, action, details=""):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "details": str(details)
        }
        
        logs = self._read_logs()
        logs.insert(0, entry) # Prepend
        # Limit to 1000
        logs = logs[:1000]
        
        try:
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"Log error: {e}")
            
    def get_logs(self, limit=100):
        return self._read_logs()[:limit]
        
    def _read_logs(self):
        if not self.log_file.exists():
            return []
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except:
            return []
            
    def clear(self):
        try:
            with open(self.log_file, 'w') as f:
                json.dump([], f)
        except:
            pass
