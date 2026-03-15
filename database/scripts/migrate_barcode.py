import psycopg2

DB_CONFIG = {
    "dbname": "medical_store_db",
    "user": "postgres",
    "password": "@#1234Deep",
    "host": "localhost",
    "port": "5432"
}

def add_barcode_column():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Checking for 'barcode' column in 'medicines' table...")
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='medicines' AND column_name='barcode'")
        if not cur.fetchone():
            print("Adding 'barcode' column...")
            cur.execute("ALTER TABLE medicines ADD COLUMN barcode VARCHAR(100) UNIQUE;")
            conn.commit()
            print("Column added successfully.")
        else:
            print("'barcode' column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    add_barcode_column()