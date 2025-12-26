#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <SPIFFS.h>

const char* ssid = "duy"; 
const char* password = "11111111"; 

Adafruit_MPU6050 mpu;
WebServer server(80);

const char* filename = "/sensor_data4.csv";


bool isRecording = false;
String currentActivityLabel = "unknown"; 


const unsigned long sampleInterval = 20; 
unsigned long lastSampleTime = 0;

const int bufferSize = 200; 
String dataBuffer[bufferSize];
int bufferIndex = 0;

void checkSPIFFSSpace() {
  size_t totalBytes = SPIFFS.totalBytes();
  size_t usedBytes = SPIFFS.usedBytes();
  Serial.printf("SPIFFS: %d bytes used out of %d bytes total\n", usedBytes, totalBytes);
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22); 

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Connected!");

 
  // Initialize SPIFFS
  if (!SPIFFS.begin(true)) {
    Serial.println("Formatting SPIFFS...");
    SPIFFS.format();
    Serial.println("SPIFFS formatted");
    if (!SPIFFS.begin(true)) {
      Serial.println("SPIFFS init failed!");
      while(1);
    }
  }
  Serial.println("SPIFFS mounted successfully");
  Serial.print("Web server IP: ");
  Serial.println(WiFi.localIP());
  // Kiểm tra dung lượng SPIFFS
  checkSPIFFSSpace(); 

  if (SPIFFS.exists(filename)) {
    SPIFFS.remove(filename);
    Serial.println("Old CSV file removed");
  }

  // Create CSV file
  File file = SPIFFS.open(filename, FILE_WRITE);
  if (file) {
    file.println("Time,AccelX,AccelY,AccelZ,GyroX,GyroY,GyroZ,ActivityLabel"); 
    file.close();
    Serial.println("CSV file created successfully");
  } else {
    Serial.println("Failed to create CSV file");
    return;
  }

  // Initialize MPU6050 sensor
  if (!mpu.begin(0x68)) {
    Serial.println("MPU6050 initialization failed. Check wiring!");
    while (1);
  }
  Serial.println("MPU6050 initialized!");

  // Configure web server routes
  server.on("/", handleRoot);
  server.on("/toggleRecord", handleToggleRecord);
  server.on("/download", handleDownload);
  server.on("/sensorData", handleSensorData);
  server.begin();
  Serial.println("Web server started");
}

void handleRoot() {
  String ipAddress = WiFi.localIP().toString();
  String message = R"rawliteral(
    <html>
      <head > <meta charset="UTF-8">

        <title>MPU6050 Sensor Data</title>
        <style>
          .button-activity {
            padding: 10px 20px;
            font-size: 16px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            background-color: #4CAF50;
            color: white;
            cursor: pointer;
          }
          .button-activity.selected {
            background-color: #008CBA;
          }
          #sensorData {
            text-align: center;
            margin-top: 20px;
          }
        </style>
      </head>
      <body>
        <center><h1>MPU6050 Sensor Data</h1></center>
        <div style="text-align:center;">
          <button class="button-activity" onclick="startRecording('fall_forward')" id="fall_forwardBtn">Fall_forward</button>
          <button class="button-activity" onclick="startRecording('fall_backward')" id="fall_backwardBtn">Fall_backward</button>
          <button class="button-activity" onclick="startRecording('fall_left')" id="fall_leftBtn">Fall_left</button>
          <button class="button-activity" onclick="startRecording('fall_right')" id="fall_rightBtn">Fall_right</button>
          <button class="button-activity" onclick="startRecording('standing')" id="standingBtn">Standing</button>
          <button id="recordButton" style="display:none;" onclick="stopRecording()">Stop Recording</button> <br><br>
          <span id="activityLabelDisplay">Hoạt động hiện tại: Chưa xác định</span>
        </div>

        <a href="/download" id="downloadLink" style="display:none;">Tải dữ liệu CSV</a>
        <div id="sensorData">
          <h2>Dữ liệu cảm biến trực tiếp</h2>
          <p>Loading...</p>
        </div>

        <script>
          let currentActivity = 'unknown';
          let isRecordingNow = false;
          const activityButtons = document.querySelectorAll('.button-activity');
          const recordButton = document.getElementById('recordButton');
          const downloadLink = document.getElementById('downloadLink');
          const activityLabelDisplay = document.getElementById('activityLabelDisplay');

          function startRecording(activity) {
            if (!isRecordingNow) {
              currentActivity = activity;
              activityLabelDisplay.innerText = 'Hoạt động hiện tại: ' + formatActivity(activity);
              activityButtons.forEach(btn => btn.classList.remove('selected'));
              document.getElementById(activity + 'Btn').classList.add('selected');

              fetch('/toggleRecord?activity=' + activity)
                .then(response => response.text())
                .then(state => {
                  if (state === 'true') {
                    isRecordingNow = true;
                    recordButton.style.display = 'inline-block';
                    activityButtons.forEach(btn => btn.disabled = true);
                  }
                });
            }
          }

          function stopRecording() {
            if (isRecordingNow) {
              fetch('/toggleRecord', {method: 'POST'})
                .then(response => response.text())
                .then(state => {
                  if (state === 'false') {
                    isRecordingNow = false;
                    recordButton.style.display = 'none';
                    downloadLink.style.display = 'block';
                    activityButtons.forEach(btn => {
                      btn.classList.remove('selected');
                      btn.disabled = false;
                    });
                    activityLabelDisplay.innerText = 'Hoạt động hiện tại: Chưa xác định';
                    currentActivity = 'unknown';
                  }
                });
            }
          }

          function formatActivity(activity) {
            switch (activity) {
              case 'fall_forward': return 'Ngã về phía trước';
              case 'fall_backward': return 'Ngã về phía sau';
              case 'fall_left': return 'Ngã sang trái';
              case 'fall_right': return 'Ngã sang phải';
              case 'standing': return 'Đứng bình thường';
              default: return 'Chưa xác định';
            }
          }

          setInterval(() => {
            fetch('/sensorData')
              .then(response => response.json())
              .then(data => {
                document.getElementById('sensorData').innerHTML = `
                  <h2>Dữ liệu cảm biến trực tiếp</h2>
                  <p>Thời gian: ${data.time}</p>
                  <p>Hoạt động: ${formatActivity(currentActivity)}</p>
                  <p>AccelX: ${data.accelX.toFixed(2)} m/s²</p>
                  <p>AccelY: ${data.accelY.toFixed(2)} m/s²</p>
                  <p>AccelZ: ${data.accelZ.toFixed(2)} m/s²</p>
                  <p>GyroX: ${data.gyroX.toFixed(2)} °/s</p>
                  <p>GyroY: ${data.gyroY.toFixed(2)} °/s</p>
                  <p>GyroZ: ${data.gyroZ.toFixed(2)} °/s</p>
                `;
              });
          }, 500);
        </script>
      </body>
    </html>
  )rawliteral";

  server.send(200, "text/html", message);
}


