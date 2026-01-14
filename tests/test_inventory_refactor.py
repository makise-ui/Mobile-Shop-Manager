import unittest
import pandas as pd
import os
import shutil
import tempfile
import time
import threading
from unittest.mock import MagicMock, patch
from core.inventory import InventoryManager
from core.config import ConfigManager
from core.constants import FIELD_IMEI, FIELD_STATUS, STATUS_SOLD, FIELD_SOURCE_FILE, FIELD_MODEL

class TestInventoryRefactor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.mappings = {}
        self.config_manager.get.return_value = 0.0 # No markup
        
        # Mock ID Registry to avoid dependency on actual DB file
        self.mock_registry = MagicMock()
        self.mock_registry.get_or_create_id.side_effect = lambda row: f"ID_{row.get(FIELD_IMEI, 'UNKNOWN')}"
        self.mock_registry.get_metadata.return_value = {}
        self.mock_registry.update_metadata = MagicMock()
        self.mock_registry.add_history_log = MagicMock()
        
        self.inventory = InventoryManager(self.config_manager)
        self.inventory.id_registry = self.mock_registry
        
        # Stop the background worker for deterministic testing if possible
        # (Though in the refactor we might want to test it specifically)
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_dummy_excel(self, filename, rows):
        path = os.path.join(self.test_dir, filename)
        df = pd.DataFrame(rows)
        df.to_excel(path, index=False)
        return path

    def test_large_dataset_performance(self):
        """Test performance of merging 10,000 items."""
        # Generate 10k items
        rows = [{'IMEI': f'1000000000{i}', 'Model': f'Model {i}', 'Price': 100} for i in range(10000)]
        path = self.create_dummy_excel("large_stock.xlsx", rows)
        
        self.config_manager.mappings = {
            path: {
                'file_path': path,
                'mapping': {'IMEI': FIELD_IMEI, 'Model': 'model', 'Price': 'price'}
            }
        }
        self.config_manager.get_file_mapping.return_value = self.config_manager.mappings[path]
        
        start_time = time.time()
        self.inventory.reload_all()
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"Loaded {len(self.inventory.inventory_df)} items in {duration:.4f} seconds")
        
        # Acceptance criteria is < 2 seconds
        self.assertLess(duration, 2.0, "Loading 10k items took too long")

    @patch('openpyxl.load_workbook')
    def test_file_lock_handling(self, mock_load):
        """Test that locked files are handled gracefully."""
        path = self.create_dummy_excel("locked.xlsx", [{'IMEI': '123456789012345', 'Model': 'Test', 'Status': 'Stock'}])
        
        self.config_manager.mappings = {
            path: {
                'file_path': path,
                'mapping': {'IMEI': FIELD_IMEI, 'Model': 'model', 'Status': FIELD_STATUS}
            }
        }
        self.config_manager.get_file_mapping.return_value = self.config_manager.mappings[path]
        
        # Load initial data
        self.inventory.reload_all()
        
        # Mock PermissionError
        mock_load.side_effect = PermissionError("Permission denied")
        
        # Mock row data
        row_data = {FIELD_SOURCE_FILE: path, FIELD_IMEI: '123456789012345', FIELD_MODEL: 'Test'}
        updates = {FIELD_STATUS: STATUS_SOLD}
        
        success, msg = self.inventory._write_excel_generic(row_data, updates)
        
        self.assertFalse(success)
        self.assertIn("File is open", msg)

    def test_schema_mismatch(self):
        """Test loading a file that doesn't match the mapping."""
        path = self.create_dummy_excel("mismatch.xlsx", [{'WrongCol': 'Data'}])
        
        self.config_manager.mappings = {
            path: {
                'file_path': path,
                'mapping': {'IMEI': FIELD_IMEI} # Expects IMEI
            }
        }
        self.config_manager.get_file_mapping.return_value = self.config_manager.mappings[path]
        
        # Should not crash, should just log error or return empty/partial
        df = self.inventory.reload_all()
        # In current logic, if column missing, it might fill with NaN or empty string.
        # We want to ensure it handles it without key errors.
        self.assertTrue(FIELD_IMEI in df.columns)

    def test_duplicate_imei_detection(self):
        """Test that duplicate IMEIs across files trigger conflicts."""
        # File 1
        path1 = self.create_dummy_excel("source1.xlsx", [{'IMEI': '999999999999999', 'Model': 'M1'}])
        # File 2 (Same IMEI)
        path2 = self.create_dummy_excel("source2.xlsx", [{'IMEI': '999999999999999', 'Model': 'M2'}])
        
        self.config_manager.mappings = {
            path1: {'file_path': path1, 'mapping': {'IMEI': FIELD_IMEI, 'Model': 'model'}},
            path2: {'file_path': path2, 'mapping': {'IMEI': FIELD_IMEI, 'Model': 'model'}}
        }
        
        self.inventory.reload_all()
        
        # Check conflicts
        self.assertTrue(len(self.inventory.conflicts) > 0, "Should detect conflicts")
        self.assertEqual(self.inventory.conflicts[0]['imei'], '999999999999999')

    def test_missing_sheet(self):
        """Test handling of missing sheet names."""
        path = self.create_dummy_excel("sheets.xlsx", [{'IMEI': '1', 'Model': 'M1'}])
        
        self.config_manager.mappings = {
            path: {
                'file_path': path,
                'sheet_name': 'NonExistentSheet',
                'mapping': {'IMEI': FIELD_IMEI}
            }
        }
        self.config_manager.get_file_mapping.return_value = self.config_manager.mappings[path]
        
        self.inventory.reload_all()
        # Current logic might print error to stdout or put error in file_status
        self.assertNotEqual(self.inventory.file_status.get(path), "OK")

    @patch('openpyxl.load_workbook')
    @patch('shutil.move')
    @patch('os.path.exists')
    def test_file_lock_retry(self, mock_exists, mock_move, mock_load):
        """Test that the writer retries when a file is locked."""
        path = self.create_dummy_excel("retry.xlsx", [{'IMEI': '1', 'Model': 'T'}])
        
        self.config_manager.get_file_mapping.return_value = {
            'mapping': {'IMEI': FIELD_IMEI}
        }
        
        # Setup mock workbook
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.worksheets = [mock_ws]
        mock_wb.active = mock_ws
        
        # Mock headers
        mock_header_cell = MagicMock()
        mock_header_cell.value = 'IMEI'
        mock_header_cell.column = 1
        mock_ws.__getitem__.return_value = [mock_header_cell]
        
        # Mock row
        mock_cell_imei = MagicMock()
        mock_cell_imei.value = '1'
        mock_cell_imei.row = 2
        mock_row = [mock_cell_imei]
        mock_ws.iter_rows.return_value = [mock_row]
        mock_ws.cell.return_value = MagicMock()
        
        # Simulate 2 failures followed by 1 success
        mock_load.side_effect = [
            PermissionError("Locked"),
            PermissionError("Locked"),
            mock_wb
        ]
        
        # Ensure we catch the .tmp file check
        def side_effect_exists(p):
            if str(p).endswith('.tmp'):
                return True
            # For other files, defer to real os.path.exists logic 
            # (but since we are patching it, we can't call original easily without saving it)
            # So we just return True for the main file too as it exists
            if p == path: return True
            return False 
            
        mock_exists.side_effect = side_effect_exists
        
        row_data = {FIELD_SOURCE_FILE: path, FIELD_IMEI: '1', FIELD_MODEL: 'T'}
        updates = {FIELD_STATUS: STATUS_SOLD}
        
        success, msg = self.inventory._write_excel_generic(row_data, updates)
        
        self.assertTrue(success, f"Should succeed with retry logic. Error: {msg}")
        self.assertEqual(mock_load.call_count, 3)

    def test_interrupted_save(self):
        """Test that data is preserved if save is interrupted (simulated)."""
        path = self.create_dummy_excel("interrupted.xlsx", [{'IMEI': '1', 'Model': 'T'}])
        
        # We need to verify that we are writing to a temp file first, then renaming.
        # We can check if `wb.save` is called with a temp path.
        
        row_data = {FIELD_SOURCE_FILE: path, FIELD_IMEI: '1', FIELD_MODEL: 'T'}
        updates = {FIELD_STATUS: STATUS_SOLD}
        
        with patch('openpyxl.Workbook.save') as mock_save:
            # Simulate save failure
            mock_save.side_effect = IOError("Disk full")
            
            self.inventory.config_manager.mappings = {
                path: {'file_path': path, 'mapping': {'IMEI': FIELD_IMEI}}
            }
            self.inventory.config_manager.get_file_mapping.return_value = self.inventory.config_manager.mappings[path]

            success, msg = self.inventory._write_excel_generic(row_data, updates)
            
            self.assertFalse(success)
            self.assertIn("Disk full", msg)
            
            # CRITICAL: Verify the original file still exists and is valid
            # (In a real scenario, we'd verify it wasn't partially overwritten, but here we check logic)
            self.assertTrue(os.path.exists(path))
            
            # Verify we TRIED to save to a temp file
            # Since mock_save calls args[0], we verify it was indeed the temp file
            args, _ = mock_save.call_args
            save_path = args[0]
            self.assertTrue(save_path.endswith('.tmp'), "Should write to .tmp file")

    def test_conflict_resolution(self):
        """Test conflict resolution logic."""
        # Setup fake conflict data
        # Row 1 (ID 100) from Source A
        # Row 2 (ID 101) from Source B
        conflict = {
            "imei": "12345",
            "unique_ids": ["100", "101"],
            "rows": [
                {FIELD_UNIQUE_ID: "100", FIELD_SOURCE_FILE: "SourceA"},
                {FIELD_UNIQUE_ID: "101", FIELD_SOURCE_FILE: "SourceB"}
            ]
        }
        
        # Test Default Merge (Should keep first, hide second)
        self.inventory.resolve_conflict(conflict, 'merge')
        
        # Check that ID 101 is hidden
        self.mock_registry.update_metadata.assert_called_with("101", {
            'is_hidden': True,
            'merged_into': "100",
            'merge_reason': 'Conflict Resolution'
        })
        
        # Reset mocks
        self.mock_registry.update_metadata.reset_mock()
        
        # Test "Keep Source B" (The Red Phase Requirement - Logic likely missing)
        # We want to keep 101 and hide 100
        self.inventory.resolve_conflict(conflict, 'merge', keep_source="SourceB")
        
        # Expectation: 100 is hidden, merged into 101
        self.mock_registry.update_metadata.assert_called_with("100", {
            'is_hidden': True,
            'merged_into': "101",
            'merge_reason': 'Conflict Resolution'
        })

if __name__ == '__main__':
    unittest.main()