from flask import Flask
from flask_login import login_required, current_user
from datetime import datetime
import platform
import os
import json

from config import Config
from models import db
from auth import init_login_manager
from routes.auth import auth
from routes.main import main
from routes.test_dispenser import test_dispenser

app = Flask(__name__)
app.config.from_object(Config)

# Khởi tạo các extension
db.init_app(app)
init_login_manager(app)

# Thêm filter để parse JSON trong template
@app.template_filter('from_json')
def from_json_filter(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return []
    return value if isinstance(value, list) else []

# Đăng ký blueprints
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(main)
app.register_blueprint(test_dispenser, url_prefix='/api')

# Khởi tạo Raspberry Pi handler chỉ khi chạy trên Raspberry Pi
rpi_handler = None
if platform.system() == 'Linux' and 'arm' in platform.machine():
    try:
        from rpi_handler import RaspberryPiHandler
        rpi_handler = RaspberryPiHandler()
        rpi_handler.start()
        print("Đã khởi tạo Raspberry Pi handler")
    except Exception as e:
        print(f"Không thể khởi tạo Raspberry Pi handler: {e}")
        print("Ứng dụng sẽ chạy ở chế độ web-only")

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        if rpi_handler:
            rpi_handler.cleanup()