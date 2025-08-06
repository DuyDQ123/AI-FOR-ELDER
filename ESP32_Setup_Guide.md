# 📱 Hướng Dẫn Cài Đặt ESP32 Màn Hình TFT cho Hệ Thống Nhắc Thuốc

## 🔧 **1. Thiết Bị Cần Thiết**
- **ESP32-2432S028R** (ESP32 với màn hình TFT 2.8 inch 240x320)
- **Cáp USB-C** để nạp code
- **WiFi Router** để kết nối internet

## 💻 **2. Cài Đặt Arduino IDE**

### **Bước 1: Tải Arduino IDE**
1. Tải từ: https://www.arduino.cc/en/software
2. Cài đặt phiên bản mới nhất

### **Bước 2: Thêm ESP32 Board**
1. Mở Arduino IDE
2. File → Preferences
3. Thêm URL vào "Additional Boards Manager URLs":
   ```
   https://dl.espressif.com/dl/package_esp32_index.json
   ```
4. Tools → Board → Boards Manager
5. Tìm "ESP32" và cài đặt "ESP32 by Espressif Systems"

### **Bước 3: Chọn Board**
1. Tools → Board → ESP32 Arduino → "ESP32 Dev Module"
2. Tools → Port → Chọn COM port của ESP32

## 📚 **3. Cài Đặt Thư Viện**

### **Cài đặt qua Library Manager:**
1. Tools → Manage Libraries
2. Tìm và cài đặt các thư viện sau:

```
- TFT_eSPI (by Bodmer) - Phiên bản mới nhất
- ArduinoJson (by Benoit Blanchon) - Phiên bản 6.x
- WiFi (built-in với ESP32)
- HTTPClient (built-in với ESP32)
```

## ⚙️ **4. Cấu Hình TFT_eSPI**

### **Bước 1: Tìm thư mục TFT_eSPI**
- Windows: `C:\Users\[Username]\Documents\Arduino\libraries\TFT_eSPI`
- Tìm file `User_Setup.h`

### **Bước 2: Sửa file User_Setup.h**
Mở file `User_Setup.h` và thêm cấu hình cho ESP32-2432S028R:

```cpp
// Thêm dòng này vào đầu file
#define ILI9341_DRIVER

// Uncomment để sử dụng hardware SPI
#define TFT_MOSI 23
#define TFT_SCLK 18
#define TFT_CS   15  // Chip select control pin
#define TFT_DC   2   // Data Command control pin
#define TFT_RST  4   // Reset pin (could connect to RST pin)
#define TFT_MISO 19  // (T_DO) Data out pin

// Touch screen pins
#define TOUCH_CS 33

// Màu sắc
#define TFT_BLACK       0x0000
#define TFT_WHITE       0xFFFF
#define TFT_RED         0xF800
#define TFT_GREEN       0x07E0
#define TFT_BLUE        0x001F
#define TFT_CYAN        0x07FF
#define TFT_MAGENTA     0xF81F
#define TFT_YELLOW      0xFFE0
```

## 🔌 **5. Kết Nối Phần Cứng ESP32-2432S028R**

ESP32-2432S028R thường có sẵn màn hình TFT được kết nối sẵn với các pin sau:

| Chức năng | ESP32 Pin | Mô tả |
|-----------|-----------|--------|
| TFT_CS    | GPIO 15   | Chip Select |
| TFT_DC    | GPIO 2    | Data/Command |
| TFT_RST   | GPIO 4    | Reset |
| TFT_MOSI  | GPIO 23   | SPI Data |
| TFT_SCLK  | GPIO 18   | SPI Clock |
| TFT_MISO  | GPIO 19   | SPI Data Input |
| Touch_CS  | GPIO 33   | Touch Chip Select |
| Touch_IRQ | GPIO 36   | Touch Interrupt |

## 📝 **6. Cập Nhật Code**

