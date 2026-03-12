from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from app.database import get_db_connection

customers_bp = Blueprint('customers', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@customers_bp.route("/customers_page")
@login_required
def customers_page():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers ORDER BY customer_id DESC")
    cols = [desc[0] for desc in cur.description]
    customers = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return render_template("customers.html", customers=customers)

@customers_bp.route("/add_customer", methods=['POST'])
@login_required
def add_customer():
    name = request.form['name']
    phone = request.form['phone']
    city = request.form['city']
    
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO customers (customer_name, phone, city) VALUES (%s, %s, %s)", (name, phone, city))
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
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM customers WHERE customer_id = %s", (id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()
