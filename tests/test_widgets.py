import unittest
import tkinter as tk
import ttkbootstrap as tb
from unittest.mock import MagicMock, patch
import sys

# Mock display for headless environment
try:
    root = tk.Tk()
    root.withdraw()
except tk.TclError:
    # If no display, we can't really test widgets easily without xvfb
    # But we can try to mock things if we really want TDD.
    print("No display detected, skipping widget UI tests")
    sys.exit(0)

from gui.widgets import IconButton

class TestIconButton(unittest.TestCase):
    def test_icon_button_creation(self):
        """Test that IconButton can be instantiated with an image and command."""
        root = tk.Toplevel()
        
        # Create a dummy image
        img = tk.PhotoImage(width=1, height=1)
        
        mock_cmd = MagicMock()
        
        btn = IconButton(root, image=img, command=mock_cmd, tooltip="Test")
        btn.pack()
        
        # Verify it's a Button
        self.assertIsInstance(btn, tb.Button)
        
        # Verify tooltip (if we can access it, usually it's attached via event binding)
        # We can check if ToolTip was initialized. 
        # For now, just ensuring it doesn't crash is a good start.
        
        # Simulate click
        btn.invoke()
        mock_cmd.assert_called_once()
        
        root.destroy()

if __name__ == '__main__':
    unittest.main()