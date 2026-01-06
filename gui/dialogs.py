import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os

class MapColumnsDialog(tk.Toplevel):
    def __init__(self, parent, file_path, on_save_callback, current_mapping=None):
        super().__init__(parent)
        self.title("Map Columns")
        self.geometry("600x700") # Taller, slightly narrower
        self.file_path = file_path
        self.on_save = on_save_callback
        self.current_mapping = current_mapping or {}
        
        self.mappings = {}
        # Added 'grade', 'condition' to default fields
        self.canonical_fields = ['imei', 'model', 'ram_rom', 'price', 'supplier', 'notes', 'status', 'color', 'buyer', 'buyer_contact', 'grade', 'condition']
        
        self.sheet_names = []
        self.current_sheet = None
        self.df = pd.DataFrame()
        self.headers = []

        # Load Sheet Names if Excel
        try:
            if file_path.endswith('.csv'):
                self.sheet_names = ["Default"]
                self._load_data(None)
            else:
                xl = pd.ExcelFile(file_path)
                self.sheet_names = xl.sheet_names
                saved_sheet = self.current_mapping.get('sheet_name')
                if saved_sheet and saved_sheet in self.sheet_names:
                    self._load_data(saved_sheet)
                else:
                    self._load_data(self.sheet_names[0])
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")
            self.destroy()
            return

        self._init_ui()

    def _load_data(self, sheet_name):
        self.current_sheet = sheet_name
        try:
            if self.file_path.endswith('.csv'):
                self.df = pd.read_csv(self.file_path, nrows=5)
            else:
                self.df = pd.read_excel(self.file_path, sheet_name=sheet_name, nrows=5)
            self.headers = [str(c) for c in self.df.columns]
        except Exception as e:
            messagebox.showerror("Error", f"Error loading data: {e}")

    def _init_ui(self):
        # 1. Header Frame (Fixed)
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        
        ttk.Label(header_frame, text=f"File: {os.path.basename(self.file_path)}", font=('bold')).pack(anchor=tk.W)
        
        if len(self.sheet_names) > 1 or not self.file_path.endswith('.csv'):
            f_sheet = ttk.Frame(header_frame)
            f_sheet.pack(fill=tk.X, pady=5)
            ttk.Label(f_sheet, text="Select Sheet:").pack(side=tk.LEFT)
            self.combo_sheet = ttk.Combobox(f_sheet, values=self.sheet_names, state="readonly")
            if self.current_sheet: self.combo_sheet.set(self.current_sheet)
            else: self.combo_sheet.current(0)
            self.combo_sheet.pack(side=tk.LEFT, padx=10)
            self.combo_sheet.bind("<<ComboboxSelected>>", self._on_sheet_change)

        ttk.Button(header_frame, text="Preview Data", command=self._show_preview).pack(anchor=tk.W, pady=5)

        # 2. Buttons Frame (Fixed at Bottom)
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(btn_frame, text="Save Mapping", command=self._on_save, style="Accent.TButton").pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        # 3. Main Content (Scrollable)
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10)
        
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.combos = {}
        self._render_mapping_ui()
        
        # 4. Supplier Override (Inside Scrollable or Fixed? Fixed is better for visibility)
        # Moving Supplier to Header for easier access
        f_supp = ttk.Frame(header_frame)
        f_supp.pack(fill=tk.X, pady=5)
        ttk.Label(f_supp, text="Default Supplier:").pack(side=tk.LEFT)
        self.ent_supplier = ttk.Entry(f_supp)
        if self.current_mapping:
            self.ent_supplier.insert(0, self.current_mapping.get('supplier', ''))
        self.ent_supplier.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def _render_mapping_ui(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Headers
        ttk.Label(self.scrollable_frame, text="Internal Field (App)", font=('bold')).grid(row=0, column=0, padx=5, pady=10, sticky=tk.W)
        ttk.Label(self.scrollable_frame, text="Excel Column", font=('bold')).grid(row=0, column=1, padx=5, pady=10, sticky=tk.W)

        existing_map = {}
        if self.current_mapping and 'mapping' in self.current_mapping:
            for k, v in self.current_mapping['mapping'].items():
                existing_map[v] = k

        # Rows
        for idx, field in enumerate(self.canonical_fields):
            row = idx + 1
            # Clean Label (e.g. 'ram_rom' -> 'RAM / ROM')
            clean_label = field.replace('_', ' ').upper()
            ttk.Label(self.scrollable_frame, text=clean_label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            
            combo = ttk.Combobox(self.scrollable_frame, values=["(Ignore)"] + self.headers, width=30)
            
            if field in existing_map and existing_map[field] in self.headers:
                combo.set(existing_map[field])
            else:
                combo.current(0)
                self._auto_suggest(field, combo)
                
            combo.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=5)
            self.combos[field] = combo

    def _on_sheet_change(self, event):
        new_sheet = self.combo_sheet.get()
        if new_sheet != self.current_sheet:
            self._load_data(new_sheet)
            self._render_mapping_ui()

    def _show_preview(self):
        top = tk.Toplevel(self)
        top.title(f"Preview: {self.current_sheet}")
        top.geometry("800x400")
        
        frame = ttk.Frame(top)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tv = ttk.Treeview(frame, show='headings')
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tv.xview)
        tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        tv.pack(fill=tk.BOTH, expand=True)
        
        tv['columns'] = self.headers
        for h in self.headers:
            tv.heading(h, text=h)
            tv.column(h, width=100)
            
        for _, row in self.df.iterrows():
            vals = [str(x) for x in row.tolist()]
            tv.insert('', tk.END, values=vals)

    def _auto_suggest(self, field, combo):
        # Improved suggestion logic
        field_map = {
            'imei': ['imei', 'serial', 'sn'],
            'model': ['model', 'item', 'product'],
            'price': ['price', 'rate', 'cost', 'mop'],
            'supplier': ['supplier', 'vendor'],
            'grade': ['grade', 'quality'],
            'condition': ['condition', 'status']
        }
        
        targets = field_map.get(field, [field])
        
        for header in self.headers:
            h_lower = header.lower()
            for t in targets:
                if t in h_lower:
                    combo.set(header)
                    return

    def _on_save(self):
        final_mapping = {}
        for field, combo in self.combos.items():
            val = combo.get()
            if val and val != "(Ignore)":
                final_mapping[val] = field 
        
        save_data = {
            "file_path": self.file_path,
            "mapping": final_mapping,
            "supplier": self.ent_supplier.get(),
            "sheet_name": self.current_sheet
        }
        
        key = self.file_path
        if self.current_sheet and self.current_sheet != "Default":
             key = f"{self.file_path}::{self.current_sheet}"
        
        self.on_save(key, save_data)
        self.destroy()

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.app_config = config_manager
        self.title("Settings")
        self.geometry("400x300")
        
        self._init_ui()
        
    def _init_ui(self):
        frame = ttk.LabelFrame(self, text="General", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Label Size
        ttk.Label(frame, text="Label Width (mm):").grid(row=0, column=0)
        self.ent_w = ttk.Entry(frame)
        self.ent_w.insert(0, str(self.app_config.get('label_width_mm')))
        self.ent_w.grid(row=0, column=1)
        
        ttk.Label(frame, text="Label Height (mm):").grid(row=1, column=0)
        self.ent_h = ttk.Entry(frame)
        self.ent_h.insert(0, str(self.app_config.get('label_height_mm')))
        self.ent_h.grid(row=1, column=1)
        
        # Store Name
        ttk.Label(frame, text="Store Name:").grid(row=2, column=0)
        self.ent_store = ttk.Entry(frame)
        self.ent_store.insert(0, self.app_config.get('store_name'))
        self.ent_store.grid(row=2, column=1)

        btn = ttk.Button(self, text="Save", command=self._save)
        btn.pack(pady=10)

    def _save(self):
        try:
            self.app_config.set('label_width_mm', float(self.ent_w.get()))
            self.app_config.set('label_height_mm', float(self.ent_h.get()))
            self.app_config.set('store_name', self.ent_store.get())
            messagebox.showinfo("Saved", "Settings saved.")
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values")
from PIL import Image, ImageDraw, ImageFont, ImageTk

class ZPLPreviewDialog(tk.Toplevel):
    def __init__(self, parent, items, on_confirm):
        super().__init__(parent)
        self.title("Print Preview (2-Up)")
        self.geometry("800x500")
        self.items = items
        self.on_confirm = on_confirm
        
        self.page_index = 0
        self.pairs = []
        for i in range(0, len(items), 2):
            pair = [items[i]]
            if i+1 < len(items):
                pair.append(items[i+1])
            self.pairs.append(pair)
            
        self._init_ui()
        self._show_page()

    def _init_ui(self):
        # Toolbar
        frame_top = ttk.Frame(self)
        frame_top.pack(fill=tk.X, pady=5)
        
        ttk.Button(frame_top, text="<< Prev", command=self._prev).pack(side=tk.LEFT, padx=10)
        self.lbl_page = ttk.Label(frame_top, text="Page 1")
        self.lbl_page.pack(side=tk.LEFT)
        ttk.Button(frame_top, text="Next >>", command=self._next).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(frame_top, text="PRINT ALL", command=self._print, style="Accent.TButton").pack(side=tk.RIGHT, padx=20)
        
        # Canvas for Image
        self.panel = ttk.Label(self)
        self.panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _prev(self):
        if self.page_index > 0:
            self.page_index -= 1
            self._show_page()

    def _next(self):
        if self.page_index < len(self.pairs) - 1:
            self.page_index += 1
            self._show_page()

    def _show_page(self):
        self.lbl_page.config(text=f"Page {self.page_index + 1} of {len(self.pairs)}")
        pair = self.pairs[self.page_index]
        
        # Simulate 2-Up Label (104mm x 22mm approx) -> 832x176 dots
        # Scale up for visibility
        scale = 2
        w, h = 832, 176
        img = Image.new('RGB', (w, h), 'white')
        draw = ImageDraw.Draw(img)
        
        # Draw Separator
        draw.line([(416, 0), (416, h)], fill='lightgrey', width=2)
        
        def draw_label(item, offset_x):
            # Simulation of ZPL layout
            # Header
            draw.text((offset_x + 150, 10), "4bros mobile", fill='black') # Approx center
            # Barcode (Rectangle placeholder)
            draw.rectangle([(offset_x + 100, 40), (offset_x + 300, 80)], outline='black', width=2)
            draw.text((offset_x + 180, 55), "||||||||", fill='black')
            # ID
            draw.text((offset_x + 180, 85), str(item.get('unique_id', '')), fill='black')
            # Model
            draw.text((offset_x + 10, 110), str(item.get('model', ''))[:25], fill='black')
            # RAM
            draw.text((offset_x + 10, 140), str(item.get('ram_rom', '')), fill='black')
            # Price
            draw.text((offset_x + 300, 135), f"Rs.{item.get('price', 0):.0f}", fill='black')

        draw_label(pair[0], 0)
        if len(pair) > 1:
            draw_label(pair[1], 416)
            
        # Resize for display
        img_disp = img.resize((w*scale, h*scale), Image.Resampling.NEAREST)
        self.photo = ImageTk.PhotoImage(img_disp)
        self.panel.config(image=self.photo)

    def _print(self):
        self.destroy()
        self.on_confirm()

class PrinterSelectionDialog(tk.Toplevel):
    def __init__(self, parent, printer_list, on_select):
        super().__init__(parent)
        self.title("Select Printer")
        self.geometry("400x150")
        self.printer_list = printer_list
        self.on_select = on_select
        
        self._init_ui()
        
    def _init_ui(self):
        ttk.Label(self, text="Choose a printer for the invoice:", font=('Segoe UI', 10)).pack(pady=10)
        
        self.combo = ttk.Combobox(self, values=self.printer_list, state="readonly", width=40)
        if self.printer_list:
            self.combo.current(0)
        self.combo.pack(pady=5, padx=20)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=15)
        
        ttk.Button(btn_frame, text="Print", command=self._confirm).pack(side=tk.RIGHT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=10)

    def _confirm(self):
        sel = self.combo.get()
        if sel:
            self.destroy()
            self.on_select(sel)
        else:
            messagebox.showwarning("Warning", "Please select a printer.")

