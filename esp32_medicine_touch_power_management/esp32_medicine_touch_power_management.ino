#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <TFT_eSPI.h>
#include <SPI.h>

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server Configuration
const char* serverURL = "http://192.168.1.100:5000";
const char* apiKey = "your-api-key-here";
const int userId = 13;

// TFT Display
TFT_eSPI tft = TFT_eSPI();

// Device State Management
enum DeviceState {
  SLEEP_MODE,      // Screen off, minimal API checks
  ACTIVE_MODE,     // Medicine notification active
  CONFIRMED_MODE   // User confirmed, preparing to sleep
};

DeviceState currentState = SLEEP_MODE;

// Timing Configuration
unsigned long lastAPICheck = 0;
unsigned long lastActivity = 0;
unsigned long lastButtonPress = 0;
unsigned long sessionStartTime = 0;
unsigned long lastStateChange = 0;

// Intervals (milliseconds)
const unsigned long SLEEP_API_INTERVAL = 30000;    // 30 seconds in sleep
const unsigned long ACTIVE_API_INTERVAL = 5000;    // 5 seconds when active
const unsigned long ACTIVITY_TIMEOUT = 180000;     // 3 minutes timeout
const unsigned long DEBOUNCE_DELAY = 2000;         // 2 seconds button debounce
const unsigned long CONFIRMED_DELAY = 5000;        // 5 seconds before sleep after confirm
const unsigned long MIN_SLEEP_TIME = 300000;       // 5 minutes minimum sleep after confirm

// Button Configuration
const int CONFIRM_BUTTON_PIN = 0;  // BOOT button
const int INFO_BUTTON_PIN = 35;    // Touch or additional button

// Session Management
bool sessionActive = false;
bool medicineConfirmed = false;
String currentMedicineName = "";
int currentCompartment = 0;

// Anti-spam Protection
bool buttonDebounced = true;
unsigned long lastConfirmTime = 0;

// Power Management
bool screenOn = true;
bool wifiConnected = false;

void setup() {
  Serial.begin(115200);
  
  // Initialize display
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  
  // Initialize buttons
  pinMode(CONFIRM_BUTTON_PIN, INPUT_PULLUP);
  pinMode(INFO_BUTTON_PIN, INPUT_PULLUP);
  
  // Connect to WiFi
  connectToWiFi();
  
  // Initialize state
  changeState(SLEEP_MODE);
  
  Serial.println("ESP32 Medicine Reminder with Power Management Started");
  displaySystemInfo();
}

void loop() {
  updateDeviceState();
  handleButtons();
  
  // Non-blocking delay
  delay(100);
}

void updateDeviceState() {
  unsigned long currentTime = millis();
  
  switch (currentState) {
    case SLEEP_MODE:
      handleSleepMode(currentTime);
      break;
      
    case ACTIVE_MODE:
      handleActiveMode(currentTime);
      break;
      
    case CONFIRMED_MODE:
      handleConfirmedMode(currentTime);
      break;
  }
}

void handleSleepMode(unsigned long currentTime) {
  // Turn off screen if not already off
  if (screenOn) {
    turnOffScreen();
  }
  
  // Check for medicine schedules every 30 seconds
  if (currentTime - lastAPICheck >= SLEEP_API_INTERVAL) {
    lastAPICheck = currentTime;
    
    if (checkForMedicineSchedule()) {
      changeState(ACTIVE_MODE);
    }
  }
}

void handleActiveMode(unsigned long currentTime) {
  // Turn on screen if not already on
  if (!screenOn) {
    turnOnScreen();
  }
  
  // Check for updates every 5 seconds
  if (currentTime - lastAPICheck >= ACTIVE_API_INTERVAL) {
    lastAPICheck = currentTime;
    
    // Re-check medicine schedule (in case it was cancelled)
    if (!checkForMedicineSchedule()) {
      changeState(SLEEP_MODE);
      return;
    }
  }
  
  // Check for activity timeout
  if (currentTime - lastActivity >= ACTIVITY_TIMEOUT) {
    Serial.println("Activity timeout - going to sleep");
    changeState(SLEEP_MODE);
  }
}

void handleConfirmedMode(unsigned long currentTime) {
  // Wait 5 seconds before going to sleep
  if (currentTime - lastStateChange >= CONFIRMED_DELAY) {
    changeState(SLEEP_MODE);
  }
}

