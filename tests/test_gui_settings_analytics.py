import unittest
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestGUISettingsAnalytics(unittest.TestCase):
    def test_import_settings_screen(self):
        """Verify that ManageFilesScreen can be imported from gui.screens.settings"""
        try:
            from gui.screens.settings import ManageFilesScreen
        except ImportError:
            self.fail("Could not import ManageFilesScreen from gui.screens.settings")

    def test_import_analytics_screen(self):
        """Verify that DashboardScreen and ActivityLogScreen can be imported from gui.screens.analytics"""
        try:
            from gui.screens.analytics import DashboardScreen, ActivityLogScreen
        except ImportError:
            self.fail("Could not import DashboardScreen/ActivityLogScreen from gui.screens.analytics")

if __name__ == '__main__':
    unittest.main()