class FileSelectionDialog(tk.Toplevel):
    def __init__(self, parent, file_list, title, on_confirm):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.file_list = file_list
        self.on_confirm = on_confirm
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        self._init_ui()
        self.focus_set()
        
    def _init_ui(self):
        ttk.Label(self, text="Select a file:", font=('Segoe UI', 10)).pack(pady=10)
        
        self.combo = ttk.Combobox(self, values=self.file_list, state="readonly", width=40)
        if self.file_list:
            self.combo.current(0)
        self.combo.pack(pady=5, padx=20)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=15)
        
        ttk.Button(btn_frame, text="OK", command=self._ok).pack(side=tk.RIGHT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=10)

    def _ok(self):
        sel = self.combo.get()
        if sel:
            self.destroy()
            self.on_confirm(sel)
        else:
            messagebox.showwarning("Warning", "Please select a file.")

class ItemSelectionDialog(tk.Toplevel):
    def __init__(self, parent, items, on_select):
        super().__init__(parent)
        self.title("Select Item")
        self.geometry("600x400")
        self.items = items
        self.on_select = on_select
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        self._init_ui()
        self.focus_set()
        
    def _init_ui(self):
        ttk.Label(self, text="Multiple items found. Please select one:", font=('Segoe UI', 10, 'bold')).pack(pady=10)
        
        # Tree
        cols = ('id', 'imei', 'model', 'price')
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('imei', text='IMEI')
        self.tree.heading('model', text='Model')
        self.tree.heading('price', text='Price')
        
        self.tree.column('id', width=60)
        self.tree.column('imei', width=120)
        self.tree.column('model', width=200)
        self.tree.column('price', width=80)
        
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate safe
        self.item_map = {}
        first_iid = None
        
        for item in self.items:
            # Let Treeview generate IID to avoid 'Item already exists' if duplicates passed
            iid = self.tree.insert('', tk.END, values=(
                item.get('unique_id', ''),
                item.get('imei', ''),
                item.get('model', ''),
                f"{item.get('price', 0):.2f}"
            ))
            self.item_map[iid] = item
            if not first_iid: first_iid = iid
            
        # Auto-select first
        if first_iid:
            self.tree.selection_set(first_iid)
            self.tree.focus(first_iid)
            
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Select", command=self._confirm).pack(side=tk.RIGHT, padx=20)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)
        
        self.tree.bind("<Double-1>", lambda e: self._confirm())
        self.bind("<Return>", lambda e: self._confirm())

    def _confirm(self):
        sel = self.tree.selection()
        if not sel: return
        
        iid = sel[0]
        item = self.item_map.get(iid)
        if item:
            self.destroy()
            self.on_select(item)

