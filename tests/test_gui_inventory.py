import unittest
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestGUIInventory(unittest.TestCase):
    def test_import_inventory_screen(self):
        """Verify that InventoryScreen can be imported from gui.screens.inventory"""
        try:
            from gui.screens.inventory import InventoryScreen
        except ImportError:
            self.fail("Could not import InventoryScreen from gui.screens.inventory")

if __name__ == '__main__':
    unittest.main()
