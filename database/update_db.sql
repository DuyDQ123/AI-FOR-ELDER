USE elder_project;

-- Add new medicine columns one at a time
ALTER TABLE medicines ADD compartment_number INT NOT NULL DEFAULT 0;
ALTER TABLE medicines ADD quantity INT NOT NULL DEFAULT 0;
ALTER TABLE medicines ADD min_quantity INT NOT NULL DEFAULT 5;
ALTER TABLE medicines ADD dosage INT NOT NULL DEFAULT 1;
ALTER TABLE medicines ADD expiry_date DATE NULL;

-- Add unique constraint for compartment
CREATE UNIQUE INDEX medicines_unique_compartment ON medicines (compartment_number);

-- Update system configurations
INSERT INTO system_config (`key`, `value`, `description`, `updated_at`, `updated_by`)
SELECT 'dispenser_servo_speed', '50', 'Tốc độ quay servo (Hz)', NOW(), 1
FROM dual
WHERE NOT EXISTS (
    SELECT 1 FROM system_config WHERE `key` = 'dispenser_servo_speed'
);

INSERT INTO system_config (`key`, `value`, `description`, `updated_at`, `updated_by`)
SELECT 'dispenser_open_time', '1.5', 'Thời gian mở ngăn thuốc (giây)', NOW(), 1
FROM dual
WHERE NOT EXISTS (
    SELECT 1 FROM system_config WHERE `key` = 'dispenser_open_time'
);

INSERT INTO system_config (`key`, `value`, `description`, `updated_at`, `updated_by`)
SELECT 'low_quantity_alert', 'true', 'Bật/tắt cảnh báo thuốc sắp hết', NOW(), 1
FROM dual
WHERE NOT EXISTS (
    SELECT 1 FROM system_config WHERE `key` = 'low_quantity_alert'
);

INSERT INTO system_config (`key`, `value`, `description`, `updated_at`, `updated_by`)
SELECT 'expiry_alert_days', '30', 'Số ngày cảnh báo trước khi thuốc hết hạn', NOW(), 1
FROM dual
WHERE NOT EXISTS (
    SELECT 1 FROM system_config WHERE `key` = 'expiry_alert_days'
);