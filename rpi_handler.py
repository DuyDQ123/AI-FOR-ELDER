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
PIN_CONFIRM = 18    # Nút xác nhận uống thuốc
PIN_NEXT = 23      # Nút chuyển thuốc tiếp theo
PIN_LIST = 17      # Nút xem danh sách thuốc
PIN_SETTINGS = 27  # Nút cài đặt

# I2C settings for OLED
I2C_BUS = 1
OLED_ADDRESS = 0x3C
OLED_WIDTH = 128
OLED_HEIGHT = 64

class RaspberryPiHandler:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.current_schedules = []
        self.is_alerting = False
        self.alert_thread = None
        self.camera = None
        self.is_scanning = False
        self.last_qr_code = None
        
        # Khởi tạo GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_CONFIRM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_NEXT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_LIST, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_SETTINGS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
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
            time.sleep(60)  # Kiểm tra mỗi phút
            
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
        
        # Bắt đầu thread cảnh báo
        self.alert_thread = threading.Thread(target=self._alert_loop)
        self.alert_thread.daemon = True
        self.alert_thread.start()
        
    def _display_oled_message(self, message):
        """Hiển thị thông báo trên màn hình OLED"""
        image = Image.new('1', (OLED_WIDTH, OLED_HEIGHT))
        draw = ImageDraw.Draw(image)
        
        y = 0
        for line in message.split('\n'):
            draw.text((0, y), line, font=self.font, fill=255)
            y += 14
            
        self.oled.image(image)
        self.oled.display()
        
    def _clear_oled(self):
        """Xóa màn hình OLED"""
        self.oled.clear()
        self.oled.display()
        
    def _play_alert_sound(self):
        """Phát âm thanh cảnh báo"""
        os.system('aplay /usr/share/sounds/sound.wav')
        
    def cleanup(self):
        """Dọn dẹp GPIO và camera khi kết thúc"""
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