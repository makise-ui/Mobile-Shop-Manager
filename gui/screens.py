import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import ImageTk
from .dialogs import MapColumnsDialog, ZPLPreviewDialog
import pandas as pd
import datetime

# --- Base Screen Class ---
class BaseScreen(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent, padding=15)
        self.app = app_context
    
    def on_show(self):
        """Called when screen becomes visible"""
        pass

# --- Inventory Screen ---
class InventoryScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.df_display = pd.DataFrame()
        self._init_ui()

    def _init_ui(self):
        # -- Filter & Search Bar --
        filter_frame = ttk.LabelFrame(self, text="Search & Filter", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid layout for filters
        ttk.Label(filter_frame, text="Search (All fields):").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.var_search = tk.StringVar()
        self.var_search.trace("w", self._on_filter_change)
        ttk.Entry(filter_frame, textvariable=self.var_search, width=30).grid(row=0, column=1, padx=5, sticky=tk.W)
        
        ttk.Label(filter_frame, text="Supplier:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.combo_supplier = ttk.Combobox(filter_frame, state="readonly", width=20)
        self.combo_supplier.bind("<<ComboboxSelected>>", self._on_filter_change)
        self.combo_supplier.grid(row=0, column=3, padx=5, sticky=tk.W)

        ttk.Label(filter_frame, text="Min Price:").grid(row=0, column=4, padx=5, sticky=tk.W)
        self.var_min_price = tk.StringVar()
        self.var_min_price.trace("w", self._on_filter_change)
        ttk.Entry(filter_frame, textvariable=self.var_min_price, width=10).grid(row=0, column=5, padx=5)

        ttk.Button(filter_frame, text="Clear Filters", command=self._clear_filters).grid(row=0, column=6, padx=10)

        # -- Actions Bar --
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(action_frame, text="Check All", command=self._select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Uncheck All", command=self._deselect_all).pack(side=tk.LEFT, padx=5)
        ttk.Separator(action_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(action_frame, text="Print Checked", command=self._print_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Add Checked to Invoice", command=self._send_to_billing).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(action_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(action_frame, text="Mark Sold", command=lambda: self._bulk_update_status("OUT")).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Mark RTN", command=lambda: self._bulk_update_status("RTN")).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="Refresh Data", command=self.refresh_data).pack(side=tk.RIGHT, padx=5)

        # -- Main Content --
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # 1. Treeview (List)
        # Added 'check' column for checkboxes
        cols = ('check', 'unique_id', 'imei', 'model', 'ram_rom', 'price_original', 'price', 'supplier', 'status')
        self.tree = ttk.Treeview(paned, columns=cols, show='headings', selectmode='extended')
        
        # Configure Columns
        self.tree.heading('check', text='[x]')
        self.tree.column('check', width=40, anchor='center', stretch=False)
        
        self.tree.heading('unique_id', text='ID')
        self.tree.column('unique_id', width=50)
        
        self.tree.heading('imei', text='IMEI')
        self.tree.column('imei', width=110)
        
        self.tree.heading('model', text='Model')
        self.tree.column('model', width=130)
        
        self.tree.heading('ram_rom', text='RAM/ROM')
        self.tree.column('ram_rom', width=90)
        
        self.tree.heading('price_original', text='Price (Buy)')
        self.tree.column('price_original', width=70, anchor='e')
        
        self.tree.heading('price', text='Price (Sell)')
        self.tree.column('price', width=70, anchor='e')
        
        self.tree.heading('supplier', text='Supplier')
        self.tree.column('supplier', width=100)
        
        self.tree.heading('status', text='Status')
        self.tree.column('status', width=70)

        # Color Tags
        self.tree.tag_configure('old', background='#fff3cd') # Yellowish
        self.tree.tag_configure('very_old', background='#f8d7da') # Reddish

        scroll = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<<TreeviewSelect>>', self._on_row_click) 
        self.tree.bind('<ButtonRelease-1>', self._on_click_check) # Specific click handler
        
        paned.add(self.tree, minsize=400, width=700)

        # 2. Preview Panel (Right)
        preview_frame = ttk.LabelFrame(paned, text="Label Preview", padding=10)
        paned.add(preview_frame, minsize=250)
        
        self.lbl_preview = ttk.Label(preview_frame, text="Select item to preview", anchor="center")
        self.lbl_preview.pack(fill=tk.BOTH, expand=True)
        
        self.lbl_info = ttk.Label(preview_frame, text="")
        self.lbl_info.pack(fill=tk.X, pady=5)
        
        self.checked_ids = set() # Store unique_ids of checked items

    def on_show(self):
        self.refresh_data()

    def refresh_data(self):
        df = self.app.inventory.get_inventory()
        if df.empty:
            self.df_display = df
        else:
            self.df_display = df.copy()
            
        # Update filter options
        if not df.empty:
            suppliers = sorted(df['supplier'].astype(str).unique().tolist())
            self.combo_supplier['values'] = ["All"] + suppliers
            
        self._apply_filters()

    def _on_filter_change(self, *args):
        self._apply_filters()

    def _clear_filters(self):
        self.var_search.set("")
        self.combo_supplier.set("")
        self.var_min_price.set("")
        self._apply_filters()

    def _apply_filters(self):
        df = self.df_display
        if df.empty:
            self._render_tree(df)
            return

        # Search
        q = self.var_search.get().lower()
        if q:
            # Concat all searchable fields
            mask = df.apply(lambda x: q in str(x['model']).lower() or 
                                      q in str(x['imei']).lower() or 
                                      q in str(x['unique_id']).lower() or
                                      q in str(x['supplier']).lower(), axis=1)
            df = df[mask]
        
        # Supplier
        supp = self.combo_supplier.get()
        if supp and supp != "All":
            df = df[df['supplier'] == supp]
            
        # Min Price
        try:
            min_p = float(self.var_min_price.get())
            df = df[df['price'] >= min_p]
        except ValueError:
            pass

        self._render_tree(df)

    def _render_tree(self, df):
        # Clear
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        now = datetime.datetime.now()
            
        for idx, row in df.iterrows():
            uid = str(row.get('unique_id', ''))
            
            # Checkbox state
            check_mark = "☑" if uid in self.checked_ids else "☐"
            
            vals = (
                check_mark,
                uid,
                str(row.get('imei', '')),
                str(row.get('model', '')),
                str(row.get('ram_rom', '')),
                f"{row.get('price_original', 0):.2f}",
                f"{row.get('price', 0):.2f}",
                str(row.get('supplier', '')),
                str(row.get('status', ''))
            )
            
            # Aging Logic
            tag = ''
            try:
                # last_updated might be string or datetime
                last_up = row.get('last_updated')
                if isinstance(last_up, str):
                    last_up = datetime.datetime.fromisoformat(str(last_up))
                
                if isinstance(last_up, datetime.datetime):
                    age_days = (now - last_up).days
                    if age_days > 60:
                        tag = 'very_old'
                    elif age_days > 30:
                        tag = 'old'
            except:
                pass

            # Use unique_id as IID
            self.tree.insert('', tk.END, values=vals, iid=uid, tags=(tag,))

    def _on_click_check(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1": # The check column
                item_id = self.tree.identify_row(event.y)
                if item_id:
                    self._toggle_check(item_id)

    def _toggle_check(self, item_id):
        if item_id in self.checked_ids:
            self.checked_ids.remove(item_id)
            icon = "☐"
        else:
            self.checked_ids.add(item_id)
            icon = "☑"
            
        # Update value in tree
        # Get current values
        vals = list(self.tree.item(item_id, 'values'))
        vals[0] = icon
        self.tree.item(item_id, values=vals)
        
        self.lbl_info.configure(text=f"{len(self.checked_ids)} Item(s) Checked")

    def _select_all(self):
        for item_id in self.tree.get_children():
            if item_id not in self.checked_ids:
                self.checked_ids.add(item_id)
                vals = list(self.tree.item(item_id, 'values'))
                vals[0] = "☑"
                self.tree.item(item_id, values=vals)
        self.lbl_info.configure(text=f"{len(self.checked_ids)} Item(s) Checked")

    def _deselect_all(self):
        for item_id in self.tree.get_children():
            if item_id in self.checked_ids:
                vals = list(self.tree.item(item_id, 'values'))
                vals[0] = "☐"
                self.tree.item(item_id, values=vals)
        self.checked_ids.clear()
        self.lbl_info.configure(text=f"0 Item(s) Checked")

    def _on_row_click(self, event):
        # Preview the selection (standard highlight)
        items = self.tree.selection()
        if not items: return
        
        uid = items[0]
        # Find data
        df = self.app.inventory.get_inventory()
        # Find row by unique_id (since iid=unique_id)
        # Note: uid is string, df column is int (from registry).
        # Convert df column to str for match
        try:
            row = df[df['unique_id'].astype(str) == str(uid)].iloc[0]
            self._update_preview(row.to_dict())
        except IndexError:
            pass

    def _update_preview(self, row_data):
        w_mm = self.app.app_config.get('label_width_mm', 50)
        h_mm = self.app.app_config.get('label_height_mm', 22)
        pil_img = self.app.barcode_gen.generate_label_preview(row_data, w_mm, h_mm, dpi=120)
        
        self.preview_img = ImageTk.PhotoImage(pil_img)
        self.lbl_preview.configure(image=self.preview_img, text="")

    def _get_checked_data(self):
        if not self.checked_ids:
            return []
        
        df = self.app.inventory.get_inventory()
        # Filter where unique_id in checked_ids
        # Ensure type match
        mask = df['unique_id'].astype(str).isin(self.checked_ids)
        return df[mask].to_dict('records')

    def _print_selected(self):
        items = self._get_checked_data()
        if not items:
            messagebox.showwarning("None Checked", "Please check items [x] to print.")
            return
        
        # Show Preview
        def do_print():
            # Use Batch ZPL Printer
            count = self.app.printer.print_batch_zpl(items)
            if count > 0:
                messagebox.showinfo("Printing", f"Sent {count} labels to printer (Batch Mode).")
            else:
                # Fallback
                success = 0
                for item in items:
                    if self.app.printer.print_label_windows(item):
                        success += 1
                messagebox.showinfo("Printing", f"Sent {success} labels to printer.")

        ZPLPreviewDialog(self.winfo_toplevel(), items, do_print)

    def _send_to_billing(self):
        items = self._get_checked_data()
        if not items:
            messagebox.showwarning("None Checked", "Please check items [x] to add to invoice.")
            return
        self.app.switch_to_billing(items)

    def _bulk_update_status(self, new_status):
        items = self._get_checked_data()
        if not items:
            messagebox.showwarning("None Checked", "Please check items [x] to update status.")
            return
            
        if not messagebox.askyesno("Confirm", f"Update status to {new_status} for {len(items)} items?"):
            return
            
        for item in items:
            self.app.inventory.update_item_status(item['unique_id'], new_status)
            
        messagebox.showinfo("Success", "Statuses updated.")
        self.refresh_data()

# --- Files Screen ---
class FilesScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        
        # Toolbar
        tb = ttk.Frame(self)
        tb.pack(fill=tk.X, pady=10)
        ttk.Button(tb, text="+ Add Excel File", command=self._add_file).pack(side=tk.LEFT)
        ttk.Button(tb, text="Edit Mapping", command=self._edit_mapping).pack(side=tk.LEFT, padx=10)
        ttk.Button(tb, text="Remove File", command=self._remove_file).pack(side=tk.LEFT, padx=10)
        ttk.Button(tb, text="Refresh All", command=self._refresh).pack(side=tk.LEFT, padx=10)
        
        # List
        self.listbox = tk.Listbox(self, font=('Consolas', 10), height=15)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(self, text="* The app automatically watches these files for changes.", font=('Arial', 8, 'italic')).pack(pady=5)

    def on_show(self):
        self._refresh_list()

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        mappings = self.app.app_config.mappings
        for fp, data in mappings.items():
            status = self.app.inventory.file_status.get(fp, "Unknown")
            supplier = data.get('supplier', 'Mixed/None')
            self.listbox.insert(tk.END, f"[{status}] {fp} (Supplier: {supplier})")

    def _add_file(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv")])
        for fp in file_paths:
            if not self.app.app_config.get_file_mapping(fp):
                MapColumnsDialog(self.winfo_toplevel(), fp, self._on_mapping_save)
            else:
                self.app.inventory.load_file(fp)
                self.app.watcher.refresh_watch_list()
        self._refresh_list()

    def _edit_mapping(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selection", "Please select a file to edit mapping.")
            return
            
        # Parse file path from listbox text "[OK] /path/to/file (Supplier: ...)"
        text = self.listbox.get(sel[0])
        # A bit hacky parsing, but simplest given current display format
        # Find first ] and (Supplier:
        try:
            start_idx = text.find("] ") + 2
            end_idx = text.rfind(" (Supplier:")
            if start_idx < 2 or end_idx == -1:
                fp = text # Fallback
            else:
                fp = text[start_idx:end_idx]
            
            # Get existing config
            existing = self.app.app_config.get_file_mapping(fp)
            
            # Open Dialog
            MapColumnsDialog(self.winfo_toplevel(), fp, self._on_mapping_save, current_mapping=existing)
        except Exception as e:
            messagebox.showerror("Error", f"Could not parse file path: {e}")

    def _remove_file(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selection", "Please select a file to remove.")
            return

        text = self.listbox.get(sel[0])
        try:
            start_idx = text.find("] ") + 2
            end_idx = text.rfind(" (Supplier:")
            if start_idx < 2 or end_idx == -1:
                fp = text
            else:
                fp = text[start_idx:end_idx]
            
            if messagebox.askyesno("Confirm", f"Remove file from inventory?\n{fp}"):
                self.app.app_config.remove_file_mapping(fp)
                self.app.inventory.reload_all()
                self.app.watcher.refresh_watch_list()
                self._refresh_list()
        except Exception as e:
            messagebox.showerror("Error", f"Could not remove file: {e}")

    def _on_mapping_save(self, file_path, mapping_data):
        self.app.app_config.set_file_mapping(file_path, mapping_data)
        self.app.inventory.reload_all()
        self.app.watcher.refresh_watch_list()
        self._refresh_list()
    
    def _refresh(self):
        self.app.inventory.reload_all()
        self._refresh_list()

# --- Billing Screen ---
class BillingScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.cart_items = []
        self._init_ui()

    def _init_ui(self):
        # 0. Scan Bar
        scan_frame = ttk.Frame(self)
        scan_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(scan_frame, text="SCAN ID:", font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        self.ent_scan = ttk.Entry(scan_frame, font=('Segoe UI', 14))
        self.ent_scan.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.ent_scan.bind('<Return>', self._on_scan)
        
        # 1. Customer Details Frame
        cust_frame = ttk.LabelFrame(self, text="Customer Details", padding=15)
        cust_frame.pack(fill=tk.X, pady=10)
        
        # Row 1: Name & Contact
        ttk.Label(cust_frame, text="Name:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.ent_name = ttk.Entry(cust_frame, width=25)
        self.ent_name.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        ttk.Label(cust_frame, text="Contact:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.ent_contact = ttk.Entry(cust_frame, width=20)
        self.ent_contact.grid(row=0, column=3, padx=5, sticky=tk.W)
        
        # Row 2: Date & Options
        ttk.Label(cust_frame, text="Date:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.ent_date = ttk.Entry(cust_frame, width=15)
        self.ent_date.insert(0, str(datetime.date.today()))
        self.ent_date.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        self.var_interstate = tk.BooleanVar()
        ttk.Checkbutton(cust_frame, text="Interstate (IGST)", variable=self.var_interstate).grid(row=1, column=2, padx=5, sticky=tk.W)
        
        self.var_inclusive = tk.BooleanVar()
        ttk.Checkbutton(cust_frame, text="Tax Inclusive Prices", variable=self.var_inclusive).grid(row=1, column=3, padx=5, sticky=tk.W)
        
        # 2. Cart (Treeview)
        cart_frame = ttk.LabelFrame(self, text="Invoice Items", padding=10)
        cart_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        cols = ('id', 'model', 'price', 'gst')
        self.tree = ttk.Treeview(cart_frame, columns=cols, show='headings', height=8)
        self.tree.heading('id', text='ID')
        self.tree.heading('model', text='Model')
        self.tree.heading('price', text='Price')
        self.tree.heading('gst', text='Tax Est.')
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 3. Actions
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Clear Cart", command=self.clear_cart).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Generate Invoice PDF", command=self._generate).pack(side=tk.RIGHT)

    def on_show(self):
        self.ent_scan.focus_set()

    def _on_scan(self, event):
        iid = self.ent_scan.get().strip()
        if not iid: return
        
        df = self.app.inventory.get_inventory()
        match = df[df['unique_id'].astype(str) == iid]
        
        if not match.empty:
            item = match.iloc[0].to_dict()
            self.add_items([item])
            self.ent_scan.delete(0, tk.END)
        else:
            messagebox.showwarning("Not Found", f"ID {iid} not found in inventory.")
            self.ent_scan.select_range(0, tk.END)

    def add_items(self, items):
        self.cart_items.extend(items)
        self._refresh_cart()

    def clear_cart(self):
        self.cart_items = []
        self._refresh_cart()

    def _refresh_cart(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        tax_rate = self.app.app_config.get('gst_default_percent', 18.0)
        is_inclusive = self.var_inclusive.get()
        
        for item in self.cart_items:
            price = float(item.get('price', 0))
            
            if is_inclusive:
                # Tax is included in price
                taxable = price / (1 + tax_rate/100)
                tax_amt = price - taxable
            else:
                tax_amt = price * (tax_rate/100)
            
            self.tree.insert('', tk.END, values=(
                str(item.get('unique_id', '')),
                item.get('model', ''),
                f"{price:.2f}",
                f"{tax_amt:.2f}"
            ))

    def _generate(self):
        if not self.cart_items:
            messagebox.showwarning("Empty", "Cart is empty")
            return
            
        fname = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile="Invoice.pdf")
        if not fname:
            return
            
        buyer = {
            "name": self.ent_name.get() or "Customer",
            "contact": self.ent_contact.get(),
            "date": self.ent_date.get(),
            "is_interstate": self.var_interstate.get(),
            "is_tax_inclusive": self.var_inclusive.get()
        }
        
        inv_num = f"INV-{int(datetime.datetime.now().timestamp())}"
        
        self.app.billing.generate_invoice(self.cart_items, buyer, inv_num, fname)
        messagebox.showinfo("Success", f"Invoice {inv_num} saved!")
        self.clear_cart()

# --- Analytics Screen ---
class AnalyticsScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        from core.analytics import AnalyticsManager
        self.analytics = AnalyticsManager(app_context.inventory)
        self._init_ui()

    def _init_ui(self):
        ttk.Label(self, text="Business Analytics Dashboard", font=('Segoe UI', 16, 'bold')).pack(pady=10)
        
        # 1. KPI Cards
        kpi_frame = ttk.Frame(self)
        kpi_frame.pack(fill=tk.X, pady=10)
        
        self.card_stock = self._create_card(kpi_frame, "Total Stock", "0")
        self.card_val = self._create_card(kpi_frame, "Stock Value", "₹0")
        self.card_sold = self._create_card(kpi_frame, "Total Sold", "0")
        self.card_profit = self._create_card(kpi_frame, "Net Profit (Sold)", "₹0")
        
        # 2. Detailed Stats (Split View)
        split_frame = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        split_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Top Models Table
        frame_models = ttk.LabelFrame(split_frame, text="Top Selling / Stocked Models")
        split_frame.add(frame_models, minsize=300)
        
        cols = ('model', 'count')
        self.tree_models = ttk.Treeview(frame_models, columns=cols, show='headings')
        self.tree_models.heading('model', text='Model Name')
        self.tree_models.heading('count', text='Count')
        self.tree_models.pack(fill=tk.BOTH, expand=True)
        
        # Supplier Stats (Simple Text for now or Graph placeholder)
        frame_supp = ttk.LabelFrame(split_frame, text="Supplier Performance")
        split_frame.add(frame_supp, minsize=250)
        
        self.txt_supp = tk.Text(frame_supp, font=('Consolas', 10), state='disabled')
        self.txt_supp.pack(fill=tk.BOTH, expand=True)

        # 3. Actions
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Refresh Dashboard", command=self.refresh).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Export Detailed Report (PDF)", command=self._export_pdf).pack(side=tk.RIGHT)

    def _create_card(self, parent, title, value):
        frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(frame, text=title, font=('Segoe UI', 10)).pack(pady=(5,0))
        lbl_val = ttk.Label(frame, text=value, font=('Segoe UI', 14, 'bold'), foreground='#007acc')
        lbl_val.pack(pady=(0,5))
        return lbl_val

    def on_show(self):
        self.refresh()

    def refresh(self):
        stats = self.analytics.get_summary()
        s_counts = stats.get('status_counts', {})
        
        total_in = s_counts.get('IN', 0) + s_counts.get('RTN', 0)
        total_out = s_counts.get('OUT', 0)
        
        # Update Cards
        self.card_stock.config(text=str(total_in))
        self.card_val.config(text=f"₹{stats['total_value']:,.0f}")
        self.card_sold.config(text=str(total_out))
        
        p_color = 'green' if stats['realized_profit'] >= 0 else 'red'
        self.card_profit.config(text=f"₹{stats['realized_profit']:,.0f}", foreground=p_color)
        
        # Update Tree
        for item in self.tree_models.get_children():
            self.tree_models.delete(item)
            
        for m, c in stats['top_models'].items():
            self.tree_models.insert('', tk.END, values=(m, c))
            
        # Update Supplier Text
        supp_txt = ""
        for s, c in stats['supplier_dist'].items():
            supp_txt += f"{s:<20} : {c}\n"
            
        self.txt_supp.configure(state='normal')
        self.txt_supp.delete(1.0, tk.END)
        self.txt_supp.insert(tk.END, supp_txt)
        self.txt_supp.configure(state='disabled')

    def _export_pdf(self):
        f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile="Analytics_Report.pdf")
        if not f: return
        
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        
        c = canvas.Canvas(f, pagesize=A4)
        width, height = A4
        
        c.setFont("Helvetica-Bold", 18)
        c.drawString(20*mm, height - 20*mm, "Business Analytics Report")
        
        c.setFont("Helvetica", 12)
        c.drawString(20*mm, height - 30*mm, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")
        
        stats = self.analytics.get_summary()
        
        # Summary
        y = height - 50*mm
        c.drawString(20*mm, y, f"Total Items: {stats['total_items']}")
        c.drawString(20*mm, y-10*mm, f"Total Stock Value: Rs. {stats['total_value']:,.2f}")
        c.drawString(20*mm, y-20*mm, f"Total Sold: {stats.get('status_counts', {}).get('OUT', 0)}")
        c.drawString(20*mm, y-30*mm, f"Net Profit (Realized): Rs. {stats['realized_profit']:,.2f}")
        
        c.drawString(20*mm, y-50*mm, "Top Models:")
        y_mod = y - 60*mm
        c.setFont("Helvetica", 10)
        for m, count in stats['top_models'].items():
            c.drawString(25*mm, y_mod, f"- {m}: {count}")
            y_mod -= 5*mm
            
        c.save()
        messagebox.showinfo("Export", "Report saved successfully.")

# --- Settings Screen ---
class SettingsScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.vars = {}
        
        # Form
        form = ttk.LabelFrame(self, text="Application Settings", padding=20)
        form.place(relx=0.5, rely=0.3, anchor='center')
        
        # Fields
        fields = [
            ("Store Name", "store_name"),
            ("Label Width (mm)", "label_width_mm"),
            ("Label Height (mm)", "label_height_mm"),
            ("GST Default %", "gst_default_percent"),
            ("Price Markup %", "price_markup_percent"),
            ("Auto Unique ID Prefix", "auto_unique_id_prefix")
        ]
        
        for idx, (lbl, key) in enumerate(fields):
            ttk.Label(form, text=lbl).grid(row=idx, column=0, sticky=tk.W, pady=8)
            var = tk.StringVar()
            self.vars[key] = var
            ttk.Entry(form, textvariable=var, width=30).grid(row=idx, column=1, pady=8, padx=10)
            
        ttk.Button(form, text="Save Changes", command=self._save).grid(row=len(fields), column=1, pady=20, sticky=tk.E)

    def on_show(self):
        # Load values
        for key, var in self.vars.items():
            val = self.app.app_config.get(key)
            var.set(str(val))

    def _save(self):
        try:
            # Validate numeric
            float(self.vars['label_width_mm'].get())
            float(self.vars['label_height_mm'].get())
            float(self.vars['gst_default_percent'].get())
            
            for key, var in self.vars.items():
                val = var.get()
                try:
                    val = float(val)
                except:
                    pass
                self.app.app_config.set(key, val)
                
            messagebox.showinfo("Saved", "Settings updated successfully.")
        except ValueError:
            messagebox.showerror("Error", "Please check numeric fields.")# --- Color Screen ---
class ColorScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        from core.color_registry import ColorRegistry
        self.registry = ColorRegistry()
        
        # UI
        lbl = ttk.Label(self, text="Manage Mobile Colors", font=('Segoe UI', 12, 'bold'))
        lbl.pack(pady=10)
        
        frame_add = ttk.Frame(self)
        frame_add.pack(pady=5)
        
        self.ent_color = ttk.Entry(frame_add, width=20)
        self.ent_color.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_add, text="Add Color", command=self._add).pack(side=tk.LEFT)
        
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Button(self, text="Delete Selected", command=self._delete).pack(pady=5)
        
        self._refresh()

    def _refresh(self):
        self.listbox.delete(0, tk.END)
        for c in self.registry.get_all():
            self.listbox.insert(tk.END, c)

    def _add(self):
        c = self.ent_color.get().strip()
        if c:
            self.registry.add_color(c)
            self.ent_color.delete(0, tk.END)
            self._refresh()

    def _delete(self):
        sel = self.listbox.curselection()
        if sel:
            c = self.listbox.get(sel[0])
            if messagebox.askyesno("Confirm", f"Delete color '{c}'?"):
                self.registry.remove_color(c)
                self._refresh()
# --- Search Screen ---
class SearchScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self._init_ui()

    def _init_ui(self):
        lbl_title = ttk.Label(self, text="ID Lookup / Mobile Details", font=('Segoe UI', 14, 'bold'))
        lbl_title.pack(pady=10)

        # Search Bar
        frame_search = ttk.Frame(self)
        frame_search.pack(fill=tk.X, pady=10)
        
        ttk.Label(frame_search, text="Enter Mobile ID:").pack(side=tk.LEFT, padx=5)
        self.ent_id = ttk.Entry(frame_search, width=20, font=('Segoe UI', 12))
        self.ent_id.pack(side=tk.LEFT, padx=5)
        self.ent_id.bind('<Return>', lambda e: self._do_lookup())
        
        ttk.Button(frame_search, text="Lookup", command=self._do_lookup).pack(side=tk.LEFT, padx=10)

        # Details Area
        self.details_frame = ttk.LabelFrame(self, text="Mobile Details", padding=20)
        self.details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.txt_details = tk.Text(self.details_frame, font=('Consolas', 12), state='disabled', bg='#f9f9f9')
        self.txt_details.pack(fill=tk.BOTH, expand=True)

    def on_show(self):
        self.ent_id.focus_set()

    def _do_lookup(self):
        iid = self.ent_id.get().strip()
        if not iid:
            return
            
        df = self.app.inventory.get_inventory()
        if df.empty:
            messagebox.showinfo("Empty", "Inventory is empty")
            return
            
        # Search by unique_id (string match)
        match = df[df['unique_id'].astype(str) == iid]
        
        if match.empty:
            self._update_text(f"No mobile found with ID: {iid}")
            return
            
        row = match.iloc[0]
        
        details = f"""
ITEM DETAILS
------------
ID          : {row.get('unique_id')}
Status      : {row.get('status')}
IMEI        : {row.get('imei')}
Model       : {row.get('model')}
RAM/ROM     : {row.get('ram_rom')}
Color       : {row.get('color', 'N/A')}

PRICING
-------
Buy Price   : ₹{row.get('price_original', 0):,.2f}
Sell Price  : ₹{row.get('price', 0):,.2f}
Markup %    : {self.app.app_config.get('price_markup_percent', 0)}%

INVENTORY INFO
--------------
Supplier    : {row.get('supplier')}
Source File : {row.get('source_file')}
Last Updated: {row.get('last_updated')}
Notes       : {row.get('notes', '')}
"""
        self._update_text(details)

    def _update_text(self, text):
        self.txt_details.configure(state='normal')
        self.txt_details.delete(1.0, tk.END)
        self.txt_details.insert(tk.END, text)
        self.txt_details.configure(state='disabled')
# --- Status Update Screen ---
class StatusScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.history = []
        self._init_ui()

    def _init_ui(self):
        ttk.Label(self, text="Quick Status Update (IN / OUT / RTN)", font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        # 1. Mode Selection
        frame_mode = ttk.LabelFrame(self, text="Select New Status", padding=10)
        frame_mode.pack(fill=tk.X, pady=5)
        
        self.var_status = tk.StringVar(value="OUT")
        
        ttk.Radiobutton(frame_mode, text="SOLD (OUT)", variable=self.var_status, value="OUT").pack(side=tk.LEFT, padx=20)
        ttk.Radiobutton(frame_mode, text="RETURN (RTN)", variable=self.var_status, value="RTN").pack(side=tk.LEFT, padx=20)
        ttk.Radiobutton(frame_mode, text="STOCK IN (IN)", variable=self.var_status, value="IN").pack(side=tk.LEFT, padx=20)
        
        # 2. Input
        frame_input = ttk.Frame(self, padding=10)
        frame_input.pack(fill=tk.X)
        
        # Search Type Toggle
        self.var_search_type = tk.StringVar(value="ID")
        frame_search_type = ttk.Frame(frame_input)
        frame_search_type.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(frame_search_type, text="Search By: ").pack(side=tk.LEFT)
        ttk.Radiobutton(frame_search_type, text="Unique ID (Exact)", variable=self.var_search_type, value="ID").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(frame_search_type, text="Model / IMEI", variable=self.var_search_type, value="MODEL").pack(side=tk.LEFT, padx=10)
        
        ttk.Label(frame_input, text="Scan/Enter Value:", font=('Segoe UI', 12)).pack(anchor=tk.W)
        self.ent_id = ttk.Entry(frame_input, font=('Segoe UI', 16))
        self.ent_id.pack(fill=tk.X, pady=5)
        self.ent_id.bind('<Return>', self._process_entry)
        
        # 3. Actions
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Update Status", command=self._process_entry).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Undo Last", command=self._undo).pack(side=tk.LEFT)
        
        # 4. Log
        self.txt_log = tk.Text(self, font=('Consolas', 10), state='disabled', height=10)
        self.txt_log.pack(fill=tk.BOTH, expand=True, pady=10)

    def on_show(self):
        self.ent_id.focus_set()

    def _process_entry(self, event=None):
        val = self.ent_id.get().strip()
        status = self.var_status.get()
        search_type = self.var_search_type.get()
        
        if not val: return
        
        df = self.app.inventory.get_inventory()
        target_id = None
        
        if search_type == "ID":
            # Exact Match
            if df[df['unique_id'].astype(str) == val].empty:
                self._log(f"Error: ID {val} not found.")
                self.ent_id.delete(0, tk.END)
                return
            target_id = val
        else:
            # Model/IMEI Search
            mask = df.apply(lambda x: val.lower() in str(x['model']).lower() or val in str(x['imei']), axis=1)
            matches = df[mask]
            
            if matches.empty:
                self._log(f"No match for '{val}'")
                return
            elif len(matches) == 1:
                target_id = str(matches.iloc[0]['unique_id'])
            else:
                # Multiple Matches - Ask User
                target_id = self._pick_from_list(matches)
                if not target_id: return

        # Update
        match = df[df['unique_id'].astype(str) == str(target_id)]
        if match.empty: return # Should not happen
        
        success = self.app.inventory.update_item_status(target_id, status, write_to_excel=True)
        
        if success:
            model = match.iloc[0]['model']
            msg = f"Updated {target_id} ({model}) -> {status}"
            self._log(msg)
            
            # Save for undo
            self.history.append({
                "id": target_id,
                "prev_status": match.iloc[0]['status'],
                "new_status": status
            })
        else:
            self._log(f"Failed to update {target_id} (Excel Error)")
            
        self.ent_id.delete(0, tk.END)

    def _pick_from_list(self, matches):
        # Popup to pick one
        top = tk.Toplevel(self)
        top.title("Select Mobile")
        top.geometry("500x300")
        
        selected_id = [None]
        
        lb = tk.Listbox(top, font=('Consolas', 10))
        lb.pack(fill=tk.BOTH, expand=True)
        
        for idx, row in matches.iterrows():
            txt = f"ID:{row['unique_id']} | {row['model']} | {row['imei']} | ₹{row['price']:,.0f}"
            lb.insert(tk.END, txt)
            
        def on_select():
            sel = lb.curselection()
            if sel:
                # Parse ID from text "ID:123 | ..."
                txt = lb.get(sel[0])
                uid = txt.split('|')[0].replace('ID:', '').strip()
                selected_id[0] = uid
                top.destroy()
                
        ttk.Button(top, text="Select", command=on_select).pack(pady=5)
        
        top.transient(self)
        top.wait_window()
        return selected_id[0]

    def _undo(self):
        if not self.history: 
            messagebox.showinfo("Undo", "Nothing to undo.")
            return
            
        last = self.history.pop()
        iid = last['id']
        prev = last['prev_status']
        
        self.app.inventory.update_item_status(iid, prev, write_to_excel=True)
        self._log(f"UNDO: Reverted {iid} -> {prev}")

    def _log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.configure(state='normal')
        self.txt_log.insert(tk.END, f"[{ts}] {msg}\n")
        self.txt_log.see(tk.END)
        self.txt_log.configure(state='disabled')
# --- Edit Data Screen ---
class EditDataScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.current_id = None
        self._init_ui()

    def _init_ui(self):
        ttk.Label(self, text="Edit Mobile Data", font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        # Search
        frame_search = ttk.Frame(self)
        frame_search.pack(fill=tk.X, pady=10)
        ttk.Label(frame_search, text="Enter ID:").pack(side=tk.LEFT, padx=5)
        self.ent_search = ttk.Entry(frame_search)
        self.ent_search.pack(side=tk.LEFT, padx=5)
        self.ent_search.bind('<Return>', self._lookup)
        ttk.Button(frame_search, text="Load", command=self._lookup).pack(side=tk.LEFT)
        
        # Form
        self.form_frame = ttk.LabelFrame(self, text="Edit Details", padding=15)
        self.form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.vars = {}
        fields = ['model', 'imei', 'price_original', 'color', 'notes']
        
        for idx, f in enumerate(fields):
            ttk.Label(self.form_frame, text=f.title()).grid(row=idx, column=0, sticky=tk.W, pady=5)
            var = tk.StringVar()
            self.vars[f] = var
            
            if f == 'color':
                from core.color_registry import ColorRegistry
                colors = ColorRegistry().get_all()
                combo = ttk.Combobox(self.form_frame, textvariable=var, values=colors)
                combo.grid(row=idx, column=1, padx=10, pady=5, sticky=tk.EW)
            else:
                ttk.Entry(self.form_frame, textvariable=var, width=40).grid(row=idx, column=1, padx=10, pady=5)
            
        ttk.Button(self.form_frame, text="Save Changes", command=self._save).grid(row=len(fields), column=1, pady=20, sticky=tk.E)

    def on_show(self):
        self.ent_search.focus_set()

    def _lookup(self, event=None):
        iid = self.ent_search.get().strip()
        if not iid: return
        
        df = self.app.inventory.get_inventory()
        match = df[df['unique_id'].astype(str) == iid]
        
        if match.empty:
            messagebox.showwarning("Error", "ID not found")
            return
            
        row = match.iloc[0]
        self.current_id = iid
        self.vars['model'].set(row.get('model', ''))
        self.vars['imei'].set(row.get('imei', ''))
        self.vars['price_original'].set(str(row.get('price_original', '')))
        self.vars['color'].set(row.get('color', ''))
        self.vars['notes'].set(row.get('notes', ''))

    def _save(self):
        if not self.current_id: return
        
        # Collect data
        updates = {k: v.get() for k, v in self.vars.items()}
        
        # Validate Price
        try:
            updates['price_original'] = float(updates['price_original'])
        except:
            messagebox.showerror("Error", "Price must be numeric")
            return

        # Update Logic (Need to add generic update_excel_row to inventory)
        if self.app.inventory.update_item_data(self.current_id, updates):
            messagebox.showinfo("Success", "Data updated in Excel and Memory.")
            self.app.inventory.reload_all() # Refresh to be safe
        else:
            messagebox.showerror("Error", "Failed to update Excel.")
