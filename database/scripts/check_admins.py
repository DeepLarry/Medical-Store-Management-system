import sys
import os

# Add the backend directory to the path 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.database import get_db_connection

def check_admins_table():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'admins'
            """)
            columns = cur.fetchall()
            print("Admins Table Columns:")
            for col in columns:
                print(f"- {col[0]} ({col[1]})")
                
        except Exception as e:
            print(f"Error checking schema: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    check_admins_table()