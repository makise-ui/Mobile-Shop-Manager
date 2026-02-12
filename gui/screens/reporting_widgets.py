import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import ttkbootstrap as tb
from datetime import datetime, timedelta
from ttkbootstrap.tooltip import ToolTip

class AdvancedFilterPanel(ttk.LabelFrame):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, text="1. Filter Logic (If/Else Conditions)", **kwargs)
        self.controller = controller
        self.available_fields = []
        self.inventory_df = None
        self.condition_widgets = []
        
        # Auto-persistence path
        try:
            self.persistence_file = self.controller.app_config.get_config_dir() / "last_filters.json"
        except:
            self.persistence_file = None

        self._init_ui()

        # Try to get initial data from inventory if available
        try:
            df = getattr(self.controller.inventory, 'inventory_df', None)
            if df is not None:
                self.update_data(df)
        except: pass
        
        # Auto-load after UI is ready
        self.after(100, self.load_last_filters)

    def _init_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="+ Add Condition", command=self.add_condition_row, bootstyle="success-outline").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Clear", command=self.clear_conditions, bootstyle="secondary-outline").pack(side=tk.LEFT, padx=5)
        
        # Presets Menu
        self.preset_btn = ttk.Menubutton(toolbar, text="💡 Examples", bootstyle="warning-outline")
        self.preset_btn.pack(side=tk.LEFT)
        
        self.preset_menu = tk.Menu(self.preset_btn, tearoff=0)
        self.preset_btn.config(menu=self.preset_menu)
        
        self._setup_presets()
        
        # Persistence
        ttk.Button(toolbar, text="💾 Save", command=self.save_filters, bootstyle="info-outline").pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="📂 Load", command=self.load_filters, bootstyle="info-outline").pack(side=tk.RIGHT, padx=2)

        # Scrollable area
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _setup_presets(self):
        examples = {
            "Expensive Stock (IN > 20k)": [
                {'logic': 'START', 'field': 'status', 'operator': 'Equals', 'value': 'IN'},
                {'logic': 'AND', 'field': 'price', 'operator': '>', 'value': '20000'}
            ],
            "Items Sold Today": [
                {'logic': 'START', 'field': 'status', 'operator': 'Equals', 'value': 'OUT'},
                {'logic': 'AND', 'field': 'date_sold', 'operator': 'Equals', 'value': datetime.now().strftime('%Y-%m-%d')}
            ],
            "Premium iPhone Sales (30 Days)": [
                {'logic': 'START', 'field': 'status', 'operator': 'Equals', 'value': 'OUT'},
                {'logic': 'AND', 'field': 'model', 'operator': 'Contains', 'value': 'iPhone'},
                {'logic': 'AND', 'field': 'price', 'operator': '>', 'value': '40000'},
                {'logic': 'AND', 'field': 'date_sold', 'operator': '>=', 'value': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}
            ],
            "Aged Budget Stock (Audit)": [
                {'logic': 'START', 'field': 'status', 'operator': 'Equals', 'value': 'IN'},
                {'logic': 'AND', 'field': 'price', 'operator': '<', 'value': '10000'},
                {'logic': 'AND', 'field': 'date_added', 'operator': '<=', 'value': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')},
                {'logic': 'AND', 'field': 'grade', 'operator': 'Not Equals', 'value': 'A'}
            ],
            "High-Value Returns (XOR Demo)": [
                {'logic': 'START', 'field': 'status', 'operator': 'Equals', 'value': 'RTN'},
                {'logic': 'XOR', 'field': 'price', 'operator': '>', 'value': '50000'}
            ],
            "Missing Grade/Info": [
                {'logic': 'START', 'field': 'status', 'operator': 'Equals', 'value': 'IN'},
                {'logic': 'AND', 'field': 'grade', 'operator': 'Is Empty', 'value': ''}
            ]
        }
        
        for name, data in examples.items():
            self.preset_menu.add_command(label=name, command=lambda d=data: self.apply_preset(d))

    def apply_preset(self, filters):
        self.clear_conditions()
        for f_data in filters:
            self.add_condition_row(f_data)
        messagebox.showinfo("Preset Applied", "Example filter has been loaded.")

    def update_data(self, df):
        self.inventory_df = df
        if df is not None:
            self.available_fields = sorted(list(df.columns))
            # Also update existing rows if any
            for row in self.condition_widgets:
                row.available_fields = self.available_fields
                row.field_cb.config(values=self.available_fields)

    def update_fields(self, fields):
        """Legacy compatibility"""
        self.available_fields = fields

    def get_unique_values(self, field):
        if self.inventory_df is None or field not in self.inventory_df.columns:
            return []
        try:
            # Get unique values, drop NaNs, convert to string, sort
            vals = self.inventory_df[field].dropna().unique().tolist()
            return sorted([str(v) for v in vals])
        except:
            return []

    def add_condition_row(self, initial_data=None):
        show_logic = len(self.condition_widgets) > 0
        
        row = ConditionRow(self.scroll_frame, self.available_fields, 
                           self.remove_condition_row, 
                           get_values_func=self.get_unique_values,
                           show_logic=show_logic)
        row.pack(fill=tk.X, pady=2)
        if initial_data:
            row.set_data(initial_data)
        self.condition_widgets.append(row)

    def remove_condition_row(self, row):
        row.destroy()
        if row in self.condition_widgets:
            self.condition_widgets.remove(row)

    def clear_conditions(self):
        for row in self.condition_widgets:
            row.destroy()
        self.condition_widgets = []

    def get_filters(self):
        filters = [row.get_data() for row in self.condition_widgets]
        self.save_last_filters(filters)
        return filters

    def save_last_filters(self, filters):
        if self.persistence_file:
            try:
                with open(self.persistence_file, 'w') as f:
                    json.dump(filters, f)
            except: pass

    def load_last_filters(self):
        if self.persistence_file and self.persistence_file.exists():
            try:
                with open(self.persistence_file, 'r') as f:
                    filters = json.load(f)
                
                self.clear_conditions()
                for f_data in filters:
                    self.add_condition_row(f_data)
            except: pass

    def save_filters(self):
        filters = self.get_filters()
        if not filters: return
        
        f_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="filter_preset.json",
            title="Save Filter Preset"
        )
        if f_path:
            try:
                with open(f_path, 'w') as f:
                    json.dump(filters, f, indent=4)
                messagebox.showinfo("Success", "Filter preset saved.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

    def load_filters(self):
        f_path = filedialog.askopenfilename(
            defaultextension=".json",
            title="Load Filter Preset"
        )
        if f_path:
            try:
                with open(f_path, 'r') as f:
                    filters = json.load(f)
                
                self.clear_conditions()
                for f_data in filters:
                    self.add_condition_row(f_data)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")

class ConditionRow(ttk.Frame):
    def __init__(self, parent, available_fields, on_delete, get_values_func=None, show_logic=False):
        super().__init__(parent)
        self.available_fields = available_fields
        self.on_delete = on_delete
        self.get_values_func = get_values_func
        self.show_logic = show_logic
        
        self.logic_var = tk.StringVar(value="AND")
        self.field_var = tk.StringVar()
        self.op_var = tk.StringVar()
        self.val_var = tk.StringVar()
        
        self._init_ui()

    def _init_ui(self):
        # 0. Logic (Conditional)
        if self.show_logic:
            self.logic_cb = ttk.Combobox(self, values=['AND', 'OR', 'AND NOT', 'OR NOT', 'XOR'], 
                                         textvariable=self.logic_var, state="readonly", width=7)
            self.logic_cb.pack(side=tk.LEFT, padx=2)

        # 1. Field
        self.field_cb = ttk.Combobox(self, values=self.available_fields, textvariable=self.field_var, state="readonly", width=15)
        self.field_cb.pack(side=tk.LEFT, padx=2)
        self.field_cb.bind("<<ComboboxSelected>>", self._on_field_change)

        # 2. Operator
        self.ops = ['Equals', 'Contains', '>', '<', '>=', '<=', 'Not Equals', 'Is Empty', 'Is Not Empty', 'Modulo', 'Above', 'Below']
        self.op_cb = ttk.Combobox(self, values=self.ops, textvariable=self.op_var, state="readonly", width=10)
        self.op_cb.pack(side=tk.LEFT, padx=2)
        self.op_cb.set('Equals')
        self.op_cb.bind("<<ComboboxSelected>>", self._on_op_change)

        # 3. Value Container
        self.val_container = ttk.Frame(self)
        self.val_container.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Now that container exists, set initial field and trigger UI update
        if self.available_fields:
            self.field_cb.set(self.available_fields[0])
            self._on_field_change()
        else:
            self._show_text_entry() # Initial
        
        # 4. Delete
        ttk.Button(self, text="X", width=3, bootstyle="danger-outline",
                   command=lambda: self.on_delete(self)).pack(side=tk.LEFT, padx=2)

    def _on_field_change(self, event=None):
        field = self.field_var.get()
        field_lower = field.lower()
        
        if 'date' in field_lower or 'updated' in field_lower or 'added' in field_lower:
            self._show_date_picker()
        else:
            # Check if we should show dropdown for values
            if self.get_values_func:
                vals = self.get_values_func(field)
                if vals:
                    self._show_dropdown(vals)
                else:
                    self._show_text_entry()
            else:
                self._show_text_entry()

    def _on_op_change(self, event=None):
        op = self.op_var.get()
        if op in ['Above', 'Below']:
            self._show_date_picker()
        elif op == 'Modulo':
            self.val_var.set("2=0")
            self._show_text_entry()

    def _show_dropdown(self, values):
        for w in self.val_container.winfo_children(): w.destroy()
        # state="normal" allows manual input
        self.val_cb = ttk.Combobox(self.val_container, values=values, textvariable=self.val_var, state="normal")
        self.val_cb.pack(fill=tk.X)
        ToolTip(self.val_cb, text="Select from list or type manually")

    def _show_date_picker(self):
        for w in self.val_container.winfo_children(): w.destroy()
        rel_dates = ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "This Month", "Pick Date...", "Manual Input..."]
        self.date_cb = ttk.Combobox(self.val_container, values=rel_dates, state="readonly")
        self.date_cb.pack(fill=tk.X)
        self.date_cb.set("Today")
        self.date_cb.bind("<<ComboboxSelected>>", self._on_rel_date_change)
        self._on_rel_date_change()

    def _on_rel_date_change(self, event=None):
        val = self.date_cb.get()
        today = datetime.now().date()
        if val == "Today": self.val_var.set(today.strftime('%Y-%m-%d'))
        elif val == "Yesterday": self.val_var.set((today - timedelta(days=1)).strftime('%Y-%m-%d'))
        elif val == "Last 7 Days": self.val_var.set((today - timedelta(days=7)).strftime('%Y-%m-%d'))
        elif val == "Last 30 Days": self.val_var.set((today - timedelta(days=30)).strftime('%Y-%m-%d'))
        elif val == "This Month": self.val_var.set(today.replace(day=1).strftime('%Y-%m-%d'))
        elif val == "Pick Date...":
            self.date_cb.destroy()
            try:
                self.de = tb.DateEntry(self.val_container)
                self.de.pack(fill=tk.X)
            except:
                self._show_text_entry()
        elif val == "Manual Input...":
            self._show_text_entry()

    def _show_text_entry(self):
        for w in self.val_container.winfo_children(): w.destroy()
        self.val_entry = ttk.Entry(self.val_container, textvariable=self.val_var)
        self.val_entry.pack(fill=tk.X)

    def get_data(self):
        val = self.val_var.get()
        # Handle DateEntry specially if it exists
        for w in self.val_container.winfo_children():
            if hasattr(w, 'entry'):
                val = w.entry.get()
        
        return {
            'logic': self.logic_var.get() if self.show_logic else 'START',
            'field': self.field_var.get(),
            'operator': self.op_var.get(),
            'value': val
        }

    def set_data(self, data):
        # We need to set variables and THEN update UI
        self.field_var.set(data.get('field', ''))
        self.op_var.set(data.get('operator', ''))
        self.val_var.set(data.get('value', ''))
        if self.show_logic:
            self.logic_var.set(data.get('logic', 'AND'))
        
        # Manually trigger field change to show correct widget
        self._on_field_change()
        # Force the value back if the dropdown/date picker cleared it or changed it
        self.val_var.set(data.get('value', ''))

