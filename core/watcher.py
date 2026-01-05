from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time
from threading import Timer

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, callback, watched_files):
        self.callback = callback
        self.watched_files = set(os.path.abspath(f) for f in watched_files)
        self.debounce_timer = None

    def on_moved(self, event):
        if not event.is_directory:
            self._check(event.dest_path)

    def on_created(self, event):
        if not event.is_directory:
            self._check(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._check(event.src_path)

    def _check(self, path):
        try:
            # Check against absolute paths
            abs_path = os.path.abspath(path)
            if abs_path in self.watched_files:
                self._debounce_callback()
                return

            # Excel Logic: Excel saves as temp then renames/moves.
            # Sometimes we just see the final file creation or move.
            # Also, check if filename matches any watched file regardless of folder 
            # (though we only watch specific folders, this adds safety)
            fname = os.path.basename(abs_path)
            
            # Simple check: Does this filename match any of our watched files?
            for w in self.watched_files:
                if os.path.basename(w) == fname:
                    self._debounce_callback()
                    return
        except Exception as e:
            print(f"Watcher check error: {e}")

    def _debounce_callback(self):
        if self.debounce_timer:
            self.debounce_timer.cancel()
        self.debounce_timer = Timer(1.0, self.callback)
        self.debounce_timer.start()
        
    def update_watched_files(self, files):
        self.watched_files = set(os.path.abspath(f) for f in files)

class InventoryWatcher:
    def __init__(self, inventory_manager, on_change_callback):
        self.inv_manager = inventory_manager
        self.external_callback = on_change_callback
        self.observer = Observer()
        self.handler = FileChangeHandler(self._on_file_changed, [])
        self.watching = False

    def _on_file_changed(self):
        print("File change detected, reloading inventory...")
        # Reload on the main thread ideally, but here we just trigger the reload
        self.inv_manager.reload_all()
        if self.external_callback:
            self.external_callback()

    def start_watching(self):
        if self.watching:
            self.stop_watching()
            
        mappings = self.inv_manager.config_manager.mappings
        files = list(mappings.keys())
        self.handler.update_watched_files(files)
        
        # Watch parent directories of all files
        directories = set(os.path.dirname(os.path.abspath(f)) for f in files if os.path.exists(f))
        
        for directory in directories:
            self.observer.schedule(self.handler, directory, recursive=False)
            
        self.observer.start()
        self.watching = True

    def stop_watching(self):
        if self.watching:
            self.observer.stop()
            self.observer.join()
            self.observer = Observer() # Re-init for fresh start
            self.watching = False
    
    def refresh_watch_list(self):
        if self.watching:
            self.stop_watching()
            self.start_watching()
