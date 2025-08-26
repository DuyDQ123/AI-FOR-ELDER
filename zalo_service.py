import smtplib
import requests
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications via Email (replaces Zalo for demo)"""
    
    def __init__(self):
        # Email configuration
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_user = getattr(Config, 'MAIL_USERNAME', None)
        self.email_password = getattr(Config, 'MAIL_PASSWORD', None)
        
        # SMS backup configuration
        self.sms_api_url = "http://api.speedsms.vn/index.php"
        self.sms_access_token = getattr(Config, 'SMS_ACCESS_TOKEN', None)
        
        # Validation
        if not self.email_user or not self.email_password:
            logger.warning("Email credentials not configured. Email notifications will not work.")

    def send_missed_medicine_notification(self, user_data: Dict, medicine_name: str, compartment: int) -> bool:
        """
        Send missed medicine notification via Email
        
        Args:
            user_data: Dictionary containing user information
            medicine_name: Medicine name
            compartment: Medicine compartment number
            
        Returns:
            bool: True if sent successfully, False if failed
        """
        try:
            # Get emergency contact email from emergency_contact_zalo_id field (reusing old field)
            emergency_email = user_data.get('emergency_contact_zalo_id') or user_data.get('emergency_contact_email')
            if not emergency_email:
                logger.warning(f"User {user_data.get('username')} has no emergency contact email")
                return self._send_sms_backup(user_data, medicine_name, compartment)

            # Create notification content
            subject, html_content, text_content = self._create_missed_medicine_email(user_data, medicine_name, compartment)
            
            # Send Email notification
            success = self._send_email(emergency_email, subject, html_content, text_content)
            
            if success:
                logger.info(f"Emergency email sent successfully to {user_data.get('emergency_contact_name')} ({emergency_email})")
                self._log_notification(user_data, 'email', 'sent', subject)
                return True
            else:
                logger.warning(f"Failed to send email, trying SMS backup...")
                return self._send_sms_backup(user_data, medicine_name, compartment)
                
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return self._send_sms_backup(user_data, medicine_name, compartment)

    def _create_missed_medicine_email(self, user_data: Dict, medicine_name: str, compartment: int) -> tuple:
        """Create missed medicine email content"""
        full_name = user_data.get('full_name') or user_data.get('username', 'Patient')
        delay_minutes = user_data.get('notification_delay_minutes', 15)
        current_time = datetime.now().strftime('%H:%M - %d/%m/%Y')
        emergency_contact_name = user_data.get('emergency_contact_name', 'Emergency Contact')
        
        subject = f"URGENT: {full_name} missed medicine {medicine_name}"
        
        # HTML content (prettier for email)
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f44336; color: white; padding: 20px; text-align: center;">
                <h1>URGENT NOTIFICATION</h1>
            </div>
            
            <div style="padding: 20px; background-color: #f9f9f9;">
                <h2 style="color: #d32f2f;">Details:</h2>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;"><strong>Patient:</strong></td>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;">{full_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;"><strong>Medicine:</strong></td>
                        <td style="padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;">{medicine_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;"><strong>Compartment:</strong></td>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;">Compartment {compartment}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;"><strong>Time:</strong></td>
                        <td style="padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;">{current_time}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;"><strong>Wait time:</strong></td>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;">{delay_minutes} minutes</td>
                    </tr>
                </table>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <h3 style="margin-top: 0; color: #856404;">Warning:</h3>
                    <p><strong>{full_name}</strong> has not confirmed taking medicine after <strong>{delay_minutes} minutes</strong>.</p>
                </div>
                
                <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <h3 style="margin-top: 0; color: #0c5460;">Required Actions:</h3>
                    <ul style="margin: 0;">
                        <li>Please <strong>contact immediately</strong> {full_name}</li>
                        <li>Check if they have taken their medicine</li>
                        <li>Remind them to take medicine on time</li>
                        <li>Ensure their health and safety</li>
                    </ul>
                </div>
            </div>
            
            <div style="background-color: #6c757d; color: white; padding: 15px; text-align: center;">
                <p style="margin: 0;"><strong>AI-FOR-ELDER Smart Medicine Reminder System</strong></p>
                <p style="margin: 5px 0 0 0; font-size: 12px;">Automated email sent at {current_time}</p>
            </div>
        </body>
        </html>
        """
        
        # Text content (fallback for email clients that don't support HTML)
        text_content = f"""
URGENT NOTIFICATION

Dear {emergency_contact_name},

Patient: {full_name}
Medicine: {medicine_name}
Compartment: {compartment}
Time: {current_time}

WARNING: {full_name} has not confirmed taking medicine after {delay_minutes} minutes.

PLEASE:
- Contact {full_name} immediately
- Check medicine intake
- Remind to take medicine on time

AI-FOR-ELDER Smart Medicine Reminder System
Automated email - {current_time}
        """
        
        return subject, html_content, text_content

    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """
        Send email notification
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            text_content: Text content (fallback)
            
        Returns:
            bool: True if sent successfully
        """
        if not self.email_user or not self.email_password:
            logger.error("Email credentials not configured")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = to_email

            # Create parts for text and HTML
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')

            # Add parts to message
            msg.attach(part1)
            msg.attach(part2)

            # Send email with detailed logging
            logger.info(f" Connecting to Gmail SMTP server...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                logger.info(f" Starting TLS encryption...")
                server.starttls()
                
                logger.info(f" Authenticating with Gmail...")
                server.login(self.email_user, self.email_password)
                
                logger.info(f" Sending email to {to_email}...")
                server.send_message(msg)

            logger.info(f" Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("Email authentication error - check username/password")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return False

    def _send_sms_backup(self, user_data: Dict, medicine_name: str, compartment: int) -> bool:
        """
        Send SMS backup if email fails
        
        Args:
            user_data: User information
            medicine_name: Medicine name
            compartment: Compartment number
            
        Returns:
            bool: True if SMS sent successfully
        """
        try:
            phone = user_data.get('emergency_contact_phone')
            if not phone or not self.sms_access_token:
                logger.warning("No phone number or SMS token available for backup")
                return False

            full_name = user_data.get('full_name') or user_data.get('username', 'Patient')
            
            # Create short SMS content (max 160 characters)
            sms_message = f"URGENT: {full_name} missed medicine {medicine_name} (compartment {compartment}). Please check!"
            
            # Send SMS via SpeedSMS API
            sms_data = {
                'access-token': self.sms_access_token,
                'phone': phone,
                'content': sms_message,
                'type': 1  # SMS brandname
            }
            
            response = requests.post(self.sms_api_url, data=sms_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    logger.info(f"SMS backup sent successfully to {phone}")
                    self._log_notification(user_data, 'sms', 'sent', sms_message)
                    return True
                else:
                    logger.error(f"SMS API error: {result.get('message')}")
                    self._log_notification(user_data, 'sms', 'failed', sms_message, result.get('message'))
                    return False
            else:
                logger.error(f"SMS HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"SMS backup error: {str(e)}")
            self._log_notification(user_data, 'sms', 'failed', '', str(e))
            return False

    def _log_notification(self, user_data: Dict, method: str, status: str, message: str, error: str = None):
        """
        Log notification to database (will be implemented in routes)
        
        Args:
            user_data: User information
            method: 'email' or 'sms'
            status: 'sent' or 'failed'
            message: Message content sent
            error: Error message if any
        """
        # Basic logging, database logging will be implemented in routes/main.py
        logger.info(f"Notification Log - User: {user_data.get('username')}, Method: {method}, Status: {status}")

    def send_test_notification(self, test_email: str, phone: str = None) -> Dict[str, Any]:
        """
        Send test notification to check configuration
        
        Args:
            test_email: Email for testing
            phone: Phone number for SMS testing (optional)
            
        Returns:
            Dict containing test results
        """
        results = {
            'email': {'success': False, 'message': ''},
            'sms': {'success': False, 'message': ''}
        }
        
        # Test Email
        try:
            current_time = datetime.now().strftime('%H:%M - %d/%m/%Y')
            test_subject = "TEST: Medicine notification system"
            
            test_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #28a745;">Test successful!</h2>
                <p><strong>Medicine notification system is working normally.</strong></p>
                <p><strong>Test time:</strong> {current_time}</p>
                <hr>
                <p style="color: #6c757d; font-size: 12px;">This is a test email from AI-FOR-ELDER system</p>
            </div>
            """
            
            test_text = f"TEST SUCCESSFUL!\n\nMedicine notification system is working normally.\nTest time: {current_time}\n\n-- AI-FOR-ELDER System"
            
            email_success = self._send_email(test_email, test_subject, test_html, test_text)
            results['email']['success'] = email_success
            results['email']['message'] = 'Sent successfully' if email_success else 'Failed'
            
        except Exception as e:
            results['email']['message'] = f'Error: {str(e)}'
        
        # Test SMS if phone number provided
        if phone:
            try:
                user_data = {'emergency_contact_phone': phone, 'username': 'test', 'full_name': 'Test User'}
                sms_success = self._send_sms_backup(user_data, 'Test Medicine', 1)
                results['sms']['success'] = sms_success
                results['sms']['message'] = 'Sent successfully' if sms_success else 'Failed'
            except Exception as e:
                results['sms']['message'] = f'Error: {str(e)}'
        
        return results

# Singleton instance - renamed for compatibility
notification_service = NotificationService()

# Alias to maintain compatibility with old code
zalo_service = notification_service