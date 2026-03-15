import sys
import os

# Add the backend directory to the path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.database import get_db_connection

def add_discount_column():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Check if discount exists in invoices, if not add it
            cur.execute("""
                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='invoices') THEN
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                       WHERE table_name='invoices' AND column_name='discount') THEN
                            ALTER TABLE invoices ADD COLUMN discount NUMERIC(10, 2) DEFAULT 0.00;
                            RAISE NOTICE 'Added discount column to invoices table.';
                        ELSE
                            RAISE NOTICE 'discount column already exists in invoices table.';
                        END IF;
                    ELSE
                        RAISE NOTICE 'invoices table does not exist.';
                    END IF;
                END
                $$;
            """)
            
            conn.commit()
            print("Successfully checked/added 'discount' column to invoices table.")
        except Exception as e:
            conn.rollback()
            print(f"Error updating database: {e}")
        finally:
            conn.close()
    else:
        print("Failed to connect to the database.")

if __name__ == "__main__":
    add_discount_column()