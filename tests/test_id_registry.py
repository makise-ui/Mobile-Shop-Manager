import unittest
import os
import json
from pathlib import Path
from core.id_registry import IDRegistry
from core import id_registry
import tempfile
import shutil

class TestIDRegistryDates(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.registry_file = Path(self.test_dir) / "id_registry.json"
        
        # Patch the file path
        self.original_path = id_registry.ID_REGISTRY_FILE
        id_registry.ID_REGISTRY_FILE = self.registry_file
        
        self.registry = IDRegistry()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        id_registry.ID_REGISTRY_FILE = self.original_path

    def test_store_and_retrieve_added_date(self):
        item_id = 1
        date_str = "2023-01-01"
        
        # Store date
        self.registry.update_metadata(item_id, {'added_date': date_str})
        
        # Retrieve
        meta = self.registry.get_metadata(item_id)
        self.assertEqual(meta.get('added_date'), date_str)
        
        # Reload registry
        new_reg = IDRegistry()
        meta_new = new_reg.get_metadata(item_id)
        self.assertEqual(meta_new.get('added_date'), date_str)

    def test_preserve_existing_date(self):
        item_id = 2
        original_date = "2023-01-01"
        
        # Set initial date
        self.registry.update_metadata(item_id, {'added_date': original_date})
        
        # Try to set new date safely
        new_date = "2023-02-01"
        self.registry.set_date_added_if_empty(item_id, new_date)
        
        meta = self.registry.get_metadata(item_id)
        self.assertEqual(meta.get('added_date'), original_date) # Should still be original
        
        # Test setting for new item
        item_id_3 = 3
        self.registry.set_date_added_if_empty(item_id_3, new_date)
        self.assertEqual(self.registry.get_metadata(item_id_3).get('added_date'), new_date)

if __name__ == '__main__':
    unittest.main()