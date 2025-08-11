#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <TFT_eSPI.h>
#include <SPI.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"

// WiFi Configuration
const char* apiKey = "my-secret-key-2025";
const char* ssid = "duy";
const char* password = "11111111";
const char* serverURL = "http://192.168.1.159:5000";  // Cập nhật IP đúng
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

// FreeRTOS Components
TaskHandle_t stateManagerTaskHandle = NULL;
TaskHandle_t apiTaskHandle = NULL;
TaskHandle_t displayTaskHandle = NULL;
TaskHandle_t buttonTaskHandle = NULL;

QueueHandle_t buttonQueue;
QueueHandle_t displayQueue;
QueueHandle_t apiQueue;

SemaphoreHandle_t stateMutex;
SemaphoreHandle_t displayMutex;

// Message Types for Queues
enum MessageType {
  MSG_BUTTON_CONFIRM,
  MSG_BUTTON_INFO,
  MSG_API_SCHEDULE_FOUND,
  MSG_API_NO_SCHEDULE,
  MSG_DISPLAY_MEDICINE,
  MSG_DISPLAY_INFO,
  MSG_DISPLAY_SYSTEM,
  MSG_DISPLAY_OFF,
  MSG_STATE_CHANGE
};

struct Message {
  MessageType type;
  String data;
  int value;
};

// Timing Configuration
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
volatile bool buttonPressed = false;
unsigned long lastConfirmTime = 0;
unsigned long lastActivity = 0;

// Power Management
bool screenOn = true;
bool wifiConnected = false;
bool systemEnabled = true;  // Track system power status
unsigned long lastSystemCheck = 0;
const unsigned long SYSTEM_CHECK_INTERVAL = 5000;  // Check system status every 15 seconds

void setup() {
  Serial.begin(115200);
  
  // Initialize display
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  
  // Initialize buttons
  pinMode(CONFIRM_BUTTON_PIN, INPUT_PULLUP);
  pinMode(INFO_BUTTON_PIN, INPUT_PULLUP);
  
  // Create FreeRTOS components
  createQueues();
  createSemaphores();
  
  // Connect to WiFi
  connectToWiFi();
  
  // Create RTOS tasks
  createTasks();
  
  Serial.println("ESP32 Medicine Reminder with RTOS Power Management Started");
  
  // Send initial display message
  Message msg = {MSG_DISPLAY_SYSTEM, "startup", 0};
  xQueueSend(displayQueue, &msg, 0);
}

void loop() {
  // FreeRTOS handles everything, main loop can be minimal
  vTaskDelay(pdMS_TO_TICKS(1000));
}

void createQueues() {
  buttonQueue = xQueueCreate(10, sizeof(Message));
  displayQueue = xQueueCreate(10, sizeof(Message));
  apiQueue = xQueueCreate(5, sizeof(Message));
  
  if (!buttonQueue || !displayQueue || !apiQueue) {
    Serial.println("Failed to create queues!");
    ESP.restart();
  }
}

void createSemaphores() {
  stateMutex = xSemaphoreCreateMutex();
  displayMutex = xSemaphoreCreateMutex();
  
  if (!stateMutex || !displayMutex) {
    Serial.println("Failed to create semaphores!");
    ESP.restart();
  }
}

void createTasks() {
  // State Manager Task - Core 1, High Priority (reduced stack)
  xTaskCreatePinnedToCore(
    stateManagerTask,
    "StateManager",
    3072,
    NULL,
    3,
    &stateManagerTaskHandle,
    1
  );
  
  // API Task - Core 0, Medium Priority (reduced stack)
  xTaskCreatePinnedToCore(
    apiTask,
    "APITask",
    6144,
    NULL,
    2,
    &apiTaskHandle,
    0
  );
  
  // Display Task - Core 1, Medium Priority (reduced stack)
  xTaskCreatePinnedToCore(
    displayTask,
    "DisplayTask",
    3072,
    NULL,
    2,
    &displayTaskHandle,
    1
  );
  
  // Button Task - Core 1, High Priority (reduced stack)
  xTaskCreatePinnedToCore(
    buttonTask,
    "ButtonTask",
    1536,
    NULL,
    4,
    &buttonTaskHandle,
    1
  );
  
  Serial.println("All RTOS tasks created successfully");
  logMemoryUsage("After task creation");
}

