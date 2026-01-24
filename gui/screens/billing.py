import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
import os
import sys
from pathlib import Path

from ..base import BaseScreen, AutocompleteEntry
from ..dialogs import PrinterSelectionDialog, ItemSelectionDialog

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
        self.ent_scan = AutocompleteEntry(scan_frame, font=('Segoe UI', 14))
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
        # LOAD MODELS for Autocomplete
        self.ent_scan.set_completion_list(self._get_all_models())

    def focus_primary(self):
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
        
        # --- NEW: Smart ID Lookup (Handles Merged Items) ---
        if mode == "ID":
            # Direct lookup with redirection
            item, redirect = self.app.inventory.get_item_by_id(q)
            if item:
                if redirect:
                    messagebox.showinfo("Merged Item", f"ID {redirect} was merged into {item['unique_id']}.\nUsing {item['unique_id']} ({item['model']}).")
                
                # Check Sold Status
                if str(item.get('status', '')).upper() == 'OUT':
                    self._handle_sold_item(item)
                    return
                    
                self.add_items([item])
                self.ent_scan.delete(0, tk.END)
                return
            else:
                # Not found (even after check)
                messagebox.showwarning("Not Found", f"No item found for ID: {q}")
                self.ent_scan.select_range(0, tk.END)
                return

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

    def focus_primary(self):
        self.ent_filter_buyer.focus_set()

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
