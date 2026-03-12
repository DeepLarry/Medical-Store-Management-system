from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from app.database import get_db_connection

inventory_bp = Blueprint('inventory', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@inventory_bp.route("/inventory")
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

@inventory_bp.route("/add_medicine", methods=['POST'])
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
        
        return redirect(url_for('inventory.inventory'))

@inventory_bp.route("/update_medicine", methods=['POST'])
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
            
        return redirect(url_for('inventory.inventory'))

@inventory_bp.route("/delete_medicine/<int:id>", methods=['POST'])
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

@inventory_bp.route("/suppliers")
@login_required
def suppliers_api():
    conn = get_db_connection()
    if not conn: return jsonify({"total_suppliers": 0})
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM suppliers")
        result = cur.fetchone()
        val = int(result[0]) if result else 0
        return jsonify({"total_suppliers": val})
    except: return jsonify({"total_suppliers": 0})
    finally: conn.close()

@inventory_bp.route("/suppliers_page")
@login_required
def suppliers_page():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM suppliers ORDER BY supplier_id DESC")
    cols = [desc[0] for desc in cur.description]
    suppliers = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return render_template("suppliers.html", suppliers=suppliers)

@inventory_bp.route("/add_supplier", methods=['POST'])
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
    return redirect(url_for('inventory.suppliers_page'))

@inventory_bp.route("/delete_supplier/<int:id>", methods=['DELETE'])
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
