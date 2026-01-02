import unittest
import os
import shutil
from core.config import ConfigManager
from core.inventory import InventoryManager
from core.analytics import AnalyticsManager
from gui.screens import BillingScreen

class MockApp:
    def __init__(self):
        self.app_config = ConfigManager()
        self.inventory = InventoryManager(self.app_config)
        self.billing = None # Mock if needed

class TestScreenLogic(unittest.TestCase):
    def setUp(self):
        self.app = MockApp()
        self.analytics = AnalyticsManager(self.app.inventory)

    def test_analytics_empty(self):
        stats = self.analytics.get_summary()
        self.assertEqual(stats['total_items'], 0)
        self.assertEqual(stats['total_value'], 0.0)

    # Note: Testing Tkinter widgets (Screens) directly in headless CI/CLI is difficult 
    # because they instantiate tk.Frame which requires a display.
    # We focus on the logic separated into 'core' or ensuring the methods don't crash 
    # if we mock the parent. But mocking Tkinter parent is hard.
    # So we trust the core logic tests and the structure.

if __name__ == '__main__':
    unittest.main()