void stateManagerTask(void *parameter) {
  Message msg;
  TickType_t lastWakeTime = xTaskGetTickCount();
  
  while (true) {
    // Check for messages from other tasks
    if (xQueueReceive(buttonQueue, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
      handleStateMessage(msg);
    }
    
    if (xQueueReceive(apiQueue, &msg, 0) == pdTRUE) {
      handleStateMessage(msg);
    }
    
    // State-specific logic
    xSemaphoreTake(stateMutex, portMAX_DELAY);
    
    switch (currentState) {
      case SLEEP_MODE:
        handleSleepState();
        break;
        
      case ACTIVE_MODE:
        handleActiveState();
        break;
        
      case CONFIRMED_MODE:
        handleConfirmedState();
        break;
    }
    
    xSemaphoreGive(stateMutex);
    
    // Run every 100ms
    vTaskDelayUntil(&lastWakeTime, pdMS_TO_TICKS(100));
  }
}

void apiTask(void *parameter) {
  TickType_t lastAPICheck = 0;
  
  while (true) {
    TickType_t currentTick = xTaskGetTickCount();
    unsigned long interval;
    
    // Check system status periodically
    if (millis() - lastSystemCheck >= SYSTEM_CHECK_INTERVAL) {
      checkSystemStatus();
      lastSystemCheck = millis();
    }
    
    // Skip medicine schedule check if system is disabled
    if (!systemEnabled) {
      Serial.println("RTOS: System disabled - skipping schedule check");
      vTaskDelay(pdMS_TO_TICKS(5000));
      continue;
    }
    
    // Determine API check interval based on state
    xSemaphoreTake(stateMutex, portMAX_DELAY);
    if (currentState == SLEEP_MODE) {
      interval = SLEEP_API_INTERVAL;
    } else {
      interval = ACTIVE_API_INTERVAL;
    }
    xSemaphoreGive(stateMutex);
    
    // Check if it's time for API call
    if (currentTick - lastAPICheck >= pdMS_TO_TICKS(interval)) {
      lastAPICheck = currentTick;
      
      bool hasSchedule = checkForMedicineSchedule();
      
      Message msg;
      if (hasSchedule) {
        msg = {MSG_API_SCHEDULE_FOUND, currentMedicineName, currentCompartment};
      } else {
        msg = {MSG_API_NO_SCHEDULE, "", 0};
      }
      
      xQueueSend(apiQueue, &msg, 0);
    }
    
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}

void displayTask(void *parameter) {
  Message msg;
  
  while (true) {
    if (xQueueReceive(displayQueue, &msg, portMAX_DELAY) == pdTRUE) {
      xSemaphoreTake(displayMutex, portMAX_DELAY);
      
      switch (msg.type) {
        case MSG_DISPLAY_MEDICINE:
          displayMedicineNotification(msg.data, msg.value);
          break;
          
        case MSG_DISPLAY_INFO:
          displayUserInfo();
          break;
          
        case MSG_DISPLAY_SYSTEM:
          displaySystemInfo();
          break;
          
        case MSG_DISPLAY_OFF:
          turnOffScreen();
          break;
          
        default:
          break;
      }
      
      xSemaphoreGive(displayMutex);
    }
  }
}

void buttonTask(void *parameter) {
  bool lastConfirmState = HIGH;
  bool lastInfoState = HIGH;
  TickType_t lastDebounceTime = 0;
  
  while (true) {
    bool confirmState = digitalRead(CONFIRM_BUTTON_PIN);
    bool infoState = digitalRead(INFO_BUTTON_PIN);
    TickType_t currentTick = xTaskGetTickCount();
    
    // Debounce protection
    if (currentTick - lastDebounceTime < pdMS_TO_TICKS(DEBOUNCE_DELAY)) {
      vTaskDelay(pdMS_TO_TICKS(50));
      continue;
    }
    
    // Confirm button pressed
    if (lastConfirmState == HIGH && confirmState == LOW) {
      lastDebounceTime = currentTick;
      lastActivity = millis();
      
      Message msg = {MSG_BUTTON_CONFIRM, "", 0};
      xQueueSend(buttonQueue, &msg, 0);
      
      Serial.println("RTOS: Confirm button pressed");
    }
    
    // Info button pressed
    if (lastInfoState == HIGH && infoState == LOW) {
      lastDebounceTime = currentTick;
      lastActivity = millis();
      
      Message msg = {MSG_BUTTON_INFO, "", 0};
      xQueueSend(buttonQueue, &msg, 0);
      
      Serial.println("RTOS: Info button pressed");
    }
    
    lastConfirmState = confirmState;
    lastInfoState = infoState;
    
    vTaskDelay(pdMS_TO_TICKS(50));
  }
}

void handleStateMessage(Message msg) {
  switch (msg.type) {
    case MSG_BUTTON_CONFIRM:
      handleConfirmButton();
      break;
      
    case MSG_BUTTON_INFO:
      handleInfoButton();
      break;
      
    case MSG_API_SCHEDULE_FOUND:
      if (currentState == SLEEP_MODE) {
        currentMedicineName = msg.data;
        currentCompartment = msg.value;
        changeState(ACTIVE_MODE);
      }
      break;
      
    case MSG_API_NO_SCHEDULE:
      if (currentState == ACTIVE_MODE && !sessionActive) {
        changeState(SLEEP_MODE);
      }
      break;
      
    default:
      break;
  }
}

void handleSleepState() {
  static bool screenTurnedOff = false;
  
  if (!screenTurnedOff) {
    Message msg = {MSG_DISPLAY_OFF, "", 0};
    xQueueSend(displayQueue, &msg, 0);
    screenTurnedOff = true;
  }
}

void handleActiveState() {
  static bool medicineDisplayed = false;
  static unsigned long stateStartTime = 0;
  
  if (!medicineDisplayed) {
    Message msg = {MSG_DISPLAY_MEDICINE, currentMedicineName, currentCompartment};
    xQueueSend(displayQueue, &msg, 0);
    medicineDisplayed = true;
    stateStartTime = millis();
    sessionActive = true;
  }
  
  // Check for timeout
  if (millis() - stateStartTime > ACTIVITY_TIMEOUT) {
    Serial.println("RTOS: Activity timeout");
    changeState(SLEEP_MODE);
    medicineDisplayed = false;
  }
}

void handleConfirmedState() {
  static unsigned long confirmedStartTime = 0;
  static bool delayStarted = false;
  
  if (!delayStarted) {
    confirmedStartTime = millis();
    delayStarted = true;
  }
  
  if (millis() - confirmedStartTime > CONFIRMED_DELAY) {
    changeState(SLEEP_MODE);
    delayStarted = false;
  }
}

void handleConfirmButton() {
  // Block all actions if system is disabled
  if (!systemEnabled) {
    Serial.println("RTOS: Confirm blocked - system disabled");
    Message msg = {MSG_DISPLAY_SYSTEM, "disabled", 0};
    xQueueSend(displayQueue, &msg, 0);
    return;
  }
  
  if (currentState == ACTIVE_MODE && sessionActive && !medicineConfirmed) {
    // Anti-spam: check minimum time since last confirm
    if (millis() - lastConfirmTime < MIN_SLEEP_TIME) {
      Serial.println("RTOS: Confirm blocked - too soon");
      return;
    }
    
    // Confirm medicine in separate task to avoid blocking
    xTaskCreate(confirmMedicineTask, "ConfirmMed", 4096, NULL, 1, NULL);
    
  } else if (currentState == SLEEP_MODE) {
    // Wake up from sleep mode
    changeState(ACTIVE_MODE);
    Message msg = {MSG_DISPLAY_SYSTEM, "", 0};
    xQueueSend(displayQueue, &msg, 0);
  }
}

void handleInfoButton() {
  Message msg = {MSG_DISPLAY_INFO, "", 0};
  xQueueSend(displayQueue, &msg, 0);
  
  // Auto return to previous display after 3 seconds
  xTaskCreate(autoReturnTask, "AutoReturn", 1024, NULL, 1, NULL);
}

void confirmMedicineTask(void *parameter) {
  if (confirmMedicine()) {
    medicineConfirmed = true;
    lastConfirmTime = millis();
    
    Serial.println("RTOS: Medicine confirmed successfully");
    changeState(CONFIRMED_MODE);
  } else {
    Serial.println("RTOS: Medicine confirmation failed");
  }
  
  vTaskDelete(NULL);
}

void autoReturnTask(void *parameter) {
  vTaskDelay(pdMS_TO_TICKS(3000));
  
  xSemaphoreTake(stateMutex, portMAX_DELAY);
  if (currentState == ACTIVE_MODE && sessionActive) {
    Message msg = {MSG_DISPLAY_MEDICINE, currentMedicineName, currentCompartment};
    xQueueSend(displayQueue, &msg, 0);
  } else {
    Message msg = {MSG_DISPLAY_SYSTEM, "", 0};
    xQueueSend(displayQueue, &msg, 0);
  }
  xSemaphoreGive(stateMutex);
  
  vTaskDelete(NULL);
}

void changeState(DeviceState newState) {
  if (currentState == newState) return;
  
  DeviceState oldState = currentState;
  currentState = newState;
  
  Serial.print("RTOS State change: ");
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
      break;
      
    case ACTIVE_MODE:
      if (!sessionActive) {
        sessionActive = true;
      }
      turnOnScreen();
      break;
      
    case CONFIRMED_MODE:
      // Display confirmation message
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
    // Use TFT_eSPI backlight control instead of display commands
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH);  // Turn on backlight
    delay(100);
    tft.fillScreen(TFT_BLACK);
    Serial.println("RTOS: Screen ON with backlight");
    logMemoryUsage("Screen ON");
  }
}

