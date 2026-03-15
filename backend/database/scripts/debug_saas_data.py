import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app.database import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

print("--- Stores ---")
try:
    cur.execute("SELECT * FROM stores")
    stores = cur.fetchall()
    print(stores)
except Exception as e:
    print(f"Error fetching stores: {e}")

print("\n--- Admins ---")
try:
    cur.execute("SELECT id, username, role, store_id FROM admins")
    admins = cur.fetchall()
    print(admins)
except Exception as e:
    print(f"Error fetching admins: {e}")

conn.close()