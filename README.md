# Hệ Thống Nhắc Thuốc Thông Minh

Hệ thống nhắc uống thuốc thông minh sử dụng Raspberry Pi và Flask, giúp người cao tuổi quản lý việc uống thuốc hiệu quả.

## Tính Năng Chính

- 📅 Lập lịch uống thuốc theo tuần/ngày/giờ
- 🔔 Nhắc nhở thông qua âm thanh và màn hình OLED
- 📱 Giao diện web quản lý thuốc và lịch uống
- 📊 Báo cáo và thống kê việc uống thuốc
- 🤖 Hỗ trợ xác nhận bằng nút nhấn
- 📷 Quét mã QR để nhận diện thuốc

## Yêu Cầu Phần Cứng

- Raspberry Pi (3B+ hoặc 4 khuyến nghị)
- Màn hình OLED SSD1306 (I2C)
- USB Camera (cho quét mã QR)
- Loa hoặc buzzer (kết nối qua jack 3.5mm)
- 4 nút nhấn
- Dây jumper
- Thẻ nhớ SD (ít nhất 8GB)
- Nguồn điện 5V/2.5A

## Sơ Đồ Kết Nối GPIO

```
GPIO Connections:
┌────────────────────────────────────────────┐
│ GPIO2 (SDA)    → OLED SDA                 │
│ GPIO3 (SCL)    → OLED SCL                 │
│ GPIO18         → Nút xác nhận uống thuốc  │
│ GPIO23         → Nút thuốc kế tiếp        │
│ GPIO17         → Nút xem DS thuốc         │
│ GPIO27         → Nút cài đặt              │
│ 3.3V           → OLED VCC                 │
│ GND            → OLED GND + Nút GND       │
└────────────────────────────────────────────┘
```

## Cài Đặt Hệ Thống

### 1. Cài Đặt Raspberry Pi OS
```bash
# Tải Raspberry Pi OS và ghi vào thẻ SD
# Kích hoạt I2C trong raspi-config
sudo raspi-config
# Chọn: Interface Options -> I2C -> Enable
```

### 2. Cài Đặt Các Gói Phụ Thuộc
```bash
# Cập nhật hệ thống
sudo apt update
sudo apt upgrade -y

# Cài đặt các gói cần thiết
sudo apt install -y python3-pip python3-dev python3-smbus i2c-tools
sudo apt install -y libsdl2-mixer-2.0-0  # Cho âm thanh

# Cài đặt thư viện cho QR code
sudo apt install -y libzbar0 libzbar-dev   # Cho pyzbar
sudo apt install -y python3-opencv         # Cho OpenCV
sudo apt install -y v4l-utils             # Cho USB camera

# Kiểm tra camera
v4l2-ctl --list-devices                   # Liệt kê camera
```

### 3. Cài Đặt Môi Trường Python
```bash
# Clone repository
git clone https://github.com/yourusername/smart-medicine-reminder
cd smart-medicine-reminder

# Cài đặt dependencies
pip3 install -r requirements.txt
```

### 4. Kiểm Tra USB Camera
```bash
# Kiểm tra camera được nhận dạng
ls /dev/video*

# Test camera
sudo apt install -y fswebcam
fswebcam test.jpg
```

### 5. Cấu Hình Âm Thanh
```bash
# Kiểm tra đầu ra âm thanh
aplay -l

# Đặt đầu ra mặc định (thường là headphone)
sudo amixer cset numid=3 1
```

## Chạy Ứng Dụng

### 1. Khởi Động Server
```bash
# Từ thư mục dự án
python3 app.py
```

### 2. Truy Cập Web Interface
- Truy cập từ máy tính cùng mạng LAN:
```
http://<raspberry_pi_ip>:5000
```

## Sử Dụng

### 1. Thêm Thuốc Mới
- Truy cập "Thêm Thuốc" trên web
- Nhập thông tin thuốc (tên, công dụng, lưu ý)
- Tạo và in mã QR cho thuốc mới

### 2. Đặt Lịch Uống Thuốc
- Vào mục "Đặt Lịch"
- Chọn thuốc từ danh sách
- Đặt thời gian và các ngày trong tuần
- Lưu lịch uống thuốc

### 3. Tương Tác với Thiết Bị
- Nút 1 (GPIO18): Xác nhận đã uống thuốc
- Nút 2 (GPIO23): Xem thuốc tiếp theo
- Nút 3 (GPIO17): Xem danh sách thuốc
- Nút 4 (GPIO27): Bật/tắt quét mã QR

### 4. Quét Mã QR Thuốc
- Nhấn nút 4 để bật chế độ quét QR
- Đưa mã QR thuốc vào camera
- Hệ thống sẽ tự động nhận diện và xác thực thuốc

## Xử Lý Sự Cố

### Camera Không Hoạt Động
1. Kiểm tra kết nối USB:
```bash
lsusb
```
2. Kiểm tra thiết bị video:
```bash
ls /dev/video*
v4l2-ctl --list-devices
```
3. Cấp quyền truy cập:
```bash
sudo usermod -a -G video $USER
```

### Mã QR Không Được Nhận Diện
1. Kiểm tra ánh sáng đầy đủ
2. Đảm bảo mã QR nằm trong tầm nhìn camera
3. Kiểm tra log lỗi:
```bash
tail -f /var/log/syslog
```

### Các Lỗi Khác
- Màn hình OLED không hiển thị:
```bash
sudo i2cdetect -y 1
```
- Âm thanh không hoạt động:
```bash
alsamixer
```
- Nút nhấn không phản hồi:
```bash
sudo gpio readall
```

## Bảo Trì

### Sao Lưu Dữ Liệu
```bash
cp -r data/ backup/
```

### Cập Nhật Phần Mềm
```bash
git pull
pip3 install -r requirements.txt --upgrade
sudo systemctl restart medicine-reminder
```

## Giấy Phép

Distributed under the MIT License. See `LICENSE` for more information.

## Liên Hệ

Your Name - email@example.com

Project Link: [https://github.com/yourusername/smart-medicine-reminder](https://github.com/yourusername/smart-medicine-reminder)