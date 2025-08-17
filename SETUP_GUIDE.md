# 🚀 AI-FOR-ELDER - Setup Guide

## 📋 Yêu cầu hệ thống

- **Python 3.8+**
- **MySQL/MariaDB**
- **Git**
- **Gmail account** (cho email notifications)

## ⚡ Cài đặt nhanh

### 1. Clone repository
```bash
git clone https://github.com/yourusername/AI-FOR-ELDER.git
cd AI-FOR-ELDER
```

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 3. Cấu hình database
```bash
# Tạo database MySQL
mysql -u root -p
CREATE DATABASE elder_project;
EXIT;

# Khởi tạo database
python init_db.py
```

### 4. Cấu hình email thông báo
```bash
# Copy file config template
cp config.example.py config.py
```

Sửa file `config.py`:
```python
# Thay bằng thông tin Gmail thật
MAIL_USERNAME = 'your_email@gmail.com'
MAIL_PASSWORD = 'your_gmail_app_password'  # Không phải password thường!
```

### 5. Tạo Gmail App Password

1. Vào **Google Account Settings** → **Security**
2. Bật **2-Step Verification**
3. Tạo **App Password**:
   - Chọn app: **Mail**
   - Copy password (VD: `abcd efgh ijkl mnop`)
   - Paste vào `MAIL_PASSWORD`

### 6. Chạy ứng dụng
```bash
python app.py
```

Truy cập: http://localhost:5000

## 🔐 Bảo mật

### Files cần ignore khi push GitHub:
- ✅ `config.py` - Đã được ignore trong `.gitignore`
- ✅ Credentials nhạy cảm khác

### Quy trình an toàn:
1. **KHÔNG BAO GIỜ** push `config.py` lên GitHub
2. Chỉ push `config.example.py` (template)
3. Mỗi developer tự tạo `config.py` từ template

## 👨‍💻 Tài khoản mặc định

### Super Admin:
- **Username:** `admin`
- **Password:** `admin123`

### Test User:
- **Username:** `testuser`
- **Password:** `password123`

## 🏥 Workflow hệ thống

### 1. Admin tạo user:
```
Admin login → User Management → Tạo user mới
→ Nhập email người thân → Save
```

### 2. Quản lý thuốc:
```
Medicine Management → Add Medicine → Compartment 1-4
Schedule Management → Tạo lịch uống thuốc
```

### 3. Thông báo khẩn cấp:
```
Raspberry Pi monitor → 15 phút không xác nhận
→ Email tự động gửi tới người thân 📧
```

## 🧪 Test email notifications

1. **Vào Admin Panel** → **User Management**
2. **Click "Test Email"**
3. **Nhập email test** → **Send**
4. **Check inbox** → Should receive test email ✅

## 🔧 Troubleshooting

### Email không gửi được:
- ✅ Check Gmail App Password
- ✅ Đảm bảo 2-Step Verification ON
- ✅ Check `MAIL_USERNAME` và `MAIL_PASSWORD`

### Database connection error:
- ✅ Check MySQL service đang chạy
- ✅ Verify database credentials trong `config.py`
- ✅ Database `elder_project` đã được tạo

### Import errors:
- ✅ Reinstall requirements: `pip install -r requirements.txt`
- ✅ Check Python version: `python --version`

## 📱 Hardware Setup (Optional)

### Raspberry Pi 4:
- Kết nối GPIO pins cho servo motors
- Chạy `rpi_handler2.py` để điều khiển hardware

### ESP32-2432S028R:
- Upload Arduino code từ folder `esp32_medicine_touch_rtos_power/`
- Kết nối WiFi để sync với server

## 🎯 Demo cho presentation

1. **Login Admin** → Tạo user với email người thân
2. **Tạo medicine schedule** 
3. **Simulate missed dose** → Show email notification
4. **Show admin dashboard** với logs và management

---

**🏆 Project ready for production!**