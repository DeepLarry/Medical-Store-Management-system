import sys
import os

# Add the backend directory to the path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.database import get_db_connection

def check_columns():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'medicines'")
            columns = [row[0] for row in cur.fetchall()]
            print("Columns in medicines table:", columns)
        except Exception as e:
            print(f"Error checking schema: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    check_columns()