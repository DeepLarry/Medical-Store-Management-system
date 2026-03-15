import sys
import os

# Add the backend directory to the path 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.database import get_db_connection

def add_min_stock_column():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Check if minimum_stock_level exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='medicines' AND column_name='minimum_stock_level'
            """)
            if not cur.fetchone():
                print("Adding 'minimum_stock_level' column...")
                cur.execute("""
                    ALTER TABLE medicines 
                    ADD COLUMN minimum_stock_level INTEGER DEFAULT 10;
                """)
                conn.commit()
                print("Successfully added 'minimum_stock_level' column.")
            else:
                print("'minimum_stock_level' column already exists.")
                
        except Exception as e:
            conn.rollback()
            print(f"Error updating database: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    add_min_stock_column()