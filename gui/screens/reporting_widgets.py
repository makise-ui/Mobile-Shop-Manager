import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from datetime import datetime, timedelta

class AdvancedFilterPanel(ttk.LabelFrame):
    def __init__(self, parent, available_fields, **kwargs):
        super().__init__(parent, text="1. Filter Logic (If/Else Conditions)", **kwargs)
        self.available_fields = available_fields
        self.condition_widgets = []
        self._init_ui()

    def _init_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="+ Add Condition", command=self.add_condition_row, bootstyle="success-outline").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Clear Filters", command=self.clear_conditions, bootstyle="secondary-outline").pack(side=tk.LEFT, padx=5)

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

    def add_condition_row(self, initial_data=None):
        row = ConditionRow(self.scroll_frame, self.available_fields, self.remove_condition_row)
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
        return [row.get_data() for row in self.condition_widgets]

class ConditionRow(ttk.Frame):
    def __init__(self, parent, available_fields, on_delete):
        super().__init__(parent)
        self.available_fields = available_fields
        self.on_delete = on_delete
        
        self.field_var = tk.StringVar()
        self.op_var = tk.StringVar()
        self.val_var = tk.StringVar()
        
        self._init_ui()

    def _init_ui(self):
        # 1. Field
        self.field_cb = ttk.Combobox(self, values=self.available_fields, textvariable=self.field_var, state="readonly", width=15)
        self.field_cb.pack(side=tk.LEFT, padx=2)
        self.field_cb.bind("<<ComboboxSelected>>", self._on_field_change)
        
        if self.available_fields:
            self.field_cb.set(self.available_fields[0])

        # 2. Operator
        self.ops = ['Equals', 'Contains', '>', '<', '>=', '<=', 'Not Equals', 'Is Empty', 'Is Not Empty', 'Modulo', 'Above', 'Below']
        self.op_cb = ttk.Combobox(self, values=self.ops, textvariable=self.op_var, state="readonly", width=10)
        self.op_cb.pack(side=tk.LEFT, padx=2)
        self.op_cb.set('Equals')
        self.op_cb.bind("<<ComboboxSelected>>", self._on_op_change)

        # 3. Value Container (Swap between Entry and DateEntry)
        self.val_container = ttk.Frame(self)
        self.val_container.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        self.val_entry = ttk.Entry(self.val_container, textvariable=self.val_var)
        self.val_entry.pack(fill=tk.X)
        
        # 4. Delete
        ttk.Button(self, text="X", width=3, bootstyle="danger-outline",
                   command=lambda: self.on_delete(self)).pack(side=tk.LEFT, padx=2)

    def _on_field_change(self, event=None):
        field = self.field_var.get().lower()
        if 'date' in field or 'updated' in field or 'added' in field:
            self._show_date_picker()
        else:
            self._show_text_entry()

    def _on_op_change(self, event=None):
        op = self.op_var.get()
        if op in ['Above', 'Below']:
            self._show_date_picker()
        elif op == 'Modulo':
            self.val_var.set("2=0") # Default hint
            self._show_text_entry()

    def _show_date_picker(self):
        for w in self.val_container.winfo_children(): w.destroy()
        rel_dates = ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "This Month", "Pick Date..."]
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
                # Fallback if DateEntry fails (e.g. no display during init)
                self.val_entry = ttk.Entry(self.val_container, textvariable=self.val_var)
                self.val_entry.pack(fill=tk.X)

    def _show_text_entry(self):
        for w in self.val_container.winfo_children(): w.destroy()
        self.val_entry = ttk.Entry(self.val_container, textvariable=self.val_var)
        self.val_entry.pack(fill=tk.X)

    def get_data(self):
        val = self.val_var.get()
        for w in self.val_container.winfo_children():
            if hasattr(w, 'entry'): # Look for tb.DateEntry's entry
                val = w.entry.get()
        
        return {
            'field': self.field_var.get(),
            'operator': self.op_var.get(),
            'value': val
        }

    def set_data(self, data):
        self.field_var.set(data.get('field', ''))
        self.op_var.set(data.get('operator', ''))
        self.val_var.set(data.get('value', ''))
        self._on_field_change()

class SamplingPanel(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Sampling & Limits", **kwargs)
        self._init_ui()

    def _init_ui(self):
        # 1. Row Limit
        f_limit = ttk.Frame(self)
        f_limit.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(f_limit, text="Row Limit:").pack(side=tk.LEFT)
        self.spin_limit = ttk.Spinbox(f_limit, from_=0, to=10000, width=10)
        self.spin_limit.set(0)
        self.spin_limit.pack(side=tk.RIGHT)
        
        # 2. Modulo Logic
        f_mod = ttk.LabelFrame(self, text="Modulo Filter (e.g. Even IDs)")
        f_mod.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(f_mod, text="Divisor:").grid(row=0, column=0, padx=2, pady=2)
        self.ent_div = ttk.Entry(f_mod, width=5)
        self.ent_div.insert(0, "2")
        self.ent_div.grid(row=0, column=1, padx=2, pady=2)
        
        ttk.Label(f_mod, text="Remainder:").grid(row=1, column=0, padx=2, pady=2)
        self.ent_rem = ttk.Entry(f_mod, width=5)
        self.ent_rem.insert(0, "0")
        self.ent_rem.grid(row=1, column=1, padx=2, pady=2)
        
        self.var_mod_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(f_mod, text="Apply Modulo", variable=self.var_mod_enabled).grid(row=2, column=0, columnspan=2)

        # 3. Custom Expression
        f_expr = ttk.LabelFrame(self, text="Custom Logic (Expression)")
        f_expr.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.txt_expr = tk.Text(f_expr, height=4, width=30, font=("Consolas", 9))
        self.txt_expr.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        hint = "Example: price > 500 and status == 'IN'"
        lbl_hint = ttk.Label(f_expr, text=hint, font=("Arial", 8, "italic"), foreground="gray")
        lbl_hint.pack(fill=tk.X)

    def get_sampling_data(self):
        return {
            'limit': self.spin_limit.get(),
            'modulo': {
                'enabled': self.var_mod_enabled.get(),
                'divisor': self.ent_div.get(),
                'remainder': self.ent_rem.get()
            },
            'custom_expression': self.txt_expr.get("1.0", tk.END).strip()
        }
