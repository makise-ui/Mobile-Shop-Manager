import unittest
import json
import os
import shutil
import sqlite3
from pathlib import Path
import sys

# Ensure root is in path
sys.path.append(str(Path(__file__).parent.parent))

# Import modules to be patched
import core.config
import core.database
import core.migration
from core.id_registry import IDRegistry
from core.database import DatabaseManager

class TestDatabaseMigration(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("temp_test_db")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        
        # Create Config Dir
        self.config_dir = self.test_dir / "config"
        self.config_dir.mkdir()
        
        # PATCH PATHS
        self.orig_config_dir = core.config.CONFIG_DIR
        self.orig_reg_file = core.config.ID_REGISTRY_FILE
        # Use getattr to be safe if DB_FILE is somehow missing (though it shouldn't be)
        self.orig_db_file = getattr(core.database, 'DB_FILE', None)
        self.orig_mig_reg_file = getattr(core.migration, 'ID_REGISTRY_FILE', None)
        
        # Apply Patch
        core.config.CONFIG_DIR = self.config_dir
        core.config.ID_REGISTRY_FILE = self.config_dir / "id_registry.json"
        core.database.DB_FILE = self.config_dir / "inventory.db"
        core.migration.ID_REGISTRY_FILE = core.config.ID_REGISTRY_FILE
        
        # Create Dummy JSON
        self.dummy_json = {
            "items": {
                "IMEI:123456789012345": 1001,
                "HASH:abcdef123456": 1002
            },
            "metadata": {
                "1001": {
                    "status": "SOLD",
                    "date_added": "2023-01-01 10:00:00",
                    "buyer": "Test Buyer",
                    "history": [
                        {"ts": "2023-01-01 10:00:00", "action": "ADD", "details": "Initial"},
                        {"ts": "2023-01-05 12:00:00", "action": "SOLD", "details": "Sold to Test Buyer"}
                    ]
                },
                "1002": {
                    "status": "IN",
                    "notes": "No IMEI item"
                }
            }
        }
        with open(core.config.ID_REGISTRY_FILE, 'w') as f:
            json.dump(self.dummy_json, f)

    def tearDown(self):
        # Restore Paths
        core.config.CONFIG_DIR = self.orig_config_dir
        core.config.ID_REGISTRY_FILE = self.orig_reg_file
        if self.orig_db_file:
            core.database.DB_FILE = self.orig_db_file
        if self.orig_mig_reg_file:
            core.migration.ID_REGISTRY_FILE = self.orig_mig_reg_file
        
        if self.test_dir.exists():
            try:
                shutil.rmtree(self.test_dir)
            except: pass

    def test_migration_and_sync(self):
        print("\n--- Testing Database Migration & Sync ---")
        
        # 1. Initialize Registry (Should trigger Migration)
        registry = IDRegistry()
        
        # 2. Verify DB Content
        # Use the patched DB_FILE directly
        db = DatabaseManager(core.database.DB_FILE)
        conn = db.connect() # Updated to connect()
        cursor = conn.cursor()
        
        # Check Items
        cursor.execute("SELECT * FROM items")
        items = cursor.fetchall()
        self.assertEqual(len(items), 2, "Should have 2 items migrated")
        
        # Check Item 1001
        cursor.execute("SELECT * FROM items WHERE unique_id='1001'")
        item1 = dict(cursor.fetchone())
        self.assertEqual(item1['status'], 'SOLD')
        self.assertEqual(item1['imei'], '123456789012345')
        
        # Check Metadata Blob
        meta1 = json.loads(item1['metadata'])
        self.assertTrue('buyer' in meta1)
        self.assertEqual(meta1['buyer'], 'Test Buyer')
        
        # Check History
        cursor.execute("SELECT * FROM history WHERE unique_id='1001'")
        hist = cursor.fetchall()
        self.assertEqual(len(hist), 2, "Should have 2 history entries")
        
        print("✓ Migration Verified")
        
        # 3. Test Batch Sync (Updating details from 'Excel')
        rows = [
            {
                'unique_id': 1001,
                'model': 'iPhone 14',
                'price': 50000,
                'color': 'Blue'
            },
            {
                'unique_id': 1002,
                'model': 'Charger',
                'price': 500
            }
        ]
        
        registry.batch_sync_details(rows)
        
        # Verify DB Updates
        cursor.execute("SELECT model, metadata FROM items WHERE unique_id='1001'")
        row = cursor.fetchone()
        self.assertEqual(row['model'], 'iPhone 14', "Model should update")
        meta = json.loads(row['metadata'])
        self.assertEqual(meta['price'], 50000, "Price should be synced")
        self.assertEqual(meta['color'], 'Blue', "Color should be synced")
        self.assertEqual(meta['buyer'], 'Test Buyer', "Existing metadata should be preserved")
        
        print("✓ Batch Sync Verified")
        conn.close()

if __name__ == '__main__':
    unittest.main()