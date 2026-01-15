import pandas as pd
import datetime

class AdvancedFilter:
    def apply(self, df, criteria):
        """
        Filters the DataFrame based on the provided criteria.
        criteria: dict
        {
          'suppliers': list of strings,
          'status': list of strings,
          'date_field': str ('last_updated' or 'date_sold'),
          'start_date': datetime,
          'end_date': datetime,
          'search': str
        }
        """
        if df.empty:
            return df
            
        result = df.copy()
        
        # 1. Suppliers
        if 'suppliers' in criteria and criteria['suppliers']:
            result = result[result['supplier'].isin(criteria['suppliers'])]
            
        # 2. Status
        if 'status' in criteria and criteria['status']:
            result = result[result['status'].isin(criteria['status'])]
            
        # 3. Date Range
        if 'date_field' in criteria and criteria.get('start_date'):
            field = criteria['date_field']
            if field in result.columns:
                # Ensure datetime
                if not pd.api.types.is_datetime64_any_dtype(result[field]):
                    result[field] = pd.to_datetime(result[field], errors='coerce')
                
                start_date = criteria['start_date']
                end_date = criteria.get('end_date')
                
                if start_date:
                    result = result[result[field] >= start_date]
                if end_date:
                    result = result[result[field] <= end_date]
                    
        # 4. Search (General) - optional if criteria has search query
        if 'search' in criteria and criteria['search']:
            q = criteria['search'].lower()
            mask = result.apply(lambda x: q in str(x.values).lower(), axis=1) # naive row search
            result = result[mask]
            
        return result