void handleButtons() {
  unsigned long currentTime = millis();
  
  // Debounce protection
  if (!buttonDebounced && (currentTime - lastButtonPress < DEBOUNCE_DELAY)) {
    return;
  }
  buttonDebounced = true;
  
  // Confirm button (BOOT)
  if (digitalRead(CONFIRM_BUTTON_PIN) == LOW && buttonDebounced) {
    lastButtonPress = currentTime;
    buttonDebounced = false;
    lastActivity = currentTime;
    
    handleConfirmButton();
  }
  
  // Info button
  if (digitalRead(INFO_BUTTON_PIN) == LOW && buttonDebounced) {
    lastButtonPress = currentTime;
    buttonDebounced = false;
    lastActivity = currentTime;
    
    handleInfoButton();
  }
}

void handleConfirmButton() {
  if (currentState == ACTIVE_MODE && sessionActive && !medicineConfirmed) {
    // Anti-spam: check minimum time since last confirm
    if (millis() - lastConfirmTime < MIN_SLEEP_TIME) {
      displayMessage("Vui lòng chờ...", TFT_YELLOW, 2000);
      return;
    }
    
    // Confirm medicine
    if (confirmMedicine()) {
      medicineConfirmed = true;
      lastConfirmTime = millis();
      displayMessage("Đã xác nhận!", TFT_GREEN, 3000);
      changeState(CONFIRMED_MODE);
    } else {
      displayMessage("Lỗi xác nhận!", TFT_RED, 2000);
    }
  } else if (currentState == SLEEP_MODE) {
    // Wake up from sleep mode
    changeState(ACTIVE_MODE);
    displaySystemInfo();
  }
}

void handleInfoButton() {
  if (screenOn) {
    displayUserInfo();
  } else {
    turnOnScreen();
    displaySystemInfo();
  }
}

void changeState(DeviceState newState) {
  if (currentState == newState) return;
  
  DeviceState oldState = currentState;
  currentState = newState;
  lastStateChange = millis();
  
  Serial.print("State change: ");
  Serial.print(getStateName(oldState));
  Serial.print(" -> ");
  Serial.println(getStateName(newState));
  
  // State-specific initialization
  switch (newState) {
    case SLEEP_MODE:
      sessionActive = false;
      medicineConfirmed = false;
      currentMedicineName = "";
      currentCompartment = 0;
      turnOffScreen();
      break;
      
    case ACTIVE_MODE:
      turnOnScreen();
      if (!sessionActive) {
        sessionActive = true;
        sessionStartTime = millis();
      }
      break;
      
    case CONFIRMED_MODE:
      displayMessage("Cảm ơn!", TFT_GREEN, 0);
      break;
  }
  
  lastActivity = millis();
}

String getStateName(DeviceState state) {
  switch (state) {
    case SLEEP_MODE: return "SLEEP";
    case ACTIVE_MODE: return "ACTIVE";
    case CONFIRMED_MODE: return "CONFIRMED";
    default: return "UNKNOWN";
  }
}

void turnOnScreen() {
  if (!screenOn) {
    screenOn = true;
    tft.writecommand(TFT_DISPON);
    Serial.println("Screen ON");
  }
}

void turnOffScreen() {
  if (screenOn) {
    screenOn = false;
    tft.fillScreen(TFT_BLACK);
    tft.writecommand(TFT_DISPOFF);
    Serial.println("Screen OFF - Power Save Mode");
  }
}

bool checkForMedicineSchedule() {
  if (!wifiConnected) {
    connectToWiFi();
    if (!wifiConnected) return false;
  }
  
  HTTPClient http;
  String url = String(serverURL) + "/api/check_schedule_by_user/" + String(userId);
  
  http.begin(url);
  http.addHeader("X-API-Key", apiKey);
  
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    DynamicJsonDocument doc(2048);
    
    if (deserializeJson(doc, response) == DeserializationError::Ok) {
      if (doc.size() > 0) {
        // Medicine schedule found
        JsonObject schedule = doc[0];
        currentMedicineName = schedule["medicine_name"].as<String>();
        currentCompartment = schedule["compartment_number"];
        
        displayMedicineNotification(currentMedicineName, currentCompartment);
        return true;
      }
    }
  }
  
  http.end();
  return false;
}

bool confirmMedicine() {
  if (!wifiConnected) return false;
  
  HTTPClient http;
  String url = String(serverURL) + "/api/confirm_medicine_by_user";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", apiKey);
  
  DynamicJsonDocument doc(1024);
  doc["user_id"] = userId;
  doc["schedule_id"] = 1; // This should come from the schedule check
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  bool success = (httpResponseCode == 200);
  
  http.end();
  return success;
}

