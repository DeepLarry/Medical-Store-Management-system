import sys
import os

# Add the backend directory to the path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.database import get_db_connection

def add_columns():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Check if purchase_price exists, if not add it
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='medicines' AND column_name='purchase_price') THEN
                        ALTER TABLE medicines ADD COLUMN purchase_price NUMERIC(10, 2) DEFAULT 0.00;
                    END IF;
                END
                $$;
            """)
            
            conn.commit()
            print("Successfully added 'purchase_price' column to medicines table.")
        except Exception as e:
            conn.rollback()
            print(f"Error updating database: {e}")
        finally:
            conn.close()
    else:
        print("Failed to connect to the database.")

if __name__ == "__main__":
    add_columns()