-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS elder_project;
USE elder_project;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    user_type VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_by INT,
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- System configuration table
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(50) NOT NULL UNIQUE,
    value VARCHAR(200),
    description TEXT,
    updated_at DATETIME NOT NULL,
    updated_by INT NOT NULL,
    FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Admin logs table
CREATE TABLE IF NOT EXISTS admin_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id INT,
    details TEXT,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (admin_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Medicines table
CREATE TABLE IF NOT EXISTS medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    notes TEXT,
    image VARCHAR(200),
    user_id INT NOT NULL,
    compartment_number INT NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    min_quantity INT NOT NULL DEFAULT 5,
    dosage INT NOT NULL DEFAULT 1,
    expiry_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY unique_compartment (compartment_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Schedules table
CREATE TABLE IF NOT EXISTS schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    user_id INT NOT NULL,
    time VARCHAR(5) NOT NULL,
    days VARCHAR(100) NOT NULL,
    period VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Medicine history table
CREATE TABLE IF NOT EXISTS medicine_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL,
    notes TEXT,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default users if not exist
INSERT IGNORE INTO users (username, email, password_hash, role, status) VALUES
('superadmin', 'superadmin@example.com', 'pbkdf2:sha256:260000$sixmZvNqFpPETCR2$16ac4017c176c630cee539632786c42a7c8fff07ffb7b1ffd159edcd0d0961f3', 'super_admin', 'active');

-- Get superadmin ID safely
SET @admin_id = (SELECT id FROM users WHERE username = 'superadmin');

-- Insert admin if not exists
INSERT IGNORE INTO users (username, email, password_hash, role, status, created_by) VALUES
('admin', 'admin@example.com', 'pbkdf2:sha256:260000$0mQs1wjwHmiHDBsj$3a56204c5408672cb5f430ad6e3c2b01349335384b4cf8738cf84e2ae5cf1552', 'admin', 'active', @admin_id);

-- Insert system configurations if not exist
INSERT IGNORE INTO system_config (`key`, value, description, updated_at, updated_by) VALUES
('max_users', '1000', 'Số lượng người dùng tối đa', NOW(), @admin_id),
('alert_timeout', '300', 'Thời gian chờ nhắc nhở lại (giây)', NOW(), @admin_id),
('backup_interval', '86400', 'Thời gian giữa các lần sao lưu tự động (giây)', NOW(), @admin_id),
('dispenser_servo_speed', '50', 'Tốc độ quay servo (Hz)', NOW(), @admin_id),
('dispenser_open_time', '1.5', 'Thời gian mở ngăn thuốc (giây)', NOW(), @admin_id),
('low_quantity_alert', 'true', 'Bật/tắt cảnh báo thuốc sắp hết', NOW(), @admin_id),
('expiry_alert_days', '30', 'Số ngày cảnh báo trước khi thuốc hết hạn', NOW(), @admin_id);