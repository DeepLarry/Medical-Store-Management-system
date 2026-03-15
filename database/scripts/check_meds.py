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
        
        print("--- MEDICINES TABLE ---")
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'medicines'")
        print([row[0] for row in cur.fetchall()])
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()