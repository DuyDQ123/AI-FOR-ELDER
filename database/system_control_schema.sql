-- Tạo bảng system_control để quản lý trạng thái hệ thống
CREATE TABLE IF NOT EXISTS system_control (
    id INT AUTO_INCREMENT PRIMARY KEY,
    system_enabled BOOLEAN DEFAULT TRUE,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by VARCHAR(50) DEFAULT 'system',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert dữ liệu mặc định
INSERT INTO system_control (id, system_enabled, updated_by, notes) 
VALUES (1, TRUE, 'system_init', 'Khởi tạo hệ thống với trạng thái BẬT')
ON DUPLICATE KEY UPDATE 
system_enabled = VALUES(system_enabled),
updated_at = CURRENT_TIMESTAMP;

-- Tạo index cho hiệu suất
CREATE INDEX idx_system_control_enabled ON system_control (system_enabled);
CREATE INDEX idx_system_control_updated ON system_control (updated_at);