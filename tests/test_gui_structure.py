import unittest
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestGUIStructure(unittest.TestCase):
    def test_gui_screens_package_exists(self):
        """Verify that the gui/screens package exists and is a valid python package."""
        self.assertTrue(os.path.isdir("gui/screens"), "gui/screens directory does not exist")
        self.assertTrue(os.path.exists("gui/screens/__init__.py"), "gui/screens/__init__.py does not exist")

    def test_gui_screens_import(self):
        """Verify that we can import from the new package."""
        # This test will fail until we actually create the package
        try:
            import gui.screens
        except ImportError:
            self.fail("Could not import gui.screens")

if __name__ == '__main__':
    unittest.main()
