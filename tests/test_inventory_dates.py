import unittest
import pandas as pd
import tempfile
import shutil
import os
import datetime
from unittest.mock import MagicMock
from core.inventory import InventoryManager
from core.constants import STATUS_OUT, STATUS_IN, FIELD_UNIQUE_ID, FIELD_STATUS

class TestInventoryDates(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.mock_config = MagicMock()
        self.mock_config.mappings = {}
        # Mock IDRegistry to avoid file I/O
        self.mock_registry = MagicMock()
        self.mock_registry.get_ids_batch.return_value = ["TEST_ID_1"]
        self.mock_registry.get_metadata.return_value = {}
        
        self.inv_mgr = InventoryManager(self.mock_config)
        # Inject mock registry
        self.inv_mgr.id_registry = self.mock_registry
        
        # Setup dummy inventory
        self.inv_mgr.inventory_df = pd.DataFrame([{
            FIELD_UNIQUE_ID: "TEST_ID_1",
            FIELD_STATUS: STATUS_IN,
            "model": "Test Model",
            "source_file": "test.xlsx"
        }])

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_sold_date_persistence(self):
        """Test that changing status to OUT persists the current date as sold_date."""
        item_id = "TEST_ID_1"
        
        # 1. Update Status to OUT
        self.inv_mgr.update_item_status(item_id, STATUS_OUT, write_to_excel=False)
        
        # 2. Verify Metadata Update
        # We expect update_metadata to be called with 'sold_date'
        args = self.mock_registry.update_metadata.call_args_list
        found_sold_date = False
        captured_date = None
        
        for call in args:
            uid, updates = call[0]
            if uid == item_id and 'sold_date' in updates:
                found_sold_date = True
                captured_date = updates['sold_date']
                break
        
        self.assertTrue(found_sold_date, "sold_date was not persisted to metadata")
        
        # Verify format (ISO)
        try:
            dt = datetime.datetime.fromisoformat(captured_date)
            # Ensure it's recent (within 5 seconds)
            diff = datetime.datetime.now() - dt
            self.assertLess(diff.total_seconds(), 5)
        except ValueError:
            self.fail(f"Persisted sold_date '{captured_date}' is not in ISO format")

    def test_sold_date_retrieval(self):
        """Test that _normalize_data retrieves sold_date from metadata."""
        # Setup metadata with a specific sold date
        past_date = (datetime.datetime.now() - datetime.timedelta(days=10)).isoformat()
        
        # Mock registry to return this metadata
        self.mock_registry.get_metadata.return_value = {
            FIELD_STATUS: STATUS_OUT,
            "sold_date": past_date
        }
        
        # Create a dummy dataframe representing a loaded file
        raw_df = pd.DataFrame([{
            "IMEI": "123456789012345",
            "Model": "Test Phone",
            "Status": "SOLD", # File says SOLD
            "Price": 10000
        }])
        
        mapping_data = {
            "mapping": {
                "IMEI": "imei",
                "Model": "model",
                "Status": "status",
                "Price": "price"
            }
        }
        
        # Use the real _normalize_data logic (we need to bypass ID generation issues if any)
        # We need to ensure get_ids_batch returns consistent IDs
        self.mock_registry.get_ids_batch.return_value = ["TEST_ID_1"]
        self.mock_registry.get_metadata.side_effect = lambda uid: {
            FIELD_STATUS: STATUS_OUT,
            "sold_date": past_date
        } if uid == "TEST_ID_1" else {}

        # Run normalization
        # We need to temporarily restore the real method if we mocked it? 
        # No, we only mocked instances on inv_mgr, but _normalize_data is a method on inv_mgr.
        # We haven't mocked _normalize_data itself.
        
        normalized = self.inv_mgr._normalize_data(raw_df, mapping_data, "dummy.xlsx")
        
        # Check if 'date_sold' column exists and matches
        self.assertIn('date_sold', normalized.columns)
        actual_date = normalized.iloc[0]['date_sold']
        
        # Should match the past_date (as string or datetime object depending on impl)
        # Ideally we want datetime object in DF
        self.assertEqual(str(actual_date), str(datetime.datetime.fromisoformat(past_date)))

if __name__ == '__main__':
    unittest.main()
