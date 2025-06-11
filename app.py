from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime, timedelta
import platform

app = Flask(__name__)
app.secret_key = 'your-secret-key'

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

# Đường dẫn đến file JSON
DATA_FILE = 'data/medicine.json'

def load_medicine_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'medicines': [], 'schedules': [], 'history': []}

def save_medicine_data(data):
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Routes chính
@app.route('/')
def index():
    data = load_medicine_data()
    current_schedules = get_today_schedules(data)
    return render_template('index.html', 
                         medicines=data['medicines'], 
                         schedules=current_schedules)

@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    if request.method == 'POST':
        data = load_medicine_data()
        new_medicine = {
            'id': len(data['medicines']) + 1,
            'name': request.form['name'],
            'description': request.form['description'],
            'notes': request.form['notes'],
            'image': request.form['image'] if 'image' in request.form else ''
        }
        data['medicines'].append(new_medicine)
        save_medicine_data(data)
        return redirect(url_for('index'))
    return render_template('add_medicine.html')

@app.route('/add_schedule', methods=['GET', 'POST'])
def add_schedule():
    if request.method == 'POST':
        data = load_medicine_data()
        new_schedule = {
            'id': len(data['schedules']) + 1,
            'medicine_id': int(request.form['medicine_id']),
            'time': request.form['time'],
            'days': request.form.getlist('days[]'),
            'period': request.form['period'],
            'active': True
        }
        data['schedules'].append(new_schedule)
        save_medicine_data(data)
        return redirect(url_for('index'))
    data = load_medicine_data()
    return render_template('add_schedule.html', medicines=data['medicines'])

@app.route('/reports')
def reports():
    data = load_medicine_data()
    weekly_stats = calculate_weekly_stats(data)
    return render_template('reports.html', 
                         medicines=data['medicines'], 
                         schedules=data['schedules'],
                         stats=weekly_stats)

# API Endpoints
@app.route('/api/check_schedule', methods=['GET'])
def check_schedule():
    data = load_medicine_data()
    current_schedules = get_current_schedules(data)
    return jsonify(current_schedules)

@app.route('/api/confirm_medicine', methods=['POST'])
def confirm_medicine():
    data = load_medicine_data()
    schedule_id = request.json.get('schedule_id')
    
    # Lưu lịch sử uống thuốc
    history_entry = {
        'schedule_id': schedule_id,
        'timestamp': datetime.now().isoformat(),
        'status': 'taken'
    }
    data['history'].append(history_entry)
    save_medicine_data(data)
    return jsonify({'success': True})

@app.route('/api/medicines', methods=['GET'])
def get_medicines():
    data = load_medicine_data()
    return jsonify(data['medicines'])

# Helper functions
def get_today_schedules(data):
    today = datetime.now().strftime('%A')
    return [
        schedule for schedule in data['schedules']
        if today in schedule['days'] and schedule['active']
    ]

def get_current_schedules(data):
    current_time = datetime.now()
    today_schedules = get_today_schedules(data)
    
    current_schedules = []
    for schedule in today_schedules:
        schedule_time = datetime.strptime(schedule['time'], '%H:%M').time()
        schedule_datetime = datetime.combine(current_time.date(), schedule_time)
        
        # Kiểm tra thời gian trong khoảng 5 phút
        if abs((schedule_datetime - current_time).total_seconds()) <= 300:
            medicine = next(
                (m for m in data['medicines'] if m['id'] == schedule['medicine_id']),
                None
            )
            if medicine:
                current_schedules.append({
                    'schedule_id': schedule['id'],
                    'medicine_name': medicine['name'],
                    'time': schedule['time'],
                    'notes': medicine['notes']
                })
    
    return current_schedules

def calculate_weekly_stats(data):
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    week_history = [
        entry for entry in data['history']
        if datetime.fromisoformat(entry['timestamp']) >= week_start
    ]
    
    total_scheduled = len(get_today_schedules(data)) * 7
    taken = len([e for e in week_history if e['status'] == 'taken'])
    missed = total_scheduled - taken
    
    return {
        'taken': taken,
        'missed': missed,
        'compliance_rate': (taken / total_scheduled * 100) if total_scheduled > 0 else 0
    }

if __name__ == '__main__':
    # Khởi tạo dữ liệu
    if not os.path.exists(DATA_FILE):
        save_medicine_data({'medicines': [], 'schedules': [], 'history': []})
    
    try:
        # Chạy Flask server
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        # Cleanup GPIO nếu đang chạy trên Raspberry Pi
        if rpi_handler:
            rpi_handler.cleanup()