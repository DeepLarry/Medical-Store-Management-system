import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app.database import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

print("--- Store Settings ---")
try:
    cur.execute("SELECT * FROM store_settings")
    settings = cur.fetchall()
    print(settings)
except Exception as e:
    print(f"Error fetching store_settings: {e}")

conn.close()