void turnOffScreen() {
  if (screenOn) {
    screenOn = false;
    tft.fillScreen(TFT_BLACK);
    // Turn off backlight instead of display
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, LOW);   // Turn off backlight
    Serial.println("RTOS: Screen OFF - Backlight disabled");
  }
}

bool checkSystemStatus() {
  if (!wifiConnected) {
    connectToWiFi();
    if (!wifiConnected) return systemEnabled;  // Keep current status if can't connect
  }
  
  HTTPClient http;
  String url = String(serverURL) + "/api/system_status";
  
  http.begin(url);
  http.addHeader("X-API-Key", apiKey);
  
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    DynamicJsonDocument doc(512);  // Reduced JSON buffer size
    
    if (deserializeJson(doc, response) == DeserializationError::Ok) {
      bool newStatus = doc["system_enabled"].as<bool>();
      
      if (newStatus != systemEnabled) {
        systemEnabled = newStatus;
        String statusText = systemEnabled ? "ENABLED" : "DISABLED";
        Serial.println("RTOS: System status changed to " + statusText);
        
        // Update display to show system status change
        Message msg = {MSG_DISPLAY_SYSTEM, "status_change", systemEnabled ? 1 : 0};
        xQueueSend(displayQueue, &msg, 0);
        
        // If system is disabled, force sleep mode
        if (!systemEnabled && currentState != SLEEP_MODE) {
          changeState(SLEEP_MODE);
        }
      }
    }
  } else {
    Serial.println("RTOS: Failed to check system status: " + String(httpResponseCode));
  }
  
  http.end();
  return systemEnabled;
}

