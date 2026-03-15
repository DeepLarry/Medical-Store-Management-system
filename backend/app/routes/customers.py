from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from app.database import get_db_connection

customers_bp = Blueprint('customers', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        if 'store_id' not in session:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT store_id, role FROM admins WHERE id = %s", (session['user_id'],))
            res = cur.fetchone()
            conn.close()
            if res:
                session['store_id'] = res[0]
                session['role'] = res[1]

        return f(*args, **kwargs)
    return decorated_function

@customers_bp.route("/customers_page")
@login_required
def customers_page():
    store_id = session.get('store_id')
    conn = get_db_connection()
    cur = conn.cursor()
    if store_id:
        cur.execute("SELECT * FROM customers WHERE store_id = %s ORDER BY customer_id DESC", (store_id,))
    else:
        cur.execute("SELECT * FROM customers WHERE 1=0")
        
    cols = [desc[0] for desc in cur.description]
    customers = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return render_template("customers.html", customers=customers)

@customers_bp.route("/add_customer", methods=['POST'])
@login_required
def add_customer():
    store_id = session.get('store_id')
    if not store_id:
        flash("Invalid Store Context", "danger")
        return redirect(url_for('customers.customers_page'))

    name = request.form['name']
    phone = request.form['phone']
    city = request.form['city']
    
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO customers (customer_name, phone, city, store_id) VALUES (%s, %s, %s, %s)", (name, phone, city, store_id))
        conn.commit()
        flash('Customer added successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(str(e), 'danger')
    finally:
        conn.close()
    return redirect(url_for('customers.customers_page'))

@customers_bp.route("/delete_customer/<int:id>", methods=['DELETE'])
@login_required
def delete_customer(id):
    store_id = session.get('store_id')
    if not store_id: return jsonify({'success': False, 'error': 'No Store Context'})

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM customers WHERE customer_id = %s AND store_id = %s", (id, store_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@customers_bp.route("/customer_orders/<int:id>")
@login_required
def get_customer_orders(id):
    store_id = session.get('store_id')
    if not store_id: return jsonify({'success': False, 'error': 'No Store Context'})

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Fetch last 10 invoices for this customer
        query = """
            SELECT i.invoice_id, i.sale_date, i.total_amount, i.payment_mode,
                   (SELECT COUNT(*) FROM sales s WHERE s.invoice_id = i.invoice_id) as item_count
            FROM invoices i
            WHERE i.customer_id = %s AND i.store_id = %s
            ORDER BY i.sale_date DESC
            LIMIT 10
        """
        cur.execute(query, (id, store_id))
        cols = [desc[0] for desc in cur.description]
        orders = [dict(zip(cols, row)) for row in cur.fetchall()]
        
        # Format date for JSON
        for order in orders:
            if order['sale_date']:
                order['sale_date'] = order['sale_date'].strftime('%Y-%m-%d %H:%M')
                
        return jsonify({'success': True, 'orders': orders})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()
