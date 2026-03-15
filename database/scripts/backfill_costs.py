import sys
import os

# Add the backend directory to the path 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.database import get_db_connection

def prevent_zero_costs():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            print("Backfilling purchase costs...")
            cur.execute("""
                UPDATE purchases p
                SET total_cost = p.quantity * COALESCE(m.purchase_price, 0)
                FROM medicines m
                WHERE p.medicine_id = m.medicine_id AND p.total_cost = 0;
            """)
            conn.commit()
            print("Successfully backfilled purchase costs.")
        except Exception as e:
            conn.rollback()
            print(f"Error backfilling: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    prevent_zero_costs()