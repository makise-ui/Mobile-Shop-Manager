import tkinter as tk
from tkinter import ttk
from core.config import ConfigManager
from core.inventory import InventoryManager
from core.watcher import InventoryWatcher
from core.barcode_utils import BarcodeGenerator
from core.printer import PrinterManager
from core.billing import BillingManager
from core.activity_log import ActivityLogger
from gui.screens import InventoryScreen, FilesScreen, BillingScreen, AnalyticsScreen, SettingsScreen, ManageDataScreen, SearchScreen, StatusScreen, EditDataScreen, HelpScreen, InvoiceHistoryScreen, ActivityLogScreen, ConflictScreen
from gui.dialogs import ConflictResolutionDialog, SplashScreen, WelcomeDialog

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("4 Bros Mobile Manager")
        self.geometry("1100x700")
        
        # --- Splash Screen ---
        store_name = ConfigManager().get('store_name', '4 Bros Mobile')
        splash = SplashScreen(self, store_name)
        self.withdraw() # Hide main window while splash shows
        
        # Set Icon (Safe Load)
        try:
            # Only try loading icon if we are on Windows or if file exists
            icon_path = "icon.jpg" 
            import sys
            import os
            
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, "icon.jpg")
            
            if os.path.exists(icon_path):
                # On Termux/X11, high-res icons can crash X_CreateWindow
                # Only load if on Windows to be safe, or wrap tightly
                if os.name == 'nt':
                    from PIL import ImageTk, Image
                    img = Image.open(icon_path)
                    self.iconphoto(True, ImageTk.PhotoImage(img))
        except Exception as e:
            print(f"Icon load skipped: {e}")
        
        # --- Core Initialization ---
        self.app_config = ConfigManager()
        self.activity_logger = ActivityLogger(self.app_config)
        self.inventory = InventoryManager(self.app_config, self.activity_logger)
        self.barcode_gen = BarcodeGenerator(self.app_config)
        self.printer = PrinterManager(self.app_config, self.barcode_gen)
        self.billing = BillingManager(self.app_config, self.activity_logger)
        
        # --- Watcher ---
        self.watcher = InventoryWatcher(self.inventory, self._on_inventory_update)
        
        # --- UI Initialization ---
        self._init_layout()
        
        # --- Start ---
        self.inventory.reload_all()
        self.watcher.start_watching()
        
        # Close Splash and Show Main
        self.after(2000, lambda: self._finish_init(splash))

    def _finish_init(self, splash):
        splash.destroy()
        self.deiconify() # Show main window
        
        # Force refresh of default screen to ensure data is visible
        if 'inventory' in self.screens:
             self.screens['inventory'].on_show()
        
        self.after(500, self._check_conflicts) # Check conflicts on startup
        
        # Check if first run (no files)
        if not self.app_config.mappings:
            WelcomeDialog(self, self._on_welcome_choice)

    def _on_welcome_choice(self, choice):
        if choice == "files":
            self.show_screen("files")
        elif choice == "help":
            self.show_screen("help")
        # 'explore' just stays on inventory

    def _init_layout(self):
        # --- Styles ---
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        BG_COLOR = "#f0f0f0"
        NAV_BG = "#2c3e50"
        NAV_FG = "white"
        ACCENT = "#007acc"
        
        self.configure(background=BG_COLOR)
        
        # Configure Styles
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, font=('Segoe UI', 10))
        style.configure("TLabelframe", background=BG_COLOR)
        style.configure("TLabelframe.Label", background=BG_COLOR, font=('Segoe UI', 11, 'bold'), foreground="#333")
        
        # Nav Button Style
        style.configure("Nav.TButton", font=('Segoe UI', 10, 'bold'), background=NAV_BG, foreground=NAV_FG, borderwidth=0, focuscolor=NAV_BG)
        style.map("Nav.TButton", background=[('active', '#34495e'), ('pressed', ACCENT)])
        
        # Accent Button
        style.configure("Accent.TButton", font=('Segoe UI', 10, 'bold'), background=ACCENT, foreground="white")
        style.map("Accent.TButton", background=[('active', '#005f9e')])
        
        # Treeview
        style.configure("Treeview", rowheight=28, font=('Segoe UI', 10), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'), background="#e0e0e0")
        
        # --- Layout ---
        
        # 1. Top Navigation Bar
        nav_frame = tk.Frame(self, bg=NAV_BG, height=50)
        nav_frame.pack(side=tk.TOP, fill=tk.X)
        nav_frame.pack_propagate(False) # Fixed height
        
        # App Title in Nav
        lbl_title = tk.Label(nav_frame, text="4BROS MANAGER", font=('Segoe UI', 14, 'bold'), bg=NAV_BG, fg="white")
        lbl_title.pack(side=tk.LEFT, padx=20)
        
        # Nav Buttons
        btn_bar = tk.Frame(nav_frame, bg=NAV_BG)
        btn_bar.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        nav_items = [
            ("Inventory", "inventory"),
            ("Search", "search"),
            ("Quick Status", "status"),
            ("Edit", "edit"),
            ("Billing", "billing"),
            ("Invoices", "invoices"),
            ("Analytics", "analytics"),
        ]
        
        self.nav_btns = {}
        for label, key in nav_items:
            btn = ttk.Button(btn_bar, text=label, style="Nav.TButton", command=lambda k=key: self.show_screen(k))
            btn.pack(side=tk.LEFT, padx=2, pady=10)
            self.nav_btns[key] = btn

        # Manage Dropdown (for less used items)
        mb = ttk.Menubutton(btn_bar, text="Manage ▼", style="Nav.TButton")
        menu = tk.Menu(mb, tearoff=0, bg=NAV_BG, fg="black", font=('Segoe UI', 10))
        
        menu.add_command(label="Manage Files", command=lambda: self.show_screen('files'))
        menu.add_command(label="Manage Data", command=lambda: self.show_screen('managedata'))
        menu.add_command(label="Activity Log", command=lambda: self.show_screen('activity'))
        menu.add_command(label="Conflicts", command=lambda: self.show_screen('conflicts'))
        menu.add_separator()
        menu.add_command(label="User Guide & Help", command=lambda: self.show_screen('help'))
        menu.add_command(label="Settings", command=lambda: self.show_screen('settings'))
        
        mb.config(menu=menu)
        mb.pack(side=tk.LEFT, padx=2, pady=10)

        # 2. Main Content Area (Card style)
        self.container = tk.Frame(self, bg=BG_COLOR)
        self.container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.content_area = ttk.Frame(self.container) # Inner frame for padding
        self.content_area.pack(fill=tk.BOTH, expand=True) # Fill the 'card' area
        
        # Initialize Screens
        self.screens = {}
        self.screens['inventory'] = InventoryScreen(self.content_area, self)
        self.screens['search'] = SearchScreen(self.content_area, self)
        self.screens['status'] = StatusScreen(self.content_area, self)
        self.screens['edit'] = EditDataScreen(self.content_area, self)
        self.screens['files'] = FilesScreen(self.content_area, self)
        self.screens['billing'] = BillingScreen(self.content_area, self)
        self.screens['invoices'] = InvoiceHistoryScreen(self.content_area, self)
        self.screens['activity'] = ActivityLogScreen(self.content_area, self)
        self.screens['conflicts'] = ConflictScreen(self.content_area, self)
        self.screens['analytics'] = AnalyticsScreen(self.content_area, self)
        self.screens['settings'] = SettingsScreen(self.content_area, self)
        self.screens['managedata'] = ManageDataScreen(self.content_area, self)
        self.screens['help'] = HelpScreen(self.content_area, self)
        
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
        if 'inventory' in self.screens:
            self.screens['inventory'].refresh_data()
        
        self._check_conflicts()
            
    def _check_conflicts(self):
        if hasattr(self.inventory, 'conflicts') and self.inventory.conflicts:
            count = len(self.inventory.conflicts)
            self.status_var.set(f"WARNING: {count} IMEI conflicts detected!")
            
            # Pop the first conflict
            c = self.inventory.conflicts[0]
            ConflictResolutionDialog(self, c, self._resolve_conflict_callback)
        else:
            self.status_var.set("Inventory Ready.")

    def _resolve_conflict_callback(self, conflict_data, action):
        # Update backend
        self.inventory.resolve_conflict(conflict_data, action)
        # Remove resolved conflict from list
        if conflict_data in self.inventory.conflicts:
            self.inventory.conflicts.remove(conflict_data)
        
        # Check if more remain
        self._check_conflicts()

    def on_close(self):
        self.watcher.stop_watching()
        self.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
