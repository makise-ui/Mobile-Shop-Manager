import pandas as pd
import os
import datetime
import hashlib
import re
from .config import ConfigManager
from .id_registry import IDRegistry
from .utils import backup_excel_file

class InventoryManager:
    def __init__(self, config_manager: ConfigManager, activity_logger=None):
        self.config_manager = config_manager
        self.activity_logger = activity_logger
        self.id_registry = IDRegistry()
        self.inventory_df = pd.DataFrame()
        self.file_status = {}  # Keep track of file read status
        self.conflicts = []

    def load_file(self, file_path):
        """Legacy wrapper or simple load."""
        mapping_data = self.config_manager.get_file_mapping(file_path)
        return self._load_file_internal(file_path, mapping_data)

    def _load_file_internal(self, file_path, mapping_data):
        if not mapping_data:
            return None, "MAPPING_REQUIRED"

        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                # Support specific sheet name
                sheet_name = mapping_data.get('sheet_name', 0)
                # Handle None or empty string properly
                if sheet_name is None or sheet_name == "":
                    sheet_name = 0
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Safety: Ensure DataFrame
            if isinstance(df, pd.Series):
                df = df.to_frame().T
            
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
            if s in ['AVAILABLE', 'AVBL', 'STOCK', 'IN', 'NAN', 'NONE', '', 'NAN']: return 'IN'
            return 'IN'

        # Create a new DF with canonical columns
        canonical = pd.DataFrame()
        
        # Helper to safely get column data as Series
        def get_col(canonical_name):
            mapped_col = None
            for col_name, can_name in mapping.items():
                if can_name == canonical_name:
                    mapped_col = col_name
                    break
            
            if mapped_col and mapped_col in df.columns:
                # SAFE CAST: Convert to object to avoid float.fillna errors
                return df[mapped_col].astype(object)
            return None

        # Map fields
        
        # IMEI Cleaning & Dual Support
        col_imei = get_col('imei')
        if col_imei is not None:
            def clean_imei(val):
                if pd.isna(val): return ""
                s = str(val).strip()
                # Find sequences of 14-16 digits
                nums = re.findall(r'\d{14,16}', s)
                if len(nums) > 1:
                    return " / ".join(sorted(list(set(nums)))) # Unique, sorted
                elif len(nums) == 1:
                    return nums[0]
                return s
            canonical['imei'] = col_imei.apply(clean_imei)
        else:
            canonical['imei'] = ''
        
        # Model
        col_model = get_col('model')
        canonical['model'] = col_model.fillna('Unknown Model').astype(str) if col_model is not None else 'Unknown Model'
        
        # Brand (Extract from model if not mapped)
        col_brand = get_col('brand')
        if col_brand is not None:
            canonical['brand'] = col_brand.fillna('').astype(str).str.upper()
        else:
            # Fallback: First word of model
            canonical['brand'] = canonical['model'].apply(lambda x: str(x).split()[0].upper() if x and str(x).split() else 'UNKNOWN')

        # Price Logic
        col_price = get_col('price')
        if col_price is not None:
            raw_price = pd.to_numeric(col_price, errors='coerce').fillna(0.0)
        else:
            raw_price = 0.0
        
        canonical['price_original'] = raw_price
        
        # Apply Markup
        try:
            markup = float(self.config_manager.get('price_markup_percent', 0.0))
        except (ValueError, TypeError):
            markup = 0.0
            
        if markup > 0:
            # Vectorized calc
            price_with_markup = raw_price * (1 + markup/100.0)
            # Round to nearest 100: round(x/100)*100
            canonical['price'] = price_with_markup.apply(lambda x: round(x / 100) * 100 if x > 0 else x)
        else:
            canonical['price'] = raw_price
        
        # RAM/ROM handling
        ram_rom = get_col('ram_rom')
        if ram_rom is not None:
             canonical['ram_rom'] = ram_rom.fillna('').astype(str)
        else:
            ram = get_col('ram')
            rom = get_col('rom')
            if ram is not None and rom is not None:
                canonical['ram_rom'] = ram.fillna('').astype(str) + " / " + rom.fillna('').astype(str)
            elif ram is not None:
                canonical['ram_rom'] = ram.fillna('').astype(str)
            else:
                canonical['ram_rom'] = ""

        # Supplier handling
        supplier_col = get_col('supplier')
        if supplier_col is not None:
            canonical['supplier'] = supplier_col.fillna(file_supplier).astype(str)
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
        col_buyer = get_col('buyer')
        canonical['buyer'] = col_buyer.fillna('').astype(str) if col_buyer is not None else ''
        
        col_contact = get_col('buyer_contact')
        canonical['buyer_contact'] = col_contact.fillna('').astype(str) if col_contact is not None else ''

        # Grade/Condition
        col_grade = get_col('grade')
        canonical['grade'] = col_grade.fillna('').astype(str) if col_grade is not None else ''

        col_condition = get_col('condition')
        canonical['condition'] = col_condition.fillna('').astype(str) if col_condition is not None else ''

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
                
            if 'notes' in meta:
                row['notes'] = meta['notes']
            if 'color' in meta:
                row['color'] = meta['color']
            if 'grade' in meta:
                row['grade'] = meta['grade']
            if 'condition' in meta:
                row['condition'] = meta['condition']
            if 'price_original' in meta:
                row['price_original'] = float(meta['price_original'])
                
                try:
                    markup = float(self.config_manager.get('price_markup_percent', 0.0))
                except (ValueError, TypeError):
                    markup = 0.0
                    
                if markup > 0:
                    raw_p = row['price_original'] * (1 + markup/100.0)
                    row['price'] = round(raw_p / 100) * 100 if raw_p > 0 else raw_p
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
        
        for key, mapping_data in mappings.items():
            # Support composite keys "path::sheet" or legacy "path"
            file_path = mapping_data.get('file_path', key)
            
            # Fallback if file_path is not in data and key looks composite
            if '::' in key and not os.path.exists(key):
                parts = key.split('::')
                if os.path.exists(parts[0]):
                    file_path = parts[0]
            
            if os.path.exists(file_path):
                # Call internal load to ensure we pass the correct mapping_data (with sheet_name)
                df, status = self._load_file_internal(file_path, mapping_data)

                if status == "SUCCESS" and df is not None:
                    # Enrich with source info (key acts as unique source ID)
                    df['source_file'] = key 
                    all_frames.append(df)
                    self.file_status[key] = "OK"
                else:
                    self.file_status[key] = f"Error: {status}"
            else:
                self.file_status[key] = "Missing"
        
        if all_frames:
            full_df = pd.concat(all_frames, ignore_index=True)
            
            # Filter Hidden Items (Merge Logic)
            def is_visible(uid):
                meta = self.id_registry.get_metadata(uid)
                return not meta.get('is_hidden', False)
            
            # Apply visibility filter
            full_df = full_df[full_df['unique_id'].apply(is_visible)]
            
            # Detect Duplicates (Dual IMEI Aware)
            # Map: Single_IMEI -> list of Row Indices (in full_df)
            imei_map = {}
            processed_indices = set()
            
            # Iterate using index
            for idx in full_df.index:
                row = full_df.loc[idx]
                raw_imei = str(row['imei'])
                if not raw_imei: continue
                
                parts = [p.strip() for p in raw_imei.split('/') if len(p.strip()) > 10]
                for p in parts:
                    if p not in imei_map: imei_map[p] = []
                    imei_map[p].append(idx)
            
            # Find conflicts
            processed_groups = set()
            
            for p, indices in imei_map.items():
                if len(indices) > 1:
                    # Group Key: Sorted Tuple of Row Indices
                    # This prevents reporting the same set of rows multiple times 
                    # (e.g. if they share multiple IMEIs)
                    group_key = tuple(sorted(indices))
                    if group_key in processed_groups: continue
                    processed_groups.add(group_key)
                    
                    rows = full_df.loc[indices]
                    
                    self.conflicts.append({
                        "imei": p,
                        "unique_ids": rows['unique_id'].tolist(),
                        "model": rows.iloc[0]['model'],
                        "sources": list(rows['source_file'].unique()),
                        "rows": rows.to_dict('records')
                    })
            
            self.inventory_df = full_df
        else:
            self.inventory_df = pd.DataFrame(columns=['unique_id', 'imei', 'brand', 'model', 'ram_rom', 'price', 'price_original', 'supplier', 'source_file', 'last_updated', 'status', 'color'])
            
        if self.activity_logger:
            self.activity_logger.log("RELOAD", f"Loaded {len(self.inventory_df)} items from {len(mappings)} sources.")
            
        return self.inventory_df
    
    def resolve_conflict(self, conflict_data, action, keep_source=None):
        """
        Resolves an IMEI conflict.
        action: 'merge' (hides duplicates)
        """
        if action == 'merge':
            rows = conflict_data.get('rows', [])
            if not rows: return False
            
            # Strategy: Keep the first one (or specific if logic allows), hide others
            keeper = rows[0]
            others = rows[1:]
            
            for row in others:
                uid = row['unique_id']
                
                # CRITICAL FIX: Do not merge if IDs are identical (Self-Merge)
                # This prevents an item from hiding itself.
                if str(uid) == str(keeper['unique_id']):
                    continue
                    
                self.id_registry.update_metadata(uid, {
                    'is_hidden': True, 
                    'merged_into': keeper['unique_id'],
                    'merge_reason': 'Conflict Resolution'
                })
                # Log
                self.id_registry.add_history_log(uid, "MERGED", f"Merged into {keeper['unique_id']}")
                if self.activity_logger:
                    self.activity_logger.log("MERGE", f"Merged {uid} into {keeper['unique_id']}")
            
            self.reload_all()
            return True
            
        return False

    def get_merged_target(self, unique_id):
        """
        Checks if an ID is merged/hidden and returns the Target ID it was merged into.
        Returns None if not merged.
        """
        meta = self.id_registry.get_metadata(unique_id)
        if meta.get('is_hidden', False):
            return meta.get('merged_into')
        return None

    def get_item_by_id(self, unique_id, resolve_merged=True):
        """
        Finds an item by ID. 
        If resolve_merged=True, it follows 'merged_into' links.
        Returns (ItemDict, RedirectedID) or (None, None).
        """
        unique_id = str(unique_id).strip()
        
        # 1. Check if merged
        target_id = unique_id
        if resolve_merged:
            merged_into = self.get_merged_target(unique_id)
            if merged_into:
                target_id = str(merged_into)
        
        # 2. Lookup in Inventory DF
        df = self.inventory_df
        mask = df['unique_id'].astype(str) == target_id
        
        if mask.any():
            item = df[mask].iloc[0].to_dict()
            redirected_from = unique_id if target_id != unique_id else None
            return item, redirected_from
            
        return None, None

    def get_inventory(self):
        return self.inventory_df

    def update_item_status(self, item_id, new_status, write_to_excel=False):
        """Updates and persists the status of an item."""
        # --- REDIRECT MERGED IDs ---
        target_id = self.get_merged_target(item_id)
        if target_id:
            if self.activity_logger:
                self.activity_logger.log("REDIRECT", f"Status update for {item_id} redirected to {target_id}")
            item_id = target_id

        # 1. Get Previous Status for logging
        mask = self.inventory_df['unique_id'].astype(str) == str(item_id)
        old_status = "UNKNOWN"
        item_model = ""
        if mask.any():
            row = self.inventory_df[mask].iloc[0]
            old_status = row['status']
            item_model = row['model']

        # 2. Update Internal Registry
        self.id_registry.update_metadata(item_id, {"status": new_status})
        self.id_registry.add_history_log(item_id, "STATUS_CHANGE", f"Moved from {old_status} to {new_status}")
        
        if self.activity_logger:
            self.activity_logger.log("STATUS_UPDATE", f"Item {item_id} ({item_model}) marked as {new_status}")
        
        # 3. Update Memory
        if mask.any():
            self.inventory_df.loc[mask, 'status'] = new_status
            
            # 3. Write to Excel (Optional)
            if write_to_excel:
                try:
                    row = self.inventory_df[mask].iloc[0]
                    # Use the generic writer for status too
                    success, msg = self._write_excel_generic(row, {"status": new_status})
                    if not success:
                        print(f"Excel Update Failed: {msg}")
                        return False
                except Exception as e:
                    print(f"Excel write error: {e}")
                    return False
        return True

    def update_item_data(self, item_id, updates):
        """Updates generic item data (price, color, etc) and writes to Excel."""
        # --- REDIRECT MERGED IDs ---
        target_id = self.get_merged_target(item_id)
        if target_id:
            item_id = target_id

        mask = self.inventory_df['unique_id'].astype(str) == str(item_id)
        if not mask.any(): return False
        
        item_model = self.inventory_df.loc[mask, 'model'].values[0]
        
        # 1. Update Persistent Registry (App DB)
        self.id_registry.update_metadata(item_id, updates)
        
        # Log generic updates
        log_details = ", ".join([f"{k}={v}" for k, v in updates.items()])
        self.id_registry.add_history_log(item_id, "DATA_UPDATE", log_details)
        
        if self.activity_logger:
            self.activity_logger.log("ITEM_UPDATE", f"Updated {item_id} ({item_model}): {log_details}")
        
        # 2. Update Memory
        for k, v in updates.items():
            if k in self.inventory_df.columns:
                self.inventory_df.loc[mask, k] = v
        
        # 3. Update Excel (Best Effort)
        try:
            row = self.inventory_df[mask].iloc[0]
            success, msg = self._write_excel_generic(row, updates)
            if not success:
                 print(f"Update failed: {msg}")
                 return False
            return True
        except Exception as e:
            print(f"Update error: {e}")
            return False

    def _write_excel_generic(self, row_data, updates):
        from openpyxl import load_workbook
        from openpyxl.styles import Font, Alignment, Border, Side
        from copy import copy
        
        # Handle composite keys (path::sheet)
        key = row_data['source_file']
        file_path = key
        if '::' in key and not os.path.exists(key):
            file_path = key.split('::')[0]

        if not os.path.exists(file_path): 
            return False, f"Source file not found: {file_path}"

        # SAFETY 1: Backup
        backup_path = backup_excel_file(file_path)
        if not backup_path:
            return False, "Failed to create backup, aborting write for safety."
            
        # Use the original KEY to get mapping data (it might be keyed by "path::sheet")
        mapping_data = self.config_manager.get_file_mapping(key)
        # If fallback needed (mapping might be keyed by just path)
        if not mapping_data:
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
        
        try:
            wb = load_workbook(file_path)
            
            # Determine Sheet
            sheet_name = mapping_data.get('sheet_name', 0)
            if '::' in key:
                 try:
                     sheet_part = key.split('::')[1]
                     if sheet_part: 
                         # Try converting to int if it looks like one
                         if sheet_part.isdigit():
                             sheet_name = int(sheet_part)
                         else:
                             sheet_name = sheet_part
                 except: pass

            ws = None
            # 1. Try Integer Index
            if isinstance(sheet_name, int):
                try:
                    ws = wb.worksheets[sheet_name]
                except IndexError:
                    print(f"Sheet index {sheet_name} out of range, falling back to active.")
            
            # 2. Try String Name
            elif isinstance(sheet_name, str):
                 if sheet_name in wb.sheetnames:
                     ws = wb[sheet_name]
                 elif sheet_name.isdigit(): # "0" as string?
                     try:
                         ws = wb.worksheets[int(sheet_name)]
                     except: pass

            # 3. Fallback
            if ws is None:
                ws = wb.active
                
            print(f"DEBUG: Writing to Sheet '{ws.title}' in '{file_path}'")

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
                'price': 'Selling Price',
                'grade': 'Grade',
                'condition': 'Condition'
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
            
            row_found = False
            
            for row in ws.iter_rows(min_row=2):
                match = False
                if imei_col_idx:
                    cell_val = row[imei_col_idx-1].value
                    if cell_val:
                        s_cell = str(cell_val).strip().replace('.0', '')
                        # Robust Check: Exact match or partial (for dual IMEI scenarios)
                        # target_imei might be "A / B", cell might be "A" or "B" or "A/B"
                        if s_cell == target_imei:
                            match = True
                        elif target_imei and (target_imei in s_cell or s_cell in target_imei):
                            match = True
                
                if not match and model_col_idx:
                    if str(row[model_col_idx-1].value).strip() == target_model:
                        match = True # Weak match fallback
                
                if match:
                    row_found = True
                    # Apply updates
                    for col_name, new_val in excel_updates.items():
                        if col_name in col_indices:
                            cell = ws.cell(row=row[0].row, column=col_indices[col_name])
                            
                            # Enforce Uppercase for strings
                            if isinstance(new_val, str):
                                new_val = new_val.upper()
                                
                            cell.value = new_val
                            
                            # --- ENFORCE USER STYLE ---
                            # Times New Roman, 11, Bold, Center, All Borders
                            thin = Side(border_style="thin", color="000000")
                            cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)
                            cell.font = Font(name='Times New Roman', size=11, bold=True)
                            cell.alignment = Alignment(horizontal='center', vertical='center')
                                
                    break
            
            if not row_found:
                print(f"Warning: No matching row found in Excel for {target_imei} / {target_model}")
                return False, f"Row not found for {target_imei}"
                
            wb.save(file_path)
            return True, "Success"
            
        except PermissionError:
            return False, "File is open in Excel. Please close it."
        except Exception as e:
            return False, f"Excel Write Error: {e}"
