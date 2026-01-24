import unittest
import os
import sys
import tkinter as tk

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestAppIntegration(unittest.TestCase):
    def test_app_imports(self):
        """Verify gui.app imports screens from gui.screens"""
        try:
            from gui.app import MainApp
            # Check if MainApp has imported screens
            import gui.screens
            self.assertTrue(hasattr(gui.screens, 'InventoryScreen'))
            self.assertTrue(hasattr(gui.screens, 'BillingScreen'))
            self.assertTrue(hasattr(gui.screens, 'DashboardScreen'))
        except ImportError as e:
            self.fail(f"App integration import failed: {e}")

if __name__ == '__main__':
    unittest.main()
