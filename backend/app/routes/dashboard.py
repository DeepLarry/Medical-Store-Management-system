from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from app.database import get_db_connection
from app.services.dashboard_service import DashboardService

dashboard_bp = Blueprint('dashboard', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        # Self-healing session: Restore store_id if missing
        if 'store_id' not in session:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT store_id, role FROM admins WHERE id = %s", (session['user_id'],))
            user_data = cur.fetchone()
            conn.close()
            if user_data:
                session['store_id'] = user_data[0]
                session['role'] = user_data[1]

        return f(*args, **kwargs)
    return decorated_function

@dashboard_bp.route("/")
def home():
    if 'user_id' in session:
         return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@dashboard_bp.route("/sales_page") # Kept for compatibility if linked elsewhere
@login_required
def sales_page_redirect():
    return redirect(url_for('sales.sales_page'))

# --- API Endpoints ---

@dashboard_bp.route("/api/dashboard/stats")
@login_required
def dashboard_stats():
    service = DashboardService()
    try:
        metrics = service.get_dashboard_metrics()
        # If metrics has "error" key, return 500
        if 'error' in metrics:
            return jsonify({"error": metrics['error']}), 500
            
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route("/api/dashboard/alerts")
@login_required
def dashboard_alerts():
    service = DashboardService()
    try:
        limit = request.args.get('limit', 5, type=int)
        alerts = service.get_low_stock_alerts(limit)
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route("/api/dashboard/expiry")
@login_required
def dashboard_expiry():
    service = DashboardService()
    try:
        limit = request.args.get('limit', 5, type=int)
        alerts = service.get_expiry_alerts(limit)
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route("/api/dashboard/top-products")
@login_required
def dashboard_top_products():
    service = DashboardService()
    try:
        # Fetch top 10 products
        data = service.get_top_selling_medicines(limit=10)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route("/api/dashboard/suppliers")
@login_required
def dashboard_suppliers():
    service = DashboardService()
    try:
        data = service.get_supplier_insights()
        # Convert Decimals to float for JSON serialization
        for item in data:
            item['total_purchase_value'] = float(item['total_purchase_value'])
            item['pending_amount'] = float(item['pending_amount'])
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route("/api/dashboard/analytics/monthly")
@login_required
def dashboard_monthly_analytics():
    service = DashboardService()
    try:
        data = service.get_monthly_analytics()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Notification System Routes ---
from app.services.notification_service import NotificationService

@dashboard_bp.route("/api/notifications")
@login_required
def get_notifications():
    service = NotificationService()
    try:
        limit = request.args.get('limit', 10, type=int)
        unread = request.args.get('unread', 'true').lower() == 'true'
        notifs = service.get_notifications(unread_only=unread, limit=limit)
        return jsonify(notifs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route("/api/notifications/count")
@login_required
def get_unread_count():
    service = NotificationService()
    try:
        count = service.get_unread_count()
        return jsonify({"unread_count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route("/api/notifications/read", methods=['POST'])
@login_required
def mark_notification_read():
    service = NotificationService()
    data = request.json
    try:
        if data.get('all'):
            service.mark_all_read()
        else:
            service.mark_as_read(data.get('id'))
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Search System Routes ---
from app.services.search_service import SearchService

@dashboard_bp.route("/api/search")
@login_required
def global_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({})
    
    service = SearchService()
    try:
        results = service.global_search(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route("/api/dashboard/chart")
@login_required
def dashboard_chart():
    service = DashboardService()
    try:
        # Default to 7 days
        days = request.args.get('days', 7, type=int)
        data = service.get_sales_chart_data(days)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Legacy route for total_sales (optional: mark as deprecated or redirect)
@dashboard_bp.route("/total_sales")
@login_required
def total_sales_api():
    conn = get_db_connection()
    if not conn: return jsonify({"total_sales": 0})
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(s.quantity * m.price), 0)
            FROM sales s
            JOIN medicines m ON s.medicine_id = m.medicine_id
        """)
        result = cur.fetchone()
        val = float(result[0]) if result and result[0] else 0.0
        return jsonify({"total_sales": val})
    except: return jsonify({"total_sales": 0})
    finally: conn.close()

@dashboard_bp.route("/total_profit")
@login_required
def total_profit_api():
    conn = get_db_connection()
    if not conn: return jsonify({"total_profit": 0})
    try:
        cur = conn.cursor()
        # Profit = (Selling Price - Purchase Price) * Quantity
        cur.execute("""
            SELECT COALESCE(SUM(s.quantity * (m.price - m.purchase_price)), 0)
            FROM sales s
            JOIN medicines m ON s.medicine_id = m.medicine_id
        """)
        result = cur.fetchone()
        val = float(result[0]) if result and result[0] else 0.0
        return jsonify({"total_profit": val})
    except Exception as e:
        print(f"Error calculating profit: {e}")
        return jsonify({"total_profit": 0})
    finally: conn.close()

@dashboard_bp.route("/total_medicines_count")
@login_required
def total_medicines_count():
    conn = get_db_connection()
    if not conn: return jsonify({"count": 0})
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM medicines")
        result = cur.fetchone()
        val = int(result[0]) if result else 0
        return jsonify({"count": val})
    except: return jsonify({"count": 0})
    finally: conn.close()

@dashboard_bp.route("/low_stock_count")
@login_required
def low_stock_count():
    conn = get_db_connection()
    if not conn: return jsonify({"count": 0})
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM medicines WHERE stock < 20")
        result = cur.fetchone()
        val = int(result[0]) if result else 0
        return jsonify({"count": val})
    except: return jsonify({"count": 0})
    finally: conn.close()

@dashboard_bp.route("/top_medicines")
@login_required
def top_medicines():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.medicine_name, SUM(s.quantity) as total_sold
            FROM sales s
            JOIN medicines m ON s.medicine_id = m.medicine_id
            GROUP BY m.medicine_name
            ORDER BY total_sold DESC
            LIMIT 5
        """)
        rows = cur.fetchall()
        data = [{"medicine": row[0], "sold": int(row[1])} for row in rows]
        return jsonify(data)
    except: return jsonify([])
    finally: conn.close()

@dashboard_bp.route("/monthly_sales")
@login_required
def monthly_sales():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT TO_CHAR(sale_date, 'YYYY-MM') as month,
                   SUM(s.quantity * m.price) as sales,
                   SUM(s.quantity * (m.price - m.purchase_price)) as profit
            FROM sales s
            JOIN medicines m ON s.medicine_id = m.medicine_id
            GROUP BY month
            ORDER BY month
            LIMIT 12
        """)
        rows = cur.fetchall()
        data = [{"month": row[0], "sales": float(row[1]), "profit": float(row[2])} for row in rows]
        return jsonify(data)
    except: return jsonify([])
    finally: conn.close()

@dashboard_bp.route("/low_stock")
@login_required
def low_stock():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT medicine_name, stock
            FROM medicines
            WHERE stock < 20
            ORDER BY stock ASC
            LIMIT 10
        """)
        rows = cur.fetchall()
        data = [{"medicine": row[0], "stock": int(row[1])} for row in rows]
        return jsonify(data)
    except: return jsonify([])
    finally: conn.close()

@dashboard_bp.route("/expiry_medicines")
@login_required
def expiry_medicines():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT medicine_name, expiry_date
            FROM medicines
            WHERE expiry_date <= (CURRENT_DATE + INTERVAL '30 days')
            ORDER BY expiry_date ASC
            LIMIT 10
        """)
        rows = cur.fetchall()
        data = [{"medicine": row[0], "expiry": str(row[1])} for row in rows]
        return jsonify(data)
    except: return jsonify([])
    finally: conn.close()

@dashboard_bp.route("/live_activity")
@login_required
def live_activity():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.sale_id, m.medicine_name, s.quantity, (s.quantity * m.price) as total_price, s.sale_date
            FROM sales s
            JOIN medicines m ON s.medicine_id = m.medicine_id
            ORDER BY s.sale_id DESC
            LIMIT 5
        """)
        sales = cur.fetchall()
        
        activity_log = []
        for s in sales:
            activity_log.append({
                'id': s[0],
                'type': 'sale',
                'message': f"Sold {s[2]}x {s[1]}",
                'amount': float(s[3]),
                'time': str(s[4])
            })
            
        return jsonify(activity_log)
    except Exception as e:
        print(f"Error fetching live activity: {e}")
        return jsonify([])
    finally:
        conn.close()

