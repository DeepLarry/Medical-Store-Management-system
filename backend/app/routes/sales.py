from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from app.database import get_db_connection
from decimal import Decimal

sales_bp = Blueprint('sales', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        # Restore session context if user is logged in but session expired
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

@sales_bp.route("/store")
@login_required
def store_frontend():
    store_id = session.get('store_id')
    conn = get_db_connection()
    cur = conn.cursor()
    # Get Medicines optimizing for frontend speed
    if store_id:
        cur.execute("SELECT medicine_id, medicine_name, barcode, price, stock, category FROM medicines WHERE stock > 0 AND store_id = %s ORDER BY medicine_name", (store_id,))
    else:
        # Fallback for superadmin or no store context? Maybe return empty or all (risky)
        # For safety return nothing if no store context
        cur.execute("SELECT medicine_id, medicine_name, barcode, price, stock, category FROM medicines WHERE stock > 0 AND 1=0 ORDER BY medicine_name")
        
    cols = [desc[0] for desc in cur.description]
    medicines = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return render_template("store_frontend.html", medicines=medicines)

@sales_bp.route("/sales")
@login_required
def sales_page():
    store_id = session.get('store_id')
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get Medicines for dropdown
    if store_id:
        cur.execute("SELECT medicine_id, medicine_name, barcode, price, stock FROM medicines WHERE stock > 0 AND store_id = %s ORDER BY medicine_name", (store_id,))
    else:
        cur.execute("SELECT medicine_id, medicine_name, barcode, price, stock FROM medicines WHERE stock > 0 AND 1=0")

    cols_med = [desc[0] for desc in cur.description]
    medicines = [dict(zip(cols_med, row)) for row in cur.fetchall()]
    
    # Get Recent Sales History
    if store_id:
        cur.execute("""
            SELECT s.sale_id, m.medicine_name, s.quantity, s.sale_date,
                   (s.quantity * m.price) as total_price
            FROM sales s
            JOIN medicines m ON s.medicine_id = m.medicine_id
            WHERE s.store_id = %s
            ORDER BY s.sale_date DESC LIMIT 10
        """, (store_id,))
    else:
        cur.execute("""
            SELECT s.sale_id, m.medicine_name, s.quantity, s.sale_date,
                   (s.quantity * m.price) as total_price
            FROM sales s
            JOIN medicines m ON s.medicine_id = m.medicine_id
            WHERE 1=0
        """)

    cols_sale = ['sale_id', 'medicine_name', 'quantity', 'sale_date', 'total_price']
    history = [dict(zip(cols_sale, row)) for row in cur.fetchall()]
    
    conn.close()
    return render_template("sales.html", medicines=medicines, sales_history=history)


@sales_bp.route("/create_sale", methods=['POST'])
@login_required
def create_sale():
    store_id = session.get('store_id')
    if not store_id:
        return {"error": "Store context missing"}, 403

    data = request.json
    if not data:
        return {"error": "Invalid data"}, 400
        
    items = data.get('items', [])
    customer_name = data.get('customer_name', 'Walk-in Customer')
    customer_phone = data.get('customer_phone', '')
    payment_mode = data.get('payment_mode', 'Cash')
    try:
        # Convert discount to Decimal to match DB NUMERIC type
        val = data.get('discount', 0.0)
        discount_val = Decimal(str(val)) if val else Decimal('0.0')
    except (ValueError, TypeError):
        discount_val = Decimal('0.0')
    
    if not items:
        return {"error": "No items in cart"}, 400

    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # Schema compatibility patch for older/reset databases.
        # Some deployments have sales table without POS columns.
        cur.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS invoice_id INTEGER")
        cur.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS customer_id INTEGER")
        cur.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS price_per_unit NUMERIC(10,2)")
        
        # 1. Handle Customer
        customer_id = None
        if customer_name:
            # Check if customer exists within THIS store
            cur.execute("SELECT customer_id FROM customers WHERE customer_name = %s AND store_id = %s", (customer_name, store_id))
            res = cur.fetchone()
            if res:
                customer_id = res[0]
                # Update phone if provided
                if customer_phone:
                    cur.execute("UPDATE customers SET phone = %s WHERE customer_id = %s", (customer_phone, customer_id))
            else:
                cur.execute("INSERT INTO customers (customer_name, phone, city, store_id) VALUES (%s, %s, '', %s) RETURNING customer_id", (customer_name, customer_phone, store_id))
                customer_id = cur.fetchone()[0]

        # 2. Calculate Total & Verify Stock First
        total_amount = Decimal('0.0')
        for item in items:
            med_id = item['medicine_id']
            qty = int(item['quantity'])
            
            # Verify medicine belongs to store
            cur.execute("SELECT price, stock FROM medicines WHERE medicine_id = %s AND store_id = %s", (med_id, store_id))
            res = cur.fetchone()
            if not res:
                raise Exception(f"Medicine ID {med_id} not found or not in store")
            
            price, stock = res
            # Ensure price is Decimal
            if not isinstance(price, Decimal):
                price = Decimal(str(price))

            if stock < qty:
                raise Exception(f"Insufficient stock for Medicine ID {med_id}. Available: {stock}")
            
            total_amount += (price * qty)

        # Apply Discount
        final_amount = max(Decimal('0.0'), total_amount - discount_val)

        # 3. Create Invoice
        cur.execute("""
            INSERT INTO invoices (customer_id, total_amount, discount, payment_mode, sale_date, store_id)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
            RETURNING invoice_id
        """, (customer_id, final_amount, discount_val, payment_mode, store_id))
        invoice_id = cur.fetchone()[0]

        # 4. Process Sales & Update Stock
        for item in items:
            med_id = item['medicine_id']
            qty = int(item['quantity'])
            
            # Get current price again to be safe
            cur.execute("SELECT price FROM medicines WHERE medicine_id = %s AND store_id = %s", (med_id, store_id))
            price = cur.fetchone()[0]
            
            # Deduct Stock with concurrency check
            cur.execute("UPDATE medicines SET stock = stock - %s WHERE medicine_id = %s AND store_id = %s AND stock >= %s", (qty, med_id, store_id, qty))
            if cur.rowcount == 0:
                 # Check current stock to give better error
                 cur.execute("SELECT stock FROM medicines WHERE medicine_id = %s AND store_id = %s", (med_id, store_id))
                 current_stock = cur.fetchone()[0]
                 raise Exception(f"Insufficient stock for Medicine ID {med_id}. Available: {current_stock}")

            # Record Sale Line Item
            cur.execute("""
                INSERT INTO sales (invoice_id, medicine_id, quantity, sale_date, customer_id, price_per_unit, store_id)
                VALUES (%s, %s, %s, CURRENT_DATE, %s, %s, %s)
            """, (invoice_id, med_id, qty, customer_id, price, store_id))
            
        conn.commit()
        
        # --- Notification Triggers ---
        try:
            from app.services.notification_service import NotificationService
            ns = NotificationService()
            
            # 1. High Sales Activity
            if final_amount >= 2000:
                 ns.add_notification(f"High Value Sale: ₹{final_amount} (Inv #{invoice_id})", "success")
                 
            # 2. Low Stock Check
            # Re-check stock for sold items
            check_conn = get_db_connection()
            check_cur = check_conn.cursor()
            for item in items:
                m_id = item['medicine_id']
                check_cur.execute("""
                    SELECT medicine_name, stock, COALESCE(minimum_stock_level, 10) 
                    FROM medicines WHERE medicine_id = %s AND store_id = %s
                """, (m_id, store_id))
                res = check_cur.fetchone()
                if res:
                    m_name, m_stock, m_min = res
                    if m_stock <= m_min:
                        # Prevent duplicate spam? For now, we just notify.
                        ns.add_notification(f"Low Stock Warning: {m_name} ({m_stock} left)", "danger")
            check_conn.close()
        except Exception as e:
            print(f"Notification error: {e}")
        # -----------------------------

        return {"status": "success", "invoice_id": invoice_id}
            
    except Exception as e:
        conn.rollback()
        print(f"Error processing sale: {e}")
        return {"error": str(e)}, 500
    finally:
        conn.close()

@sales_bp.route("/invoice/<int:invoice_id>")
@login_required
def view_invoice(invoice_id):
    store_id = session.get('store_id')
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get Invoice Details, enforcing store_id check
    if store_id:
        cur.execute("""
            SELECT i.invoice_id, i.sale_date, i.total_amount, i.discount, c.customer_name, i.payment_mode
            FROM invoices i
            JOIN customers c ON i.customer_id = c.customer_id
            WHERE i.invoice_id = %s AND i.store_id = %s
        """, (invoice_id, store_id))
    else:
        # Fallback security
        cur.execute("SELECT 1 WHERE 1=0")
        
    invoice = cur.fetchone()
    
    if not invoice:
        return "Invoice not found or access denied", 404
        
    cols_inv = ['invoice_id', 'sale_date', 'total_amount', 'discount', 'customer_name', 'payment_mode']
    invoice_data = dict(zip(cols_inv, invoice))
    
    # Get Invoice Items
    # Note: We rely on invoice ownership, but could also filter items if needed. 
    # Usually invoice ownership is enough.
    cur.execute("""
        SELECT m.medicine_name, s.quantity, s.price_per_unit, (s.quantity * s.price_per_unit) as total
        FROM sales s
        JOIN medicines m ON s.medicine_id = m.medicine_id
        WHERE s.invoice_id = %s
    """, (invoice_id,))
    cols_items = ['medicine_name', 'quantity', 'price_per_unit', 'total']
    items = [dict(zip(cols_items, row)) for row in cur.fetchall()]
    
    conn.close()
    return render_template("invoice.html", invoice=invoice_data, items=items)

