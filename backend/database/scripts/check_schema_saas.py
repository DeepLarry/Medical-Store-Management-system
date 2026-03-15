import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app.database import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

tables = ['stores']
for t in tables:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (t,))
    cols = [row[0] for row in cur.fetchall()]
    print(f"Table {t} columns: {cols}")

conn.close()