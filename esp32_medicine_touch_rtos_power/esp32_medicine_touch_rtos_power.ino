int ledPin = 8;  // LED nối vào chân 8

void setup() {
  pinMode(ledPin, OUTPUT);  // đặt chân 8 là OUTPUT
}

void loop() {
  digitalWrite(ledPin, HIGH);  // bật LED
  delay(100);                 // chờ 1 giây

  digitalWrite(ledPin, LOW);   // tắt LED
  delay(100);                 // chờ 1 giây
}
