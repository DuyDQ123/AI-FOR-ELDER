#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <MPU6050.h>

const char* ssid = "duy";
const char* password = "11111111";
const char* serverUrl = "http://192.168.1.159:5000/sensor";

MPU6050 mpu;

void setup() {
    Serial.begin(115200);
    Wire.begin();
    mpu.initialize();

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Đang kết nối WiFi...");
    }
    Serial.println("WiFi đã kết nối!");
}

void sendSensorData() {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(serverUrl);
        http.addHeader("Content-Type", "application/json");

        int16_t ax, ay, az, gx, gy, gz;
        mpu.getAcceleration(&ax, &ay, &az);
        mpu.getRotation(&gx, &gy, &gz);

        StaticJsonDocument<200> jsonDoc;
        jsonDoc["ax"] = ax / 16384.0;
        jsonDoc["ay"] = ay / 16384.0;
        jsonDoc["az"] = az / 16384.0;
        jsonDoc["gx"] = gx / 131.0;
        jsonDoc["gy"] = gy / 131.0;
        jsonDoc["gz"] = gz / 131.0;

        String jsonStr;
        serializeJson(jsonDoc, jsonStr);

        int httpResponseCode = http.POST(jsonStr);
        if (httpResponseCode > 0) {
            String response = http.getString();
            Serial.println("Server Response: " + response);
        } else {
            Serial.println("Lỗi gửi dữ liệu!");
        }
        
        http.end(); // Giải phóng HTTP client
    }
}


void loop() {
    sendSensorData();
    delay(200); // Gửi dữ liệu mỗi 200ms
}
