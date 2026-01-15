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