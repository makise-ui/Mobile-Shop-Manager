import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
import sys
import os
import datetime
import pandas as pd
from core.config import ConfigManager
from core.inventory import InventoryManager
from core.printer import PrinterManager
from core.billing import BillingManager
from core.updater import UpdateChecker
from core.version import APP_VERSION
from core.activity_log import ActivityLogger
from core.barcode_utils import BarcodeGenerator
from core.watcher import InventoryWatcher
from core.licensing import LicenseManager
from gui.activation import LicenseDialog
from gui.quick_nav import QuickNavOverlay
from gui.screens import (
    InventoryScreen, BillingScreen, AnalyticsScreen, SettingsScreen, 
    ManageDataScreen, SearchScreen, StatusScreen, EditDataScreen, 
    HelpScreen, InvoiceHistoryScreen, ActivityLogScreen, ConflictScreen,
    DashboardScreen, ManageFilesScreen
)
from gui.reporting import ReportingScreen
from gui.dialogs import ConflictResolutionDialog, SplashScreen, WelcomeDialog
from gui.quick_entry import QuickEntryScreen
from gui.zpl_designer import ZPLDesignerScreen
from gui.testing_screen import TestingScreen

class MainApp(tb.Window):
    def __init__(self):
        # Load Theme from Config
        conf = ConfigManager()
        theme = conf.get('theme_name', 'cosmo')
        
        super().__init__(themename=theme)
        self.app_config = conf # Reuse loaded config
        
        app_title = self.app_config.get('app_display_name', 'Mobile Shop Manager')
        self.title(f"{app_title} v{APP_VERSION}")
        self.geometry("1100x700")
        
        # Use bind_all for global shortcuts
        self.bind_all("<Control-n>", self.open_quick_nav, add='+')
        self.bind_all("<Control-N>", self.open_quick_nav, add='+')
        self.bind_all("<Control-w>", self.open_quick_nav, add='+')
        self.bind_all("<Control-W>", self.open_quick_nav, add='+')
        
        # Power User Hotkeys
        self.bind_all("<F1>", lambda e: self.show_screen('search'), add='+')
        self.bind_all("<F2>", lambda e: self.show_screen('quick_entry'), add='+')
        self.bind_all("<F3>", lambda e: self.show_screen('status'), add='+')
        self.bind_all("<F4>", lambda e: self.show_screen('billing'), add='+')
        self.bind_all("<F5>", lambda e: self.manual_refresh(), add='+')
        self.bind_all("<Escape>", lambda e: self.show_screen('dashboard'), add='+')
        
        self.license_mgr = LicenseManager(self.app_config)
        self.suppress_conflicts = False # Flag to suppress conflict dialogs
        
        # --- License Check ---
        if not self.license_mgr.is_activated():
            self.withdraw() # Hide main window
            # Show Activation Dialog. 
            # Note: We pass 'self._start_application' as the success callback
            LicenseDialog(self, self.license_mgr, self._start_application)
        else:
            self._start_application()

    def _start_application(self):
        # --- Splash Screen ---
        app_name = self.app_config.get('app_display_name', 'Mobile Shop Manager')
        splash = SplashScreen(self, app_name)
        self.withdraw() # Ensure hidden while splash runs
        
        # Set Icon (Safe Load)
        try:
            icon_path = "icon.ico" 
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, "icon.ico")
            
            if os.path.exists(icon_path):
                if os.name == 'nt':
                    from PIL import ImageTk, Image
                    img = Image.open(icon_path)
                    self.iconphoto(True, ImageTk.PhotoImage(img))
        except Exception as e:
            print(f"Icon load skipped: {e}")
        
        # --- Core Initialization ---
        self.activity_logger = ActivityLogger(self.app_config)
        self.updater = UpdateChecker()
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
        self.updater.check_for_updates(self._on_update_found)
        if 'inventory' in self.screens:
             self.screens['inventory'].on_show()
        self.after(500, self._check_conflicts)
        if not self.app_config.mappings:
            WelcomeDialog(self, self._on_welcome_choice)

    def _on_update_found(self, available, tag, notes):
        if available:
            self.btn_update.config(text=f"⬇ Update Available ({tag})")
            self.btn_update.pack(side=tk.RIGHT, padx=20)

    def _show_update_dialog(self):
        top = tk.Toplevel(self)
        top.title("Update Available")
        top.geometry("500x450")
        top.transient(self)
        top.grab_set()
        
        ttk.Label(top, text=f"New Version Available: {self.updater.latest_version}", font=('Segoe UI', 14, 'bold')).pack(pady=10)
        lbl_notes = ttk.Label(top, text="What's New:", font=('Segoe UI', 10, 'bold'))
        lbl_notes.pack(anchor=tk.W, padx=10)
        
        txt = tk.Text(top, height=10, font=('Segoe UI', 10), wrap=tk.WORD, bg="#f0f0f0", relief=tk.FLAT)
        txt.insert(tk.END, self.updater.release_notes)
        txt.configure(state='disabled')
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(top, variable=progress_var, maximum=100)
        lbl_status = ttk.Label(top, text="")
        
        def update_progress(percent):
            progress_var.set(percent)
            lbl_status.config(text=f"Downloading... {percent}%")
            top.update_idletasks()
            
        def finish_download(file_path):
            lbl_status.config(text="Installing...")
            success, msg = self.updater.restart_and_install(file_path)
            if not success:
                lbl_status.config(text="Update Failed", foreground="red")
                messagebox.showwarning("Update Error", msg)
                btn_update.config(state='normal')
            else:
                self.update_idletasks()
                if self.watcher: self.watcher.stop_watching()
                self.destroy()
                sys.exit(0)

        def start_download():
            btn_update.config(state='disabled')
            progress_bar.pack(fill=tk.X, padx=20, pady=(10,0))
            lbl_status.pack(pady=5)
            self.updater.download_update(update_progress, finish_download)
            
        btn_update = ttk.Button(top, text="Update Now & Restart", command=start_download, style="Accent.TButton")
        btn_update.pack(pady=20)

    def _on_welcome_choice(self, choice):
        if choice == "files":
            self.show_screen("files")
        elif choice == "help":
            self.show_screen("help")

    def _init_layout(self):
        style = ttk.Style()
        NAV_BG = "#343a40"
        style.configure("Treeview", rowheight=30, font=('Segoe UI', 10))
        style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
        
        # 1. Top Navigation Bar
        nav_frame = tk.Frame(self, bg=NAV_BG, height=60)
        nav_frame.pack(side=tk.TOP, fill=tk.X)
        nav_frame.pack_propagate(False)
        
        app_title = self.app_config.get('app_display_name', 'Mobile Shop Manager').upper()
        lbl_title = tk.Label(nav_frame, text=app_title, font=('Segoe UI', 14, 'bold'), bg=NAV_BG, fg="white")
        lbl_title.pack(side=tk.LEFT, padx=20)
        
        self.btn_refresh = ttk.Button(nav_frame, text="⟳ REFRESH", style="info.TButton", command=self.manual_refresh)
        self.btn_refresh.pack(side=tk.RIGHT, padx=10, pady=10)
        self.btn_update = ttk.Button(nav_frame, text="⬇ Update Available", style="danger.TButton", command=self._show_update_dialog)

        btn_bar = tk.Frame(nav_frame, bg=NAV_BG)
        btn_bar.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        # Primary Navigation Items (High Usage)
        nav_items = [
            ("Inventory", "inventory"),
            ("Search", "search"),
            ("Quick Status", "status"),
            ("Quick Entry", "quick_entry"),
            ("Billing", "billing"),
            ("Dashboard", "dashboard"),
        ]
        
        self.nav_btns = {}
        for label, key in nav_items:
            btn = ttk.Button(btn_bar, text=label, style="primary.TButton", command=lambda k=key: self.show_screen(k))
            btn.pack(side=tk.LEFT, padx=2, pady=10)
            self.nav_btns[key] = btn

        # --- REPORTS Menu ---
        mb_rep = ttk.Menubutton(btn_bar, text="Reports ▼", style="primary.TButton")
        m_rep = tk.Menu(mb_rep, tearoff=0, font=('Segoe UI', 10))
        m_rep.add_command(label="Analytics Dashboard", command=lambda: self.show_screen('analytics'))
        m_rep.add_command(label="Advanced Reporting", command=lambda: self.show_screen('reporting'))
        m_rep.add_command(label="Invoice History", command=lambda: self.show_screen('invoices'))
        m_rep.add_command(label="Activity Logs", command=lambda: self.show_screen('activity'))
        mb_rep.config(menu=m_rep)
        mb_rep.pack(side=tk.LEFT, padx=2, pady=10)
        
        # --- MORE Menu ---
        mb_more = ttk.Menubutton(btn_bar, text="Edit / More ▼", style="primary.TButton")
        m_more = tk.Menu(mb_more, tearoff=0, font=('Segoe UI', 10))
        m_more.add_command(label="Edit Mobile Data", command=lambda: self.show_screen('edit'))
        m_more.add_separator()
        m_more.add_command(label="System Diagnostics", command=lambda: self.show_screen('testing'))
        mb_more.config(menu=m_more)
        mb_more.pack(side=tk.LEFT, padx=2, pady=10)

        mb_manage = ttk.Menubutton(btn_bar, text="Manage ▼", style="primary.TButton")
        m_manage = tk.Menu(mb_manage, tearoff=0, font=('Segoe UI', 10))
        m_manage.add_command(label="Manage Files", command=lambda: self.show_screen('files'))
        m_manage.add_command(label="Manage Data (Colors/Grades)", command=lambda: self.show_screen('managedata'))
        m_manage.add_command(label="Label Designer", command=lambda: self.show_screen('designer'))
        m_manage.add_command(label="Conflicts", command=lambda: self.show_screen('conflicts'))
        m_manage.add_separator()
        m_manage.add_command(label="Settings", command=lambda: self.show_screen('settings'))
        m_manage.add_command(label="Help / User Guide", command=lambda: self.show_screen('help'))
        mb_manage.config(menu=m_manage)
        mb_manage.pack(side=tk.LEFT, padx=2, pady=10)

        # 2. Main Content Area
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.content_area = ttk.Frame(self.container)
        self.content_area.pack(fill=tk.BOTH, expand=True)
        
        # Initialize Screens
        self.screens = {}
        self.screens['dashboard'] = DashboardScreen(self.content_area, self)
        self.screens['quick_entry'] = QuickEntryScreen(self.content_area, self)
        self.screens['inventory'] = InventoryScreen(self.content_area, self)
        self.screens['search'] = SearchScreen(self.content_area, self)
        self.screens['status'] = StatusScreen(self.content_area, self)
        self.screens['edit'] = EditDataScreen(self.content_area, self)
        self.screens['files'] = ManageFilesScreen(self.content_area, self)
        self.screens['billing'] = BillingScreen(self.content_area, self)
        self.screens['invoices'] = InvoiceHistoryScreen(self.content_area, self)
        self.screens['activity'] = ActivityLogScreen(self.content_area, self)
        self.screens['conflicts'] = ConflictScreen(self.content_area, self)
        self.screens['reporting'] = ReportingScreen(self.content_area, self)
        self.screens['analytics'] = AnalyticsScreen(self.content_area, self)
        self.screens['settings'] = SettingsScreen(self.content_area, self)
        self.screens['managedata'] = ManageDataScreen(self.content_area, self)
        self.screens['designer'] = ZPLDesignerScreen(self.content_area, self)
        self.screens['help'] = HelpScreen(self.content_area, self)
        self.screens['testing'] = TestingScreen(self.content_area, self)
        
        self.show_screen('inventory')
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    def open_quick_nav(self, event=None):
        screens_map = {
            'dashboard': 'Dashboard',
            'inventory': 'Inventory',
            'billing': 'Billing',
            'edit': 'High-Speed Edit',
            'quick_entry': 'Quick Entry',
            'search': 'Search',
            'status': 'Status',
            'analytics': 'Analytics',
            'reporting': 'Advanced Reporting',
            'invoices': 'Invoices',
            'designer': 'Label Designer',
            'files': 'Manage Files',
            'managedata': 'Manage Data',
            'settings': 'Settings'
        }
        QuickNavOverlay(self, screens_map, self.show_screen)

    def show_screen(self, key):
        for screen in self.screens.values(): screen.pack_forget()
        target = self.screens.get(key)
        
        # Suppress conflict popups while in Quick Entry to avoid interruption
        self.suppress_conflicts = (key == 'quick_entry')
        
        if target:
            target.pack(fill=tk.BOTH, expand=True)
            target.on_show()
            target.focus_primary() # Auto-focus on primary input

    def switch_to_billing(self, items):
        self.screens['billing'].add_items(items)
        self.show_screen('billing')

    def manual_refresh(self):
        self.status_var.set("Refreshing data...")
        self.update_idletasks()
        self.inventory.reload_all()
        self.watcher.refresh_watch_list()
        self._refresh_ui()
        self.status_var.set("Data refreshed.")

    def _on_inventory_update(self):
        self.after(0, self._refresh_ui)

    def _refresh_ui(self):
        if 'inventory' in self.screens: self.screens['inventory'].refresh_data()
        self._check_conflicts()
            
    def _check_conflicts(self):
        if hasattr(self.inventory, 'conflicts') and self.inventory.conflicts:
            count = len(self.inventory.conflicts)
            self.status_var.set(f"WARNING: {count} IMEI conflicts detected!")
            
            if not self.suppress_conflicts:
                ConflictResolutionDialog(self, self.inventory.conflicts[0], self._resolve_conflict_callback)
        else:
            self.status_var.set("Inventory Ready.")

    def _resolve_conflict_callback(self, conflict_data, action):
        self.inventory.resolve_conflict(conflict_data, action)
        if conflict_data in self.inventory.conflicts: self.inventory.conflicts.remove(conflict_data)
        self._check_conflicts()

    def on_close(self):
        self.watcher.stop_watching()
        self.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()