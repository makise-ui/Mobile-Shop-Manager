import unittest
import pandas as pd
import datetime
from core.reporting import ReportGenerator

class TestAdvancedReporting(unittest.TestCase):
    def setUp(self):
        # Create a sample DataFrame
        self.data = {
            'unique_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'model': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
            'price': [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
            'last_updated': [
                datetime.datetime.now() - datetime.timedelta(days=i) 
                for i in range(10)
            ]
        }
        self.df = pd.DataFrame(self.data)
        self.reporter = ReportGenerator(self.df)

    def test_modulo_filtering_even(self):
        """Test filtering even IDs: ID % 2 == 0"""
        conditions = [{
            'field': 'unique_id',
            'operator': 'Modulo',
            'value': '2=0'  # Divisor=Remainder
        }]
        result = self.reporter.apply_filters(conditions)
        self.assertEqual(len(result), 5)
        self.assertTrue(all(result['unique_id'] % 2 == 0))

    def test_modulo_filtering_odd(self):
        """Test filtering odd IDs: ID % 2 == 1"""
        conditions = [{
            'field': 'unique_id',
            'operator': 'Modulo',
            'value': '2=1'
        }]
        result = self.reporter.apply_filters(conditions)
        self.assertEqual(len(result), 5)
        self.assertTrue(all(result['unique_id'] % 2 == 1))

    def test_apply_limit(self):
        """Test limiting the result set"""
        limit = 3
        # Assuming we add apply_limit method to ReportGenerator or as a separate util
        # Since the plan says "Implement apply_limit(df, limit)", I'll assume it's a method on the instance for now 
        # or we pass it to export/filter. The spec says "Sampling & Limits" in sidebar.
        # Let's assume we implement it as a method on ReportGenerator.
        
        # NOTE: Since the method doesn't exist yet, this test will fail (AttributeError).
        result = self.reporter.apply_limit(self.df, limit)
        self.assertEqual(len(result), 3)
        self.assertEqual(result.iloc[0]['unique_id'], 1)

    def test_custom_expression_valid(self):
        """Test valid custom expression"""
        expr = "price > 500 and unique_id < 9"
        # Expect IDs 6, 7, 8 (prices 600, 700, 800)
        result = self.reporter.apply_custom_expression(self.df, expr)
        self.assertEqual(len(result), 3)
        self.assertListEqual(result['unique_id'].tolist(), [6, 7, 8])

    def test_custom_expression_invalid(self):
        """Test invalid custom expression handles gracefully"""
        expr = "price >>>> 500" # Syntax error
        result = self.reporter.apply_custom_expression(self.df, expr)
        # Should return original DF or empty? Usually logging error and returning empty or original is safer.
        # Let's decide to return empty DF on error to indicate failure/no matches.
        self.assertTrue(result.empty)

    def test_date_above(self):
        """Test date 'Above' (Greater Than)"""
        # Date 2 days ago
        target_date = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        conditions = [{
            'field': 'last_updated',
            'operator': 'Above',
            'value': target_date
        }]
        # Dates are: Now, Now-1d, Now-2d, ...
        # Above Now-2d means Now and Now-1d (since they are newer/greater)
        result = self.reporter.apply_filters(conditions)
        # Check logic: "Above" usually means "After" in dates.
        # Expected: 0 and 1 days ago.
        self.assertTrue(len(result) >= 1) 
        # NOTE: Date comparison in strings vs datetime objects needs care. 
        # apply_filters implementation needs to handle this.

if __name__ == '__main__':
    unittest.main()
