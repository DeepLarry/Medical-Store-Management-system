import sys
import os

# Add the 'backend' folder to sys.path so we can import 'app.database'
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
if backend_path not in sys.path:
    sys.path.append(backend_path)

from app.database import get_db_connection

def test_metrics(store_id=None):
    print(f"\n--- Testing Metrics for Store ID: {store_id} ---")
    conn = get_db_connection()
    if not conn:
        print("DB Connection failed")
        return

    params = (store_id,) if store_id else ()
    cur = conn.cursor()

    try:
        # 1. Total Sales
        print("1. Total Sales...")
        sql = "SELECT COALESCE(SUM(total_amount), 0) FROM invoices"
        if store_id: sql += " WHERE store_id = %s"
        # cur.mogrify returns bytes, so decode to print
        full_sql = cur.mogrify(sql, params).decode('utf-8')
        print(f"   Executing: {full_sql}")
        cur.execute(sql, params)
        res = cur.fetchone()
        print(f"   Result: {res}")
        if res and res[0] is not None:
             total_sales = float(res[0])
        else:
             total_sales = 0.0
        print(f"   Total Sales: {total_sales}")

        # 2. Total Medicines
        print("2. Total Medicines...")
        sql = "SELECT COUNT(*) FROM medicines"
        if store_id: sql += " WHERE store_id = %s"
        full_sql = cur.mogrify(sql, params).decode('utf-8')
        print(f"   Executing: {full_sql}")
        cur.execute(sql, params)
        res = cur.fetchone()
        if res:
             total_medicines = int(res[0])
        else:
             total_medicines = 0
        print(f"   Total Medicines: {total_medicines}")

        # 3. Net Profit
        print("3. Net Profit...")
        sql = """
            SELECT COALESCE(SUM(s.quantity * m.purchase_price), 0)
            FROM sales s
            JOIN medicines m ON s.medicine_id = m.medicine_id
        """
        if store_id:
            sql += " WHERE s.store_id = %s"
        
        full_sql = cur.mogrify(sql, params).decode('utf-8')
        print(f"   Executing: {full_sql}")
        cur.execute(sql, params)
        res = cur.fetchone()
        print(f"   Result: {res}")
        if res and res[0] is not None:
            cogs = float(res[0])
        else:
            cogs = 0.0
        
        net_profit = total_sales - cogs
        print(f"   Net Profit: {net_profit}")

        # 4. Low Stock
        print("4. Low Stock...")
        sql = "SELECT COUNT(*) FROM medicines WHERE stock < COALESCE(minimum_stock_level, 10)"
        if store_id: sql += " AND store_id = %s"
        full_sql = cur.mogrify(sql, params).decode('utf-8')
        print(f"   Executing: {full_sql}")
        cur.execute(sql, params)
        res = cur.fetchone()
        print(f"   Result: {res}")

    except Exception as e:
        print(f"!!! ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    # Test with store_id=1 (assuming user is store 1)
    test_metrics(1)
