import tkinter as tk
from tkinter import ttk

# --- Custom Widgets ---
class AutocompleteEntry(ttk.Entry):
    def __init__(self, parent, completion_list=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._completion_list = sorted(completion_list) if completion_list else []
        self.bind('<KeyRelease>', self.handle_keyrelease)

    def set_completion_list(self, completion_list):
        """Update the list of possible completions"""
        # Filter out non-strings and empty strings, ensure sorted unique
        clean_list = sorted(list(set([str(x) for x in completion_list if x])))
        self._completion_list = clean_list

    def handle_keyrelease(self, event):
        """Inline Type-Ahead Autocomplete"""
        if event.keysym in ('BackSpace', 'Left', 'Right', 'Up', 'Down', 'Return', 'Tab', 'Delete', 'Escape'):
            return

        # Only autocomplete if cursor is at the end
        if self.index(tk.INSERT) != len(self.get()):
            return

        # Get typed text
        full_text = self.get()
        if not full_text: return
        
        # Find closest match that STARTS with full_text
        # Use Case-Insensitive match, but insert the Match's case
        match = next((item for item in self._completion_list if item.lower().startswith(full_text.lower())), None)
        
        if match:
            # Check if we already have the full match (to avoid loops)
            if full_text == match:
                return
                
            remainder = match[len(full_text):]
            self.insert(tk.END, remainder)
            self.select_range(len(full_text), tk.END)
            self.icursor(len(full_text))

# --- Base Screen Class ---
class BaseScreen(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent, padding=15)
        self.app = app_context
    
    def on_show(self):
        """Called when screen becomes visible"""
        pass

    def focus_primary(self):
        """Focus on the primary input widget of the screen"""
        pass

    def _get_all_models(self):
        """Helper to get unique models for autocomplete"""
        try:
            df = self.app.inventory.get_inventory()
            if not df.empty:
                return df['model'].dropna().unique().tolist()
        except: pass
        return []
