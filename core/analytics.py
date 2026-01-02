import pandas as pd

class AnalyticsManager:
    def __init__(self, inventory_manager):
        self.inv_manager = inventory_manager

    def get_summary(self):
        df = self.inv_manager.get_inventory()
        if df.empty:
            return {
                "total_items": 0,
                "total_value": 0.0,
                "status_counts": {"IN": 0, "OUT": 0, "RTN": 0},
                "top_models": {},
                "supplier_dist": {}
            }
            
        total_items = len(df)
        total_value = df['price'].sum()
        
        # Status Counts
        # Normalize stats for report
        # IN = IN + RTN
        # OUT = OUT
        s_counts = df['status'].value_counts().to_dict()
        
        # Top 5 Models
        top_models = df['model'].value_counts().head(5).to_dict()
        
        # Supplier Distribution
        supplier_dist = df['supplier'].value_counts().to_dict()
        
        return {
            "total_items": total_items,
            "total_value": total_value,
            "status_counts": s_counts,
            "top_models": top_models,
            "supplier_dist": supplier_dist
        }
