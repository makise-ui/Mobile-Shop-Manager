import pandas as pd
import os
import datetime
import hashlib
from .config import ConfigManager
from .id_registry import IDRegistry
from .utils import backup_excel_file

class InventoryManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.id_registry = IDRegistry()
        self.inventory_df = pd.DataFrame()
        self.file_status = {}  # Keep track of file read status
        self.conflicts = []

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
        """
        mapping = mapping_data.get('mapping', {})
        file_supplier = mapping_data.get('supplier', '')
        
        # Helper: Normalize Status
        def norm_status(val):
            s = str(val).upper().strip()
            if s in ['OUT', 'SOLD', 'SALE']: return 'OUT'
            if s in ['RTN', 'RETURN', 'RET']: return 'RTN'
            # Catch-all for available synonyms
            if s in ['AVAILABLE', 'AVBL', 'STOCK', 'IN', 'NAN', 'NONE', '']: return 'IN'
            # Fallback: if it's not OUT/RTN, treat as IN but log it?
            # For strictness, let's treat anything else as IN
            return 'IN'

        # Create a new DF with canonical columns
        canonical = pd.DataFrame()
        
        # ... (keep get_col helper) ...
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
        try:
            markup = float(self.config_manager.get('price_markup_percent', 0.0))
        except (ValueError, TypeError):
            markup = 0.0
            
        if markup > 0:
            canonical['price'] = raw_price * (1 + markup/100.0)
        else:
            canonical['price'] = raw_price
        
        # RAM/ROM handling
        ram_rom = get_col('ram_rom')
        if ram_rom is not None:
             canonical['ram_rom'] = ram_rom
        else:
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

        # Status handling (Excel)
        status_col = get_col('status')
        if status_col is not None:
            canonical['status'] = status_col.apply(norm_status)
        else:
            canonical['status'] = 'IN' # Default status (Available)

        # Color handling
        color_col = get_col('color')
        if color_col is not None:
            canonical['color'] = color_col.fillna('').astype(str)
        else:
            canonical['color'] = ''

        # Buyer handling
        canonical['buyer'] = get_col('buyer').fillna('').astype(str) if get_col('buyer') is not None else ''
        canonical['buyer_contact'] = get_col('buyer_contact').fillna('').astype(str) if get_col('buyer_contact') is not None else ''

        # Fill missing basics
        canonical['imei'] = canonical['imei'].fillna('').astype(str)
        canonical['model'] = canonical['model'].fillna('Unknown Model').astype(str)
        
        # Metadata
        canonical['source_file'] = str(file_path)
        canonical['last_updated'] = datetime.datetime.now()
        
        # Generate Unique ID using persistent registry
        canonical['unique_id'] = canonical.apply(lambda row: self.id_registry.get_or_create_id(row), axis=1)
        
        # Merge persistent metadata (status, notes, color, price overrides)
        def apply_overrides(row):
            meta = self.id_registry.get_metadata(row['unique_id'])
            
            # Conflict Detection Logic
            excel_status = row['status']
            app_status = None
            
            if 'status' in meta:
                # Normalize the app-stored status too!
                app_status = norm_status(meta['status'])
                row['status'] = app_status
                
                # Check for conflict (only if excel has explicit status)
                if excel_status != app_status:
                    # We trust App status usually, but let's note the conflict
                    pass

            if 'notes' in meta:
                row['notes'] = meta['notes']
            if 'color' in meta:
                row['color'] = meta['color']
            if 'price_original' in meta:
                row['price_original'] = float(meta['price_original'])
                
                try:
                    markup = float(self.config_manager.get('price_markup_percent', 0.0))
                except (ValueError, TypeError):
                    markup = 0.0
                    
                if markup > 0:
                    row['price'] = row['price_original'] * (1 + markup/100.0)
                else:
                    row['price'] = row['price_original']
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
                            "model": group.iloc[0]['model'],
                            "sources": list(sources),
                            "rows": group.to_dict('records')
                        })
            
            self.inventory_df = full_df
        else:
            self.inventory_df = pd.DataFrame(columns=['unique_id', 'imei', 'model', 'ram_rom', 'price', 'price_original', 'supplier', 'source_file', 'last_updated', 'status', 'color'])
            
        return self.inventory_df
    
    def resolve_conflict(self, conflict_data, action, keep_source=None):
        """
        Resolves an IMEI conflict.
        action: 'merge' (not really applicable for physical goods, usually means keep one) or 'keep_one'
        keep_source: The file path to keep the record from.
        """
        # Logic: If 'keep_one', we effectively want to IGNORE the other rows in future loads?
        # Or just tell the user to fix the Excel file?
        # For now, we can flag the 'duplicate' in the ID Registry to be ignored or just log it.
        # But real resolution involves modifying the source file to remove the duplicate.
        
        if action == 'keep_one' and keep_source:
            # We can't easily delete from the source excel here without risk.
            # Best approach: Add to a 'blacklist' or 'ignore' list in config?
            # Or just update the registry to map this IMEI -> Specific Source File preferred?
            pass
        return True # Placeholder

    def get_inventory(self):
        return self.inventory_df

    def update_item_status(self, item_id, new_status, write_to_excel=False):
        """Updates and persists the status of an item."""
        # 1. Get Previous Status for logging
        mask = self.inventory_df['unique_id'].astype(str) == str(item_id)
        old_status = "UNKNOWN"
        if mask.any():
            old_status = self.inventory_df.loc[mask, 'status'].values[0]

        # 2. Update Internal Registry
        self.id_registry.update_metadata(item_id, {"status": new_status})
        self.id_registry.add_history_log(item_id, "STATUS_CHANGE", f"Moved from {old_status} to {new_status}")
        
        # 3. Update Memory
        if mask.any():
            self.inventory_df.loc[mask, 'status'] = new_status
            
            # 3. Write to Excel (Optional)
            if write_to_excel:
                try:
                    row = self.inventory_df[mask].iloc[0]
                    # Use the generic writer for status too
                    self._write_excel_generic(row, {"status": new_status})
                except Exception as e:
                    print(f"Excel write error: {e}")
                    return False
        return True

    def update_item_data(self, item_id, updates):
        """Updates generic item data (price, color, etc) and writes to Excel."""
        mask = self.inventory_df['unique_id'].astype(str) == str(item_id)
        if not mask.any(): return False
        
        # 1. Update Persistent Registry (App DB)
        self.id_registry.update_metadata(item_id, updates)
        
        # Log generic updates
        log_details = ", ".join([f"{k}={v}" for k, v in updates.items()])
        self.id_registry.add_history_log(item_id, "DATA_UPDATE", log_details)
        
        # 2. Update Memory
        for k, v in updates.items():
            if k in self.inventory_df.columns:
                self.inventory_df.loc[mask, k] = v
        
        # 3. Update Excel (Best Effort)
        try:
            row = self.inventory_df[mask].iloc[0]
            self._write_excel_generic(row, updates)
            return True
        except Exception as e:
            print(f"Update error: {e}")
            return False

    def _write_excel_generic(self, row_data, updates):
        from openpyxl import load_workbook
        
        file_path = row_data['source_file']
        if not os.path.exists(file_path): return

        # SAFETY 1: Backup
        backup_path = backup_excel_file(file_path)
        if not backup_path:
            print("Failed to create backup, aborting write for safety.")
            return

        mapping_data = self.config_manager.get_file_mapping(file_path)
        mapping = mapping_data.get('mapping', {})
        
        # Build map of InternalField -> ExcelColumnName
        field_to_col = {v: k for k, v in mapping.items()}
        
        # Map updates to Excel headers
        excel_updates = {}
        for k, v in updates.items():
            if k == 'price_original': k = 'price'
            if k in field_to_col:
                excel_updates[field_to_col[k]] = v
        
        # If excel_updates empty, check if we need to CREATE columns
        # even if not mapped.
        
        try:
            wb = load_workbook(file_path)
            ws = wb.active
            
            # Find Header Columns
            col_indices = {}
            max_col_idx = 0
            for cell in ws[1]:
                val = str(cell.value).strip()
                if val:
                    col_indices[val] = cell.column
                    if cell.column > max_col_idx: max_col_idx = cell.column
            
            default_headers = {
                'buyer': 'Buyer Name',
                'buyer_contact': 'Buyer Contact',
                'notes': 'Notes',
                'status': 'Status',
                'color': 'Color',
                'price': 'Selling Price'
            }
            
            for field, value in updates.items():
                header_name = None
                if field in field_to_col:
                    header_name = field_to_col[field]
                elif field in default_headers:
                    header_name = default_headers[field]
                
                if header_name:
                    if header_name not in col_indices:
                        # Create New Column
                        max_col_idx += 1
                        ws.cell(row=1, column=max_col_idx).value = header_name
                        col_indices[header_name] = max_col_idx
                    excel_updates[header_name] = value

            # Find Row (Match IMEI or Model)
            target_imei = str(row_data['imei'])
            target_model = str(row_data['model'])
            
            # Find IMEI/Model col for matching
            imei_header = field_to_col.get('imei')
            model_header = field_to_col.get('model')
            
            imei_col_idx = col_indices.get(imei_header)
            model_col_idx = col_indices.get(model_header)
            
            for row in ws.iter_rows(min_row=2):
                match = False
                if imei_col_idx and str(row[imei_col_idx-1].value) == target_imei:
                    match = True
                elif model_col_idx and str(row[model_col_idx-1].value) == target_model:
                    match = True # Weak match
                
                if match:
                    # Apply updates
                    for col_name, new_val in excel_updates.items():
                        if col_name in col_indices:
                            ws.cell(row=row[0].row, column=col_indices[col_name]).value = new_val
                    break
            
            wb.save(file_path)
            
        except PermissionError:
            print(f"Error: File {file_path} is open in Excel. Cannot save.")
            raise Exception("File is open in Excel. Please close it.")
        except Exception as e:
            print(f"Excel Write Error: {e}")
            raise
