import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.toast import ToastNotification

from ..base import BaseScreen
from ..dialogs import MapColumnsDialog

class ManageFilesScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        
        self.add_header("Manage Inventory Files", help_section="Excel and File Management")
        
        # Toolbar
        tb = ttk.Frame(self)
        tb.pack(fill=tk.X, pady=10)
        ttk.Button(tb, text="+ Add Excel File", command=self._add_file).pack(side=tk.LEFT)
        ttk.Button(tb, text="Edit Mapping", command=self._edit_mapping).pack(side=tk.LEFT, padx=10)
        ttk.Button(tb, text="Remove File", command=self._remove_file).pack(side=tk.LEFT, padx=10)
        ttk.Button(tb, text="Refresh All", command=self._refresh).pack(side=tk.LEFT, padx=10)
        
        # List
        self.listbox = tk.Listbox(self, font=('Consolas', 10), height=15)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(self, text="* The app automatically watches these files for changes.", font=('Arial', 8, 'italic')).pack(pady=5)

    def on_show(self):
        self._refresh_list()

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        mappings = self.app.app_config.mappings
        
        # Store keys to map listbox index back to config key
        self.list_keys = []
        
        for key, data in mappings.items():
            status = self.app.inventory.file_status.get(key, "Unknown")
            supplier = data.get('supplier', 'Mixed/None')
            
            # Display: [OK] /path/to/file.xlsx (Sheet: Sheet1, Supplier: ABC)
            file_path = data.get('file_path', key)
            sheet = data.get('sheet_name', 'Default')
            
            display_text = f"[{status}] {file_path} (Sheet: {sheet}, Supplier: {supplier})"
            self.listbox.insert(tk.END, display_text)
            self.list_keys.append(key)

    def _add_file(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv")])
        for fp in file_paths:
            # Always open dialog to allow sheet selection
            # even if file is already mapped (could be different sheet)
            MapColumnsDialog(self.winfo_toplevel(), fp, self._on_mapping_save)
        
        # Refresh happens in callback, but call it here just in case of cancel/close
        # Actually _on_mapping_save handles refresh.

    def _edit_mapping(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selection", "Please select a file to edit mapping.")
            return
            
        key = self.list_keys[sel[0]]
        mapping_data = self.app.app_config.mappings.get(key)
        
        if not mapping_data: return
        
        fp = mapping_data.get('file_path', key)
        if '::' in fp: fp = fp.split('::')[0] # Safety
        
        MapColumnsDialog(self.winfo_toplevel(), fp, self._on_mapping_save, current_mapping=mapping_data)

    def _remove_file(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selection", "Please select a file to remove.")
            return

        key = self.list_keys[sel[0]]
        
        if messagebox.askyesno("Confirm", f"Remove inventory source?\n{key}"):
            # We need to expose remove logic in config that takes a KEY
            # Currently remove_file_mapping takes 'file_path' and does `del mappings[str(file_path)]`
            # This works if we pass the key!
            self.app.app_config.remove_file_mapping(key)
            self.app.inventory.reload_all()
            self.app.watcher.refresh_watch_list()
            self._refresh_list()

    def _on_mapping_save(self, key, mapping_data):
        # Key here is either file_path or composite key passed from Dialog
        self.app.app_config.set_file_mapping(key, mapping_data)
        self.app.inventory.reload_all()
        self.app.watcher.refresh_watch_list()
        self._refresh_list()
    
    def _refresh(self):
        self.app.inventory.reload_all()
        self._refresh_list()

class SettingsScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.style = tb.Style()
        self.vars = {}
        self.text_widgets = {}
        self._init_ui()

    def _init_ui(self):
        self.add_header("Application Settings", help_section="Features and Functionality")
        
        # Tabs
        tabs = ttk.Notebook(self)
        tabs.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # --- Tab 1: General ---
        tab_gen = ttk.Frame(tabs, padding=20)
        tabs.add(tab_gen, text="General")
        
        # Helper for grid
        def add_entry(parent, label, key, r, width=30):
            ttk.Label(parent, text=label).grid(row=r, column=0, sticky=tk.W, pady=5)
            var = tk.StringVar(value=str(self.app.app_config.get(key, '')))
            self.vars[key] = var
            ttk.Entry(parent, textvariable=var, width=width).grid(row=r, column=1, padx=10, sticky=tk.W)
            return r + 1

        r = 0
        r = add_entry(tab_gen, "Store Name:", "store_name", r)
        r = add_entry(tab_gen, "Auto-ID Prefix:", "auto_unique_id_prefix", r, width=10)
        r = add_entry(tab_gen, "Price Markup %:", "price_markup_percent", r, width=10)
        
        self.var_buyer = tk.BooleanVar(value=self.app.app_config.get("enable_buyer_tracking", True))
        ttk.Checkbutton(tab_gen, text="Enable Buyer Tracking (Save to Excel)", variable=self.var_buyer).grid(row=r, column=0, columnspan=2, sticky=tk.W, pady=10)

        # --- Tab 2: Printing ---
        tab_print = ttk.Frame(tabs, padding=20)
        tabs.add(tab_print, text="Printing")
        
        r = 0
        r = add_entry(tab_print, "Label Width (mm):", "label_width_mm", r, width=10)
        r = add_entry(tab_print, "Label Height (mm):", "label_height_mm", r, width=10)

        # --- Tab 3: Invoice ---
        tab_inv = ttk.Frame(tabs, padding=20)
        tabs.add(tab_inv, text="Invoice")
        
        r = 0
        r = add_entry(tab_inv, "GSTIN:", "store_gstin", r)
        r = add_entry(tab_inv, "Phone / Contact:", "store_contact", r)
        r = add_entry(tab_inv, "GST Default %:", "gst_default_percent", r, width=10)
        
        # Address
        ttk.Label(tab_inv, text="Store Address:").grid(row=r, column=0, sticky=tk.NW, pady=5)
        txt_addr = tk.Text(tab_inv, height=4, width=40, font=('Segoe UI', 10))
        txt_addr.insert('1.0', self.app.app_config.get('store_address', ''))
        txt_addr.grid(row=r, column=1, padx=10, pady=5)
        self.text_widgets['store_address'] = txt_addr
        r += 1
        
        # Terms
        ttk.Label(tab_inv, text="Invoice Terms:").grid(row=r, column=0, sticky=tk.NW, pady=5)
        txt_terms = tk.Text(tab_inv, height=4, width=40, font=('Segoe UI', 10))
        txt_terms.insert('1.0', self.app.app_config.get('invoice_terms', ''))
        txt_terms.grid(row=r, column=1, padx=10, pady=5)
        self.text_widgets['invoice_terms'] = txt_terms
        
        # --- Tab 4: Appearance ---
        tab_app = ttk.Frame(tabs, padding=20)
        tabs.add(tab_app, text="Appearance")
        
        ttk.Label(tab_app, text="Theme:", font=('bold')).pack(anchor=tk.W)
        
        # Ensure full sorted list of themes
        themes = sorted(self.style.theme_names())
        current = self.app.app_config.get('theme_name', 'cosmo')
        
        # Helper label for dark mode
        ttk.Label(tab_app, text="(Try 'darkly', 'superhero', 'cyborg' for Dark Mode)", font=('Segoe UI', 9), foreground='gray').pack(anchor=tk.W, pady=(0,5))
        self.var_theme = tk.StringVar(value=current)
        
        cb = ttk.Combobox(tab_app, textvariable=self.var_theme, values=themes, state="readonly", width=20)
        cb.pack(anchor=tk.W, pady=5)
        cb.bind("<<ComboboxSelected>>", self._on_theme_change)
        
        # --- Tab 2: Intelligence (AI) ---
        tab_ai = ttk.Frame(tabs, padding=20)
        tabs.add(tab_ai, text="Intelligence")
        
        ttk.Label(tab_ai, text="Artificial Intelligence Features", font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        self.var_ai = tk.BooleanVar(value=self.app.app_config.get('enable_ai_features', True))
        chk_ai = ttk.Checkbutton(tab_ai, text="Enable AI Actions & Insights", variable=self.var_ai, bootstyle="round-toggle")
        chk_ai.pack(anchor=tk.W, pady=10)
        
        ttk.Label(tab_ai, text="Features Enabled:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        ttk.Label(tab_ai, text="• Demand Forecasting (Stockout Alerts)\n• Smart Price Rounding\n• Brand Extraction", foreground="gray").pack(anchor=tk.W, padx=20)

        # Save Button
        ttk.Button(self, text="Save All Settings", command=self._save, style="success.TButton").pack(pady=20)

    def _on_theme_change(self, event):
        self.style.theme_use(self.var_theme.get())

    def _save(self):
        try:
            # Save Vars
            for key, var in self.vars.items():
                val = var.get()
                # Try convert to float if it looks like one (for mm, price)
                try:
                    if key in ['label_width_mm', 'label_height_mm', 'price_markup_percent', 'gst_default_percent']:
                        val = float(val)
                except:
                    pass
                self.app.app_config.set(key, val)
            
            # Save Text Widgets
            for key, widget in self.text_widgets.items():
                self.app.app_config.set(key, widget.get("1.0", tk.END).strip())
                
            # Save Specifics
            self.app.app_config.set("enable_buyer_tracking", self.var_buyer.get())
            self.app.app_config.set("enable_ai_features", self.var_ai.get())
            self.app.app_config.set('theme_name', self.var_theme.get())
            
            ToastNotification(
                title="Saved", 
                message="Settings updated successfully.", 
                duration=3000, 
                bootstyle="success"
            ).show_toast()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values")

class ManageDataScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        from core.data_registry import DataRegistry
        self.registry = DataRegistry()
        
        # UI
        self.add_header("Manage App Data", help_section="Data Management")
        
        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Colors
        self.tab_colors = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_colors, text="Mobile Colors")
        self._init_list_ui(self.tab_colors, "Color", self.registry.get_colors, self.registry.add_color, self.registry.remove_color)
        
        # Tab 2: Buyers
        self.tab_buyers = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_buyers, text="Frequent Buyers")
        self._init_list_ui(self.tab_buyers, "Buyer Name", self.registry.get_buyers, self.registry.add_buyer, self.registry.remove_buyer)

        # Tab 3: Grades
        self.tab_grades = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_grades, text="Grades")
        self._init_list_ui(self.tab_grades, "Grade", self.registry.get_grades, self.registry.add_grade, self.registry.remove_grade)

    def _init_list_ui(self, parent, item_name, get_func, add_func, remove_func):
        frame_add = ttk.Frame(parent, padding=10)
        frame_add.pack(fill=tk.X)
        
        ent = ttk.Entry(frame_add, width=30)
        ent.pack(side=tk.LEFT, padx=5)
        
        lb = tk.Listbox(parent, font=('Segoe UI', 10))
        lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def refresh():
            lb.delete(0, tk.END)
            for item in get_func():
                lb.insert(tk.END, item)
                
        def add():
            val = ent.get().strip()
            if val:
                add_func(val)
                ent.delete(0, tk.END)
                refresh()
                
        def remove():
            sel = lb.curselection()
            if sel:
                val = lb.get(sel[0])
                if messagebox.askyesno("Confirm", f"Delete '{val}'?"):
                    remove_func(val)
                    refresh()

        ttk.Button(frame_add, text=f"Add {item_name}", command=add).pack(side=tk.LEFT)
        ttk.Button(parent, text="Delete Selected", command=remove).pack(pady=10)
        
        # Initial load
        refresh()
