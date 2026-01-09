import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from core.reporting import ReportGenerator
import datetime

class ReportingScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.conditions = []
        self.condition_widgets = []
        
        # available fields will be populated from data
        self.available_fields = [] 
        
        # PRESET DEFINITIONS
        self.presets = {
            "Select a Preset...": [],
            "All IN Stock": [{'field': 'Status', 'operator': 'Equals', 'value': 'IN'}],
            "All OUT Stock": [{'field': 'Status', 'operator': 'Equals', 'value': 'OUT'}],
            "All Returns (RTN)": [{'field': 'Status', 'operator': 'Equals', 'value': 'RTN'}],
            "IN Stock < 6000": [
                {'field': 'Status', 'operator': 'Equals', 'value': 'IN'},
                {'field': 'Price', 'operator': '<', 'value': '6000'}
            ],
            "IN Stock > 10000": [
                {'field': 'Status', 'operator': 'Equals', 'value': 'IN'},
                {'field': 'Price', 'operator': '>', 'value': '10000'}
            ],
            "Low Price (< 2000)": [{'field': 'Price', 'operator': '<', 'value': '2000'}],
            "Expensive (> 20000)": [{'field': 'Price', 'operator': '>', 'value': '20000'}]
        }
        
        self._init_ui()

    def _init_ui(self):
        # Main Layout: Split into Left (Config) and Right (Actions/Preview?)
        
        # === Header ===
        header = ttk.Label(self, text="Advanced Reporting & Export", font=("Segoe UI", 16, "bold"))
        header.pack(pady=10, anchor="w", padx=20)

        # === Content Container ===
        content = ttk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Left Panel: Filtering Logic
        left_panel = ttk.LabelFrame(content, text="1. Filter Logic (If/Else Conditions)")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Toolbar for Filters
        filter_toolbar = ttk.Frame(left_panel)
        filter_toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(filter_toolbar, text="+ Add Condition", command=self.add_condition_row, bootstyle="success-outline").pack(side=tk.LEFT)
        ttk.Button(filter_toolbar, text="Clear Filters", command=self.clear_conditions, bootstyle="secondary-outline").pack(side=tk.LEFT, padx=5)

        # Preset Loader
        ttk.Label(filter_toolbar, text=" |  Load Preset: ").pack(side=tk.LEFT, padx=(10, 5))
        self.preset_cb = ttk.Combobox(filter_toolbar, values=list(self.presets.keys()), state="readonly", width=20)
        self.preset_cb.set("Select a Preset...")
        self.preset_cb.pack(side=tk.LEFT)
        self.preset_cb.bind("<<ComboboxSelected>>", self.apply_preset)

        # Scrollable area for conditions
        self.filter_canvas = tk.Canvas(left_panel)
        self.filter_scroll = ttk.Scrollbar(left_panel, orient="vertical", command=self.filter_canvas.yview)
        self.filter_frame = ttk.Frame(self.filter_canvas)

        self.filter_frame.bind(
            "<Configure>",
            lambda e: self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))
        )

        self.filter_canvas.create_window((0, 0), window=self.filter_frame, anchor="nw")
        self.filter_canvas.configure(yscrollcommand=self.filter_scroll.set)

        self.filter_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.filter_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Right Panel: Field Selection (Dual Listbox) & Actions
        right_panel = ttk.Frame(content, width=400) # Increased width for dual lists
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        right_panel.pack_propagate(False) 

        # Field Selection
        fields_group = ttk.LabelFrame(right_panel, text="2. Select Fields (Drag/Move)")
        fields_group.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Dual List Container
        dl_frame = ttk.Frame(fields_group)
        dl_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left List (Available)
        lbl_avail = ttk.Label(dl_frame, text="Available Fields")
        lbl_avail.grid(row=0, column=0, sticky="w")
        
        self.lb_avail = tk.Listbox(dl_frame, selectmode=tk.MULTIPLE, height=10)
        self.lb_avail.grid(row=1, column=0, sticky="nsew")
        
        # Buttons (Middle)
        btn_frame = ttk.Frame(dl_frame)
        btn_frame.grid(row=1, column=1, padx=5, sticky="ns")
        
        ttk.Button(btn_frame, text=">", width=4, command=self.move_right).pack(pady=2)
        ttk.Button(btn_frame, text="<", width=4, command=self.move_left).pack(pady=2)
        ttk.Button(btn_frame, text=">>", width=4, command=self.move_all_right).pack(pady=10)
        ttk.Button(btn_frame, text="<<", width=4, command=self.move_all_left).pack(pady=2)

        # Right List (Selected)
        lbl_sel = ttk.Label(dl_frame, text="Selected (In Order)")
        lbl_sel.grid(row=0, column=2, sticky="w")
        
        self.lb_sel = tk.Listbox(dl_frame, selectmode=tk.MULTIPLE, height=10)
        self.lb_sel.grid(row=1, column=2, sticky="nsew")
        
        # Reorder Buttons (Right Side)
        reorder_frame = ttk.Frame(dl_frame)
        reorder_frame.grid(row=1, column=3, padx=5, sticky="ns")
        ttk.Button(reorder_frame, text="▲", width=3, command=self.move_up).pack(pady=2)
        ttk.Button(reorder_frame, text="▼", width=3, command=self.move_down).pack(pady=2)
        
        dl_frame.columnconfigure(0, weight=1)
        dl_frame.columnconfigure(2, weight=1)
        dl_frame.rowconfigure(1, weight=1)

        # Options
        self.serial_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(fields_group, text="Include S.No (Row Count)", variable=self.serial_var).pack(pady=5)

        # Actions
        actions_group = ttk.LabelFrame(right_panel, text="3. Export Actions")
        actions_group.pack(fill=tk.X)
        
        ttk.Button(actions_group, text="Export to Excel (.xlsx)", command=lambda: self.export_data('excel'), bootstyle="success").pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(actions_group, text="Export to PDF", command=lambda: self.export_data('pdf'), bootstyle="danger").pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(actions_group, text="Export to Word (.docx)", command=lambda: self.export_data('word'), bootstyle="primary").pack(fill=tk.X, padx=5, pady=5)
        
        # Result Preview (Status Bar)
        self.status_lbl = ttk.Label(self, text="Ready. Add filters to get started.", relief=tk.SUNKEN, anchor="w")
        self.status_lbl.pack(fill=tk.X, side=tk.BOTTOM)

    def on_show(self):
        # Refresh fields based on current inventory data
        self.refresh_data()

    def refresh_data(self):
        # Get dataframe from controller
        df = getattr(self.controller.inventory, 'inventory_df', None)
        if df is None or df.empty:
            return

        cols = sorted(list(df.columns))
        
        # Update logic: Only if new columns appeared, add them to "Available"
        # Don't reset user's current selection if possible
        
        current_sel = self.lb_sel.get(0, tk.END)
        current_avail = self.lb_avail.get(0, tk.END)
        known = set(current_sel) | set(current_avail)
        
        new_cols = [c for c in cols if c not in known]
        
        # If it's first run (empty), populate Available
        if not known:
            # Default: Select typical fields
            defaults = ['brand', 'imei', 'model', 'price', 'status', 'buyer']
            for c in cols:
                if c in defaults:
                    self.lb_sel.insert(tk.END, c)
                else:
                    self.lb_avail.insert(tk.END, c)
        else:
            # Just add new ones to available
            for c in new_cols:
                self.lb_avail.insert(tk.END, c)

        self.available_fields = cols
        
        # Update Filter Comboboxes
        for widgets in self.condition_widgets:
            widgets['field_cb']['values'] = self.available_fields

    # --- Dual Listbox Logic ---
    def move_right(self):
        sel = self.lb_avail.curselection()
        # Move items in reverse order to avoid index shifting issues (if we were deleting in loop)
        # But here we delete using list
        items = [self.lb_avail.get(i) for i in sel]
        for item in items:
            self.lb_sel.insert(tk.END, item)
            # Find and delete from source
            idx = self.lb_avail.get(0, tk.END).index(item)
            self.lb_avail.delete(idx)
            
    def move_left(self):
        sel = self.lb_sel.curselection()
        items = [self.lb_sel.get(i) for i in sel]
        for item in items:
            self.lb_avail.insert(tk.END, item)
            idx = self.lb_sel.get(0, tk.END).index(item)
            self.lb_sel.delete(idx)

    def move_all_right(self):
        items = self.lb_avail.get(0, tk.END)
        for item in items:
            self.lb_sel.insert(tk.END, item)
        self.lb_avail.delete(0, tk.END)

    def move_all_left(self):
        items = self.lb_sel.get(0, tk.END)
        for item in items:
            self.lb_avail.insert(tk.END, item)
        self.lb_sel.delete(0, tk.END)

    def move_up(self):
        sel = self.lb_sel.curselection()
        if not sel: return
        for i in sel:
            if i == 0: continue
            text = self.lb_sel.get(i)
            self.lb_sel.delete(i)
            self.lb_sel.insert(i-1, text)
            self.lb_sel.selection_set(i-1)

    def move_down(self):
        sel = self.lb_sel.curselection()
        if not sel: return
        # Reverse to avoid index issues
        for i in reversed(sel):
            if i == self.lb_sel.size() - 1: continue
            text = self.lb_sel.get(i)
            self.lb_sel.delete(i)
            self.lb_sel.insert(i+1, text)
            self.lb_sel.selection_set(i+1)

    def add_condition_row(self, initial_data=None):
        row_frame = ttk.Frame(self.filter_frame)
        row_frame.pack(fill=tk.X, pady=2)

        # 1. Field
        field_cb = ttk.Combobox(row_frame, values=self.available_fields, state="readonly", width=15)
        field_cb.pack(side=tk.LEFT, padx=2)
        
        if initial_data and initial_data.get('field'):
             field_cb.set(initial_data['field'])
        elif self.available_fields:
            # Default to first available field
            field_cb.set(self.available_fields[0])

        # 2. Operator
        ops = ['Equals', 'Contains', '>', '<', '>=', '<=', 'Not Equals', 'Is Empty', 'Is Not Empty']
        op_cb = ttk.Combobox(row_frame, values=ops, state="readonly", width=10)
        op_cb.pack(side=tk.LEFT, padx=2)
        
        if initial_data and initial_data.get('operator'):
            op_cb.set(initial_data['operator'])
        else:
            op_cb.set('Equals')

        # 3. Value
        val_entry = ttk.Entry(row_frame, width=20)
        val_entry.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        if initial_data and initial_data.get('value'):
            val_entry.insert(0, initial_data['value'])

        # 4. Delete
        widgets = {
            'frame': row_frame,
            'field_cb': field_cb,
            'op_cb': op_cb,
            'val_entry': val_entry
        }
        
        del_btn = ttk.Button(row_frame, text="X", width=3, bootstyle="danger-outline",
                             command=lambda: self.remove_condition_row(widgets))
        del_btn.pack(side=tk.LEFT, padx=2)
        
        self.condition_widgets.append(widgets)

    def remove_condition_row(self, widgets):
        widgets['frame'].destroy()
        if widgets in self.condition_widgets:
            self.condition_widgets.remove(widgets)

    def clear_conditions(self):
        for w in self.condition_widgets:
            w['frame'].destroy()
        self.condition_widgets = []
        self.preset_cb.set("Select a Preset...")

    def apply_preset(self, event=None):
        name = self.preset_cb.get()
        if name not in self.presets: return
        
        conditions = self.presets[name]
        if not conditions: return
        
        self.clear_conditions()
        self.preset_cb.set(name) # Restore name after clear
        
        for cond in conditions:
            self.add_condition_row(cond)

    def get_current_filters(self):
        conditions = []
        for w in self.condition_widgets:
            cond = {
                'field': w['field_cb'].get(),
                'operator': w['op_cb'].get(),
                'value': w['val_entry'].get()
            }
            conditions.append(cond)
        return conditions

    def get_selected_fields(self):
        # Return items from the Right Listbox (Selected)
        return list(self.lb_sel.get(0, tk.END))

    def export_data(self, format_type):
        df = getattr(self.controller.inventory, 'inventory_df', None)
        if df is None or df.empty:
            messagebox.showerror("Error", "No inventory data available to export.")
            return

        conditions = self.get_current_filters()
        selected_fields = self.get_selected_fields()

        if not selected_fields:
            messagebox.showwarning("Warning", "Please select at least one field to export.")
            return

        # Generate Report
        generator = ReportGenerator(df)
        filtered_df = generator.apply_filters(conditions)
        
        count = len(filtered_df)
        self.status_lbl.config(text=f"Found {count} records matching conditions.")
        
        if count == 0:
            messagebox.showinfo("Result", "No records match these filters.")
            return

        # File Dialog
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        ext_map = {'excel': '.xlsx', 'pdf': '.pdf', 'word': '.docx'}
        file_types = {
            'excel': ("Excel Files", "*.xlsx"),
            'pdf': ("PDF Files", "*.pdf"),
            'word': ("Word Documents", "*.docx")
        }
        
        default_name = f"Report_{timestamp}{ext_map[format_type]}"
        
        f_path = filedialog.asksaveasfilename(
            defaultextension=ext_map[format_type],
            filetypes=[file_types[format_type]],
            initialfile=default_name,
            title=f"Export to {format_type.upper()}"
        )

        if not f_path:
            return

        # PASS include_serial PARAMETER
        success, msg = generator.export(
            filtered_df, 
            selected_fields, 
            format_type, 
            f_path, 
            include_serial=self.serial_var.get()
        )
        
        if success:
            messagebox.showinfo("Success", f"Exported {count} rows successfully!\nSaved to: {f_path}")
        else:
            messagebox.showerror("Export Failed", msg)
    
    def focus_primary(self):
        pass
