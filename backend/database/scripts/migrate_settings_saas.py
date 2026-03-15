import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app.database import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

try:
    print("Checking store_settings schema...")
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'store_settings' AND column_name = 'store_id'")
    if not cur.fetchone():
        print("Adding store_id to store_settings...")
        cur.execute("ALTER TABLE store_settings ADD COLUMN store_id INTEGER")
        cur.execute("ALTER TABLE store_settings ADD CONSTRAINT fk_store_settings_store FOREIGN KEY (store_id) REFERENCES stores(store_id)")
        
        # Link existing settings to Default Store (ID 1)
        cur.execute("UPDATE store_settings SET store_id = 1 WHERE store_id IS NULL")
        
        # Make store_id NOT NULL if we want strictly one per store (optional but good practice)
        # However, we only have one row now.
        
        # Also ensure store_settings is unique per store
        cur.execute("ALTER TABLE store_settings ADD CONSTRAINT unique_store_settings UNIQUE (store_id)")
        
        conn.commit()
        print("Migration successful.")
    else:
        print("store_settings already has store_id.")
        
except Exception as e:
    conn.rollback()
    print(f"Error during migration: {e}")
finally:
    cur.close()
    conn.close()