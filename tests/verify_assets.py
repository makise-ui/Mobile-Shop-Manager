import os
import sys
from PIL import Image, ImageTk
import tkinter as tk

# Mock display if needed (but we need to test loading into Tk)
try:
    root = tk.Tk()
    root.withdraw()
except:
    print("WARNING: No display, cannot test ImageTk fully.")
    # We can still test PIL Image.open

def verify():
    icon_dir = "assets/icons"
    if not os.path.exists(icon_dir):
        print(f"FAIL: {icon_dir} does not exist.")
        return

    icons = ["plus-lg.png", "printer.png", "trash.png", "arrow-clockwise.png", "filter.png", "search.png"]
    
    for icon in icons:
        path = os.path.join(icon_dir, icon)
        if not os.path.exists(path):
            print(f"FAIL: Missing {icon}")
            continue
            
        try:
            img = Image.open(path)
            print(f"PASS: Opened {icon} ({img.size})")
            
            if 'tkinter' in sys.modules and tk._default_root:
                tk_img = ImageTk.PhotoImage(img)
                print(f"PASS: Loaded {icon} into ImageTk")
        except Exception as e:
            print(f"FAIL: Error loading {icon}: {e}")

if __name__ == "__main__":
    verify()