import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        # Use DATABASE_URL from environment variable (Production & Development via .env)
        db_url = os.environ.get('DATABASE_URL')
        
        if db_url:
            # Ensure SSL mode is enabled for Neon/Vercel if not already in URL
            if 'sslmode' not in db_url and 'localhost' not in db_url:
                db_url += '?sslmode=require'
                
            conn = psycopg2.connect(db_url)
            return conn
        else:
            print("Error: DATABASE_URL environment variable is not set.")
            return None
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None
