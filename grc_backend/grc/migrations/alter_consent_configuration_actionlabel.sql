-- Migration: Increase ActionLabel column size in consent_configuration table
-- From: VARCHAR(100) 
-- To: VARCHAR(1000)
-- Reason: Encrypted action labels can exceed 100 characters

-- Run this SQL script in your MySQL database

ALTER TABLE `grc2`.`consent_configuration` 
MODIFY COLUMN `ActionLabel` VARCHAR(1000) NOT NULL;

-- Verify the change
-- DESCRIBE `grc2`.`consent_configuration`;