### **Thay đổi thông tin WiFi và Server:**
```cpp
// WiFi Configuration
const char* ssid = "TEN_WIFI_CUA_BAN";
const char* password = "MAT_KHAU_WIFI";

// Server Configuration  
const char* serverURL = "http://192.168.1.100:5000"; // IP của máy chạy Flask
const char* apiKey = "my-secret-key-2025";
const int userId = 13; // User ID cần hiển thị thông báo
```

### **Tìm IP của máy chủ Flask:**
1. Trên máy chạy Flask, mở Command Prompt
2. Gõ: `ipconfig` (Windows) hoặc `ifconfig` (Linux/Mac)
3. Tìm địa chỉ IPv4 của mạng WiFi (ví dụ: 192.168.1.100)

## 🚀 **7. Upload Code**

### **Bước 1: Kết nối ESP32**
1. Kết nối ESP32 với máy tính qua USB
2. Nhấn và giữ nút BOOT trên ESP32
3. Nhấn nút RESET rồi thả ra
4. Thả nút BOOT (ESP32 vào chế độ download)

### **Bước 2: Upload**
1. Mở file `esp32_medicine_display.ino` trong Arduino IDE
2. Chọn đúng Board và Port
3. Nhấn nút Upload (→)
4. Đợi quá trình upload hoàn tất

### **Bước 3: Kiểm tra**
1. Mở Serial Monitor (Tools → Serial Monitor)
2. Đặt baud rate: 115200
3. Reset ESP32 để xem log

## 📱 **8. Tính Năng Màn Hình**

### **Màn hình chờ:**
- Hiển thị thời gian thực
- Trạng thái kết nối WiFi
- User ID
- Thông báo "SYSTEM READY"

### **Khi có thông báo thuốc:**
- Hiệu ứng nhấp nháy màu đỏ
- Hiển thị tên thuốc
- Số ngăn chứa thuốc
- Thời gian hiện tại
- Ghi chú (nếu có)
- Hướng dẫn cảm ứng xác nhận

### **Sau khi xác nhận:**
- Màn hình xanh "CONFIRMED!"
- Gửi xác nhận về server
- Trở lại màn hình chờ

## 🔧 **9. Khắc Phục Sự Cố**

### **Lỗi không kết nối WiFi:**
- Kiểm tra tên WiFi và mật khẩu
- Đảm bảo WiFi hoạt động bình thường
- Thử reset ESP32

### **Màn hình không hiển thị:**
- Kiểm tra cấu hình TFT_eSPI
- Đảm bảo các pin được cấu hình đúng
- Thử các ví dụ cơ bản của TFT_eSPI

### **Không nhận được thông báo:**
- Kiểm tra IP server
- Đảm bảo Flask server đang chạy
- Kiểm tra User ID trong code
- Xem Serial Monitor để debug

### **Cảm ứng không hoạt động:**
- ESP32-2432S028R có thể cần thư viện touch riêng
- Tạm thời dùng nút GPIO0 để xác nhận
- Kiểm tra thư viện XPT2046_Touchscreen

## 🎯 **10. Tùy Chỉnh Thêm**

### **Thay đổi màu sắc:**
```cpp
#define BACKGROUND_COLOR TFT_BLACK    // Màu nền
#define TEXT_COLOR TFT_WHITE          // Màu chữ
#define MEDICINE_COLOR TFT_CYAN       // Màu thông tin thuốc
#define WARNING_COLOR TFT_RED         // Màu cảnh báo
#define SUCCESS_COLOR TFT_GREEN       // Màu thành công
```

### **Thay đổi thời gian kiểm tra:**
```cpp
// Kiểm tra lịch thuốc mỗi 5 giây
if (millis() - lastCheck > 5000) {
```

### **Thay đổi thời gian nhắc nhở:**
```cpp
// Nhắc nhở sau 30 giây
if (millis() - alertStartTime > 30000) {
```

## 📞 **11. Hỗ Trợ**

Nếu gặp vấn đề, hãy kiểm tra:
1. **Serial Monitor** để xem log lỗi
2. **Kết nối WiFi** và **IP server**
3. **Cấu hình thư viện** TFT_eSPI
4. **User ID** trong database

**Chúc bạn thành công với dự án ESP32 Nhắc Thuốc Thông Minh! 🎉**