class ConflictResolutionDialog(tk.Toplevel):
    def __init__(self, parent, conflict_data, on_resolve):
        super().__init__(parent)
        self.title("Data Conflict Detected")
        self.geometry("600x450")
        self.conflict = conflict_data
        self.on_resolve = on_resolve
        self.result = None
        
        self._init_ui()
        
    def _init_ui(self):
        ttk.Label(self, text="Conflict: Duplicate IMEI Found", font=('Segoe UI', 12, 'bold'), foreground='red').pack(pady=10)
        
        info_frame = ttk.LabelFrame(self, text="Item Details", padding=10)
        info_frame.pack(fill=tk.X, padx=10)
        
        ttk.Label(info_frame, text=f"IMEI: {self.conflict['imei']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Model: {self.conflict['model']}").pack(anchor=tk.W)
        
        ttk.Label(self, text="Found in multiple files:", font=('Segoe UI', 10, 'bold')).pack(pady=(10,5), anchor=tk.W, padx=10)
        
        # Sources List
        self.lb = tk.Listbox(self, height=5)
        self.lb.pack(fill=tk.X, padx=10)
        
        for src in self.conflict['sources']:
            self.lb.insert(tk.END, src)
            
        ttk.Label(self, text="Action Required:", font=('Segoe UI', 10, 'bold')).pack(pady=(10,5), anchor=tk.W, padx=10)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # Options
        ttk.Button(btn_frame, text="Keep All (Merge)", command=self._merge).pack(side=tk.LEFT, padx=20, expand=True)
        # ttk.Button(btn_frame, text="Keep One (Ignore Others)", command=self._keep_one).pack(side=tk.LEFT, padx=20, expand=True) # Logic too complex for now
        ttk.Button(btn_frame, text="Ignore Warning", command=self.destroy).pack(side=tk.RIGHT, padx=20, expand=True)
        
    def _merge(self):
        self.on_resolve(self.conflict, 'merge')
        self.destroy()

    def _keep_one(self):
        # Determine which one to keep?
        # For now let's just support Merge or Ignore
        pass

