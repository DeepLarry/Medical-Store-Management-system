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
        
        # Check sales table columns
        print("--- SALES TABLE ---")
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'sales'")
        for row in cur.fetchall():
            print(f"{row[0]}: {row[1]}")
            
        # Check if 'orders' or 'invoices' exist
        print("\n--- ALL TABLES ---")
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        for row in cur.fetchall():
            print(row[0])
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()