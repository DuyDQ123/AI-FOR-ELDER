# Hệ Thống Nhắc Thuốc Thông Minh

Hệ thống nhắc uống thuốc thông minh sử dụng Raspberry Pi và Flask, giúp người cao tuổi quản lý việc uống thuốc hiệu quả và an toàn.

## Tính Năng Chính

### 1. Nhắc Thuốc Thông Minh
- 📅 Lập lịch theo tuần/ngày/giờ (sáng/trưa/chiều/tối)
- 🔔 Nhắc nhở qua âm thanh và màn hình OLED
- 🔄 Tự động lặp lại nhắc nhở nếu chưa xác nhận
- ✅ Tự động tắt khi đã xác nhận uống thuốc

### 2. Quản Lý Dữ Liệu
- 📱 Giao diện web đa nền tảng
- ➕ Thêm/Sửa/Xóa lịch uống thuốc
- 📝 Quản lý danh sách thuốc (tên, công dụng, hình ảnh)
- 📊 Báo cáo tuần về việc uống thuốc
- ⚠️ Cảnh báo cho người chăm sóc

### 3. Phân Tích & AI
- 📈 Phân tích hành vi uống thuốc
- 💡 Gợi ý điều chỉnh lịch uống
- 👤 Nhận diện khuôn mặt người dùng
- 📷 Quét mã QR nhận diện thuốc

### 4. Tính Năng Phần Cứng
- 📍 Tích hợp NFC cho nhận diện thuốc
- 🌡️ Theo dõi nhiệt độ bảo quản
- 🔐 Tự động điều khiển tủ thuốc
- 🗣️ Tích hợp trợ lý giọng nói

## Yêu Cầu Hệ Thống

### Phần Cứng
- Raspberry Pi (3B+ hoặc 4)
- Màn hình OLED SSD1306
- Module âm thanh PCM5102
- Camera USB
- 4 nút nhấn
- Các cảm biến (tùy chọn)

### Phần Mềm
- Python 3.7+
- Flask Framework
- SQLite/PostgreSQL
- OpenCV
- Các thư viện hỗ trợ

## Cài Đặt

### 1. Chuẩn Bị Môi Trường
```bash
# Cập nhật hệ thống
sudo apt update && sudo apt upgrade -y

# Cài đặt các gói cần thiết
sudo apt install -y python3-pip python3-dev python3-venv
sudo apt install -y libsdl2-mixer-2.0-0 libzbar0
```

### 2. Cài Đặt Ứng Dụng
```bash
# Tạo môi trường ảo
python3 -m venv venv
source venv/bin/activate  # Linux
venv\Scripts\activate     # Windows

# Cài đặt dependencies
pip install -r requirements.txt

# Khởi tạo cơ sở dữ liệu
flask db upgrade
```

### 3. Cấu Hình
```bash
# Tạo file .env
cp .env.example .env

# Chỉnh sửa các thông số trong .env
nano .env
```

### 4. Chạy Ứng Dụng
```bash
# Chạy ứng dụng
python app.py

# Truy cập web interface
http://localhost:5000
```

## Bảo Mật

### Tính Năng Bảo Mật
- 🔐 Xác thực người dùng
- 👥 Phân quyền (bệnh nhân/người chăm sóc/admin)
- 🔒 Bảo vệ API bằng key
- 📡 Hỗ trợ HTTPS
- 🔑 Mã hóa dữ liệu nhạy cảm

### Đăng Nhập Hệ Thống
- Tạo tài khoản mới tại /auth/register
- Đăng nhập tại /auth/login
- Quản lý thông tin tại /auth/profile

## Hỗ Trợ

### Xử Lý Sự Cố
- Kiểm tra logs trong thư mục /logs
- Xem status hệ thống tại /status
- Báo lỗi qua GitHub Issues

### Liên Hệ
- Email: support@example.com
- Website: http://example.com
- GitHub: http://github.com/example

## Cập Nhật

### Phiên Bản Mới
```bash
# Pull code mới
git pull

# Cập nhật dependencies
pip install -r requirements.txt --upgrade

# Cập nhật database
flask db upgrade

# Khởi động lại service
sudo systemctl restart medicine-reminder
```

#DuyCode <3