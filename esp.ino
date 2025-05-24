#include <Wire.h>
#include "RTClib.h"

RTC_DS3231 rtc;

const int speakerPin = 25; // chân nối với loa
const int remindHour = 8;   // giờ nhắc thuốc (8h sáng)
const int remindMinute = 0; // phút

bool reminded = false;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  rtc.begin();

  pinMode(speakerPin, OUTPUT);
  digitalWrite(speakerPin, LOW);

  if (rtc.lostPower()) {
    Serial.println("RTC mất nguồn, thiết lập thời gian mới...");
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__))); // Lấy giờ từ máy tính
  }
}

void loop() {
  DateTime now = rtc.now();

  Serial.print("Giờ hiện tại: ");
  Serial.print(now.hour());
  Serial.print(":");
  Serial.println(now.minute());

  // Nếu đến giờ và chưa phát nhắc
  if (now.hour() == remindHour && now.minute() == remindMinute && !reminded) {
    playReminderSound();
    reminded = true; // tránh phát lại nhiều lần
  }

  // Reset cờ reminded sau 1 phút
  if (now.minute() != remindMinute) {
    reminded = false;
  }

  delay(1000);
}

void playReminderSound() {
  Serial.println(">>> Nhắc thuốc!");
  for (int i = 0; i < 3; i++) {
    tone(speakerPin, 1000); // phát âm 1000Hz
    delay(500);
    noTone(speakerPin);
    delay(300);
  }
}
