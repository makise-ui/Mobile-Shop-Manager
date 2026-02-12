import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import datetime
import ttkbootstrap as tb

from ..base import BaseScreen
from ..dialogs import ConflictResolutionDialog
from core.analytics import AnalyticsManager

class DashboardScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.sim_params = {}
        self._init_ui()

    def _init_ui(self):
        # Header
        h_frame = self.add_header("Dashboard", help_section="Understand the Dashboard")
        ttk.Button(h_frame, text="⚙ Price Simulation", bootstyle="info-outline", command=self.open_sim_settings).pack(side=tk.RIGHT, padx=5)

        # Scrollable Container
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.lbl_sim = ttk.Label(self.scroll_frame, text="⚠️ SIMULATION MODE ACTIVE: Profits based on assumed costs.", bootstyle="warning-inverse", anchor="center")
        
        # 1. Main KPI Cards
        f_cards = ttk.Frame(self.scroll_frame)
        f_cards.pack(fill=tk.X, padx=20, pady=10)
        
        self.card_stock = self._create_card(f_cards, "Total Items (In Stock)", "0")
        self.card_stock.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.card_value = self._create_card(f_cards, "Stock Value", "₹0")
        self.card_value.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.card_aging = self._create_card(f_cards, "Items Aging (>60 Days)", "0")
        self.card_aging.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # --- AI Insights Section (Hidden by default) ---
        self.f_ai = ttk.LabelFrame(self.scroll_frame, text=" ✨ AI Demand Insights ", bootstyle="primary")
        
        cols_ai = ('model', 'velocity', 'stock', 'days', 'status')
        self.tree_ai = ttk.Treeview(self.f_ai, columns=cols_ai, show='headings', height=5)
        self.tree_ai.heading('model', text='Model')
        self.tree_ai.heading('velocity', text='Sales/Week')
        self.tree_ai.heading('stock', text='Current Stock')
        self.tree_ai.heading('days', text='Days Left')
        self.tree_ai.heading('status', text='Status')
        
        self.tree_ai.column('velocity', width=80, anchor='center')
        self.tree_ai.column('stock', width=80, anchor='center')
        self.tree_ai.column('days', width=80, anchor='center')
        self.tree_ai.column('status', width=120, anchor='center')
        
        self.tree_ai.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.f_ai.pack(fill=tk.X, padx=20, pady=10)

        # 2. Alerts Section
        f_alerts = ttk.LabelFrame(self.scroll_frame, text=" Inventory Health Alerts ", bootstyle="danger")
        f_alerts.pack(fill=tk.X, padx=20, pady=20)
        
        # Split Alerts: Aging & Low Stock
        f_split = ttk.Frame(f_alerts, padding=10)
        f_split.pack(fill=tk.BOTH, expand=True)
        
        # Aging Table
        f_old = ttk.LabelFrame(f_split, text=" Old Stock (Risk) ", bootstyle="warning")
        f_old.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        cols_old = ('model', 'days', 'price')
        self.tree_aging = ttk.Treeview(f_old, columns=cols_old, show='headings', height=6)
        self.tree_aging.heading('model', text='Model')
        self.tree_aging.heading('days', text='Days in Stock')
        self.tree_aging.heading('price', text='Price')
        self.tree_aging.column('days', width=80, anchor='center')
        self.tree_aging.column('price', width=80, anchor='e')
        self.tree_aging.pack(fill=tk.BOTH, expand=True)
        
        # Low Stock Table
        f_low = ttk.LabelFrame(f_split, text=" Low Stock Models (< 2 units) ", bootstyle="info")
        f_low.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        cols_low = ('model', 'count', 'sold_last_30')
        self.tree_low = ttk.Treeview(f_low, columns=cols_low, show='headings', height=6)
        self.tree_low.heading('model', text='Model Family')
        self.tree_low.heading('count', text='In Stock')
        self.tree_low.heading('sold_last_30', text='Sold (30d)')
        self.tree_low.column('count', width=80, anchor='center')
        self.tree_low.pack(fill=tk.BOTH, expand=True)
        
        # Top Sellers Table
        f_top_sellers = ttk.LabelFrame(self.scroll_frame, text=" Top Selling Models (Last 30 Days) ", bootstyle="success")
        f_top_sellers.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        cols_top = ('rank', 'model', 'sold_count')
        self.tree_top = ttk.Treeview(f_top_sellers, columns=cols_top, show='headings', height=5)
        self.tree_top.heading('rank', text='#')
        self.tree_top.heading('model', text='Model')
        self.tree_top.heading('sold_count', text='Units Sold')
        self.tree_top.column('rank', width=40, anchor='center')
        self.tree_top.column('sold_count', width=100, anchor='center')
        self.tree_top.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 3. Recent Activity
        ttk.Label(self.scroll_frame, text="Recent Activity", font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        self.tree_log = ttk.Treeview(self.scroll_frame, columns=('time', 'action', 'details'), show='headings', height=8)
        self.tree_log.heading('time', text='Time')
        self.tree_log.column('time', width=150)
        self.tree_log.heading('action', text='Action')
        self.tree_log.column('action', width=120)
        self.tree_log.heading('details', text='Details')
        self.tree_log.column('details', width=400)
        
        self.tree_log.pack(fill=tk.X, padx=20, pady=10)

    def _create_card(self, parent, title, value):
        f = ttk.LabelFrame(parent, text=title)
        lbl = ttk.Label(f, text=value, font=('Segoe UI', 24, 'bold'), foreground="#007acc")
        lbl.pack()
        f.lbl_val = lbl # Store ref
        return f

    def open_sim_settings(self):
        # Dynamic import to avoid circular dependency if simulation imports screens
        from gui.simulation import PriceSimulationDialog
        dlg = PriceSimulationDialog(self, self.sim_params)
        if dlg.result:
            self.sim_params = dlg.result
            self._refresh_stats()

    def on_show(self):
        self._refresh_stats()
        self._refresh_log()

    def _refresh_stats(self):
        df = self.app.inventory.get_inventory()
        
        if self.sim_params.get('enabled'):
            self.lbl_sim.pack(fill=tk.X, pady=(0, 10), after=self.scroll_frame.winfo_children()[0])
        else:
            self.lbl_sim.pack_forget()

        if df.empty:
            count = 0
            val = 0
            self._update_alerts(pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        else:
            # Filter Available
            available = df[df['status'] == 'IN']
            count = len(available)
            val = available['price'].sum()
            
            # Aging Logic
            now = datetime.datetime.now()
            def get_age(row):
                try:
                    d = row.get('last_updated')
                    if isinstance(d, str): d = datetime.datetime.fromisoformat(d)
                    if not isinstance(d, datetime.datetime): return 0
                    return (now - d).days
                except: return 0
            
            if not available.empty:
                available = available.copy()
                available['age_days'] = available.apply(get_age, axis=1)
                aging_stock = available[available['age_days'] > 60].sort_values('age_days', ascending=False)
            else:
                aging_stock = pd.DataFrame()
                
            self.card_aging.lbl_val.config(text=str(len(aging_stock)), foreground="red" if not aging_stock.empty else "green")
            self._update_alerts(available, aging_stock, df)
            
        self.card_stock.lbl_val.config(text=str(count))
        self.card_value.lbl_val.config(text=f"₹{val:,.0f}")
        
        # AI Forecast Logic
        if str(self.app.app_config.get("enable_ai_features", "True")) == "True":
            self.f_ai.pack(fill=tk.X, padx=20, pady=10, before=self.tree_aging.master.master.master)
            
            if 'analytics' in self.app.screens:
                # This assumes 'analytics' screen is initialized.
                # Since we are in Dashboard, and AnalyticsScreen is separate, we might share the manager?
                # Or Dashboard creates its own? The original code accessed app.screens['analytics'].
                # If AnalyticsScreen is not loaded, this might fail.
                # Safe check:
                if hasattr(self.app.screens.get('analytics', None), 'analytics'):
                    forecast = self.app.screens['analytics'].analytics.get_demand_forecast()
                    for i in self.tree_ai.get_children(): self.tree_ai.delete(i)
                    
                    for item in forecast:
                         tag = 'normal'
                         if item['status'] == 'OUT_OF_STOCK': tag = 'danger'
                         elif item['status'] == 'LOW_STOCK': tag = 'warning'
                         
                         self.tree_ai.insert('', tk.END, values=(
                             item['model'], 
                             f"{item['velocity']}/wk",
                             item['stock'],
                             f"{item['days_left']} days",
                             item['status']
                         ), tags=(tag,))
                    
                    self.tree_ai.tag_configure('danger', foreground='red')
                    self.tree_ai.tag_configure('warning', foreground='#ffcc00')
        else:
            self.f_ai.pack_forget()

    def _update_alerts(self, available_df, aging_df, full_df):
        for i in self.tree_aging.get_children(): self.tree_aging.delete(i)
        if not aging_df.empty:
            for _, row in aging_df.head(20).iterrows():
                self.tree_aging.insert('', tk.END, values=(row['model'], f"{row['age_days']} days", f"₹{row['price']:,.0f}"))
                
        for i in self.tree_low.get_children(): self.tree_low.delete(i)
        if not available_df.empty:
            available_df['model_fam'] = available_df['model'].apply(lambda x: " ".join(str(x).split()[:2]))
            counts = available_df['model_fam'].value_counts()
            low_stock = counts[counts < 2]
            for model, count in low_stock.head(20).items():
                self.tree_low.insert('', tk.END, values=(model, count, "-"))

        for i in self.tree_top.get_children(): self.tree_top.delete(i)
        if not full_df.empty:
            sold = full_df[full_df['status'].isin(['OUT', 'SOLD'])]
            if not sold.empty:
                now = datetime.datetime.now()
                def is_recent(row):
                    try:
                        d = row.get('last_updated')
                        if isinstance(d, str): d = datetime.datetime.fromisoformat(d)
                        if not isinstance(d, datetime.datetime): return False
                        return (now - d).days <= 30
                    except: return False
                
                recent_sold = sold[sold.apply(is_recent, axis=1)].copy()
                if not recent_sold.empty:
                    recent_sold['model_fam'] = recent_sold['model'].apply(lambda x: " ".join(str(x).split()[:2]))
                    top_counts = recent_sold['model_fam'].value_counts()
                    for idx, (model, count) in enumerate(top_counts.head(10).items()):
                        self.tree_top.insert('', tk.END, values=(idx+1, model, count))

    def _refresh_log(self):
        for i in self.tree_log.get_children():
            self.tree_log.delete(i)
        logs = self.app.activity_logger.get_logs(limit=20)
        for log in logs:
            self.tree_log.insert('', tk.END, values=(log['timestamp'], log['action'], log['details']))

class ActivityLogScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self._init_ui()

    def _init_ui(self):
        tb = self.add_header("Activity Log", help_section="Data Loss After Excel Update")
        ttk.Button(tb, text="Refresh", command=self._refresh_list).pack(side=tk.RIGHT, padx=5)
        ttk.Button(tb, text="Clear Logs", command=self._clear_logs).pack(side=tk.RIGHT, padx=5)
        
        cols = ('time', 'action', 'details')
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        self.tree.heading('time', text='Timestamp')
        self.tree.column('time', width=150)
        self.tree.heading('action', text='Action')
        self.tree.column('action', width=120)
        self.tree.heading('details', text='Details')
        self.tree.column('details', width=400)
        
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def on_show(self):
        self._refresh_list()

    def _refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if not self.app.activity_logger:
            return
            
        logs = self.app.activity_logger.get_logs(limit=200)
        for log in logs:
            ts = log.get('timestamp', '')
            try:
                dt = datetime.datetime.fromisoformat(ts)
                ts = dt.strftime("%Y-%m-%d %H:%M:%S")
            except: pass
            self.tree.insert('', tk.END, values=(ts, log.get('action'), log.get('details')))

    def _clear_logs(self):
        if messagebox.askyesno("Confirm", "Clear all activity logs?"):
            if self.app.activity_logger:
                self.app.activity_logger.clear()
            self._refresh_list()

class ConflictScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self._init_ui()

    def _init_ui(self):
        tb = self.add_header("Data Conflicts", help_section="Conflict Detected")
        ttk.Button(tb, text="Refresh", command=self._refresh_list).pack(side=tk.RIGHT, padx=5)
        ttk.Button(tb, text="Resolve Selected", command=self._resolve).pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(self, text="Conflicts occur when the same IMEI appears in multiple Excel files or rows.", font=('Segoe UI', 9, 'italic')).pack(fill=tk.X, pady=(0,10))
        
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        cols = ('ids', 'imei', 'model', 'sources')
        self.tree = ttk.Treeview(container, columns=cols, show='headings')
        self.tree.heading('ids', text='Unique IDs')
        self.tree.heading('imei', text='IMEI')
        self.tree.heading('model', text='Model')
        self.tree.heading('sources', text='Found In (Files)')
        
        self.tree.column('ids', width=100)
        self.tree.column('imei', width=150)
        self.tree.column('model', width=200)
        self.tree.column('sources', width=600)
        
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def on_show(self):
        self._refresh_list()

    def _refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        conflicts = self.app.inventory.conflicts
        for i, c in enumerate(conflicts):
            src_str = ", ".join(c['sources'])
            ids_str = ", ".join(map(str, c.get('unique_ids', [])))
            self.tree.insert('', tk.END, iid=str(i), values=(ids_str, c['imei'], c['model'], src_str))

    def _resolve(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection", "Select a conflict to resolve.")
            return
            
        idx = int(sel[0])
        conflicts = self.app.inventory.conflicts
        if idx < len(conflicts):
            c_data = conflicts[idx]
            ConflictResolutionDialog(self.winfo_toplevel(), c_data, self.app._resolve_conflict_callback)

class AnalyticsScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.analytics = AnalyticsManager(app_context.inventory)
        self.sim_params = {}
        self._init_ui()

    def _init_ui(self):
        h_frame = self.add_header("Business Intelligence Dashboard", help_section="Analytics and Business Intelligence")
        ttk.Button(h_frame, text="⚙ Price Simulation", bootstyle="info-outline", command=self.open_sim_settings).pack(side=tk.RIGHT, padx=5)

        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)

        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.lbl_sim = ttk.Label(self.scroll_frame, text="⚠️ SIMULATION MODE ACTIVE: Profits based on assumed costs.", bootstyle="warning-inverse", anchor="center")

        kpi_container = ttk.Frame(self.scroll_frame)
        kpi_container.pack(fill=tk.X, padx=20, pady=10)

        self.kpi_stock = self._add_kpi_card(kpi_container, "STOCK VALUE", "₹0", "success")
        self.kpi_sold = self._add_kpi_card(kpi_container, "ITEMS SOLD", "0", "info")
        self.kpi_revenue = self._add_kpi_card(kpi_container, "TOTAL REVENUE", "₹0", "primary")
        self.kpi_profit = self._add_kpi_card(kpi_container, "EST. PROFIT", "₹0", "warning")

        charts_frame = ttk.Frame(self.scroll_frame)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.brand_frame = ttk.LabelFrame(charts_frame, text=" Brand Distribution ", bootstyle="info")
        self.brand_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 10))
        self.brand_inner = ttk.Frame(self.brand_frame, padding=15)
        self.brand_inner.pack(fill=tk.BOTH, expand=True)

        self.buyer_frame = ttk.LabelFrame(charts_frame, text=" Top Buyers Performance ", bootstyle="primary")
        self.buyer_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(10, 0))
        
        b_canvas = tk.Canvas(self.buyer_frame, borderwidth=0, highlightthickness=0, height=200)
        b_scroll = ttk.Scrollbar(self.buyer_frame, orient="vertical", command=b_canvas.yview)
        self.buyer_inner = ttk.Frame(b_canvas, padding=10)
        
        self.buyer_inner.bind("<Configure>", lambda e: b_canvas.configure(scrollregion=b_canvas.bbox("all")))
        b_canvas.create_window((0, 0), window=self.buyer_inner, anchor="nw")
        b_canvas.configure(yscrollcommand=b_scroll.set)
        
        b_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        b_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)

        self.history_frame = ttk.LabelFrame(self.scroll_frame, text=" Buyer Purchase History ", bootstyle="warning")
        self.history_frame.pack(fill=tk.X, padx=20, pady=10)
        
        h_inner = ttk.Frame(self.history_frame, padding=10)
        h_inner.pack(fill=tk.X)

        cols_h = ('model', 'imei', 'price', 'date')
        self.tree_history = ttk.Treeview(h_inner, columns=cols_h, show='headings', height=5)
        self.tree_history.heading('model', text='Model Name')
        self.tree_history.heading('imei', text='IMEI / Serial')
        self.tree_history.heading('price', text='Sale Price')
        self.tree_history.heading('date', text='Date')
        
        self.tree_history.column('model', width=250)
        self.tree_history.column('price', width=100, anchor='e')
        self.tree_history.pack(fill=tk.X)

        detail_frame = ttk.LabelFrame(self.scroll_frame, text=" Model-Wise Stock Analysis ", bootstyle="secondary")
        detail_frame.pack(fill=tk.X, padx=20, pady=20)
        
        detail_inner = ttk.Frame(detail_frame, padding=10)
        detail_inner.pack(fill=tk.BOTH, expand=True)

        cols = ('model', 'in_stock', 'sold', 'avg_price')
        self.tree_details = ttk.Treeview(detail_inner, columns=cols, show='headings', height=8)
        self.tree_details.heading('model', text='Model Name')
        self.tree_details.heading('in_stock', text='In Stock')
        self.tree_details.heading('sold', text='Sold')
        self.tree_details.heading('avg_price', text='Avg. Selling Price')
        self.tree_details.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(self.scroll_frame, padding=20)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="REFRESH DASHBOARD", command=self.refresh, bootstyle="success-outline", width=25).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="EXPORT ANALYTICS (PDF)", command=self._export_pdf, bootstyle="danger-outline").pack(side=tk.RIGHT)

    def _add_kpi_card(self, parent, title, value, color):
        card = ttk.Frame(parent, bootstyle=f"{color}.TFrame", padding=1)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        inner = ttk.Frame(card, padding=15)
        inner.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(inner, text=title, font=('Segoe UI', 9, 'bold'), foreground="gray").pack(anchor=tk.W)
        lbl_val = ttk.Label(inner, text=value, font=('Segoe UI', 18, 'bold'), bootstyle=color)
        lbl_val.pack(anchor=tk.W, pady=(5, 0))
        return lbl_val

    def on_show(self):
        self.refresh()

    def open_sim_settings(self):
        from gui.simulation import PriceSimulationDialog
        dlg = PriceSimulationDialog(self, self.sim_params)
        if dlg.result:
            self.sim_params = dlg.result
            self.refresh()

    def _show_buyer_history(self, buyer_name):
        clean_name = str(buyer_name).strip()
        self.history_frame.config(text=f" Purchase History: {clean_name} ")
        for item in self.tree_history.get_children(): self.tree_history.delete(item)
        
        if hasattr(self, 'sold_data') and not self.sold_data.empty:
            matches = self.sold_data[self.sold_data['buyer'].astype(str).str.strip().str.lower() == clean_name.lower()]
            for _, row in matches.iterrows():
                self.tree_history.insert('', tk.END, values=(
                    row.get('model', 'Unknown'),
                    row.get('imei', '-'),
                    f"₹{row.get('price', 0):,.0f}",
                    str(row.get('last_updated', '-'))[:10]
                ))

    def refresh(self):
        stats = self.analytics.get_summary(self.sim_params)
        df = self.app.inventory.get_inventory()
        
        if self.sim_params.get('enabled'):
            self.lbl_sim.pack(fill=tk.X, pady=(0, 10), after=self.scroll_frame.winfo_children()[0])
        else:
            self.lbl_sim.pack_forget()

        self.kpi_stock.config(text=f"₹{stats['total_value']:,.0f}")
        self.kpi_sold.config(text=str(stats.get('status_counts', {}).get('OUT', 0)))
        
        sold_df = df[df['status'] == 'OUT']
        self.sold_data = sold_df
        
        revenue = sold_df['price'].sum() if not sold_df.empty else 0
        self.kpi_revenue.config(text=f"₹{revenue:,.0f}")
        
        p_val = stats['realized_profit']
        p_color = "success" if p_val >= 0 else "danger"
        self.kpi_profit.config(text=f"₹{p_val:,.0f}", bootstyle=p_color)

        for w in self.brand_inner.winfo_children(): w.destroy()
        if not df.empty:
            df['brand'] = df['model'].apply(lambda x: str(x).split()[0].upper())
            brand_counts = df['brand'].value_counts().head(6)
            max_val = brand_counts.max() if not brand_counts.empty else 1
            
            for brand, count in brand_counts.items():
                f = ttk.Frame(self.brand_inner)
                f.pack(fill=tk.X, pady=5)
                ttk.Label(f, text=f"{brand:<12}", font=('Consolas', 10)).pack(side=tk.LEFT)
                bar_container = ttk.Frame(f, height=15, bootstyle="secondary")
                bar_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
                pct = (count / max_val)
                bar = ttk.Frame(bar_container, height=15, bootstyle="info")
                bar.place(relx=0, rely=0, relwidth=pct, relheight=1)
                ttk.Label(f, text=str(count), font=('bold')).pack(side=tk.RIGHT)

        for w in self.buyer_inner.winfo_children(): w.destroy()
        self.buyer_widgets = []
        
        if not sold_df.empty:
            temp_sold = sold_df.copy()
            temp_sold['buyer_clean'] = temp_sold['buyer'].astype(str).str.strip()
            buyer_stats = temp_sold.groupby('buyer_clean').agg({'unique_id': 'count', 'price': 'sum'}).sort_values('price', ascending=False).head(15)
            
            for buyer, row in buyer_stats.iterrows():
                f = ttk.Frame(self.buyer_inner, cursor="hand2")
                f.pack(fill=tk.X, pady=2)
                
                def on_click(event, b=buyer, frame=f): 
                    for bf in self.buyer_widgets: frame.master.nametowidget(bf).configure(bootstyle="default")
                    self._show_buyer_history(b)
                
                name_lbl = ttk.Label(f, text=f"👤 {str(buyer)[:20]}", font=('Segoe UI', 10))
                name_lbl.pack(side=tk.LEFT, padx=5)
                
                price_lbl = ttk.Label(f, text=f"₹{row['price']:,.0f}", bootstyle="primary")
                price_lbl.pack(side=tk.RIGHT, padx=5)
                
                count_lbl = ttk.Label(f, text=f"{int(row['unique_id'])} items", foreground="gray")
                count_lbl.pack(side=tk.RIGHT, padx=5)
                
                for widget in [f, name_lbl, price_lbl, count_lbl]:
                    widget.bind("<Button-1>", on_click)
                
                self.buyer_widgets.append(f)
        else:
            ttk.Label(self.buyer_inner, text="No sales data recorded yet.", foreground="gray").pack(pady=20)

        for item in self.tree_details.get_children(): self.tree_details.delete(item)
        if not df.empty:
            model_summary = df.groupby('model').apply(lambda x: pd.Series({
                'in_stock': (x['status'] == 'IN').sum(),
                'sold': (x['status'] == 'OUT').sum(),
                'avg_price': x['price'].mean()
            }), include_groups=False).sort_values('in_stock', ascending=False).head(20)
            
            for model, row in model_summary.iterrows():
                self.tree_details.insert('', tk.END, values=(model, int(row['in_stock']), int(row['sold']), f"₹{row['avg_price']:,.0f}"))

    def _export_pdf(self):
        f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=f"Analytics_Detailed_{datetime.date.today()}.pdf")
        if not f: return
        
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        
        try:
            doc = SimpleDocTemplate(f, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            elements.append(Paragraph("Detailed Business Analytics Report", styles['Title']))
            elements.append(Paragraph(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            stats = self.analytics.get_summary()
            df = self.app.inventory.get_inventory()
            
            elements.append(Paragraph("Financial Snapshot", styles['Heading2']))
            data = [
                ["Metric", "Value"],
                ["Total Inventory Value", f"Rs. {stats['total_value']:,.2f}"],
                ["Items In Stock", str(stats.get('status_counts', {}).get('IN', 0))],
                ["Items Sold", str(stats.get('status_counts', {}).get('OUT', 0))],
                ["Realized Profit (Est)", f"Rs. {stats['realized_profit']:,.2f}"]
            ]
            t = Table(data, colWidths=[200, 200])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 20))
            
            elements.append(Paragraph("Detailed Sales Log (Sold Items)", styles['Heading2']))
            
            sold_df = df[df['status'] == 'OUT'].copy()
            if not sold_df.empty:
                if 'last_updated' in sold_df.columns:
                    sold_df['last_updated'] = pd.to_datetime(sold_df['last_updated'], errors='coerce')
                    sold_df = sold_df.sort_values('last_updated', ascending=False)
                
                table_data = [["Date", "Buyer Name", "Model", "Sale Price"]]
                
                for _, row in sold_df.iterrows():
                    d = str(row.get('last_updated', '-'))[:10]
                    b = str(row.get('buyer', 'Unknown'))
                    m = str(row.get('model', 'Unknown'))
                    p = f"{row.get('price', 0):,.0f}"
                    table_data.append([d, b, m, p])
                
                t2 = Table(table_data, colWidths=[70, 110, 200, 70], repeatRows=1)
                t2.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('ALIGN', (-1,1), (-1,-1), 'RIGHT'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.whitesmoke])
                ]))
                elements.append(t2)
            else:
                elements.append(Paragraph("No sales recorded yet.", styles['Normal']))

            doc.build(elements)
            messagebox.showinfo("Export Success", f"Detailed report saved to:\n{f}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not generate PDF:\n{e}")
