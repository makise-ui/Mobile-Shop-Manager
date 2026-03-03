from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time
import threading
from threading import Timer

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, callback, watched_files):
        self.callback = callback
        self.watched_files = set(os.path.abspath(f) for f in watched_files)
        self.debounce_timer = None
        self._timer_lock = threading.Lock()  # Bug #14 fix

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
        # Bug #14 fix: protect debounce timer with a lock
        with self._timer_lock:
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
        self.observer = None
        self.handler = FileChangeHandler(self._on_file_changed, [])
        self.watching = False

    def _on_file_changed(self):
        """Called from Timer thread. Reload data then safely notify GUI."""
        print("File change detected, reloading inventory...")
        try:
            self.inv_manager.reload_all()
        except Exception as e:
            print(f"Reload failed: {e}")
            return
        # Bug #11 fix: external_callback is already wrapped with
        # self.after(0, ...) in app.py, which is Tk-thread-safe.
        # But we add extra safety by catching errors here.
        if self.external_callback:
            try:
                self.external_callback()
            except Exception as e:
                print(f"Watcher callback error: {e}")

    def start_watching(self):
        # Bug #17 fix: fully stop any existing observer before starting
        if self.watching:
            self.stop_watching()
        
        # Always create a fresh observer
        self.observer = Observer()
            
        mappings = self.inv_manager.config_manager.mappings
        files = list(mappings.keys())
        self.handler.update_watched_files(files)
        
        # Watch parent directories of all files
        directories = set(os.path.dirname(os.path.abspath(f)) for f in files if os.path.exists(f))
        
        for directory in directories:
            self.observer.schedule(self.handler, directory, recursive=False)
        
        try:
            self.observer.start()
            self.watching = True
        except Exception as e:
            print(f"Watcher start error: {e}")
            self.watching = False

    def stop_watching(self):
        if self.watching and self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=5)  # Bug #17 fix: timeout prevents hang
            except Exception as e:
                print(f"Watcher stop error: {e}")
            self.observer = None
            self.watching = False
    
    def refresh_watch_list(self):
        if self.watching:
            self.stop_watching()
            self.start_watching()
