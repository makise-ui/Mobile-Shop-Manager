import unittest
import os
import sys
import tkinter as tk

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestGUIBase(unittest.TestCase):
    def test_import_base_screen(self):
        """Verify that BaseScreen can be imported from gui.base"""
        try:
            from gui.base import BaseScreen
        except ImportError:
            self.fail("Could not import BaseScreen from gui.base")

    def test_import_autocomplete_entry(self):
        """Verify that AutocompleteEntry can be imported from gui.base"""
        try:
            from gui.base import AutocompleteEntry
        except ImportError:
            self.fail("Could not import AutocompleteEntry from gui.base")

if __name__ == '__main__':
    unittest.main()
