import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import datetime
import ttkbootstrap as tb

from ..base import BaseScreen, AutocompleteEntry

class SearchScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self._init_ui()

    def _init_ui(self):
        self.add_header("Search & History", help_section="Core Features")
        
        self.paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.left_pane = ttk.Frame(self.paned)
        self.paned.add(self.left_pane, minsize=300, width=350)
        
        f_search = ttk.LabelFrame(self.left_pane, text="Find Item", padding=10)
        f_search.pack(fill=tk.X, pady=5, padx=5)
        
        self.var_search_type = tk.StringVar(value="ID")
        f_radios = ttk.Frame(f_search)
        f_radios.pack(fill=tk.X)
        ttk.Radiobutton(f_radios, text="Unique ID", variable=self.var_search_type, value="ID").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(f_radios, text="Model/IMEI", variable=self.var_search_type, value="MODEL").pack(side=tk.LEFT, padx=5)
        
        self.ent_search = AutocompleteEntry(f_search, font=('Segoe UI', 12))
        self.ent_search.pack(fill=tk.X, pady=5)
        self.ent_search.bind('<Return>', lambda e: self._do_lookup())
        ttk.Button(f_search, text="SEARCH", command=self._do_lookup).pack(fill=tk.X, pady=5)
        
        self.list_results = tk.Listbox(self.left_pane, font=('Segoe UI', 10))
        self.list_results.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.list_results.bind('<Button-3>', self._show_context_menu)
        self.list_results.bind('<<ListboxSelect>>', self._on_result_select)

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Mark as SOLD", command=self._ctx_mark_sold)
        self.context_menu.add_command(label="Add to Invoice", command=self._ctx_add_to_invoice)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Print Label", command=self._ctx_print)
        self.context_menu.add_command(label="Edit Details", command=self._ctx_edit)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy IMEI", command=self._ctx_copy_imei)
        
        self.right_pane = ttk.Frame(self.paned)
        self.paned.add(self.right_pane, minsize=400)
        
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
        
        self.nb_details = ttk.Notebook(self.right_pane)
        self.nb_details.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tab_info = ttk.Frame(self.nb_details)
        self.nb_details.add(self.tab_info, text="Details & Specs")
        
        self.txt_info = tk.Text(self.tab_info, font=('Consolas', 11), state='disabled', padx=10, pady=10, bg="#f9f9f9")
        self.txt_info.pack(fill=tk.BOTH, expand=True)
        
        self.tab_history = ttk.Frame(self.nb_details)
        self.nb_details.add(self.tab_history, text="History & Logs")
        
        self.txt_timeline = tk.Text(self.tab_history, font=('Segoe UI', 11), state='disabled', padx=20, pady=20, bg="#ffffff", relief=tk.FLAT)
        scroll_hist = ttk.Scrollbar(self.tab_history, orient=tk.VERTICAL, command=self.txt_timeline.yview)
        self.txt_timeline.configure(yscrollcommand=scroll_hist.set)
        
        scroll_hist.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_timeline.pack(fill=tk.BOTH, expand=True)
        
        self.txt_timeline.tag_configure("center", justify='center')
        self.txt_timeline.tag_configure("status", font=('Segoe UI', 12, 'bold'), foreground="#007acc")
        self.txt_timeline.tag_configure("date", font=('Segoe UI', 9), foreground="#666")
        self.txt_timeline.tag_configure("line", font=('Consolas', 14), foreground="#ccc")

    def _show_context_menu(self, event):
        try:
            index = self.list_results.nearest(event.y)
            self.list_results.selection_clear(0, tk.END)
            self.list_results.selection_set(index)
            self.list_results.activate(index)
            self._on_result_select(None)
            self.context_menu.post(event.x_root, event.y_root)
        except: pass

    def _get_current_match(self):
        sel = self.list_results.curselection()
        if not sel: return None
        return self.matches[sel[0]]

    def _ctx_mark_sold(self):
        row = self._get_current_match()
        if row is None: return
        
        if messagebox.askyesno("Confirm", f"Mark {row['model']} as SOLD?"):
            if self.app.inventory.update_item_status(row['unique_id'], "OUT", write_to_excel=True):
                 messagebox.showinfo("Success", "Item Marked SOLD")
                 self._do_lookup()

    def _ctx_add_to_invoice(self):
        row = self._get_current_match()
        if row is not None:
            self.app.switch_to_billing([row.to_dict()])

    def _ctx_print(self):
        row = self._get_current_match()
        if row is not None:
            self.app.printer.print_label_windows(row.to_dict())

    def _ctx_edit(self):
        row = self._get_current_match()
        if row is not None:
             self.app.show_screen('edit')
             self.app.screens['edit'].ent_search.delete(0, tk.END)
             self.app.screens['edit'].ent_search.insert(0, str(row['unique_id']))
             self.app.screens['edit']._lookup()

    def _ctx_copy_imei(self):
        row = self._get_current_match()
        if row is not None:
            self.clipboard_clear()
            self.clipboard_append(str(row.get('imei', '')))


    def focus_primary(self):
        self.ent_search.focus_set()

    def on_show(self):
        self.ent_search.focus_set()
        self.ent_search.set_completion_list(self._get_all_models())

    def _do_lookup(self):
        query = self.ent_search.get().strip()
        if not query: return
        
        df = self.app.inventory.get_inventory()
        self.list_results.delete(0, tk.END)
        self.matches = []
        
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
            
        for _, row in match_df.iterrows():
            self.matches.append(row)
            self.list_results.insert(tk.END, f"{row['model']} | ID: {row['unique_id']}")
            
        self.list_results.selection_set(0)
        self._on_result_select(None)

    def _on_result_select(self, event):
        sel = self.list_results.curselection()
        if not sel: return
        
        idx = sel[0]
        row = self.matches[idx]
        self._show_details(row)

    def _get_display_date(self, row):
        if row.get('date_added'):
            return str(row.get('date_added'))
            
        reg_meta = self.app.inventory.id_registry.get_metadata(row['unique_id'])
        history = reg_meta.get('history', [])
        if history:
            sorted_h = sorted(history, key=lambda x: x.get('ts', ''))
            return sorted_h[0].get('ts')
            
        return str(row.get('last_updated', 'Unknown'))

    def _show_details(self, row):
        self.lbl_model.config(text=row.get('model', 'Unknown'))
        price = row.get('price', 0)
        self.lbl_price.config(text=f"₹{price:,.2f}")
        
        status = str(row.get('status', 'IN')).upper()
        bg_col = "#d4edda" if status == 'IN' else "#f8d7da"
        fg_col = "#155724" if status == 'IN' else "#721c24"
        self.lbl_status.config(text=status, bg=bg_col, fg=fg_col)
        
        raw_source = str(row.get('source_file', ''))
        import os
        if '::' in raw_source:
            parts = raw_source.split('::')
            fname = os.path.basename(parts[0])
            display_source = f"{fname} (Sheet: {parts[1]})"
        else:
            display_source = os.path.basename(raw_source)

        date_out = "-"
        if str(row.get('status')).upper() in ['OUT', 'SOLD']:
            sold_val = row.get('date_sold')
            if sold_val:
                date_out = str(sold_val)
            else:
                date_out = "Unknown"
            
        date_in = self._get_display_date(row)

        buyer_str = f"{row.get('buyer', '-')} {row.get('buyer_contact', '')}".strip() or "-"

        info = f"""
UNIQUE ID   : {row.get('unique_id')}
IMEI        : {row.get('imei')}
MODEL       : {row.get('model')}
RAM/ROM     : {row.get('ram_rom')}
COLOR       : {row.get('color')}
GRADE       : {row.get('grade', '-')}
CONDITION   : {row.get('condition', '-')}
SUPPLIER    : {row.get('supplier')}

HISTORY LOG
-----------
DATE IN     : {date_in}
DATE OUT    : {date_out}
SOLD TO     : {buyer_str}

FINANCIALS
----------
BUY PRICE   : ₹{row.get('price_original', 0):,.2f}
SELL PRICE  : ₹{row.get('price', 0):,.2f}
PROFIT      : ₹{(row.get('price', 0) - row.get('price_original', 0)):,.2f}

METADATA
--------
Source File : {display_source}
Notes       : {row.get('notes', '')}
"""
        self.txt_info.configure(state='normal')
        self.txt_info.delete(1.0, tk.END)
        self.txt_info.insert(tk.END, info)
        self.txt_info.configure(state='disabled')
        
        self.txt_timeline.configure(state='normal')
        self.txt_timeline.delete(1.0, tk.END)
            
        reg_meta = self.app.inventory.id_registry.get_metadata(row['unique_id'])
        history = reg_meta.get('history', [])
        
        if not history:
            self.txt_timeline.insert(tk.END, "INITIAL ENTRY\n", ("status", "center"))
            self.txt_timeline.insert(tk.END, f"Recorded on {row.get('last_updated')}\n", ("date", "center"))
        else:
            history = sorted(history, key=lambda x: x.get('ts', ''))
            
            for i, h in enumerate(history):
                disp_action = h.get('action')
                details = h.get('details', '')
                
                status_text = disp_action
                
                if "Moved from" in details:
                    parts = details.split(" to ")
                    status_text = parts[1] if len(parts) > 1 else details
                elif disp_action == "DATA_UPDATE":
                    if "buyer=" in details or "buyer_contact=" in details:
                        status_text = "BUYER INFO UPDATE"
                    elif "notes=" in details:
                        status_text = "NOTES ADDED"
                    elif "price=" in details:
                        status_text = "PRICE CHANGE"
                    elif "status=" in details:
                        import re
                        m = re.search(r"status=(\w+)", details)
                        if m: status_text = m.group(1).upper()
                
                self.txt_timeline.insert(tk.END, f"{status_text}\n", ("status", "center"))
                self.txt_timeline.insert(tk.END, f"on {h.get('ts')}\n", ("date", "center"))
                
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

class StatusScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        from core.data_registry import DataRegistry
        self.registry = DataRegistry()
        self.history = []
        self.current_item = None
        self.batch_list = []
        self._init_ui()

    def _init_ui(self):
        self.add_header("Quick Status Update", help_section="Core Features")
        
        self.var_batch_mode = tk.BooleanVar(value=False)
        f_top = ttk.Frame(self)
        f_top.pack(fill=tk.X, padx=20)
        ttk.Checkbutton(f_top, text="BATCH MODE (Scan multiple, update at end)", variable=self.var_batch_mode, command=self._toggle_batch_ui).pack(side=tk.RIGHT)
        
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        left_pane = ttk.LabelFrame(main_frame, text="1. Scan Item", padding=15)
        left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.var_search_type = tk.StringVar(value="ID")
        f_type = ttk.Frame(left_pane)
        f_type.pack(fill=tk.X, pady=5)
        ttk.Label(f_type, text="Scan Mode:").pack(side=tk.LEFT)
        ttk.Radiobutton(f_type, text="Unique ID", variable=self.var_search_type, value="ID").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(f_type, text="Model/IMEI", variable=self.var_search_type, value="MODEL").pack(side=tk.LEFT, padx=10)
        
        f_input = ttk.Frame(left_pane)
        f_input.pack(fill=tk.X, pady=10)
        self.ent_id = ttk.Entry(f_input, font=('Segoe UI', 14))
        self.ent_id.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.ent_id.bind('<Return>', self._lookup_item)
        ttk.Button(f_input, text="FIND", command=self._lookup_item, width=8).pack(side=tk.LEFT, padx=5)
        
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
        
        self.lbl_details = tk.Label(left_pane, text="Ready to scan...", font=('Consolas', 11), bg="#e8e8e8", relief=tk.SUNKEN, height=6, justify=tk.LEFT, anchor="nw", padx=10, pady=10)
        self.lbl_details.pack(fill=tk.BOTH, expand=True, pady=10)

        right_pane = ttk.LabelFrame(main_frame, text="2. Update Status", padding=15)
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.var_status = tk.StringVar(value="OUT")
        
        btn_frame = ttk.Frame(right_pane)
        btn_frame.pack(fill=tk.X, pady=10)
        
        r_out = ttk.Radiobutton(btn_frame, text="SOLD (OUT)", variable=self.var_status, value="OUT", command=self._toggle_buyer_fields)
        r_rtn = ttk.Radiobutton(btn_frame, text="RETURN (RTN)", variable=self.var_status, value="RTN", command=self._toggle_buyer_fields)
        r_in  = ttk.Radiobutton(btn_frame, text="STOCK IN (IN)", variable=self.var_status, value="IN", command=self._toggle_buyer_fields)
        
        r_out.pack(fill=tk.X, pady=5)
        r_rtn.pack(fill=tk.X, pady=5)
        r_in.pack(fill=tk.X, pady=5)

        self.frame_buyer = ttk.Frame(right_pane, padding=10, relief=tk.RIDGE, borderwidth=1)
        self.frame_buyer.pack(fill=tk.X, pady=10)
        
        ttk.Label(self.frame_buyer, text="Buyer Name:").pack(anchor=tk.W)
        
        self.ent_buyer = AutocompleteEntry(self.frame_buyer, width=30)
        self.ent_buyer.pack(fill=tk.X, pady=(0,5))
        self.ent_buyer.bind('<Return>', self._check_buyer_contact)
        self.ent_buyer.bind('<FocusOut>', self._check_buyer_contact)
        
        ttk.Label(self.frame_buyer, text="Contact No:").pack(anchor=tk.W)
        self.ent_contact = ttk.Entry(self.frame_buyer)
        self.ent_contact.pack(fill=tk.X, pady=(0,5))
        self.ent_contact.bind('<Return>', self._confirm_update)
        
        self.buyer_cache = {} 

        self.btn_update = ttk.Button(right_pane, text="CONFIRM UPDATE", command=self._confirm_update, style="Accent.TButton")
        self.btn_update.pack(fill=tk.X, pady=(20, 10))
        
        ttk.Button(right_pane, text="UNDO LAST ACTION", command=self._undo).pack(fill=tk.X, pady=5)
        
        self.batch_frame = ttk.Frame(self)
        self.batch_tree = ttk.Treeview(self.batch_frame, columns=('id', 'model'), show='headings', height=6)
        self.batch_tree.heading('id', text='ID')
        self.batch_tree.heading('model', text='Model')
        self.batch_tree.column('id', width=60)
        self.batch_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        btn_batch_commit = ttk.Button(self.batch_frame, text="FINISH & REVIEW BATCH", command=self._finish_batch, style="Accent.TButton")
        btn_batch_commit.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        self.log_frame = ttk.LabelFrame(self, text="Recent Activity", padding=10)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.txt_log = tk.Text(self.log_frame, font=('Consolas', 9), state='disabled', height=5, bg="#f9f9f9")
        self.txt_log.pack(fill=tk.BOTH, expand=True)

    def on_show(self):
        self.ent_id.focus_set()
        self._refresh_buyers()
        self._toggle_buyer_fields()

    def _refresh_buyers(self):
        predefined = self.registry.get_buyers()
        history_buyers = self.app.inventory.id_registry.get_all_buyers()
        self.buyer_cache = history_buyers
        all_buyers = sorted(list(set(predefined + list(history_buyers.keys()))))
        self.ent_buyer.set_completion_list(all_buyers)

    def _check_buyer_contact(self, event=None):
        name = self.ent_buyer.get().strip()
        if not name: return
        
        if name in self.buyer_cache:
            contact = self.buyer_cache[name]
            if contact:
                current = self.ent_contact.get().strip()
                if not current:
                    self.ent_contact.delete(0, tk.END)
                    self.ent_contact.insert(0, contact)
        
        if event and event.keysym == 'Return':
            self.ent_contact.focus_set()


    def _toggle_batch_ui(self):
        if self.var_batch_mode.get():
            self.log_frame.pack_forget()
            self.batch_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            self.btn_update.config(state='disabled')
            self._refresh_batch_list()
        else:
            self.batch_frame.pack_forget()
            self.log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            self.btn_update.config(state='normal')
            
            if self.batch_list:
                if messagebox.askyesno("Clear Batch", "Batch mode disabled. Clear current batch list?"):
                    self.batch_list = []
                else:
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
                txt = lb.get(sel[0])
                uid = txt.split('|')[0].replace('ID:', '').strip()
                selected_id[0] = uid
                top.destroy()
                
        ttk.Button(top, text="Select", command=on_select).pack(pady=5)
        
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
        
        if self.var_batch_mode.get():
            if any(str(x['unique_id']) == str(self.current_item['unique_id']) for x in self.batch_list):
                self._log(f"Already in batch: {val}")
            else:
                self.batch_list.append(self.current_item)
                self._refresh_batch_list()
                self.lbl_details.config(text=f"Added to batch: {self.current_item['model']}", fg="blue")
            
            self.ent_id.delete(0, tk.END)
            self.ent_id.focus_set()
            return

        d = self.current_item
        status_color = "green" if d['status'] == 'IN' else "red"
        
        txt = f"MODEL : {d['model']}\nIMEI  : {d['imei']}\nCOLOR : {d['color']}\nPRICE : ₹{d['price']:,.0f}\nSTATUS: {d['status']}"
        self.lbl_details.config(text=txt, fg="black")
        
        if self.var_status.get() == "OUT":
            self.ent_buyer.focus_set()

    def _finish_batch(self):
        if not self.batch_list:
            messagebox.showinfo("Empty", "Batch is empty")
            return
            
        top = tk.Toplevel(self)
        top.title(f"Review Batch ({len(self.batch_list)} Items)")
        top.geometry("600x500")
        
        lbl = ttk.Label(top, text=f"Update all to: {self.var_status.get()}?", font=('bold'))
        lbl.pack(pady=10)
        
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
                
            count = 0
            for item in self.batch_list:
                if self.app.inventory.update_item_data(item['unique_id'], updates):
                    count += 1
            
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
            self.ent_buyer.delete(0, tk.END)
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
            
        success = self.app.inventory.update_item_data(uid, updates)
        
        if success:
            self._log(f"Updated ID {uid} -> {status}")
            self.history.append({"id": uid, "prev_status": self.current_item['status']})
            
            if status == "OUT" and self.var_auto_inv.get():
                self._generate_silent_invoice([self.current_item], updates.get('buyer'), self.ent_inv_date.get(), self.var_tax_inc.get())
                messagebox.showinfo("Success", f"Item marked as {status}\nInvoice Generated.")
            else:
                messagebox.showinfo("Success", f"Item marked as {status}")
            
            self.ent_id.delete(0, tk.END)
            self.lbl_details.config(text="Ready to scan next...", fg="gray")
            self.ent_buyer.delete(0, tk.END)
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
            except:
                pass

class EditDataScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.current_id = None
        self.entry_widgets = []
        self.skip_vars = {}
        self.vars = {}
        self._init_ui()

    def _init_ui(self):
        self.add_header("High-Speed Edit", help_section="Data Management")
        
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

        self.form_frame = ttk.Frame(self, padding=20)
        self.form_frame.pack(fill=tk.BOTH, expand=True)

        self.fields = [
            ('Model Name', 'model', 50),
            ('IMEI No', 'imei', 30),
            ('Supplier', 'supplier', 30),
            ('Price (Orig)', 'price_original', 15),
            ('Color', 'color', 20),
            ('Grade', 'grade', 10),
            ('Condition', 'condition', 30),
            ('Other / Notes', 'notes', 50)
        ]
        
        self._build_form()
        
        btn_frame = ttk.Frame(self, padding=20)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.btn_save = ttk.Button(btn_frame, text="Save Changes [Enter]", command=self._save, bootstyle="success", width=20)
        self.btn_save.pack(side=tk.RIGHT)

    def _build_form(self):
        from core.data_registry import DataRegistry
        colors = DataRegistry().get_colors()

        for idx, (lbl, key, w) in enumerate(self.fields):
            ttk.Label(self.form_frame, text=lbl, width=15, font=('Segoe UI', 10)).grid(row=idx, column=0, sticky=tk.W, pady=5)
            
            var = tk.StringVar()
            self.vars[key] = var
            
            if key == 'color':
                ent = ttk.Combobox(self.form_frame, textvariable=var, values=colors, width=w)
            elif key in ['grade', 'condition']:
                 vals = DataRegistry().get_grades() if key == 'grade' else ['New', 'Refurb', 'Used', 'Damaged']
                 ent = ttk.Combobox(self.form_frame, textvariable=var, values=vals, width=w)
            else:
                ent = ttk.Entry(self.form_frame, textvariable=var, width=w)
            
            ent.grid(row=idx, column=1, sticky=tk.W, padx=10, pady=5)
            self.entry_widgets.append(ent)
            
            skip_var = tk.BooleanVar(value=False)
            self.skip_vars[key] = skip_var
            
            cb = ttk.Checkbutton(self.form_frame, text="Skip", variable=skip_var, bootstyle="round-toggle", command=lambda k=key, e=ent, v=skip_var: self._toggle_skip(k, e, v))
            cb.grid(row=idx, column=2, padx=10)
            
            ent.bind('<Return>', lambda e, i=idx: self._on_enter(i))

    def _toggle_skip(self, key, widget, var):
        if var.get():
            widget.configure(state='disabled')
        else:
            widget.configure(state='normal')

    def _on_enter(self, current_index):
        next_idx = current_index + 1
        found = False
        
        while next_idx < len(self.entry_widgets):
            key = self.fields[next_idx][1]
            if not self.skip_vars[key].get():
                target = self.entry_widgets[next_idx]
                target.focus_set()
                try: target.select_range(0, tk.END) 
                except: pass
                found = True
                break
            next_idx += 1
            
        if not found:
            self.btn_save.focus_set()
            self.btn_save.invoke()

    def _load_item_dict(self, data):
        self.current_id = str(data.get('unique_id', ''))
        for lbl, key, w in self.fields:
            val = data.get(key, '')
            self.vars[key].set(str(val))
            
        self.after(100, lambda: self._on_enter(-1))

    def _lookup(self, event=None):
        q = self.ent_search.get().strip()
        if not q: return
        
        mode = self.var_mode.get()
        df = self.app.inventory.get_inventory()
        match = pd.DataFrame()
        
        if mode == 'ID':
            match = df[df['unique_id'].astype(str) == q]
        else:
            match = df[df['imei'].astype(str).str.contains(q, na=False) | df['model'].astype(str).str.contains(q, case=False, na=False)]
            
        if match.empty:
            messagebox.showwarning("Not Found", f"No item found for {q}")
            return
            
        row = match.iloc[0].to_dict()
        self._load_item_dict(row)

    def _save(self):
        if not self.current_id: return
        
        updates = {k: v.get() for k, v in self.vars.items()}
        
        try:
            updates['price_original'] = float(updates['price_original'])
        except:
            pass 
            
        success = self.app.inventory.update_item_data(self.current_id, updates)
        
        if success:
            from ttkbootstrap.toast import ToastNotification
            ToastNotification(title="Updated", message=f"Item {self.current_id} saved.", bootstyle="success", duration=2000).show_toast()
