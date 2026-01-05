import requests
import threading
import webbrowser
from packaging import version
from .version import APP_VERSION, REPO_OWNER, REPO_NAME

class UpdateChecker:
    def __init__(self):
        self.current_version = APP_VERSION
        self.latest_version = None
        self.download_url = None
        
    def check_for_updates(self, callback):
        """
        Checks for updates in a background thread.
        callback(is_available, version_tag, url)
        """
        def _check():
            try:
                url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    tag_name = data.get('tag_name', '0.0.0')
                    html_url = data.get('html_url', '')
                    
                    # Remove 'v' prefix for comparison
                    clean_tag = tag_name.lstrip('v')
                    clean_current = self.current_version.lstrip('v')
                    
                    if version.parse(clean_tag) > version.parse(clean_current):
                        self.latest_version = tag_name
                        self.download_url = html_url
                        callback(True, tag_name, html_url)
                    else:
                        callback(False, None, None)
                else:
                    callback(False, None, None)
            except Exception as e:
                print(f"Update check failed: {e}")
                callback(False, None, None)
                
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()

    def open_download_page(self):
        if self.download_url:
            webbrowser.open(self.download_url)