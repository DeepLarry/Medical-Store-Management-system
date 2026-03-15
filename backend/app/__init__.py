from flask import Flask
import flask_cors # type: ignore
import os

def create_app():
    # Point table/static to the root folders
    app = Flask(__name__, template_folder='../../frontend/templates', static_folder='../../frontend/static')
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
