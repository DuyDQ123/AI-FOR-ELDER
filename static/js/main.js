// Kiểm tra và yêu cầu quyền thông báo
document.addEventListener('DOMContentLoaded', function() {
    if ('Notification' in window) {
        Notification.requestPermission();
    }
    
    // Tự động ẩn flash messages sau 3 giây
    const flashMessages = document.querySelectorAll('.custom-alert');
    flashMessages.forEach(message => {
        // Thêm class show sau 100ms để trigger animation
        setTimeout(() => {
            message.classList.add('show');
        }, 100);

        // Tự động ẩn sau 3 giây
        setTimeout(() => {
            message.classList.remove('show');
            setTimeout(() => {
                message.remove();
            }, 500);
        }, 3000);
    });

    // Xử lý nút đóng
    document.querySelectorAll('.alert .btn-close').forEach(button => {
        button.addEventListener('click', function() {
            const alert = this.closest('.custom-alert');
            alert.classList.remove('show');
            setTimeout(() => {
                alert.remove();
            }, 500);
        });
    });
});

// Hàm hiển thị thông báo nhắc uống thuốc
function showMedicineReminder(medicineName, time) {
    // Hiển thị toast trong trang
    const toastEl = document.querySelector('.toast');
    const toast = new bootstrap.Toast(toastEl);
    toastEl.querySelector('.toast-body').textContent = 
        `Đã đến giờ uống thuốc ${medicineName}!`;
    toast.show();

    // Hiển thị thông báo trình duyệt
    if (Notification.permission === 'granted') {
        new Notification('Nhắc uống thuốc', {
            body: `Đã đến giờ uống thuốc ${medicineName}!`,
            icon: '/static/images/medicine-icon.png'
        });
    }

    // Phát âm thanh nhắc nhở
    playRemindSound();
}

// Phát âm thanh nhắc nhở
function playRemindSound() {
    const audio = new Audio('/static/sounds/reminder.mp3');
    audio.play();
}

// Kiểm tra lịch uống thuốc
function checkMedicineSchedule() {
    const now = new Date();
    const currentDay = now.toLocaleDateString('vi-VN', { weekday: 'long' });
    const currentTime = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

    // Lấy dữ liệu lịch từ localStorage hoặc API
    fetch('/check_schedule')
        .then(response => response.json())
        .then(schedules => {
            schedules.forEach(schedule => {
                if (schedule.days.includes(currentDay) && schedule.time === currentTime) {
                    showMedicineReminder(schedule.medicine_name, schedule.time);
                }
            });
        });
}

// Kiểm tra lịch mỗi phút
setInterval(checkMedicineSchedule, 60000);
checkMedicineSchedule(); // Kiểm tra ngay khi tải trang

// Xác nhận đã uống thuốc
function confirmMedicineTaken(scheduleId) {
    fetch('/confirm_medicine', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ scheduleId: scheduleId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Cập nhật UI
            const button = document.querySelector(`[data-schedule-id="${scheduleId}"]`);
            button.classList.remove('btn-success');
            button.classList.add('btn-secondary');
            button.textContent = 'Đã uống';
            button.disabled = true;
        }
    });
}

// Xử lý form thêm thuốc
if (document.querySelector('#addMedicineForm')) {
    document.querySelector('#addMedicineForm').addEventListener('submit', function(e) {
        const nameInput = document.querySelector('#name');
        if (nameInput.value.trim() === '') {
            e.preventDefault();
            alert('Vui lòng nhập tên thuốc!');
            return;
        }
    });
}

// Xử lý form lịch uống thuốc
if (document.querySelector('#addScheduleForm')) {
    document.querySelector('#addScheduleForm').addEventListener('submit', function(e) {
        const daysChecked = document.querySelectorAll('input[name="days[]"]:checked');
        if (daysChecked.length === 0) {
            e.preventDefault();
            alert('Vui lòng chọn ít nhất một ngày trong tuần!');
            return;
        }
    });
}

// Kết nối với ESP32 (sẽ thêm sau)
let espConnection = null;

// Hàm kết nối với ESP32
function connectToESP32() {
    // Sẽ thêm code kết nối WebSocket với ESP32 sau
    console.log('Connecting to ESP32...');
}

// Hàm gửi lệnh đến ESP32
function sendCommandToESP32(command) {
    // Sẽ thêm code gửi lệnh đến ESP32 sau
    console.log('Sending command to ESP32:', command);
}

// Auto-save form data
function autoSaveFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    // Restore saved data
    const savedData = localStorage.getItem(`formData_${formId}`);
    if (savedData) {
        const data = JSON.parse(savedData);
        Object.keys(data).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) input.value = data[key];
        });
    }

    // Save data on input change
    form.addEventListener('input', function(e) {
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => data[key] = value);
        localStorage.setItem(`formData_${formId}`, JSON.stringify(data));
    });
}