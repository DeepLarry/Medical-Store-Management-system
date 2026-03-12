from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from app.database import get_db_connection

dashboard_bp = Blueprint('dashboard', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
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

# --- API Endpoints for Dashboard ---

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
                   SUM(s.quantity * m.price) as sales
            FROM sales s
            JOIN medicines m ON s.medicine_id = m.medicine_id
            GROUP BY month
            ORDER BY month
            LIMIT 12
        """)
        rows = cur.fetchall()
        data = [{"month": row[0], "sales": float(row[1])} for row in rows]
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
