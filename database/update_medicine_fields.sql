-- Add new columns to medicines table for dispenser functionality
ALTER TABLE medicines 
ADD COLUMN compartment_number INTEGER NOT NULL DEFAULT 0;

ALTER TABLE medicines
ADD COLUMN quantity INTEGER NOT NULL DEFAULT 0;

ALTER TABLE medicines
ADD COLUMN min_quantity INTEGER NOT NULL DEFAULT 5;

ALTER TABLE medicines
ADD COLUMN dosage INTEGER NOT NULL DEFAULT 1;

ALTER TABLE medicines
ADD COLUMN expiry_date DATE NULL;

-- Add unique constraint for compartment
ALTER TABLE medicines
ADD CONSTRAINT unique_compartment UNIQUE (compartment_number);

-- Add new system configurations for dispenser
INSERT INTO system_config (`key`, `value`, `description`, `updated_at`, `updated_by`) 
SELECT 'dispenser_servo_speed', '50', 'Tốc độ quay servo (Hz)', CURRENT_TIMESTAMP, 1
WHERE NOT EXISTS (SELECT 1 FROM system_config WHERE `key` = 'dispenser_servo_speed');

INSERT INTO system_config (`key`, `value`, `description`, `updated_at`, `updated_by`)
SELECT 'dispenser_open_time', '1.5', 'Thời gian mở ngăn thuốc (giây)', CURRENT_TIMESTAMP, 1
WHERE NOT EXISTS (SELECT 1 FROM system_config WHERE `key` = 'dispenser_open_time');

INSERT INTO system_config (`key`, `value`, `description`, `updated_at`, `updated_by`)
SELECT 'low_quantity_alert', 'true', 'Bật/tắt cảnh báo thuốc sắp hết', CURRENT_TIMESTAMP, 1
WHERE NOT EXISTS (SELECT 1 FROM system_config WHERE `key` = 'low_quantity_alert');

INSERT INTO system_config (`key`, `value`, `description`, `updated_at`, `updated_by`)
SELECT 'expiry_alert_days', '30', 'Số ngày cảnh báo trước khi thuốc hết hạn', CURRENT_TIMESTAMP, 1
WHERE NOT EXISTS (SELECT 1 FROM system_config WHERE `key` = 'expiry_alert_days');