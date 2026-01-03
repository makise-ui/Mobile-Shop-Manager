import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

class MapColumnsDialog(tk.Toplevel):
    def __init__(self, parent, file_path, on_save_callback, current_mapping=None):
        super().__init__(parent)
        self.title("Map Columns")
        self.geometry("600x500")
        self.file_path = file_path
        self.on_save = on_save_callback
        self.current_mapping = current_mapping or {}
        
        self.mappings = {}
        # Removed 'ram', 'rom'
        self.canonical_fields = ['imei', 'model', 'ram_rom', 'price', 'supplier', 'notes', 'status', 'color', 'buyer', 'buyer_contact']
        
        # Load sample data
        try:
            if file_path.endswith('.csv'):
                self.df = pd.read_csv(file_path, nrows=3)
            else:
                self.df = pd.read_excel(file_path, nrows=3)
            self.headers = list(self.df.columns)
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")
            self.destroy()
            return

        self._init_ui()

    def _init_ui(self):
        # Header Info
        lbl_info = ttk.Label(self, text=f"Mapping for: {self.file_path}")
        lbl_info.pack(pady=10)

        # Mapping Frame
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Grid Header
        ttk.Label(frame, text="Internal Field", font=('bold')).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(frame, text="File Column", font=('bold')).grid(row=0, column=1, padx=5, pady=5)

        self.combos = {}
        
        # Load existing map: {FileCol: InternalCol}
        # We need reverse map for UI: {InternalCol: FileCol}
        existing_map = {}
        if self.current_mapping and 'mapping' in self.current_mapping:
            for k, v in self.current_mapping['mapping'].items():
                existing_map[v] = k

        # Rows
        for idx, field in enumerate(self.canonical_fields):
            row = idx + 1
            ttk.Label(frame, text=field).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            
            combo = ttk.Combobox(frame, values=["(Ignore)"] + self.headers)
            
            # Pre-select if exists
            if field in existing_map:
                if existing_map[field] in self.headers:
                    combo.set(existing_map[field])
            else:
                combo.current(0)
                # Auto-suggest only if not mapped
                self._auto_suggest(field, combo)
                
            combo.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=5)
            self.combos[field] = combo

        # Supplier Override
        frame_supp = ttk.Frame(self, padding=10)
        frame_supp.pack(fill=tk.X)
        ttk.Label(frame_supp, text="Default Supplier (if column not mapped):").pack(side=tk.LEFT)
        self.ent_supplier = ttk.Entry(frame_supp)
        
        if self.current_mapping:
            self.ent_supplier.insert(0, self.current_mapping.get('supplier', ''))
            
        self.ent_supplier.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Buttons
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Save", command=self._on_save).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def _auto_suggest(self, field, combo):
        # Simple heuristic
        for header in self.headers:
            h_lower = header.lower()
            if field in h_lower:
                combo.set(header)
                return
            # Price specific
            if field == 'price' and ('cost' in h_lower or 'mrp' in h_lower or 'rate' in h_lower):
                combo.set(header)
                return

    def _on_save(self):
        final_mapping = {}
        for field, combo in self.combos.items():
            val = combo.get()
            if val and val != "(Ignore)":
                final_mapping[val] = field # Store as {FileCol: InternalCol} for inventory logic 
                # Wait, inventory.py expects {FileCol: InternalCol} in 'mapping' dict logic?
                # Let's check inventory.py:
                # for col_name, can_name in mapping.items():
                #    if can_name == canonical_name: ...
                # Yes, inventory.py iterates mapping.items() where key=FileCol, value=InternalCol.
                pass
        
        # Construct the object expected by config
        # We need {FileCol: InternalCol}
        # My loop above: final_mapping[val] = field  -> {HeaderName: 'imei'}
        
        save_data = {
            "mapping": final_mapping,
            "supplier": self.ent_supplier.get()
        }
        
        self.on_save(self.file_path, save_data)
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


