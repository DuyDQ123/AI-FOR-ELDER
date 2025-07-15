import RPi.GPIO as GPIO
import time
import threading
import requests

SERVO_PINS = {
    1: 12,
    2: 13,
    3: 18,
    4: 19,
}
PIN_CONFIRM = 18  # Nút xác nhận uống thuốc

SERVO_CLOSED = 0
SERVO_OPEN = 90

SERVER_URL = "http://localhost:5000"
API_KEY = "my-secret-key-2025"

class TestRaspberryPiHandler:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_CONFIRM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.servos = {}
        for compartment, pin in SERVO_PINS.items():
            GPIO.setup(pin, GPIO.OUT)
            self.servos[compartment] = GPIO.PWM(pin, 50)
            self.servos[compartment].start(0)
            self.set_servo_angle(compartment, SERVO_CLOSED)
        GPIO.add_event_detect(PIN_CONFIRM, GPIO.FALLING, callback=self.confirm_callback, bouncetime=300)
        self.is_alerting = False
        self.current_compartment = None
        self.schedule_thread = threading.Thread(target=self.schedule_loop)
        self.schedule_thread.daemon = True
        self.schedule_thread.start()
        print("Khởi tạo xong. Đang kiểm tra lịch uống thuốc...")

    def set_servo_angle(self, compartment, angle):
        duty = angle / 18 + 2
        self.servos[compartment].ChangeDutyCycle(duty)
        time.sleep(2)
        self.servos[compartment].ChangeDutyCycle(0)

    def schedule_loop(self):
        while True:
            try:
                headers = {"X-API-Key": API_KEY}
                response = requests.get(f"{SERVER_URL}/api/check_schedule", headers=headers)
                if response.status_code == 200:
                    schedules = response.json()
                    for schedule in schedules:
                        compartment = schedule.get("compartment_number")
                        medicine_name = schedule.get("medicine_name")
                        if compartment in SERVO_PINS and not self.is_alerting:
                            self.is_alerting = True
                            self.current_compartment = compartment
                            print(f"[THÔNG BÁO] Đã đến giờ uống thuốc ngăn {compartment}: {medicine_name}")
                            self.set_servo_angle(compartment, SERVO_OPEN)
                            print(f"Ngăn {compartment} đã mở 90 độ trong 2s để nhả thuốc")
                            self.set_servo_angle(compartment, SERVO_CLOSED)
                            print(f"Ngăn {compartment} đã đóng lại")
                else:
                    print(f"Lỗi API: {response.text}")
            except Exception as e:
                print(f"Lỗi kiểm tra lịch: {e}")
            time.sleep(5)

    def confirm_callback(self, channel):
        if self.is_alerting and self.current_compartment:
            print(f"[XÁC NHẬN] Đã uống thuốc ở ngăn {self.current_compartment}")
            self.is_alerting = False
            self.current_compartment = None

    def cleanup(self):
        for servo in self.servos.values():
            servo.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    try:
        handler = TestRaspberryPiHandler()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Dừng thử nghiệm...")
        handler.cleanup()