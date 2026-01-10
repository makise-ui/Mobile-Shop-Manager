import pandas as pd

class AnalyticsManager:
    def __init__(self, inventory_manager):
        self.inv_manager = inventory_manager

    def get_summary(self, sim_params=None):
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
            
        # Normalize status for consistent counting
        df['status'] = df['status'].astype(str).str.upper().str.strip()
        
        # Ensure Cost Column
        if 'price_original' not in df.columns:
            df['price_original'] = df['price']

        # HELPER: Vectorized Simulation
        def get_sim_values(sub_df):
            if not sim_params or not sim_params.get('enabled', False):
                return sub_df['price'], sub_df['price_original']
            
            tgt = sim_params.get('target', 'cost')
            base = sim_params.get('base', 'price')
            pct = float(sim_params.get('percent', 0.0))
            flat = float(sim_params.get('flat', 0.0))
            
            base_series = sub_df['price'] if base == 'price' else sub_df['price_original']
            new_val = base_series * (1 + pct/100.0) + flat
            
            if tgt == 'cost':
                return sub_df['price'], new_val
            else:
                return new_val, sub_df['price_original']

        # --- Metrics for CURRENT STOCK (Status = IN only) ---
        stock_df = df[df['status'] == 'IN'].copy()
        
        # Calculate Simulated Values
        s_price, s_cost = get_sim_values(stock_df)
        
        total_items = len(stock_df)
        total_value = s_price.sum()
        total_cost = s_cost.sum()
        est_profit = total_value - total_cost
        
        # --- Realized Profit (Sold Items Only) ---
        sold_df = df[df['status'] == 'OUT'].copy()
        
        r_price, r_cost = get_sim_values(sold_df)
        
        realized_sales = r_price.sum()
        realized_profit = realized_sales - r_cost.sum()
        
        # Status Counts
        s_counts = df['status'].value_counts().to_dict()
        
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

    def get_demand_forecast(self):
        """
        AI/Statistical Forecast for Stock Demand.
        Returns: List of dicts {model, sales_velocity, current_stock, days_remaining, status}
        """
        df = self.inv_manager.get_inventory()
        if df.empty or 'status' not in df.columns or 'last_updated' not in df.columns:
            return []
            
        # 1. Calculate Sales Velocity (Items sold per day over last 30 days)
        sold_df = df[df['status'] == 'OUT'].copy()
        
        # Ensure dates
        sold_df['last_updated'] = pd.to_datetime(sold_df['last_updated'], errors='coerce')
        
        # Filter for recent history (e.g., last 60 days to get a trend)
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=60)
        recent_sales = sold_df[sold_df['last_updated'] >= cutoff_date]
        
        if recent_sales.empty:
            return []
            
        # Group by Model -> Count
        sales_counts = recent_sales['model'].value_counts()
        
        # Velocity = Count / 60 days
        # Improvement: If first sale was 10 days ago, divide by 10, not 60?
        # For simplicity/robustness, we use a fixed window of 30 days active selling.
        # Let's use 30 days average.
        sales_velocity = sales_counts / 60.0 # items per day
        
        # 2. Get Current Stock
        stock_df = df[df['status'] == 'IN']
        stock_counts = stock_df['model'].value_counts()
        
        # 3. Forecast
        alerts = []
        for model, velocity in sales_velocity.items():
            if velocity < 0.1: continue # Ignore very slow movers (< 1 per 10 days)
            
            current_stock = stock_counts.get(model, 0)
            
            if current_stock == 0:
                days_left = 0
                status = "OUT_OF_STOCK"
            else:
                days_left = int(current_stock / velocity)
                status = "LOW_STOCK" if days_left < 14 else "OK"
            
            if status != "OK":
                alerts.append({
                    "model": model,
                    "velocity": round(velocity * 7, 1), # Weekly Sales
                    "stock": current_stock,
                    "days_left": days_left,
                    "status": status
                })
        
        # Sort by urgency (Out of stock first, then low days)
        alerts.sort(key=lambda x: x['days_left'])
        return alerts
