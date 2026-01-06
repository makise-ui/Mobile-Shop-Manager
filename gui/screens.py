import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import ImageTk
from .dialogs import MapColumnsDialog, ZPLPreviewDialog, PrinterSelectionDialog, FileSelectionDialog, ItemSelectionDialog
import pandas as pd
import datetime
import os
import glob
import ttkbootstrap as tb
from ttkbootstrap.toast import ToastNotification

# --- Base Screen Class ---
class BaseScreen(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent, padding=15)
        self.app = app_context
    
    def on_show(self):
        """Called when screen becomes visible"""
        pass

# --- Dashboard Screen ---
class DashboardScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self._init_ui()

    def _init_ui(self):
        ttk.Label(self, text="Dashboard", font=('Segoe UI', 20, 'bold')).pack(pady=20)
        
        # Cards Frame
        f_cards = ttk.Frame(self)
        f_cards.pack(fill=tk.X, padx=20, pady=10)
        
        # Card 1: Total Stock
        self.card_stock = self._create_card(f_cards, "Total Items", "0")
        self.card_stock.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Card 2: Total Value
        self.card_value = self._create_card(f_cards, "Stock Value", "₹0")
        self.card_value.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Card 3: Today's Sales (Placeholder)
        self.card_sales = self._create_card(f_cards, "Today's Sales", "0")
        self.card_sales.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Recent Activity
        ttk.Label(self, text="Recent Activity", font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        self.tree_log = ttk.Treeview(self, columns=('time', 'action', 'details'), show='headings', height=10)
        self.tree_log.heading('time', text='Time')
        self.tree_log.column('time', width=100)
        self.tree_log.heading('action', text='Action')
        self.tree_log.column('action', width=120)
        self.tree_log.heading('details', text='Details')
        self.tree_log.column('details', width=400)
        
        self.tree_log.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    def _create_card(self, parent, title, value):
        f = ttk.LabelFrame(parent, text=title, padding=15)
        lbl = ttk.Label(f, text=value, font=('Segoe UI', 24, 'bold'), foreground="#007acc")
        lbl.pack()
        f.lbl_val = lbl # Store ref
        return f

    def on_show(self):
        self._refresh_stats()
        self._refresh_log()

    def _refresh_stats(self):
        df = self.app.inventory.get_inventory()
        if df.empty:
            count = 0
            val = 0
        else:
            # Filter Available
            available = df[df['status'] == 'IN']
            count = len(available)
            val = available['price'].sum()
            
        self.card_stock.lbl_val.config(text=str(count))
        self.card_value.lbl_val.config(text=f"₹{val:,.0f}")
        self.card_sales.lbl_val.config(text="-")

    def _refresh_log(self):
        for i in self.tree_log.get_children():
            self.tree_log.delete(i)
        logs = self.app.activity_logger.get_logs(limit=20)
        for log in logs:
            self.tree_log.insert('', tk.END, values=(log['timestamp'], log['action'], log['details']))

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
        
        # Preview Toggle
        self.var_show_preview = tk.BooleanVar(value=False)
        ttk.Checkbutton(action_frame, text="Show Preview", variable=self.var_show_preview, command=self._toggle_preview).pack(side=tk.RIGHT, padx=10)
        
        ttk.Button(action_frame, text="Refresh Data", command=self.refresh_data).pack(side=tk.RIGHT, padx=5)

        # -- Main Content --
        self.paned = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # 1. Treeview (List)
        # Added 'check' column for checkboxes
        cols = ('check', 'unique_id', 'imei', 'model', 'ram_rom', 'price_original', 'price', 'supplier', 'status')
        self.tree = ttk.Treeview(self.paned, columns=cols, show='headings', selectmode='extended')
        
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
        self.tree.column('price_original', width=80, anchor='e')
        
        self.tree.heading('price', text='Price (Sell)')
        self.tree.column('price', width=80, anchor='e')
        
        self.tree.heading('supplier', text='Supplier')
        self.tree.column('supplier', width=100)
        
        self.tree.heading('status', text='Status')
        self.tree.column('status', width=70)

        # Color Tags
        self.tree.tag_configure('old', background='#fff3cd') # Yellowish
        self.tree.tag_configure('very_old', background='#f8d7da') # Reddish

        # Scrollbars
        scroll_y = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_x = ttk.Scrollbar(self.tree, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scroll_y.set, xscroll=scroll_x.set)
        
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree.bind('<<TreeviewSelect>>', self._on_row_click) 
        self.tree.bind('<ButtonRelease-1>', self._on_click_check) # Specific click handler
        
        self.paned.add(self.tree, minsize=400, width=700)

        # 2. Preview Panel (Right) - Hidden by default
        self.preview_frame = ttk.LabelFrame(self.paned, text="Label Preview", padding=10)
        
        self.lbl_preview = ttk.Label(self.preview_frame, text="Select item to preview", anchor="center")
        self.lbl_preview.pack(fill=tk.BOTH, expand=True)
        
        self.lbl_info = ttk.Label(self.preview_frame, text="")
        self.lbl_info.pack(fill=tk.X, pady=5)
        
        self.checked_ids = set() # Store unique_ids of checked items

    def _toggle_preview(self):
        if self.var_show_preview.get():
            self.paned.add(self.preview_frame, minsize=250)
        else:
            self.paned.remove(self.preview_frame)

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
        existing_iids = set()
            
        for idx, row in df.iterrows():
            uid = str(row.get('unique_id', ''))
            
            # Ensure unique IID for Treeview
            original_uid = uid
            if uid in existing_iids:
                uid = f"{uid}_{idx}"
            existing_iids.add(uid)
            
            # Checkbox state
            check_mark = "☑" if original_uid in self.checked_ids else "☐"
            
            vals = (
                check_mark,
                original_uid, # Display original ID text
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
        items = self.tree.selection()
        if not items:
            # Fallback to checked items if any
            if self.checked_ids:
                # Convert checked IDs to iids
                # In tree render, iid=uid.
                items = list(self.checked_ids)
            else:
                messagebox.showwarning("Select", "Please check or select items to update.")
                return

        # --- "Mark Sold" Enhanced Flow ---
        if new_status == "OUT":
            self._show_mark_sold_dialog(items)
            return

        # --- Standard Flow (for RTN/IN) ---
        if not messagebox.askyesno("Confirm", f"Mark {len(items)} items as {new_status}?"):
            return
            
        success_count = 0
        for iid in items:
            # iid is the unique_id (or uid_idx, but we stripped idx in _render_tree? 
            # Wait, _render_tree handles duplicates by appending _idx.
            # We need the real unique_id.
            real_uid = str(iid).split('_')[0]
            
            if self.app.inventory.update_item_status(real_uid, new_status, write_to_excel=True):
                success_count += 1
                
        messagebox.showinfo("Done", f"Updated {success_count} items to {new_status}")
        self.checked_ids.clear()
        self.refresh_data()

    def _show_mark_sold_dialog(self, items):
        # items is a list of iids
        
        # 1. Gather Data
        df = self.app.inventory.get_inventory()
        selected_rows = []
        for iid in items:
            real_uid = str(iid).split('_')[0]
            # Find row
            mask = df['unique_id'].astype(str) == real_uid
            if mask.any():
                selected_rows.append(df[mask].iloc[0])
        
        if not selected_rows: return

        # 2. Dialog UI
        dlg = tk.Toplevel(self)
        dlg.title("Mark as Sold")
        dlg.geometry("400x350")
        dlg.transient(self)
        dlg.grab_set()
        
        ttk.Label(dlg, text=f"Marking {len(selected_rows)} items as SOLD (OUT)", font=('Segoe UI', 11, 'bold')).pack(pady=10)
        
        # Auto Invoice Options
        frame_opts = ttk.LabelFrame(dlg, text="Invoice Options", padding=10)
        frame_opts.pack(fill=tk.X, padx=10, pady=5)
        
        var_auto = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_opts, text="Generate Invoice Automatically", variable=var_auto).pack(anchor=tk.W)
        
        # Date
        f_date = ttk.Frame(frame_opts)
        f_date.pack(fill=tk.X, pady=5)
        ttk.Label(f_date, text="Date:").pack(side=tk.LEFT)
        ent_date = ttk.Entry(f_date, width=12)
        ent_date.insert(0, str(datetime.date.today()))
        ent_date.pack(side=tk.LEFT, padx=5)
        
        # Buyer
        f_buyer = ttk.Frame(frame_opts)
        f_buyer.pack(fill=tk.X, pady=5)
        ttk.Label(f_buyer, text="Buyer:").pack(side=tk.LEFT)
        ent_buyer = ttk.Entry(f_buyer, width=20)
        ent_buyer.insert(0, "Walk-in")
        ent_buyer.pack(side=tk.LEFT, padx=5)
        
        # Tax
        var_inc = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_opts, text="Tax Inclusive Prices", variable=var_inc).pack(anchor=tk.W, pady=5)
        
        def do_confirm():
            # 1. Update Status
            success_count = 0
            for row in selected_rows:
                if self.app.inventory.update_item_status(row['unique_id'], "OUT", write_to_excel=True):
                    success_count += 1
            
            # 2. Generate Invoice
            if var_auto.get() and success_count > 0:
                self._create_auto_invoice(selected_rows, ent_buyer.get(), ent_date.get(), var_inc.get())
                
            dlg.destroy()
            self.checked_ids.clear()
            self.refresh_data()
            messagebox.showinfo("Success", f"Sold {success_count} items." + ("\nInvoice Generated." if var_auto.get() else ""))

        ttk.Button(dlg, text="CONFIRM SOLD", command=do_confirm, style="Accent.TButton").pack(pady=20)

    def _create_auto_invoice(self, rows, buyer_name, date_str, is_inclusive):
        # Convert rows to cart_item format
        cart = []
        for row in rows:
            cart.append({
                'unique_id': row['unique_id'],
                'model': row['model'],
                'price': float(row.get('price', 0)),
                'imei': row.get('imei', '')
            })
            
        buyer = {
            "name": buyer_name,
            "contact": "",
            "date": date_str,
            "is_interstate": False,
            "is_tax_inclusive": is_inclusive
        }
        
        ts = int(datetime.datetime.now().timestamp())
        safe_name = "".join([c for c in buyer_name if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = f"{safe_name}_{ts}.pdf"
        save_path = self.app.app_config.get_invoices_dir() / filename
        inv_num = f"INV-{ts}"
        
        try:
            success, verify_hash, pdf_total = self.app.billing.generate_invoice(cart, buyer, inv_num, str(save_path))
            
            if success:
                # Save Registry
                try:
                    import json
                    from pathlib import Path
                    reg_path = Path.home() / "Documents" / "4BrosManager" / "config" / "invoice_registry.json"
                    registry = {}
                    if reg_path.exists():
                        with open(reg_path, 'r') as f: registry = json.load(f)
                        
                    registry[verify_hash] = {
                        "inv_no": inv_num,
                        "date": date_str,
                        "amount": f"{pdf_total:.2f}",
                        "buyer": buyer_name
                    }
                    with open(reg_path, 'w') as f: json.dump(registry, f, indent=4)
                except: pass
                
        except Exception as e:
            messagebox.showerror("Invoice Error", f"Failed to auto-generate invoice: {e}")

# --- Files Screen ---
class ManageFilesScreen(BaseScreen):
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
        
        # Store keys to map listbox index back to config key
        self.list_keys = []
        
        for key, data in mappings.items():
            status = self.app.inventory.file_status.get(key, "Unknown")
            supplier = data.get('supplier', 'Mixed/None')
            
            # Display: [OK] /path/to/file.xlsx (Sheet: Sheet1, Supplier: ABC)
            file_path = data.get('file_path', key)
            sheet = data.get('sheet_name', 'Default')
            
            display_text = f"[{status}] {file_path} (Sheet: {sheet}, Supplier: {supplier})"
            self.listbox.insert(tk.END, display_text)
            self.list_keys.append(key)

    def _add_file(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv")])
        for fp in file_paths:
            # Always open dialog to allow sheet selection
            # even if file is already mapped (could be different sheet)
            from .dialogs import MapColumnsDialog
            MapColumnsDialog(self.winfo_toplevel(), fp, self._on_mapping_save)
        
        # Refresh happens in callback, but call it here just in case of cancel/close
        # Actually _on_mapping_save handles refresh.

    def _edit_mapping(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selection", "Please select a file to edit mapping.")
            return
            
        key = self.list_keys[sel[0]]
        mapping_data = self.app.app_config.mappings.get(key)
        
        if not mapping_data: return
        
        fp = mapping_data.get('file_path', key)
        if '::' in fp: fp = fp.split('::')[0] # Safety
        
        from .dialogs import MapColumnsDialog
        MapColumnsDialog(self.winfo_toplevel(), fp, self._on_mapping_save, current_mapping=mapping_data)

    def _remove_file(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selection", "Please select a file to remove.")
            return

        key = self.list_keys[sel[0]]
        
        if messagebox.askyesno("Confirm", f"Remove inventory source?\n{key}"):
            # We need to expose remove logic in config that takes a KEY
            # Currently remove_file_mapping takes 'file_path' and does `del mappings[str(file_path)]`
            # This works if we pass the key!
            self.app.app_config.remove_file_mapping(key)
            self.app.inventory.reload_all()
            self.app.watcher.refresh_watch_list()
            self._refresh_list()

    def _on_mapping_save(self, key, mapping_data):
        # Key here is either file_path or composite key passed from Dialog
        self.app.app_config.set_file_mapping(key, mapping_data)
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
        
        # Search Mode
        ttk.Label(scan_frame, text="Search By:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.var_search_mode = tk.StringVar(value="ID")
        self.combo_mode = ttk.Combobox(scan_frame, textvariable=self.var_search_mode, values=["ID", "IMEI", "Model"], state="readonly", width=8)
        self.combo_mode.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(scan_frame, text="Scan/Search:", font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT, padx=5)
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
        cart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        cols = ('id', 'model', 'price', 'gst')
        self.tree = ttk.Treeview(cart_frame, columns=cols, show='headings', height=8)
        self.tree.heading('id', text='ID')
        self.tree.heading('model', text='Model')
        self.tree.heading('price', text='Price')
        self.tree.heading('gst', text='Tax Est.')
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 3. Discount & Totals
        adj_frame = ttk.Frame(self)
        adj_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(adj_frame, text="Discount/Exchange Note:").pack(side=tk.LEFT, padx=5)
        self.ent_disc_reason = ttk.Entry(adj_frame, width=20)
        self.ent_disc_reason.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(adj_frame, text="Disc:").pack(side=tk.LEFT, padx=(10,5))
        
        self.var_disc_type = tk.StringVar(value="AMT") # AMT or PERCENT
        
        self.ent_disc_amt = ttk.Entry(adj_frame, width=8)
        self.ent_disc_amt.insert(0, "0")
        self.ent_disc_amt.pack(side=tk.LEFT, padx=5)
        self.ent_disc_amt.bind('<KeyRelease>', self._calculate_totals)
        
        # Toggle Buttons (Small)
        f_toggle = ttk.Frame(adj_frame)
        f_toggle.pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(f_toggle, text="₹", variable=self.var_disc_type, value="AMT", command=self._calculate_totals).pack(side=tk.LEFT)
        ttk.Radiobutton(f_toggle, text="%", variable=self.var_disc_type, value="PERCENT", command=self._calculate_totals).pack(side=tk.LEFT)

        self.lbl_grand_total = ttk.Label(adj_frame, text="Payable: ₹0.00", font=('Segoe UI', 12, 'bold'), foreground="#007acc")
        self.lbl_grand_total.pack(side=tk.RIGHT, padx=20)
        
        # 4. Actions
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Clear Cart", command=self.clear_cart).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Edit Price", command=self._edit_price).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(btn_frame, text="Print Invoice", command=self._print_invoice).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Save PDF", command=self._save_invoice).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="SAVE & SOLD", command=self._save_and_sold, style="Accent.TButton").pack(side=tk.RIGHT, padx=20)

    def on_show(self):
        self.ent_scan.focus_set()

    def _save_and_sold(self):
        if not self.cart_items:
            messagebox.showwarning("Empty", "Cart is empty")
            return

        # 1. First Save the Invoice
        path = self._generate_file()
        if not path:
            return # Generation failed or cancelled

        # 2. Then Mark as Sold
        buyer_name = self.ent_name.get().strip()
        buyer_contact = self.ent_contact.get().strip()
        
        count = 0
        updates = {
            "status": "OUT",
            "buyer": buyer_name,
            "buyer_contact": buyer_contact
        }
        
        for item in self.cart_items:
            if self.app.inventory.update_item_data(item['unique_id'], updates):
                count += 1
                
        messagebox.showinfo("Success", f"Invoice saved.\nMarked {count} items as SOLD (OUT).")
        self.clear_cart()

    def _handle_sold_item(self, item):
        buyer = item.get('buyer', 'Unknown')
        
        # Custom Dialog
        top = tk.Toplevel(self)
        top.title("Item Already Sold")
        top.geometry("400x350")
        top.transient(self)
        top.grab_set()
        
        msg = f"This item is marked as SOLD.\n\nModel: {item.get('model')}\nBuyer: {buyer}\n\nWhat would you like to do?"
        ttk.Label(top, text=msg, padding=20, font=('Segoe UI', 10)).pack()
        
        def action_rtn():
            # Mark RTN then Add
            self.app.inventory.update_item_status(item['unique_id'], 'RTN', write_to_excel=True)
            self.add_items([item])
            top.destroy()
            self.ent_scan.delete(0, tk.END)

        def action_in():
             # Mark IN then Add
            self.app.inventory.update_item_status(item['unique_id'], 'IN', write_to_excel=True)
            self.add_items([item])
            top.destroy()
            self.ent_scan.delete(0, tk.END)

        def action_anyway():
            # Just Add
            self.add_items([item])
            top.destroy()
            self.ent_scan.delete(0, tk.END)

        def action_cancel():
            top.destroy()
            self.ent_scan.delete(0, tk.END)

        # Buttons
        ttk.Button(top, text="Mark Return (RTN) & Sell", command=action_rtn).pack(fill=tk.X, padx=40, pady=5)
        ttk.Button(top, text="Mark Stock (IN) & Sell", command=action_in).pack(fill=tk.X, padx=40, pady=5)
        ttk.Button(top, text="Sell Anyway (Keep History)", command=action_anyway).pack(fill=tk.X, padx=40, pady=5)
        ttk.Button(top, text="Cancel", command=action_cancel).pack(fill=tk.X, padx=40, pady=(20, 10))

    def _on_scan(self, event):
        q = self.ent_scan.get().strip()
        if not q: return
        
        mode = self.var_search_mode.get()
        df = self.app.inventory.get_inventory()
        match = pd.DataFrame()
        
        if mode == "ID":
            match = df[df['unique_id'].astype(str) == q]
        elif mode == "IMEI":
            match = df[df['imei'].astype(str).str.contains(q, na=False)]
        elif mode == "Model":
            match = df[df['model'].astype(str).str.contains(q, case=False, na=False)]
            
        # Deduplicate
        if not match.empty:
            match = match.drop_duplicates(subset=['unique_id'])
            
        if match.empty:
            messagebox.showwarning("Not Found", f"No item found for {mode}: {q}")
            self.ent_scan.select_range(0, tk.END)
            return
            
        if len(match) == 1:
            item = match.iloc[0].to_dict()
            
            # Check Sold Status
            if str(item.get('status', '')).upper() == 'OUT':
                self._handle_sold_item(item)
                return
                
            self.add_items([item])
            self.ent_scan.delete(0, tk.END)
        else:
            # Multiple matches
            items = match.to_dict('records')
            ItemSelectionDialog(self.winfo_toplevel(), items, lambda item: self.add_items([item]))
            self.ent_scan.delete(0, tk.END)

    def _edit_price(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection", "Select an item in the cart to edit price.")
            return
            
        idx = self.tree.index(sel[0])
        if idx < len(self.cart_items):
            item = self.cart_items[idx]
            old = item.get('price', 0)
            new_p = simpledialog.askfloat("Edit Price", f"New price for {item.get('model')}:", initialvalue=old, parent=self)
            
            if new_p is not None:
                item['price'] = new_p
                self._refresh_cart()

    def add_items(self, items):
        self.cart_items.extend(items)
        self._refresh_cart()

    def clear_cart(self):
        self.cart_items = []
        self.ent_disc_amt.delete(0, tk.END)
        self.ent_disc_amt.insert(0, "0")
        self.ent_disc_reason.delete(0, tk.END)
        self._refresh_cart()

    def _calculate_totals(self, event=None):
        subtotal = sum(float(item.get('price', 0)) for item in self.cart_items)
        try:
            val = float(self.ent_disc_amt.get())
        except ValueError:
            val = 0.0
            
        disc_amt = 0.0
        if self.var_disc_type.get() == "PERCENT":
            disc_amt = subtotal * (val / 100.0)
        else:
            disc_amt = val
        
        final = subtotal - disc_amt
        # Show details in label? For now just Payable
        self.lbl_grand_total.config(text=f"Payable: ₹{final:,.2f}")

    def _refresh_cart(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        tax_rate = self.app.app_config.get('gst_default_percent', 18.0)
        is_inclusive = self.var_inclusive.get()
        
        for item in self.cart_items:
            price = float(item.get('price', 0))
            
            if is_inclusive:
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
        
        self._calculate_totals()

    def _generate_file(self):
        if not self.cart_items:
            messagebox.showwarning("Empty", "Cart is empty")
            return None
            
        buyer_name = self.ent_name.get().strip() or "Customer"
        safe_name = "".join([c for c in buyer_name if c.isalnum() or c in (' ', '-', '_')]).strip()
        ts = int(datetime.datetime.now().timestamp())
        filename = f"{safe_name}_{ts}.pdf"
        
        save_path = self.app.app_config.get_invoices_dir() / filename
        
        buyer = {
            "name": buyer_name,
            "contact": self.ent_contact.get(),
            "date": self.ent_date.get(),
            "is_interstate": self.var_interstate.get(),
            "is_tax_inclusive": self.var_inclusive.get()
        }
        
        discount = None
        try:
            val = float(self.ent_disc_amt.get())
            if val > 0:
                reason = self.ent_disc_reason.get().strip() or "Discount"
                subtotal = sum(float(item.get('price', 0)) for item in self.cart_items)
                
                d_amt = 0.0
                if self.var_disc_type.get() == "PERCENT":
                    d_amt = subtotal * (val / 100.0)
                    reason += f" ({val}%)"
                else:
                    d_amt = val
                
                discount = {
                    "reason": reason,
                    "amount": d_amt
                }
        except:
            pass
        
        inv_num = f"INV-{ts}"
        
        # Call Generator first to get the authoritative Hash
        try:
            success, verify_hash, pdf_total = self.app.billing.generate_invoice(self.cart_items, buyer, inv_num, str(save_path), discount=discount)
            
            if success:
                # --- Save to Signature Registry ---
                try:
                    import json
                    from pathlib import Path
                    reg_path = Path.home() / "Documents" / "4BrosManager" / "config" / "invoice_registry.json"
                    
                    registry = {}
                    if reg_path.exists():
                        try:
                            with open(reg_path, 'r') as f:
                                registry = json.load(f)
                        except: pass
                    
                    registry[verify_hash] = {
                        "inv_no": inv_num,
                        "date": str(datetime.date.today()),
                        "amount": f"{pdf_total:.2f}",
                        "buyer": buyer_name
                    }
                    
                    with open(reg_path, 'w') as f:
                        json.dump(registry, f, indent=4)
                except Exception as e:
                    print(f"Registry Save Error: {e}")

                return str(save_path)
            else:
                return None
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate invoice: {e}")
            return None

    def _save_invoice(self):
        path = self._generate_file()
        if path:
            messagebox.showinfo("Success", f"Invoice saved to:\n{path}")
            self.clear_cart()

    def _print_invoice(self):
        path = self._generate_file()
        if not path: return
        
        printers = self.app.printer.get_system_printers()
        if not printers:
            messagebox.showwarning("No Printers", "No Windows printers found. PDF saved only.")
            return

        def on_printer_select(printer_name):
            if self.app.printer.print_pdf(path, printer_name):
                messagebox.showinfo("Sent", f"Invoice sent to {printer_name}")
                self.clear_cart()
            else:
                messagebox.showerror("Error", "Failed to print.")

        PrinterSelectionDialog(self.winfo_toplevel(), printers, on_printer_select)

class InvoiceHistoryScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self._init_ui()

    def _init_ui(self):
        # Toolbar
        tb = ttk.Frame(self)
        tb.pack(fill=tk.X, pady=10)
        
        ttk.Label(tb, text="Generated Invoices", font=('Segoe UI', 14, 'bold')).pack(side=tk.LEFT)
        
        # Filter Frame
        f_filter = ttk.LabelFrame(self, text="Filter", padding=5)
        f_filter.pack(fill=tk.X, pady=5)
        
        ttk.Label(f_filter, text="Buyer:").pack(side=tk.LEFT, padx=5)
        self.ent_filter_buyer = ttk.Entry(f_filter, width=15)
        self.ent_filter_buyer.pack(side=tk.LEFT, padx=5)
        self.ent_filter_buyer.bind('<Return>', lambda e: self._refresh_list())
        
        ttk.Label(f_filter, text="Date (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        self.ent_filter_date = ttk.Entry(f_filter, width=12)
        self.ent_filter_date.pack(side=tk.LEFT, padx=5)
        self.ent_filter_date.bind('<Return>', lambda e: self._refresh_list())
        
        ttk.Button(f_filter, text="Search", command=self._refresh_list).pack(side=tk.LEFT, padx=10)
        ttk.Button(f_filter, text="Clear", command=self._clear_filters).pack(side=tk.LEFT)
        
        ttk.Button(tb, text="Refresh List", command=self._refresh_list).pack(side=tk.RIGHT, padx=5)
        
        # Actions
        actions = ttk.Frame(self)
        actions.pack(fill=tk.X, pady=5)
        ttk.Button(actions, text="Open PDF", command=self._open_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions, text="Print", command=self._print_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions, text="Delete", command=self._delete_invoice).pack(side=tk.LEFT, padx=5)
        
        # List
        cols = ('date', 'name', 'filename', 'size')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', selectmode='extended')
        self.tree.heading('date', text='Date')
        self.tree.column('date', width=120)
        self.tree.heading('name', text='Customer Name')
        self.tree.column('name', width=200)
        self.tree.heading('filename', text='Filename')
        self.tree.heading('size', text='Size')
        self.tree.column('size', width=80)
        
        self.tree.pack(fill=tk.BOTH, expand=True)

        # --- Verification UI ---
        ttk.Separator(self, orient='horizontal').pack(fill=tk.X, pady=10)
        
        v_frame = ttk.LabelFrame(self, text="Verify Digital Signature", padding=10)
        v_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(v_frame, text="Enter Code from Invoice:").pack(side=tk.LEFT)
        self.ent_verify = ttk.Entry(v_frame, width=30, font=('Courier', 10))
        self.ent_verify.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(v_frame, text="CHECK VALIDITY", command=self._verify_code, style="Accent.TButton").pack(side=tk.LEFT)

    def _verify_code(self):
        code = self.ent_verify.get().strip().upper()
        if not code: return
        
        # Load Registry
        import json
        from pathlib import Path
        reg_path = Path.home() / "Documents" / "4BrosManager" / "config" / "invoice_registry.json"
        
        if not reg_path.exists():
            messagebox.showerror("Error", "No invoice registry found. Cannot verify.")
            return
            
        try:
            with open(reg_path, 'r') as f:
                registry = json.load(f)
                
            clean_code = code.replace(" ", "")
            data = registry.get(clean_code)
            if data:
                msg = f"✅ VALID SIGNATURE\n\nInvoice: {data.get('inv_no')}\nDate: {data.get('date')}\nAmount: {data.get('amount')}\nBuyer: {data.get('buyer')}"
                messagebox.showinfo("Legit", msg)
            else:
                messagebox.showerror("FAKE", "❌ INVALID SIGNATURE\n\nThis code does not match any invoice in the system.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Verification failed: {e}")

    def on_show(self):
        self._refresh_list()

    def _clear_filters(self):
        self.ent_filter_buyer.delete(0, tk.END)
        self.ent_filter_date.delete(0, tk.END)
        self._refresh_list()

    def _refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        inv_dir = self.app.app_config.get_invoices_dir()
        if not inv_dir.exists(): return
        
        # Filters
        f_buyer = self.ent_filter_buyer.get().strip().lower()
        f_date = self.ent_filter_date.get().strip()
        
        # Get PDF files
        files = list(inv_dir.glob("*.pdf"))
        # Sort by modification time (newest first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        for f in files:
            stats = f.stat()
            dt_obj = datetime.datetime.fromtimestamp(stats.st_mtime)
            dt = dt_obj.strftime("%Y-%m-%d %H:%M")
            date_only = dt_obj.strftime("%Y-%m-%d")
            size = f"{stats.st_size / 1024:.1f} KB"
            
            # Try to guess name from filename: Name_Timestamp.pdf
            name = f.stem.split('_')[0] if '_' in f.stem else "Unknown"
            
            # Filter Logic
            if f_buyer and f_buyer not in name.lower():
                continue
            if f_date and f_date not in date_only:
                continue
            
            self.tree.insert('', tk.END, values=(dt, name, f.name, size), iid=str(f))

    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select at least one invoice.")
            return None
        return sel # Return list of iids

    def _open_pdf(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select an invoice.")
            return
            
        path = sel[0] # Open only first
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file: {e}")

    def _print_pdf(self):
        selection = self._get_selected()
        if not selection: return
        
        printers = self.app.printer.get_system_printers()
        if not printers:
            messagebox.showwarning("No Printers", "No Windows printers found.")
            return

        def on_printer_select(printer_name):
            success_count = 0
            for path in selection:
                if self.app.printer.print_pdf(path, printer_name):
                    success_count += 1
            
            if success_count > 0:
                messagebox.showinfo("Sent", f"Sent {success_count} files to {printer_name}")
            else:
                messagebox.showerror("Error", "Failed to print files.")

        PrinterSelectionDialog(self.winfo_toplevel(), printers, on_printer_select)

    def _delete_invoice(self):
        selection = self._get_selected()
        if not selection: return
        
        if messagebox.askyesno("Confirm", f"Delete {len(selection)} invoice(s) permanently?"):
            try:
                for path in selection:
                    os.remove(path)
                self._refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")

    # --- Verification UI ---
        
        # Separator
        ttk.Separator(self, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Verify Frame
        v_frame = ttk.LabelFrame(self, text="Verify Digital Signature", padding=10)
        v_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(v_frame, text="Enter Code from Invoice:").pack(side=tk.LEFT)
        self.ent_verify = ttk.Entry(v_frame, width=30, font=('Courier', 10))
        self.ent_verify.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(v_frame, text="CHECK VALIDITY", command=self._verify_code, style="Accent.TButton").pack(side=tk.LEFT)
        
    def _verify_code(self):
        code = self.ent_verify.get().strip().upper()
        if not code: return
        
        # Load Registry
        import json
        from pathlib import Path
        reg_path = Path.home() / "Documents" / "4BrosManager" / "config" / "invoice_registry.json"
        
        if not reg_path.exists():
            messagebox.showerror("Error", "No invoice registry found. Cannot verify.")
            return
            
        try:
            with open(reg_path, 'r') as f:
                registry = json.load(f)
                
            # Registry format: { "CODE": { "inv_no": "...", "amount": "..." } }
            # Code on paper is formatted with spaces "AAAA BBBB...", strip them
            clean_code = code.replace(" ", "")
            
            data = registry.get(clean_code)
            if data:
                msg = f"✅ VALID SIGNATURE\n\nInvoice: {data.get('inv_no')}\nDate: {data.get('date')}\nAmount: {data.get('amount')}\nBuyer: {data.get('buyer')}"
                messagebox.showinfo("Legit", msg)
            else:
                messagebox.showerror("FAKE", "❌ INVALID SIGNATURE\n\nThis code does not match any invoice in the system.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Verification failed: {e}")

class ActivityLogScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self._init_ui()

    def _init_ui(self):
        # Header
        tb = ttk.Frame(self)
        tb.pack(fill=tk.X, pady=10)
        ttk.Label(tb, text="Activity Log", font=('Segoe UI', 14, 'bold')).pack(side=tk.LEFT)
        ttk.Button(tb, text="Refresh", command=self._refresh_list).pack(side=tk.RIGHT, padx=5)
        ttk.Button(tb, text="Clear Logs", command=self._clear_logs).pack(side=tk.RIGHT, padx=5)
        
        # Tree
        cols = ('time', 'action', 'details')
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        self.tree.heading('time', text='Timestamp')
        self.tree.column('time', width=150)
        self.tree.heading('action', text='Action')
        self.tree.column('action', width=120)
        self.tree.heading('details', text='Details')
        self.tree.column('details', width=400)
        
        # Scroll
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
            # Format time for readability
            ts = log.get('timestamp', '')
            try:
                dt = datetime.datetime.fromisoformat(ts)
                ts = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
                
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
        # Header
        tb = ttk.Frame(self)
        tb.pack(fill=tk.X, pady=10)
        ttk.Label(tb, text="Data Conflicts", font=('Segoe UI', 14, 'bold')).pack(side=tk.LEFT)
        ttk.Button(tb, text="Refresh", command=self._refresh_list).pack(side=tk.RIGHT, padx=5)
        ttk.Button(tb, text="Resolve Selected", command=self._resolve).pack(side=tk.RIGHT, padx=5)
        
        # Info
        ttk.Label(self, text="Conflicts occur when the same IMEI appears in multiple Excel files or rows.", font=('Segoe UI', 9, 'italic')).pack(fill=tk.X, pady=(0,10))
        
        # Container for Tree + Scrollbars
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Tree
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
        
        # Scrollbars
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
            from .dialogs import ConflictResolutionDialog
            ConflictResolutionDialog(self.winfo_toplevel(), c_data, self.app._resolve_conflict_callback)

# --- Analytics Screen ---
class AnalyticsScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        from core.analytics import AnalyticsManager
        self.analytics = AnalyticsManager(app_context.inventory)
        self._init_ui()

    def _init_ui(self):
        # Main Scrollable Container (in case of small screens)
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)

        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Title
        ttk.Label(self.scroll_frame, text="Business Intelligence Dashboard", font=('Segoe UI', 20, 'bold'), bootstyle="primary").pack(pady=20, padx=20, anchor=tk.W)

        # --- Row 1: KPI Cards ---
        kpi_container = ttk.Frame(self.scroll_frame)
        kpi_container.pack(fill=tk.X, padx=20, pady=10)

        self.kpi_stock = self._add_kpi_card(kpi_container, "STOCK VALUE", "₹0", "success")
        self.kpi_sold = self._add_kpi_card(kpi_container, "ITEMS SOLD", "0", "info")
        self.kpi_revenue = self._add_kpi_card(kpi_container, "TOTAL REVENUE", "₹0", "primary")
        self.kpi_profit = self._add_kpi_card(kpi_container, "EST. PROFIT", "₹0", "warning")

        # --- Row 2: Charts & Rankings ---
        charts_frame = ttk.Frame(self.scroll_frame)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left Column: Brand Distribution
        self.brand_frame = ttk.LabelFrame(charts_frame, text=" Brand Distribution ", bootstyle="info")
        self.brand_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 10))
        self.brand_inner = ttk.Frame(self.brand_frame, padding=15)
        self.brand_inner.pack(fill=tk.BOTH, expand=True)

        # Right Column: Top Buyers
        self.buyer_frame = ttk.LabelFrame(charts_frame, text=" Top Buyers Performance ", bootstyle="primary")
        self.buyer_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(10, 0))
        self.buyer_inner = ttk.Frame(self.buyer_frame, padding=15)
        self.buyer_inner.pack(fill=tk.BOTH, expand=True)

        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)

        # --- Row 3: Buyer Details (Interactive) ---
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

        # --- Row 4: Detail Tables ---
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

        # Actions
        btn_frame = ttk.Frame(self.scroll_frame, padding=20)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="REFRESH DASHBOARD", command=self.refresh, bootstyle="success-outline", width=25).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="EXPORT ANALYTICS (PDF)", command=self._export_pdf, bootstyle="danger-outline").pack(side=tk.RIGHT)

    def _add_kpi_card(self, parent, title, value, color):
        card = ttk.Frame(parent, bootstyle=f"{color}.TFrame", padding=1) # Border effect
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        inner = ttk.Frame(card, padding=15)
        inner.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(inner, text=title, font=('Segoe UI', 9, 'bold'), foreground="gray").pack(anchor=tk.W)
        lbl_val = ttk.Label(inner, text=value, font=('Segoe UI', 18, 'bold'), bootstyle=color)
        lbl_val.pack(anchor=tk.W, pady=(5, 0))
        return lbl_val

    def on_show(self):
        self.refresh()

    def _show_buyer_history(self, buyer_name):
        """Populates the detail tree when a buyer is clicked."""
        self.history_frame.config(text=f" Purchase History: {buyer_name} ")
        for item in self.tree_history.get_children(): self.tree_history.delete(item)
        
        if hasattr(self, 'sold_data') and not self.sold_data.empty:
            matches = self.sold_data[self.sold_data['buyer'] == buyer_name]
            for _, row in matches.iterrows():
                self.tree_history.insert('', tk.END, values=(
                    row.get('model', 'Unknown'),
                    row.get('imei', '-'),
                    f"₹{row.get('price', 0):,.0f}",
                    row.get('last_updated', '-')[:10] # Just Date
                ))

    def refresh(self):
        stats = self.analytics.get_summary()
        df = self.app.inventory.get_inventory()

        # 1. Update KPIs
        self.kpi_stock.config(text=f"₹{stats['total_value']:,.0f}")
        self.kpi_sold.config(text=str(stats.get('status_counts', {}).get('OUT', 0)))
        
        # Calculate Revenue (Price of Sold items)
        sold_df = df[df['status'] == 'OUT']
        self.sold_data = sold_df # Store for interaction
        
        revenue = sold_df['price'].sum() if not sold_df.empty else 0
        self.kpi_revenue.config(text=f"₹{revenue:,.0f}")
        
        p_val = stats['realized_profit']
        p_color = "success" if p_val >= 0 else "danger"
        self.kpi_profit.config(text=f"₹{p_val:,.0f}", bootstyle=p_color)

        # 2. Update Brand Distribution
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

        # 3. Top Buyers (Rankings - Clickable!)
        for w in self.buyer_inner.winfo_children(): w.destroy()
        if not sold_df.empty:
            buyer_stats = sold_df.groupby('buyer').agg({'unique_id': 'count', 'price': 'sum'}).sort_values('price', ascending=False).head(5)
            
            for buyer, row in buyer_stats.iterrows():
                f = ttk.Frame(self.buyer_inner, cursor="hand2")
                f.pack(fill=tk.X, pady=5)
                
                # Highlight effect on click
                def on_click(event, b=buyer): 
                    self._show_buyer_history(b)
                
                name_lbl = ttk.Label(f, text=f"👤 {str(buyer)[:15]}", font=('Segoe UI', 10))
                name_lbl.pack(side=tk.LEFT)
                
                price_lbl = ttk.Label(f, text=f"₹{row['price']:,.0f}", bootstyle="primary")
                price_lbl.pack(side=tk.RIGHT)
                
                count_lbl = ttk.Label(f, text=f"{int(row['unique_id'])} items | ", foreground="gray")
                count_lbl.pack(side=tk.RIGHT)
                
                # Bind clicks to frame and all labels inside it
                f.bind("<Button-1>", on_click)
                name_lbl.bind("<Button-1>", on_click)
                price_lbl.bind("<Button-1>", on_click)
                count_lbl.bind("<Button-1>", on_click)
        else:
            ttk.Label(self.buyer_inner, text="No sales data recorded yet.", foreground="gray").pack(pady=20)

        # 4. Details Tree
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
        # Implementation remains similar but with richer data
        f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=f"Analytics_{datetime.date.today()}.pdf")
        if not f: return
        
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        
        c = canvas.Canvas(f, pagesize=A4)
        w, h = A4
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.setStrokeColorRGB(0, 0.48, 0.8) # Primary Blue
        c.drawString(20*mm, h - 25*mm, "Business Performance Report")
        c.line(20*mm, h-28*mm, 190*mm, h-28*mm)
        
        c.setFont("Helvetica", 10)
        c.drawString(20*mm, h - 35*mm, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")

        stats = self.analytics.get_summary()
        df = self.app.inventory.get_inventory()
        
        # Stats Grid
        y = h - 50*mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(25*mm, y, "FINANCIAL SUMMARY")
        
        c.setFont("Helvetica", 11)
        y -= 10*mm
        c.drawString(25*mm, y, f"Total Inventory Value : Rs. {stats['total_value']:,.2f}")
        y -= 7*mm
        c.drawString(25*mm, y, f"Total Items in Stock : {stats.get('status_counts', {}).get('IN', 0)}")
        y -= 7*mm
        c.drawString(25*mm, y, f"Total Items Sold     : {stats.get('status_counts', {}).get('OUT', 0)}")
        y -= 7*mm
        c.drawString(25*mm, y, f"Net Realized Profit  : Rs. {stats['realized_profit']:,.2f}")

        # Top Models
        y -= 20*mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(25*mm, y, "TOP STOCKING MODELS")
        c.setFont("Helvetica", 10)
        y -= 8*mm
        for m, count in list(stats['top_models'].items())[:10]:
            c.drawString(30*mm, y, f"• {m:<30} : {count} units")
            y -= 6*mm
            if y < 30*mm: break

        c.showPage()
        c.save()
        messagebox.showinfo("Export Success", f"Analytics report saved to:\n{f}")


# --- Settings Screen ---
class SettingsScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.style = tb.Style()
        self.vars = {}
        self.text_widgets = {}
        self._init_ui()

    def _init_ui(self):
        ttk.Label(self, text="Application Settings", font=('Segoe UI', 16, 'bold')).pack(pady=20)
        
        # Tabs
        tabs = ttk.Notebook(self)
        tabs.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # --- Tab 1: General ---
        tab_gen = ttk.Frame(tabs, padding=20)
        tabs.add(tab_gen, text="General")
        
        # Helper for grid
        def add_entry(parent, label, key, r, width=30):
            ttk.Label(parent, text=label).grid(row=r, column=0, sticky=tk.W, pady=5)
            var = tk.StringVar(value=str(self.app.app_config.get(key, '')))
            self.vars[key] = var
            ttk.Entry(parent, textvariable=var, width=width).grid(row=r, column=1, padx=10, sticky=tk.W)
            return r + 1

        r = 0
        r = add_entry(tab_gen, "Store Name:", "store_name", r)
        r = add_entry(tab_gen, "Auto-ID Prefix:", "auto_unique_id_prefix", r, width=10)
        r = add_entry(tab_gen, "Price Markup %:", "price_markup_percent", r, width=10)
        
        self.var_buyer = tk.BooleanVar(value=self.app.app_config.get("enable_buyer_tracking", True))
        ttk.Checkbutton(tab_gen, text="Enable Buyer Tracking (Save to Excel)", variable=self.var_buyer).grid(row=r, column=0, columnspan=2, sticky=tk.W, pady=10)

        # --- Tab 2: Printing ---
        tab_print = ttk.Frame(tabs, padding=20)
        tabs.add(tab_print, text="Printing")
        
        r = 0
        r = add_entry(tab_print, "Label Width (mm):", "label_width_mm", r, width=10)
        r = add_entry(tab_print, "Label Height (mm):", "label_height_mm", r, width=10)

        # --- Tab 3: Invoice ---
        tab_inv = ttk.Frame(tabs, padding=20)
        tabs.add(tab_inv, text="Invoice")
        
        r = 0
        r = add_entry(tab_inv, "GSTIN:", "store_gstin", r)
        r = add_entry(tab_inv, "Phone / Contact:", "store_contact", r)
        r = add_entry(tab_inv, "GST Default %:", "gst_default_percent", r, width=10)
        
        # Address
        ttk.Label(tab_inv, text="Store Address:").grid(row=r, column=0, sticky=tk.NW, pady=5)
        txt_addr = tk.Text(tab_inv, height=4, width=40, font=('Segoe UI', 10))
        txt_addr.insert('1.0', self.app.app_config.get('store_address', ''))
        txt_addr.grid(row=r, column=1, padx=10, pady=5)
        self.text_widgets['store_address'] = txt_addr
        r += 1
        
        # Terms
        ttk.Label(tab_inv, text="Invoice Terms:").grid(row=r, column=0, sticky=tk.NW, pady=5)
        txt_terms = tk.Text(tab_inv, height=4, width=40, font=('Segoe UI', 10))
        txt_terms.insert('1.0', self.app.app_config.get('invoice_terms', ''))
        txt_terms.grid(row=r, column=1, padx=10, pady=5)
        self.text_widgets['invoice_terms'] = txt_terms
        
        # --- Tab 4: Appearance ---
        tab_app = ttk.Frame(tabs, padding=20)
        tabs.add(tab_app, text="Appearance")
        
        ttk.Label(tab_app, text="Theme:", font=('bold')).pack(anchor=tk.W)
        
        # Ensure full sorted list of themes
        themes = sorted(self.style.theme_names())
        current = self.app.app_config.get('theme_name', 'cosmo')
        
        # Helper label for dark mode
        ttk.Label(tab_app, text="(Try 'darkly', 'superhero', 'cyborg' for Dark Mode)", font=('Segoe UI', 9), foreground='gray').pack(anchor=tk.W, pady=(0,5))
        self.var_theme = tk.StringVar(value=current)
        
        cb = ttk.Combobox(tab_app, textvariable=self.var_theme, values=themes, state="readonly", width=20)
        cb.pack(anchor=tk.W, pady=5)
        cb.bind("<<ComboboxSelected>>", self._on_theme_change)
        
        # Save Button
        ttk.Button(self, text="Save All Settings", command=self._save, style="success.TButton").pack(pady=20)

    def _on_theme_change(self, event):
        self.style.theme_use(self.var_theme.get())

    def _save(self):
        try:
            # Save Vars
            for key, var in self.vars.items():
                val = var.get()
                # Try convert to float if it looks like one (for mm, price)
                try:
                    if key in ['label_width_mm', 'label_height_mm', 'price_markup_percent', 'gst_default_percent']:
                        val = float(val)
                except: pass
                self.app.app_config.set(key, val)
            
            # Save Text Widgets
            for key, widget in self.text_widgets.items():
                self.app.app_config.set(key, widget.get("1.0", tk.END).strip())
                
            # Save Specifics
            self.app.app_config.set("enable_buyer_tracking", self.var_buyer.get())
            self.app.app_config.set('theme_name', self.var_theme.get())
            
            ToastNotification(
                title="Saved", 
                message="Settings updated successfully.", 
                duration=3000, 
                bootstyle="success"
            ).show_toast()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values")# --- Manage Data Screen (Colors & Buyers) ---
class ManageDataScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        from core.data_registry import DataRegistry
        self.registry = DataRegistry()
        
        # UI
        ttk.Label(self, text="Manage App Data", font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Colors
        self.tab_colors = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_colors, text="Mobile Colors")
        self._init_list_ui(self.tab_colors, "Color", self.registry.get_colors, self.registry.add_color, self.registry.remove_color)
        
        # Tab 2: Buyers
        self.tab_buyers = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_buyers, text="Frequent Buyers")
        self._init_list_ui(self.tab_buyers, "Buyer Name", self.registry.get_buyers, self.registry.add_buyer, self.registry.remove_buyer)

        # Tab 3: Grades
        self.tab_grades = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_grades, text="Grades")
        self._init_list_ui(self.tab_grades, "Grade", self.registry.get_grades, self.registry.add_grade, self.registry.remove_grade)

    def _init_list_ui(self, parent, item_name, get_func, add_func, remove_func):
        frame_add = ttk.Frame(parent, padding=10)
        frame_add.pack(fill=tk.X)
        
        ent = ttk.Entry(frame_add, width=30)
        ent.pack(side=tk.LEFT, padx=5)
        
        lb = tk.Listbox(parent, font=('Segoe UI', 10))
        lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def refresh():
            lb.delete(0, tk.END)
            for item in get_func():
                lb.insert(tk.END, item)
                
        def add():
            val = ent.get().strip()
            if val:
                add_func(val)
                ent.delete(0, tk.END)
                refresh()
                
        def remove():
            sel = lb.curselection()
            if sel:
                val = lb.get(sel[0])
                if messagebox.askyesno("Confirm", f"Delete '{val}'?"):
                    remove_func(val)
                    refresh()

        ttk.Button(frame_add, text=f"Add {item_name}", command=add).pack(side=tk.LEFT)
        ttk.Button(parent, text="Delete Selected", command=remove).pack(pady=10)
        
        # Initial load
        refresh()

# --- Search Screen ---
class SearchScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self._init_ui()

    def _init_ui(self):
        # Header
        ttk.Label(self, text="Search & History", font=('Segoe UI', 16, 'bold')).pack(pady=(10, 5))
        
        # Split Panes
        self.paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- LEFT: Search ---
        self.left_pane = ttk.Frame(self.paned)
        self.paned.add(self.left_pane, minsize=300, width=350)
        
        # Search Box
        f_search = ttk.LabelFrame(self.left_pane, text="Find Item", padding=10)
        f_search.pack(fill=tk.X, pady=5, padx=5)
        
        self.var_search_type = tk.StringVar(value="ID")
        f_radios = ttk.Frame(f_search)
        f_radios.pack(fill=tk.X)
        ttk.Radiobutton(f_radios, text="Unique ID", variable=self.var_search_type, value="ID").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(f_radios, text="Model/IMEI", variable=self.var_search_type, value="MODEL").pack(side=tk.LEFT, padx=5)
        
        self.ent_search = ttk.Entry(f_search, font=('Segoe UI', 12))
        self.ent_search.pack(fill=tk.X, pady=5)
        self.ent_search.bind('<Return>', lambda e: self._do_lookup())
        ttk.Button(f_search, text="SEARCH", command=self._do_lookup).pack(fill=tk.X, pady=5)
        
        # Results List (for multiple matches)
        self.list_results = tk.Listbox(self.left_pane, font=('Segoe UI', 10))
        self.list_results.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.list_results.bind('<<ListboxSelect>>', self._on_result_select)
        
        # --- RIGHT: Details Card ---
        self.right_pane = ttk.Frame(self.paned)
        self.paned.add(self.right_pane, minsize=400)
        
        # Card Header
        self.f_header = tk.Frame(self.right_pane, bg='white', bd=1, relief=tk.SOLID)
        self.f_header.pack(fill=tk.X, padx=10, pady=10)
        
        self.lbl_model = tk.Label(self.f_header, text="No Item Selected", font=('Segoe UI', 18, 'bold'), bg='white', fg='#333', anchor='w')
        self.lbl_model.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        f_sub = tk.Frame(self.f_header, bg='white')
        f_sub.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.lbl_price = tk.Label(f_sub, text="--", font=('Segoe UI', 14, 'bold'), bg='white', fg='#007acc')
        self.lbl_price.pack(side=tk.LEFT)
        
        self.lbl_status = tk.Label(f_sub, text="STATUS", font=('Segoe UI', 10, 'bold'), bg='#eee', fg='#333', padx=8, pady=2)
        self.lbl_status.pack(side=tk.RIGHT)
        
        # Details Notebook
        self.nb_details = ttk.Notebook(self.right_pane)
        self.nb_details.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Info
        self.tab_info = ttk.Frame(self.nb_details)
        self.nb_details.add(self.tab_info, text="Details & Specs")
        
        self.txt_info = tk.Text(self.tab_info, font=('Consolas', 11), state='disabled', padx=10, pady=10, bg="#f9f9f9")
        self.txt_info.pack(fill=tk.BOTH, expand=True)
        
        # Tab 2: History Timeline
        self.tab_history = ttk.Frame(self.nb_details)
        self.nb_details.add(self.tab_history, text="History & Logs")
        
        self.txt_timeline = tk.Text(self.tab_history, font=('Segoe UI', 11), state='disabled', padx=20, pady=20, bg="#ffffff", relief=tk.FLAT)
        scroll_hist = ttk.Scrollbar(self.tab_history, orient=tk.VERTICAL, command=self.txt_timeline.yview)
        self.txt_timeline.configure(yscrollcommand=scroll_hist.set)
        
        scroll_hist.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_timeline.pack(fill=tk.BOTH, expand=True)
        
        # Tags for styling
        self.txt_timeline.tag_configure("center", justify='center')
        self.txt_timeline.tag_configure("status", font=('Segoe UI', 12, 'bold'), foreground="#007acc")
        self.txt_timeline.tag_configure("date", font=('Segoe UI', 9), foreground="#666")
        self.txt_timeline.tag_configure("line", font=('Consolas', 14), foreground="#ccc")

    def on_show(self):
        self.ent_search.focus_set()

    def _do_lookup(self):
        query = self.ent_search.get().strip()
        if not query: return
        
        df = self.app.inventory.get_inventory()
        self.list_results.delete(0, tk.END)
        self.matches = [] # Store raw rows
        
        search_type = self.var_search_type.get()
        match_df = pd.DataFrame()
        
        if search_type == "ID":
            match_df = df[df['unique_id'].astype(str) == query]
        else:
            mask = df.apply(lambda x: query.lower() in str(x['model']).lower() or query in str(x['imei']), axis=1)
            match_df = df[mask]
            
        if match_df.empty:
            self.lbl_model.config(text="No Results Found")
            self.lbl_price.config(text="--")
            self.lbl_status.config(text="--", bg="#eee", fg="#333")
            self._clear_details()
            return
            
        # Populate List
        for _, row in match_df.iterrows():
            self.matches.append(row)
            self.list_results.insert(tk.END, f"{row['model']} | ID: {row['unique_id']}")
            
        # Auto-select first
        self.list_results.selection_set(0)
        self._on_result_select(None)

    def _on_result_select(self, event):
        sel = self.list_results.curselection()
        if not sel: return
        
        idx = sel[0]
        row = self.matches[idx]
        self._show_details(row)

    def _show_details(self, row):
        # 1. Header
        self.lbl_model.config(text=row.get('model', 'Unknown'))
        price = row.get('price', 0)
        self.lbl_price.config(text=f"₹{price:,.2f}")
        
        status = str(row.get('status', 'IN')).upper()
        bg_col = "#d4edda" if status == 'IN' else "#f8d7da" # Green/Red tint
        fg_col = "#155724" if status == 'IN' else "#721c24"
        self.lbl_status.config(text=status, bg=bg_col, fg=fg_col)
        
        # Parse Source File (Handle composite key path::sheet)
        raw_source = str(row.get('source_file', ''))
        import os
        if '::' in raw_source:
            parts = raw_source.split('::')
            fname = os.path.basename(parts[0])
            display_source = f"{fname} (Sheet: {parts[1]})"
        else:
            display_source = os.path.basename(raw_source)

        # 2. Details Text
        info = f"""
UNIQUE ID   : {row.get('unique_id')}
IMEI        : {row.get('imei')}
RAM/ROM     : {row.get('ram_rom')}
COLOR       : {row.get('color')}
GRADE       : {row.get('grade', '-')}
CONDITION   : {row.get('condition', '-')}
SUPPLIER    : {row.get('supplier')}

BUY PRICE   : ₹{row.get('price_original', 0):,.2f}
SELL PRICE  : ₹{row.get('price', 0):,.2f}

BUYER INFO
----------
Name        : {row.get('buyer', '-')}
Contact     : {row.get('buyer_contact', '-')}

METADATA
--------
Source File : {display_source}
Last Updated: {row.get('last_updated')}
Notes       : {row.get('notes', '')}
"""
        self.txt_info.configure(state='normal')
        self.txt_info.delete(1.0, tk.END)
        self.txt_info.insert(tk.END, info)
        self.txt_info.configure(state='disabled')
        
        # 3. History Timeline
        self.txt_timeline.configure(state='normal')
        self.txt_timeline.delete(1.0, tk.END)
            
        # Fetch from Registry
        reg_meta = self.app.inventory.id_registry.get_metadata(row['unique_id'])
        history = reg_meta.get('history', [])
        
        if not history:
            # Fallback entry
            self.txt_timeline.insert(tk.END, "INITIAL ENTRY\n", ("status", "center"))
            self.txt_timeline.insert(tk.END, f"Recorded on {row.get('last_updated')}\n", ("date", "center"))
        else:
            # Sort chronological (Oldest first for timeline flow)
            history = sorted(history, key=lambda x: x.get('ts', ''))
            
            for i, h in enumerate(history):
                # Extract status if it's a status change
                disp_action = h.get('action')
                details = h.get('details', '')
                
                if "Moved from" in details:
                    # Clean up: just show the NEW status clearly
                    parts = details.split(" to ")
                    status_text = parts[1] if len(parts) > 1 else details
                else:
                    status_text = disp_action
                
                # Insert Entry
                self.txt_timeline.insert(tk.END, f"{status_text}\n", ("status", "center"))
                self.txt_timeline.insert(tk.END, f"on {h.get('ts')}\n", ("date", "center"))
                
                # Add connector line if not last
                if i < len(history) - 1:
                    self.txt_timeline.insert(tk.END, "   |   \n", ("line", "center"))
                    self.txt_timeline.insert(tk.END, "   |   \n", ("line", "center"))

        self.txt_timeline.configure(state='disabled')

    def _clear_details(self):
        self.txt_info.configure(state='normal')
        self.txt_info.delete(1.0, tk.END)
        self.txt_info.configure(state='disabled')
        self.txt_timeline.configure(state='normal')
        self.txt_timeline.delete(1.0, tk.END)
        self.txt_timeline.configure(state='disabled')


# --- Status Update Screen ---
class StatusScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        from core.data_registry import DataRegistry
        self.registry = DataRegistry()
        self.history = []
        self.current_item = None
        self.batch_list = [] # List of items scanned in batch mode
        self._init_ui()

    def _init_ui(self):
        # Header
        ttk.Label(self, text="Quick Status Update", font=('Segoe UI', 16, 'bold')).pack(pady=10)
        
        # Batch Toggle
        self.var_batch_mode = tk.BooleanVar(value=False)
        f_top = ttk.Frame(self)
        f_top.pack(fill=tk.X, padx=20)
        ttk.Checkbutton(f_top, text="BATCH MODE (Scan multiple, update at end)", variable=self.var_batch_mode, command=self._toggle_batch_ui).pack(side=tk.RIGHT)
        
        # Main Container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # --- Left Side: Scan & Details ---
        left_pane = ttk.LabelFrame(main_frame, text="1. Scan Item", padding=15)
        left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Search Type
        self.var_search_type = tk.StringVar(value="ID")
        f_type = ttk.Frame(left_pane)
        f_type.pack(fill=tk.X, pady=5)
        ttk.Label(f_type, text="Scan Mode:").pack(side=tk.LEFT)
        ttk.Radiobutton(f_type, text="Unique ID", variable=self.var_search_type, value="ID").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(f_type, text="Model/IMEI", variable=self.var_search_type, value="MODEL").pack(side=tk.LEFT, padx=10)
        
        # Input
        f_input = ttk.Frame(left_pane)
        f_input.pack(fill=tk.X, pady=10)
        self.ent_id = ttk.Entry(f_input, font=('Segoe UI', 14))
        self.ent_id.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.ent_id.bind('<Return>', self._lookup_item)
        ttk.Button(f_input, text="FIND", command=self._lookup_item, width=8).pack(side=tk.LEFT, padx=5)
        
        # --- Auto Invoice Settings (Moved to Scan Section) ---
        self.frame_inv_opts = ttk.LabelFrame(left_pane, text="Invoice Settings (for Sold items)", padding=5)
        self.frame_inv_opts.pack(fill=tk.X, pady=5)
        
        self.var_auto_inv = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.frame_inv_opts, text="Auto-Generate Invoice", variable=self.var_auto_inv).pack(anchor=tk.W)
        
        f_date = ttk.Frame(self.frame_inv_opts)
        f_date.pack(fill=tk.X, pady=2)
        ttk.Label(f_date, text="Date:").pack(side=tk.LEFT)
        self.ent_inv_date = ttk.Entry(f_date, width=12)
        self.ent_inv_date.insert(0, str(datetime.date.today()))
        self.ent_inv_date.pack(side=tk.LEFT, padx=5)
        
        self.var_tax_inc = tk.BooleanVar(value=False)
        ttk.Checkbutton(f_date, text="Tax Inc.", variable=self.var_tax_inc).pack(side=tk.LEFT, padx=5)
        
        # Details Box
        self.lbl_details = tk.Label(left_pane, text="Ready to scan...", font=('Consolas', 11), bg="#e8e8e8", relief=tk.SUNKEN, height=6, justify=tk.LEFT, anchor="nw", padx=10, pady=10)
        self.lbl_details.pack(fill=tk.BOTH, expand=True, pady=10)

        # --- Right Side: Action ---
        right_pane = ttk.LabelFrame(main_frame, text="2. Update Status", padding=15)
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Status Buttons (Big)
        self.var_status = tk.StringVar(value="OUT")
        
        btn_frame = ttk.Frame(right_pane)
        btn_frame.pack(fill=tk.X, pady=10)
        
        r_out = ttk.Radiobutton(btn_frame, text="SOLD (OUT)", variable=self.var_status, value="OUT", command=self._toggle_buyer_fields)
        r_rtn = ttk.Radiobutton(btn_frame, text="RETURN (RTN)", variable=self.var_status, value="RTN", command=self._toggle_buyer_fields)
        r_in  = ttk.Radiobutton(btn_frame, text="STOCK IN (IN)", variable=self.var_status, value="IN", command=self._toggle_buyer_fields)
        
        r_out.pack(fill=tk.X, pady=5)
        r_rtn.pack(fill=tk.X, pady=5)
        r_in.pack(fill=tk.X, pady=5)

        # Buyer Fields (Conditional)
        self.frame_buyer = ttk.Frame(right_pane, padding=10, relief=tk.RIDGE, borderwidth=1)
        self.frame_buyer.pack(fill=tk.X, pady=10)
        
        ttk.Label(self.frame_buyer, text="Buyer Name:").pack(anchor=tk.W)
        self.ent_buyer = ttk.Combobox(self.frame_buyer)
        self.ent_buyer.pack(fill=tk.X, pady=(0,5))
        self.ent_buyer.bind('<Return>', lambda e: self.ent_contact.focus_set())
        
        ttk.Label(self.frame_buyer, text="Contact No:").pack(anchor=tk.W)
        self.ent_contact = ttk.Entry(self.frame_buyer)
        self.ent_contact.pack(fill=tk.X, pady=(0,5))
        self.ent_contact.bind('<Return>', self._confirm_update)
        
        # Update Button
        self.btn_update = ttk.Button(right_pane, text="CONFIRM UPDATE", command=self._confirm_update, style="Accent.TButton")
        self.btn_update.pack(fill=tk.X, pady=(20, 10))
        
        ttk.Button(right_pane, text="UNDO LAST ACTION", command=self._undo).pack(fill=tk.X, pady=5)
        
        # --- Batch View (Hidden by default) ---
        self.batch_frame = ttk.Frame(self) # Will pack at bottom when active
        self.batch_tree = ttk.Treeview(self.batch_frame, columns=('id', 'model'), show='headings', height=6)
        self.batch_tree.heading('id', text='ID')
        self.batch_tree.heading('model', text='Model')
        self.batch_tree.column('id', width=60)
        self.batch_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        btn_batch_commit = ttk.Button(self.batch_frame, text="FINISH & REVIEW BATCH", command=self._finish_batch, style="Accent.TButton")
        btn_batch_commit.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        # --- Bottom: Log ---
        self.log_frame = ttk.LabelFrame(self, text="Recent Activity", padding=10)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.txt_log = tk.Text(self.log_frame, font=('Consolas', 9), state='disabled', height=5, bg="#f9f9f9")
        self.txt_log.pack(fill=tk.BOTH, expand=True)

    def on_show(self):
        self.ent_id.focus_set()
        self._refresh_buyers()
        self._toggle_buyer_fields()

    def _refresh_buyers(self):
        self.ent_buyer['values'] = self.registry.get_buyers()

    def _toggle_batch_ui(self):
        if self.var_batch_mode.get():
            # Show Batch UI, Hide Log
            self.log_frame.pack_forget()
            
            # Pack batch frame in the same spot (bottom)
            self.batch_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            self.btn_update.config(state='disabled') # Disable single update
            
            # Refresh list
            self._refresh_batch_list()
        else:
            # Show Log, Hide Batch UI
            self.batch_frame.pack_forget()
            
            self.log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            self.btn_update.config(state='normal')
            
            # Clear batch warning if needed?
            if self.batch_list:
                if messagebox.askyesno("Clear Batch", "Batch mode disabled. Clear current batch list?"):
                    self.batch_list = []
                else:
                    # Revert check
                    self.var_batch_mode.set(True)
                    self._toggle_batch_ui()

    def _refresh_batch_list(self):
        for i in self.batch_tree.get_children():
            self.batch_tree.delete(i)
        for item in self.batch_list:
            self.batch_tree.insert('', tk.END, values=(item['unique_id'], item['model']))

    def _toggle_buyer_fields(self):
        status = self.var_status.get()
        if status == "OUT":
            self.frame_buyer.pack(fill=tk.X, pady=10)
            self.btn_update.config(text="CONFIRM SALE")
        elif status == "RTN":
            self.frame_buyer.pack_forget()
            self.btn_update.config(text="CONFIRM RETURN")
        else:
            self.frame_buyer.pack_forget()
            self.btn_update.config(text="CONFIRM STOCK IN")

    def _pick_from_list(self, matches):
        # Popup to pick one
        top = tk.Toplevel(self)
        top.title("Select Mobile")
        top.geometry("600x400")
        
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
        
        # Make modal
        top.transient(self)
        top.grab_set()
        self.wait_window(top)
        return selected_id[0]

    def _log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.configure(state='normal')
        self.txt_log.insert(tk.END, f"[{ts}] {msg}\n")
        self.txt_log.see(tk.END)
        self.txt_log.configure(state='disabled')

    def _lookup_item(self, event=None):
        val = self.ent_id.get().strip()
        if not val: return
        
        df = self.app.inventory.get_inventory()
        search_type = self.var_search_type.get()
        match = pd.DataFrame()
        
        if search_type == "ID":
            match = df[df['unique_id'].astype(str) == val]
        else:
            mask = df.apply(lambda x: val.lower() in str(x['model']).lower() or val in str(x['imei']), axis=1)
            match = df[mask]
            
        if match.empty:
            self.lbl_details.config(text=f"NO MATCH FOUND FOR:\n'{val}'\n\nTry different ID or Check spelling.", fg="red")
            self.current_item = None
            self.ent_id.select_range(0, tk.END)
            return
            
        if len(match) > 1:
            uid = self._pick_from_list(match)
            if not uid: return
            match = df[df['unique_id'].astype(str) == str(uid)]
            
        self.current_item = match.iloc[0]
        
        # BATCH MODE LOGIC
        if self.var_batch_mode.get():
            # Add to batch and reset
            # Check if already in batch
            if any(str(x['unique_id']) == str(self.current_item['unique_id']) for x in self.batch_list):
                self._log(f"Already in batch: {val}")
            else:
                self.batch_list.append(self.current_item)
                self._refresh_batch_list()
                self.lbl_details.config(text=f"Added to batch: {self.current_item['model']}", fg="blue")
            
            self.ent_id.delete(0, tk.END)
            self.ent_id.focus_set()
            return

        # Normal Mode
        d = self.current_item
        status_color = "green" if d['status'] == 'IN' else "red"
        
        txt = f"MODEL : {d['model']}\nIMEI  : {d['imei']}\nCOLOR : {d['color']}\nPRICE : ₹{d['price']:,.0f}\nSTATUS: {d['status']}"
        self.lbl_details.config(text=txt, fg="black")
        
        # Auto-focus logic
        if self.var_status.get() == "OUT":
            self.ent_buyer.focus_set()

    def _finish_batch(self):
        if not self.batch_list:
            messagebox.showinfo("Empty", "Batch is empty")
            return
            
        # Review Dialog
        top = tk.Toplevel(self)
        top.title(f"Review Batch ({len(self.batch_list)} Items)")
        top.geometry("600x500")
        
        lbl = ttk.Label(top, text=f"Update all to: {self.var_status.get()}?", font=('bold'))
        lbl.pack(pady=10)
        
        # List
        frame_list = ttk.Frame(top)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10)
        
        tv = ttk.Treeview(frame_list, columns=('id', 'model', 'price'), show='headings')
        tv.heading('id', text='ID')
        tv.heading('model', text='Model')
        tv.heading('price', text='Price')
        tv.pack(fill=tk.BOTH, expand=True)
        
        for item in self.batch_list:
            tv.insert('', tk.END, values=(item['unique_id'], item['model'], item['price']))
            
        def remove_sel():
            sel = tv.selection()
            if not sel: return
            for s in sel:
                vals = tv.item(s)['values']
                uid = str(vals[0])
                # Remove from batch_list
                self.batch_list = [x for x in self.batch_list if str(x['unique_id']) != uid]
                tv.delete(s)
            self._refresh_batch_list()

        ttk.Button(top, text="Remove Selected", command=remove_sel).pack(pady=5)
        
        def confirm():
            status = self.var_status.get()
            buyer = self.ent_buyer.get().strip()
            contact = self.ent_contact.get().strip()
            
            if status == "OUT" and not buyer:
                messagebox.showwarning("Error", "Buyer Name Required")
                return
                
            updates = {"status": status}
            if status == "OUT":
                updates['buyer'] = buyer
                updates['buyer_contact'] = contact
                
            # Process
            count = 0
            for item in self.batch_list:
                if self.app.inventory.update_item_data(item['unique_id'], updates):
                    count += 1
            
            # --- Auto Invoice for Batch ---
            if status == "OUT" and self.var_auto_inv.get():
                try:
                    self._generate_silent_invoice(self.batch_list, buyer, self.ent_inv_date.get(), self.var_tax_inc.get())
                    messagebox.showinfo("Done", f"Updated {count} items & Generated Invoice.")
                except Exception as e:
                    messagebox.showinfo("Done", f"Updated {count} items.\nWarning: Invoice failed {e}")
            else:
                messagebox.showinfo("Done", f"Updated {count} items successfully.")
                
            self.batch_list = []
            self._refresh_batch_list()
            self.ent_id.delete(0, tk.END)
            self.ent_buyer.set('')
            self.ent_contact.delete(0, tk.END)
            top.destroy()
            
        ttk.Button(top, text="CONFIRM UPDATE ALL", command=confirm, style="Accent.TButton").pack(pady=10, fill=tk.X, padx=20)

    def _confirm_update(self, event=None):
        if self.current_item is None:
            messagebox.showwarning("Wait", "Please scan/find an item first.")
            return
            
        status = self.var_status.get()
        uid = self.current_item['unique_id']
        
        updates = {"status": status}
        if status == "OUT":
            buyer = self.ent_buyer.get().strip()
            if not buyer:
                messagebox.showwarning("Required", "Please enter Buyer Name")
                self.ent_buyer.focus_set()
                return
            updates['buyer'] = buyer
            updates['buyer_contact'] = self.ent_contact.get().strip()
            
        # Update
        success = self.app.inventory.update_item_data(uid, updates)
        
        if success:
            # Log & History
            self._log(f"Updated ID {uid} -> {status}")
            self.history.append({"id": uid, "prev_status": self.current_item['status']})
            
            # --- Auto Invoice Single ---
            if status == "OUT" and self.var_auto_inv.get():
                self._generate_silent_invoice([self.current_item], updates.get('buyer'), self.ent_inv_date.get(), self.var_tax_inc.get())
                messagebox.showinfo("Success", f"Item marked as {status}\nInvoice Generated.")
            else:
                messagebox.showinfo("Success", f"Item marked as {status}")
            
            # Reset UI
            self.ent_id.delete(0, tk.END)
            self.lbl_details.config(text="Ready to scan next...", fg="gray")
            self.ent_buyer.set('') # Clear combo
            self.ent_contact.delete(0, tk.END)
            self.current_item = None
            self.ent_id.focus_set()
        else:
            messagebox.showerror("Error", "Update failed.")
            self._log(f"FAILED update for {uid}")

    def _undo(self):
        if not self.history: 
            messagebox.showinfo("Undo", "Nothing to undo.")
            return
            
        last = self.history.pop()
        iid = last['id']
        prev = last['prev_status']
        
        if self.app.inventory.update_item_status(iid, prev, write_to_excel=True):
            self._log(f"UNDO: Reverted {iid} -> {prev}")
            messagebox.showinfo("Undo", f"Reverted ID {iid} to {prev}")
        else:
            messagebox.showerror("Undo Error", f"Failed to revert {iid}")

    def _generate_silent_invoice(self, items, buyer_name, date_str, is_inclusive):
        # Convert items to cart format
        cart = []
        for item in items:
            cart.append({
                'unique_id': item['unique_id'],
                'model': item['model'],
                'price': float(item.get('price', 0)),
                'imei': item.get('imei', '')
            })
            
        buyer = {
            "name": buyer_name,
            "contact": "",
            "date": date_str,
            "is_interstate": False,
            "is_tax_inclusive": is_inclusive
        }
        
        ts = int(datetime.datetime.now().timestamp())
        safe_name = "".join([c for c in buyer_name if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = f"{safe_name}_{ts}.pdf"
        save_path = self.app.app_config.get_invoices_dir() / filename
        inv_num = f"INV-{ts}"
        
        success, verify_hash, pdf_total = self.app.billing.generate_invoice(cart, buyer, inv_num, str(save_path))
        
        if success:
            # Save Registry
            try:
                import json
                from pathlib import Path
                reg_path = Path.home() / "Documents" / "4BrosManager" / "config" / "invoice_registry.json"
                registry = {}
                if reg_path.exists():
                    with open(reg_path, 'r') as f: registry = json.load(f)
                    
                registry[verify_hash] = {
                    "inv_no": inv_num,
                    "date": date_str,
                    "amount": f"{pdf_total:.2f}",
                    "buyer": buyer_name
                }
                with open(reg_path, 'w') as f: json.dump(registry, f, indent=4)
            except: pass

# --- Edit Data Screen ---
class EditDataScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.current_id = None
        self.entry_widgets = [] # Ordered list for navigation
        self.skip_vars = {}
        self.vars = {}
        self._init_ui()

    def _init_ui(self):
        ttk.Label(self, text="High-Speed Edit", font=('Segoe UI', 16, 'bold'), bootstyle="primary").pack(pady=10)
        
        # Search Bar
        frame_search = ttk.Frame(self, padding=10)
        frame_search.pack(fill=tk.X, padx=20)
        
        ttk.Label(frame_search, text="Search By:").pack(side=tk.LEFT, padx=(0,5))
        self.var_mode = tk.StringVar(value="ID")
        self.combo_mode = ttk.Combobox(frame_search, textvariable=self.var_mode, values=["ID", "IMEI", "Model"], state="readonly", width=8)
        self.combo_mode.pack(side=tk.LEFT, padx=5)
        
        self.ent_search = ttk.Entry(frame_search, width=30)
        self.ent_search.pack(side=tk.LEFT, padx=5)
        self.ent_search.bind('<Return>', self._lookup)
        
        ttk.Button(frame_search, text="Load", command=self._lookup, bootstyle="outline-primary").pack(side=tk.LEFT, padx=5)

        # Form Container
        self.form_frame = ttk.Frame(self, padding=20)
        self.form_frame.pack(fill=tk.BOTH, expand=True)

        # Fields Config
        self.fields = [
            # Label, Key, Width
            ('Model Name', 'model', 50),
            ('IMEI No', 'imei', 30),
            ('Price (Orig)', 'price_original', 15),
            ('Color', 'color', 20),
            ('Grade', 'grade', 10),
            ('Condition', 'condition', 30),
            ('Other / Notes', 'notes', 50)
        ]
        
        self._build_form()
        
        # Save Button Area
        btn_frame = ttk.Frame(self, padding=20)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.btn_save = ttk.Button(btn_frame, text="Save Changes [Enter]", command=self._save, bootstyle="success", width=20)
        self.btn_save.pack(side=tk.RIGHT)

    def _build_form(self):
        from core.data_registry import DataRegistry
        colors = DataRegistry().get_colors()

        for idx, (lbl, key, w) in enumerate(self.fields):
            # 1. Label
            ttk.Label(self.form_frame, text=lbl, width=15, font=('Segoe UI', 10)).grid(row=idx, column=0, sticky=tk.W, pady=5)
            
            # 2. Input Widget
            var = tk.StringVar()
            self.vars[key] = var
            
            if key == 'color':
                ent = ttk.Combobox(self.form_frame, textvariable=var, values=colors, width=w)
            elif key in ['grade', 'condition']:
                 # Suggestions
                 vals = DataRegistry().get_grades() if key == 'grade' else ['New', 'Refurb', 'Used', 'Damaged']
                 ent = ttk.Combobox(self.form_frame, textvariable=var, values=vals, width=w)
            else:
                ent = ttk.Entry(self.form_frame, textvariable=var, width=w)
            
            ent.grid(row=idx, column=1, sticky=tk.W, padx=10, pady=5)
            self.entry_widgets.append(ent)
            
            # 3. Skip Checkbox
            skip_var = tk.BooleanVar(value=False)
            self.skip_vars[key] = skip_var
            
            # Checkbox calls _toggle_skip on change
            cb = ttk.Checkbutton(self.form_frame, text="Skip", variable=skip_var, bootstyle="round-toggle", command=lambda k=key, e=ent, v=skip_var: self._toggle_skip(k, e, v))
            cb.grid(row=idx, column=2, padx=10)
            
            # Bind Enter Key Navigation
            # We use a closure to capture the current index
            ent.bind('<Return>', lambda e, i=idx: self._on_enter(i))

    def _toggle_skip(self, key, widget, var):
        if var.get():
            widget.configure(state='disabled')
        else:
            # For Combobox, 'normal' means editable, 'readonly' means select-only.
            # We want to allow typing? Assuming yes for productivity.
            widget.configure(state='normal')

    def _on_enter(self, current_index):
        # Find next ENABLED widget
        next_idx = current_index + 1
        found = False
        
        while next_idx < len(self.entry_widgets):
            # Check if skipped
            key = self.fields[next_idx][1]
            if not self.skip_vars[key].get():
                # Found enabled widget
                target = self.entry_widgets[next_idx]
                target.focus_set()
                # Select all text if Entry
                try: target.select_range(0, tk.END) 
                except: pass
                found = True
                break
            next_idx += 1
            
        if not found:
            # If no more fields, focus Save button or Submit
            self.btn_save.focus_set()
            self.btn_save.invoke()

    def _load_item_dict(self, data):
        self.current_id = str(data.get('unique_id', ''))
        for lbl, key, w in self.fields:
            val = data.get(key, '')
            self.vars[key].set(str(val))
            
        # Focus first enabled field
        self.after(100, lambda: self._on_enter(-1))

    def _save(self):
        if not self.current_id: return
        
        # Collect data
        updates = {k: v.get() for k, v in self.vars.items()}
        
        # Validate Price
        try:
            updates['price_original'] = float(updates['price_original'])
        except:
            pass # Allow empty or invalid for now, or handle stricter
            
        # Update Inventory
        success = self.app.inventory.update_item_data(self.current_id, updates)
        
        if success:
            # Optional: Show Toast
            from ttkbootstrap.toast import ToastNotification
            ToastNotification(title="Updated", message=f"Item {self.current_id} saved.", bootstyle="success", duration=2000).show_toast()
            
            # Clear / Focus Search for next item
            self.ent_search.delete(0, tk.END)
            self.ent_search.focus_set()
            self.current_id = None
            # Clear vars?
            for v in self.vars.values(): v.set('')
        else:
            messagebox.showerror("Error", "Failed to update item.")

    def _lookup(self, event=None):
        q = self.ent_search.get().strip()
        if not q: return
        
        mode = self.var_mode.get()
        df = self.app.inventory.get_inventory()
        match = pd.DataFrame()
        
        if mode == "ID":
            match = df[df['unique_id'].astype(str) == q]
        elif mode == "IMEI":
            match = df[df['imei'].astype(str).str.contains(q, na=False)]
        elif mode == "Model":
            match = df[df['model'].astype(str).str.contains(q, case=False, na=False)]
            
        if not match.empty:
            match = match.drop_duplicates(subset=['unique_id'])
            
        if match.empty:
            messagebox.showwarning("Error", f"No item found for {mode}: {q}")
            return
            
        if len(match) == 1:
            self._load_item_dict(match.iloc[0].to_dict())
        else:
            items = match.to_dict('records')
            ItemSelectionDialog(self.winfo_toplevel(), items, self._load_item_dict)

# --- Help / User Guide Screen ---
class HelpScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self._init_ui()

    def _init_ui(self):
        ttk.Label(self, text="User Guide & Help", font=('Segoe UI', 16, 'bold')).pack(pady=10)
        
        # Notebook for sections
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)
        
        # 1. Getting Started
        f_start = ttk.Frame(nb)
        nb.add(f_start, text="Getting Started")
        self._add_scroll_text(f_start, self._get_start_text())
        
        # 2. Features & How-To
        f_feat = ttk.Frame(nb)
        nb.add(f_feat, text="Features Guide")
        self._add_scroll_text(f_feat, self._get_feature_text())
        
        # 3. FAQ
        f_faq = ttk.Frame(nb)
        nb.add(f_faq, text="FAQ")
        self._add_scroll_text(f_faq, self._get_faq_text())

    def _add_scroll_text(self, parent, content):
        txt = tk.Text(parent, font=('Segoe UI', 10), wrap=tk.WORD, padx=10, pady=10)
        scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(fill=tk.BOTH, expand=True)
        
        txt.insert(tk.END, content)
        txt.configure(state='disabled')

    def _get_start_text(self):
        return """WELCOME TO 4BROS MOBILE MANAGER

Step 1: Add Your Inventory
--------------------------
1. Go to "Manage" -> "Manage Files".
2. Click "+ Add Excel File".
3. Select your stock Excel file (.xlsx) or CSV.
4. Map your columns! The app needs to know which column is IMEI, Model, Price, etc.
   - If you don't have a column, select "(Ignore)".
   - You can set a default Supplier for the whole file.

Step 2: Check Your Dashboard
----------------------------
- Go to "Inventory" to see all your items combined.
- The app automatically assigns a 'Unique ID' to every phone. Use this ID for fast scanning!

Step 3: Printing Labels
-----------------------
- In "Inventory", check the boxes [x] next to items.
- Click "Print Checked".
- Select "Batch Mode" if you have a ZPL Thermal Printer for best results (2-up labels).

Step 4: Selling
---------------
- Go to "Quick Status".
- Scan the Unique ID (or search by IMEI).
- Select "SOLD".
- Enter Buyer Name (select from list or type new).
- Click Confirm. The app updates your Excel file automatically!
"""

    def _get_feature_text(self):
        return """KEY FEATURES GUIDE

1. BATCH SCANNING (New!)
------------------------
- In "Quick Status", check "BATCH MODE".
- Scan multiple phones one after another.
- They are added to a waiting list.
- When done, click "FINISH & REVIEW".
- You can review the list, verify prices, and update them all to SOLD in one click.

2. BUYER & DATA MANAGEMENT
--------------------------
- Go to "Manage" -> "Manage Data".
- Pre-load your Frequent Buyers list to save typing time.
- Manage standard Colors for consistent data entry.

3. INVOICING / BILLING
----------------------
- Go to "Billing".
- Scan IDs to add to cart.
- Enter Customer Details.
- Click "Generate Invoice" to get a professional PDF receipt with GST breakdowns.

4. ANALYTICS
------------
- See your total stock value, potential profit, and sales performance.
- Export detailed PDF reports for your records.

5. SAFETY & BACKUPS
-------------------
- The app creates a backup (.bak) of your Excel file before every write.
- If Excel is open, the app will warn you instead of crashing.
- Data like 'Sold' status is saved internally too, so you never lose track even if you replace the Excel file.
"""

    def _get_faq_text(self):
        return """FREQUENTLY ASKED QUESTIONS

Q: My Excel file isn't updating!
A: Ensure the file is NOT open in Microsoft Excel. The app cannot write if the file is locked by another program. Close Excel and try again.

Q: I see "Conflict Detected" warning.
A: This means the same IMEI was found in two different files or rows. The app asks you to merge them. Usually, you should check your source files for duplicates.

Q: How do I change the Store Name on labels?
A: Go to "Manage" -> "Settings". You can change Store Name, Label Size, and GST % there.

Q: Can I use this without Excel?
A: You need at least one Excel/CSV file to load inventory. You can create a simple dummy file with headers (Model, IMEI, Price) to start.

Q: Where is my data saved?
A: All config and history is saved in your 'Documents/4BrosManager' folder. Do not delete the 'config' folder there unless you want to reset everything.
"""