void handleToggleRecord() {
  if (server.hasArg("activity")) {
    currentActivityLabel = server.arg("activity");
    Serial.print("Start recording activity: ");
    Serial.println(currentActivityLabel);
    isRecording = true;
  } else {
    Serial.println("Stop recording requested");
    isRecording = false;
  }

  server.send(200, "text/plain", isRecording ? "true" : "false");
}

void handleDownload() {
  if (!SPIFFS.exists(filename)) {
    server.send(500, "text/plain", "No CSV file available");
    return;
  }

  File file = SPIFFS.open(filename, FILE_READ);
  if (!file) {
    server.send(500, "text/plain", "Failed to open file for reading");
    return;
  }

  server.streamFile(file, "text/csv");
  file.close();
}

void handleSensorData() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  String jsonData = "{";
  jsonData += "\"time\":" + String(millis()) + ",";
  jsonData += "\"activity\":\"" + currentActivityLabel + "\",";
  jsonData += "\"accelX\":" + String(a.acceleration.x, 2) + ",";
  jsonData += "\"accelY\":" + String(a.acceleration.y, 2) + ",";
  jsonData += "\"accelZ\":" + String(a.acceleration.z, 2) + ",";
  jsonData += "\"gyroX\":" + String(g.gyro.x, 2) + ",";
  jsonData += "\"gyroY\":" + String(g.gyro.y, 2) + ",";
  jsonData += "\"gyroZ\":" + String(g.gyro.z, 2) + "}";

  server.send(200, "application/json", jsonData);
}

void appendToCSV(sensors_event_t a, sensors_event_t g) {
  String csvLine = String(millis()) + "," +
                   String(a.acceleration.x, 2) + "," +
                   String(a.acceleration.y, 2) + "," +
                   String(a.acceleration.z, 2) + "," +
                   String(g.gyro.x, 2) + "," +
                   String(g.gyro.y, 2) + "," +
                   String(g.gyro.z, 2) + "," +
                   currentActivityLabel;

  // Add data to buffer
  dataBuffer[bufferIndex] = csvLine;
  bufferIndex++;

  // Write buffer to file if full
  if (bufferIndex >= bufferSize) {
    File file = SPIFFS.open(filename, FILE_APPEND);
    if (file) {
      for (int i = 0; i < bufferSize; i++) {
        file.println(dataBuffer[i]);
      }
      file.close();
      bufferIndex = 0; // Reset buffer index
    }
  }
}

void loop() {
  server.handleClient();

  if (isRecording) {
    unsigned long currentTime = millis();
    if (currentTime - lastSampleTime >= sampleInterval) {
      sensors_event_t accel, gyro, temp;
      mpu.getEvent(&accel, &gyro, &temp);
      appendToCSV(accel, gyro);
      lastSampleTime = currentTime;
    }
  }
}
