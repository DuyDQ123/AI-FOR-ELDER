import RPi.GPIO as GPIO
import json
import time
from datetime import datetime
import threading
import requests
import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont
import os
import cv2
from pyzbar.pyzbar import decode
import numpy as np

# Pin definitions for Raspberry Pi
PIN_CONFIRM = 16    # Nút xác nhận uống thuốc
PIN_NEXT = 23      # Nút chuyển thuốc tiếp theo
PIN_LIST = 17      # Nút xem danh sách thuốc
PIN_SETTINGS = 27  # Nút cài đặt

# I2S Audio pins
I2S_BCK = 12      # Bit Clock
I2S_LRCK = 13     # Left-Right Clock (Word Select)
I2S_DIN = 20      # Data In

# Servo motor pins for each compartment (1-4)
SERVO_PINS = {
    1: 12,
    2: 13,
    3: 18,
    4: 19,
}

# Servo angles
SERVO_CLOSED = 0
SERVO_OPEN = 90
SERVO_DISPENSE = 180

# I2C settings for OLED
I2C_BUS = 1
OLED_ADDRESS = 0x3C
OLED_WIDTH = 128
OLED_HEIGHT = 64

# Constants for power protection
SERVO_COOLDOWN_TIME = 2.0  # Seconds between servo operations
SERVO_MAX_OPERATIONS = 10   # Maximum operations per minute
SERVO_OPERATION_TIMEOUT = 1.5  # Maximum time for one operation

# Sound alert settings
ALERT_MAX_REPEATS = 3      # Maximum number of alert repetitions
ALERT_INTERVAL = 30        # Seconds between alerts
ALERT_VOLUME = 80         # Default volume percentage

