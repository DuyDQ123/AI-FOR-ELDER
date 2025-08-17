import RPi.GPIO as GPIO
import time
import threading
import requests
from datetime import datetime
import sys
import os

# Add path to import notification service
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from zalo_service import notification_service
    NOTIFICATION_AVAILABLE = True
    print("Notification service imported successfully")
except ImportError as e:
    print(f"Warning: Cannot import notification service: {e}")
    print("Notification features will be disabled")
    NOTIFICATION_AVAILABLE = False

# Servo pin configuration (compartment_number: GPIO pin)
SERVO_PINS = {
    1: 12,
    2: 13,
    3: 18,
    4: 19,
}
PIN_CONFIRM = 16  # Confirmation button GPIO (changed from 18 to avoid conflict with servo)
PIN_INFO = 23  # GPIO pin for the "INFO" button
PIN_POWER = 22  # GPIO pin for the "POWER" button (system on/off)
SERVO_CLOSED = 0
SERVO_OPEN = 90

SERVER_URL = "http://192.168.1.159:5000"
API_KEY = "my-secret-key-2025"

# User ID - change according to the specific user
USER_ID = 15

class TestRaspberryPiHandler:
    def __init__(self):
        print("=" * 60)
        print("AUTOMATIC MEDICINE DISPENSER SYSTEM - TEST PROGRAM")
        print("=" * 60)
        print(f"USER ID: {USER_ID}")
        print("=" * 60)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_CONFIRM, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(PIN_INFO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(PIN_POWER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(PIN_INFO, GPIO.FALLING, callback=self.info_callback, bouncetime=300)
        GPIO.add_event_detect(PIN_POWER, GPIO.FALLING, callback=self.power_callback, bouncetime=500)

        self.servos = {}
        print(f"Initializing {len(SERVO_PINS)} medicine compartments:")
        for compartment, pin in SERVO_PINS.items():
            GPIO.setup(pin, GPIO.OUT)
            self.servos[compartment] = GPIO.PWM(pin, 50)
            self.servos[compartment].start(0)
            self.set_servo_angle(compartment, SERVO_CLOSED)
            print(f"   Compartment {compartment} (GPIO {pin}) - Closed")

        GPIO.add_event_detect(PIN_CONFIRM, GPIO.FALLING, callback=self.confirm_callback, bouncetime=300)

        self.is_alerting = False
        self.current_compartment = None
        self.current_medicine = None
        self.current_schedule_id = None
        self.alert_time = None
        self.system_enabled = True  # Track system power status
        self.power_button_press_time = None
        
        # Emergency notification tracking
        self.pending_notifications = {}  # Track unconfirmed notifications
        self.notification_sent = {}  # Track sent notifications

        print(f"Confirmation button: GPIO {PIN_CONFIRM}")
        print(f"INFO button: GPIO {PIN_INFO}")
        print(f"POWER button: GPIO {PIN_POWER}")
        print("Connecting to server...")
        
        # Check initial system status
        self.check_system_status()

        self.schedule_thread = threading.Thread(target=self.schedule_loop)
        self.schedule_thread.daemon = True
        self.schedule_thread.start()

        print("Initialization complete! Checking medicine schedule...")
        print("=" * 60)
        print("INSTRUCTIONS:")
        print("   - When notified, press the confirmation button after taking the medicine")
        print("   - Press INFO button to view user profile on ESP32 display")
        print("   - Press POWER button to enable/disable the system")
        print("   - Press Ctrl+C to stop the program")
        print("=" * 60)

    def set_servo_angle(self, compartment, angle):
        duty = angle / 18 + 2
        self.servos[compartment].ChangeDutyCycle(duty)
        time.sleep(2)
        self.servos[compartment].ChangeDutyCycle(0)

    def check_system_status(self):
        """Check system power status from server"""
        try:
            headers = {"X-API-Key": API_KEY}
            response = requests.get(f"{SERVER_URL}/api/system_status", headers=headers)
            
            if response.status_code == 200:
                status_data = response.json()
                self.system_enabled = status_data.get('system_enabled', True)
                status_text = "ENABLED" if self.system_enabled else "DISABLED"
                print(f"System Status: {status_text}")
                return self.system_enabled
            else:
                print(f"Error checking system status: {response.status_code}")
                return True  # Default to enabled if can't check
        except Exception as e:
            print(f"Error checking system status: {e}")
            return True

    def schedule_loop(self):
        print("Starting schedule check for user ID:", USER_ID)
        while True:
            try:
                # Check and send notifications for unconfirmed medicines
                self.check_pending_notifications()
                
                # Check system status first
                if not self.check_system_status():
                    print("System is DISABLED - Skipping schedule check")
                    time.sleep(10)  # Check less frequently when disabled
                    continue
                
                headers = {"X-API-Key": API_KEY}
                response = requests.get(f"{SERVER_URL}/api/check_schedule_by_user/{USER_ID}", headers=headers)

                if response.status_code == 200:
                    schedules = response.json()
                    if schedules:
                        print(f"Found {len(schedules)} scheduled medicines for user {USER_ID}:")

                    for schedule in schedules:
                        compartment = schedule.get("compartment_number")
                        medicine_name = schedule.get("medicine_name")
                        schedule_id = schedule.get("schedule_id")
                        notes = schedule.get("notes", "")

                        if compartment in SERVO_PINS and not self.is_alerting and self.system_enabled:
                            self.is_alerting = True
                            self.current_compartment = compartment
                            self.current_medicine = medicine_name
                            self.current_schedule_id = schedule_id
                            self.alert_time = datetime.now()

                            print("\n" + "=" * 60)
                            print("MEDICINE REMINDER!")
                            print("=" * 60)
                            print(f"User ID: {USER_ID}")
                            print(f"Time: {self.alert_time.strftime('%H:%M:%S - %d/%m/%Y')}")
                            print(f"Medicine: {medicine_name}")
                            print(f"Compartment: {compartment}")
                            if notes:
                                print(f"Note: {notes}")
                            print("=" * 60)

                            # Open the compartment
                            print(f"Opening compartment {compartment}...")
                            self.set_servo_angle(compartment, SERVO_OPEN)
                            print(f"Compartment {compartment} opened to 90 degrees for 2 seconds")

                            # Close the compartment
                            self.set_servo_angle(compartment, SERVO_CLOSED)
                            print(f"Compartment {compartment} closed")

                            print("\nPLEASE PRESS THE CONFIRM BUTTON AFTER TAKING THE MEDICINE!")
                            print("Waiting for confirmation...")

                            # Setup emergency notification timer
                            self.setup_notification_timer(schedule_id, medicine_name, compartment)

                            self.start_reminder_timer()

                elif response.status_code == 401:
                    print("Authentication error - Check your API key or login status")
                else:
                    print(f"API error ({response.status_code}): {response.text}")

            except requests.exceptions.ConnectionError:
                print("Cannot connect to the server. Retrying...")
            except Exception as e:
                print(f"Error checking schedule: {e}")

            time.sleep(5)

    def start_reminder_timer(self):
        """Start reminder thread to alert if user hasn't confirmed"""
        def reminder_loop():
            time.sleep(30)
            if self.is_alerting:
                print("\nREMINDER: Please press the confirm button after taking your medicine!")
                time.sleep(60)
                if self.is_alerting:
                    print("WARNING: 1 minute 30 seconds passed without confirmation!")
                    print(f"Medicine: {self.current_medicine}")
                    print(f"Compartment: {self.current_compartment}")

        reminder_thread = threading.Thread(target=reminder_loop)
        reminder_thread.daemon = True
        reminder_thread.start()

    def confirm_callback(self, channel):
        if self.is_alerting and self.current_compartment:
            confirm_time = datetime.now()
            time_diff = confirm_time - self.alert_time

            print("\n" + "=" * 60)
            print("CONFIRMATION RECEIVED!")
            print("=" * 60)
            print(f"User ID: {USER_ID}")
            print(f"Medicine: {self.current_medicine}")
            print(f"Compartment: {self.current_compartment}")
            print(f"Confirmed at: {confirm_time.strftime('%H:%M:%S - %d/%m/%Y')}")
            print(f"Response time: {time_diff.seconds} seconds")
            print("=" * 60)
            print("Thank you for taking your medicine on time!")
            print("=" * 60)

            try:
                if self.current_schedule_id:
                    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
                    data = {"schedule_id": self.current_schedule_id, "user_id": USER_ID}

                    response = requests.post(f"{SERVER_URL}/api/confirm_medicine_by_user",
                                             headers=headers, json=data)

                    if response.status_code == 200:
                        print("Confirmation successfully sent to server!")
                        pi_flag_data = {
                            "schedule_id": self.current_schedule_id,
                            "user_id": USER_ID,
                            "pi_button_flag": True
                        }
                        
                        pi_response = requests.post(f"{SERVER_URL}/api/confirm_pi_button",
                                                   headers=headers, json=pi_flag_data)
                        
                        if pi_response.status_code == 200:
                            print("Pi button flag sent to server for ESP32 sync!")
                        else:
                            print(f"Error sending Pi button flag: {pi_response.status_code}")
                            
                    else:
                        print(f"Error sending confirmation to server: {response.status_code}")

            except Exception as e:
                print(f"Error sending confirmation: {e}")

            # Cancel pending notification when confirmed
            if self.current_schedule_id in self.pending_notifications:
                del self.pending_notifications[self.current_schedule_id]
                print("Emergency notification cancelled - user confirmed")

            self.is_alerting = False
            self.current_compartment = None
            self.current_medicine = None
            self.current_schedule_id = None
            self.alert_time = None

            print("System returned to standby...")
        else:
            print("No pending medicine reminder to confirm!")
        
    def info_callback(self, channel):
            print("INFO button pressed!")
            try:
                headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
                data = {"user_id": USER_ID, "info_flag": True}  # Add a flag for the INFO button
        
                response = requests.post(f"{SERVER_URL}/api/trigger_info_display", headers=headers, json=data)
        
                if response.status_code == 200:
                    print("INFO flag successfully sent to server!")
                else:
                    print(f"Error sending INFO flag: {response.status_code}")
            except Exception as e:
                print(f"Error handling INFO button press: {e}")

    def power_callback(self, channel):
        """Handle power button press to toggle system on/off"""
        press_time = datetime.now()
        
        # Debounce protection
        if self.power_button_press_time:
            time_diff = (press_time - self.power_button_press_time).total_seconds()
            if time_diff < 2:  # Ignore presses within 2 seconds
                return
        
        self.power_button_press_time = press_time
        print("\n" + "=" * 60)
        print("POWER BUTTON PRESSED!")
        print("=" * 60)
        
        try:
            # Get current system status
            current_status = self.check_system_status()
            new_action = 'disable' if current_status else 'enable'
            
            headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
            data = {
                "user_id": USER_ID,
                "duration": 1,  # Button press duration
                "timestamp": press_time.isoformat()
            }
            
            response = requests.post(f"{SERVER_URL}/api/power_button_press", headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.system_enabled = result.get('new_status', True)
                status_text = "ENABLED" if self.system_enabled else "DISABLED"
                
                print(f"Power button processed successfully!")
                print(f"System Status: {status_text}")
                print(f"Action: {result.get('action', 'unknown').upper()}")
                print("=" * 60)
                
                if not self.system_enabled:
                    print("SYSTEM DISABLED - Medicine dispensing is now OFF")
                    print("Press POWER button again to re-enable the system")
                else:
                    print("SYSTEM ENABLED - Medicine dispensing is now ON")
                    print("Resuming normal operation...")
                    
            else:
                print(f"Error processing power button: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Error handling power button press: {e}")
        
        print("=" * 60)

    def setup_notification_timer(self, schedule_id, medicine_name, compartment):
        """Setup timer for emergency notifications"""
        if not NOTIFICATION_AVAILABLE:
            print("Warning: Notification service not available")
            return
            
        try:
            # Get user info from server to know notification delay
            headers = {"X-API-Key": API_KEY}
            response = requests.get(f"{SERVER_URL}/api/user_profile/{USER_ID}", headers=headers)
            
            if response.status_code == 200:
                user_info = response.json()
                notification_delay = user_info.get('notification_delay_minutes', 15)
                
                # Save pending notification info - use direct access to root level fields
                self.pending_notifications[schedule_id] = {
                    'user_info': user_info,  # Store full user_info at root level
                    'medicine_name': medicine_name,
                    'compartment': compartment,
                    'alert_time': time.time(),
                    'notification_delay_seconds': notification_delay * 60,
                    'notified': False
                }
                
                print(f"Set notification timer: {notification_delay} minutes for {medicine_name}")
            else:
                print(f"Cannot get user info to set notification timer")
                
        except Exception as e:
            print(f"Error setting up notification timer: {e}")

    def check_pending_notifications(self):
        """Check and send notifications for unconfirmed medicines"""
        if not NOTIFICATION_AVAILABLE or not self.pending_notifications:
            return
            
        current_time = time.time()
        to_remove = []
        
        for schedule_id, notification_info in self.pending_notifications.items():
            time_elapsed = current_time - notification_info['alert_time']
            
            # If time has passed and notification not sent yet
            if (time_elapsed >= notification_info['notification_delay_seconds'] and
                not notification_info['notified']):
                
                self.send_emergency_notification(schedule_id, notification_info)
                notification_info['notified'] = True
                
            # Remove notification after 2 hours
            elif time_elapsed >= 7200:  # 2 hours
                to_remove.append(schedule_id)
        
        # Clean up old notifications
        for schedule_id in to_remove:
            del self.pending_notifications[schedule_id]
            print(f"Cleaned up old notification for schedule {schedule_id}")

    def send_emergency_notification(self, schedule_id, notification_info):
        """Send emergency notification via email"""
        if not NOTIFICATION_AVAILABLE:
            print("Warning: Cannot send notification - Notification service unavailable")
            return
            
        try:
            user_info = notification_info['user_info']
            medicine_name = notification_info['medicine_name']
            compartment = notification_info['compartment']
            
            print(f"\nSENDING EMERGENCY NOTIFICATION")
            # Access user info from nested structure or direct access
            user_name = user_info.get('user_info', {}).get('full_name') or user_info.get('full_name', 'Unknown')
            print(f"User: {user_name}")
            print(f"Medicine: {medicine_name}")
            print(f"Emergency Contact: {user_info.get('emergency_contact_name', 'Unknown')}")
            print(f"Contact Phone: {user_info.get('emergency_contact_phone', 'Unknown')}")
            print(f"Contact Email: {user_info.get('emergency_contact_zalo_id', 'Unknown')}")
            
            # Send notification
            success = notification_service.send_missed_medicine_notification(
                user_info, medicine_name, compartment
            )
            
            if success:
                print("Emergency notification sent successfully!")
                self.log_notification_to_server(
                    user_info, 'email', 'sent', medicine_name, compartment, schedule_id
                )
            else:
                print("Failed to send emergency notification")
                self.log_notification_to_server(
                    user_info, 'email', 'failed', medicine_name, compartment, schedule_id
                )
                
        except Exception as e:
            print(f"Error sending emergency notification: {e}")

    def log_notification_to_server(self, user_info, method, status, medicine_name, compartment, schedule_id):
        """Log notification to server"""
        try:
            headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
            log_data = {
                'user_id': USER_ID,
                'schedule_id': schedule_id,
                'notification_type': 'missed_medicine',
                'method': method,
                'delivery_status': status,
                'medicine_name': medicine_name,
                'compartment': compartment,
                'emergency_contact_name': user_info.get('emergency_contact_name'),
                'emergency_contact_phone': user_info.get('emergency_contact_phone'),
                'emergency_contact_zalo_id': user_info.get('emergency_contact_zalo_id')
            }
            
            response = requests.post(f"{SERVER_URL}/api/log_notification",
                                   headers=headers, json=log_data, timeout=5)
            
            if response.status_code == 200:
                print(f"Notification logged to server")
            else:
                print(f"Cannot log notification: {response.status_code}")
                
        except Exception as e:
            print(f"Error logging notification: {e}")

    def cleanup(self):
        for servo in self.servos.values():
            servo.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    try:
        handler = TestRaspberryPiHandler()
        print("System running... Press Ctrl+C to stop")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("TEST PROGRAM STOPPED")
        print("=" * 60)
        print("Summary:")
        print("   - Program ran successfully")
        print("   - All servos reset to default position")
        print("   - GPIO cleaned up properly")
        print("=" * 60)
        print("Thank you for using the system!")

        handler.cleanup()

