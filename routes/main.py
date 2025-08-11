from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from flask import flash
from models import db, Medicine, Schedule, MedicineHistory, User, SystemConfig, AdminLog
from datetime import datetime, timedelta
from auth import require_api_key, admin_required, super_admin_required, user_active_required
from werkzeug.security import generate_password_hash

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
    return render_template('admin/manage_users.html', users=users)

@main.route('/admin/create-user', methods=['POST'])
@super_admin_required
def create_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    if role not in ['admin', 'user']:
        return jsonify({'error': 'Invalid role'}), 400

    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role,
        created_at=datetime.now()
    )
    db.session.add(new_user)
    db.session.commit()

    log = AdminLog(
        admin_id=current_user.id,
        action='create_user',
        target_type='user',
        target_id=new_user.id,
        details=f'Created user {username} with role {role}',
        timestamp=datetime.now()
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'success': True, 'user_id': new_user.id})

@main.route('/admin/create-user-full', methods=['POST'])
@admin_required
def create_user_full():
    """Tạo tài khoản người dùng với đầy đủ thông tin"""
    try:
        # Lấy thông tin đăng nhập
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        user_type = request.form.get('user_type', 'patient')
        
        # Lấy thông tin cá nhân
        full_name = request.form.get('full_name')
        age = request.form.get('age')
        phone = request.form.get('phone')
        address = request.form.get('address')

        # Validation
        if not username or not email or not password:
            flash('Vui lòng điền đầy đủ thông tin bắt buộc (tên đăng nhập, email, mật khẩu)', 'error')
            return redirect(url_for('main.user_management'))

        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự', 'error')
            return redirect(url_for('main.user_management'))

        if role not in ['admin', 'user']:
            flash('Vai trò không hợp lệ', 'error')
            return redirect(url_for('main.user_management'))

        # Kiểm tra trùng lặp
        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại', 'error')
            return redirect(url_for('main.user_management'))

        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng', 'error')
            return redirect(url_for('main.user_management'))

        # Tạo user mới
        new_user = User(
            username=username,
            email=email,
            role=role,
            user_type=user_type,
            status='active',
            created_by=current_user.id,
            created_at=datetime.now(),
            full_name=full_name if full_name else None,
            age=int(age) if age else None,
            phone=phone if phone else None,
            address=address if address else None
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Ghi log
        log = AdminLog(
            admin_id=current_user.id,
            action='create_user_full',
            target_type='user',
            target_id=new_user.id,
            details=f'Created user {username} (email: {email}) with role {role}',
            timestamp=datetime.now()
        )
        db.session.add(log)
        db.session.commit()

        flash(f'Đã tạo thành công tài khoản cho {full_name or username}', 'success')
        return redirect(url_for('main.user_management'))

    except ValueError as e:
        flash('Tuổi phải là số hợp lệ', 'error')
        return redirect(url_for('main.user_management'))
    except Exception as e:
        flash(f'Lỗi khi tạo tài khoản: {str(e)}', 'error')
        return redirect(url_for('main.user_management'))

@main.route('/admin/manage_user/<int:user_id>', methods=['POST'])
@super_admin_required
def manage_user(user_id):
    user = User.query.get_or_404(user_id)
    action = request.form.get('action')
    
    if action == 'lock':
        user.status = 'locked'
        db.session.commit()
    elif action == 'unlock':
        user.status = 'active'
        db.session.commit()
    elif action == 'change_role':
        new_role = request.form.get('role')
        if new_role in ['admin', 'user']:
            user.role = new_role
            db.session.commit()
            
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
    return render_template('admin/logs.html', logs=logs, User=User)

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
    users = User.query.filter_by(role='user').all()
    return render_template('admin/manage_schedules.html', users=users)

@main.route('/admin/schedules/<int:user_id>')
@admin_required
def user_schedules(user_id):
    user = User.query.get_or_404(user_id)
    schedules = Schedule.query.filter_by(user_id=user_id).all()
    return render_template('admin/user_schedules.html', user=user, schedules=schedules)


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
        @main.route('/delete_schedule/<int:schedule_id>', methods=['POST'])
        @login_required
        def delete_schedule(schedule_id):
            """Delete a specific schedule for the logged-in user."""
            schedule = Schedule.query.get_or_404(schedule_id)
            if schedule.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized access'}), 403
        
            # Remove associated medicine history entries before deleting the schedule
            MedicineHistory.query.filter_by(schedule_id=schedule.id).delete()
            db.session.delete(schedule)
            db.session.commit()
            flash('Schedule deleted successfully.', 'success')
            return redirect(url_for('main.index'))
        
        print(f"Rendering index with {len(medicines)} medicines and {len(schedules)} schedules.")
        return render_template('index.html', medicines=medicines, schedules=schedules)

@main.route('/delete_schedule/<int:schedule_id>', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    """Delete a specific schedule for the logged-in user."""
    print(f"Attempting to delete schedule with ID: {schedule_id} for user ID: {current_user.id}")
    schedule = Schedule.query.get_or_404(schedule_id)
    if schedule.user_id != current_user.id:
        print("Unauthorized access attempt.")
        return jsonify({'error': 'Unauthorized access'}), 403

    db.session.delete(schedule)
    db.session.commit()
    print("Schedule deleted successfully.")
    flash('Schedule deleted successfully.', 'success')
    return redirect(url_for('main.index'))

@main.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    if request.method == 'POST':
        compartment_number = int(request.form['compartment_number'])
        
        # Check if compartment number is valid (1-4)
        if compartment_number not in [1, 2, 3, 4]:
            return "Số ngăn không hợp lệ. Chỉ có 4 ngăn (1-4)", 400
        
        # Check if compartment is already in use by this user
        existing = Medicine.query.filter_by(
            compartment_number=compartment_number,
            user_id=current_user.id
        ).first()
        
        if existing:
            return f"Ngăn {compartment_number} đã được sử dụng cho thuốc '{existing.name}'. Vui lòng chọn ngăn khác hoặc xóa thuốc cũ trước.", 400
            
        new_medicine = Medicine(
            name=request.form['name'],
            description=request.form['description'],
            notes=request.form['notes'],
            image=request.form['image'] if 'image' in request.form else '',
            compartment_number=compartment_number,
            quantity=int(request.form['quantity']),
            min_quantity=int(request.form['min_quantity']),
            dosage=int(request.form['dosage']),
            expiry_date=datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date() if request.form['expiry_date'] else None,
            user_id=current_user.id
        )
        
        try:
            db.session.add(new_medicine)
            db.session.commit()
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            # Handle specific constraint violation
            if 'medicines_unique_compartment' in str(e):
                return f"Ngăn {compartment_number} đã được sử dụng. Vui lòng chọn ngăn khác.", 400
            else:
                return f"Lỗi khi thêm thuốc: {str(e)}", 500
                
    return render_template('add_medicine.html')

@main.route('/add_schedule', methods=['GET', 'POST'])
@login_required
def add_schedule():
    if request.method == 'POST':
        import json
        days_list = request.form.getlist('days[]')
        new_schedule = Schedule(
            medicine_id=int(request.form['medicine_id']),
            user_id=current_user.id,
            time=request.form['time'],
            days=json.dumps(days_list),  # Convert to JSON string
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

@main.route('/api/check_schedule_by_user/<int:user_id>', methods=['GET'])
@require_api_key
def check_schedule_by_user(user_id):
    # API cho Raspberry Pi - chi can API key, khong can dang nhap
    schedules = get_current_schedules(user_id)
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

@main.route('/api/confirm_medicine_by_user', methods=['POST'])
@require_api_key
def confirm_medicine_by_user():
    # API cho Raspberry Pi - chi can API key, khong can dang nhap
    schedule_id = request.json.get('schedule_id')
    user_id = request.json.get('user_id')
    
    schedule = Schedule.query.get_or_404(schedule_id)
    
    # Kiem tra xem schedule co phai cua user nay khong
    if schedule.user_id != user_id:
        return jsonify({'error': 'Không có quyền truy cập'}), 403
    
    history_entry = MedicineHistory(
        schedule_id=schedule_id,
        timestamp=datetime.now(),
        status='taken'
    )
    db.session.add(history_entry)
    db.session.commit()
    
    return jsonify({'success': True})

@main.route('/api/trigger_info_display', methods=['POST'])
@require_api_key
def trigger_info_display():
    """API endpoint to handle INFO button press and notify ESP32"""
    user_id = request.json.get('user_id')
    info_flag = request.json.get('info_flag')

    if not user_id or not info_flag:
        return jsonify({'error': 'Missing required fields'}), 400

    # Log the INFO flag for ESP32 to detect
    try:
        log_entry = AdminLog(
            admin_id=user_id,
            action='info_flag',
            target_type='user',
            target_id=user_id,
            details='INFO button pressed',
            timestamp=datetime.now()
        )
        db.session.add(log_entry)
        db.session.commit()

        return jsonify({'success': True, 'message': 'INFO flag logged successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/check_info_flag/<int:user_id>', methods=['GET'])
@require_api_key
def check_info_flag(user_id):
    """API endpoint for ESP32 to check if INFO button was pressed"""
    # Tìm INFO flag gần nhất trong vòng 1 phút
    from datetime import timedelta
    recent_time = datetime.now() - timedelta(minutes=2)
    
    recent_info_flag = AdminLog.query.filter(
        AdminLog.target_id == user_id,
        AdminLog.action == 'info_flag',
        AdminLog.timestamp >= recent_time
    ).order_by(AdminLog.timestamp.desc()).first()
    
    if recent_info_flag:
        return jsonify({
            'info_flag_detected': True,
            'timestamp': recent_info_flag.timestamp.isoformat(),
            'flag_id': recent_info_flag.id
        })
    else:
        return jsonify({'info_flag_detected': False})

@main.route('/api/clear_info_flag/<int:flag_id>', methods=['POST'])
@require_api_key
def clear_info_flag(flag_id):
    """API để ESP32 xóa INFO flag sau khi đã hiển thị"""
    flag = AdminLog.query.get_or_404(flag_id)
    # Đổi action để không còn được detect nữa
    flag.action = 'info_flag_displayed'
    db.session.commit()
    
    return jsonify({'success': True})

    """API đặc biệt để Pi button gửi flag cho ESP32 sync"""
    schedule_id = request.json.get('schedule_id')
    user_id = request.json.get('user_id')
    
    schedule = Schedule.query.get_or_404(schedule_id)
    
    # Kiểm tra xem schedule có phải của user này không
    if schedule.user_id != user_id:
        return jsonify({'error': 'Không có quyền truy cập'}), 403
    
    # Tạo history entry với flag đặc biệt cho Pi button
    pi_history_entry = MedicineHistory(
        schedule_id=schedule_id,
        timestamp=datetime.now(),
        status='taken',
        notes='pi_button_confirmed'  # Flag đặc biệt để ESP32 detect
    )
    db.session.add(pi_history_entry)
    db.session.commit()
    
    return jsonify({'success': True, 'pi_confirmation_id': pi_history_entry.id})

@main.route('/api/medicine/<int:medicine_id>', methods=['GET'])
@require_api_key
def get_medicine(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    return jsonify({
        'id': medicine.id,
        'name': medicine.name,
        'compartment_number': medicine.compartment_number,
        'quantity': medicine.quantity,
        'dosage': medicine.dosage,
        'notes': medicine.notes
    })

@main.route('/api/update_quantity', methods=['POST'])
@require_api_key
def update_quantity():
    medicine_id = request.json.get('medicine_id')
    quantity_change = request.json.get('quantity_change')
    
    if not all([medicine_id, quantity_change]):
        return jsonify({'error': 'Missing required fields'}), 400
        
    medicine = Medicine.query.get_or_404(medicine_id)
    old_quantity = medicine.quantity
    medicine.quantity = max(0, old_quantity + quantity_change)
    
    if medicine.quantity <= medicine.min_quantity:
        # TODO: Send notification about low quantity
        pass
        
    db.session.commit()
    return jsonify({
        'success': True,
        'new_quantity': medicine.quantity
    })

@main.route('/api/verify_compartment', methods=['POST'])
@require_api_key
def verify_compartment():
    compartment = request.json.get('compartment')
    medicine_id = request.json.get('medicine_id')
    
    if not all([compartment, medicine_id]):
        return jsonify({'error': 'Missing required fields'}), 400
        
    medicine = Medicine.query.get_or_404(medicine_id)
    if medicine.compartment_number != compartment:
        return jsonify({'error': 'Compartment mismatch'}), 400
        
    return jsonify({'success': True})

@main.route('/api/user_profile/<int:user_id>', methods=['GET'])
@require_api_key
def get_user_profile(user_id):
    """API endpoint để ESP32 lấy user profile + thống kê tuần"""
    user = User.query.get_or_404(user_id)
    
    # Tính thống kê tuần này
    from datetime import timedelta
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Lấy lịch sử uống thuốc tuần này
    week_history = MedicineHistory.query.join(Schedule).filter(
        Schedule.user_id == user_id,
        MedicineHistory.timestamp >= week_start,
        MedicineHistory.timestamp <= week_end,
        MedicineHistory.status == 'taken'
    ).count()
    
    # Tổng số lịch thuốc active
    total_schedules = Schedule.query.filter_by(user_id=user_id, active=True).count()
    
    # Compliance rate tuần này
    expected_doses_week = total_schedules * 7  # 7 ngày
    compliance_rate = (week_history / expected_doses_week * 100) if expected_doses_week > 0 else 0
    
    # Thuốc hôm nay
    today_start = datetime.combine(now.date(), datetime.min.time())
    today_end = datetime.combine(now.date(), datetime.max.time())
    
    taken_today = MedicineHistory.query.join(Schedule).filter(
        Schedule.user_id == user_id,
        MedicineHistory.timestamp >= today_start,
        MedicineHistory.timestamp <= today_end,
        MedicineHistory.status == 'taken'
    ).count()
    
    # Lấy danh sách thuốc trong các ngăn
    medicines = Medicine.query.filter_by(user_id=user_id).all()
    medicine_list = []
    for med in medicines:
        medicine_list.append({
            'name': med.name,
            'compartment': med.compartment_number,
            'quantity': med.quantity,
            'low_stock': med.quantity <= med.min_quantity
        })
    
    return jsonify({
        'user_info': {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name or user.username,
            'age': user.age or 'N/A',
            'email': user.email,
            'phone': user.phone or 'N/A',
            'user_type': user.user_type or 'patient'
        },
        'weekly_stats': {
            'doses_taken': week_history,
            'expected_doses': expected_doses_week,
            'compliance_rate': round(compliance_rate, 1),
            'taken_today': taken_today
        },
        'medicines': medicine_list,
        'system_info': {
            'total_medicines': len(medicine_list),
            'low_stock_count': sum(1 for m in medicine_list if m['low_stock']),
            'active_schedules': total_schedules
        }
    })

def get_current_schedules(user_id):
    current_time = datetime.now()
    current_weekday = current_time.weekday()  # 0=Monday, 6=Sunday
    weekday_mapping = {
        0: 'monday',
        1: 'tuesday',
        2: 'wednesday',
        3: 'thursday',
        4: 'friday',
        5: 'saturday',
        6: 'sunday'
    }
    current_day = weekday_mapping[current_weekday]
    
    today_schedules = Schedule.query.filter_by(
        user_id=user_id,
        active=True
    ).all()
    
    current_schedules = []
    for schedule in today_schedules:
        # Kiem tra xem hom nay co trong danh sach ngay khong
        import json
        try:
            schedule_days = json.loads(schedule.days) if isinstance(schedule.days, str) else schedule.days
        except:
            schedule_days = []
            
        if current_day not in schedule_days:
            continue
            
        schedule_time = datetime.strptime(schedule.time, '%H:%M').time()
        schedule_datetime = datetime.combine(current_time.date(), schedule_time)
        
        # Kiem tra xem da uong chua trong ngay hom nay
        today_start = datetime.combine(current_time.date(), datetime.min.time())
        today_end = datetime.combine(current_time.date(), datetime.max.time())
        
        existing_history = MedicineHistory.query.filter(
            MedicineHistory.schedule_id == schedule.id,
            MedicineHistory.timestamp >= today_start,
            MedicineHistory.timestamp <= today_end,
            MedicineHistory.status == 'taken'
        ).first()
        
        # Neu da uong roi thi khong hien thi nua
        if existing_history:
            continue
        
        # Kiem tra thoi gian (trong vong 2 phut)
        if abs((schedule_datetime - current_time).total_seconds()) <= 120:
            medicine = Medicine.query.get(schedule.medicine_id)
            if medicine:
                current_schedules.append({
                    'schedule_id': schedule.id,
                    'medicine_id': medicine.id,
                    'medicine_name': medicine.name,
                    'compartment_number': medicine.compartment_number,
                    'time': schedule.time,
                    'dosage': medicine.dosage,
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

@main.route('/api/check_confirmation_status/<int:user_id>', methods=['GET'])
@require_api_key
def check_confirmation_status(user_id):
    """API endpoint để ESP32 kiểm tra trạng thái confirmation từ Pi button"""
    # Tìm confirmation gần nhất trong vòng 5 phút
    from datetime import timedelta
    recent_time = datetime.now() - timedelta(minutes=5)
    
    recent_confirmation = MedicineHistory.query.join(Schedule).filter(
        Schedule.user_id == user_id,
        MedicineHistory.timestamp >= recent_time,
        MedicineHistory.status == 'taken',
        MedicineHistory.notes == 'pi_button_confirmed'  # Flag đặc biệt cho Pi button
    ).order_by(MedicineHistory.timestamp.desc()).first()
    
    if recent_confirmation:
        schedule = Schedule.query.get(recent_confirmation.schedule_id)
        medicine = Medicine.query.get(schedule.medicine_id)
        
        return jsonify({
            'confirmed': True,
            'timestamp': recent_confirmation.timestamp.isoformat(),
            'medicine_name': medicine.name,
            'compartment_number': medicine.compartment_number,
            'confirmation_id': recent_confirmation.id
        })
    else:
        return jsonify({'confirmed': False})

@main.route('/api/clear_confirmation/<int:confirmation_id>', methods=['POST'])
@require_api_key
def clear_confirmation(confirmation_id):
    """API để ESP32 xóa confirmation sau khi đã hiển thị"""
    confirmation = MedicineHistory.query.get_or_404(confirmation_id)
    # Đổi notes để không còn được detect nữa
    confirmation.notes = 'pi_button_confirmed_displayed'
    db.session.commit()
    
    return jsonify({'success': True})

# ============ SYSTEM POWER CONTROL API ============

@main.route('/api/system_status', methods=['GET'])
@require_api_key
def get_system_status():
    """API để ESP32 kiểm tra trạng thái hệ thống (bật/tắt)"""
    try:
        # Execute raw SQL query to get system status
        result = db.session.execute(
            "SELECT system_enabled, updated_at FROM system_control ORDER BY id DESC LIMIT 1"
        ).fetchone()
        
        if result:
            return jsonify({
                'system_enabled': bool(result[0]),
                'last_updated': result[1].isoformat() if result[1] else None,
                'status': 'active' if result[0] else 'disabled'
            })
        else:
            # Nếu chưa có record nào, tạo mặc định
            db.session.execute("""
                INSERT INTO system_control (system_enabled, updated_by, notes)
                VALUES (TRUE, 'auto_init', 'Auto-created system status')
            """)
            db.session.commit()
            
            return jsonify({
                'system_enabled': True,
                'status': 'active',
                'last_updated': datetime.now().isoformat()
            })
            
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@main.route('/api/system_control', methods=['POST'])
@require_api_key
def update_system_control():
    """API để Raspberry Pi cập nhật trạng thái hệ thống (bật/tắt)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        action = data.get('action')  # 'enable' hoặc 'disable'
        source = data.get('source', 'pi_button')  # nguồn thay đổi
        notes = data.get('notes', '')
        
        if action not in ['enable', 'disable']:
            return jsonify({'error': 'Invalid action. Use "enable" or "disable"'}), 400
        
        system_enabled = True if action == 'enable' else False
        
        # Cập nhật trạng thái trong database
        result = db.session.execute("""
            UPDATE system_control
            SET system_enabled = :enabled, updated_at = :updated_at, updated_by = :updated_by, notes = :notes
            WHERE id = 1
        """, {
            'enabled': system_enabled,
            'updated_at': datetime.now(),
            'updated_by': source,
            'notes': f'{action.title()} by {source}. {notes}'
        })
        
        if result.rowcount == 0:
            # Nếu chưa có record, tạo mới
            db.session.execute("""
                INSERT INTO system_control (id, system_enabled, updated_by, notes)
                VALUES (1, :enabled, :updated_by, :notes)
            """, {
                'enabled': system_enabled,
                'updated_by': source,
                'notes': f'{action.title()} by {source}. {notes}'
            })
        
        db.session.commit()
        
        # Log action cho admin
        log_entry = AdminLog(
            admin_id=1,  # System user
            action=f'system_{action}',
            target_type='system_control',
            target_id=1,
            details=f'System {action}d by {source}. {notes}',
            timestamp=datetime.now()
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'action': action,
            'system_enabled': system_enabled,
            'timestamp': datetime.now().isoformat(),
            'message': f'System successfully {action}d'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to update system status: {str(e)}'}), 500

@main.route('/api/power_button_press', methods=['POST'])
@require_api_key
def handle_power_button_press():
    """API đặc biệt để xử lý nhấn nút power từ Raspberry Pi"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        button_duration = data.get('duration', 0)  # thời gian nhấn nút (giây)
        
        # Lấy trạng thái hiện tại
        result = db.session.execute(
            "SELECT system_enabled FROM system_control ORDER BY id DESC LIMIT 1"
        ).fetchone()
        
        current_status = result[0] if result else True
        
        # Toggle trạng thái
        new_status = not current_status
        action = 'enable' if new_status else 'disable'
        
        # Cập nhật database
        update_result = db.session.execute("""
            UPDATE system_control
            SET system_enabled = :enabled, updated_at = :updated_at, updated_by = :updated_by, notes = :notes
            WHERE id = 1
        """, {
            'enabled': new_status,
            'updated_at': datetime.now(),
            'updated_by': f'power_button_user_{user_id}',
            'notes': f'Power button pressed for {button_duration}s - {action}d system'
        })
        
        if update_result.rowcount == 0:
            db.session.execute("""
                INSERT INTO system_control (id, system_enabled, updated_by, notes)
                VALUES (1, :enabled, :updated_by, :notes)
            """, {
                'enabled': new_status,
                'updated_by': f'power_button_user_{user_id}',
                'notes': f'Power button pressed - {action}d system'
            })
        
        db.session.commit()
        
        # Log cho admin
        log_entry = AdminLog(
            admin_id=user_id,
            action=f'power_button_{action}',
            target_type='system_control',
            target_id=1,
            details=f'Power button pressed by user {user_id} - System {action}d',
            timestamp=datetime.now()
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'previous_status': current_status,
            'new_status': new_status,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'message': f'Power button processed - System {action}d'
        })
        
    except Exception as e:
        return jsonify({'error': f'Power button processing failed: {str(e)}'}), 500

@main.route('/admin/system-power')
@admin_required
def system_power_control():
    """Admin interface để kiểm soát power system"""
    try:
        # Lấy trạng thái hiện tại
        result = db.session.execute(
            "SELECT * FROM system_control ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        
        # Convert result to dict-like object if exists
        current_status = None
        if result:
            current_status = {
                'system_enabled': result[1],
                'updated_at': result[2],
                'updated_by': result[3],
                'notes': result[4]
            }
        
        # Lấy lịch sử thay đổi gần đây
        recent_logs = AdminLog.query.filter(
            AdminLog.target_type == 'system_control'
        ).order_by(AdminLog.timestamp.desc()).limit(20).all()
        
        return render_template('admin/system_power.html',
                             current_status=current_status,
                             recent_logs=recent_logs,
                             User=User)
    except Exception as e:
        flash(f'Lỗi khi tải trang quản lý power: {str(e)}', 'error')
        return redirect(url_for('main.admin_logs'))