import requests
import threading
import sys
import os
import subprocess
from packaging import version
from .version import APP_VERSION, REPO_OWNER, REPO_NAME

class UpdateChecker:
    def __init__(self):
        self.current_version = APP_VERSION
        self.latest_version = None
        self.release_notes = ""
        self.asset_url = None
        
    def check_for_updates(self, callback):
        """
        callback(is_available, version_tag, release_notes)
        """
        def _check():
            try:
                url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    tag_name = data.get('tag_name', '0.0.0')
                    body = data.get('body', 'No details provided.')
                    
                    clean_tag = tag_name.lstrip('v')
                    clean_current = self.current_version.lstrip('v')
                    
                    if version.parse(clean_tag) > version.parse(clean_current):
                        self.latest_version = tag_name
                        self.release_notes = body
                        
                        # Find .exe asset
                        for asset in data.get('assets', []):
                            if asset['name'].endswith('.exe'):
                                self.asset_url = asset['browser_download_url']
                                break
                        
                        callback(True, tag_name, body)
                    else:
                        callback(False, None, None)
                else:
                    callback(False, None, None)
            except Exception as e:
                print(f"Update check failed: {e}")
                callback(False, None, None)
                
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()

    def download_update(self, progress_callback, complete_callback):
        if not self.asset_url: return
        
        def _download():
            try:
                response = requests.get(self.asset_url, stream=True)
                total_length = int(response.headers.get('content-length', 0))
                
                downloaded = 0
                temp_name = "update_pkg.tmp"
                
                with open(temp_name, "wb") as f:
                    for chunk in response.iter_content(chunk_size=4096):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_length > 0:
                                percent = int((downloaded / total_length) * 100)
                                progress_callback(percent)
                
                complete_callback(temp_name)
            except Exception as e:
                print(f"Download failed: {e}")
                
        thread = threading.Thread(target=_download, daemon=True)
        thread.start()

    def restart_and_install(self, new_file_path):
        # Logic for Frozen (PyInstaller) app
        if not getattr(sys, 'frozen', False):
            print("Not running as frozen exe. Update downloaded but swap skipped.")
            return

        exe_name = os.path.basename(sys.executable)
        
        batch_script = f"""
@echo off
timeout /t 2 /nobreak > NUL
del "{exe_name}"
move "{new_file_path}" "{exe_name}"
start "" "{exe_name}"
del "%~f0"
"""
        with open("updater.bat", "w") as f:
            f.write(batch_script)
            
        subprocess.Popen("updater.bat", shell=True)
        sys.exit()