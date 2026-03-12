from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
# from authlib.integrations.flask_client import OAuth
import psycopg2
import os
from functools import wraps

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# Configuration
app.secret_key = 'super_secret_key_change_in_production' 

# OAUTHLIB configuration for local development - disabled for now
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Google OAuth Configuration - disabled for now
# app.config['GOOGLE_CLIENT_ID'] = 'YOUR_GOOGLE_CLIENT_ID'
# app.config['GOOGLE_CLIENT_SECRET'] = 'YOUR_GOOGLE_CLIENT_SECRET'

# oauth = OAuth(app)
# google = oauth.register(...)

# Database Connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="medical_store_db",
            user="postgres",
            password="@#1234Deep",
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

# Login Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- AUTH ROUTES ---

# Google Auth routes disabled for now to simplify deployment
# @app.route('/login/google') ...

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash FROM admins WHERE username = %s OR email = %s", (identifier, identifier))
        user = cur.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password', 'error')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- PAGE ROUTES ---

@app.route("/")
def home():
    if 'user_id' in session:
         return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/inventory")
@login_required
def inventory():
    conn = get_db_connection()
    cur = conn.cursor()
    # Fetch medicines
    cur.execute("SELECT * FROM medicines ORDER BY medicine_id DESC")
    cols = [desc[0] for desc in cur.description]
    medicines = [dict(zip(cols, row)) for row in cur.fetchall()]
    
    # Fetch suppliers for the dropdown
    cur.execute("SELECT supplier_id, supplier_name FROM suppliers ORDER BY supplier_name")
    cols_sup = [desc[0] for desc in cur.description]
    suppliers = [dict(zip(cols_sup, row)) for row in cur.fetchall()]
    
    conn.close()
    return render_template("inventory.html", medicines=medicines, suppliers=suppliers)

@app.route("/sales")
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

@app.route("/suppliers_page")
@login_required
def suppliers_page():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM suppliers ORDER BY supplier_id DESC")
    cols = [desc[0] for desc in cur.description]
    suppliers = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return render_template("suppliers.html", suppliers=suppliers)

@app.route("/customers_page")
@login_required
def customers_page():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers ORDER BY customer_id DESC")
    cols = [desc[0] for desc in cur.description]
    customers = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return render_template("customers.html", customers=customers)

