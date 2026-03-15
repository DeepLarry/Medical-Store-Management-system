import sys
import os

# Add the backend directory to the path 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.database import get_db_connection

def create_notifications_table():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'notifications'
                );
            """)
            exists = cur.fetchone()[0]
            
            if not exists:
                print("Creating 'notifications' table...")
                cur.execute("""
                    CREATE TABLE notifications (
                        id SERIAL PRIMARY KEY,
                        message TEXT NOT NULL,
                        type VARCHAR(20) DEFAULT 'info', -- info, success, warning, danger
                        is_read BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
                print("Successfully created 'notifications' table.")
            else:
                print("'notifications' table already exists.")
                
        except Exception as e:
            conn.rollback()
            print(f"Error creating table: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    create_notifications_table()