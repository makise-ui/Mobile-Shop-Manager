import sqlite3
import json
import datetime
from pathlib import Path
from .config import CONFIG_DIR

DB_FILE = CONFIG_DIR / "inventory.db"

class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path else DB_FILE
        self._init_db()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # Access columns by name
        return conn

    def get_connection(self):
        return self.connect()

    def _init_db(self):
        """Initialize the database schema."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # 1. Items Table (The Registry)
        # Stores the persistent identity and metadata of every item
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                unique_id TEXT PRIMARY KEY,
                imei TEXT,
                hash_key TEXT,
                model TEXT,
                status TEXT,
                date_added TIMESTAMP,
                last_updated TIMESTAMP,
                is_hidden INTEGER DEFAULT 0,
                merged_into TEXT,
                metadata TEXT  -- JSON blob for flexible extra fields (color, notes, buyer, etc)
            )
        ''')
        
        # 2. History Table (Structured Logs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unique_id TEXT,
                timestamp TIMESTAMP,
                action TEXT,
                details TEXT,
                FOREIGN KEY(unique_id) REFERENCES items(unique_id)
            )
        ''')
        
        # Indexes for speed
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_imei ON items(imei)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash ON items(hash_key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_uid ON history(unique_id)')
        
        conn.commit()
        conn.close()

    def upsert_item(self, unique_id, imei=None, model=None, status=None, date_added=None):
        """Insert or Update a core item record."""
        conn = self.connect()
        cursor = conn.cursor()
        
        now = datetime.datetime.now()
        
        # Check if exists
        cursor.execute("SELECT unique_id, metadata FROM items WHERE unique_id = ?", (str(unique_id),))
        row = cursor.fetchone()
        
        if row:
            # Update
            fields = []
            values = []
            if imei: 
                fields.append("imei = ?")
                values.append(imei)
            if model: 
                fields.append("model = ?")
                values.append(model)
            if status: 
                fields.append("status = ?")
                values.append(status)
            
            fields.append("last_updated = ?")
            values.append(now)
            
            values.append(str(unique_id))
            
            sql = f"UPDATE items SET {', '.join(fields)} WHERE unique_id = ?"
            cursor.execute(sql, values)
        else:
            # Insert
            cursor.execute('''
                INSERT INTO items (unique_id, imei, model, status, date_added, last_updated, metadata)
                VALUES (?, ?, ?, ?, ?, ?, '{}')
            ''', (str(unique_id), imei, model, status, date_added or now, now))
            
        conn.commit()
        conn.close()

    def update_metadata(self, unique_id, meta_dict):
        """Updates the JSON metadata column."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT metadata FROM items WHERE unique_id = ?", (str(unique_id),))
        row = cursor.fetchone()
        
        current_meta = {}
        if row and row['metadata']:
            try:
                current_meta = json.loads(row['metadata'])
            except: pass
            
        # Merge
        current_meta.update(meta_dict)
        
        cursor.execute("UPDATE items SET metadata = ?, last_updated = ? WHERE unique_id = ?", 
                       (json.dumps(current_meta), datetime.datetime.now(), str(unique_id)))
        
        conn.commit()
        conn.close()

    def add_history(self, unique_id, action, details, timestamp=None):
        """Add a structured history log."""
        conn = self.connect()
        cursor = conn.cursor()
        
        if not timestamp:
            timestamp = datetime.datetime.now()
            
        cursor.execute('''
            INSERT INTO history (unique_id, timestamp, action, details)
            VALUES (?, ?, ?, ?)
        ''', (str(unique_id), timestamp, action, details))
        
        conn.commit()
        conn.close()

    def get_item_data(self, unique_id):
        """Get full item data including metadata."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM items WHERE unique_id = ?", (str(unique_id),))
        row = cursor.fetchone()
        conn.close()
        
        if not row: return {}
        
        data = dict(row)
        # Expand metadata
        if data.get('metadata'):
            try:
                meta = json.loads(data['metadata'])
                data.update(meta) # Flatten metadata into main dict
            except: pass
        return data

    def get_history(self, unique_id):
        """Get list of history events."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT timestamp as ts, action, details FROM history WHERE unique_id = ? ORDER BY timestamp DESC", (str(unique_id),))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(r) for r in rows]