class RaspberryPiHandler:
    def __init__(self, server_url="http://localhost:5000"):
        # Configure I2S audio
        os.system('sudo modprobe snd-bcm2835')  # Enable I2S kernel module
        os.system('sudo dtoverlay i2s-mmap')    # Enable I2S overlay
        
        # Set default audio output to I2S
        os.system('amixer cset numid=3 1')      # 1 for I2S output
        self.server_url = server_url
        self.current_schedules = []
        self.is_alerting = False
        self.alert_thread = None
        self.camera = None
        self.is_scanning = False
        self.last_qr_code = None
        self.servos = {}
        self.last_servo_operation = 0  # Timestamp of last servo use
        self.servo_operations_count = 0  # Count operations within a minute
        self.servo_operations_timer = time.time()  # Timer for operation counting
        
        # Khởi tạo GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_CONFIRM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_NEXT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_LIST, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_SETTINGS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Khởi tạo servo motors
        for compartment, pin in SERVO_PINS.items():
            GPIO.setup(pin, GPIO.OUT)
            self.servos[compartment] = GPIO.PWM(pin, 50)  # 50Hz frequency
            self.servos[compartment].start(0)
            self._set_servo_angle(compartment, SERVO_CLOSED)
        
        # Khởi tạo OLED
        self.oled = Adafruit_SSD1306.SSD1306_128_64(rst=None)
        self.oled.begin()
        self.oled.clear()
        self.oled.display()
        
        # Font cho OLED
        self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
        
        # Khởi tạo camera
        self.init_camera()
        
    def init_camera(self):
        """Khởi tạo USB camera"""
        try:
            self.camera = cv2.VideoCapture(0)  # Thử camera đầu tiên
            if not self.camera.isOpened():
                self.camera = cv2.VideoCapture(1)  # Thử camera thứ hai nếu camera đầu không hoạt động
            
            if not self.camera.isOpened():
                print("Không thể kết nối camera!")
                return False
                
            print("Đã kết nối camera thành công!")
            return True
        except Exception as e:
            print(f"Lỗi khi khởi tạo camera: {e}")
            return False
        
    def start(self):
        """Khởi động các tính năng của Raspberry Pi"""
        # Thêm interrupt cho các nút
        GPIO.add_event_detect(PIN_CONFIRM, GPIO.FALLING, 
                            callback=self._button_callback, bouncetime=300)
        GPIO.add_event_detect(PIN_NEXT, GPIO.FALLING, 
                            callback=self._button_callback, bouncetime=300)
        GPIO.add_event_detect(PIN_LIST, GPIO.FALLING, 
                            callback=self._button_callback, bouncetime=300)
        GPIO.add_event_detect(PIN_SETTINGS, GPIO.FALLING, 
                            callback=self._button_callback, bouncetime=300)
        
        # Khởi động các thread
        self.schedule_checker = threading.Thread(target=self._check_schedules_loop)
        self.schedule_checker.daemon = True
        self.schedule_checker.start()
        
        # Thread quét mã QR
        self.qr_scanner = threading.Thread(target=self._qr_scan_loop)
        self.qr_scanner.daemon = True
        self.qr_scanner.start()
        
    def _qr_scan_loop(self):
        """Vòng lặp quét mã QR"""
        while True:
            if self.is_scanning and self.camera and self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret:
                    # Quét mã QR
                    decoded_objects = decode(frame)
                    for obj in decoded_objects:
                        qr_data = obj.data.decode('utf-8')
                        if qr_data != self.last_qr_code:
                            self.last_qr_code = qr_data
                            self._handle_qr_code(qr_data)
                            
                    # Hiển thị frame với khung nhận diện
                    cv2.imshow('QR Scanner', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.is_scanning = False
                        
            time.sleep(0.1)  # Giảm tải CPU
            
    def _handle_qr_code(self, qr_data):
        """Xử lý dữ liệu từ mã QR"""
        try:
            # Giả sử mã QR chứa JSON với thông tin thuốc
            medicine_info = json.loads(qr_data)
            self._display_oled_message(
                f"Thuốc: {medicine_info.get('name', 'N/A')}\n"
                f"Liều lượng: {medicine_info.get('dosage', 'N/A')}\n"
                f"Ghi chú: {medicine_info.get('notes', 'N/A')}"
            )
            
            # Gửi thông tin lên server
            requests.post(f"{self.server_url}/api/verify_medicine",
                        json=medicine_info)
                        
        except json.JSONDecodeError:
            print(f"Mã QR không hợp lệ: {qr_data}")
            self._display_oled_message("Mã QR không hợp lệ!")
            
    def start_scanning(self):
        """Bắt đầu quét mã QR"""
        self.is_scanning = True
        self._display_oled_message("Đang quét mã QR...")
        
    def stop_scanning(self):
        """Dừng quét mã QR"""
        self.is_scanning = False
        cv2.destroyAllWindows()
        self._clear_oled()
        
    def _button_callback(self, channel):
        """Xử lý sự kiện nút nhấn"""
        if channel == PIN_CONFIRM and self.is_alerting:
            if self._dispense_medicine(self.current_schedule):
                self._confirm_medicine()
        elif channel == PIN_NEXT:
            self._show_next_medicine()
        elif channel == PIN_LIST:
            self._show_medicine_list()
        elif channel == PIN_SETTINGS:
            # Toggle QR scanning
            if self.is_scanning:
                self.stop_scanning()
            else:
                self.start_scanning()
            
    def _check_schedules_loop(self):
        """Kiểm tra lịch uống thuốc liên tục"""
        while True:
            try:
                response = requests.get(f"{self.server_url}/api/check_schedule")
                if response.status_code == 200:
                    schedules = response.json()
                    if schedules and not self.is_alerting:
                        self._start_alert(schedules[0])
            except Exception as e:
                print(f"Lỗi khi kiểm tra lịch: {e}")
            time.sleep(30)  # Kiểm tra mỗi 30 giây để không bị lỡ giờ
            
    def _start_alert(self, schedule):
        """Bắt đầu cảnh báo cho lịch uống thuốc"""
        self.is_alerting = True
        self.current_schedule = schedule
        
        # Hiển thị thông tin trên OLED
        message = (
            f"Đã đến giờ uống thuốc!\n"
            f"{schedule['medicine_name']}\n"
            f"Thời gian: {schedule['time']}"
        )
        self._display_oled_message(message)
        
        self.current_alert_count = 0
        self.last_alert_time = time.time()
        
        # Bắt đầu thread cảnh báo
        self.alert_thread = threading.Thread(target=self._alert_loop)
        self.alert_thread.daemon = True
        self.alert_thread.start()
        
    def _display_oled_message(self, message):
        """Hiển thị thông báo trên màn hình OLED (thay bằng print khi chưa có LCD)"""
        print(f"[THÔNG BÁO]:\n{message}")
        
    def _clear_oled(self):
        """Xóa màn hình OLED"""
        self.oled.clear()
        self.oled.display()
        
    def _play_alert_sound(self, medicine_name=None):
        """Thông báo bằng print khi chưa có âm thanh"""
        if medicine_name:
            print(f"[CẢNH BÁO]: Đã đến giờ uống thuốc {medicine_name}")
        else:
            print("[CẢNH BÁO]: Đã đến giờ uống thuốc")
            
    def _alert_loop(self):
        """Vòng lặp phát cảnh báo định kỳ"""
        while self.is_alerting and self.current_alert_count < ALERT_MAX_REPEATS:
            current_time = time.time()
            
            # Phát cảnh báo lần đầu hoặc sau mỗi khoảng thời gian
            if self.current_alert_count == 0 or (current_time - self.last_alert_time) >= ALERT_INTERVAL:
                # Phát âm thanh cảnh báo
                self._play_alert_sound(self.current_schedule.get('medicine_name'))
                self.last_alert_time = current_time
                self.current_alert_count += 1
                
                # Hiển thị số lần nhắc còn lại
                remaining = ALERT_MAX_REPEATS - self.current_alert_count
                if remaining > 0:
                    print(f"Còn {remaining} lần nhắc")
                    self._display_oled_message(
                        f"Nhắc lần {self.current_alert_count}/{ALERT_MAX_REPEATS}\n"
                        f"Thuốc: {self.current_schedule['medicine_name']}\n"
                        f"Thời gian: {self.current_schedule['time']}"
                    )
            
            time.sleep(1)  # Kiểm tra mỗi giây
        
        if self.current_alert_count >= ALERT_MAX_REPEATS:
            print("Đã hết số lần nhắc")
            self._display_oled_message("Đã hết thời gian nhắc nhở\nVui lòng kiểm tra lịch sử")
            
        self.is_alerting = False
        
    def _check_servo_safety(self):
        """Kiểm tra các điều kiện an toàn trước khi chạy servo"""
        current_time = time.time()
        
        # Kiểm tra thời gian cooldown
        if current_time - self.last_servo_operation < SERVO_COOLDOWN_TIME:
            print(f"Đang trong thời gian cooldown. Còn {SERVO_COOLDOWN_TIME - (current_time - self.last_servo_operation):.1f}s")
            return False
            
        # Reset bộ đếm operations mỗi phút
        if current_time - self.servo_operations_timer >= 60:
            self.servo_operations_count = 0
            self.servo_operations_timer = current_time
            
        # Kiểm tra số lượng operations trong 1 phút
        if self.servo_operations_count >= SERVO_MAX_OPERATIONS:
            print("Đã đạt giới hạn số lần hoạt động trong 1 phút")
            return False
            
        return True

    def _set_servo_angle(self, compartment, angle):
        """Điều khiển góc quay của servo với các biện pháp bảo vệ"""
        if compartment not in self.servos:
            return False
            
        if not self._check_servo_safety():
            return False
            
        try:
            # Ghi nhận thời điểm hoạt động
            self.last_servo_operation = time.time()
            self.servo_operations_count += 1
            
            # Convert angle to duty cycle (0-180 degrees maps to 2-12% duty cycle)
            duty = angle / 18 + 2
            self.servos[compartment].ChangeDutyCycle(duty)
            
            # Đợi servo đến vị trí với timeout
            start_time = time.time()
            while time.time() - start_time < SERVO_OPERATION_TIMEOUT:
                time.sleep(0.1)
                if time.time() - start_time >= 0.5:  # Minimum wait time
                    break
                    
            self.servos[compartment].ChangeDutyCycle(0)  # Stop servo jitter
            return True
            
        except Exception as e:
            print(f"Lỗi điều khiển servo: {e}")
            self.servos[compartment].ChangeDutyCycle(0)  # Ensure servo is stopped
            return False

    def _dispense_medicine(self, schedule):
        """Thả thuốc từ ngăn được chỉ định"""
        try:
            # Get medicine details from server
            response = requests.get(f"{self.server_url}/api/medicine/{schedule['medicine_id']}")
            if response.status_code != 200:
                print("Không thể lấy thông tin thuốc")
                return False
                
            medicine = response.json()
            compartment = medicine['compartment_number']
            medicines_in_compartment = medicine.get('medicines_in_compartment', [])
            
            if not (1 <= compartment <= 4):
                print(f"Số ngăn không hợp lệ: {compartment}")
                return False
            
            print(f"Thả thuốc từ ngăn {compartment}")
            
            # Open compartment - quay servo 90 độ
            self._set_servo_angle(compartment, SERVO_OPEN)
            time.sleep(2)  # Đợi 2 giây như yêu cầu
            
            # Close compartment - về vị trí ban đầu
            self._set_servo_angle(compartment, SERVO_CLOSED)
            
            # Update medicine quantity on server
            for med in medicines_in_compartment:
                requests.post(f"{self.server_url}/api/update_quantity",
                    json={
                        'medicine_id': med['id'],
                        'quantity_change': -med['dosage']
                    })
            
            return True
            
        except Exception as e:
            print(f"Lỗi khi thả thuốc: {e}")
            return False

    def cleanup(self):
        """Dọn dẹp GPIO và camera khi kết thúc"""
        # Stop all servos
        for servo in self.servos.values():
            servo.stop()
            
        GPIO.cleanup()
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        handler = RaspberryPiHandler()
        handler.start()
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping Raspberry Pi handler...")
        handler.cleanup()