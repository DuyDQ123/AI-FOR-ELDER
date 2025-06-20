from functools import wraps
from flask import request, jsonify, current_app
from flask_login import LoginManager, current_user
from models import User

login_manager = LoginManager()

def init_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin():
            return jsonify({'error': 'Yêu cầu quyền Super Admin'}), 403
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or \
           not (current_user.is_admin() or current_user.is_super_admin()):
            return jsonify({'error': 'Yêu cầu quyền Admin'}), 403
        if not current_user.is_active():
            return jsonify({'error': 'Tài khoản đã bị khóa'}), 403
        return f(*args, **kwargs)
    return decorated_function

def user_active_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        if not current_user.is_active():
            return jsonify({'error': 'Tài khoản đã bị khóa'}), 403
        return f(*args, **kwargs)
    return decorated_function

def caregiver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or \
           not (current_user.user_type == 'caregiver' or current_user.is_admin() or current_user.is_super_admin()):
            return jsonify({'error': 'Yêu cầu quyền Người chăm sóc'}), 403
        if not current_user.is_active():
            return jsonify({'error': 'Tài khoản đã bị khóa'}), 403
        return f(*args, **kwargs)
    return decorated_function

def verify_api_key():
    if not current_app.config['API_KEY_REQUIRED']:
        return True
        
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != current_app.config['API_KEY']:
        return False
    return True

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not verify_api_key():
            return jsonify({'error': 'API key không hợp lệ'}), 401
        return f(*args, **kwargs)
    return decorated_function