bool checkForMedicineSchedule() {
  if (!wifiConnected) {
    connectToWiFi();
    if (!wifiConnected) return false;
  }
  
  // Don't check medicine schedule if system is disabled
  if (!systemEnabled) {
    return false;
  }
  
  HTTPClient http;
  String url = String(serverURL) + "/api/check_schedule_by_user/" + String(userId);
  
  http.begin(url);
  http.addHeader("X-API-Key", apiKey);
  
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    DynamicJsonDocument doc(1024);  // Reduced JSON buffer size
    
    if (deserializeJson(doc, response) == DeserializationError::Ok) {
      if (doc.size() > 0) {
        // Medicine schedule found
        JsonObject schedule = doc[0];
        currentMedicineName = schedule["medicine_name"].as<String>();
        currentCompartment = schedule["compartment_number"];
        
        Serial.println("RTOS: Medicine schedule found - " + currentMedicineName);
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
  
  DynamicJsonDocument doc(512);  // Reduced JSON buffer size
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
  logMemoryUsage("Before display medicine");
  
  // Force screen on and ensure backlight is active
  screenOn = true;
  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, HIGH);
  delay(200);  // Longer delay for display stabilization
  
  // Re-initialize display if needed
  tft.init();
  tft.setRotation(1);
  
  // Clear screen with bright color first to test display
  tft.fillScreen(TFT_RED);
  delay(100);
  tft.fillScreen(TFT_BLACK);
  delay(100);
  
  Serial.println("RTOS: Display medicine notification starting...");
  
  // Header with bright colors for visibility
  tft.setTextColor(TFT_WHITE, TFT_BLUE);
  tft.setTextSize(2);
  tft.fillRect(0, 0, 320, 40, TFT_BLUE);
  tft.drawCentreString("UONG THUOC", 160, 10, 2);
  
  // Medicine info with bright colors
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.setTextSize(3);
  tft.drawCentreString(medicineName, 160, 60, 2);
  
  // Compartment info
  tft.setTextColor(TFT_RED, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawCentreString("NGAN " + String(compartment), 160, 110, 2);
  
  // Instructions with bright color
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawCentreString("NHAN BOOT XAC NHAN", 160, 150, 2);
  
  // Debug info
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawString("Screen: ON", 10, 200, 1);
  tft.drawString("Backlight: HIGH", 10, 215, 1);
  
  Serial.println("RTOS: Display medicine notification completed");
  logMemoryUsage("After display medicine");
}

void displayUserInfo() {
  if (!screenOn) turnOnScreen();
  
  tft.fillScreen(TFT_BLACK);
  
  // Header
  tft.setTextColor(TFT_WHITE, TFT_GREEN);
  tft.setTextSize(2);
  tft.fillRect(0, 0, 320, 40, TFT_GREEN);
  tft.drawCentreString("THÔNG TIN RTOS", 160, 10, 2);
  
  // RTOS info
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawString("User ID: " + String(userId), 10, 60, 2);
  tft.drawString("State: " + getStateName(currentState), 10, 80, 2);
  tft.drawString("Tasks: " + String(uxTaskGetNumberOfTasks()), 10, 100, 2);
  tft.drawString("Free Heap: " + String(ESP.getFreeHeap()), 10, 120, 2);
  
  // Task info
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.drawString("Core 0 Tasks: API", 10, 150, 2);
  tft.drawString("Core 1 Tasks: State, Display, Button", 10, 170, 2);
  tft.drawString("WiFi: " + String(wifiConnected ? "OK" : "Failed"), 10, 190, 2);
  
  // Queue status
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawString("Button Q: " + String(uxQueueMessagesWaiting(buttonQueue)), 160, 150, 1);
  tft.drawString("Display Q: " + String(uxQueueMessagesWaiting(displayQueue)), 160, 160, 1);
  tft.drawString("API Q: " + String(uxQueueMessagesWaiting(apiQueue)), 160, 170, 1);
}

void displaySystemInfo() {
  // Force screen on
  screenOn = true;
  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, HIGH);
  delay(100);
  
  tft.fillScreen(TFT_BLACK);
  
  // Header with system status color
  uint16_t headerColor = systemEnabled ? TFT_PURPLE : TFT_RED;
  tft.setTextColor(TFT_WHITE, headerColor);
  tft.setTextSize(2);
  tft.fillRect(0, 0, 320, 40, headerColor);
  tft.drawCentreString("RTOS MEDICINE", 160, 10, 2);
  
  // System Power Status
  tft.setTextColor(systemEnabled ? TFT_GREEN : TFT_RED, TFT_BLACK);
  tft.setTextSize(2);
  String statusText = systemEnabled ? "ENABLED" : "DISABLED";
  tft.drawCentreString(statusText, 160, 50, 2);
  
  // State Status
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawCentreString("State: " + getStateName(currentState), 160, 90, 2);
  
  // Connection status
  tft.setTextColor(wifiConnected ? TFT_GREEN : TFT_RED, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawCentreString("WiFi: " + String(wifiConnected ? "OK" : "FAIL"), 160, 130, 2);
  
  // Test display with bright colors
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawCentreString("DISPLAY TEST ACTIVE", 160, 170, 2);
  
  Serial.println("RTOS: System info displayed");
}

void connectToWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    return;
  }
  
  Serial.print("RTOS: Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    vTaskDelay(pdMS_TO_TICKS(500));
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\nRTOS: WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    wifiConnected = false;
    Serial.println("\nRTOS: WiFi connection failed!");
  }
}

// Memory monitoring function
void logMemoryUsage(String location) {
  Serial.printf("RTOS Memory [%s]: Free Heap: %d, Min Free: %d, Stack HWM: %d\n",
    location.c_str(), ESP.getFreeHeap(), ESP.getMinFreeHeap(),
    uxTaskGetStackHighWaterMark(NULL));
}