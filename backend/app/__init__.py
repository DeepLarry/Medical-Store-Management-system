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
