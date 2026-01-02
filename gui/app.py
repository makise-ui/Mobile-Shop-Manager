import tkinter as tk
from tkinter import ttk
from core.config import ConfigManager
from core.inventory import InventoryManager
from core.watcher import InventoryWatcher
from core.barcode_utils import BarcodeGenerator
from core.printer import PrinterManager
from core.billing import BillingManager
from gui.screens import InventoryScreen, FilesScreen, BillingScreen, AnalyticsScreen, SettingsScreen, ColorScreen, SearchScreen

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("4 Bros Mobile Manager")
        self.geometry("1100x700")
        
        # --- Core Initialization ---
        self.app_config = ConfigManager()
        self.inventory = InventoryManager(self.app_config)
        self.barcode_gen = BarcodeGenerator(self.app_config)
        self.printer = PrinterManager(self.app_config, self.barcode_gen)
        self.billing = BillingManager(self.app_config)
        
        # --- Watcher ---
        self.watcher = InventoryWatcher(self.inventory, self._on_inventory_update)
        
        # --- UI Initialization ---
        self._init_layout()
        
        # --- Start ---
        self.inventory.reload_all()
        self.watcher.start_watching()

    def _init_layout(self):
        # --- Styles ---
        style = ttk.Style()
        style.theme_use('clam') # 'clam' usually looks cleaner than default 'tk'
        
        # Treeview Style
        style.configure("Treeview", rowheight=25, font=('Segoe UI', 10))
        style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
        
        # General
        style.configure("TButton", font=('Segoe UI', 10), padding=5)
        style.configure("TLabel", font=('Segoe UI', 10))
        style.configure("TLabelframe.Label", font=('Segoe UI', 10, 'bold'))
        
        # Main Container: Sidebar (Left) + Content (Right)
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        sidebar = ttk.Frame(container, padding=5, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        # Sidebar Buttons
        # Use simple Buttons for navigation
        nav_items = [
            ("Inventory", "inventory"),
            ("Search ID", "search"),
            ("Manage Files", "files"),
            ("Billing / GST", "billing"),
            ("Analytics", "analytics"),
            ("Manage Colors", "colors"),
            ("Settings", "settings")
        ]
        
        ttk.Label(sidebar, text="MENU", font=('Arial', 10, 'bold')).pack(pady=10)
        
        for label, key in nav_items:
            btn = ttk.Button(sidebar, text=label, command=lambda k=key: self.show_screen(k))
            btn.pack(fill=tk.X, pady=2)

        # Content Area
        self.content_area = ttk.Frame(container)
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Initialize Screens
        self.screens = {}
        self.screens['inventory'] = InventoryScreen(self.content_area, self)
        self.screens['search'] = SearchScreen(self.content_area, self)
        self.screens['files'] = FilesScreen(self.content_area, self)
        self.screens['billing'] = BillingScreen(self.content_area, self)
        self.screens['analytics'] = AnalyticsScreen(self.content_area, self)
        self.screens['settings'] = SettingsScreen(self.content_area, self)
        self.screens['colors'] = ColorScreen(self.content_area, self)
        
        # Show default
        self.show_screen('inventory')
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        statusbar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def show_screen(self, key):
        # Hide all
        for screen in self.screens.values():
            screen.pack_forget()
        
        # Show selected
        target = self.screens.get(key)
        if target:
            target.pack(fill=tk.BOTH, expand=True)
            target.on_show() # Trigger refresh hook

    def switch_to_billing(self, items):
        """Helper to jump to billing with items"""
        billing_screen = self.screens['billing']
        billing_screen.add_items(items)
        self.show_screen('billing')

    def _on_inventory_update(self):
        self.after(0, self._refresh_ui)

    def _refresh_ui(self):
        # If inventory is visible, refresh it
        # We can just call on_show of current if it's inventory
        # For simplicity, just refresh inventory screen data if it exists
        if 'inventory' in self.screens:
            self.screens['inventory'].refresh_data()
        
        # Check conflicts
        if hasattr(self.inventory, 'conflicts') and self.inventory.conflicts:
            count = len(self.inventory.conflicts)
            self.status_var.set(f"Inventory updated. WARNING: {count} IMEI conflicts detected!")
            # Ideally show a dialog or button to resolve
        else:
            self.status_var.set("Inventory updated from file change.")

    def on_close(self):
        self.watcher.stop_watching()
        self.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()