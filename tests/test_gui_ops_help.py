import unittest
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestGUIOpsHelp(unittest.TestCase):
    def test_import_help_screen(self):
        """Verify that HelpScreen can be imported from gui.screens.help"""
        try:
            from gui.screens.help import HelpScreen
        except ImportError:
            self.fail("Could not import HelpScreen from gui.screens.help")

    def test_import_ops_screens(self):
        """Verify that SearchScreen, StatusScreen, EditDataScreen can be imported from gui.screens.ops"""
        try:
            from gui.screens.ops import SearchScreen, StatusScreen, EditDataScreen
        except ImportError:
            self.fail("Could not import screens from gui.screens.ops")

if __name__ == '__main__':
    unittest.main()
