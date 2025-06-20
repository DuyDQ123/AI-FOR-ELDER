from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, Medicine, Schedule, MedicineHistory, User, SystemConfig, AdminLog
from datetime import datetime, timedelta
from auth import require_api_key, admin_required, super_admin_required, user_active_required

main = Blueprint('main', __name__)

# Super Admin Routes
@main.route('/admin/system-config', methods=['GET', 'POST'])
@super_admin_required
def system_config():
    if request.method == 'POST':
        key = request.form.get('key')
        value = request.form.get('value')
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            old_value = config.value
            config.value = value
            config.updated_at = datetime.now()
            config.updated_by = current_user.id
            
            # Log the change
            log = AdminLog(
                admin_id=current_user.id,
                action='update_config',
                target_type='system_config',
                target_id=config.id,
                details=f'Changed {key} from {old_value} to {value}',
                timestamp=datetime.now()
            )
            db.session.add(log)
            db.session.commit()
            
    configs = SystemConfig.query.all()
    return render_template('admin/system_config.html', configs=configs)

@main.route('/admin/user-management')
@super_admin_required
def user_management():
    users = User.query.filter(User.role != 'super_admin').all()
    return render_template('admin/user_management.html', users=users)

@main.route('/admin/user/<int:user_id>', methods=['POST'])
@super_admin_required
def manage_user(user_id):
    user = User.query.get_or_404(user_id)
    action = request.form.get('action')
    
    if action == 'lock':
        user.status = 'locked'
    elif action == 'unlock':
        user.status = 'active'
    elif action == 'change_role':
        new_role = request.form.get('role')
        if new_role in ['admin', 'user']:
            user.role = new_role
            
    log = AdminLog(
        admin_id=current_user.id,
        action=action,
        target_type='user',
        target_id=user.id,
        details=f'User {user.username}: {action}',
        timestamp=datetime.now()
    )
    db.session.add(log)
    db.session.commit()
    
    return redirect(url_for('main.user_management'))

@main.route('/admin/logs')
@admin_required
def admin_logs():
    logs = AdminLog.query.order_by(AdminLog.timestamp.desc()).limit(100).all()
    return render_template('admin/logs.html', logs=logs)

# Admin Routes
@main.route('/admin/users')
@admin_required
def manage_users():
    users = User.query.filter_by(role='user').all()
    return render_template('admin/manage_users.html', users=users)

@main.route('/admin/user/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'user':
        new_password = request.form.get('new_password')
        user.set_password(new_password)
        
        log = AdminLog(
            admin_id=current_user.id,
            action='reset_password',
            target_type='user',
            target_id=user.id,
            details=f'Reset password for {user.username}',
            timestamp=datetime.now()
        )
        db.session.add(log)
        db.session.commit()
        
    return redirect(url_for('main.manage_users'))

@main.route('/admin/schedules')
@admin_required
def manage_schedules():
    schedules = Schedule.query.all()
    return render_template('admin/manage_schedules.html', schedules=schedules)


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('welcome.html')
        
    if current_user.is_super_admin():
        return redirect(url_for('main.system_config'))
    elif current_user.is_admin():
        return redirect(url_for('main.admin_logs'))
    else:
        schedules = Schedule.query.filter_by(user_id=current_user.id).all()
        medicines = Medicine.query.filter_by(user_id=current_user.id).all()
        return render_template('index.html', medicines=medicines, schedules=schedules)

@main.route('/add_medicine', methods=['GET', 'POST'])
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
        return redirect(url_for('main.index'))
    return render_template('add_medicine.html')

@main.route('/add_schedule', methods=['GET', 'POST'])
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
        return redirect(url_for('main.index'))
    medicines = Medicine.query.filter_by(user_id=current_user.id).all()
    return render_template('add_schedule.html', medicines=medicines)

@main.route('/reports')
@login_required
def reports():
    weekly_stats = calculate_weekly_stats(current_user.id)
    return render_template('reports.html', stats=weekly_stats)

@main.route('/api/check_schedule', methods=['GET'])
@login_required
@require_api_key
def check_schedule():
    schedules = get_current_schedules(current_user.id)
    return jsonify(schedules)

@main.route('/api/confirm_medicine', methods=['POST'])
@login_required
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