class SplashScreen(tk.Toplevel):
    def __init__(self, parent, store_name):
        super().__init__(parent)
        self.title("Welcome")
        self.geometry("500x300")
        self.overrideredirect(True) # No title bar
        
        # Center on screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w // 2) - 250
        y = (screen_h // 2) - 150
        self.geometry(f"+{x}+{y}")
        
        self.configure(bg='#2c3e50')
        
        frame = tk.Frame(self, bg='#2c3e50', bd=5, relief=tk.RAISED)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="WELCOME TO", font=('Segoe UI', 12), bg='#2c3e50', fg='white').pack(pady=(50, 5))
        tk.Label(frame, text=store_name.upper(), font=('Segoe UI', 24, 'bold'), bg='#2c3e50', fg='#007acc').pack(pady=5)
        tk.Label(frame, text="Management System", font=('Segoe UI', 10), bg='#2c3e50', fg='lightgray').pack(pady=5)
        
        tk.Label(frame, text="Loading inventory and settings...", font=('Segoe UI', 8, 'italic'), bg='#2c3e50', fg='gray').pack(side=tk.BOTTOM, pady=20)
        
        self.update()

class WelcomeDialog(tk.Toplevel):
    def __init__(self, parent, on_choice):
        super().__init__(parent)
        self.title("Welcome - Getting Started")
        self.geometry("500x400")
        self.on_choice = on_choice
        
        # Center
        self.transient(parent)
        self.grab_set()
        
        self._init_ui()
        
    def _init_ui(self):
        ttk.Label(self, text="Welcome to 4Bros Manager!", font=('Segoe UI', 16, 'bold')).pack(pady=20)
        ttk.Label(self, text="It looks like you haven't added any inventory files yet.", font=('Segoe UI', 10)).pack(pady=10)
        
        btn_frame = ttk.Frame(self, padding=20)
        btn_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(btn_frame, text="1. ADD EXCEL FILE", width=30, command=lambda: self._choose("files")).pack(pady=10)
        ttk.Button(btn_frame, text="2. USER GUIDE (Read First)", width=30, command=lambda: self._choose("help")).pack(pady=10)
        ttk.Button(btn_frame, text="3. EXPLORE APP (Without Files)", width=30, command=lambda: self._choose("explore")).pack(pady=10)
        
        ttk.Label(self, text="Tip: You can find these options later in the 'Manage' menu.", font=('Segoe UI', 8, 'italic')).pack(side=tk.BOTTOM, pady=20)

    def _choose(self, choice):
        self.destroy()
        self.on_choice(choice)


