import sys
import os

# Add the backend directory to the path 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.database import get_db_connection

def prepare_saas_schema():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # 1. Create Stores Table (to manage tenants)
            print("Creating 'stores' table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stores (
                    store_id SERIAL PRIMARY KEY,
                    store_name VARCHAR(100) NOT NULL,
                    domain VARCHAR(100) UNIQUE, -- for subdomain tenancy
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                );
            """)

            # 2. Add 'role' and 'store_id' to Admins (Users)
            print("Updating 'admins' table for RBAC and Tenancy...")
            cur.execute("""
                ALTER TABLE admins 
                ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'admin', -- admin, manager, cashier
                ADD COLUMN IF NOT EXISTS store_id INTEGER REFERENCES stores(store_id);
            """)

            # Initialize a default store if none exists
            cur.execute("SELECT COUNT(*) FROM stores")
            if cur.fetchone()[0] == 0:
                print("Initializing default store...")
                cur.execute("INSERT INTO stores (store_name) VALUES ('Default Store') RETURNING store_id")
                default_store_id = cur.fetchone()[0]
                
                # Assign existing admin users to this default store
                cur.execute("UPDATE admins SET store_id = %s WHERE store_id IS NULL", (default_store_id,))
                
                # Only for this migration: assign ALL existing data to this store to prevent data loss
                data_tables = ['medicines', 'sales', 'purchases', 'customers', 'suppliers', 'invoices', 'notifications']
                for table in data_tables:
                    print(f"Adding store_id to {table}...")
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS store_id INTEGER REFERENCES stores(store_id);")
                    cur.execute(f"UPDATE {table} SET store_id = %s WHERE store_id IS NULL", (default_store_id,))

            conn.commit()
            print("SaaS Schema Preparation Complete.")

        except Exception as e:
            conn.rollback()
            print(f"Error preparing schema: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    prepare_saas_schema()