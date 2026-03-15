from app.database import get_db_connection

class SearchService:
    def global_search(self, query_str):
        """
        Search across Medicines, Invoices, Customers, and Suppliers.
        Returns categorized results.
        """
        if not query_str or len(query_str.strip()) < 2:
            return {}

        search_term = f"%{query_str.strip()}%"
        conn = get_db_connection()
        if not conn:
            return {}
        
        results = {
            "medicines": [],
            "invoices": [],
            "customers": [],
            "suppliers": []
        }

        try:
            cur = conn.cursor()

            # 1. Search Medicines
            # Matches name, barcode, or category
            cur.execute("""
                SELECT medicine_id, medicine_name, category, stock, price
                FROM medicines
                WHERE medicine_name ILIKE %s 
                   OR barcode ILIKE %s 
                   OR category ILIKE %s
                LIMIT 5
            """, (search_term, search_term, search_term))
            
            med_cols = ['id', 'title', 'subtitle', 'stock', 'price']
            # Mapping columns to a generic UI structure can be helpful, 
            # but let's stick to domain data for now.
            for row in cur.fetchall():
                results["medicines"].append({
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "stock": row[3],
                    "price": float(row[4])
                })

            # 2. Search Invoices
            # Matches Invoice ID or Customer Name
            cur.execute("""
                SELECT i.invoice_id, c.customer_name, i.total_amount, TO_CHAR(i.sale_date, 'YYYY-MM-DD')
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.customer_id
                WHERE CAST(i.invoice_id AS TEXT) ILIKE %s 
                   OR c.customer_name ILIKE %s
                ORDER BY i.sale_date DESC
                LIMIT 5
            """, (search_term, search_term))
            
            for row in cur.fetchall():
                results["invoices"].append({
                    "id": row[0],
                    "customer": row[1] or "Walk-in",
                    "amount": float(row[2]),
                    "date": row[3]
                })

            # 3. Search Customers
            # Matches Name or Phone
            cur.execute("""
                SELECT customer_id, customer_name, phone, city
                FROM customers
                WHERE customer_name ILIKE %s 
                   OR phone ILIKE %s
                LIMIT 5
            """, (search_term, search_term))
            
            for row in cur.fetchall():
                results["customers"].append({
                    "id": row[0],
                    "name": row[1],
                    "phone": row[2],
                    "city": row[3]
                })

            # 4. Search Suppliers
            # Matches Name or Phone
            cur.execute("""
                SELECT supplier_id, supplier_name, phone, city
                FROM suppliers
                WHERE supplier_name ILIKE %s 
                   OR phone ILIKE %s
                LIMIT 5
            """, (search_term, search_term))
            
            for row in cur.fetchall():
                results["suppliers"].append({
                    "id": row[0],
                    "name": row[1],
                    "phone": row[2],
                    "city": row[3]
                })

            return results

        except Exception as e:
            print(f"Global search error: {e}")
            return {}
        finally:
            conn.close()
