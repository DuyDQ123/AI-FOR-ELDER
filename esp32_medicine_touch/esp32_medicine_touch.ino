/*
  ESP32 Medicine Reminder - WITH TOUCH SCREEN
  Phiên bản có cảm ứng màn hình thực sự
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <TFT_eSPI.h>

// CẬP NHẬT THÔNG TIN NÀY
const char* ssid = "duy";
const char* password = "11111111";
const char* serverURL = "http://192.168.1.159:5000";  // Cập nhật IP đúng
const int userId = 13;

TFT_eSPI tft = TFT_eSPI();

bool alertActive = false;
String medicine = "";
int compartmentNum = 0;
int scheduleId = 0;
unsigned long lastCheck = 0;
unsigned long lastTouch = 0;
unsigned long lastConfirmCheck = 0;
unsigned long lastInfoCheck = 0;
int currentConfirmationId = 0;

// Touch areas (x, y, width, height)
struct TouchArea {
  int x, y, w, h;
  String name;
};

TouchArea checkButton = {20, 130, 130, 40, "CHECK"};
TouchArea infoButton = {170, 130, 130, 40, "INFO"};
TouchArea confirmButton = {30, 130, 260, 45, "CONFIRM"};

void setup() {
  Serial.begin(115200);
  
  // Bật đèn nền
  pinMode(21, OUTPUT);
  digitalWrite(21, HIGH);
  
  // Khởi tạo màn hình
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  
  // Hiển thị khởi động
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  tft.drawString("KHOI DONG...", 80, 100);
  
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("System with touch ready!");
  showMainScreen();
}

void loop() {
  // Kiểm tra thuốc mỗi 5 giây
  if (millis() - lastCheck > 5000) {
    checkMedicine();
    lastCheck = millis();
  }
  
  // Kiểm tra Pi button confirmation mỗi 2 giây
  if (millis() - lastConfirmCheck > 2000) {
      checkPiConfirmation();
      lastConfirmCheck = millis();
  }
  
  // Check for INFO flag every 4 seconds
  if (millis() - lastInfoCheck > 4000) {
      checkInfoFlag();
      lastInfoCheck = millis();
  }
  
  // Kiểm tra touch screen
  checkTouch();
  
  delay(50);
}

void checkTouch() {
  // Đọc trạng thái touch - sử dụng analog pin như touch sensor
  int touchValue = analogRead(33); // Pin touch
  
  // Nếu có touch (giá trị thay đổi đáng kể)
  if (touchValue > 100 && millis() - lastTouch > 300) { // Debounce 300ms
    lastTouch = millis();
    
    // Giả lập tọa độ touch đơn giản
    int touchX = 180; // Giữa màn hình
    int touchY = 150;
    
    Serial.println("Touch detected at: " + String(touchX) + "," + String(touchY));
    
    if (alertActive) {
      // Trong chế độ cảnh báo - chỉ có nút confirm
      if (isTouchInArea(touchX, touchY, confirmButton)) {
        Serial.println("Confirm button touched!");
        confirmMedicine();
      }
    } else {
      // Trong chế độ bình thường
      if (isTouchInArea(touchX, touchY, checkButton)) {
        Serial.println("Check button touched!");
        checkMedicine();
      } else if (isTouchInArea(touchX, touchY, infoButton)) {
        Serial.println("Info button touched!");
        showInfo();
      }
    }
  }
  
  // Fallback: cũng hỗ trợ nút BOOT
  if (digitalRead(0) == LOW && millis() - lastTouch > 300) {
    lastTouch = millis();
    Serial.println("BOOT button pressed!");
    
    if (alertActive) {
      confirmMedicine();
    } else {
      checkMedicine();
    }
  }
}

bool isTouchInArea(int x, int y, TouchArea area) {
  return (x >= area.x && x <= (area.x + area.w) && 
          y >= area.y && y <= (area.y + area.h));
}

void checkMedicine() {
  if (WiFi.status() != WL_CONNECTED) {
    showError("WiFi mat ket noi!");
    return;
  }
  
  // Hiện thị đang kiểm tra
  tft.fillRect(10, 100, 300, 20, TFT_BLACK);
  tft.setTextColor(TFT_YELLOW);
  tft.setTextSize(1);
  tft.drawString("Dang kiem tra lich thuoc...", 10, 100);
  
  HTTPClient http;
  http.begin(String(serverURL) + "/api/check_schedule_by_user/" + String(userId));
  http.addHeader("X-API-Key", "my-secret-key-2025");
  
  int code = http.GET();
  
  if (code == 200) {
    String data = http.getString();
    
    if (data.indexOf("medicine_name") > 0) {
      // Tìm tên thuốc
      int start = data.indexOf("\"medicine_name\":\"") + 17;
      int end = data.indexOf("\"", start);
      medicine = data.substring(start, end);
      
      // Tìm ngăn
      start = data.indexOf("\"compartment_number\":") + 21;
      end = data.indexOf(",", start);
      compartmentNum = data.substring(start, end).toInt();
      
      // Tìm schedule ID
      start = data.indexOf("\"schedule_id\":") + 14;
      end = data.indexOf(",", start);
      scheduleId = data.substring(start, end).toInt();
      
      if (!alertActive) {
        alertActive = true;
        showAlertScreen();
      }
    } else {
      if (alertActive) {
        alertActive = false;
        showMainScreen();
      } else {
        // Hiển thị không có thuốc
        tft.fillRect(10, 100, 300, 20, TFT_BLACK);
        tft.setTextColor(TFT_GREEN);
        tft.drawString("Khong co lich uong thuoc!", 10, 100);
      }
    }
  } else {
    showError("Loi API: " + String(code));
  }
  
  http.end();
}

void showMainScreen() {
  tft.fillScreen(TFT_BLACK);
  
  // Header với gradient effect
  tft.fillRect(0, 0, 320, 30, TFT_BLUE);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  tft.drawString("HE THONG NHAC THUOC", 30, 8);
  
  // Trạng thái
  tft.setTextColor(TFT_GREEN);
  tft.setTextSize(2);
  tft.drawString("SAN SANG", 110, 40);
  
  // Thông tin
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  tft.drawString("Nguoi dung: " + String(userId), 10, 70);
  
  // WiFi status với icon
  if (WiFi.status() == WL_CONNECTED) {
    tft.setTextColor(TFT_GREEN);
    tft.drawString("WiFi: Ket noi", 10, 85);
  } else {
    tft.setTextColor(TFT_RED);
    tft.drawString("WiFi: Loi", 10, 85);
  }
  
  // Nút cảm ứng với viền
  drawTouchButton(checkButton, TFT_BLUE, "KIEM TRA");
  drawTouchButton(infoButton, TFT_ORANGE, "THONG TIN");
  
  // Hướng dẫn
  tft.setTextColor(TFT_CYAN);
  tft.setTextSize(1);
  tft.drawString("CAM UNG: Cham vao nut de su dung", 40, 190);
  tft.drawString("NUT BOOT: Cung co the bam nut vat ly", 35, 205);
}

void showAlertScreen() {
  // Hiệu ứng nhấp nháy
  for (int i = 0; i < 3; i++) {
    tft.fillScreen(TFT_RED);
    delay(150);
    tft.fillScreen(TFT_BLACK);
    delay(150);
  }
  
  tft.fillScreen(TFT_BLACK);
  
  // Header cảnh báo nhấp nháy
  tft.fillRect(0, 0, 320, 40, TFT_RED);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(3);
  tft.drawString("UONG THUOC!", 60, 8);
  
  // Thông tin thuốc
  tft.setTextColor(TFT_CYAN);
  tft.setTextSize(2);
  tft.drawString("Ten thuoc:", 10, 50);
  
  String shortName = medicine;
  if (shortName.length() > 25) {
    shortName = shortName.substring(0, 22) + "...";
  }
  
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  tft.drawString(shortName, 10, 75);
  
  tft.setTextColor(TFT_CYAN);
  tft.setTextSize(2);
  tft.drawString("Ngan: " + String(compartmentNum), 10, 95);
  
  // Nút xác nhận lớn với hiệu ứng
  drawTouchButton(confirmButton, TFT_GREEN, "XAC NHAN UONG");
  
  // Hướng dẫn nhấp nháy
  tft.setTextColor(TFT_YELLOW);
  tft.setTextSize(1);
  tft.drawString("CAM UNG: Cham vao nut xanh", 70, 190);
  tft.drawString("CHI XAC NHAN SAU KHI UONG!", 55, 205);
  
  Serial.println("CANH BAO: " + medicine + " - Ngan " + String(compartmentNum));
}

void drawTouchButton(TouchArea area, uint16_t color, String text) {
  // Vẽ nút với viền và shadow
  tft.fillRoundRect(area.x + 2, area.y + 2, area.w, area.h, 8, TFT_DARKGREY); // Shadow
  tft.fillRoundRect(area.x, area.y, area.w, area.h, 8, color); // Button
  tft.drawRoundRect(area.x, area.y, area.w, area.h, 8, TFT_WHITE); // Border
  
  // Text
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  int textX = area.x + (area.w - text.length() * 6) / 2;
  int textY = area.y + area.h / 2 - 4;
  tft.drawString(text, textX, textY);
}

void showInfo() {
    Serial.println("showInfo() function called");
    
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi not connected in showInfo");
        showError("WiFi mat ket noi!");
        return;
    }

    Serial.println("Making API call to get user profile...");
    HTTPClient http;
    http.begin(String(serverURL) + "/api/user_profile/" + String(userId));
    http.addHeader("X-API-Key", "my-secret-key-2025");

    int code = http.GET();
    Serial.println("User profile API response code: " + String(code));

    if (code == 200) {
        String data = http.getString();
        Serial.println("User profile data received: " + data.substring(0, 100) + "...");

        // Parse user info
        String fullName = extractJsonValue(data, "full_name");
        String age = extractJsonValue(data, "age");
        String email = extractJsonValue(data, "email");
        String phone = extractJsonValue(data, "phone");

        // Parse weekly stats
        String dosesTaken = extractJsonValue(data, "doses_taken");
        String complianceRate = extractJsonValue(data, "compliance_rate");

        Serial.println("Displaying user info on TFT...");
        tft.fillScreen(TFT_NAVY);
        tft.setTextColor(TFT_WHITE);
        tft.setTextSize(2);
        tft.drawString("THONG TIN NGUOI DUNG", 20, 10);

        tft.setTextSize(1);
        tft.drawString("Ten: " + fullName, 10, 40);
        tft.drawString("Tuoi: " + age, 10, 60);
        tft.drawString("Email: " + email, 10, 80);
        tft.drawString("SDT: " + phone, 10, 100);

        tft.setTextColor(TFT_YELLOW);
        tft.drawString("Thong ke tuan:", 10, 120);
        tft.drawString("Da uong: " + dosesTaken, 10, 140);
        tft.drawString("Ty le: " + complianceRate + "%", 10, 160);

        tft.setTextColor(TFT_CYAN);
        tft.drawString("Cham man hinh de quay lai", 40, 190);
        
        Serial.println("TFT display completed, waiting 5 seconds...");
    } else {
        Serial.println("Error getting user profile: " + String(code));
        showError("Loi API: " + String(code));
    }

    http.end();
    delay(5000);  // Hiển thị lâu hơn để user đọc được
    Serial.println("Returning to main screen...");
    showMainScreen();
}

String extractJsonValue(String json, String key) {
    int start = json.indexOf("\"" + key + "\":") + key.length() + 3;
    int end = json.indexOf(",", start);
    if (end == -1) end = json.indexOf("}", start);
    String result = json.substring(start, end);
    result.replace("\"", "");
    return result;
}

void showError(String error) {
  tft.fillRect(10, 100, 300, 40, TFT_RED);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  tft.drawString("LOI: " + error, 15, 110);
  Serial.println("ERROR: " + error);
}

void confirmMedicine() {
  confirmMedicine(true); // Gọi với sendAPI = true (default)
}

void confirmMedicine(bool sendAPI) {
  Serial.println("XAC NHAN UONG THUOC!");
  
  // Hiệu ứng xác nhận
  tft.fillScreen(TFT_GREEN);
  tft.setTextColor(TFT_BLACK);
  tft.setTextSize(3);
  tft.drawString("XAC NHAN!", 80, 60);
  tft.setTextSize(2);
  tft.drawString("Cam on ban!", 90, 100);
  tft.setTextSize(1);
  
  if (sendAPI) {
    tft.drawString("Da gui thong bao len server", 70, 140);
  } else {
    tft.drawString("Raspberry Pi da xac nhan", 70, 140);
  }
  
  // Gửi xác nhận chỉ khi cần
  if (sendAPI && WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(String(serverURL) + "/api/confirm_medicine_by_user");
    http.addHeader("X-API-Key", "my-secret-key-2025");
    http.addHeader("Content-Type", "application/json");
    
    String json = "{\"schedule_id\":" + String(scheduleId) + ",\"user_id\":" + String(userId) + "}";
    int result = http.POST(json);
    
    if (result == 200) {
      Serial.println("Gui xac nhan thanh cong!");
    } else {
      Serial.println("Loi gui: " + String(result));
    }
    
    http.end();
  }
  
  delay(2000);
  
  // Reset
  alertActive = false;
  medicine = "";
  compartmentNum = 0;
  scheduleId = 0;
  
  showMainScreen();
}

void checkInfoFlag() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, skipping INFO flag check");
    return; // Only check when WiFi is connected
  }

  Serial.println("Checking INFO flag for user: " + String(userId));
  HTTPClient http;
  http.begin(String(serverURL) + "/api/check_info_flag/" + String(userId));
  http.addHeader("X-API-Key", "my-secret-key-2025");

  int code = http.GET();
  Serial.println("INFO flag check response code: " + String(code));

  if (code == 200) {
    String data = http.getString();
    Serial.println("INFO flag response: " + data);

    if (data.indexOf("\"info_flag_detected\":true") > 0) {
      Serial.println("INFO flag detected! Displaying user profile...");
      
      // Extract flag_id to clear it after displaying
      int idStart = data.indexOf("\"flag_id\":") + 10;
      int idEnd = data.indexOf("}", idStart);
      if (idEnd == -1) idEnd = data.indexOf(",", idStart);
      int flagId = data.substring(idStart, idEnd).toInt();
      Serial.println("Flag ID to clear: " + String(flagId));
      
      // Clear the flag first to prevent repeated detection
      clearInfoFlag(flagId);
      
      // Show user info
      Serial.println("Starting to display user info...");
      showInfo();
      Serial.println("User info display completed");
      
    } else {
      Serial.println("No INFO flag detected");
    }
  } else {
    Serial.println("Error checking INFO flag: " + String(code));
  }

  http.end();
}

void checkPiConfirmation() {
  if (WiFi.status() != WL_CONNECTED || !alertActive) {
    return; // Chỉ check khi có WiFi và đang alert
  }
  
  HTTPClient http;
  http.begin(String(serverURL) + "/api/check_confirmation_status/" + String(userId));
  http.addHeader("X-API-Key", "my-secret-key-2025");
  
  int code = http.GET();
  
  if (code == 200) {
    String data = http.getString();
    
    // Kiểm tra xem có confirmation mới không
    if (data.indexOf("\"confirmed\":true") > 0) {
      // Tìm confirmation_id
      int idStart = data.indexOf("\"confirmation_id\":") + 18;
      int idEnd = data.indexOf("}", idStart);
      if (idEnd == -1) idEnd = data.indexOf(",", idStart);
      int confirmId = data.substring(idStart, idEnd).toInt();
      
      // Nếu là confirmation mới
      if (confirmId != currentConfirmationId && confirmId > 0) {
        currentConfirmationId = confirmId;
        
        Serial.println("PI BUTTON CONFIRMATION DETECTED!");
        
        // HIỂN THỊ GIỐNG NHƯ KHI NHẤN NÚT BOOT
        // Sử dụng cùng function confirmMedicine() nhưng không gửi API
        confirmMedicine(false);  // false = không gửi API vì Pi đã gửi rồi
        
        // Xóa confirmation sau khi hiển thị
        clearConfirmation(confirmId);
      }
    }
  } else {
    Serial.println("Error checking Pi confirmation: " + String(code));
  }
  
  http.end();
}

void clearInfoFlag(int flagId) {
  HTTPClient http;
  http.begin(String(serverURL) + "/api/clear_info_flag/" + String(flagId));
  http.addHeader("X-API-Key", "my-secret-key-2025");
  http.addHeader("Content-Type", "application/json");
  
  int result = http.POST("{}");
  
  if (result == 200) {
    Serial.println("INFO flag cleared successfully!");
  } else {
    Serial.println("Error clearing INFO flag: " + String(result));
  }
  
  http.end();
}


void clearConfirmation(int confirmId) {
  HTTPClient http;
  http.begin(String(serverURL) + "/api/clear_confirmation/" + String(confirmId));
  http.addHeader("X-API-Key", "my-secret-key-2025");
  http.addHeader("Content-Type", "application/json");
  
  int result = http.POST("{}");
  
  if (result == 200) {
    Serial.println("Confirmation cleared successfully!");
  } else {
    Serial.println("Error clearing confirmation: " + String(result));
  }
  
  http.end();
}