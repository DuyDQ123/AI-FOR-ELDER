/*
  ESP32 Medicine Reminder - WITH MULTITHREADING
  Sử dụng FreeRTOS tasks để xử lý parallel
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <TFT_eSPI.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>

// Cấu hình WiFi và Server
const char* ssid = "duy";
const char* password = "11111111";
const char* serverURL = "http://172.20.10.2:5000";
const int userId = 15;

TFT_eSPI tft = TFT_eSPI();

// FreeRTOS handles
TaskHandle_t networkTaskHandle = NULL;
TaskHandle_t displayTaskHandle = NULL;
TaskHandle_t touchTaskHandle = NULL;
TaskHandle_t systemTaskHandle = NULL;

// Queues for inter-task communication
QueueHandle_t displayQueue;
QueueHandle_t networkQueue;

// Semaphores for resource protection
SemaphoreHandle_t tftMutex;
SemaphoreHandle_t wifiMutex;

// Shared data structures
struct DisplayMessage {
  String type;      // "alert", "info", "main", "error"
  String data;      // JSON data or message
  int priority;     // 1=high, 2=medium, 3=low
};

struct NetworkRequest {
  String type;      // "check_medicine", "check_info", "check_confirmation", "user_profile", "clear_flag"
  String endpoint;
  int param;        // flag_id, user_id, etc.
};

// System state
bool alertActive = false;
String medicine = "";
int compartmentNum = 0;
int scheduleId = 0;
int currentConfirmationId = 0;

// Touch areas
struct TouchArea {
  int x, y, w, h;
  String name;
};

TouchArea checkButton = {20, 130, 130, 40, "CHECK"};
TouchArea infoButton = {170, 130, 130, 40, "INFO"};
TouchArea confirmButton = {30, 130, 260, 45, "CONFIRM"};

void setup() {
  Serial.begin(115200);
  Serial.println("Starting ESP32 Multithreaded Medicine System...");
  
  // Khởi tạo hardware
  pinMode(21, OUTPUT);
  digitalWrite(21, HIGH);
  
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  tft.drawString("KHOI DONG...", 80, 100);
  
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("WiFi connected!");
  
  // Tạo mutexes và queues
  tftMutex = xSemaphoreCreateMutex();
  wifiMutex = xSemaphoreCreateMutex();
  displayQueue = xQueueCreate(10, sizeof(DisplayMessage));
  networkQueue = xQueueCreate(10, sizeof(NetworkRequest));
  
  if (tftMutex == NULL || wifiMutex == NULL || displayQueue == NULL || networkQueue == NULL) {
    Serial.println("Failed to create mutexes/queues!");
    return;
  }
  
  // Tạo tasks
  xTaskCreatePinnedToCore(
    networkTask,
    "NetworkTask",
    8192,  // Stack size
    NULL,
    2,     // Priority
    &networkTaskHandle,
    0      // Core 0
  );
  
  xTaskCreatePinnedToCore(
    displayTask,
    "DisplayTask", 
    8192,
    NULL,
    3,     // Higher priority for display
    &displayTaskHandle,
    1      // Core 1
  );
  
  xTaskCreatePinnedToCore(
    touchTask,
    "TouchTask",
    4096,
    NULL,
    2,
    &touchTaskHandle,
    1      // Core 1
  );
  
  xTaskCreatePinnedToCore(
    systemTask,
    "SystemTask",
    4096, 
    NULL,
    1,     // Lower priority
    &systemTaskHandle,
    0      // Core 0
  );
  
  Serial.println("All tasks created successfully!");
  
  // Hiển thị main screen
  DisplayMessage msg;
  msg.type = "main";
  msg.data = "";
  msg.priority = 2;
  xQueueSend(displayQueue, &msg, portMAX_DELAY);
}

void loop() {
  // Main loop rất nhẹ, chỉ monitor system
  vTaskDelay(pdMS_TO_TICKS(1000));
  
  // Print free heap periodically
  static unsigned long lastHeapPrint = 0;
  if (millis() - lastHeapPrint > 30000) {
    Serial.println("Free heap: " + String(ESP.getFreeHeap()));
    lastHeapPrint = millis();
  }
}

// NETWORK TASK - Handle all HTTP requests
void networkTask(void *parameter) {
  NetworkRequest req;
  
  while (true) {
    // Check for network requests
    if (xQueueReceive(networkQueue, &req, pdMS_TO_TICKS(100)) == pdPASS) {
      processNetworkRequest(req);
    }
    
    // Auto-schedule periodic checks
    static unsigned long lastMedicineCheck = 0;
    static unsigned long lastInfoCheck = 0;
    static unsigned long lastConfirmCheck = 0;
    
    unsigned long now = millis();
    
    // Check medicine schedule every 5 seconds
    if (now - lastMedicineCheck > 5000) {
      NetworkRequest medicineReq;
      medicineReq.type = "check_medicine";
      medicineReq.endpoint = "/api/check_schedule_by_user/" + String(userId);
      medicineReq.param = userId;
      
      processNetworkRequest(medicineReq);
      lastMedicineCheck = now;
    }
    
    // Check INFO flag every 4 seconds
    if (now - lastInfoCheck > 4000) {
      NetworkRequest infoReq;
      infoReq.type = "check_info";
      infoReq.endpoint = "/api/check_info_flag/" + String(userId);
      infoReq.param = userId;
      
      processNetworkRequest(infoReq);
      lastInfoCheck = now;
    }
    
    // Check Pi confirmation every 2 seconds when alert active
    if (alertActive && (now - lastConfirmCheck > 2000)) {
      NetworkRequest confirmReq;
      confirmReq.type = "check_confirmation";
      confirmReq.endpoint = "/api/check_confirmation_status/" + String(userId);
      confirmReq.param = userId;
      
      processNetworkRequest(confirmReq);
      lastConfirmCheck = now;
    }
    
    vTaskDelay(pdMS_TO_TICKS(100));
  }
}

// DISPLAY TASK - Handle all TFT operations
void displayTask(void *parameter) {
  DisplayMessage msg;
  
  while (true) {
    if (xQueueReceive(displayQueue, &msg, portMAX_DELAY) == pdPASS) {
      if (xSemaphoreTake(tftMutex, pdMS_TO_TICKS(1000)) == pdTRUE) {
        processDisplayMessage(msg);
        xSemaphoreGive(tftMutex);
      }
    }
  }
}

// TOUCH TASK - Handle touch and button inputs
void touchTask(void *parameter) {
  unsigned long lastTouch = 0;
  
  while (true) {
    // Check touch sensor
    int touchValue = analogRead(33);
    
    if (touchValue > 100 && millis() - lastTouch > 300) {
      lastTouch = millis();
      
      int touchX = 160;
      int touchY = 150;
      
      Serial.println("Touch detected at: " + String(touchX) + "," + String(touchY));
      
      if (alertActive) {
        if (isTouchInArea(touchX, touchY, confirmButton)) {
          handleConfirmTouch();
        }
      } else {
        if (isTouchInArea(touchX, touchY, checkButton)) {
          handleCheckTouch();
        } else if (isTouchInArea(touchX, touchY, infoButton)) {
          handleInfoTouch();
        }
      }
    }
    
    // Check BOOT button
    if (digitalRead(0) == LOW && millis() - lastTouch > 300) {
      lastTouch = millis();
      Serial.println("BOOT button pressed!");
      
      if (alertActive) {
        handleConfirmTouch();
      } else {
        handleCheckTouch();
      }
    }
    
    vTaskDelay(pdMS_TO_TICKS(50));
  }
}

// SYSTEM TASK - System monitoring and maintenance
void systemTask(void *parameter) {
  while (true) {
    // Monitor WiFi connection
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi disconnected, attempting reconnect...");
      WiFi.reconnect();
    }
    
    // Memory cleanup if needed
    if (ESP.getFreeHeap() < 10000) {
      Serial.println("Low memory warning: " + String(ESP.getFreeHeap()));
    }
    
    vTaskDelay(pdMS_TO_TICKS(5000));
  }
}

void processNetworkRequest(NetworkRequest req) {
  if (xSemaphoreTake(wifiMutex, pdMS_TO_TICKS(5000)) != pdTRUE) {
    Serial.println("Failed to acquire WiFi mutex");
    return;
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, skipping request: " + req.type);
    xSemaphoreGive(wifiMutex);
    return;
  }
  
  HTTPClient http;
  http.begin(String(serverURL) + req.endpoint);
  http.addHeader("X-API-Key", "my-secret-key-2025");
  http.setTimeout(8000);
  
  int code = http.GET();
  String response = "";
  
  if (code > 0) {
    response = http.getString();
  }
  
  http.end();
  xSemaphoreGive(wifiMutex);
  
  // Process response based on request type
  if (req.type == "check_medicine") {
    processMedicineResponse(code, response);
  } else if (req.type == "check_info") {
    processInfoResponse(code, response);
  } else if (req.type == "check_confirmation") {
    processConfirmationResponse(code, response);
  } else if (req.type == "user_profile") {
    processUserProfileResponse(code, response);
  }
}

void processDisplayMessage(DisplayMessage msg) {
  if (msg.type == "main") {
    showMainScreen();
  } else if (msg.type == "alert") {
    showAlertScreen();
  } else if (msg.type == "info") {
    showUserInfo(msg.data);
  } else if (msg.type == "error") {
    showError(msg.data);
  } else if (msg.type == "confirm") {
    showConfirmation();
  }
}

void processMedicineResponse(int code, String response) {
  if (code == 200 && response.indexOf("medicine_name") > 0) {
    // Parse medicine data
    int start = response.indexOf("\"medicine_name\":\"") + 17;
    int end = response.indexOf("\"", start);
    medicine = response.substring(start, end);
    
    start = response.indexOf("\"compartment_number\":") + 21;
    end = response.indexOf(",", start);
    compartmentNum = response.substring(start, end).toInt();
    
    start = response.indexOf("\"schedule_id\":") + 14;
    end = response.indexOf(",", start);
    scheduleId = response.substring(start, end).toInt();
    
    if (!alertActive) {
      alertActive = true;
      DisplayMessage msg;
      msg.type = "alert";
      msg.priority = 1;
      xQueueSend(displayQueue, &msg, 0);
    }
  } else if (alertActive && response.indexOf("medicine_name") == -1) {
    alertActive = false;
    DisplayMessage msg;
    msg.type = "main";
    msg.priority = 2;
    xQueueSend(displayQueue, &msg, 0);
  }
}

void processInfoResponse(int code, String response) {
  if (code == 200 && response.indexOf("\"info_flag_detected\":true") > 0) {
    Serial.println("INFO flag detected! Processing...");
    
    // Extract flag_id
    int idStart = response.indexOf("\"flag_id\":") + 10;
    int idEnd = response.indexOf("}", idStart);
    if (idEnd == -1) idEnd = response.indexOf(",", idStart);
    int flagId = response.substring(idStart, idEnd).toInt();
    
    // Clear flag first
    clearInfoFlag(flagId);
    
    // Request user profile
    NetworkRequest profileReq;
    profileReq.type = "user_profile";
    profileReq.endpoint = "/api/user_profile/" + String(userId);
    profileReq.param = userId;
    
    // Process immediately in this task
    processNetworkRequest(profileReq);
  }
}

void processConfirmationResponse(int code, String response) {
  if (code == 200 && response.indexOf("\"confirmed\":true") > 0) {
    int idStart = response.indexOf("\"confirmation_id\":") + 18;
    int idEnd = response.indexOf("}", idStart);
    if (idEnd == -1) idEnd = response.indexOf(",", idStart);
    int confirmId = response.substring(idStart, idEnd).toInt();
    
    if (confirmId != currentConfirmationId && confirmId > 0) {
      currentConfirmationId = confirmId;
      Serial.println("PI BUTTON CONFIRMATION DETECTED!");
      
      // Clear confirmation
      clearConfirmation(confirmId);
      
      // Show confirmation display
      DisplayMessage msg;
      msg.type = "confirm";
      msg.priority = 1;
      xQueueSend(displayQueue, &msg, 0);
      
      // Reset alert state after delay
      vTaskDelay(pdMS_TO_TICKS(2000));
      alertActive = false;
      medicine = "";
      compartmentNum = 0;
      scheduleId = 0;
      
      DisplayMessage mainMsg;
      mainMsg.type = "main";
      mainMsg.priority = 2;
      xQueueSend(displayQueue, &mainMsg, 0);
    }
  }
}

void processUserProfileResponse(int code, String response) {
  if (code == 200) {
    Serial.println("Displaying user profile...");
    DisplayMessage msg;
    msg.type = "info";
    msg.data = response;
    msg.priority = 1;
    xQueueSend(displayQueue, &msg, 0);
    
    // Auto return to main screen after 5 seconds
    vTaskDelay(pdMS_TO_TICKS(5000));
    DisplayMessage mainMsg;
    mainMsg.type = "main";
    mainMsg.priority = 2;
    xQueueSend(displayQueue, &mainMsg, 0);
  }
}

void clearInfoFlag(int flagId) {
  HTTPClient http;
  http.begin(String(serverURL) + "/api/clear_info_flag/" + String(flagId));
  http.addHeader("X-API-Key", "my-secret-key-2025");
  http.addHeader("Content-Type", "application/json");
  
  int result = http.POST("{}");
  if (result == 200) {
    Serial.println("INFO flag cleared successfully!");
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
  }
  http.end();
}

// Touch handling functions
void handleCheckTouch() {
  Serial.println("Check button touched!");
  NetworkRequest req;
  req.type = "check_medicine";
  req.endpoint = "/api/check_schedule_by_user/" + String(userId);
  req.param = userId;
  xQueueSend(networkQueue, &req, 0);
}

void handleInfoTouch() {
  Serial.println("Info button touched!");
  NetworkRequest req;
  req.type = "user_profile";
  req.endpoint = "/api/user_profile/" + String(userId);
  req.param = userId;
  xQueueSend(networkQueue, &req, 0);
}

void handleConfirmTouch() {
  Serial.println("Confirm button touched!");
  if (alertActive) {
    DisplayMessage msg;
    msg.type = "confirm";
    msg.priority = 1;
    xQueueSend(displayQueue, &msg, 0);
    
    // Send confirmation to server
    HTTPClient http;
    http.begin(String(serverURL) + "/api/confirm_medicine_by_user");
    http.addHeader("X-API-Key", "my-secret-key-2025");
    http.addHeader("Content-Type", "application/json");
    
    String json = "{\"schedule_id\":" + String(scheduleId) + ",\"user_id\":" + String(userId) + "}";
    http.POST(json);
    http.end();
    
    // Reset state
    vTaskDelay(pdMS_TO_TICKS(2000));
    alertActive = false;
    medicine = "";
    compartmentNum = 0;
    scheduleId = 0;
    
    DisplayMessage mainMsg;
    mainMsg.type = "main";
    mainMsg.priority = 2;
    xQueueSend(displayQueue, &mainMsg, 0);
  }
}

bool isTouchInArea(int x, int y, TouchArea area) {
  return (x >= area.x && x <= (area.x + area.w) && 
          y >= area.y && y <= (area.y + area.h));
}

// Display functions
void showMainScreen() {
  Serial.println("Displaying main screen");
  tft.fillScreen(TFT_BLACK);
  
  tft.fillRect(0, 0, 320, 30, TFT_BLUE);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  tft.drawString("HE THONG NHAC THUOC", 30, 8);
  
  tft.setTextColor(TFT_GREEN);
  tft.setTextSize(2);
  tft.drawString("SAN SANG", 110, 40);
  
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  tft.drawString("Nguoi dung: " + String(userId), 10, 70);
  
  if (WiFi.status() == WL_CONNECTED) {
    tft.setTextColor(TFT_GREEN);
    tft.drawString("WiFi: Ket noi", 10, 85);
  } else {
    tft.setTextColor(TFT_RED);
    tft.drawString("WiFi: Loi", 10, 85);
  }
  
  drawTouchButton(checkButton, TFT_BLUE, "KIEM TRA");
  drawTouchButton(infoButton, TFT_ORANGE, "THONG TIN");
  
  tft.setTextColor(TFT_CYAN);
  tft.setTextSize(1);
  tft.drawString("CAM UNG: Cham vao nut de su dung", 40, 190);
  tft.drawString("Free RAM: " + String(ESP.getFreeHeap()), 40, 205);
}

void showAlertScreen() {
  Serial.println("Displaying alert screen");
  for (int i = 0; i < 3; i++) {
    tft.fillScreen(TFT_RED);
    vTaskDelay(pdMS_TO_TICKS(150));
    tft.fillScreen(TFT_BLACK);
    vTaskDelay(pdMS_TO_TICKS(150));
  }
  
  tft.fillScreen(TFT_BLACK);
  
  tft.fillRect(0, 0, 320, 40, TFT_RED);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(3);
  tft.drawString("UONG THUOC!", 60, 8);
  
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
  
  drawTouchButton(confirmButton, TFT_GREEN, "XAC NHAN UONG");
  
  tft.setTextColor(TFT_YELLOW);
  tft.setTextSize(1);
  tft.drawString("CAM UNG: Cham vao nut xanh", 70, 190);
  tft.drawString("CHI XAC NHAN SAU KHI UONG!", 55, 205);
}

void showUserInfo(String data) {
  Serial.println("Displaying user info");
  
  String fullName = extractJsonValue(data, "full_name");
  String age = extractJsonValue(data, "age");
  String email = extractJsonValue(data, "email");
  String phone = extractJsonValue(data, "phone");
  String dosesTaken = extractJsonValue(data, "doses_taken");
  String complianceRate = extractJsonValue(data, "compliance_rate");
  
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
  tft.drawString("Tu dong quay lai sau 5s", 60, 190);
}

void showConfirmation() {
  Serial.println("Displaying confirmation");
  tft.fillScreen(TFT_GREEN);
  tft.setTextColor(TFT_BLACK);
  tft.setTextSize(3);
  tft.drawString("XAC NHAN!", 80, 60);
  tft.setTextSize(2);
  tft.drawString("Cam on ban!", 90, 100);
  tft.setTextSize(1);
  tft.drawString("Pi button da xac nhan", 70, 140);
}

void showError(String error) {
  tft.fillRect(10, 100, 300, 40, TFT_RED);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  tft.drawString("LOI: " + error, 15, 110);
  Serial.println("ERROR: " + error);
}

void drawTouchButton(TouchArea area, uint16_t color, String text) {
  tft.fillRoundRect(area.x + 2, area.y + 2, area.w, area.h, 8, TFT_DARKGREY);
  tft.fillRoundRect(area.x, area.y, area.w, area.h, 8, color);
  tft.drawRoundRect(area.x, area.y, area.w, area.h, 8, TFT_WHITE);
  
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  int textX = area.x + (area.w - text.length() * 6) / 2;
  int textY = area.y + area.h / 2 - 4;
  tft.drawString(text, textX, textY);
}

String extractJsonValue(String json, String key) {
  int start = json.indexOf("\"" + key + "\":") + key.length() + 3;
  int end = json.indexOf(",", start);
  if (end == -1) end = json.indexOf("}", start);
  String result = json.substring(start, end);
  result.replace("\"", "");
  return result;
}