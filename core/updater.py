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
                    body = data.get('body') or 'No details provided.'
                    
                    clean_tag = tag_name.lstrip('v')
                    clean_current = self.current_version.lstrip('v')
                    
                    if version.parse(clean_tag) > version.parse(clean_current):
                        self.latest_version = tag_name
                        self.release_notes = body
                        
                        # Detect variant (Free vs Licensed)
                        is_free = False
                        if hasattr(sys, '_MEIPASS'):
                            is_free = os.path.exists(os.path.join(sys._MEIPASS, "no_license.flag"))
                        
                        target_keyword = "Free" if is_free else "Licensed"
                        self.asset_url = None
                        
                        # 1. Try Exact Match
                        for asset in data.get('assets', []):
                            if asset['name'].endswith('.exe') and target_keyword in asset['name']:
                                self.asset_url = asset['browser_download_url']
                                break
                        
                        # 2. Fallback (Any .exe if exact match fails)
                        if not self.asset_url:
                            for asset in data.get('assets', []):
                                if asset['name'].endswith('.exe'):
                                    self.asset_url = asset['browser_download_url']
                                    break
                        
                        if self.asset_url:
                            callback(True, tag_name, body)
                        else:
                            callback(False, None, None)
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
                import tempfile
                import hashlib
                
                response = requests.get(self.asset_url, stream=True)
                total_length = int(response.headers.get('content-length', 0))
                
                downloaded = 0
                # Bug #9 fix: Download to a secure temp directory instead of CWD
                temp_dir = tempfile.mkdtemp(prefix="msm_update_")
                temp_path = os.path.join(temp_dir, "update_pkg.tmp")
                
                sha256_hash = hashlib.sha256()
                with open(temp_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=4096):
                        if chunk:
                            f.write(chunk)
                            sha256_hash.update(chunk)
                            downloaded += len(chunk)
                            if total_length > 0:
                                percent = int((downloaded / total_length) * 100)
                                progress_callback(percent)
                
                # Bug #8 fix: Verify SHA256 hash if available in release notes
                computed_hash = sha256_hash.hexdigest()
                if self.release_notes and 'sha256:' in self.release_notes.lower():
                    import re
                    hash_match = re.search(r'sha256:\s*([a-fA-F0-9]{64})', self.release_notes, re.IGNORECASE)
                    if hash_match:
                        expected_hash = hash_match.group(1).lower()
                        if computed_hash != expected_hash:
                            print(f"SECURITY WARNING: SHA256 mismatch! Expected {expected_hash}, got {computed_hash}")
                            os.remove(temp_path)
                            return
                        else:
                            print(f"SHA256 verification passed: {computed_hash}")
                    else:
                        print(f"WARNING: Could not parse SHA256 from release notes. Downloaded file hash: {computed_hash}")
                else:
                    print(f"WARNING: No SHA256 hash in release notes. Downloaded file hash: {computed_hash}")
                
                complete_callback(temp_path)
            except Exception as e:
                print(f"Download failed: {e}")
                
        thread = threading.Thread(target=_download, daemon=True)
        thread.start()

    def restart_and_install(self, new_file_path):
        # Logic for Frozen (PyInstaller) app
        if not getattr(sys, 'frozen', False):
            return False, "Cannot update: App is running from source (Python script)."

        import tempfile
        
        exe_path = sys.executable
        exe_dir = os.path.dirname(exe_path)
        exe_name = os.path.basename(exe_path)
        pid = os.getpid()
        
        # Resolve absolute path for the new file (it's likely in CWD or temp)
        new_file_abs = os.path.abspath(new_file_path)
        
        # Write bat file to System Temp to avoid locking issues in _MEI or App Dir
        bat_path = os.path.join(tempfile.gettempdir(), f"msm_update_{pid}.bat")
        
        # Robust Batch Script
        # 1. Wait for PID to vanish
        # 2. Delete old exe
        # 3. Move new exe
        # 4. Relaunch
        batch_script = f"""
@echo off
set "PYTHONPATH="
set "PYTHONHOME="
:loop
tasklist | findstr /R "\\<{pid}\\>" >nul
if %errorlevel% == 0 (
    timeout /t 1 /nobreak >nul
    goto loop
)

REM Process {pid} is gone. Wait 1s for file locks.
timeout /t 1 /nobreak >nul

cd /d "{exe_dir}"
if exist "{exe_name}" del "{exe_name}"

if exist "{exe_name}" (
    REM Delete failed? Wait and try again
    timeout /t 2 /nobreak >nul
    del "{exe_name}"
)

move /Y "{new_file_abs}" "{exe_name}"
start "" "{exe_name}"

REM Cleanup self
(goto) 2>nul & del "%~f0"
"""
        try:
            with open(bat_path, "w") as f:
                f.write(batch_script)
                
            # Sanitize Environment
            # PyInstaller sets _MEIPASS. If we inherit it, the new process might try 
            # to use the old (deleted) temp dir.
            clean_env = os.environ.copy()
            if '_MEIPASS' in clean_env:
                del clean_env['_MEIPASS']
            
            # Launch detached process — avoid shell=True for security
            subprocess.Popen(["cmd.exe", "/c", bat_path], shell=False, close_fds=True, cwd=exe_dir, env=clean_env)
            
            return True, "Restarting..."
        except Exception as e:
            return False, f"Failed to launch updater: {e}"