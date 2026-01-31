import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from core.reporting import ReportGenerator
import datetime
import pandas as pd
from .screens.reporting_widgets import AdvancedFilterPanel, SamplingPanel

class ReportingScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self._init_ui()

    def _init_ui(self):
        # Header
        header = ttk.Label(self, text="Advanced Reporting & Export", font=("Segoe UI", 16, "bold"))
        header.pack(pady=10, anchor="w", padx=20)

        # Container
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # 1. Config View
        self.config_frame = ttk.Frame(self.container)
        self.config_frame.pack(fill=tk.BOTH, expand=True)
        
        # Split Config
        left_panel = ttk.Frame(self.config_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_panel = ttk.Frame(self.config_frame, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        
        # Widgets
        self.filter_panel = AdvancedFilterPanel(left_panel, [])
        self.filter_panel.pack(fill=tk.BOTH, expand=True)
        
        self.sampling_panel = SamplingPanel(right_panel)
        self.sampling_panel.pack(fill=tk.X, pady=(0, 10))
        
        # Field Selection (Dual Listbox)
        fields_group = ttk.LabelFrame(right_panel, text="2. Select Fields")
        fields_group.pack(fill=tk.BOTH, expand=True)
        
        dl_frame = ttk.Frame(fields_group)
        dl_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left List (Available)
        ttk.Label(dl_frame, text="Available").grid(row=0, column=0, sticky="w")
        self.lb_avail = tk.Listbox(dl_frame, selectmode=tk.MULTIPLE, height=10)
        self.lb_avail.grid(row=1, column=0, sticky="nsew")
        
        # Buttons
        btn_frame = ttk.Frame(dl_frame)
        btn_frame.grid(row=1, column=1, padx=5)
        ttk.Button(btn_frame, text=">", width=4, command=self.move_right).pack(pady=2)
        ttk.Button(btn_frame, text="<", width=4, command=self.move_left).pack(pady=2)
        
        # Right List (Selected)
        ttk.Label(dl_frame, text="Selected").grid(row=0, column=2, sticky="w")
        self.lb_sel = tk.Listbox(dl_frame, selectmode=tk.MULTIPLE, height=10)
        self.lb_sel.grid(row=1, column=2, sticky="nsew")
        
        dl_frame.columnconfigure(0, weight=1)
        dl_frame.columnconfigure(2, weight=1)

        self.serial_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(fields_group, text="Include S.No", variable=self.serial_var).pack(pady=5)

        # Preview Button
        ttk.Button(self.config_frame, text="PREVIEW DATA >>", command=self.show_preview, bootstyle="primary").pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # 2. Preview View
        self.preview_frame = ttk.Frame(self.container)
        
        p_tb = ttk.Frame(self.preview_frame)
        p_tb.pack(fill=tk.X, pady=5)
        ttk.Button(p_tb, text="<< BACK TO CONFIG", command=self.show_config, bootstyle="secondary-outline").pack(side=tk.LEFT)
        self.lbl_preview_count = ttk.Label(p_tb, text="Preview: 0 rows", font=("bold"))
        self.lbl_preview_count.pack(side=tk.LEFT, padx=20)
        
        ttk.Button(p_tb, text="Export Excel", command=lambda: self.export_data('excel'), bootstyle="success").pack(side=tk.RIGHT, padx=5)
        ttk.Button(p_tb, text="Export PDF", command=lambda: self.export_data('pdf'), bootstyle="danger").pack(side=tk.RIGHT, padx=5)
        
        self.tree = ttk.Treeview(self.preview_frame, show='headings')
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        self.preview_df = None

    def on_show(self):
        self.refresh_data()

    def refresh_data(self):
        df = getattr(self.controller.inventory, 'inventory_df', None)
        if df is None or df.empty: return

        cols = sorted(list(df.columns))
        
        # Update available fields in Filter Panel
        self.filter_panel.update_fields(cols)
        
        # Update Lists
        current_sel = self.lb_sel.get(0, tk.END)
        current_avail = self.lb_avail.get(0, tk.END)
        known = set(current_sel) | set(current_avail)
        
        new_cols = [c for c in cols if c not in known]
        
        if not known:
            defaults = ['brand', 'imei', 'model', 'price', 'status', 'buyer']
            for c in cols:
                if c in defaults:
                    self.lb_sel.insert(tk.END, c)
                else:
                    self.lb_avail.insert(tk.END, c)
        else:
            for c in new_cols:
                self.lb_avail.insert(tk.END, c)

    def move_right(self):
        sel = self.lb_avail.curselection()
        items = [self.lb_avail.get(i) for i in sel]
        for item in items:
            self.lb_sel.insert(tk.END, item)
            idx = self.lb_avail.get(0, tk.END).index(item)
            self.lb_avail.delete(idx)

    def move_left(self):
        sel = self.lb_sel.curselection()
        items = [self.lb_sel.get(i) for i in sel]
        for item in items:
            self.lb_avail.insert(tk.END, item)
            idx = self.lb_sel.get(0, tk.END).index(item)
            self.lb_sel.delete(idx)

    def get_selected_fields(self):
        return list(self.lb_sel.get(0, tk.END))

    def generate_report_df(self):
        df = getattr(self.controller.inventory, 'inventory_df', None)
        if df is None or df.empty: return pd.DataFrame()
        
        filters = self.filter_panel.get_filters()
        sampling = self.sampling_panel.get_sampling_data()
        
        generator = ReportGenerator(df)
        
        # 1. Filter
        res = generator.apply_filters(filters)
        
        # 2. Custom Expression
        res = generator.apply_custom_expression(res, sampling['custom_expression'])
        
        # 3. Modulo
        mod_data = sampling.get('modulo', {})
        if mod_data.get('enabled'):
            try:
                div = int(mod_data['divisor'])
                rem = int(mod_data['remainder'])
                # Assuming filtering on 'unique_id' if numeric?
                # Or we need a field selector for modulo?
                # Spec said "Mathematical Sampling (Modulo): Ability to filter rows based on a modulo operation (e.g., ID % 2 == 0)".
                # I'll default to unique_id or add a selector later. For now unique_id.
                # Ensure numeric
                if 'unique_id' in res.columns:
                    nums = pd.to_numeric(res['unique_id'], errors='coerce').fillna(0)
                    res = res[nums % div == rem]
            except: pass
            
        # 4. Limit
        res = generator.apply_limit(res, sampling['limit'])
        
        return res

    def show_preview(self):
        selected_fields = self.get_selected_fields()
        if not selected_fields:
            messagebox.showwarning("Warning", "Select at least one field.")
            return
            
        self.preview_df = self.generate_report_df()
        
        # Render Tree
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = selected_fields
        for col in selected_fields:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
            
        for _, row in self.preview_df.iterrows():
            vals = [row.get(c, '') for c in selected_fields]
            self.tree.insert("", tk.END, values=vals)
            
        self.lbl_preview_count.config(text=f"Preview: {len(self.preview_df)} rows")
        
        self.config_frame.pack_forget()
        self.preview_frame.pack(fill=tk.BOTH, expand=True)

    def show_config(self):
        self.preview_frame.pack_forget()
        self.config_frame.pack(fill=tk.BOTH, expand=True)

    def export_data(self, format_type):
        if self.preview_df is None or self.preview_df.empty:
            messagebox.showwarning("Empty", "No data to export.")
            return
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        f_path = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}" if format_type != 'excel' else '.xlsx',
            initialfile=f"Report_{timestamp}"
        )
        if not f_path: return
        
        cols = self.get_selected_fields()
        generator = ReportGenerator(self.preview_df)
        success, msg = generator.export(self.preview_df, cols, format_type, f_path, include_serial=self.serial_var.get())
        
        if success:
            messagebox.showinfo("Success", f"Exported to {f_path}")
        else:
            messagebox.showerror("Error", msg)
            
    def focus_primary(self):
        pass