@app.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        
        # Handle POST
        if request.method == 'POST':
            store_name = request.form.get('store_name')
            currency_symbol = request.form.get('currency')
            tax_rate = request.form.get('tax_rate')
            address = request.form.get('address')
            phone = request.form.get('phone')
            
            try:
                # Always update the first row for now (Single Tenant Logic)
                cur.execute("SELECT id FROM store_settings ORDER BY id ASC LIMIT 1")
                res = cur.fetchone()
                
                if res:
                    cur.execute("""
                        UPDATE store_settings 
                        SET store_name=%s, currency_symbol=%s, tax_rate=%s, address=%s, phone=%s 
                        WHERE id=%s
                    """, (store_name, currency_symbol, tax_rate, address, phone, res[0]))
                else:
                    cur.execute("""
                        INSERT INTO store_settings (store_name, currency_symbol, tax_rate, address, phone)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (store_name, currency_symbol, tax_rate, address, phone))
                    
                conn.commit()
                flash('Settings saved successfully', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error saving settings: {e}', 'danger')
            finally:
                cur.close()
                conn.close()
            return redirect(url_for('settings'))

        # Handle GET
        try:
            cur.execute("SELECT * FROM store_settings ORDER BY id ASC LIMIT 1")
            row = cur.fetchone()
            cols = [desc[0] for desc in cur.description]
            settings_data = dict(zip(cols, row)) if row else {}
        except:
            settings_data = {}
        finally:
            cur.close()
            conn.close()
    else:
        settings_data = {}

    return render_template("settings.html", settings=settings_data)


# --- ACTION ROUTES (Form Submissions) ---

@app.route("/add_medicine", methods=['POST'])
@login_required
def add_medicine():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        stock = request.form['stock']
        expiry = request.form['expiry_date']
        supplier_id = request.form['supplier_id']
        
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO medicines (medicine_name, category, price, stock, expiry_date, supplier_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, category, price, stock, expiry, supplier_id))
            conn.commit()
            flash('Medicine added successfully', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error adding medicine: {e}', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('inventory'))

@app.route("/update_medicine", methods=['POST'])
@login_required
def update_medicine():
    if request.method == 'POST':
        med_id = request.form['medicine_id']
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        stock = request.form['stock']
        expiry = request.form['expiry_date']
        supplier_id = request.form['supplier_id']

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE medicines 
                SET medicine_name=%s, category=%s, price=%s, stock=%s, expiry_date=%s, supplier_id=%s
                WHERE medicine_id=%s
            """, (name, category, price, stock, expiry, supplier_id, med_id))
            conn.commit()
            flash('Medicine updated successfully', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error updating medicine: {e}', 'danger')
        finally:
            conn.close()
            
        return redirect(url_for('inventory'))

@app.route("/delete_medicine/<int:id>", methods=['POST'])
@login_required
def delete_medicine(id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM medicines WHERE medicine_id = %s", (id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route("/create_sale", methods=['POST'])
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
            return redirect(url_for('sales_page'))
            
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
        
    return redirect(url_for('sales_page'))

@app.route("/add_supplier", methods=['POST'])
@login_required
def add_supplier():
    name = request.form['name']
    phone = request.form['phone']
    city = request.form['city']
    
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO suppliers (supplier_name, phone, city) VALUES (%s, %s, %s)", (name, phone, city))
        conn.commit()
        flash('Supplier added successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(str(e), 'danger')
    finally:
        conn.close()
    return redirect(url_for('suppliers_page'))

@app.route("/delete_supplier/<int:id>", methods=['DELETE'])
@login_required
def delete_supplier(id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM suppliers WHERE supplier_id = %s", (id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route("/add_customer", methods=['POST'])
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
    return redirect(url_for('customers_page'))

@app.route("/delete_customer/<int:id>", methods=['DELETE'])
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

# --- API Endpoints ---

@app.route("/total_sales")
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
        conn.close()
        return jsonify({"total_sales": val})
    except: return jsonify({"total_sales": 0})

@app.route("/suppliers")
@login_required
def suppliers_api():
    conn = get_db_connection()
    if not conn: return jsonify({"total_suppliers": 0})
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM suppliers")
        result = cur.fetchone()
        val = int(result[0]) if result else 0
        conn.close()
        return jsonify({"total_suppliers": val})
    except: return jsonify({"total_suppliers": 0})

@app.route("/total_medicines_count")
@login_required
def total_medicines_count():
    conn = get_db_connection()
    if not conn: return jsonify({"count": 0})
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM medicines")
        result = cur.fetchone()
        val = int(result[0]) if result else 0
        conn.close()
        return jsonify({"count": val})
    except: return jsonify({"count": 0})

@app.route("/low_stock_count")
@login_required
def low_stock_count():
    conn = get_db_connection()
    if not conn: return jsonify({"count": 0})
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM medicines WHERE stock < 20")
        result = cur.fetchone()
        val = int(result[0]) if result else 0
        conn.close()
        return jsonify({"count": val})
    except: return jsonify({"count": 0})

@app.route("/top_medicines")
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
        conn.close()
        return jsonify(data)
    except: return jsonify([])

@app.route("/monthly_sales")
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
        conn.close()
        return jsonify(data)
    except: return jsonify([])

@app.route("/low_stock")
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
        conn.close()
        return jsonify(data)
    except: return jsonify([])

@app.route("/expiry_medicines")
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
        conn.close()
        return jsonify(data)
    except: return jsonify([])

@app.route("/live_activity")
@login_required
def live_activity():
    """
    Returns latest sales to provide a real-time feed effect.
    Ideally this would use WebSockets, but polling works for this scale.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Fetch last 5 sales with timestamps
        cur.execute("""
            SELECT s.sale_id, m.medicine_name, s.quantity, (s.quantity * m.price) as total_price, s.sale_date
            FROM sales s
            JOIN medicines m ON s.medicine_id = m.medicine_id
            ORDER BY s.sale_id DESC
            LIMIT 5
        """)
        sales = cur.fetchall()
        
        # Format for frontend
        activity_log = []
        for s in sales:
            activity_log.append({
                'id': s[0],
                'type': 'sale',
                'message': f"Sold {s[2]}x {s[1]}",
                'amount': float(s[3]),
                'time': str(s[4]) # Simplistic date string
            })
            
        return jsonify(activity_log)
    except Exception as e:
        print(f"Error fetching live activity: {e}")
        return jsonify([])
    finally:
        conn.close()

if __name__ == "__main__":
    # production server uses wsgi.py, local dev matches
    app.run(debug=True, port=5000)
