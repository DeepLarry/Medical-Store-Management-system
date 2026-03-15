from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from app.database import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            if conn is None:
                flash('Database connection failed. Please check your configuration.', 'error')
                return render_template('login.html')

            cur = conn.cursor()
            # Fetch role and store_id as well
            cur.execute("SELECT id, username, password_hash, role, store_id FROM admins WHERE username = %s OR email = %s", (identifier, identifier))
            user = cur.fetchone()
            conn.close()
            
            if user:
                # Debugging: Check hash directly
                is_valid = check_password_hash(user[2], password)
                
                if is_valid:
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    # Store SaaS context in session
                    session['role'] = user[3] if user[3] else 'admin' 
                    session['store_id'] = user[4]
                    return redirect(url_for('dashboard.dashboard'))
                else:
                    # Detailed debug error for Vercel
                    flash(f'Debug: Password mismatch. Stored hash prefix: {user[2][:15]}...', 'error')
                    return redirect(url_for('auth.login'))
            else:
                flash(f'Debug: User "{identifier}" not found in database.', 'error')
                return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            return render_template('login.html')
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
