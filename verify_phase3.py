import tkinter as tk
import ttkbootstrap as tb
import pandas as pd
from gui.reporting import ReportingScreen
from unittest.mock import MagicMock

def verify():
    root = tb.Window(themename="flatly")
    root.title("Phase 3 UI Verification")
    root.geometry("1000x700")

    # Mock Controller
    controller = MagicMock()
    
    # Mock Inventory
    data = {
        'unique_id': [1, 2, 3, 4, 5],
        'model': ['A', 'B', 'C', 'D', 'E'],
        'price': [100, 200, 300, 400, 500],
        'status': ['IN', 'OUT', 'IN', 'IN', 'OUT'],
        'last_updated': ['2026-01-01', '2026-01-02', '2026-01-03', '2026-01-04', '2026-01-05']
    }
    df = pd.DataFrame(data)
    controller.inventory.inventory_df = df

    app = ReportingScreen(root, controller)
    app.pack(fill=tk.BOTH, expand=True)
    
    # Trigger load
    app.on_show()

    print("Opening verification window. Please test PREVIEW and BACK buttons.")
    root.mainloop()

if __name__ == "__main__":
    try:
        verify()
    except tk.TclError:
        print("[SKIP] No display detected.")
