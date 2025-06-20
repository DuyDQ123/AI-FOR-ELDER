from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import platform
import os

from config import Config
from models import db, User, Medicine, Schedule, MedicineHistory
from auth import init_login_manager, admin_required, caregiver_required, require_api_key
from routes.auth import auth

app = Flask(__name__)
app.config.from_object(Config)

# Khởi tạo các extension
db.init_app(app)
init_login_manager(app)

# Đăng ký blueprint
app.register_blueprint(auth, url_prefix='/auth')

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

# Routes chính
@app.route('/')
@login_required
def index():
    schedules = Schedule.query.filter_by(user_id=current_user.id).all()
    medicines = Medicine.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', medicines=medicines, schedules=schedules)

@app.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    if request.method == 'POST':
        new_medicine = Medicine(
            name=request.form['name'],
            description=request.form['description'],
            notes=request.form['notes'],
            image=request.form['image'] if 'image' in request.form else '',
            user_id=current_user.id
        )
        db.session.add(new_medicine)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_medicine.html')

@app.route('/add_schedule', methods=['GET', 'POST'])
@login_required
def add_schedule():
    if request.method == 'POST':
        new_schedule = Schedule(
            medicine_id=int(request.form['medicine_id']),
            user_id=current_user.id,
            time=request.form['time'],
            days=request.form.getlist('days[]'),
            period=request.form['period'],
            active=True
        )
        db.session.add(new_schedule)
        db.session.commit()
        return redirect(url_for('index'))
    medicines = Medicine.query.filter_by(user_id=current_user.id).all()
    return render_template('add_schedule.html', medicines=medicines)

@app.route('/reports')
@login_required
def reports():
    weekly_stats = calculate_weekly_stats(current_user.id)
    return render_template('reports.html', stats=weekly_stats)

# API Endpoints
@app.route('/api/check_schedule', methods=['GET'])
@require_api_key
def check_schedule():
    schedules = get_current_schedules(current_user.id)
    return jsonify(schedules)

@app.route('/api/confirm_medicine', methods=['POST'])
@require_api_key
def confirm_medicine():
    schedule_id = request.json.get('schedule_id')
    schedule = Schedule.query.get_or_404(schedule_id)
    
    if schedule.user_id != current_user.id:
        return jsonify({'error': 'Không có quyền truy cập'}), 403
    
    history_entry = MedicineHistory(
        schedule_id=schedule_id,
        timestamp=datetime.now(),
        status='taken'
    )
    db.session.add(history_entry)
    db.session.commit()
    
    return jsonify({'success': True})

# Helper functions
def get_current_schedules(user_id):
    current_time = datetime.now()
    today_schedules = Schedule.query.filter_by(
        user_id=user_id,
        active=True
    ).all()
    
    current_schedules = []
    for schedule in today_schedules:
        schedule_time = datetime.strptime(schedule.time, '%H:%M').time()
        schedule_datetime = datetime.combine(current_time.date(), schedule_time)
        
        if abs((schedule_datetime - current_time).total_seconds()) <= 300:
            medicine = Medicine.query.get(schedule.medicine_id)
            if medicine:
                current_schedules.append({
                    'schedule_id': schedule.id,
                    'medicine_name': medicine.name,
                    'time': schedule.time,
                    'notes': medicine.notes
                })
    
    return current_schedules

def calculate_weekly_stats(user_id):
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    
    week_history = MedicineHistory.query.join(Schedule).filter(
        Schedule.user_id == user_id,
        MedicineHistory.timestamp >= week_start
    ).all()
    
    total_scheduled = Schedule.query.filter_by(user_id=user_id, active=True).count() * 7
    taken = sum(1 for h in week_history if h.status == 'taken')
    missed = total_scheduled - taken
    
    return {
        'taken': taken,
        'missed': missed,
        'compliance_rate': (taken / total_scheduled * 100) if total_scheduled > 0 else 0
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        if rpi_handler:
            rpi_handler.cleanup()