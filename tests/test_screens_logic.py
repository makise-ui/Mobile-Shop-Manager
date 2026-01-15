import unittest
from gui.screens import SearchScreen

class TestSearchScreenLogic(unittest.TestCase):
    def test_method_existence(self):
        self.assertTrue(hasattr(SearchScreen, '_get_display_date'), "SearchScreen missing _get_display_date method")

if __name__ == '__main__':
    unittest.main()