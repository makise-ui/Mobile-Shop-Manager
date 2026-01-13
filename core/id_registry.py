import json
import hashlib
import datetime
from .database import DatabaseManager
from .migration import migrate_json_to_db

class IDRegistry:
    def __init__(self):
        # Ensure migration happens before any DB usage
        migrate_json_to_db()
        self.db = DatabaseManager()

    def get_or_create_id(self, row_data):
        """
        Returns a stable integer ID for the given row (Database-backed).
        """
        imei = str(row_data.get('imei', '')).strip()
        model = str(row_data.get('model', '')).strip()
        ram_rom = str(row_data.get('ram_rom', '')).strip()
        supplier = str(row_data.get('supplier', '')).strip()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        found_id = None
        
        # 1. Lookup by IMEI
        if imei and len(imei) > 4:
            cursor.execute("SELECT unique_id FROM items WHERE imei = ?", (imei,))
            row = cursor.fetchone()
            if row: found_id = row[0]
        
        # 2. Lookup by Hash (Fallback for non-IMEI items)
        hash_key = None
        if not found_id:
            raw_str = f"{model}|{ram_rom}|{supplier}"
            hash_key = f"HASH:{hashlib.md5(raw_str.encode()).hexdigest()}"
            cursor.execute("SELECT unique_id FROM items WHERE hash_key = ?", (hash_key,))
            row = cursor.fetchone()
            if row: found_id = row[0]
            
        if found_id:
            conn.close()
            return found_id
            
        # 3. Create New ID
        # Find next available ID (MAX integer value)
        cursor.execute("SELECT MAX(CAST(unique_id AS INTEGER)) FROM items")
        res = cursor.fetchone()
        max_id = res[0] if res and res[0] is not None else 0
        new_id = str(max_id + 1)
        
        try:
            cursor.execute('''
                INSERT INTO items (unique_id, imei, hash_key, date_added, last_updated, status)
                VALUES (?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'), 'IN')
            ''', (new_id, imei if len(imei)>4 else None, hash_key))
            conn.commit()
        except Exception as e:
            print(f"ID Generation Error: {e}")
        finally:
            conn.close()
            
        return new_id

    def update_metadata(self, item_id, data):
        """Updates persistent data. Handles core columns and JSON blob."""
        data = data.copy() # Don't mutate original
        
        # Core fields
        status = data.pop('status', None)
        
        # Database Update
        conn = self.db.get_connection()
        try:
            # 1. Update Core
            if status:
                conn.execute("UPDATE items SET status = ?, last_updated = datetime('now', 'localtime') WHERE unique_id = ?", (status, str(item_id)))
            
            # 2. Update Metadata Blob
            if data:
                cursor = conn.execute("SELECT metadata FROM items WHERE unique_id = ?", (str(item_id),))
                row = cursor.fetchone()
                current_meta = {}
                if row and row[0]:
                    try: current_meta = json.loads(row[0])
                    except: pass
                
                current_meta.update(data)
                conn.execute("UPDATE items SET metadata = ?, last_updated = datetime('now', 'localtime') WHERE unique_id = ?", 
                             (json.dumps(current_meta), str(item_id)))
            
            conn.commit()
        finally:
            conn.close()

    def batch_update_metadata(self, updates_dict):
        """
        Transactional batch update.
        updates_dict: { item_id: {data_dict}, ... }
        """
        conn = self.db.get_connection()
        try:
            for uid, data in updates_dict.items():
                data = data.copy()
                status = data.pop('status', None)
                date_added = data.pop('date_added', None)
                
                # Update Core Columns
                fields = []
                vals = []
                if status: 
                    fields.append("status = ?")
                    vals.append(status)
                if date_added:
                    fields.append("date_added = ?")
                    vals.append(date_added)
                
                if fields:
                    fields.append("last_updated = datetime('now', 'localtime')")
                    vals.append(str(uid))
                    conn.execute(f"UPDATE items SET {', '.join(fields)} WHERE unique_id = ?", vals)
                
                # Update JSON Metadata
                if data:
                    cursor = conn.execute("SELECT metadata FROM items WHERE unique_id = ?", (str(uid),))
                    row = cursor.fetchone()
                    meta = {}
                    if row and row[0]:
                        try: meta = json.loads(row[0])
                        except: pass
                    meta.update(data)
                    conn.execute("UPDATE items SET metadata = ? WHERE unique_id = ?", (json.dumps(meta), str(uid)))
            
            conn.commit()
        except Exception as e:
            print(f"Batch Update Error: {e}")
            conn.rollback()
        finally:
            conn.close()

    def batch_sync_details(self, items_list):
        """
        Synchronizes full item details from Excel to DB.
        items_list: list of dicts with 'unique_id' and other fields.
        """
        conn = self.db.get_connection()
        try:
            for item in items_list:
                # Copy to avoid mutating original
                item = item.copy()
                uid = str(item.pop('unique_id'))
                model = item.get('model', '')
                
                # Exclude core/control fields from metadata blob
                # We want to store attributes like price, ram, color, supplier
                exclude = ['imei', 'hash_key', 'date_added', 'last_updated', 'status', 'is_hidden', 'source_file', 'check']
                meta_update = {k: v for k, v in item.items() if k not in exclude}
                
                # Fetch existing to merge
                cursor = conn.execute("SELECT metadata FROM items WHERE unique_id = ?", (uid,))
                row = cursor.fetchone()
                current_meta = {}
                if row and row[0]:
                    try: current_meta = json.loads(row[0])
                    except: pass
                
                # Update with new values
                current_meta.update(meta_update)
                
                conn.execute("UPDATE items SET model = ?, metadata = ? WHERE unique_id = ?", 
                             (model, json.dumps(current_meta), uid))
            
            conn.commit()
        except Exception as e:
            print(f"Batch Sync Error: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_metadata(self, item_id):
        """Returns dict of item data + history list."""
        data = self.db.get_item_data(item_id)
        data['history'] = self.db.get_history(item_id)
        return data

    def add_history_log(self, item_id, action, details):
        self.db.add_history(item_id, action, details)

    def get_all_buyers(self):
        """Returns { 'Buyer': 'Contact' }"""
        # Scan DB items where metadata contains 'buyer'
        # Currently buyer is in metadata blob or flattened in get_item_data?
        # InventoryManager puts buyer in metadata.
        # We can scan the items table.
        # Since 'metadata' is JSON text, we can't query it easily with simple SQLite unless JSON1 is enabled.
        # Fallback: Read all items (SLOW?) or just rely on new buyers added.
        # Optimization: Fetch only metadata column
        
        buyers = {}
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT metadata FROM items WHERE metadata LIKE '%buyer%'")
        
        while True:
            rows = cursor.fetchmany(100)
            if not rows: break
            for row in rows:
                try:
                    meta = json.loads(row[0])
                    b = meta.get('buyer')
                    c = meta.get('buyer_contact')
                    if b:
                        buyers[b] = c
                except: pass
        conn.close()
        return buyers