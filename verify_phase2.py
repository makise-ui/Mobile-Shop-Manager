import tkinter as tk
import ttkbootstrap as tb
from gui.screens.reporting_widgets import AdvancedFilterPanel, SamplingPanel

def verify():
    root = tb.Window(themename="flatly")
    root.title("Phase 2 UI Verification")
    root.geometry("800x600")

    available_fields = ["unique_id", "imei", "model", "price", "last_updated", "status"]
    
    left = AdvancedFilterPanel(root, available_fields)
    left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    right = SamplingPanel(root)
    right.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
    
    def show_data():
        print("Filters:", left.get_filters())
        print("Sampling:", right.get_sampling_data())

    tb.Button(root, text="Print State to Console", command=show_data).pack(side=tk.BOTTOM, pady=10)

    print("Opening verification window. Please check the UI components.")
    root.mainloop()

if __name__ == "__main__":
    try:
        verify()
    except tk.TclError:
        print("[SKIP] No display detected. UI verification requires a screen.")
