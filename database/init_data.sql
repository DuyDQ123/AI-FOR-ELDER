USE elder_project;

-- Insert superadmin if not exists
INSERT IGNORE INTO users (username, email, password_hash, role, status) VALUES
('superadmin', 'superadmin@example.com', 'pbkdf2:sha256:260000$sixmZvNqFpPETCR2$16ac4017c176c630cee539632786c42a7c8fff07ffb7b1ffd159edcd0d0961f3', 'super_admin', 'active');

-- Get superadmin ID safely
SET @admin_id = (SELECT id FROM users WHERE username = 'superadmin');

-- Insert admin if not exists
INSERT IGNORE INTO users (username, email, password_hash, role, status, created_by) VALUES
('admin', 'admin@example.com', 'pbkdf2:sha256:260000$0mQs1wjwHmiHDBsj$3a56204c5408672cb5f430ad6e3c2b01349335384b4cf8738cf84e2ae5cf1552', 'admin', 'active', @admin_id);

-- Insert or update system configurations
INSERT INTO system_config (`key`, value, description, updated_at, updated_by) VALUES
('dispenser_servo_speed', '50', 'Tốc độ quay servo (Hz)', NOW(), @admin_id),
('dispenser_open_time', '1.5', 'Thời gian mở ngăn thuốc (giây)', NOW(), @admin_id),
('low_quantity_alert', 'true', 'Bật/tắt cảnh báo thuốc sắp hết', NOW(), @admin_id),
('expiry_alert_days', '30', 'Số ngày cảnh báo trước khi thuốc hết hạn', NOW(), @admin_id)
ON DUPLICATE KEY UPDATE 
    value = VALUES(value),
    description = VALUES(description),
    updated_at = NOW(),
    updated_by = @admin_id;