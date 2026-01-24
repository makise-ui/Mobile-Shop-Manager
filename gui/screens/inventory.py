import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from PIL import ImageTk, Image
import pandas as pd
import datetime
import ttkbootstrap as tb

from ..base import BaseScreen, AutocompleteEntry
from ..dialogs import ZPLPreviewDialog
from ..widgets import IconButton, CollapsibleFrame
from core.filters import AdvancedFilter

class InventoryScreen(BaseScreen):
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        self.df_display = pd.DataFrame()
        self._load_icons()
        self._init_ui()

    def _load_icons(self):
        self.icons = {}
        # Map: internal_name -> filename
        icon_map = {
            "delete": "trash.png"
        }
        
        # Robust path resolution
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.abspath(".")
            
        assets_dir = os.path.join(base_dir, "assets", "icons")
        
        for name, filename in icon_map.items():
            try:
                path = os.path.join(assets_dir, filename)
                if os.path.exists(path):
                    pil_img = Image.open(path)
                    # Use original size (24x24) to avoid quality loss
                    self.icons[name] = ImageTk.PhotoImage(pil_img)
                else:
                    print(f"Warning: Icon missing at {path}")
            except Exception as e:
                print(f"Error loading icon {filename}: {e}")

    def _init_ui(self):
        # Initialize Filter Variables
        self.var_search = tk.StringVar()
        self.var_min_price = tk.StringVar()
        
        # -- Compact Toolbar --
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Left: Filter Toggle
        self.btn_filter = IconButton(toolbar, text="⚡", 
                                     command=self._toggle_filter_panel, 
                                     tooltip="Toggle Filters")
        self.btn_filter.pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Actions
        IconButton(toolbar, text="➕", 
                   command=self._send_to_billing, # Reusing 'Add Checked to Invoice' logic for now or 'Add Item'
                   tooltip="Add Checked to Invoice").pack(side=tk.LEFT, padx=2)
                   
        IconButton(toolbar, text="🖨️", 
                   command=self._print_selected, 
                   tooltip="Print Checked").pack(side=tk.LEFT, padx=2)
                   
        self.btn_select_all = IconButton(toolbar, text="☑ All", 
                   command=self._toggle_select_all, 
                   tooltip="Check/Uncheck All Visible")
        self.btn_select_all.pack(side=tk.LEFT, padx=2)
                   
        # Mark Sold/RTN
        ttk.Button(toolbar, text="Sold", command=lambda: self._bulk_update_status("OUT"), bootstyle="secondary-outline-small").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Rtn", command=lambda: self._bulk_update_status("RTN"), bootstyle="danger-outline-small").pack(side=tk.LEFT, padx=2)
        
        # Right Side
        IconButton(toolbar, text="🔄", 
                   command=self.refresh_data, 
                   tooltip="Refresh Data").pack(side=tk.RIGHT, padx=2)
                   
        # Preview Toggle
        self.var_show_preview = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text="Preview", variable=self.var_show_preview, command=self._toggle_preview, bootstyle="round-toggle").pack(side=tk.RIGHT, padx=10)

        # -- Collapsible Filter Panel --
        self.filter_panel = CollapsibleFrame(self, padding=10, bootstyle="bg")
        
        # Build Filter Form
        fp = self.filter_panel
        
        # Row 0: Search
        ttk.Label(fp, text="Search Keywords:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ent_search = AutocompleteEntry(fp, textvariable=self.var_search, width=35)
        self.ent_search.grid(row=0, column=1, columnspan=2, sticky="we", padx=5)
        ttk.Button(fp, text="🔍 Search", command=self._apply_filters, bootstyle="secondary-outline").grid(row=0, column=3, sticky="w", padx=5)
        
        # Row 1: Supplier & Status
        ttk.Label(fp, text="Supplier:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.combo_supplier = ttk.Combobox(fp, state="readonly", width=25)
        self.combo_supplier.grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(fp, text="Status:").grid(row=1, column=2, sticky="w", padx=5)
        self.combo_status = ttk.Combobox(fp, values=["All", "IN", "OUT", "RTN"], state="readonly", width=15)
        self.combo_status.set("All")
        self.combo_status.grid(row=1, column=3, sticky="w", padx=5)
        
        # Row 2: Date Range (Optional, if DateEntry fails we fallback)
        try:
            ttk.Label(fp, text="Date Added:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
            self.date_start = tb.DateEntry(fp, width=12)
            self.date_start.grid(row=2, column=1, sticky="w", padx=5)
            
            ttk.Label(fp, text="to").grid(row=2, column=2, sticky="w", padx=5)
            self.date_end = tb.DateEntry(fp, width=12)
            self.date_end.grid(row=2, column=3, sticky="w", padx=5)
        except Exception as e:
            print(f"DateEntry error: {e}")
            
        # Apply Button
        ttk.Button(fp, text="Apply Filters", command=self._apply_advanced_filters, bootstyle="primary").grid(row=3, column=3, sticky="e", pady=10)

        # -- Main Content --
        self.paned = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # 1. Treeview (List)
        cols = ('check', 'unique_id', 'imei', 'model', 'ram_rom', 'price_original', 'price', 'supplier', 'status')
        self.tree = ttk.Treeview(self.paned, columns=cols, show='headings', selectmode='extended')
        
        # -- Status Bar --
        status_bar = ttk.Frame(self)
        status_bar.pack(fill=tk.X, pady=(5, 0))
        self.lbl_counter = ttk.Label(status_bar, text="Total: 0 | Selected: 0", font=("Arial", 9, "bold"))
        self.lbl_counter.pack(side=tk.LEFT)
        
        # Shortcuts Hint
        shortcuts_text = "Tip: Ctrl+F to Search"
        ttk.Label(status_bar, text=shortcuts_text, font=("Arial", 8), foreground="gray").pack(side=tk.RIGHT, padx=10)
        
        self.lbl_info = ttk.Label(status_bar, text="")
        
        self._setup_tree_columns()
        
    def _toggle_filter_panel(self):
        self.filter_panel.toggle(fill=tk.X, pady=(0, 10))

    def _apply_advanced_filters(self):
        # Trigger filter logic
        self._apply_filters()
        
    def _setup_tree_columns(self):
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
        self.tree.bind('<Double-1>', self._on_double_click) # Double-click to Edit
        self.tree.bind('<Button-3>', self._show_context_menu) # Right-click context menu
        
        # Keyboard shortcuts for multi-select
        self.tree.bind('<Control-Shift-Down>', self._multi_select_down) # Ctrl+Shift+Down: Select down
        self.tree.bind('<Control-Shift-Up>', self._multi_select_up)     # Ctrl+Shift+Up: Select up
        self.tree.bind('<Control-Shift-Home>', self._multi_select_home) # Ctrl+Shift+Home: Select to beginning
        self.tree.bind('<Control-Shift-End>', self._multi_select_end)   # Ctrl+Shift+End: Select to end
        self.tree.bind('<Control-a>', self._select_all_keyboard)        # Ctrl+A: Select all
        self.tree.bind('<Control-Shift-a>', self._deselect_all_keyboard) # Ctrl+Shift+A: Deselect all
        
        self.paned.add(self.tree, minsize=400, width=700)

        # 2. Preview Panel (Right) - Hidden by default
        self.preview_frame = ttk.LabelFrame(self.paned, text="Label Preview", padding=10)
        
        self.lbl_preview = ttk.Label(self.preview_frame, text="Select item to preview", anchor="center")
        self.lbl_preview.pack(fill=tk.BOTH, expand=True)
        
        self.lbl_info = ttk.Label(self.preview_frame, text="")
        self.lbl_info.pack(fill=tk.X, pady=5)
        
        self.checked_ids = set() # Store unique_ids of checked items
        self.last_selected_idx = None # Track last selected for range selection

        # --- Context Menu ---
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Add to Invoice", command=self._ctx_add_to_invoice)
        self.context_menu.add_command(label="Mark as SOLD", command=self._ctx_mark_sold)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Print Label", command=self._ctx_print)
        self.context_menu.add_command(label="Edit Details", command=self._ctx_edit)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy IMEI", command=self._ctx_copy_imei)

    def _show_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            # Select the item if not already selected
            if item_id not in self.tree.selection():
                self.tree.selection_set(item_id)
            self.context_menu.post(event.x_root, event.y_root)

    def _get_selected_row_data(self):
        # Helper to get dict of currently selected single row
        sel = self.tree.selection()
        if not sel: return None
        
        # iid is unique_id (or uid_idx)
        uid = str(sel[0]).split('_')[0]
        df = self.app.inventory.get_inventory()
        match = df[df['unique_id'].astype(str) == uid]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None

    def _ctx_add_to_invoice(self):
        row = self._get_selected_row_data()
        if row:
            self.app.switch_to_billing([row])

    def _ctx_mark_sold(self):
        # Use existing logic but for specific selection
        self._bulk_update_status("OUT")

    def _ctx_print(self):
        row = self._get_selected_row_data()
        if row:
            # Print single
            self.app.printer.print_label_windows(row)
            self.checked_ids.add(self.tree.selection()[0])
            self._print_selected()

    def _ctx_edit(self):
        row = self._get_selected_row_data()
        if row:
            # Switch to Edit Screen and load
            self.app.show_screen('edit')
            self.app.screens['edit'].ent_search.delete(0, tk.END)
            self.app.screens['edit'].ent_search.insert(0, str(row['unique_id']))
            self.app.screens['edit']._lookup()

    def _ctx_copy_imei(self):
        row = self._get_selected_row_data()
        if row:
            self.clipboard_clear()
            self.clipboard_append(str(row.get('imei', '')))


    def _toggle_preview(self):
        if self.var_show_preview.get():
            self.paned.add(self.preview_frame, minsize=250)
        else:
            self.paned.remove(self.preview_frame)

    def on_show(self):
        self.refresh_data()
        # LOAD MODELS for Autocomplete
        self.ent_search.set_completion_list(self._get_all_models())

    def focus_primary(self):
        self.ent_search.focus_set()

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
        df = self.app.inventory.get_inventory()
        if df.empty:
            self._render_tree(df)
            return

        criteria = {}
        
        # Search
        q = self.var_search.get().strip()
        if q:
            if q.isdigit():
                redirect = self.app.inventory.get_merged_target(q)
                if redirect: q = str(redirect)
            criteria['search'] = q
            
        # Supplier
        supp = self.combo_supplier.get()
        if supp and supp != "All":
            criteria['suppliers'] = [supp]
            
        # Status
        if hasattr(self, 'combo_status'):
            stat = self.combo_status.get()
            if stat and stat != "All":
                criteria['status'] = [stat]
            
        # Date Range (Basic implementation)
        try:
            if hasattr(self, 'date_start') and self.date_start.entry.get():
                criteria['date_field'] = 'last_updated'
                # Attempt to parse date logic is skipped for simplicity here
                pass
        except:
            pass

        f = AdvancedFilter()
        filtered_df = f.apply(df, criteria)
        
        # Legacy Min Price
        try:
            min_p = float(self.var_min_price.get())
            if min_p > 0:
                filtered_df = filtered_df[filtered_df['price'] >= min_p]
        except ValueError:
            pass

        self.df_display = filtered_df
        self._render_tree(filtered_df)

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
            
            status = str(row.get('status', 'IN')).upper()
            status_display = f"🟢 {status}" if status == "IN" else f"🔴 {status}"
            
            vals = (
                check_mark,
                original_uid, # Display original ID text
                str(row.get('imei', '')),
                str(row.get('model', '')),
                str(row.get('ram_rom', '')),
                f"{row.get('price_original', 0):.2f}",
                f"{row.get('price', 0):.2f}",
                str(row.get('supplier', '')),
                status_display
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
        
        # Update counter after rendering
        self._update_counter()

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
            self.last_selected_idx = item_id  # Track for range selection
            
        # Update value in tree
        vals = list(self.tree.item(item_id, 'values'))
        vals[0] = icon
        self.tree.item(item_id, values=vals)
        
        self._update_counter()

    def _update_counter(self):
        """Update the counter label with total and selected items"""
        total_items = len(self.tree.get_children())
        selected_items = len(self.checked_ids)
        self.lbl_counter.configure(
            text=f"Total: {total_items} | Selected: {selected_items}",
            foreground="darkgreen" if selected_items > 0 else "gray"
        )
        self.lbl_info.configure(text=f"{selected_items} Item(s) Checked")

    def _multi_select_down(self, event):
        """Ctrl+Shift+Down: Select next item"""
        if not self.tree.get_children():
            return 'break'
        
        children = self.tree.get_children()
        if not self.last_selected_idx or self.last_selected_idx not in children:
            if children:
                self._toggle_check(children[0])
        else:
            current_idx = children.index(self.last_selected_idx)
            if current_idx < len(children) - 1:
                next_item = children[current_idx + 1]
                self._toggle_check(next_item)
        return 'break'

    def _multi_select_up(self, event):
        """Ctrl+Shift+Up: Select previous item"""
        if not self.tree.get_children():
            return 'break'
        
        children = self.tree.get_children()
        if not self.last_selected_idx or self.last_selected_idx not in children:
            if children:
                self._toggle_check(children[-1])
        else:
            current_idx = children.index(self.last_selected_idx)
            if current_idx > 0:
                prev_item = children[current_idx - 1]
                self._toggle_check(prev_item)
        return 'break'

    def _multi_select_home(self, event):
        """Ctrl+Shift+Home: Select all items from current to beginning"""
        if not self.tree.get_children():
            return 'break'
        
        children = self.tree.get_children()
        if self.last_selected_idx and self.last_selected_idx in children:
            current_idx = children.index(self.last_selected_idx)
            for i in range(current_idx + 1):
                if children[i] not in self.checked_ids:
                    self.checked_ids.add(children[i])
                    vals = list(self.tree.item(children[i], 'values'))
                    vals[0] = "☑"
                    self.tree.item(children[i], values=vals)
        self._update_counter()
        return 'break'

    def _multi_select_end(self, event):
        """Ctrl+Shift+End: Select all items from current to end"""
        if not self.tree.get_children():
            return 'break'
        
        children = self.tree.get_children()
        if self.last_selected_idx and self.last_selected_idx in children:
            current_idx = children.index(self.last_selected_idx)
            for i in range(current_idx, len(children)):
                if children[i] not in self.checked_ids:
                    self.checked_ids.add(children[i])
                    vals = list(self.tree.item(children[i], 'values'))
                    vals[0] = "☑"
                    self.tree.item(children[i], values=vals)
        self._update_counter()
        return 'break'

    def _select_all_keyboard(self, event):
        """Ctrl+A: Select all items"""
        self._select_all()
        return 'break'

    def _deselect_all_keyboard(self, event):
        """Ctrl+Shift+A: Deselect all items"""
        self._deselect_all()
        return 'break'

    def _on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            uid = str(item_id).split('_')[0]
            self.app.show_screen('edit')
            self.app.screens['edit'].ent_search.delete(0, tk.END)
            self.app.screens['edit'].ent_search.insert(0, uid)
            self.app.screens['edit']._lookup()

    def _on_row_click(self, event):
        items = self.tree.selection()
        if not items: return
        
        uid = items[0]
        df = self.app.inventory.get_inventory()
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
        mask = df['unique_id'].astype(str).isin(self.checked_ids)
        return df[mask].to_dict('records')

    def _refresh_tree_checks(self):
        for item_id in self.tree.get_children():
            icon = "☑" if item_id in self.checked_ids else "☐"
            vals = list(self.tree.item(item_id, 'values'))
            if vals:
                vals[0] = icon
                self.tree.item(item_id, values=vals)

    def _select_all(self):
        if not hasattr(self, 'df_display') or self.df_display.empty:
            return
        
        uids = self.df_display['unique_id'].astype(str).tolist()
        self.checked_ids.update(uids)
        self._refresh_tree_checks()
        self._update_counter()

    def _deselect_all(self):
        self.checked_ids.clear()
        self._refresh_tree_checks()
        self._update_counter()

    def _toggle_select_all(self):
        if not hasattr(self, 'df_display') or self.df_display.empty:
            return
            
        visible_uids = set(self.df_display['unique_id'].astype(str).tolist())
        
        if visible_uids.issubset(self.checked_ids):
            self._deselect_all()
            if hasattr(self, 'btn_select_all'):
                self.btn_select_all.configure(text="☑ All")
        else:
            self._select_all()
            if hasattr(self, 'btn_select_all'):
                self.btn_select_all.configure(text="☐ All")

    def _print_selected(self):
        items = self._get_checked_data()
        if not items:
            messagebox.showwarning("None Checked", "Please check items [x] to print.")
            return
        
        def do_print():
            count = self.app.printer.print_batch_zpl(items)
            if count > 0:
                messagebox.showinfo("Printing", f"Sent {count} labels to printer (Batch Mode).")
            else:
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
            if self.checked_ids:
                items = list(self.checked_ids)
            else:
                messagebox.showwarning("Select", "Please check or select items to update.")
                return

        if new_status == "OUT":
            self._show_mark_sold_dialog(items)
            return

        if not messagebox.askyesno("Confirm", f"Mark {len(items)} items as {new_status}?"):
            return
            
        success_count = 0
        for iid in items:
            real_uid = str(iid).split('_')[0]
            
            if self.app.inventory.update_item_status(real_uid, new_status, write_to_excel=True):
                success_count += 1
                
        messagebox.showinfo("Done", f"Updated {success_count} items to {new_status}")
        self.checked_ids.clear()
        self.refresh_data()

    def _show_mark_sold_dialog(self, items):
        df = self.app.inventory.get_inventory()
        selected_rows = []
        for iid in items:
            real_uid = str(iid).split('_')[0]
            mask = df['unique_id'].astype(str) == real_uid
            if mask.any():
                selected_rows.append(df[mask].iloc[0])
        
        if not selected_rows: return

        dlg = tk.Toplevel(self)
        dlg.title("Mark as Sold")
        dlg.geometry("400x350")
        dlg.transient(self)
        dlg.grab_set()
        
        ttk.Label(dlg, text=f"Marking {len(selected_rows)} items as SOLD (OUT)", font=('Segoe UI', 11, 'bold')).pack(pady=10)
        
        frame_opts = ttk.LabelFrame(dlg, text="Invoice Options", padding=10)
        frame_opts.pack(fill=tk.X, padx=10, pady=5)
        
        var_auto = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_opts, text="Generate Invoice Automatically", variable=var_auto).pack(anchor=tk.W)
        
        f_date = ttk.Frame(frame_opts)
        f_date.pack(fill=tk.X, pady=5)
        ttk.Label(f_date, text="Date:").pack(side=tk.LEFT)
        ent_date = ttk.Entry(f_date, width=12)
        ent_date.insert(0, str(datetime.date.today()))
        ent_date.pack(side=tk.LEFT, padx=5)
        
        f_buyer = ttk.Frame(frame_opts)
        f_buyer.pack(fill=tk.X, pady=5)
        ttk.Label(f_buyer, text="Buyer:").pack(side=tk.LEFT)
        ent_buyer = ttk.Entry(f_buyer, width=20)
        ent_buyer.insert(0, "Walk-in")
        ent_buyer.pack(side=tk.LEFT, padx=5)
        
        var_inc = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_opts, text="Tax Inclusive Prices", variable=var_inc).pack(anchor=tk.W, pady=5)
        
        def do_confirm():
            success_count = 0
            for row in selected_rows:
                if self.app.inventory.update_item_status(row['unique_id'], "OUT", write_to_excel=True):
                    success_count += 1
            
            if var_auto.get() and success_count > 0:
                self._create_auto_invoice(selected_rows, ent_buyer.get(), ent_date.get(), var_inc.get())
                
            dlg.destroy()
            self.checked_ids.clear()
            self.refresh_data()
            messagebox.showinfo("Success", f"Sold {success_count} items." + ("\nInvoice Generated." if var_auto.get() else ""))

        ttk.Button(dlg, text="CONFIRM SOLD", command=do_confirm, style="Accent.TButton").pack(pady=20)

    def _create_auto_invoice(self, rows, buyer_name, date_str, is_inclusive):
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
                
        except Exception as e:
            messagebox.showerror("Invoice Error", f"Failed to auto-generate invoice: {e}")
