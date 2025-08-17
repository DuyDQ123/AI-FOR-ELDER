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
    """Service để gửi thông báo qua Email (thay thế Zalo cho demo)"""
    
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
            logger.warning("Email credentials not configured. Thông báo email sẽ không hoạt động.")

    def send_missed_medicine_notification(self, user_data: Dict, medicine_name: str, compartment: int) -> bool:
        """
        Gửi thông báo nhỡ thuốc qua Email
        
        Args:
            user_data: Dictionary chứa thông tin user
            medicine_name: Tên thuốc
            compartment: Số ngăn thuốc
            
        Returns:
            bool: True nếu gửi thành công, False nếu thất bại
        """
        try:
            # Lấy email người thân từ emergency_contact_zalo_id field (dùng lại field cũ)
            emergency_email = user_data.get('emergency_contact_zalo_id') or user_data.get('emergency_contact_email')
            if not emergency_email:
                logger.warning(f"User {user_data.get('username')} không có email người thân")
                return self._send_sms_backup(user_data, medicine_name, compartment)

            # Tạo nội dung thông báo
            subject, html_content, text_content = self._create_missed_medicine_email(user_data, medicine_name, compartment)
            
            # Gửi thông báo Email
            success = self._send_email(emergency_email, subject, html_content, text_content)
            
            if success:
                logger.info(f"✅ Đã gửi thông báo Email thành công cho {user_data.get('emergency_contact_name')} ({emergency_email})")
                self._log_notification(user_data, 'email', 'sent', subject)
                return True
            else:
                logger.warning(f"❌ Thất bại gửi Email, thử gửi SMS backup...")
                return self._send_sms_backup(user_data, medicine_name, compartment)
                
        except Exception as e:
            logger.error(f"Lỗi gửi thông báo Email: {str(e)}")
            return self._send_sms_backup(user_data, medicine_name, compartment)

    def _create_missed_medicine_email(self, user_data: Dict, medicine_name: str, compartment: int) -> tuple:
        """Tạo nội dung email thông báo nhỡ thuốc"""
        full_name = user_data.get('full_name') or user_data.get('username', 'Người thân')
        delay_minutes = user_data.get('notification_delay_minutes', 15)
        current_time = datetime.now().strftime('%H:%M - %d/%m/%Y')
        emergency_contact_name = user_data.get('emergency_contact_name', 'Người thân')
        
        subject = f"🚨 KHẨN CẤP: {full_name} chưa uống thuốc {medicine_name}"
        
        # HTML content (đẹp hơn cho email)
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f44336; color: white; padding: 20px; text-align: center;">
                <h1>🚨 THÔNG BÁO KHẨN CẤP 🚨</h1>
            </div>
            
            <div style="padding: 20px; background-color: #f9f9f9;">
                <h2 style="color: #d32f2f;">Thông tin chi tiết:</h2>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;"><strong>👤 Người bệnh:</strong></td>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;">{full_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;"><strong>💊 Tên thuốc:</strong></td>
                        <td style="padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;">{medicine_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;"><strong>📦 Ngăn thuốc:</strong></td>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;">Ngăn số {compartment}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;"><strong>⏰ Thời gian:</strong></td>
                        <td style="padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd;">{current_time}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;"><strong>⏱️ Thời gian chờ:</strong></td>
                        <td style="padding: 10px; background-color: white; border: 1px solid #ddd;">{delay_minutes} phút</td>
                    </tr>
                </table>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <h3 style="margin-top: 0; color: #856404;">❗ Cảnh báo:</h3>
                    <p><strong>{full_name}</strong> chưa xác nhận uống thuốc sau <strong>{delay_minutes} phút</strong>.</p>
                </div>
                
                <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <h3 style="margin-top: 0; color: #0c5460;">🔔 Hành động cần thiết:</h3>
                    <ul style="margin: 0;">
                        <li>Vui lòng <strong>liên hệ ngay</strong> với {full_name}</li>
                        <li>Kiểm tra xem họ đã uống thuốc chưa</li>
                        <li>Nhắc nhở uống thuốc đúng giờ</li>
                        <li>Đảm bảo sức khỏe và an toàn</li>
                    </ul>
                </div>
            </div>
            
            <div style="background-color: #6c757d; color: white; padding: 15px; text-align: center;">
                <p style="margin: 0;"><strong>📱 Hệ thống nhắc thuốc thông minh AI-FOR-ELDER</strong></p>
                <p style="margin: 5px 0 0 0; font-size: 12px;">Email tự động được gửi lúc {current_time}</p>
            </div>
        </body>
        </html>
        """
        
        # Text content (fallback cho email clients không hỗ trợ HTML)
        text_content = f"""
🚨 THÔNG BÁO KHẨN CẤP 🚨

Kính gửi {emergency_contact_name},

👤 Người bệnh: {full_name}
💊 Thuốc: {medicine_name}
📦 Ngăn: {compartment}
⏰ Thời gian: {current_time}

❗ CẢNH BÁO: {full_name} chưa xác nhận uống thuốc sau {delay_minutes} phút.

🔔 VUI LÒNG:
- Liên hệ ngay với {full_name}
- Kiểm tra việc uống thuốc
- Nhắc nhở uống thuốc đúng giờ

📱 Hệ thống nhắc thuốc thông minh AI-FOR-ELDER
Email tự động - {current_time}
        """
        
        return subject, html_content, text_content

    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """
        Gửi email thông báo
        
        Args:
            to_email: Email người nhận
            subject: Tiêu đề email
            html_content: Nội dung HTML
            text_content: Nội dung text (fallback)
            
        Returns:
            bool: True nếu gửi thành công
        """
        if not self.email_user or not self.email_password:
            logger.error("Email credentials không được cấu hình")
            return False
            
        try:
            # Tạo message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = to_email

            # Tạo parts cho text và HTML
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')

            # Thêm parts vào message
            msg.attach(part1)
            msg.attach(part2)

            # Gửi email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)

            logger.info(f"Đã gửi email thành công tới {to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("Lỗi xác thực email - kiểm tra username/password")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Lỗi SMTP: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Lỗi gửi email: {str(e)}")
            return False

    def _send_sms_backup(self, user_data: Dict, medicine_name: str, compartment: int) -> bool:
        """
        Gửi SMS backup nếu Zalo thất bại
        
        Args:
            user_data: Thông tin user
            medicine_name: Tên thuốc
            compartment: Số ngăn
            
        Returns:
            bool: True nếu gửi SMS thành công
        """
        try:
            phone = user_data.get('emergency_contact_phone')
            if not phone or not self.sms_access_token:
                logger.warning("Không có số điện thoại hoặc SMS token để gửi backup")
                return False

            full_name = user_data.get('full_name') or user_data.get('username', 'Nguoi than')
            
            # Tạo nội dung SMS ngắn gọn (tối đa 160 ký tự)
            sms_message = f"KHAN CAP: {full_name} chua uong thuoc {medicine_name} (ngan {compartment}). Vui long kiem tra!"
            
            # Gửi SMS qua SpeedSMS API
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
                    logger.info(f"✅ Đã gửi SMS backup thành công tới {phone}")
                    self._log_notification(user_data, 'sms', 'sent', sms_message)
                    return True
                else:
                    logger.error(f"Lỗi SMS API: {result.get('message')}")
                    self._log_notification(user_data, 'sms', 'failed', sms_message, result.get('message'))
                    return False
            else:
                logger.error(f"Lỗi HTTP SMS: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Lỗi gửi SMS backup: {str(e)}")
            self._log_notification(user_data, 'sms', 'failed', '', str(e))
            return False

    def _log_notification(self, user_data: Dict, method: str, status: str, message: str, error: str = None):
        """
        Ghi log thông báo vào database (sẽ được implement trong routes)
        
        Args:
            user_data: Thông tin user
            method: 'zalo' hoặc 'sms'
            status: 'sent' hoặc 'failed'
            message: Nội dung đã gửi
            error: Thông báo lỗi nếu có
        """
        # Log cơ bản, database logging sẽ được implement trong routes/main.py
        logger.info(f"Notification Log - User: {user_data.get('username')}, Method: {method}, Status: {status}")

    def send_test_notification(self, test_email: str, phone: str = None) -> Dict[str, Any]:
        """
        Gửi thông báo test để kiểm tra cấu hình
        
        Args:
            test_email: Email để test
            phone: Số điện thoại để test SMS (optional)
            
        Returns:
            Dict chứa kết quả test
        """
        results = {
            'email': {'success': False, 'message': ''},
            'sms': {'success': False, 'message': ''}
        }
        
        # Test Email
        try:
            current_time = datetime.now().strftime('%H:%M - %d/%m/%Y')
            test_subject = "🧪 TEST: Hệ thống thông báo thuốc"
            
            test_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #28a745;">✅ Test thành công!</h2>
                <p><strong>Hệ thống thông báo thuốc đang hoạt động bình thường.</strong></p>
                <p><strong>Thời gian test:</strong> {current_time}</p>
                <hr>
                <p style="color: #6c757d; font-size: 12px;">Đây là email test từ hệ thống AI-FOR-ELDER</p>
            </div>
            """
            
            test_text = f"✅ TEST THÀNH CÔNG!\n\nHệ thống thông báo thuốc đang hoạt động bình thường.\nThời gian test: {current_time}\n\n-- Hệ thống AI-FOR-ELDER"
            
            email_success = self._send_email(test_email, test_subject, test_html, test_text)
            results['email']['success'] = email_success
            results['email']['message'] = 'Gửi thành công' if email_success else 'Thất bại'
            
        except Exception as e:
            results['email']['message'] = f'Lỗi: {str(e)}'
        
        # Test SMS nếu có số điện thoại
        if phone:
            try:
                user_data = {'emergency_contact_phone': phone, 'username': 'test', 'full_name': 'Test User'}
                sms_success = self._send_sms_backup(user_data, 'Test Medicine', 1)
                results['sms']['success'] = sms_success
                results['sms']['message'] = 'Gửi thành công' if sms_success else 'Thất bại'
            except Exception as e:
                results['sms']['message'] = f'Lỗi: {str(e)}'
        
        return results

# Singleton instance - đổi tên cho phù hợp
notification_service = NotificationService()

# Alias để tương thích với code cũ
zalo_service = notification_service