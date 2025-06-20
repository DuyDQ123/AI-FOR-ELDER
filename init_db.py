from flask import Flask
from models import db, User, SystemConfig
from config import Config
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_db():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    with app.app_context():
        # Xóa và tạo lại tất cả các bảng
        db.drop_all()
        db.create_all()
        
        # Tạo tài khoản super_admin mặc định
        super_admin = User(
            username='superadmin',
            email='superadmin@example.com',
            role='super_admin',
            status='active'
        )
        super_admin.set_password('superadmin123')
        db.session.add(super_admin)
        db.session.commit()

        # Tạo tài khoản admin mặc định
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            status='active',
            created_by=super_admin.id
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

        # Thêm cấu hình hệ thống mặc định
        default_configs = [
            {
                'key': 'max_users',
                'value': '1000',
                'description': 'Số lượng người dùng tối đa',
            },
            {
                'key': 'alert_timeout',
                'value': '300',
                'description': 'Thời gian chờ nhắc nhở lại (giây)',
            },
            {
                'key': 'backup_interval',
                'value': '86400',
                'description': 'Thời gian giữa các lần sao lưu tự động (giây)',
            }
        ]

        for config in default_configs:
            new_config = SystemConfig(
                key=config['key'],
                value=config['value'],
                description=config['description'],
                updated_at=datetime.now(),
                updated_by=super_admin.id
            )
            db.session.add(new_config)
        
        db.session.commit()
        
        print("Đã khởi tạo cơ sở dữ liệu thành công!")
        print("\nTài khoản super admin mặc định:")
        print(f"Username: {super_admin.username}")
        print(f"Password: superadmin123")
        print("\nTài khoản admin mặc định:")
        print(f"Username: {admin.username}")
        print(f"Password: admin123")

if __name__ == '__main__':
    init_db()