-- SQL script to create AccessRequestTPRM table for TPRM access requests
-- This table stores user requests for access permissions that require admin approval

CREATE TABLE IF NOT EXISTS `AccessRequestTPRM` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `requested_url` VARCHAR(500) NULL,
    `requested_feature` VARCHAR(255) NULL,
    `required_permission` VARCHAR(255) NULL,
    `requested_role` VARCHAR(100) NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'REQUESTED',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `approved_by` INT NULL,
    `audit_trail` JSON NULL,
    `message` TEXT NULL,
    INDEX `idx_user_id_created_at` (`user_id`, `created_at`),
    INDEX `idx_status` (`status`),
    INDEX `idx_approved_by` (`approved_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

