import unittest
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestGUIBilling(unittest.TestCase):
    def test_import_billing_screen(self):
        """Verify that BillingScreen can be imported from gui.screens.billing"""
        try:
            from gui.screens.billing import BillingScreen
        except ImportError:
            self.fail("Could not import BillingScreen from gui.screens.billing")

if __name__ == '__main__':
    unittest.main()
