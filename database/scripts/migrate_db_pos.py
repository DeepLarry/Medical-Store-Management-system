import psycopg2
from datetime import datetime

DB_CONFIG = {
    "dbname": "medical_store_db",
    "user": "postgres",
    "password": "@#1234Deep",
    "host": "localhost",
    "port": "5432"
}

def migrate():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Create invoices table
        print("Creating 'invoices' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id SERIAL PRIMARY KEY,
                customer_id INT REFERENCES customers(customer_id),
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount DECIMAL(10, 2),
                payment_mode VARCHAR(50) DEFAULT 'Cash'
            );
        """)
        
        # 2. Add invoice_id and price_per_unit to sales table
        print("Altering 'sales' table...")
        
        # Check if invoice_id exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='sales' AND column_name='invoice_id'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE sales ADD COLUMN invoice_id INT REFERENCES invoices(invoice_id);")
            print(" - Added 'invoice_id' column")
        
        # Check if price_per_unit exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='sales' AND column_name='price_per_unit'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE sales ADD COLUMN price_per_unit DECIMAL(10, 2);")
            print(" - Added 'price_per_unit' column")

        conn.commit()
        print("Migration successful!")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()