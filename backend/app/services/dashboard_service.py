from app.database import get_db_connection

class DashboardService:
    def get_dashboard_metrics(self):
        conn = get_db_connection()
        if not conn:
            return None
        
        # Retrieve store_id from session (using Flask global object 'g' or 'session')
        from flask import session
        store_id = session.get('store_id')
        params = (store_id,) if store_id else ()
        
        try:
            cur = conn.cursor()
            
            # 1. Total Sales (Revenue)
            sql = "SELECT COALESCE(SUM(total_amount), 0) FROM invoices"
            if store_id: sql += " WHERE store_id = %s"
            cur.execute(sql, params)
            total_sales = float(cur.fetchone()[0])
            
            # 2. Total Medicines Count
            sql = "SELECT COUNT(*) FROM medicines"
            if store_id: sql += " WHERE store_id = %s"
            cur.execute(sql, params)
            total_medicines = int(cur.fetchone()[0])
            
            # 3. Net Profit Calculation
            sql = """
                SELECT COALESCE(SUM(s.quantity * m.purchase_price), 0)
                FROM sales s
                JOIN medicines m ON s.medicine_id = m.medicine_id
            """
            if store_id:
                sql += " WHERE s.store_id = %s"
                
            cur.execute(sql, params)
            total_cogs = float(cur.fetchone()[0])
            net_profit = total_sales - total_cogs
            
            # 4. Low Stock Count
            sql = "SELECT COUNT(*) FROM medicines WHERE stock < COALESCE(minimum_stock_level, 10)"
            if store_id: sql += " AND store_id = %s"
            cur.execute(sql, params)
            low_stock_count = int(cur.fetchone()[0])

            return {
                "total_sales": total_sales,
                "total_medicines": total_medicines,
                "net_profit": net_profit,
                "low_stock_count": low_stock_count
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error fetching dashboard metrics: {e}")
            return {"error": str(e)}
        finally:
            conn.close()

    def get_low_stock_alerts(self, limit=5):
        """Fetch medicines with stock below minimum level"""
        conn = get_db_connection()
        if not conn:
            return []
            
        from flask import session
        store_id = session.get('store_id')

        try:
            cur = conn.cursor()
            query = """
                SELECT 
                    m.medicine_name, 
                    m.stock, 
                    COALESCE(m.minimum_stock_level, 10) as min_stock,
                    COALESCE(s.supplier_name, 'Unknown') as supplier_name,
                    TO_CHAR(m.expiry_date, 'YYYY-MM-DD') as expiry_date
                FROM medicines m
                LEFT JOIN suppliers s ON m.supplier_id = s.supplier_id
                WHERE m.stock < COALESCE(m.minimum_stock_level, 10)
            """
            q_params = []
            if store_id:
                query += " AND m.store_id = %s"
                q_params.append(store_id)
            
            query += " ORDER BY m.stock ASC LIMIT %s"
            q_params.append(limit)
            
            cur.execute(query, tuple(q_params))
            cols = ['medicine_name', 'current_stock', 'min_stock', 'supplier', 'expiry_date']
            results = [dict(zip(cols, row)) for row in cur.fetchall()]
            return results
        except Exception as e:
            print(f"Error fetching low stock alerts: {e}")
            return []
        finally:
            conn.close()

    def get_expiry_alerts(self, limit=5):
        """Fetch medicines expiring in 30 days or already expired"""
        conn = get_db_connection()
        if not conn:
            return []

        from flask import session
        store_id = session.get('store_id')

        try:
            cur = conn.cursor()
            # We fetch anything expired OR expiring in next 30 days
            query = """
                SELECT 
                    medicine_name,
                    batch_number,
                    TO_CHAR(expiry_date, 'YYYY-MM-DD') as expiry_date,
                    stock,
                    CASE 
                        WHEN expiry_date < CURRENT_DATE THEN 'Expired'
                        WHEN expiry_date <= CURRENT_DATE + INTERVAL '15 days' THEN 'Expiring soon (15d)'
                        ELSE 'Expiring in 30d'
                    END as status
                FROM medicines
                WHERE expiry_date <= CURRENT_DATE + INTERVAL '30 days'
            """
            q_params = []
            if store_id:
                query += " AND store_id = %s"
                q_params.append(store_id)
            
            query += " ORDER BY expiry_date ASC LIMIT %s"
            q_params.append(limit)
            
            cur.execute(query, tuple(q_params))
            cols = ['medicine_name', 'batch_number', 'expiry_date', 'stock', 'status']
            results = [dict(zip(cols, row)) for row in cur.fetchall()]
            return results
        except Exception as e:
            print(f"Error fetching expiry alerts: {e}")
            return []
        finally:
            conn.close()

    def get_top_selling_medicines(self, limit=10):
        """Fetch top selling medicines by quantity"""
        conn = get_db_connection()
        if not conn:
            return []

        from flask import session
        store_id = session.get('store_id')

        try:
            cur = conn.cursor()
            query = """
                SELECT 
                    m.medicine_name, 
                    SUM(s.quantity) as total_quantity, 
                    SUM(s.quantity * COALESCE(s.price_per_unit, m.price)) as total_revenue
                FROM sales s
                JOIN medicines m ON s.medicine_id = m.medicine_id
            """
            q_params = []
            if store_id:
                query += " WHERE s.store_id = %s"
                q_params.append(store_id)
            
            query += " GROUP BY m.medicine_name ORDER BY total_quantity DESC LIMIT %s"
            q_params.append(limit)
            
            cur.execute(query, tuple(q_params))
            cols = ['medicine_name', 'quantity', 'revenue']
            results = [dict(zip(cols, row)) for row in cur.fetchall()]
            
            # Format for Chart.js (labels, data)
            return {
                "labels": [item['medicine_name'] for item in results],
                "quantities": [int(item['quantity']) for item in results],
                "revenues": [float(item['revenue']) for item in results],
                "raw": results # Keep raw data for table if needed
            }
        except Exception as e:
            print(f"Error fetching top selling medicines: {e}")
            return {"labels": [], "quantities": [], "revenues": [], "raw": []}
        finally:
            conn.close()

    def get_supplier_insights(self):
        """Fetch supplier performance metrics"""
        conn = get_db_connection()
        if not conn:
            return []
        
        from flask import session
        store_id = session.get('store_id')

        try:
            cur = conn.cursor()
            query = """
                SELECT 
                    s.supplier_name, 
                    COUNT(p.purchase_id) as total_orders, 
                    SUM(COALESCE(p.total_cost, 0)) as total_purchase_value,
                    SUM(CASE WHEN p.payment_status = 'Pending' THEN COALESCE(p.total_cost, 0) ELSE 0 END) as pending_amount
                FROM suppliers s
                LEFT JOIN purchases p ON s.supplier_id = p.supplier_id
            """
            q_params = []
            if store_id:
                query += " WHERE s.store_id = %s"
                q_params.append(store_id)
            
            query += """
                GROUP BY s.supplier_name
                HAVING COUNT(p.purchase_id) > 0
                ORDER BY total_purchase_value DESC
                LIMIT 5
            """
            cur.execute(query, tuple(q_params))
            cols = ['supplier_name', 'total_orders', 'total_purchase_value', 'pending_amount']
            results = [dict(zip(cols, row)) for row in cur.fetchall()]
            return results
        except Exception as e:
            print(f"Error fetching supplier insights: {e}")
            return []
        finally:
            conn.close()

    def get_monthly_analytics(self):
        """Fetch monthly revenue and profit for last 12 months"""
        conn = get_db_connection()
        if not conn:
            return []
        
        from flask import session
        store_id = session.get('store_id')

        try:
            cur = conn.cursor()
            
            # We must inject store_id into BOTH CTEs if possible, or filter logic carefully.
            # 1. invoices -> store_id
            # 2. sales -> store_id
            
            q_params = []
            
            sql_inv = "WHERE sale_date >= CURRENT_DATE - INTERVAL '11 months'"
            if store_id:
                sql_inv += " AND store_id = %s"
                q_params.append(store_id)
            
            sql_sales = "WHERE s.sale_date >= CURRENT_DATE - INTERVAL '11 months'"
            if store_id:
                sql_sales += " AND s.store_id = %s"
                q_params.append(store_id)

            query = f"""
                WITH monthly_revenue AS (
                    SELECT 
                        TO_CHAR(sale_date, 'Mon-YY') as month_label,
                        TO_CHAR(sale_date, 'YYYY-MM') as sort_key,
                        SUM(total_amount) as revenue
                    FROM invoices
                    {sql_inv}
                    GROUP BY month_label, sort_key
                ),
                monthly_cost AS (
                    SELECT 
                        TO_CHAR(s.sale_date, 'YYYY-MM') as sort_key,
                        SUM(s.quantity * m.purchase_price) as cogs
                    FROM sales s
                    JOIN medicines m ON s.medicine_id = m.medicine_id
                    {sql_sales}
                    GROUP BY sort_key
                )
                SELECT 
                    r.month_label,
                    r.revenue,
                    (r.revenue - COALESCE(c.cogs, 0)) as profit
                FROM monthly_revenue r
                LEFT JOIN monthly_cost c ON r.sort_key = c.sort_key
                ORDER BY r.sort_key ASC;
            """
            
            cur.execute(query, tuple(q_params))
            cols = ['month', 'revenue', 'profit']
            results = [dict(zip(cols, row)) for row in cur.fetchall()]
            
            return {
                "labels": [row['month'] for row in results],
                "revenue": [float(row['revenue']) for row in results],
                "profit": [float(row['profit']) for row in results]
            }
        except Exception as e:
            print(f"Error fetching monthly analytics: {e}")
            return {"labels": [], "revenue": [], "profit": []}
        finally:
            conn.close()

    def get_sales_chart_data(self, days=7):
        """Fetch daily sales for the last 'days' days"""
        conn = get_db_connection()
        if not conn:
            return []
        
        from flask import session
        store_id = session.get('store_id')
        
        try:
            cur = conn.cursor()
            sql = """
                SELECT TO_CHAR(sale_date, 'YYYY-MM-DD') as day, SUM(total_amount)
                FROM invoices
                WHERE sale_date >= CURRENT_DATE - (%s || ' days')::INTERVAL
            """
            params = [str(days)]
            
            if store_id:
                sql += " AND store_id = %s"
                params.append(store_id)
                
            sql += " GROUP BY day ORDER BY day ASC"
            
            cur.execute(sql, tuple(params))
            
            results = cur.fetchall()
            return [{"date": row[0], "amount": float(row[1])} for row in results]
        except Exception as e:
            print(f"Error fetching chart data: {e}")
            return []
        finally:
            conn.close()
