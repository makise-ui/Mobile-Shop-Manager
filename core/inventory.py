import pandas as pd
import os
import datetime
import hashlib
from .config import ConfigManager
from .id_registry import IDRegistry

class InventoryManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.id_registry = IDRegistry()
        self.inventory_df = pd.DataFrame()
        self.file_status = {}  # Keep track of file read status

    def load_file(self, file_path):
        mapping_data = self.config_manager.get_file_mapping(file_path)
        if not mapping_data:
            # Need mapping
            return None, "MAPPING_REQUIRED"

        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Normalize columns based on mapping
            normalized_df = self._normalize_data(df, mapping_data, file_path)
            return normalized_df, "SUCCESS"
        except Exception as e:
            return None, str(e)

    def _normalize_data(self, df, mapping_data, file_path):
        """
        Converts the raw dataframe to the canonical format using the mapping.
        Canonical columns: unique_id, imei, model, ram_rom, price, supplier, status, source_file, last_updated
        """
        mapping = mapping_data.get('mapping', {})
        file_supplier = mapping_data.get('supplier', '')
        
        # Create a new DF with canonical columns
        canonical = pd.DataFrame()
        
        # Helper to safely get column data
        def get_col(canonical_name):
            mapped_col = None
            for col_name, can_name in mapping.items():
                if can_name == canonical_name:
                    mapped_col = col_name
                    break
            
            if mapped_col and mapped_col in df.columns:
                return df[mapped_col]
            return None

        # Map fields
        canonical['imei'] = get_col('imei')
        canonical['model'] = get_col('model')
        
        # Price Logic
        raw_price = pd.to_numeric(get_col('price'), errors='coerce').fillna(0.0)
        canonical['price_original'] = raw_price
        
        # Apply Markup
        markup = self.config_manager.get('price_markup_percent', 0.0)
        if markup > 0:
            canonical['price'] = raw_price * (1 + markup/100.0)
        else:
            canonical['price'] = raw_price
        
        # RAM/ROM handling
        ram_rom = get_col('ram_rom')
        if ram_rom is not None:
             canonical['ram_rom'] = ram_rom
        else:
            # Try combining if mapped separately
            ram = get_col('ram')
            rom = get_col('rom')
            if ram is not None and rom is not None:
                canonical['ram_rom'] = ram.astype(str) + " / " + rom.astype(str)
            elif ram is not None:
                canonical['ram_rom'] = ram.astype(str)
            else:
                canonical['ram_rom'] = ""

        # Supplier handling
        supplier_col = get_col('supplier')
        if supplier_col is not None:
            canonical['supplier'] = supplier_col
        else:
            canonical['supplier'] = file_supplier

        # Status handling
        status_col = get_col('status')
        if status_col is not None:
            # Normalize to IN/OUT/RTN
            def norm_status(val):
                s = str(val).upper().strip()
                if s in ['OUT', 'SOLD', 'SALE']: return 'OUT'
                if s in ['RTN', 'RETURN', 'RET']: return 'RTN'
                return 'IN' # Default
            canonical['status'] = status_col.apply(norm_status)
        else:
            canonical['status'] = 'IN' # Default status (Available)

        # Color handling
        color_col = get_col('color')
        if color_col is not None:
            canonical['color'] = color_col.fillna('').astype(str)
        else:
            canonical['color'] = ''

        # Fill missing basics
        canonical['imei'] = canonical['imei'].fillna('').astype(str)
        canonical['model'] = canonical['model'].fillna('Unknown Model').astype(str)
        
        # Metadata
        canonical['source_file'] = str(file_path)
        canonical['last_updated'] = datetime.datetime.now()
        canonical['status'] = 'Available' # Default status
        
        # Generate Unique ID using persistent registry
        canonical['unique_id'] = canonical.apply(lambda row: self.id_registry.get_or_create_id(row), axis=1)
        
        # Merge persistent metadata (status override)
        def apply_overrides(row):
            meta = self.id_registry.get_metadata(row['unique_id'])
            if 'status' in meta:
                row['status'] = meta['status']
            if 'notes' in meta:
                row['notes'] = meta['notes']
            return row
            
        canonical = canonical.apply(apply_overrides, axis=1)
        
        return canonical

    def reload_all(self):
        """Reloads all files in mappings and merges them."""
        all_frames = []
        mappings = self.config_manager.mappings
        self.conflicts = [] # Reset conflicts
        
        for file_path in mappings.keys():
            if os.path.exists(file_path):
                df, status = self.load_file(file_path)
                if status == "SUCCESS" and df is not None:
                    all_frames.append(df)
                    self.file_status[file_path] = "OK"
                else:
                    self.file_status[file_path] = f"Error: {status}"
            else:
                self.file_status[file_path] = "Missing"
        
        if all_frames:
            full_df = pd.concat(all_frames, ignore_index=True)
            
            # Detect Duplicates (IMEI based)
            # Filter valid IMEIs
            valid_imeis = full_df[full_df['imei'].str.len() > 10]
            dupes = valid_imeis[valid_imeis.duplicated('imei', keep=False)]
            
            if not dupes.empty:
                # Group by IMEI to identify source files
                for imei, group in dupes.groupby('imei'):
                    sources = group['source_file'].unique()
                    if len(sources) > 1:
                        self.conflicts.append({
                            "imei": imei,
                            "sources": list(sources),
                            "rows": group.to_dict('records')
                        })
            
            self.inventory_df = full_df
        else:
            self.inventory_df = pd.DataFrame(columns=['unique_id', 'imei', 'model', 'ram_rom', 'price', 'price_original', 'supplier', 'source_file', 'last_updated', 'status', 'color'])
            
        return self.inventory_df

    def get_inventory(self):
        return self.inventory_df

    def update_item_status(self, item_id, new_status):
        """Updates and persists the status of an item."""
        self.id_registry.update_metadata(item_id, {"status": new_status})
        # Update in-memory DF
        mask = self.inventory_df['unique_id'].astype(str) == str(item_id)
        self.inventory_df.loc[mask, 'status'] = new_status
