from flask import g, request, session, abort
from functools import wraps

class TenantContext:
    @staticmethod
    def get_current_store_id():
        """Retrieve the store ID from the current session or request context."""
        if 'store_id' in session:
            return session['store_id']
        # For APIs using API Keys or JWT, check request headers
        store_id = request.headers.get('X-Store-ID')
        if store_id:
            return store_id
        return None

def store_required(f):
    """Decorator to ensure store context is present."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        store_id = TenantContext.get_current_store_id()
        if not store_id:
            return {"error": "Store context missing"}, 401
        g.store_id = store_id
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Decorator for Role-Based Access Control (RBAC)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('role', 'cashier') # Default minimal privilege
            if user_role not in allowed_roles:
                return {"error": "Insufficient permissions"}, 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
