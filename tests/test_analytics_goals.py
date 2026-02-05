import pytest
import pandas as pd
from unittest.mock import MagicMock
from core.analytics import AnalyticsManager

# Mock Inventory Manager
class MockInventory:
    def __init__(self, data):
        self.data = data
    def get_inventory(self):
        return pd.DataFrame(self.data)

def test_goal_progress_calculation():
    # Setup Data: 2 Sold items, Profit = (1000-800) + (500-400) = 200 + 100 = 300
    mock_data = [
        {'model': 'A', 'status': 'OUT', 'price': 1000.0, 'price_original': 800.0, 'supplier': 'Sup1', 'last_updated': pd.Timestamp.now()},
        {'model': 'B', 'status': 'OUT', 'price': 500.0, 'price_original': 400.0, 'supplier': 'Sup2', 'last_updated': pd.Timestamp.now()},
        {'model': 'C', 'status': 'IN', 'price': 2000.0, 'price_original': 1500.0, 'supplier': 'Sup1', 'last_updated': pd.Timestamp.now()},
    ]
    
    inv = MockInventory(mock_data)
    analytics = AnalyticsManager(inv)
    
    # Test Goal: Target 1000
    # Expected: Profit 300. Progress 30%. Remaining 700.
    result = analytics.get_goal_progress("Test Trip", target_amount=1000)
    
    print(f"\nResult: {result}")
    
    assert result['current'] == 300.0
    assert result['percent'] == 30.0
    assert result['remaining'] == 700.0
    assert result['daily_profit_avg'] > 0  # Should have velocity
    assert result['est_days_to_goal'] < 9999

def test_goal_zero_sales():
    mock_data = [
        {'model': 'C', 'status': 'IN', 'price': 2000.0, 'price_original': 1500.0, 'supplier': 'Sup1', 'last_updated': pd.Timestamp.now()},
    ]
    inv = MockInventory(mock_data)
    analytics = AnalyticsManager(inv)
    
    result = analytics.get_goal_progress("Test Trip", target_amount=1000)
    
    assert result['current'] == 0.0
    assert result['percent'] == 0.0
    assert result['remaining'] == 1000.0
    assert result['est_days_to_goal'] == 9999

if __name__ == "__main__":
    # Allow running directly to see print output
    test_goal_progress_calculation()
    test_goal_zero_sales()
    print("All tests passed!")
