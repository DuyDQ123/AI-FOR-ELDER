import os
from datetime import timedelta

class Config:
    # Cài đặt bảo mật cơ bản
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-2024'
    
    # Cấu hình SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql://root:@localhost/elder_project'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cấu hình JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-2024'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Cấu hình bảo mật
    SECURITY_PASSWORD_SALT = 'security-password-salt-2024'
    SECURITY_PASSWORD_HASH = 'sha512_crypt'
    
    # Cấu hình email
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Cấu hình API
    API_KEY_REQUIRED = True
    API_KEY = os.environ.get('API_KEY') or 'khóa-api-mặc-định'