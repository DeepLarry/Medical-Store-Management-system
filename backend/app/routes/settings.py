from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from app.database import get_db_connection

settings_bp = Blueprint('settings', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        # Restore session context if missing
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

@settings_bp.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    store_id = session.get('store_id')
    if not store_id:
        flash("Store context missing", "error")
        return redirect(url_for('dashboard.dashboard'))

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
                # Check if settings exist for this store
                cur.execute("SELECT id FROM store_settings WHERE store_id = %s", (store_id,))
                res = cur.fetchone()
                
                if res:
                    cur.execute("""
                        UPDATE store_settings 
                        SET store_name=%s, currency_symbol=%s, tax_rate=%s, address=%s, phone=%s, updated_at=CURRENT_TIMESTAMP
                        WHERE store_id=%s
                    """, (store_name, currency_symbol, tax_rate, address, phone, store_id))
                else:
                    cur.execute("""
                        INSERT INTO store_settings (store_name, currency_symbol, tax_rate, address, phone, store_id, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """, (store_name, currency_symbol, tax_rate, address, phone, store_id))
                    
                conn.commit()
                flash('Settings saved successfully', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error saving settings: {e}', 'danger')
            finally:
                cur.close()
                conn.close()
            return redirect(url_for('settings.settings'))

        # Handle GET
        try:
            cur.execute("SELECT * FROM store_settings WHERE store_id = %s", (store_id,))
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
