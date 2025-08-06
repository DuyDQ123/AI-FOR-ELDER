# ESP32 - Raspberry Pi Database Sync Guide

## 🔄 **Workflow Overview**

Hệ thống đồng bộ giữa **Raspberry Pi GPIO 16 button** và **ESP32 TFT display** thông qua **database**.

### **Cách hoạt động:**
```
1. Pi hiển thị medicine alert → User bấm GPIO 16 
2. Pi gửi confirmation đến database → Flask server lưu với flag đặc biệt
3. ESP32 check database mỗi 2 giây → Phát hiện Pi confirmation
4. ESP32 hiển thị "Pi CONFIRMED!" → Auto clear alert
```

---

## 🛠 **Technical Implementation**

### **1. Database Structure**
- **Table:** `medicine_history` 
- **Flag field:** `notes = 'pi_button_confirmed'`
- **Detection:** ESP32 tìm records có flag này trong 5 phút gần nhất

### **2. API Endpoints**

#### **A. `/api/confirm_pi_button` (POST)**
- **Mục đích:** Pi gửi flag đặc biệt khi GPIO 16 được bấm
- **Headers:** `X-API-Key: my-secret-key-2025`
- **Body:**
```json
{
  "schedule_id": 123,
  "user_id": 13,
  "pi_button_flag": true
}
```

#### **B. `/api/check_confirmation_status/<user_id>` (GET)**
- **Mục đích:** ESP32 check xem Pi có confirmation mới không
- **Response:**
```json
{
  "confirmed": true,
  "timestamp": "2025-07-31T16:00:00",
  "medicine_name": "Paracetamol", 
  "compartment_number": 1,
  "confirmation_id": 456
}
```

#### **C. `/api/clear_confirmation/<confirmation_id>` (POST)**
- **Mục đích:** ESP32 clear confirmation sau khi hiển thị
- **Effect:** Đổi `notes` thành `'pi_button_confirmed_displayed'`

---

## 📁 **Code Changes**

### **1. rpi_handler2.py**
```python
# THÊM VÀO confirm_callback() function:
pi_flag_data = {
    "schedule_id": self.current_schedule_id, 
    "user_id": USER_ID,
    "pi_button_flag": True
}

pi_response = requests.post(f"{SERVER_URL}/api/confirm_pi_button",
                           headers=headers, json=pi_flag_data)
```

### **2. routes/main.py**
```python
# THÊM 3 API endpoints mới:
@main.route('/api/confirm_pi_button', methods=['POST'])
@main.route('/api/check_confirmation_status/<int:user_id>', methods=['GET']) 
@main.route('/api/clear_confirmation/<int:confirmation_id>', methods=['POST'])
```

### **3. esp32_medicine_touch.ino**
```cpp
// THÊM VÀO loop():
if (millis() - lastConfirmCheck > 2000) {
    checkPiConfirmation();
    lastConfirmCheck = millis();
}

// THÊM functions mới:
void checkPiConfirmation()
void showPiConfirmationScreen()
void clearConfirmation(int confirmId)
```

---

## ⚡ **Performance**

### **Độ trễ sync:**
- **Trung bình:** 2-3 giây
- **Tối đa:** 5 giây (nếu ESP32 vừa check xong)
- **Tối thiểu:** 0.5 giây (nếu ESP32 sắp check)

### **Network traffic:**
- **ESP32 → Server:** Mỗi 2 giây, ~200 bytes
- **Pi → Server:** Khi có confirmation, ~150 bytes
- **Total:** ~6KB/phút (rất thấp)

---

## 🔧 **Configuration**

### **IP Address:**
- **Pi:** `192.168.1.159`
- **ESP32:** Auto DHCP
- **Server:** `192.168.1.159:5000`

### **API Key:**
```
X-API-Key: my-secret-key-2025
```

### **User ID:**
```
USER_ID = 13  # (Pi)
const int userId = 13;  // (ESP32)
```

---

## 🧪 **Testing Workflow**

### **Bước 1: Khởi động hệ thống**
```bash
# Terminal 1: Start Flask server
python app.py

# Terminal 2: Start Pi handler  
python rpi_handler2.py

# Terminal 3: Upload ESP32 code
# (Sử dụng Arduino IDE)
```

### **Bước 2: Test scenario**
1. **Tạo medicine schedule** qua web interface
2. **Đợi notification** trên Pi terminal
3. **Bấm GPIO 16** trên Pi 
4. **Kiểm tra ESP32** hiển thị "PI CONFIRMED!"

### **Bước 3: Debug logs**
- **Pi:** Console output với "Pi button flag sent!"
- **ESP32:** Serial monitor với "PI BUTTON CONFIRMATION DETECTED!"
- **Server:** Flask logs với API calls

---

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **1. ESP32 không nhận được confirmation**
- ✅ Check WiFi connection: `WiFi.status() == WL_CONNECTED`
- ✅ Check server IP: `http://192.168.1.159:5000`
- ✅ Check API key: `my-secret-key-2025`

#### **2. Pi không gửi được flag**
- ✅ Check internet connection
- ✅ Check server running: `curl http://192.168.1.159:5000`
- ✅ Check API endpoint: `/api/confirm_pi_button`

#### **3. Database issues**
- ✅ Check MedicineHistory table exists
- ✅ Check notes field allows string
- ✅ Check foreign key constraints

### **Debug Commands:**
```bash
# Test Pi API call
curl -X POST http://192.168.1.159:5000/api/confirm_pi_button \
  -H "X-API-Key: my-secret-key-2025" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id":1,"user_id":13,"pi_button_flag":true}'

# Test ESP32 API call  
curl -X GET http://192.168.1.159:5000/api/check_confirmation_status/13 \
  -H "X-API-Key: my-secret-key-2025"
```

---

## ✅ **Success Indicators**

### **Pi Side:**
```
Pi button flag sent to server for ESP32 sync!
```

### **ESP32 Side:**
```
PI BUTTON CONFIRMATION DETECTED!
HIEN THI: Pi button da xac nhan thuoc Paracetamol
```

### **Database:**
```sql
SELECT * FROM medicine_history 
WHERE notes = 'pi_button_confirmed' 
ORDER BY timestamp DESC LIMIT 5;
```

---

## 📊 **System Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raspberry Pi  │    │   Flask Server   │    │     ESP32       │
│                 │    │                  │    │                 │
│ GPIO 16 Button  ├────┤ Database + APIs  ├────┤ TFT Display     │
│ rpi_handler2.py │    │ routes/main.py   │    │ .ino file       │
│                 │    │                  │    │                 │
│ POST /confirm_  │    │ medicine_history │    │ GET /check_     │
│ pi_button       │    │ table            │    │ confirmation    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 🎯 **Next Steps**

1. ✅ **Test complete workflow** từ Pi button → ESP32 display
2. ⚡ **Optimize polling** interval nếu cần (hiện tại 2s)
3. 🔔 **Add sound notification** cho ESP32 (optional)
4. 📱 **Mobile app integration** (future enhancement)

**Database sync solution hoàn thành!** 🚀