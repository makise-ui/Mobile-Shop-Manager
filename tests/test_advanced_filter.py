import unittest
import pandas as pd
import datetime
from core.filters import AdvancedFilter

class TestAdvancedFilter(unittest.TestCase):
    def setUp(self):
        # Create dummy data
        self.df = pd.DataFrame([
            {
                'unique_id': 1, 'model': 'S23', 'supplier': 'Samsung', 
                'status': 'IN', 'price': 1000, 
                'last_updated': datetime.datetime(2023, 1, 1),
                'date_sold': None
            },
            {
                'unique_id': 2, 'model': 'iPhone 14', 'supplier': 'Apple', 
                'status': 'OUT', 'price': 1200, 
                'last_updated': datetime.datetime(2023, 2, 1),
                'date_sold': datetime.datetime(2023, 2, 10)
            },
            {
                'unique_id': 3, 'model': 'Pixel 7', 'supplier': 'Google', 
                'status': 'IN', 'price': 800, 
                'last_updated': datetime.datetime(2023, 3, 1),
                'date_sold': None
            }
        ])
        self.filter = AdvancedFilter()

    def test_filter_by_supplier(self):
        criteria = {'suppliers': ['Samsung', 'Google']}
        res = self.filter.apply(self.df, criteria)
        self.assertEqual(len(res), 2)
        self.assertTrue(all(s in ['Samsung', 'Google'] for s in res['supplier']))

    def test_filter_by_date_range(self):
        # Filter 'last_updated' between Jan 15 and Feb 15
        criteria = {
            'date_field': 'last_updated',
            'start_date': datetime.datetime(2023, 1, 15),
            'end_date': datetime.datetime(2023, 2, 15)
        }
        res = self.filter.apply(self.df, criteria)
        self.assertEqual(len(res), 1)
        self.assertEqual(res.iloc[0]['model'], 'iPhone 14')

    def test_filter_by_status(self):
        criteria = {'status': ['IN']}
        res = self.filter.apply(self.df, criteria)
        self.assertEqual(len(res), 2)
        self.assertTrue(all(s == 'IN' for s in res['status']))

    def test_multi_criteria(self):
        # Status IN AND Supplier Samsung
        criteria = {'status': ['IN'], 'suppliers': ['Samsung']}
        res = self.filter.apply(self.df, criteria)
        self.assertEqual(len(res), 1)
        self.assertEqual(res.iloc[0]['model'], 'S23')

if __name__ == '__main__':
    unittest.main()