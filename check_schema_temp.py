import psycopg2

def check_schema():
    try:
        conn = psycopg2.connect(
            dbname="medical_store_db",
            user="postgres",
            password="@#1234Deep",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()
        
        tables = ['sales', 'invoices', 'medicines', 'customers']
        for table in tables:
            print(f"\n--- Columns in {table} ---")
            cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            rows = cur.fetchall()
            for row in rows:
                print(f"{row[0]}: {row[1]}")
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()