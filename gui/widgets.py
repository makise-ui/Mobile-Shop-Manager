import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.tooltip import ToolTip

class IconButton(tb.Button):
    """
    A reusable Icon Button with ToolTip support.
    """
    def __init__(self, master, image=None, command=None, tooltip=None, bootstyle="light-outline", **kwargs):
        super().__init__(master, image=image, command=command, bootstyle=bootstyle, **kwargs)
        self.image = image # Keep reference to avoid garbage collection
        
        if tooltip:
            ToolTip(self, text=tooltip, bootstyle="inverse")
            
    def update_icon(self, new_image):
        self.configure(image=new_image)
        self.image = new_image

class CollapsibleFrame(ttk.Frame):
    """
    A Frame designed to be toggled visibility.
    Assumes it is managed via pack().
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._is_expanded = False
        self._pack_opts = {}
        
    def show(self, **pack_opts):
        """Show the frame using pack geometry manager."""
        self._pack_opts = pack_opts
        self.pack(**pack_opts)
        self._is_expanded = True
        
    def hide(self):
        """Hide the frame."""
        self.pack_forget()
        self._is_expanded = False
        
    def toggle(self, **pack_opts):
        """Toggle visibility."""
        if self._is_expanded:
            self.hide()
        else:
            # Use stored pack options if none provided
            opts = pack_opts if pack_opts else self._pack_opts
            self.show(**opts)
            
    @property
    def is_expanded(self):
        return self._is_expanded