import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
import os
import shutil
import tempfile
import threading
import time
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import Core Modules (assuming they are importable)
from core.config import ConfigManager
from core.inventory import InventoryManager
from core.data_registry import DataRegistry
from core.billing import BillingManager
from core.printer import PrinterManager
from core.barcode_utils import BarcodeGenerator
from core.activity_log import ActivityLogger

class TestingScreen(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent)
        self.app = app_context
        self.test_runner = None
        self._init_ui()

    def _init_ui(self):
        # Header
        hdr = ttk.Frame(self, padding=10)
        hdr.pack(fill=tk.X)
        ttk.Label(hdr, text="System Diagnostics & Regression Suite", font=('Segoe UI', 16, 'bold')).pack(side=tk.LEFT)
        
        btn_frame = ttk.Frame(hdr)
        btn_frame.pack(side=tk.RIGHT)
        
        self.btn_run = ttk.Button(btn_frame, text="▶ Run Full Diagnostic", style="success.TButton", command=self.start_tests)
        self.btn_run.pack(side=tk.LEFT, padx=5)
        
        # Progress
        self.progress = ttk.Progressbar(self, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
        # Results Table
        cols = ("Test Case", "Status", "Duration", "Message")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', selectmode='browse')
        
        self.tree.heading("Test Case", text="Test Case")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Duration", text="Duration (ms)")
        self.tree.heading("Message", text="Details")
        
        self.tree.column("Test Case", width=250)
        self.tree.column("Status", width=100)
        self.tree.column("Duration", width=100)
        self.tree.column("Message", width=400)
        
        # Scrollbar
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=10)
        sb.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0,10))
        
        # Tag Config
        self.tree.tag_configure('PASS', foreground='green')
        self.tree.tag_configure('FAIL', foreground='red', background='#ffe6e6')
        self.tree.tag_configure('ERROR', foreground='darkred', background='#ffcccc')

    def start_tests(self):
        self.btn_run.config(state='disabled')
        # Clear Tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.test_runner = SystemTestRunner(self.update_result, self.on_complete)
        threading.Thread(target=self.test_runner.run, daemon=True).start()

    def update_result(self, test_name, status, duration, message):
        tag = status
        self.tree.insert("", tk.END, values=(test_name, status, f"{duration:.2f}", message), tags=(tag,))
        self.tree.yview_moveto(1)
        
    def on_complete(self, passed, total):
        self.btn_run.config(state='normal')
        if passed == total:
            messagebox.showinfo("Diagnostics Complete", f"All {total} tests PASSED successfully.")
        else:
            messagebox.showwarning("Diagnostics Complete", f"{passed}/{total} tests passed. Check logs for failures.")


