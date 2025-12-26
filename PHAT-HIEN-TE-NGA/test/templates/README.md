<h1 align="center">HỆ THỐNG GIÁM SÁT VÀ PHÂN TÍCH HÀNH ĐỘNG TÉ NGÃNGÃ </h1>

<div align="center">

<p align="center">
  <img src="D:/AIOT/BTL/images/logoDaiNam.png" alt="DaiNam University Logo" width="200"/>
  <img src="D:/AIOT/BTL/images/LogoAIoTLab.png" alt="AIoTLab Logo" width="170"/>
</p>

[![Made by AIoTLab](https://img.shields.io/badge/Made%20by%20AIoTLab-blue?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Fit DNU](https://img.shields.io/badge/Fit%20DNU-green?style=for-the-badge)](https://fitdnu.net/)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-red?style=for-the-badge)](https://dainam.edu.vn)

</div>

<h2 align="center">Hệ thống giám sát và phân tích hàng động té ngã </h2>

<p align="center">
  Hệ thống giám sát và phân tích hàng động té ngã là một dự án tích hợp giữa phần cứng (Arduino) và phần mềm (Python) nhằm phân tích hành động té ngã. Dự án sử dụng cảm biến MPU6050 gắn trên người để thu thập dữ liệu gia tốc, gửi đến ESP32 xử lý và truyền qua HTTP đến máy chủ. Dữ liệu được lưu dưới dạng CSV và phân tích bằng mô hình học máy để nhận diện hành động. Kết quả được hiển thị trên ứng dụng(web) và gửi thông báo(Telegram) khi phát hiện té ngã, giúp cảnh báo kịp thời cho người.
</p>

---

## 🌟 Giới thiệuthiệu

- **📌 Phát hiện chính xác:** Xác định té ngã thông qua dữ liệu cảm biến.
- **💡 Cảnh báo nhanh:** Gửi thông báo đến người thân.
- **📊 Quản lý dữ liệu:** Dữ liệu gia tốc, con quay hồi chuyển được lưu trữ o file CSV, có thể xem lịch sử.
- **🖥️ Giao diện thân thiện:** Sử dụng Flask cho xử lý dữ liệu từ cảm biến qua web.

---
## Chức Năng Chính
1. **Thu thập dữ liệu:** ESP32 đọc dữ liệu từ MPU6050.
2. **Nhận diện té ngã:** Xử lý dữ liệu bằng thuật toán CNN + LSTM.
3. **Lưu trữ dữ liệu:** Ghi vào file CSV trên ESP32.
4. **Hiển thị kết quả:** Web Server hiển thị dữ liệu theo thời gian thực.
5. **Gửi cảnh báo:** Khi té ngã xảy ra, hệ thống gửi tin nhắn đến Telegram.

---
## 🏗️ HỆ THỐNG
<p align="center">
  <img src="D:/AIOT/BTL/images/anhSdHT.png" alt="System Architecture" width="800"/>
</p>

---
## 📂 Cấu trúc dự án

📦 Project  
├── 📂 images  # Thư mục chứa ảnh liên quan đến dự án.
├── 📂 Test 
│   ├── 📂 esp32 #Code Arduino thu dữ liệu, rồi gửi lên Server Flask qua HTTP.  
|   ├──📂static
│   |    |   ├── script.js # Code giúp trang web hiển thị đẹp và cập nhật dữ liệu động.
|   |    |   ├── style.css # Code giúp trang web hiển thị đẹp và cập nhật dữ liệu động.
|   ├──📂templates
|   |    |   ├── index.html #  Giao diện web phát hiện, phân tích hành động té ngã và dữ liệu cảm biến cập nhật theo thời gian thực. 
|   |    |   ├── readme.md # Giới thiệu tổng quan về dự án.
|   ├── fall_detection_model.h5  #  Mô hình đã train.
|   ├──flask_server.py #Code Flask Server để nhận dữ liệu từ ESP32. 
|   ├──sersor_data.db #  Dữ liệu cảm biển đượ train model.
├── 📂thu_du_du_lieulieu
|   ├── get_data_from_esp32.ino # Code dùng để thu dữ liệu cảm biến, phục vụ cho việc xử lý dữ liệuliệu
├── 📂truc_quan_hoa_du_lieulieu  
|   ├── code.py #Code này ggiúp kiểm tra và phân tích đặc trưng tín hiệu cảm biến cho từng hành động té ngã.
|   ├── data_action.csv #file CSV thu dữ liệu từ cảm biến.
├── 📂Xu_ly_du_lieulieu 
|   ├── client1.py #Code trên để thực hiện tiền xử lý dữ liệu thu thập từ cảm biến MPU6050 để phục vụ huấn luyện mô hình nhận diện hành động té ngã.
|   ├── data_action # file CSV thu dữ liệu từ cảm biến.
|   ├──X_balanced1.npy # file code dùng cho huấn luyện mô hình.
|   ├──y_balanced1.npy #file code dùng cho huấn luyện mô hình.
---



## 🛠️ CÔNG NGHỆ SỬ DỤNG

<div align="center">

### 📡 Phần cứng
![ESP32](https://img.shields.io/badge/ESP32-ESPressif-red?style=for-the-badge&logo=espressif&logoColor=white)
![MPU6050](https://img.shields.io/badge/MPU6050-IMU-blue?style=for-the-badge&logo=bosch&logoColor=white)
[![WiFi](https://img.shields.io/badge/WiFi-2.4GHz-orange?style=for-the-badge)]()
![Power Source](https://img.shields.io/badge/Power%20Source-Battery%20%7C%20Adapter-blue?style=for-the-badge&logo=electricity&logoColor=white)

### 🖥️ Phần mềm
[![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)]()
[![Flask](https://img.shields.io/badge/Flask-Framework-black?style=for-the-badge&logo=flask)]()
![CNN+LSTM](https://img.shields.io/badge/CNN+LSTM-Deep%20Learning-blue?style=for-the-badge&logo=tensorflow&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)

</div>

## 🛠️ Yêu cầu hệ thống

### 🔌 Phần cứng
- **ESP32** (hoặc board tương thích) với **MPU6050**.
- **Cáp USB** để kết nối ESP32 với máy tính.
- ⚠️ **Lưu ý:** Mặc định mã nguồn ESP32 trong `esp32.ino` sử dụng cổng `COM4`. Nếu ESP32 của bạn sử dụng cổng khác, hãy thay đổi biến `SERIAL_PORT` trong `flask_serverserver.py`.

### 💻 Phần mềm
- **Python 3+**
- **⚡ ESP32** để thu dữ liệu từ cảm biếnbiến.

### 📦 Các thư viện Python cần thiết
Cài đặt các thư viện bằng lệnh:

    pip install numpy as np, 
    pip install tensorflow as tf
## 🧮 Bảng mạch

### 🔩 Kết nối phần cứng:
<img src="D:/AIOT/BTL/images/sodothietbiithudulieu.jpg" alt="System Architecture" width="800"/>

### ⛓️‍💥 Hướng dẫn cắm dây
| Thiết bị        | Chân trên thiết bị | Kết nối ESP32ESP32 | Ghi chú                         |
|-----------------|-------------------|---------------------|---------------------------------|
| Breadboard      | -                 | -                   | Dùng để kết nối linh kiện       |
| MPU6050MPU6050   | VCC, GND, SCL, SDA | VCC → 3.3V, GND → GND, SCL → GPIO22, SDA → GPIO21 | Kết nối cảm biến gia tốc MPU6050|
|ESP32     | -                 | -                   | Vi điền khiển chínhchính |
| 5 dây điện      | -                 | -                   | Dùng để nối các linh kiện       |

## 🚀 Hướng dẫn cài đặt và chạy hệ thống.
1️⃣ Chuẩn bị phần cứng
    1. Kết Nối 
    **MPU6050** với **ESP32** qua giao thức I2C.
    2. Cấp nguồn điện cho **ESP32** để thu dữ liệu.

2️⃣ Cài đặt thư viện Python. 

Cài đặt Python 3 nếu chưa có, sau đó cài đặt các thư viện cần thiết bằng pip.

3️⃣ Cài đặt phần mềm.
**Ở file Thu_du_lieu**
    1. Mở **Arduino IDE** hoặc **PlatformIO**.
    2. Cài đặt thư viện cần thiết.
    3. Cập nhật thông tin WiFi.
    4. Nạp code vào ESP32.
    5. Mở Serial Monitor để xem địa chỉ Ip.
    6. Dùng trình duyệt truy cập vào địa chỉ IP của ESP32.
    7. Trang web server cho phép người dùng bắt đầu/dừng ghi dữ liệu với nhãn hành động cụ thể. Dữ liệu cảm biến cũng được hiển thị theo thời gian thực trên web.Khi bộ đệm đầy, dữ liệu được ghi vào file để tối ưu hiệu suất. Chúng ta sẽ tải file CSV qua nút "Download" trên web.
**Trên file Xu_ly_du_lieu**
    1.Đọc dữ liệu từ file CSV.
    2. Lọc các hoạt động hợp lệ.
    3. Chuẩn hóa dữ liệu.
    4. Mã hóa nhãn hoạt động.
    5. Tạo cửa sổ trượt (Sliding Window).
    6. Xử lý mất cân bằng dữ liệu (SMOTE).
    7. Lưu dữ liệu đã cân bằng.
    8. Kiểm tra số lượng mẫu theo từng nhãn sau khi cân bằng.
**Truc_quan_hoa_du_lieu**
    1. Đọc dữ liệu từ file CSV.
    2. Hiển thị từng biểu đồ theo từng loại hành động. 
**Huấn luyện mô hình CNN + LSTM**
    1. Huấn luyện trên Google Colab.
    2. Thực hiện các bước huấn luyện mô hình như file "tranining model.txt".
    3. Lưu mô hình "fall_detection_model.h5" đã huấn luyện vào folder "test" để thực nghiệm đánh giá kết quả.
**Chay hệ thống**
1. **Chạy esp32.ino**
    - Mở **Arduino IDE** hoặc **PlatformIO**.
    - Cài đặt các thư viện cần thiết.
    - Cập nhật thông tin WiFi.
    - Nạp code vào ESP32.
    - Dữ liệu được gửi đến server Flask (http://192.168.137.1:5000/sensor) bằng HTTP POST, nhận phản hồi từ server và hiển thị lên Serial Monitor. 
2. **Chạy flask_server.py** trên máy tính.
    - Cài đặt các thư viện cần thiết.
    - Chạy code "python flask_server.py"
    - Dùng trình duyệt truy cập vào (http://127.0.0.1:5000)
    -Hiển thị gigiao diện web: trạng thái mới nhất từ cảm biến và biểu đồ cảm biến cập nhật dữ liệu theo thời gian thực.
    -  Sau đó "Nhận cảnh báo" khi té ngã qua Telegram.

## ⚙️ Cấu hình & Ghi chú

1. Cổng ESP32: 
- Mặc định sử dụng COM55. 
2. Gửi tin nhắn cảnh báobáo:
- Trong `flask_server.py`, cập nhật thông tin *TELEGRAM_BOT_TOKEN* và *TELEGRAM_CHAT_ID*.(TELEGRAM_BOT_TOKEN là bot của tài khoảnkhoản Telegram, TELEGRAM_CHAT_ID là mã id của tài khoản Telegram.)
3. Thời gian gửi tin nhắn thông báo: cập nhật hành động ngã mới nhất sau sau 2 giây.
4. Môi trường mạng: 
- Thiết bị esp32 cần kết nối cùng mạng với máy chủ.

## 📰 Poster
<p align="center">
  <img src="D:/AIOT/BTL/images/Poster_Group3-CNTT1604.pngpng" alt="System Architecture" width="800"/>
</p>

## 🤝 Đóng góp
Dự án được phát triển bởi 4 thành viên:

| Họ và Tên              | Vai trò                  |
|------------------------|--------------------------|
| Phạm Thị Hồng Ngọc     | Phát triển toàn bộ mã nguồn, train model, kiểm thử, biên soạn tài liệu Overleaf, Poster Powerpoint triển khai dự án và thực hiện video giới thiệu.|
| Nguyễn Đức ThườngThường| Hỗ trợ Poster, Powerpoint, thuyết trình, hỗ trợ bài tập lớn |
| Nguyễn Đào Nguyên Giáp | Thuyết trình, hỗ trợ bài tập lớn.  |
| Nguyễn Hải Phong       | Hỗ trợ bài tập lớn. |

© 2025 NHÓM 3, CNTT16-04, TRƯỜNG ĐẠI HỌC ĐẠI NAM