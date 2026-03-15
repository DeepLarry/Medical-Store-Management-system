import sys
import os

# Add the backend directory to the path 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.database import get_db_connection

def update_purchases_table():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Check for total_cost column
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='purchases' AND column_name='total_cost'
            """)
            if not cur.fetchone():
                print("Adding 'total_cost' column...")
                cur.execute("ALTER TABLE purchases ADD COLUMN total_cost NUMERIC(10, 2) DEFAULT 0.00;")
            
            # Check for payment_status column
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='purchases' AND column_name='payment_status'
            """)
            if not cur.fetchone():
                print("Adding 'payment_status' column...")
                cur.execute("ALTER TABLE purchases ADD COLUMN payment_status VARCHAR(20) DEFAULT 'Paid';")
            
            conn.commit()
            print("Purchases table updated successfully.")
        except Exception as e:
            conn.rollback()
            print(f"Error updating database: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    update_purchases_table()