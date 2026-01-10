import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb

class PriceSimulationDialog(tb.Toplevel):
    def __init__(self, parent, current_params=None):
        super().__init__(parent)
        self.title("Analytics Simulation Mode")
        self.geometry("500x450")
        self.result = None
        self.current_params = current_params or {}
        self._init_ui()
        self.transient(parent)
        self.grab_set()
        self.wait_window()

    def _init_ui(self):
        ttk.Label(self, text="Advanced Price Simulation", font=('Segoe UI', 14, 'bold')).pack(pady=15)
        
        ttk.Label(self, text="Simulate hypothetical profits by adjusting Cost or Price logic.", 
                 wraplength=450, foreground="gray").pack(pady=(0, 15))
        
        # Enable Checkbox
        self.var_enable = tk.BooleanVar(value=self.current_params.get('enabled', False))
        chk = ttk.Checkbutton(self, text="Enable Simulation Mode", variable=self.var_enable, bootstyle="round-toggle")
        chk.pack(pady=5)
        
        # Frame for controls
        f_controls = ttk.LabelFrame(self, text=" Simulation Rules ", padding=15)
        f_controls.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Grid Layout
        f_controls.columnconfigure(1, weight=1)
        
        # 1. Target (What to Simulate)
        ttk.Label(f_controls, text="Simulate Target:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.var_target = tk.StringVar(value=self.current_params.get('target', 'cost'))
        cb_target = ttk.Combobox(f_controls, textvariable=self.var_target, state="readonly", 
                                values=['cost', 'price'])
        cb_target.grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(f_controls, text="(The value that changes)").grid(row=0, column=2, sticky=tk.W)
        
        # 2. Base (Based On)
        ttk.Label(f_controls, text="Based On:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.var_base = tk.StringVar(value=self.current_params.get('base', 'price'))
        cb_base = ttk.Combobox(f_controls, textvariable=self.var_base, state="readonly", 
                              values=['cost', 'price'])
        cb_base.grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(f_controls, text="(The source value)").grid(row=1, column=2, sticky=tk.W)
        
        # 3. Percentage Modifier
        ttk.Label(f_controls, text="Percentage (+/-").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.var_pct = tk.DoubleVar(value=self.current_params.get('percent', -8.0))
        ttk.Spinbox(f_controls, from_=-100, to=100, increment=0.5, textvariable=self.var_pct).grid(row=2, column=1, sticky=tk.EW, padx=5)
        ttk.Label(f_controls, text="%").grid(row=2, column=2, sticky=tk.W)
        
        # 4. Flat Modifier
        ttk.Label(f_controls, text="Flat Adjustment:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.var_flat = tk.DoubleVar(value=self.current_params.get('flat', 0.0))
        ttk.Entry(f_controls, textvariable=self.var_flat).grid(row=3, column=1, sticky=tk.EW, padx=5)
        ttk.Label(f_controls, text="₹ (Add/Subtract)").grid(row=3, column=2, sticky=tk.W)
        
        # Example Label
        self.lbl_example = ttk.Label(f_controls, text="", foreground="#17a2b8", font=('Segoe UI', 9))
        self.lbl_example.grid(row=4, column=0, columnspan=3, pady=15)
        
        # Buttons
        f_btns = ttk.Frame(self)
        f_btns.pack(fill=tk.X, pady=15, padx=20)
        ttk.Button(f_btns, text="Apply Simulation", command=self.apply, bootstyle="success").pack(side=tk.RIGHT)
        ttk.Button(f_btns, text="Cancel", command=self.destroy, bootstyle="secondary").pack(side=tk.RIGHT, padx=10)
        
        # Bind for dynamic update
        for v in [self.var_target, self.var_base, self.var_pct, self.var_flat]:
            v.trace_add("write", lambda *a: self._update_example())
            
        self._update_example()

    def _update_example(self):
        try:
            # Example Data
            cost_real = 3200
            price_real = 4500
            
            tgt = self.var_target.get()
            base = self.var_base.get()
            pct = self.var_pct.get()
            flat = self.var_flat.get()
            
            base_val = price_real if base == 'price' else cost_real
            new_val = base_val * (1 + pct/100.0) + flat
            
            res_cost = new_val if tgt == 'cost' else cost_real
            res_price = new_val if tgt == 'price' else price_real
            
            profit = res_price - res_cost
            
            txt = f"Example Item: Real Cost=₹{cost_real}, Sold=₹{price_real}\n"
            txt += f"------------------------------------------------\n"
            if tgt == 'cost':
                txt += f"SIMULATED COST: ₹{res_cost:,.0f} (Based on {base.title()})\n"
            else:
                txt += f"SIMULATED PRICE: ₹{res_price:,.0f} (Based on {base.title()})\n"
            
            txt += f"Projected Profit: ₹{profit:,.0f}"
            self.lbl_example.config(text=txt)
        except:
            self.lbl_example.config(text="Invalid input")

    def apply(self):
        self.result = {
            'enabled': self.var_enable.get(),
            'target': self.var_target.get(),
            'base': self.var_base.get(),
            'percent': self.var_pct.get(),
            'flat': self.var_flat.get()
        }
        self.destroy()