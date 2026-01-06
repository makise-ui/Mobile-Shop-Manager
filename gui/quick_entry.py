import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import datetime
from core.scraper import PhoneScraper

class QuickEntryScreen(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent)
        self.app = app_context
        self.scraper = PhoneScraper()
        
        # State Variables
        self.var_imei = tk.StringVar()
        self.var_model = tk.StringVar()
        self.var_ram = tk.StringVar()
        self.var_rom = tk.StringVar()
        self.var_price = tk.StringVar()
        self.var_color = tk.StringVar()
        self.var_supplier = tk.StringVar()
        
        self.var_grade = tk.StringVar()
        self.var_condition = tk.StringVar()
        
        # Toggles / Locks
        self.var_lock_supplier = tk.BooleanVar(value=False)
        self.var_lock_grade = tk.BooleanVar(value=False)
        self.var_auto_fetch = tk.BooleanVar(value=True)
        self.var_manual_model = tk.BooleanVar(value=False) # Manual Mode
        self.var_print_after_save = tk.BooleanVar(value=False)
        
        self.target_file_key = tk.StringVar()
        self.file_options = []
        
        self._init_ui()
        
    def _init_ui(self):
        # --- Top Bar: File & Settings ---
        top_bar = ttk.Frame(self, padding=10)
        top_bar.pack(fill=tk.X)
        
        ttk.Label(top_bar, text="Target File:", font=('bold')).pack(side=tk.LEFT)
        self.combo_file = ttk.Combobox(top_bar, textvariable=self.target_file_key, state="readonly", width=30)
        self.combo_file.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_bar, text="Refresh Files", command=self._refresh_files).pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(top_bar, text="Auto-Fetch Info (API)", variable=self.var_auto_fetch).pack(side=tk.RIGHT, padx=10)
        ttk.Checkbutton(top_bar, text="Manual Model Entry", variable=self.var_manual_model, command=self._toggle_model_entry).pack(side=tk.RIGHT, padx=10)

        # --- Main Form ---
        self.form_frame = ttk.LabelFrame(self, text="New Entry Details", padding=15)
        self.form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Grid Layout Helper
        r = 0
        def add_field(label, var, widget_cls=ttk.Entry, **kwargs):
            nonlocal r
            ttk.Label(self.form_frame, text=label).grid(row=r, column=0, sticky=tk.W, pady=5)
            w = widget_cls(self.form_frame, textvariable=var, **kwargs)
            w.grid(row=r, column=1, sticky=tk.EW, padx=5, pady=5)
            # Add Enter Key traversal
            w.bind('<Return>', lambda e: w.tk_focusNext().focus())
            return w, r
        
        # 1. IMEI
        lbl = ttk.Label(self.form_frame, text="IMEI / SN:")
        lbl.grid(row=r, column=0, sticky=tk.W, pady=5)
        self.ent_imei = ttk.Entry(self.form_frame, textvariable=self.var_imei, width=30, font=('Consolas', 11))
        self.ent_imei.grid(row=r, column=1, sticky=tk.EW, padx=5, pady=5)
        self.ent_imei.bind('<Return>', self._on_imei_enter) # Special Handler
        ttk.Button(self.form_frame, text="Fetch", command=self._fetch_info).grid(row=r, column=2, padx=5)
        r += 1
        
        # 2. Model
        lbl_mod = ttk.Label(self.form_frame, text="Model Name:")
        lbl_mod.grid(row=r, column=0, sticky=tk.W, pady=5)
        self.ent_model = ttk.Entry(self.form_frame, textvariable=self.var_model, state='readonly') # Default readonly
        self.ent_model.grid(row=r, column=1, sticky=tk.EW, padx=5, pady=5)
        r += 1

        # 3. Spec Row (RAM / ROM / Color)
        f_specs = ttk.Frame(self.form_frame)
        f_specs.grid(row=r, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(f_specs, text="RAM:").pack(side=tk.LEFT)
        ttk.Entry(f_specs, textvariable=self.var_ram, width=6).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(f_specs, text="ROM:").pack(side=tk.LEFT, padx=(10,0))
        ttk.Entry(f_specs, textvariable=self.var_rom, width=6).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(f_specs, text="Color:").pack(side=tk.LEFT, padx=(10,0))
        # Color Combo
        from core.data_registry import DataRegistry
        colors = DataRegistry().get_colors()
        cb_col = ttk.Combobox(f_specs, textvariable=self.var_color, values=colors, width=10)
        cb_col.pack(side=tk.LEFT, padx=5)
        r += 1

        # 4. Price & Supplier
        f_ps = ttk.Frame(self.form_frame)
        f_ps.grid(row=r, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(f_ps, text="Price:").pack(side=tk.LEFT)
        ttk.Entry(f_ps, textvariable=self.var_price, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(f_ps, text="Supplier:").pack(side=tk.LEFT, padx=(15,0))
        ttk.Entry(f_ps, textvariable=self.var_supplier, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(f_ps, text="🔒", variable=self.var_lock_supplier).pack(side=tk.LEFT)
        r += 1
        
        # 5. Grade & Condition
        f_gc = ttk.Frame(self.form_frame)
        f_gc.grid(row=r, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(f_gc, text="Grade:").pack(side=tk.LEFT)
        grades = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C", "D", "E"]
        ttk.Combobox(f_gc, textvariable=self.var_grade, values=grades, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(f_gc, text="🔒", variable=self.var_lock_grade).pack(side=tk.LEFT)
        
        ttk.Label(f_gc, text="Condition:").pack(side=tk.LEFT, padx=(15,0))
        ttk.Entry(f_gc, textvariable=self.var_condition, width=20).pack(side=tk.LEFT, padx=5)
        r += 1

        # --- Action Bar ---
        action_bar = ttk.Frame(self, padding=20)
        action_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(action_bar, text="SAVE ENTRY (Enter)", command=self._save_entry, style="Accent.TButton", width=20).pack(side=tk.RIGHT)
        ttk.Checkbutton(action_bar, text="Print Label after Save", variable=self.var_print_after_save).pack(side=tk.RIGHT, padx=15)
        
        self.lbl_status = ttk.Label(action_bar, text="Ready", foreground="gray")
        self.lbl_status.pack(side=tk.LEFT)

        # Configure Grid Weights
        self.form_frame.columnconfigure(1, weight=1)

    def on_show(self):
        self._refresh_files()
        self.ent_imei.focus_set()

    def _refresh_files(self):
        mappings = self.app.app_config.mappings
        self.file_options = list(mappings.keys())
        self.combo_file['values'] = self.file_options
        if self.file_options:
            if not self.target_file_key.get():
                self.combo_file.current(0)
        else:
            self.combo_file.set("No Configured Files")

    def _toggle_model_entry(self):
        if self.var_manual_model.get():
            self.ent_model.config(state='normal')
        else:
            self.ent_model.config(state='readonly')

    def _on_imei_enter(self, event):
        val = self.var_imei.get().strip()
        if not val: return
        
        if self.var_auto_fetch.get() and not self.var_manual_model.get():
            self._fetch_info()
        else:
            # Just move focus
            self.ent_model.focus_set()

    def _fetch_info(self):
        imei = self.var_imei.get().strip()
        if not imei: return
        
        self.lbl_status.config(text="Fetching info...", foreground="blue")
        self.update_idletasks()
        
        # Threading would be better, but blocking for now is safer for stability
        data = self.scraper.fetch_details(imei)
        
        if data.get("error"):
            self.lbl_status.config(text=f"Error: {data['error']}", foreground="red")
            if not self.var_manual_model.get():
                # Allow manual edit on failure
                if messagebox.askyesno("Fetch Failed", "Could not fetch details. Enable manual entry?"):
                    self.var_manual_model.set(True)
                    self._toggle_model_entry()
                    self.ent_model.focus_set()
        else:
            name = data.get("name", "")
            self.var_model.set(name)
            self.lbl_status.config(text="Details Fetched!", foreground="green")
            
            # Jump to Price/Specs
            self.ent_model.focus_set()
            # self.tk_focusNext().focus() # Or jump further

    def _save_entry(self):
        # Validate
        imei = self.var_imei.get().strip()
        model = self.var_model.get().strip()
        target = self.target_file_key.get()
        
        if not imei or not model:
            messagebox.showwarning("Missing Data", "IMEI and Model are required.")
            return
            
        if not target or target == "No Configured Files":
            messagebox.showwarning("Target File", "Please select a target Excel file.")
            return

        # Prepare Data
        # Combine RAM/ROM
        ram = self.var_ram.get().strip()
        rom = self.var_rom.get().strip()
        ram_rom = f"{ram}/{rom}" if ram and rom else (ram or rom)
        
        price = 0.0
        try:
            p_str = self.var_price.get().strip()
            if p_str: price = float(p_str)
        except: pass

        new_data = {
            "imei": imei,
            "model": model,
            "ram_rom": ram_rom,
            "color": self.var_color.get().strip(),
            "price_original": price,
            "supplier": self.var_supplier.get().strip(),
            "grade": self.var_grade.get().strip(),
            "condition": self.var_condition.get().strip(),
            "status": "IN", # Default
            "source_file": target
        }
        
        # 1. Update Registry (Create ID)
        uid = self.app.inventory.id_registry.get_or_create_id(new_data)
        new_data['unique_id'] = uid
        
        # 2. Append to Excel
        # We need a method in InventoryManager to "add_new_row".
        # Since _write_excel_generic updates existing, we need a slight variant or just append.
        # Actually, if we just add it to the DF and save?
        # NO, InventoryManager relies on reloading.
        
        # Let's implement a simple `add_item_to_file` in InventoryManager or helper.
        success = self._append_to_excel(target, new_data)
        
        if success:
            self.lbl_status.config(text=f"Saved ID: {uid}", foreground="green")
            
            # 3. Print?
            if self.var_print_after_save.get():
                self._print_label(new_data)
            
            # 4. Clear Fields (Respect Locks)
            self.var_imei.set("")
            self.var_model.set("")
            self.var_ram.set("")
            self.var_rom.set("")
            self.var_price.set("")
            self.var_color.set("")
            
            if not self.var_lock_supplier.get():
                self.var_supplier.set("")
            if not self.var_lock_grade.get():
                self.var_grade.set("")
                self.var_condition.set("")
                
            self.ent_imei.focus_set()
            
            # Reload inventory in background or next refresh
            # self.app.inventory.reload_all() # Might be slow
        else:
            messagebox.showerror("Error", "Failed to save to Excel file.")

    def _append_to_excel(self, file_key, data):
        # Determine Path and Sheet
        path = file_key
        sheet = 0
        if "::" in file_key:
            parts = file_key.split("::")
            path = parts[0]
            sheet = parts[1]
            
        # Get Mapping to convert Internal -> Column Name
        mapping_data = self.app.app_config.get_file_mapping(file_key)
        if not mapping_data: return False
        
        mapping = mapping_data.get('mapping', {})
        # Inverse mapping: Internal -> Col Name
        field_to_col = {v: k for k, v in mapping.items()}
        
        row_dict = {}
        for field, val in data.items():
            if field == 'price_original': field = 'price'
            if field in field_to_col:
                row_dict[field_to_col[field]] = val
        
        # Append using Pandas? Slow to load/save entire file.
        # Use openpyxl
        try:
            from openpyxl import load_workbook
            wb = load_workbook(path)
            
            ws = None
            if isinstance(sheet, str) and sheet in wb.sheetnames:
                ws = wb[sheet]
            else:
                ws = wb.active
                
            # Find Column Indices based on Headers (Row 1)
            col_map = {} # HeaderName -> ColIndex
            for cell in ws[1]:
                if cell.value:
                    col_map[str(cell.value).strip()] = cell.column
            
            # Find next empty row
            next_row = ws.max_row + 1
            
            for col_name, val in row_dict.items():
                if col_name in col_map:
                    ws.cell(row=next_row, column=col_map[col_name], value=val)
                else:
                    # Column doesn't exist? Create it?
                    # For now, skip or log
                    pass
            
            wb.save(path)
            return True
        except Exception as e:
            print(f"Append Error: {e}")
            return False

    def _print_label(self, item):
        # 1-up print for immediate entry
        # Use existing printer logic
        # Need to wrap item in list for ZPL generator
        
        printers = self.app.printer.get_system_printers()
        if not printers: return
        
        # Default to first or saved
        target = printers[0]
        
        # Construct ZPL
        zpl = self.app.printer.generate_zpl_2up([item]) # Logic is 2-up, but works for 1 if list is short?
        # Actually generate_zpl_2up puts 2 on one label.
        # If we print 1 item, it occupies left side.
        
        self.app.printer.send_raw_zpl(zpl, target)
