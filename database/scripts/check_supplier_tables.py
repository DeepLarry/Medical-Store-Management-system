import sys
import os

# Add the backend directory to the path 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.database import get_db_connection

def check_tables():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cur.fetchall()]
            print("Tables:", tables)
            
            for table in tables:
                if 'supplier' in table or 'purchase' in table or 'payment' in table:
                     cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
                     columns = [row[0] for row in cur.fetchall()]
                     print(f"Columns in {table}: {columns}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    check_tables()