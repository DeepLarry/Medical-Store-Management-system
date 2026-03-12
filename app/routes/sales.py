from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from app.database import get_db_connection

sales_bp = Blueprint('sales', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@sales_bp.route("/sales")
@login_required
def sales_page():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get Medicines for dropdown
    cur.execute("SELECT medicine_id, medicine_name, price, stock FROM medicines WHERE stock > 0 ORDER BY medicine_name")
    cols_med = [desc[0] for desc in cur.description]
    medicines = [dict(zip(cols_med, row)) for row in cur.fetchall()]
    
    # Get Recent Sales History
    cur.execute("""
        SELECT s.sale_id, m.medicine_name, s.quantity, s.sale_date,
               (s.quantity * m.price) as total_price
        FROM sales s
        JOIN medicines m ON s.medicine_id = m.medicine_id
        ORDER BY s.sale_date DESC LIMIT 10
    """)
    cols_sale = ['sale_id', 'medicine_name', 'quantity', 'sale_date', 'total_price']
    history = [dict(zip(cols_sale, row)) for row in cur.fetchall()]
    
    conn.close()
    return render_template("sales.html", medicines=medicines, sales_history=history)

@sales_bp.route("/create_sale", methods=['POST'])
@login_required
def create_sale():
    medicine_id = request.form['medicine_id']
    quantity = int(request.form['quantity'])
    customer_name = request.form.get('customer_name')
    
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # 1. Handle Customer
        customer_id = None
        if customer_name:
            # Check if customer exists
            cur.execute("SELECT customer_id FROM customers WHERE customer_name = %s", (customer_name,))
            res = cur.fetchone()
            if res:
                customer_id = res[0]
            else:
                # Create new customer (simplified, phone/city empty)
                cur.execute("INSERT INTO customers (customer_name, phone, city) VALUES (%s, '', '') RETURNING customer_id", (customer_name,))
                customer_id = cur.fetchone()[0]

        # 2. Check stock
        cur.execute("SELECT stock FROM medicines WHERE medicine_id = %s", (medicine_id,))
        res = cur.fetchone()
        if not res:
            flash("Medicine not found", "danger")
            return redirect(url_for('sales.sales_page'))
            
        current_stock = res[0]
        
        if current_stock >= quantity:
            # 3. Reduce Stock
            cur.execute("UPDATE medicines SET stock = stock - %s WHERE medicine_id = %s", (quantity, medicine_id))
            
            # 4. Record Sale
            cur.execute("""
                INSERT INTO sales (medicine_id, quantity, sale_date, customer_id)
                VALUES (%s, %s, CURRENT_DATE, %s)
            """, (medicine_id, quantity, customer_id))
            
            conn.commit()
            flash('Sale recorded successfully', 'success')
        else:
            flash(f'Insufficient stock! Available: {current_stock}', 'danger')
            
    except Exception as e:
        conn.rollback()
        print(e)
        flash(f'Error processing sale: {e}', 'danger')
    finally:
        conn.close()
        
    return redirect(url_for('sales.sales_page'))
