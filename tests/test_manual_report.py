import unittest
import shutil
import tempfile
import os
from pathlib import Path
from core.manual_report import ManualReportSession

class MockConfigManager:
    def __init__(self, temp_dir):
        self.config_dir = Path(temp_dir)
        
    def get_config_dir(self):
        return self.config_dir

class TestManualReportSession(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = MockConfigManager(self.temp_dir)
        self.session = ManualReportSession(self.config_manager)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_add_and_persistence(self):
        self.session.add_id("ID1")
        self.session.add_id("ID2")
        self.assertEqual(self.session.get_ids(), ["ID1", "ID2"])
        
        # Reload
        new_session = ManualReportSession(self.config_manager)
        self.assertEqual(new_session.get_ids(), ["ID1", "ID2"])

    def test_remove(self):
        self.session.add_id("ID1")
        self.session.remove_id("ID1")
        self.assertEqual(self.session.get_ids(), [])
        
        # Reload
        new_session = ManualReportSession(self.config_manager)
        self.assertEqual(new_session.get_ids(), [])

    def test_clear(self):
        self.session.add_id("ID1")
        self.session.clear()
        self.assertEqual(self.session.get_ids(), [])
        
        # Reload
        new_session = ManualReportSession(self.config_manager)
        self.assertEqual(new_session.get_ids(), [])

    def test_duplicate_add(self):
        self.assertTrue(self.session.add_id("ID1"))
        self.assertFalse(self.session.add_id("ID1")) # Should return False
        self.assertEqual(len(self.session.get_ids()), 1)

if __name__ == '__main__':
    unittest.main()
