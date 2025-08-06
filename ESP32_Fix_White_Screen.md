# 🔧 Khắc Phục Màn Hình Trắng ESP32-2432S028R

## 🚨 **Vấn đề hiện tại:**
- Màn hình chỉ hiển thị màu trắng
- Có thể nhấp nháy (backlight hoạt động)
- Touch screen hoạt động
- **Nguyên nhân:** Cấu hình TFT driver sai

## 📋 **Các bước khắc phục:**

### **Bước 1: Thay đổi User_Setup.h**

1. **Tìm file User_Setup.h:**
   ```
   C:\Users\[TenBan]\Documents\Arduino\libraries\TFT_eSPI\User_Setup.h
   ```

2. **Backup file gốc:**
   - Đổi tên `User_Setup.h` thành `User_Setup_backup.h`

3. **Copy nội dung file `User_Setup_Fixed.h`:**
   - Mở file `User_Setup_Fixed.h` 
   - Copy All (Ctrl+A, Ctrl+C)
   - Tạo file mới `User_Setup.h`
   - Paste (Ctrl+V) và Save

### **Bước 2: Test với file đơn giản**

1. **Upload file test:**
   - Mở `esp32_simple_test.ino` trong Arduino IDE
   - Upload lên ESP32
   - Mở Serial Monitor (115200 baud)

2. **Kiểm tra kết quả:**
   - **Nếu thấy màu sắc** → Thành công!
   - **Nếu vẫn trắng** → Thử bước 3

### **Bước 3: Thử các driver khác**

Trong file `User_Setup.h`, thay đổi driver:

#### **Option 1: ST7789 (thử đầu tiên)**
```cpp
// Comment dòng này:
//#define ILI9341_DRIVER

// Uncomment dòng này:
#define ST7789_DRIVER
```

#### **Option 2: ILI9488**
```cpp
//#define ILI9341_DRIVER
//#define ST7789_DRIVER
#define ILI9488_DRIVER
```

#### **Option 3: ILI9342**
```cpp
//#define ILI9341_DRIVER
//#define ST7789_DRIVER
//#define ILI9488_DRIVER
#define ILI9342_DRIVER
```

### **Bước 4: Thử pin mapping khác**

Nếu vẫn không work, thử pin mapping thay thế:

```cpp
// Comment các dòng hiện tại:
//#define TFT_MISO 12
//#define TFT_MOSI 13  
//#define TFT_SCLK 14

// Uncomment các dòng này:
#define TFT_MISO 19
#define TFT_MOSI 23
#define TFT_SCLK 18
```

### **Bước 5: Kiểm tra SPI frequency**

Thử giảm tần số SPI:

```cpp
// Thay đổi từ:
#define SPI_FREQUENCY  27000000

// Thành:
#define SPI_FREQUENCY  20000000
// hoặc
#define SPI_FREQUENCY  10000000
```

## 🔄 **Quy trình thử nghiệm:**

### **Test 1: ST7789 Driver**
1. Thay `#define ILI9341_DRIVER` thành `#define ST7789_DRIVER`
2. Upload `esp32_simple_test.ino`
3. Kiểm tra màn hình

### **Test 2: Pin mapping thay thế**
1. Đổi pin từ (12,13,14) sang (19,23,18)
2. Upload test
3. Kiểm tra màn hình

### **Test 3: ILI9488 Driver**
1. Thay thành `#define ILI9488_DRIVER`
2. Upload test
3. Kiểm tra màn hình

## ✅ **Dấu hiệu thành công:**
- Màn hình hiển thị màu sắc khác nhau
- Text "TEST" hiển thị rõ ràng
- Serial Monitor hiển thị "Basic test completed!"

## 🎯 **Sau khi tìm được cấu hình đúng:**
1. Note lại driver và pin mapping hoạt động
2. Quay lại sử dụng code chính `esp32_medicine_display_advanced.ino`
3. Cập nhật WiFi và server info

## 📞 **Nếu vẫn không work:**
Thử tìm kiếm "ESP32-2432S028R TFT_eSPI config" hoặc kiểm tra:
- Có thể board sử dụng driver đặc biệt
- Kiểm tra kết nối phần cứng
- Thử với ví dụ cơ bản của TFT_eSPI library

**Chúc bạn thành công! 🎉**