import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import datetime
import threading
import os
from pathlib import Path
from core.scraper import PhoneScraper

class QuickEntryScreen(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent)
        self.app = app_context
        self.scraper = PhoneScraper()
        
        # State Variables
        self.var_imei = tk.StringVar()
        self.var_model = tk.StringVar()
        self.var_ram_rom = tk.StringVar() # Combined
        self.var_price = tk.StringVar()
        self.var_color = tk.StringVar()
        self.var_supplier = tk.StringVar()
        
        self.var_grade = tk.StringVar()
        self.var_condition = tk.StringVar()
        
        # Toggles / Locks
        self.var_lock_supplier = tk.BooleanVar(value=False)
        self.var_lock_grade = tk.BooleanVar(value=False)
        self.var_lock_color = tk.BooleanVar(value=False) # New Color Lock
        self.var_auto_fetch = tk.BooleanVar(value=True)
        self.var_manual_model = tk.BooleanVar(value=False) # Manual Mode
        self.var_print_after_save = tk.BooleanVar(value=False)
        self.var_batch_mode = tk.BooleanVar(value=False) # Batch Mode Toggle
        
        self.target_file_key = tk.StringVar()
        self.file_options = []
        self.batch_rows = [] # Store widget references for batch items
        
        self._init_ui()
        
        # Shortcuts
        self.bind_all("<Control-Return>", lambda e: self._focus_batch_start(), add='+')
        
    def focus_primary(self):
        self.ent_imei.focus_set()

    def _init_ui(self):
        # --- Top Bar: File & Settings ---
        top_bar = ttk.Frame(self, padding=10)
        top_bar.pack(fill=tk.X)
        
        ttk.Label(top_bar, text="Target File:", font=('bold')).pack(side=tk.LEFT)
        self.combo_file = ttk.Combobox(top_bar, textvariable=self.target_file_key, state="readonly", width=25)
        self.combo_file.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_bar, text="+ New", command=self._create_new_file, width=6).pack(side=tk.LEFT)
        ttk.Button(top_bar, text="Refresh", command=self._refresh_files).pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(top_bar, text="Auto-Fetch (Bg)", variable=self.var_auto_fetch).pack(side=tk.RIGHT, padx=10)
        ttk.Checkbutton(top_bar, text="Manual Model", variable=self.var_manual_model, command=self._toggle_model_entry).pack(side=tk.RIGHT, padx=10)
        ttk.Checkbutton(top_bar, text="Batch Mode", variable=self.var_batch_mode, command=self._toggle_batch_mode, bootstyle="round-toggle").pack(side=tk.RIGHT, padx=10)

        # --- Main Form (Single Entry) ---
        self.form_frame = ttk.LabelFrame(self, text="New Entry Details", padding=15)
        # We pack/unpack this based on mode
        
        # --- Batch Frame (Hidden by default) ---
        self.batch_container = ttk.Frame(self)
        
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
        ttk.Button(self.form_frame, text="Fetch Now", command=lambda: self._fetch_info_bg(self.var_imei.get())).grid(row=r, column=2, padx=5)
        r += 1
        
        # 2. Model
        lbl_mod = ttk.Label(self.form_frame, text="Model Name:")
        lbl_mod.grid(row=r, column=0, sticky=tk.W, pady=5)
        self.ent_model = ttk.Entry(self.form_frame, textvariable=self.var_model, state='readonly') # Default readonly
        self.ent_model.grid(row=r, column=1, sticky=tk.EW, padx=5, pady=5)
        r += 1

        # 3. Spec Row (RAM/ROM / Color)
        f_specs = ttk.Frame(self.form_frame)
        f_specs.grid(row=r, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(f_specs, text="RAM/ROM:").pack(side=tk.LEFT)
        self.ent_ram_rom = ttk.Entry(f_specs, textvariable=self.var_ram_rom, width=15)
        self.ent_ram_rom.pack(side=tk.LEFT, padx=5)
        self.ent_ram_rom.bind('<Return>', lambda e: self.cb_col.focus_set())
        
        ttk.Label(f_specs, text="Color:").pack(side=tk.LEFT, padx=(10,0))
        # Color Combo
        from core.data_registry import DataRegistry
        colors = DataRegistry().get_colors()
        self.cb_col = ttk.Combobox(f_specs, textvariable=self.var_color, values=colors, width=15)
        self.cb_col.pack(side=tk.LEFT, padx=5)
        self.cb_col.bind('<Return>', lambda e: self.ent_price.focus_set())
        ttk.Checkbutton(f_specs, text="🔒", variable=self.var_lock_color).pack(side=tk.LEFT)
        r += 1

        # 4. Price & Supplier
        f_ps = ttk.Frame(self.form_frame)
        f_ps.grid(row=r, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(f_ps, text="Price:").pack(side=tk.LEFT)
        self.ent_price = ttk.Entry(f_ps, textvariable=self.var_price, width=10)
        self.ent_price.pack(side=tk.LEFT, padx=5)
        self.ent_price.bind('<Return>', lambda e: self.ent_supplier.focus_set())
        
        ttk.Label(f_ps, text="Supplier:").pack(side=tk.LEFT, padx=(15,0))
        self.ent_supplier = ttk.Entry(f_ps, textvariable=self.var_supplier, width=15)
        self.ent_supplier.pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(f_ps, text="🔒", variable=self.var_lock_supplier).pack(side=tk.LEFT)
        self.ent_supplier.bind('<Return>', lambda e: self.cb_grade.focus_set())
        r += 1
        
        # 5. Grade & Condition
        f_gc = ttk.Frame(self.form_frame)
        f_gc.grid(row=r, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(f_gc, text="Grade:").pack(side=tk.LEFT)
        grades = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C", "D", "E"]
        self.cb_grade = ttk.Combobox(f_gc, textvariable=self.var_grade, values=grades, width=5)
        self.cb_grade.pack(side=tk.LEFT, padx=5)
        self.cb_grade.bind('<Return>', lambda e: self.ent_cond.focus_set())
        ttk.Checkbutton(f_gc, text="🔒", variable=self.var_lock_grade).pack(side=tk.LEFT)
        
        ttk.Label(f_gc, text="Condition:").pack(side=tk.LEFT, padx=(15,0))
        self.ent_cond = ttk.Entry(f_gc, textvariable=self.var_condition, width=20)
        self.ent_cond.pack(side=tk.LEFT, padx=5)
        self.ent_cond.bind('<Return>', lambda e: self._save_entry()) # Enter on last field saves
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

    def _toggle_batch_mode(self):
        if self.var_batch_mode.get():
            # Switch to Batch
            self.form_frame.pack_forget()
            self.batch_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            self._setup_batch_ui()
            self.ent_batch_scan.focus_set()
        else:
            # Switch to Single
            self.batch_container.pack_forget()
            self.form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            self.ent_imei.focus_set()

    def _setup_batch_ui(self):
        # Clear existing
        for w in self.batch_container.winfo_children(): w.destroy()
        self.batch_rows = []
        
        # 1. Scan Header
        f_scan = ttk.Frame(self.batch_container)
        f_scan.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(f_scan, text="Batch Scan IMEI:", font=('bold')).pack(side=tk.LEFT)
        self.var_batch_scan = tk.StringVar()
        self.ent_batch_scan = ttk.Entry(f_scan, textvariable=self.var_batch_scan, width=30, font=('Consolas', 12))
        self.ent_batch_scan.pack(side=tk.LEFT, padx=10)
        self.ent_batch_scan.bind('<Return>', self._on_imei_enter)
        
        ttk.Label(f_scan, text="(Press Ctrl+N to stop scanning and edit list)", foreground="gray").pack(side=tk.LEFT, padx=10)
        
        # 2. Scrollable List
        canvas = tk.Canvas(self.batch_container)
        scrollbar = ttk.Scrollbar(self.batch_container, orient="vertical", command=canvas.yview)
        self.batch_list_frame = ttk.Frame(canvas)
        
        self.batch_list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.batch_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Headers
        headers = ["IMEI", "Model Name", "RAM/ROM", "Color", "Price"]
        f_head = ttk.Frame(self.batch_list_frame)
        f_head.pack(fill=tk.X, pady=2)
        for i, h in enumerate(headers):
             w = 30 if i == 1 else 15
             ttk.Label(f_head, text=h, width=w, font=('bold')).pack(side=tk.LEFT, padx=2)

    def _add_batch_row(self, imei):
        # Create Row Widgets
        row_frame = ttk.Frame(self.batch_list_frame)
        row_frame.pack(fill=tk.X, pady=2)
        
        # Data Vars
        v_imei = tk.StringVar(value=imei)
        v_model = tk.StringVar(value="Fetching..." if self.var_auto_fetch.get() else "")
        v_rr = tk.StringVar(value=self.var_ram_rom.get()) # Inherit from single form (optional)
        v_col = tk.StringVar(value=self.var_color.get() if self.var_lock_color.get() else "")
        v_price = tk.StringVar(value=self.var_price.get())
        
        # Widgets
        e_imei = ttk.Entry(row_frame, textvariable=v_imei, width=15, state='readonly')
        e_imei.pack(side=tk.LEFT, padx=2)
        
        e_model = ttk.Entry(row_frame, textvariable=v_model, width=30)
        e_model.pack(side=tk.LEFT, padx=2)
        
        e_rr = ttk.Entry(row_frame, textvariable=v_rr, width=15)
        e_rr.pack(side=tk.LEFT, padx=2)
        
        e_col = ttk.Entry(row_frame, textvariable=v_col, width=15)
        e_col.pack(side=tk.LEFT, padx=2)
        
        e_price = ttk.Entry(row_frame, textvariable=v_price, width=15)
        e_price.pack(side=tk.LEFT, padx=2)
        
        # Store for logic
        row_data = {
            "vars": (v_imei, v_model, v_rr, v_col, v_price),
            "widgets": (e_imei, e_model, e_rr, e_col, e_price)
        }
        self.batch_rows.append(row_data)
        
        # Key Nav: Enter on Model -> Next Row's Model
        curr_idx = len(self.batch_rows) - 1
        def focus_next(idx):
            if idx + 1 < len(self.batch_rows):
                self.batch_rows[idx+1]["widgets"][1].focus_set() # Next Model
            else:
                self.ent_batch_scan.focus_set() # Back to scan
        
        e_model.bind('<Return>', lambda e, i=curr_idx: focus_next(i))
        
        # Trigger Fetch
        if self.var_auto_fetch.get():
             self._fetch_info_bg(imei, row_data)

    def _focus_batch_start(self):
        if not self.var_batch_mode.get() or not self.batch_rows:
            return
        # Focus first row model
        self.batch_rows[0]["widgets"][1].focus_set()

    def _toggle_model_entry(self):
        if self.var_manual_model.get():
            self.ent_model.config(state='normal')
        else:
            self.ent_model.config(state='readonly')

    def _on_imei_enter(self, event):
        # Determine Source Widget
        is_batch = self.var_batch_mode.get()
        if is_batch:
            val = self.var_batch_scan.get().strip()
            self.var_batch_scan.set("") # Clear immediately
        else:
            val = self.var_imei.get().strip()
            
        if not val: return
        
        is_real_imei = val.isdigit()
        
        if not is_real_imei:
             if not is_batch:
                self.var_manual_model.set(True)
                self._toggle_model_entry()
                self.ent_model.focus_set()
             return

        if is_batch:
            self._add_batch_row(val)
            # Keep focus on scan
            self.ent_batch_scan.focus_set()
        else:
            # Single Mode Logic
            self.ent_ram_rom.focus_set()
            if self.var_auto_fetch.get() and not self.var_manual_model.get():
                self._fetch_info_bg(val)

    def _fetch_info_bg(self, imei, batch_row=None):
        if not batch_row:
             self.lbl_status.config(text="Fetching info...", foreground="blue")
        
        def run():
            data = self.scraper.fetch_details(imei)
            self.after(0, lambda: self._on_fetch_complete(data, batch_row))
            
        threading.Thread(target=run, daemon=True).start()

    def _on_fetch_complete(self, data, batch_row=None):
        name = data.get("name", "")
        
        if batch_row:
            # Update Batch Row
            v_model = batch_row["vars"][1]
            if name:
                v_model.set(name)
            else:
                v_model.set("Not Found")
        else:
            # Update Single Form
            if data.get("error"):
                self.lbl_status.config(text=f"Fetch Error: {data['error']}", foreground="red")
            else:
                if name:
                    self.var_model.set(name)
                    self.lbl_status.config(text="Details Fetched!", foreground="green")
                else:
                    self.lbl_status.config(text="Model not found.", foreground="orange")

    def _create_new_file(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            title="Create New Inventory File",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialdir=self.app.app_config.get('output_folder', '.')
        )
        if not path: return
        
        if os.path.exists(path):
            messagebox.showerror("Error", "File already exists!")
            return
            
        # Create Empty Excel with standard headers
        try:
            headers = ["S.NO", "SUPPLIER", "MODEL NAME", "RAM/ROM", "IMEI NO", "RATE", "STATUS", "BUYERS", "COLOR", "GRADE", "CONDITION"]
            df = pd.DataFrame(columns=headers)
            df.to_excel(path, index=False)
            
            # Add to mapping
            mapping = {
                "SUPPLIER": "supplier",
                "MODEL NAME": "model",
                "RAM/ROM": "ram_rom",
                "IMEI NO": "imei",
                "RATE": "price",
                "STATUS": "status",
                "BUYERS": "buyer",
                "COLOR": "color",
                "GRADE": "grade",
                "CONDITION": "condition"
            }
            save_data = {
                "file_path": path,
                "mapping": mapping,
                "supplier": "",
                "sheet_name": "Sheet1"
            }
            self.app.app_config.set_file_mapping(path, save_data)
            
            # Refresh
            self._refresh_files()
            self.target_file_key.set(path)
            messagebox.showinfo("Success", f"Created {os.path.basename(path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create file: {e}")

    def _save_entry(self):
        target = self.target_file_key.get()
        if not target or target == "No Configured Files":
            messagebox.showwarning("Target File", "Please select a target Excel file.")
            return

        # --- BATCH MODE SAVE ---
        if self.var_batch_mode.get():
            if not self.batch_rows:
                return
            
            saved_count = 0
            for row_data in self.batch_rows:
                # Extract values from row variables
                vars = row_data["vars"] # (imei, model, rr, col, price)
                
                imei = vars[0].get().strip()
                model = vars[1].get().strip()
                
                # Skip invalid rows
                if not imei or not model or model == "Fetching...":
                    continue
                    
                price = 0.0
                try:
                    if vars[4].get(): price = float(vars[4].get())
                except: pass
                
                new_data = {
                    "imei": imei,
                    "model": model,
                    "ram_rom": vars[2].get().strip(),
                    "color": vars[3].get().strip(),
                    "price_original": price,
                    "supplier": self.var_supplier.get().strip(), # Use shared supplier
                    "grade": self.var_grade.get().strip(),       # Use shared grade
                    "condition": self.var_condition.get().strip(), # Use shared condition
                    "status": "IN",
                    "source_file": target
                }
                
                # Create ID
                uid = self.app.inventory.id_registry.get_or_create_id(new_data)
                new_data['unique_id'] = uid
                
                # Save
                if self._append_to_excel(target, new_data):
                    saved_count += 1
                    # Print if enabled
                    if self.var_print_after_save.get():
                        self._print_label(new_data)
            
            if saved_count > 0:
                messagebox.showinfo("Batch Save", f"Successfully saved {saved_count} items.")
                # Clear Batch UI
                for w in self.batch_list_frame.winfo_children():
                    if isinstance(w, ttk.Frame) and w != self.batch_list_frame: # Skip self
                         # Actually winfo_children returns children widgets. 
                         # Headers are labels directly in batch_list_frame? No, check _setup_batch_ui
                         # Headers are in f_head which is packed. Rows are row_frame which are packed.
                         pass
                         
                # Re-setup UI to clear
                self._setup_batch_ui()
                self.ent_batch_scan.focus_set()
            else:
                messagebox.showwarning("Save Failed", "No valid items to save.")
            return

        # --- SINGLE ENTRY SAVE ---
        # Validate
        imei = self.var_imei.get().strip()
        model = self.var_model.get().strip()
        
        if not imei or not model:
            messagebox.showwarning("Missing Data", "IMEI and Model are required.")
            self.ent_imei.focus_set()
            return

        # Prepare Data
        price = 0.0
        try:
            p_str = self.var_price.get().strip()
            if p_str: price = float(p_str)
        except: pass

        new_data = {
            "imei": imei,
            "model": model,
            "ram_rom": self.var_ram_rom.get().strip(),
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
        success = self._append_to_excel(target, new_data)
        
        if success:
            self.lbl_status.config(text=f"Saved ID: {uid}", foreground="green")
            
            # 3. Print?
            if self.var_print_after_save.get():
                self._print_label(new_data)
            
            # 4. Clear Fields (Respect Locks)
            self.var_imei.set("")
            self.var_model.set("")
            self.var_ram_rom.set("")
            self.var_price.set("")
            # Respect Color Lock check
            if not self.var_lock_color.get():
                self.var_color.set("")
            
            if not self.var_lock_supplier.get():
                self.var_supplier.set("")
            if not self.var_lock_grade.get():
                self.var_grade.set("")
                self.var_condition.set("")
                
            self.ent_imei.focus_set()
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
            
        # Get Mapping
        mapping_data = self.app.app_config.get_file_mapping(file_key)
        if not mapping_data: return False
        
        mapping = mapping_data.get('mapping', {})
        field_to_col = {v: k for k, v in mapping.items()}
        
        row_dict = {}
        for field, val in data.items():
            if field == 'price_original': field = 'price'
            if field in field_to_col:
                row_dict[field_to_col[field]] = val
        
        try:
            from openpyxl import load_workbook
            wb = load_workbook(path)
            
            ws = None
            if isinstance(sheet, str) and sheet in wb.sheetnames:
                ws = wb[sheet]
            else:
                ws = wb.active
                
            # Find Column Indices
            col_map = {}
            for cell in ws[1]:
                if cell.value:
                    col_map[str(cell.value).strip()] = cell.column
            
            # Find next empty row
            next_row = ws.max_row + 1
            
            from openpyxl.styles import Font, Alignment, Border, Side
            thin = Side(border_style="thin", color="000000")
            border = Border(top=thin, left=thin, right=thin, bottom=thin)
            font = Font(name='Times New Roman', size=11, bold=True)
            align = Alignment(horizontal='center', vertical='center')

            for col_name, val in row_dict.items():
                if col_name in col_map:
                    # Enforce FULL CAPS for strings
                    if isinstance(val, str):
                        val = val.upper()
                        
                    cell = ws.cell(row=next_row, column=col_map[col_name], value=val)
                    cell.font = font
                    cell.border = border
                    cell.alignment = align
            
            wb.save(path)
            return True
        except Exception as e:
            print(f"Append Error: {e}")
            return False

    def _print_label(self, item):
        printers = self.app.printer.get_system_printers()
        if not printers: return
        target = printers[0]
        zpl = self.app.printer.generate_zpl_2up([item]) 
        self.app.printer.send_raw_zpl(zpl, target)