void displayMedicineNotification(String medicineName, int compartment) {
  if (!screenOn) return;
  
  tft.fillScreen(TFT_BLACK);
  
  // Header
  tft.setTextColor(TFT_WHITE, TFT_BLUE);
  tft.setTextSize(2);
  tft.fillRect(0, 0, 320, 40, TFT_BLUE);
  tft.drawCentreString("NHẮC UỐNG THUỐC", 160, 10, 2);
  
  // Medicine info
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(3);
  tft.drawCentreString(medicineName, 160, 70, 2);
  
  // Compartment info
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawCentreString("NGĂN " + String(compartment), 160, 120, 2);
  
  // Instructions
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawCentreString("Nhấn nút BOOT để xác nhận", 160, 160, 2);
  
  // Time info
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.drawCentreString("Thời gian: " + getCurrentTime(), 160, 190, 2);
  
  // State info
  tft.setTextColor(TFT_MAGENTA, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawString("State: " + getStateName(currentState), 10, 220, 1);
  tft.drawString("Session: " + String(sessionActive ? "Active" : "Inactive"), 10, 230, 1);
}

void displayUserInfo() {
  if (!screenOn) return;
  
  tft.fillScreen(TFT_BLACK);
  
  // Header
  tft.setTextColor(TFT_WHITE, TFT_GREEN);
  tft.setTextSize(2);
  tft.fillRect(0, 0, 320, 40, TFT_GREEN);
  tft.drawCentreString("THÔNG TIN NGƯỜI DÙNG", 160, 10, 2);
  
  // User info (this would come from API)
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawString("User ID: " + String(userId), 10, 60, 2);
  tft.drawString("Trạng thái: Hoạt động", 10, 80, 2);
  tft.drawString("Kết nối: " + String(wifiConnected ? "OK" : "Lỗi"), 10, 100, 2);
  tft.drawString("Pin: Tốt", 10, 120, 2);
  
  // System info
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.drawString("State: " + getStateName(currentState), 10, 150, 2);
  tft.drawString("Uptime: " + String(millis()/1000) + "s", 10, 170, 2);
  tft.drawString("Free Heap: " + String(ESP.getFreeHeap()), 10, 190, 2);
  
  delay(3000);
  
  if (currentState == ACTIVE_MODE && sessionActive) {
    displayMedicineNotification(currentMedicineName, currentCompartment);
  } else {
    displaySystemInfo();
  }
}

void displaySystemInfo() {
  if (!screenOn) return;
  
  tft.fillScreen(TFT_BLACK);
  
  // Header
  tft.setTextColor(TFT_WHITE, TFT_PURPLE);
  tft.setTextSize(2);
  tft.fillRect(0, 0, 320, 40, TFT_PURPLE);
  tft.drawCentreString("HỆ THỐNG NHẮC THUỐC", 160, 10, 2);
  
  // Status
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawCentreString("Trạng thái: " + getStateName(currentState), 160, 70, 2);
  tft.drawCentreString("Thời gian: " + getCurrentTime(), 160, 100, 2);
  
  // Connection status
  tft.setTextColor(wifiConnected ? TFT_GREEN : TFT_RED, TFT_BLACK);
  tft.drawCentreString("WiFi: " + String(wifiConnected ? "Kết nối" : "Mất kết nối"), 160, 130, 2);
  
  // Instructions based on state
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  if (currentState == SLEEP_MODE) {
    tft.drawCentreString("Đang chờ lịch thuốc...", 160, 160, 2);
    tft.drawCentreString("Nhấn BOOT để thức", 160, 180, 1);
  } else {
    tft.drawCentreString("Nhấn BOOT để info", 160, 160, 1);
  }
}

void displayMessage(String message, uint16_t color, int duration) {
  if (!screenOn) return;
  
  tft.fillRect(0, 200, 320, 40, TFT_BLACK);
  tft.setTextColor(color, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawCentreString(message, 160, 210, 2);
  
  if (duration > 0) {
    delay(duration);
  }
}

String getCurrentTime() {
  unsigned long seconds = millis() / 1000;
  unsigned long minutes = seconds / 60;
  unsigned long hours = minutes / 60;
  
  return String(hours % 24) + ":" + 
         String((minutes % 60) < 10 ? "0" : "") + String(minutes % 60) + ":" +
         String((seconds % 60) < 10 ? "0" : "") + String(seconds % 60);
}

void connectToWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    return;
  }
  
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    wifiConnected = false;
    Serial.println("\nWiFi connection failed!");
  }
}