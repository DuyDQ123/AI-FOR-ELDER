import os
from datetime import timedelta

class Config:
    # Cài đặt bảo mật cơ bản
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Cấu hình SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql://root:@localhost:3307/elder_project'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cấu hình JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Cấu hình bảo mật
    SECURITY_PASSWORD_SALT = 'your-security-password-salt'
    SECURITY_PASSWORD_HASH = 'sha512_crypt'
    
    # Cấu hình email - CẦN THIẾT cho thông báo
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    # QUAN TRỌNG: Thay bằng Gmail thật và App Password
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your_email@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your_gmail_app_password'
    
    # Cấu hình API
    API_KEY_REQUIRED = True
    API_KEY = os.environ.get('API_KEY') or 'your-api-key'
    
    # Cấu hình SMS backup (SpeedSMS) - OPTIONAL
    SMS_ACCESS_TOKEN = os.environ.get('SMS_ACCESS_TOKEN') or 'your_sms_access_token_here'
    
    # Cấu hình thông báo
    NOTIFICATION_SETTINGS = {
        'DEFAULT_DELAY_MINUTES': 15,
        'MAX_NOTIFICATIONS_PER_DAY': 5,
        'QUIET_HOURS_START': '22:00',
        'QUIET_HOURS_END': '07:00'
    }