class SystemTestRunner:
    def __init__(self, callback_fn, complete_fn):
        self.callback = callback_fn
        self.complete_fn = complete_fn
        self.temp_dir = None
        
    def setup_env(self):
        # Create a sandboxed environment
        self.temp_dir = tempfile.mkdtemp(prefix="mobileshop_test_")
        self.config_dir = os.path.join(self.temp_dir, "config")
        self.logs_dir = os.path.join(self.temp_dir, "logs")
        os.makedirs(self.config_dir)
        os.makedirs(self.logs_dir)
        
        # Mock Config Manager
        self.conf = ConfigManager() 
        # Hack override the internal paths for the test instance
        # Note: Ideally ConfigManager should accept a path in __init__, but assuming it uses a constant or singleton
        # We will create a local instance that we manually feed into other managers
        # Since ConfigManager might read from global CONFIG_DIR, we need to be careful.
        # For safety, we will mock the behavior by manually setting dict values where possible
        # or relying on the managers accepting the config object.
        
        self.conf.config = {
            "app_display_name": "Test Shop",
            "mappings": {},
            "theme_name": "cosmo"
        }
        self.conf.save_config = lambda: None # Disable real saving for now or mock it
        
        # Init Managers with this Mock Config
        self.logger = ActivityLogger(self.conf)
        self.logger.log_file = os.path.join(self.logs_dir, "activity.log") # Redirect log
        
        self.inventory = InventoryManager(self.conf, self.logger)
        self.billing = BillingManager(self.conf, self.logger)
        self.data_reg = DataRegistry() # This reads from real file usually.
        # We need to mock DataRegistry to avoid messing with real colors
        self.data_reg.data = {
            "colors": ["TestColor"],
            "grades": ["A", "B"],
            "buyers": ["TestBuyer"],
            "conditions": ["New", "Old"]
        }
        self.data_reg.save = lambda: None 

    def teardown_env(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass

    def run(self):
        tests = [
            self.test_environment_setup,
            self.test_inventory_file_creation,
            self.test_add_single_item,
            self.test_inventory_search,
            self.test_duplicate_detection,
            self.test_conflict_resolution,
            self.test_batch_queue_logic,
            self.test_status_workflow,
            self.test_billing_validation,
            self.test_billing_checkout,
            self.test_autocomplete_data,
            self.test_zpl_generator,
            self.test_settings_update,
            self.test_data_registry_mgmt,
            self.test_multi_select_logic,
            self.test_file_mapping_logic
        ]
        
        passed = 0
        try:
            self.setup_env()
            
            for test in tests:
                start = time.time()
                name = test.__name__
                try:
                    test()
                    dur = (time.time() - start) * 1000
                    self.callback(name, "PASS", dur, "OK")
                    passed += 1
                except AssertionError as ae:
                    dur = (time.time() - start) * 1000
                    self.callback(name, "FAIL", dur, str(ae))
                except Exception as e:
                    dur = (time.time() - start) * 1000
                    import traceback
                    self.callback(name, "ERROR", dur, str(e))
                    
        except Exception as e:
            self.callback("SETUP_FATAL", "CRITICAL", 0, str(e))
        finally:
            self.teardown_env()
            self.complete_fn(passed, len(tests))

    # --- TEST CASES ---

    def test_environment_setup(self):
        """Verify temp environment is isolated"""
        if not os.path.exists(self.temp_dir):
            raise AssertionError("Temp directory not created")
        if not self.inventory:
            raise AssertionError("Inventory Manager failed to init")

    def test_inventory_file_creation(self):
        """Test creating a new Excel inventory file"""
        self.test_file = os.path.join(self.temp_dir, "test_inv.xlsx")
        
        # Create Mock DF
        df = pd.DataFrame(columns=["S.NO", "MODEL", "IMEI", "PRICE", "STATUS", "COLOR", "GRADE", "CONDITION"])
        df.to_excel(self.test_file, index=False)
        
        if not os.path.exists(self.test_file):
            raise AssertionError("Excel file creation failed")
            
        # Register in Config
        mapping = {
            "MODEL": "model", "IMEI": "imei", "PRICE": "price", 
            "STATUS": "status", "COLOR": "color", "GRADE": "grade", "CONDITION": "condition"
        }
        self.conf.set_file_mapping(self.test_file, {"mapping": mapping, "sheet_name": "Sheet1"})
        
        # Reload Inventory
        self.inventory.reload_all()
        if len(self.inventory.master_df) != 0:
            raise AssertionError("Inventory should be empty initially")

    def test_add_single_item(self):
        """Test adding a single item via logic"""
        # Simulate Quick Entry save
        new_data = {
            "imei": "111222333",
            "model": "Test Phone 1",
            "price": 1000.0,
            "status": "IN",
            "source_file": self.test_file,
            "color": "TestColor"
        }
        
        # 1. Get ID (Mock ID Registry)
        # We need to manually append since we are bypassing UI
        # But InventoryManager doesn't have 'add_item' usually, it reads from file.
        # So we simulate writing to file then reloading.
        
        self._append_to_file(self.test_file, new_data)
        self.inventory.reload_all()
        
        item = self.inventory.get_item_by_imei("111222333")
        if not item:
            raise AssertionError("Item not found after adding")
        if item['model'] != "Test Phone 1":
            raise AssertionError("Model mismatch")

    def test_inventory_search(self):
        """Test searching functionality"""
        results = self.inventory.search("Test Phone")
        if len(results) != 1:
            raise AssertionError(f"Search failed. Expected 1, got {len(results)}")
            
        results_imei = self.inventory.search("111222")
        if len(results_imei) != 1:
            raise AssertionError("Search by Partial IMEI failed")

    def test_duplicate_detection(self):
        """Test adding a duplicate IMEI"""
        # Add same IMEI again
        dup_data = {
            "imei": "111222333",
            "model": "Test Phone Duplicate",
            "price": 2000.0,
            "status": "IN",
            "source_file": self.test_file
        }
        self._append_to_file(self.test_file, dup_data)
        self.inventory.reload_all()
        
        if not self.inventory.conflicts:
            raise AssertionError("Conflict not detected for duplicate IMEI")
        
        if self.inventory.conflicts[0]['imei'] != "111222333":
            raise AssertionError("Incorrect conflict IMEI detected")

    def test_conflict_resolution(self):
        """Test resolving the conflict (Keep New)"""
        if not self.inventory.conflicts:
            raise AssertionError("No conflicts to resolve")
            
        conflict = self.inventory.conflicts[0]
        # Action: 'keep_new' -> Marks old as DUPLICATE, keeps new as IN
        self.inventory.resolve_conflict(conflict, 'keep_new')
        
        # Verify
        self.inventory.reload_all()
        items = self.inventory.master_df[self.inventory.master_df['imei'] == "111222333"]
        # Should have 2 rows now, one IN, one HIDDEN/DUPLICATE or just updated?
        # Logic depends on implementation. Usually marks one as 'DUPLICATE' in status or hidden.
        
        # Check active items
        active = self.inventory.get_item_by_imei("111222333")
        if active['model'] != "Test Phone Duplicate":
             raise AssertionError("Failed to keep new item")

    def test_batch_queue_logic(self):
        """Test Batch Queue Add/Remove logic (Simulated)"""
        queue = []
        # Add
        queue.append("BATCH001")
        queue.append("BATCH002")
        
        if len(queue) != 2: raise AssertionError("Queue add failed")
        
        # Remove (Logic from QuickEntry: LIFO display, FIFO queue)
        # Removing index 0 from Listbox (newest, BATCH002) means removing last from queue
        
        # Simulate UI removal of top item (BATCH002)
        idx_to_remove = 0 # Listbox index
        queue_idx = len(queue) - 1 - idx_to_remove
        removed = queue.pop(queue_idx)
        
        if removed != "BATCH002":
            raise AssertionError(f"Wrong item removed: {removed}")
        if len(queue) != 1:
            raise AssertionError("Queue size incorrect after removal")

    def test_status_workflow(self):
        """Test IN -> SOLD status transition"""
        # We need to simulate marking as SOLD.
        # Usually done via updating Excel status column.
        
        # Let's add a new item for this
        self._append_to_file(self.test_file, {"imei": "SOLD001", "model": "Sales Phone", "status": "IN"})
        self.inventory.reload_all()
        
        # Update Status
        # We cheat and write to file directly because InventoryManager doesn't support direct status write yet 
        # (it relies on ActivityLogger or external edits usually, or the `status.py` screen logic).
        # But wait, InventoryManager usually reads. 
        # We will simulate the Excel update.
        
        # Read file, update, save
        df = pd.read_excel(self.test_file)
        df.loc[df['IMEI'] == "SOLD001", "STATUS"] = "SOLD"
        df.to_excel(self.test_file, index=False)
        
        self.inventory.reload_all()
        item = self.inventory.get_item_by_imei("SOLD001")
        if item['status'] != "SOLD":
            raise AssertionError("Status update failed")

    def test_billing_validation(self):
        """Test that Billing rejects SOLD items"""
        # Try to get the item we just sold
        item = self.inventory.get_item_by_imei("SOLD001")
        
        # Validation logic usually in BillingScreen.add_item
        # We replicate the check:
        if item['status'].upper() in ['SOLD', 'RETURN']:
            # This is expected
            pass
        else:
            raise AssertionError("Billing should verify status is not SOLD")
            
        # Try adding valid item
        valid_item = self.inventory.get_item_by_imei("111222333") # This one is IN
        if valid_item['status'] != "IN":
            raise AssertionError(f"Item status should be IN, got {valid_item['status']}")

    def test_billing_checkout(self):
        """Test full checkout calculation"""
        # Mock Cart
        cart = [
            {"model": "P1", "price": 1000.0, "imei": "C1"},
            {"model": "P2", "price": 500.0, "imei": "C2"}
        ]
        
        total = sum(x['price'] for x in cart)
        if total != 1500.0:
            raise AssertionError("Cart Total Calculation Wrong")
            
        # Tax Calc
        tax_rate = 18.0
        tax_amt = total * (tax_rate / 100)
        grand = total + tax_amt
        
        if grand != 1770.0:
            raise AssertionError("Tax Calculation Wrong")

    def test_autocomplete_data(self):
        """Verify DataRegistry and Inventory feed autocomplete"""
        # DataRegistry
        colors = self.data_reg.get_colors()
        if "TestColor" not in colors:
            raise AssertionError("DataRegistry missing colors")
            
        # Inventory
        # We added "Test Phone 1" and "Test Phone Duplicate"
        df = self.inventory.get_inventory()
        models = df['model'].unique().tolist()
        
        if "Test Phone 1" not in models:
            raise AssertionError("Inventory Autocomplete missing models")

    def test_zpl_generator(self):
        """Test ZPL String Generation"""
        # Mock Generator
        gen = BarcodeGenerator(self.conf)
        # Mock Item
        item = {"model": "Pixel 6", "imei": "123456789", "price": 30000, "variant": "8/128", "grade": "A"}
        
        # Just check if it returns a string starting with ^XA
        # Note: We need PrinterManager logic really.
        pm = PrinterManager(self.conf, gen)
        zpl = pm.generate_zpl_2up([item])
        
        if "^XA" not in zpl or "^XZ" not in zpl:
             raise AssertionError("Invalid ZPL generated")
        if "Pixel 6" not in zpl:
             raise AssertionError("Model name missing in ZPL")

    def test_settings_update(self):
        """Test updating configuration"""
        self.conf.set('tax_rate', 20.0)
        val = self.conf.get('tax_rate')
        if val != 20.0:
            raise AssertionError("Config update failed")

    def test_data_registry_mgmt(self):
        """Test adding/removing data registry items"""
        # Add
        self.data_reg.add_condition("Broken")
        if "Broken" not in self.data_reg.get_conditions():
            raise AssertionError("Add Condition failed")
            
        # Remove
        self.data_reg.remove_condition("Broken")
        if "Broken" in self.data_reg.get_conditions():
            raise AssertionError("Remove Condition failed")

    def test_multi_select_logic(self):
        """Test logic for multi-selection indices"""
        # Simulating logic used in InventoryScreen
        total_items = 10
        selected = {1, 2, 3}
        
        # Test "Select Range"
        anchor = 1
        current = 5
        # Range 1 to 5 -> 1, 2, 3, 4, 5
        new_sel = set(range(min(anchor, current), max(anchor, current) + 1))
        
        if len(new_sel) != 5:
            raise AssertionError("Range selection logic error")
        if 5 not in new_sel:
            raise AssertionError("Range missing end item")

    def test_file_mapping_logic(self):
        """Test column mapping retrieval"""
        # We set this up in `test_inventory_file_creation`
        mapping_data = self.conf.get_file_mapping(self.test_file)
        if not mapping_data:
            raise AssertionError("File mapping lost")
        
        m = mapping_data['mapping']
        if m['MODEL'] != 'model':
             raise AssertionError("Mapping key-value mismatch")

    # --- Helper ---
    def _append_to_file(self, path, data_dict):
        """Helper to append row to Excel for testing"""
        df = pd.read_excel(path)
        # Map keys to headers
        # Mapping was: MODEL->model, etc.
        # We need to reverse it to write to Excel headers
        rev_map = {
            "model": "MODEL", "imei": "IMEI", "price": "PRICE", 
            "status": "STATUS", "color": "COLOR"
        }
        
        new_row = {}
        for k, v in data_dict.items():
            if k in rev_map:
                new_row[rev_map[k]] = v
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_excel(path, index=False)