class SamplingPanel(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Sampling & Limits", **kwargs)
        self._init_ui()

    def _init_ui(self):
        vcmd = (self.register(self._validate_int), '%P')

        # Toggle Switch
        self.var_enable = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Enable Advanced Sampling", variable=self.var_enable, 
                        command=self._toggle_visibility, bootstyle="round-toggle").pack(anchor=tk.W, padx=5, pady=5)
        
        # Inner Frame (Hidden by default)
        self.inner_frame = ttk.Frame(self)
        
        # 1. Row Limit
        f_limit = ttk.Frame(self.inner_frame)
        f_limit.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(f_limit, text="Row Limit:").pack(side=tk.LEFT)
        self.spin_limit = ttk.Spinbox(f_limit, from_=0, to=10000, width=10, validate="key", validatecommand=vcmd)
        self.spin_limit.set(0)
        self.spin_limit.pack(side=tk.RIGHT)
        
        # 2. Modulo Logic
        f_mod = ttk.LabelFrame(self.inner_frame, text="Modulo Filter (e.g. Even IDs)")
        f_mod.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(f_mod, text="Divisor:").grid(row=0, column=0, padx=2, pady=2)
        self.ent_div = ttk.Entry(f_mod, width=5, validate="key", validatecommand=vcmd)
        self.ent_div.insert(0, "2")
        self.ent_div.grid(row=0, column=1, padx=2, pady=2)
        
        ttk.Label(f_mod, text="Remainder:").grid(row=1, column=0, padx=2, pady=2)
        self.ent_rem = ttk.Entry(f_mod, width=5, validate="key", validatecommand=vcmd)
        self.ent_rem.insert(0, "0")
        self.ent_rem.grid(row=1, column=1, padx=2, pady=2)
        
        self.var_mod_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(f_mod, text="Apply Modulo", variable=self.var_mod_enabled).grid(row=2, column=0, columnspan=2)

        # 3. Custom Expression
        f_expr = ttk.LabelFrame(self.inner_frame, text="Custom Logic (Expression)")
        f_expr.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.txt_expr = tk.Text(f_expr, height=4, width=30, font=("Consolas", 9))
        self.txt_expr.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        hint = "Example: price > 500 and status == 'IN'"
        lbl_hint = ttk.Label(f_expr, text=hint, font=("Arial", 8, "italic"), foreground="gray")
        lbl_hint.pack(fill=tk.X)
        
        ToolTip(lbl_hint, text="Enter a valid Pandas query string.\nFields: unique_id, price, model, status, etc.\nUse 'and', 'or', '==', '!=', '>', '<'", bootstyle="info")
        
        # Initial State
        self._toggle_visibility()

    def _validate_int(self, P):
        if P == "": return True
        return P.isdigit()

    def _toggle_visibility(self):
        if self.var_enable.get():
            self.inner_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        else:
            self.inner_frame.pack_forget()

    def get_sampling_data(self):
        if not self.var_enable.get():
            return {
                'limit': 0,
                'modulo': {'enabled': False, 'divisor': '2', 'remainder': '0'},
                'custom_expression': ''
            }
            
        return {
            'limit': self.spin_limit.get(),
            'modulo': {
                'enabled': self.var_mod_enabled.get(),
                'divisor': self.ent_div.get(),
                'remainder': self.ent_rem.get()
            },
            'custom_expression': self.txt_expr.get("1.0", tk.END).strip()
        }
