import unittest
from gui.screens import InventoryScreen

class TestInventorySelection(unittest.TestCase):
    def test_methods_exist(self):
        self.assertTrue(hasattr(InventoryScreen, '_select_all'), "InventoryScreen missing _select_all")
        self.assertTrue(hasattr(InventoryScreen, '_deselect_all'), "InventoryScreen missing _deselect_all")
        self.assertTrue(hasattr(InventoryScreen, '_toggle_select_all'), "InventoryScreen missing _toggle_select_all")

if __name__ == '__main__':
    unittest.main()