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
                "total_cost": 0.0,
                "est_profit": 0.0,
                "status_counts": {"IN": 0, "OUT": 0, "RTN": 0},
                "top_models": {},
                "supplier_dist": {}
            }
            
        total_items = len(df)
        total_value = df['price'].sum()
        
        # Calculate Cost & Profit
        # Ensure price_original exists
        if 'price_original' not in df.columns:
            total_cost = total_value # Fallback
            df['price_original'] = df['price'] # Temp fix for calculation
        else:
            total_cost = df['price_original'].sum()
            
        est_profit = total_value - total_cost
        
        # Realized Profit (Sold Items Only)
        # Normalize status for consistent counting
        df['status'] = df['status'].astype(str).str.upper().str.strip()
        
        sold_df = df[df['status'] == 'OUT']
        realized_sales = sold_df['price'].sum()
        realized_cost = sold_df['price_original'].sum()
        realized_profit = realized_sales - realized_cost
        
        # Status Counts
        s_counts = df['status'].value_counts().to_dict()
        print(f"DEBUG ANALYTICS: {s_counts}")
        
        # Top 5 Models
        top_models = df['model'].value_counts().head(5).to_dict()
        
        # Supplier Distribution
        supplier_dist = df['supplier'].value_counts().to_dict()
        
        return {
            "total_items": total_items,
            "total_value": total_value,
            "total_cost": total_cost,
            "est_profit": est_profit,
            "realized_sales": realized_sales,
            "realized_profit": realized_profit,
            "status_counts": s_counts,
            "top_models": top_models,
            "supplier_dist": supplier_dist
        }
