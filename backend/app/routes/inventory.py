from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from app.database import get_db_connection
from datetime import datetime, timedelta

inventory_bp = Blueprint('inventory', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        # Self-heal session
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

@inventory_bp.route("/inventory")
@login_required
def inventory():
    store_id = session.get('store_id')
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch medicines filtered by store
    if store_id:
        cur.execute("SELECT * FROM medicines WHERE store_id = %s ORDER BY medicine_id DESC", (store_id,))
    else:
        cur.execute("SELECT * FROM medicines ORDER BY medicine_id DESC")
        
    cols = [desc[0] for desc in cur.description]
    medicines = [dict(zip(cols, row)) for row in cur.fetchall()]
    
    # Calculate stats for SaaS Dashboard
    total_meds = len(medicines)
    low_stock_count = sum(1 for m in medicines if m['stock'] < 20) # Assuming 20 is low stock threshold
    out_of_stock_count = sum(1 for m in medicines if m['stock'] == 0)
    total_value = sum(m['stock'] * m['purchase_price'] for m in medicines if m['purchase_price'])

    # Fetch suppliers for the dropdown
    if store_id:
        cur.execute("SELECT supplier_id, supplier_name FROM suppliers WHERE store_id = %s ORDER BY supplier_name", (store_id,))
    else:
        cur.execute("SELECT supplier_id, supplier_name FROM suppliers ORDER BY supplier_name")
        
    cols_sup = [desc[0] for desc in cur.description]
    suppliers = [dict(zip(cols_sup, row)) for row in cur.fetchall()]
    
    conn.close()
    return render_template("inventory.html", medicines=medicines, suppliers=suppliers, 
                         stats={'total': total_meds, 'low': low_stock_count, 'out': out_of_stock_count, 'value': total_value})

@inventory_bp.route("/add_medicine", methods=['POST'])
@login_required
def add_medicine():
    store_id = session.get('store_id')
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        barcode = request.form.get('barcode', '').strip()
        purchase_price = request.form.get('purchase_price', 0.0)
        price = request.form['price']
        stock = request.form['stock']
        expiry = request.form['expiry_date']
        supplier_id = request.form['supplier_id']
        
        if barcode == "":
            barcode = None
            
        if not supplier_id or supplier_id.strip() == "":
            supplier_id = None
        
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO medicines (medicine_name, category, barcode, price, purchase_price, stock, expiry_date, supplier_id, store_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, category, barcode, price, purchase_price, stock, expiry, supplier_id, store_id))
            conn.commit()
            
            # Notification System Trigger
            try:
                from app.services.notification_service import NotificationService
                ns = NotificationService()
                ns.add_notification(f"New Medicine Added: {name}", "success")
            except Exception as notify_err:
                print(f"Notification Error: {notify_err}")

            flash('Medicine added successfully', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error adding medicine: {e}', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('inventory.inventory'))

@inventory_bp.route("/update_medicine", methods=['POST'])
@login_required
def update_medicine():
    store_id = session.get('store_id')
    if request.method == 'POST':
        med_id = request.form['medicine_id']
        name = request.form['name']
        category = request.form['category']
        barcode = request.form.get('barcode', '').strip()
        purchase_price = request.form.get('purchase_price', 0.0)
        price = request.form['price']
        stock = request.form['stock']
        expiry = request.form['expiry_date']
        supplier_id = request.form['supplier_id']

        if barcode == "":
            barcode = None

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            sql = """
                UPDATE medicines 
                SET medicine_name=%s, category=%s, barcode=%s, price=%s, purchase_price=%s, stock=%s, expiry_date=%s, supplier_id=%s
                WHERE medicine_id=%s
            """
            params = [name, category, barcode, price, purchase_price, stock, expiry, supplier_id, med_id]
            if store_id:
                sql += " AND store_id=%s"
                params.append(store_id)
                
            cur.execute(sql, tuple(params))
            conn.commit()
            flash('Medicine updated successfully', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error updating medicine: {e}', 'danger')
        finally:
            conn.close()
            
        return redirect(url_for('inventory.inventory'))

@inventory_bp.route("/delete_medicine/<int:id>", methods=['POST'])
@login_required
def delete_medicine(id):
    store_id = session.get('store_id')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if store_id:
            cur.execute("DELETE FROM medicines WHERE medicine_id = %s AND store_id = %s", (id, store_id))
        else:
            cur.execute("DELETE FROM medicines WHERE medicine_id = %s", (id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@inventory_bp.route("/suppliers")
@login_required
def suppliers_api():
    store_id = session.get('store_id')
    conn = get_db_connection()
    if not conn: return jsonify({"total_suppliers": 0})
    try:
        cur = conn.cursor()
        if store_id:
            cur.execute("SELECT COUNT(*) FROM suppliers WHERE store_id = %s", (store_id,))
        else:
            cur.execute("SELECT COUNT(*) FROM suppliers")
        result = cur.fetchone()
        val = int(result[0]) if result else 0
        return jsonify({"total_suppliers": val})
    except: return jsonify({"total_suppliers": 0})
    finally: conn.close()

@inventory_bp.route("/suppliers_page")
@login_required
def suppliers_page():
    store_id = session.get('store_id')
    conn = get_db_connection()
    cur = conn.cursor()
    if store_id:
        cur.execute("SELECT * FROM suppliers WHERE store_id = %s ORDER BY supplier_id DESC", (store_id,))
    else:
        cur.execute("SELECT * FROM suppliers ORDER BY supplier_id DESC")
    cols = [desc[0] for desc in cur.description]
    suppliers = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return render_template("suppliers.html", suppliers=suppliers)

@inventory_bp.route("/add_supplier", methods=['POST'])
@login_required
def add_supplier():
    store_id = session.get('store_id')
    name = request.form['name']
    phone = request.form['phone']
    city = request.form['city']
    
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO suppliers (supplier_name, phone, city, store_id) VALUES (%s, %s, %s, %s)", (name, phone, city, store_id))
        conn.commit()
        flash('Supplier added successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(str(e), 'danger')
    finally:
        conn.close()
    return redirect(url_for('inventory.suppliers_page'))

@inventory_bp.route("/delete_supplier/<int:id>", methods=['DELETE'])
@login_required
def delete_supplier(id):
    store_id = session.get('store_id')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if store_id:
            cur.execute("DELETE FROM suppliers WHERE supplier_id = %s AND store_id = %s", (id, store_id))
        else:
             cur.execute("DELETE FROM suppliers WHERE supplier_id = %s", (id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@inventory_bp.route('/expiry_analytics')
@login_required
def expiry_analytics():
    store_id = session.get('store_id')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Today's date
        today = datetime.now().date()
        date_30 = today + timedelta(days=30)
        date_90 = today + timedelta(days=90)
        
        # 1. Expired Items (Already Expired)
        cur.execute('SELECT * FROM medicines WHERE expiry_date < %s AND stock > 0 AND store_id = %s', (today, store_id))
        cols = [desc[0] for desc in cur.description]
        expired = [dict(zip(cols, row)) for row in cur.fetchall()]
        
        # 2. Critical (< 30 Days)
        cur.execute('SELECT * FROM medicines WHERE expiry_date BETWEEN %s AND %s AND stock > 0 AND store_id = %s', (today, date_30, store_id))
        critical = [dict(zip(cols, row)) for row in cur.fetchall()]
        
        # 3. Upcoming (30 - 90 Days)
        cur.execute('SELECT * FROM medicines WHERE expiry_date BETWEEN %s AND %s AND stock > 0 AND store_id = %s', (date_30, date_90, store_id))
        upcoming = [dict(zip(cols, row)) for row in cur.fetchall()]
        
        # Calculate Potential Loss (Cost * Quantity of Expired + Critical)
        expired_loss = sum(float(item['purchase_price']) * int(item['stock']) for item in expired) if expired else 0.0
        critical_risk = sum(float(item['purchase_price']) * int(item['stock']) for item in critical) if critical else 0.0
        
    except Exception as e:
        flash(f'Error fetching expiry data: {str(e)}', 'danger')
        expired = []
        critical = []
        upcoming = []
        expired_loss = 0
        critical_risk = 0
    finally:
        conn.close()
        
    return render_template('expiry_analytics.html', 
                         expired=expired, 
                         critical=critical, 
                         upcoming=upcoming,
                         expired_loss=expired_loss,
                         critical_risk=critical_risk,
                         today=today)


@inventory_bp.route('/api/supplier_medicines/<int:supplier_id>')
@login_required
def get_supplier_medicines(supplier_id):
    conn = get_db_connection()
    cur = conn.cursor()
    # Fetch medicines from this supplier, prioritizing low stock
    cur.execute('''
        SELECT medicine_name, stock, minimum_stock_level as min_stock, batch_number as sku 
        FROM medicines 
        WHERE supplier_id = %s AND stock <= COALESCE(minimum_stock_level, 10)
        ORDER BY stock ASC
    ''', (supplier_id,))
    
    cols = [desc[0] for desc in cur.description]
    medicines = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return jsonify(medicines)

