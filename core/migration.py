import json
import datetime
from .database import DatabaseManager
from .config import ID_REGISTRY_FILE

def migrate_json_to_db():
    """
    Safely migrates data from id_registry.json to inventory.db.
    This is a one-time operation.
    """
    if not ID_REGISTRY_FILE.exists():
        print("Migration: No JSON registry found. Skipping.")
        return

    db = DatabaseManager()
    
    # Check if DB is already populated (Simple check: count items)
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM items")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count > 0:
        # DB already has data. Assume migration done.
        return

    print("Migration: Starting JSON to SQLite migration...")
    
    try:
        with open(ID_REGISTRY_FILE, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Migration Failed: Could not load JSON file. {e}")
        return

    # 1. Migrate Identity Mappings (The "items" key)
    # structure: "IMEI:123": 1001 or "HASH:abc": 1002
    items_map = data.get("items", {})
    items_metadata = data.get("metadata", {})
    
    conn = db.connect()
    try:
        total_migrated = 0
        
        # Step A: Create Base Records from ID Map
        for key, unique_id in items_map.items():
            imei = None
            hash_key = None
            
            if key.startswith("IMEI:"):
                imei = key.split(":", 1)[1]
            elif key.startswith("HASH:"):
                hash_key = key.split(":", 1)[1]
            
            # Insert basic identity
            conn.execute('''
                INSERT OR IGNORE INTO items (unique_id, imei, hash_key, date_added, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(unique_id), imei, hash_key, datetime.datetime.now(), datetime.datetime.now()))
            
        # Step B: Enrich with Metadata
        for unique_id, meta in items_metadata.items():
            # Extract core fields
            status = meta.get('status', 'IN')
            date_added = meta.get('date_added')
            history = meta.get('history', [])
            
            # Infer date if missing
            if not date_added and history:
                try:
                    sorted_hist = sorted(history, key=lambda x: x.get('ts', ''))
                    date_added = sorted_hist[0].get('ts')
                except: pass
            
            if not date_added:
                date_added = datetime.datetime.now()

            # Prepare JSON metadata blob (exclude promoted fields)
            meta_copy = meta.copy()
            meta_copy.pop('history', None)
            meta_copy.pop('status', None)
            meta_copy.pop('date_added', None)
            
            # Update the record created in Step A (or create if missing metadata-only entry?)
            # UPSERT logic: Try update, if 0 rows, insert (though Step A should have covered it if it had a mapping)
            
            cursor = conn.execute('''
                UPDATE items 
                SET status = ?, date_added = ?, last_updated = ?, metadata = ?
                WHERE unique_id = ?
            ''', (status, date_added, datetime.datetime.now(), json.dumps(meta_copy), str(unique_id)))
            
            if cursor.rowcount == 0:
                # Orphaned metadata (no mapping)? Insert it anyway.
                conn.execute('''
                    INSERT INTO items (unique_id, status, date_added, last_updated, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (str(unique_id), status, date_added, datetime.datetime.now(), json.dumps(meta_copy)))

            # Step C: Migrate History
            for h in history:
                ts = h.get('ts')
                action = h.get('action')
                details = h.get('details')
                if ts and action:
                    conn.execute('''
                        INSERT INTO history (unique_id, timestamp, action, details)
                        VALUES (?, ?, ?, ?)
                    ''', (str(unique_id), ts, action, details))
            
            total_migrated += 1
            
        conn.commit()
        print(f"Migration Success: Processed {len(items_map)} IDs and {total_migrated} metadata records.")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration Error: {e}")
    finally:
        conn.close()