import unittest
import os
import shutil
import pandas as pd
from core.config import ConfigManager
from core.inventory import InventoryManager
from core.billing import BillingManager

class TestAppLogic(unittest.TestCase):
    def setUp(self):
        # Create a temp test directory
        self.test_dir = "test_env"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Mock paths for config
        self.config_path = os.path.join(self.test_dir, "config.json")
        self.mappings_path = os.path.join(self.test_dir, "mappings.json")
        
        # Init ConfigManager with mocked paths
        self.cm = ConfigManager()
        self.cm.config_path = self.config_path
        self.cm.mappings_path = self.mappings_path
        self.cm.save_config(self.cm.load_config()) # Init files

        self.im = InventoryManager(self.cm)
        self.bm = BillingManager(self.cm)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_config_defaults(self):
        self.assertEqual(self.cm.get('store_name'), "4 Bros Mobile")
        self.assertEqual(self.cm.get('gst_default_percent'), 18.0)

    def test_inventory_logic(self):
        # Create a dummy CSV
        csv_path = os.path.join(self.test_dir, "stock.csv")
        df = pd.DataFrame({
            'Model Name': ['Vivo V27', 'Oppo A78'],
            'IMEI Number': ['123456789012345', '987654321098765'],
            'Cost': [25000, 15000],
            'RAM': [8, 8],
            'ROM': [128, 128]
        })
        df.to_csv(csv_path, index=False)
        
        # Set Mapping
        mapping = {
            "mapping": {
                "Model Name": "model",
                "IMEI Number": "imei",
                "Cost": "price",
                "RAM": "ram",
                "ROM": "rom"
            },
            "supplier": "Test Supplier"
        }
        self.cm.set_file_mapping(csv_path, mapping)
        
        # Load
        df_inv = self.im.reload_all()
        
        self.assertFalse(df_inv.empty)
        self.assertEqual(len(df_inv), 2)
        
        # Check canonical fields
        row1 = df_inv.iloc[0]
        self.assertEqual(row1['model'], 'Vivo V27')
        self.assertEqual(row1['price'], 25000)
        self.assertEqual(row1['supplier'], 'Test Supplier')
        self.assertEqual(row1['ram_rom'], '8 / 128') # Combined logic
        self.assertEqual(row1['unique_id'], '123456789012345')

    def test_billing_calc(self):
        # Taxable Value = 1000, Tax 18%
        calc = self.bm.calculate_tax(1000.0, 18.0, is_interstate=False)
        self.assertEqual(calc['taxable_value'], 1000.0)
        self.assertEqual(calc['total_tax'], 180.0)
        self.assertEqual(calc['cgst'], 90.0)
        self.assertEqual(calc['sgst'], 90.0)
        self.assertEqual(calc['igst'], 0.0)
        self.assertEqual(calc['total_amount'], 1180.0)

        # Interstate
        calc_inter = self.bm.calculate_tax(1000.0, 18.0, is_interstate=True)
        self.assertEqual(calc_inter['igst'], 180.0)
        self.assertEqual(calc_inter['cgst'], 0.0)

if __name__ == '__main__':
    unittest.main()
