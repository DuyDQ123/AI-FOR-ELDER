from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy as sa

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(80), unique=True, nullable=False)
    email = sa.Column(sa.String(120), unique=True, nullable=False)
    password_hash = sa.Column(sa.String(128))
    role = sa.Column(sa.String(20), nullable=False, default='user')  # super_admin, admin, user
    user_type = sa.Column(sa.String(20), nullable=True)  # patient, caregiver
    status = sa.Column(sa.String(20), nullable=False, default='active')  # active, locked
    created_by = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=True)
    medicines = db.relationship('Medicine', backref='user', lazy=True)
    schedules = db.relationship('Schedule', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_user(self):
        return self.role == 'user'
    
    def is_active(self):
        return self.status == 'active'

class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    
    id = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column(sa.String(50), unique=True, nullable=False)
    value = sa.Column(sa.String(200))
    description = sa.Column(sa.Text)
    updated_at = sa.Column(sa.DateTime, nullable=False)
    updated_by = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)

class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    
    id = sa.Column(sa.Integer, primary_key=True)
    admin_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    action = sa.Column(sa.String(50), nullable=False)
    target_type = sa.Column(sa.String(50), nullable=False)  # user, medicine, schedule, etc.
    target_id = sa.Column(sa.Integer)
    details = sa.Column(sa.Text)
    timestamp = sa.Column(sa.DateTime, nullable=False)

class Medicine(db.Model):
    __tablename__ = 'medicines'
    
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)
    description = sa.Column(sa.Text)
    notes = sa.Column(sa.Text)
    image = sa.Column(sa.String(200))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    compartment_number = sa.Column(sa.Integer, nullable=False)  # 1-4
    medicines_in_compartment = sa.Column(sa.JSON, nullable=True)  # JSON to store multiple medicines and their quantities
    quantity = sa.Column(sa.Integer, nullable=False, default=0)  # current quantity
    min_quantity = sa.Column(sa.Integer, nullable=False, default=5)  # alert threshold
    dosage = sa.Column(sa.Integer, nullable=False, default=1)  # pills per dose
    expiry_date = sa.Column(sa.Date, nullable=True)
    schedules = db.relationship('Schedule', backref='medicine', lazy=True)
    
    # Ràng buộc: mỗi user chỉ có thể sử dụng mỗi ngăn cho 1 loại thuốc
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'compartment_number', name='medicines_unique_compartment'),
        # Remove constraint as multiple medicines can now exist in a compartment
    )

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = sa.Column(sa.Integer, primary_key=True)
    medicine_id = sa.Column(sa.Integer, sa.ForeignKey('medicines.id'), nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    time = sa.Column(sa.String(5), nullable=False)  # Format: "HH:MM"
    days = sa.Column(sa.String(100), nullable=False)  # JSON string of days
    period = sa.Column(sa.String(50))
    active = sa.Column(sa.Boolean, default=True)
    history = db.relationship('MedicineHistory', backref='schedule', lazy=True)

class MedicineHistory(db.Model):
    __tablename__ = 'medicine_history'
    
    id = sa.Column(sa.Integer, primary_key=True)
    schedule_id = sa.Column(sa.Integer, sa.ForeignKey('schedules.id'), nullable=False)
    timestamp = sa.Column(sa.DateTime, nullable=False)
    status = sa.Column(sa.String(20), nullable=False)  # taken, missed, late
    notes = sa.Column(sa.Text)