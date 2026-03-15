import sys
import os

# Add the backend directory to the path 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.database import get_db_connection

def add_batch_number_column():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Check if batch_number exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='medicines' AND column_name='batch_number'
            """)
            if not cur.fetchone():
                print("Adding 'batch_number' column...")
                cur.execute("""
                    ALTER TABLE medicines 
                    ADD COLUMN batch_number VARCHAR(50) DEFAULT 'BATCH-001';
                """)
                conn.commit()
                print("Successfully added 'batch_number' column.")
            else:
                print("'batch_number' column already exists.")
                
        except Exception as e:
            conn.rollback()
            print(f"Error updating database: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    add_batch_number_column()