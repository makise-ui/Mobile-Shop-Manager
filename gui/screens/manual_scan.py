import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import datetime
from core.manual_report import ManualReportSession
from core.reporting import ReportGenerator

class ManualScanScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.manual_session = ManualReportSession(self.controller.app_config)
        
        self._init_ui()

    def _init_ui(self):
        # Header
        header = ttk.Label(self, text="Manual Scan Reporting", font=("Segoe UI", 16, "bold"))
        header.pack(pady=10, anchor="w", padx=20)
        
        # Main Layout: Split Log (Left) and Config (Right)
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # RIGHT: Field Selection (Fixed Width)
        # Pack FIRST with side=RIGHT so it stays anchored
        right_frame = ttk.Frame(self.main_container, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=(10, 0))
        right_frame.pack_propagate(False) # Force width stability
        
        fields_group = ttk.LabelFrame(right_frame, text="Select Columns")
        fields_group.pack(fill=tk.BOTH, expand=True)
        
        # Dual Listbox Container
        dl_frame = ttk.Frame(fields_group)
        dl_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Available
        ttk.Label(dl_frame, text="Available Fields").pack(anchor=tk.W)
        self.lb_avail = tk.Listbox(dl_frame, selectmode=tk.MULTIPLE, height=15)
        self.lb_avail.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Buttons
        btn_frame = ttk.Frame(dl_frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Add ⬇", command=self.move_right).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove ⬆", command=self.move_left).pack(side=tk.LEFT, padx=5)

        # Selected
        ttk.Label(dl_frame, text="Selected Columns (Order)").pack(anchor=tk.W)
        self.lb_sel = tk.Listbox(dl_frame, selectmode=tk.MULTIPLE, height=15)
        self.lb_sel.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        ttk.Button(fields_group, text="Refresh View", command=self._refresh_list, bootstyle="info-outline").pack(fill=tk.X, padx=5, pady=10)

        # Serial Number Toggle
        self.serial_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(fields_group, text="Include S.No in Export", variable=self.serial_var).pack(pady=5)


        # LEFT: Scan & Log (Takes remaining space)
        left_frame = ttk.Frame(self.main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 1. Top Bar: Scan Input
        scan_frame = ttk.LabelFrame(left_frame, text="Scan Item")
        scan_frame.pack(fill=tk.X, pady=(0, 10))
        
        lbl_instr = ttk.Label(scan_frame, text="Scan Barcode / IMEI / Unique ID:", font=("Segoe UI", 11))
        lbl_instr.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.scan_entry = ttk.Entry(scan_frame, font=("Consolas", 12))
        self.scan_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        self.scan_entry.bind('<Return>', self._on_scan)
        
        ttk.Button(scan_frame, text="Add", command=lambda: self._on_scan(None), bootstyle="success").pack(side=tk.LEFT, padx=10)

        # 2. Main List (The "Logs")
        # Toolbar
        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=tk.X, pady=5)
        
        self.lbl_count = ttk.Label(toolbar, text="Items Scanned: 0", font=("Segoe UI", 10, "bold"))
        self.lbl_count.pack(side=tk.LEFT)
        
        ttk.Button(toolbar, text="Clear Session", command=self._clear_session, bootstyle="danger-outline").pack(side=tk.RIGHT)
        
        # Treeview Container
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_frame, show='headings')
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree.bind('<Delete>', self._delete_selected)

        # 3. Bottom Actions (Export)
        action_frame = ttk.LabelFrame(left_frame, text="Export Actions")
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="Export to Excel", command=lambda: self._export('excel'), bootstyle="success").pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(action_frame, text="Export to PDF", command=lambda: self._export('pdf'), bootstyle="danger").pack(side=tk.LEFT, padx=10, pady=10)

    def on_show(self):
        self._init_fields()
        self._refresh_list()
        self.focus_primary()

    def focus_primary(self):
        self.scan_entry.focus_set()

    def _init_fields(self):
        # Populate Available fields from Inventory
        df = getattr(self.controller.inventory, 'inventory_df', None)
        if df is None: return

        all_cols = sorted(list(df.columns))
        if 'timestamp' not in all_cols: all_cols.insert(0, 'timestamp') # Special field
        
        # Default Selection
        defaults = ['timestamp', 'unique_id', 'model', 'imei', 'price', 'status']
        
        # Clear
        self.lb_avail.delete(0, tk.END)
        self.lb_sel.delete(0, tk.END)
        
        # Populate
        for c in defaults:
            if c in all_cols:
                self.lb_sel.insert(tk.END, c)
                
        for c in all_cols:
            if c not in defaults:
                self.lb_avail.insert(tk.END, c)

    def move_right(self):
        sel = self.lb_avail.curselection()
        items = [self.lb_avail.get(i) for i in sel]
        for item in items:
            self.lb_sel.insert(tk.END, item)
            idx = self.lb_avail.get(0, tk.END).index(item)
            self.lb_avail.delete(idx)
        self._refresh_list()

    def move_left(self):
        sel = self.lb_sel.curselection()
        items = [self.lb_sel.get(i) for i in sel]
        for item in items:
            self.lb_avail.insert(tk.END, item)
            idx = self.lb_sel.get(0, tk.END).index(item)
            self.lb_sel.delete(idx)
        self._refresh_list()

    def get_selected_fields(self):
        return list(self.lb_sel.get(0, tk.END))

    def _on_scan(self, event):
        query = self.scan_entry.get().strip()
        if not query: return
        
        # Lookup
        item, _ = self.controller.inventory.get_item_by_id(query)
        
        if not item:
            # Try IMEI search
            df = getattr(self.controller.inventory, 'inventory_df', None)
            if df is not None and not df.empty:
                matches = df[df['imei'].astype(str).str.contains(query, na=False, case=False)]
                if not matches.empty:
                    item = matches.iloc[0].to_dict()
        
        if item:
            # Store FULL item data + timestamp
            data = item.copy()
            data['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Ensure unique_id is present
            if 'unique_id' not in data: data['unique_id'] = 'UNKNOWN'
            
            if self.manual_session.add_item(data):
                self.scan_entry.delete(0, tk.END)
                self._refresh_list()
                # Scroll to bottom using the new IID (unique_id)
                uid = data['unique_id']
                if self.tree.exists(uid):
                    self.tree.see(uid)
                    self.tree.selection_set(uid)
            else:
                messagebox.showwarning("Duplicate", f"Item already scanned:\n{item.get('model', 'Unknown')}")
                self.scan_entry.select_range(0, tk.END)
        else:
            messagebox.showerror("Not Found", f"Item not found: {query}")
            self.scan_entry.select_range(0, tk.END)

    def _refresh_list(self):
        # 1. Update Tree Columns based on Selection
        cols = self.get_selected_fields()
        if not cols: return
        
        self.tree["columns"] = cols
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100) # Default width

        # 2. Populate Data
        self.tree.delete(*self.tree.get_children())
        items = self.manual_session.get_items()
        self.lbl_count.config(text=f"Items Scanned: {len(items)}")
        
        for item in items:
            vals = [item.get(c, '') for c in cols]
            # Use unique_id as IID for robust deletion
            uid = item.get('unique_id', '')
            if uid:
                try:
                    self.tree.insert("", tk.END, iid=uid, values=vals)
                except tk.TclError:
                    # Fallback if IID collision somehow happens (shouldn't with add_item check)
                    self.tree.insert("", tk.END, values=vals)

    def _delete_selected(self, event):
        sel = self.tree.selection()
        if not sel: return
        
        if messagebox.askyesno("Delete", "Remove selected items?"):
            for iid in sel:
                # iid is now the unique_id (mostly)
                self.manual_session.remove_id(iid)
            
            self._refresh_list()

    def _clear_session(self):
        if messagebox.askyesno("Confirm", "Clear all scanned items?"):
            self.manual_session.clear()
            self._refresh_list()

    def _export(self, fmt):
        items = self.manual_session.get_items()
        if not items:
            messagebox.showwarning("Empty", "Nothing to export.")
            return
        
        # Create DataFrame from Session Items (which now have full data)
        df = pd.DataFrame(items)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        f_path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}" if fmt != 'excel' else '.xlsx',
            initialfile=f"ManualScanReport_{timestamp}"
        )
        if not f_path: return

        # Use Selected Columns
        cols = self.get_selected_fields()
        
        # Filter DF to selected columns
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        
        export_df = df[cols]
        
        generator = ReportGenerator(export_df)
        success, msg = generator.export(export_df, cols, fmt, f_path, include_serial=self.serial_var.get())
        
        if success:
            messagebox.showinfo("Success", f"Exported to {f_path}")
        else:
            messagebox.showerror("Error", msg)
