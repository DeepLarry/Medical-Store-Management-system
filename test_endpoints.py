import sys
import os
import json
from flask import session

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app import create_app
from app.database import get_db_connection

app = create_app()
app.config['TESTING'] = True
app.secret_key = 'test_secret'

def test_apis():
    print("\n=== Testing Dashboard APIs ===")
    
    with app.test_client() as client:
        # 1. Login to set session
        print("1. Logging in...")
        # We need a valid user. Let's find one.
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, store_id FROM admins LIMIT 1")
        user = cur.fetchone()
        conn.close()
        
        if not user:
            print("No admin user found to test with.")
            # Create a dummy user? For now assuming one exists as per context.
            return

        uid, username, store_id = user
        # 2. Simulate session
        with client.session_transaction() as sess:
            sess['user_id'] = uid
            sess['store_id'] = store_id
            sess['role'] = 'admin'
            print(f"   Session set: User ID {uid}, Store ID {store_id}")

        # 3. Test Stats API
        print("\n2. Testing /api/dashboard/stats")
        rv = client.get('/api/dashboard/stats')
        print(f"   Status: {rv.status_code}")
        print(f"   Data: {rv.data.decode('utf-8')}")

        # 4. Test Monthly Analytics (Chart)
        print("\n3. Testing /api/dashboard/analytics/monthly")
        rv = client.get('/api/dashboard/analytics/monthly')
        print(f"   Status: {rv.status_code}")
        print(f"   Data: {rv.data.decode('utf-8')}")
        
        # 5. Test Top Products (Graph)
        print("\n4. Testing /api/dashboard/top-products")
        rv = client.get('/api/dashboard/top-products')
        print(f"   Status: {rv.status_code}")
        try:
             # Just print first bit to avoid clutter
             print(f"   Data: {rv.data.decode('utf-8')[:200]}...")
        except:
             print(f"   Data: {rv.data}")

if __name__ == "__main__":
    test_apis()