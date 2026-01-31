import unittest
import sys
import os
import tkinter as tk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestReportingIntegration(unittest.TestCase):
    def test_reporting_screen_structure(self):
        """Verify ReportingScreen imports and method existence."""
        try:
            from gui.reporting import ReportingScreen
            # Check for new methods we plan to add
            # (Note: They don't exist yet, so this is just checking import for now)
            self.assertTrue(hasattr(ReportingScreen, '__init__'))
        except ImportError:
            self.fail("Could not import ReportingScreen")

if __name__ == '__main__':
    unittest.main()
