from flask import Flask
import flask_cors # type: ignore
import os

def create_app():
    # Determine absolute paths for templates and static files
    base_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(base_dir, '../../frontend')
    template_dir = os.path.join(frontend_dir, 'templates')
    static_dir = os.path.join(frontend_dir, 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Enable Debugging to see errors on Vercel
    app.config['DEBUG'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True

    # Debug route to check environment
    @app.route('/debug-info')
    def debug_info():
        import os
        cwd = os.getcwd()
        try:
            frontend_ls = str(os.listdir(frontend_dir))
            template_ls = str(os.listdir(template_dir))
        except Exception as e:
            frontend_ls = f"Error: {e}"
            template_ls = "N/A"
            
        return {
            "cwd": cwd,
            "base_dir": base_dir,
            "frontend_dir": frontend_dir,
            "template_dir": template_dir,
            "frontend_files": frontend_ls,
            "template_files": template_ls,
            "env_vars": [k for k in os.environ.keys() if 'DATABASE' in k or 'SECRET' in k]
        }
    flask_cors.CORS(app)
    
    # Configuration
    app.secret_key = 'super_secret_key_change_in_production' 
    
    # Import Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.inventory import inventory_bp
    from app.routes.sales import sales_bp
    from app.routes.customers import customers_bp
    from app.routes.settings import settings_bp
    
    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(settings_bp)
    
    return app
