import psycopg2
from flask import g

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="medical_store_db",
            user="postgres",
            password="@#1234Deep",
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None
