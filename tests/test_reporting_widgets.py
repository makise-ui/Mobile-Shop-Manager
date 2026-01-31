import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestReportingWidgetsImports(unittest.TestCase):
    def test_imports(self):
        """Verify that we can import the new widget classes."""
        try:
            # These will fail initially (Red Phase)
            from gui.screens.reporting_widgets import AdvancedFilterPanel, SamplingPanel
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import AdvancedFilterPanel or SamplingPanel from gui.screens.reporting_widgets")

if __name__ == '__main__':
    unittest.main()
