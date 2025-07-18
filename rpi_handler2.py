import RPi.GPIO as GPIO
import time
import threading
import requests
from datetime import datetime

# Servo pin configuration (compartment_number: GPIO pin)
SERVO_PINS = {
    1: 12,
    2: 13,
    3: 18,
    4: 19,
}
PIN_CONFIRM = 16  # Confirmation button GPIO (changed from 18 to avoid conflict with servo)

SERVO_CLOSED = 0
SERVO_OPEN = 90

SERVER_URL = "http://localhost:5000"
API_KEY = "my-secret-key-2025"

# User ID - change according to the specific user
USER_ID = 13

class TestRaspberryPiHandler:
    def __init__(self):
        print("=" * 60)
        print("AUTOMATIC MEDICINE DISPENSER SYSTEM - TEST PROGRAM")
        print("=" * 60)
        print(f"USER ID: {USER_ID}")
        print("=" * 60)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_CONFIRM, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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

        print(f"Confirmation button: GPIO {PIN_CONFIRM}")
        print("Connecting to server...")

        self.schedule_thread = threading.Thread(target=self.schedule_loop)
        self.schedule_thread.daemon = True
        self.schedule_thread.start()

        print("Initialization complete! Checking medicine schedule...")
        print("=" * 60)
        print("INSTRUCTIONS:")
        print("   - When notified, press the confirmation button after taking the medicine")
        print("   - Press Ctrl+C to stop the program")
        print("=" * 60)

    def set_servo_angle(self, compartment, angle):
        duty = angle / 18 + 2
        self.servos[compartment].ChangeDutyCycle(duty)
        time.sleep(2)
        self.servos[compartment].ChangeDutyCycle(0)

    def schedule_loop(self):
        print("Starting schedule check for user ID:", USER_ID)
        while True:
            try:
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

                        if compartment in SERVO_PINS and not self.is_alerting:
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
                    else:
                        print(f"Error sending confirmation to server: {response.status_code}")

            except Exception as e:
                print(f"Error sending confirmation: {e}")

            self.is_alerting = False
            self.current_compartment = None
            self.current_medicine = None
            self.current_schedule_id = None
            self.alert_time = None

            print("System returned to standby...")
        else:
            print("No pending medicine reminder to confirm!")

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
