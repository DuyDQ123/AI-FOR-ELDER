-- SQL script to update the `users` table and add missing columns
ALTER TABLE `users`
ADD COLUMN `full_name` VARCHAR(100) DEFAULT NULL AFTER `status`,
ADD COLUMN `age` INT DEFAULT NULL AFTER `full_name`,
ADD COLUMN `phone` VARCHAR(20) DEFAULT NULL AFTER `age`,
ADD COLUMN `address` TEXT DEFAULT NULL AFTER `phone`,
ADD COLUMN `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP AFTER `address`;