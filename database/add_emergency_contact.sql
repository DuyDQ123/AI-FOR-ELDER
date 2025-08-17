-- Thêm các trường thông tin người thân khẩn cấp vào bảng users
ALTER TABLE users 
ADD COLUMN emergency_contact_name VARCHAR(100) COMMENT 'Tên người thân khẩn cấp',
ADD COLUMN emergency_contact_phone VARCHAR(20) COMMENT 'SĐT người thân khẩn cấp', 
ADD COLUMN emergency_contact_relationship VARCHAR(50) COMMENT 'Mối quan hệ với người thân',
ADD COLUMN emergency_contact_zalo_id VARCHAR(100) COMMENT 'Zalo ID người thân để gửi thông báo',
ADD COLUMN notification_delay_minutes INT DEFAULT 15 COMMENT 'Thời gian chờ trước khi gửi thông báo (phút)';

-- Thêm bảng lịch sử thông báo
CREATE TABLE IF NOT EXISTS notification_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    schedule_id INT,
    notification_type VARCHAR(50) NOT NULL COMMENT 'missed_medicine, emergency, reminder',
    recipient_phone VARCHAR(20),
    recipient_zalo_id VARCHAR(100),
    message_content TEXT,
    delivery_status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending, sent, failed',
    sent_at DATETIME NOT NULL,
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (schedule_id) REFERENCES schedules(id),
    INDEX idx_notification_user_time (user_id, sent_at),
    INDEX idx_notification_status (delivery_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;