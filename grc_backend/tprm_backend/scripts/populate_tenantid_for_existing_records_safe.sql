-- ============================================================================
-- Populate TenantId for Existing Records in All Tables (SAFE VERSION)
-- ============================================================================
-- This script ONLY updates tables that actually exist in your database
-- It dynamically finds all tables with TenantId column and updates them
-- ============================================================================
-- 
-- ASSUMPTION: You have 2 tenants with TenantId = 1 and TenantId = 2
-- ============================================================================

-- Verify tenants exist
SELECT 
    TenantId, 
    Name, 
    Subdomain, 
    Status 
FROM tenants 
WHERE TenantId IN (1, 2)
ORDER BY TenantId;

-- ============================================================================
-- DYNAMIC APPROACH: Find and update only existing tables
-- ============================================================================

-- Create a stored procedure to safely update each table
DELIMITER $$

DROP PROCEDURE IF EXISTS populate_tenantid_for_all_tables$$

CREATE PROCEDURE populate_tenantid_for_all_tables()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE table_name VARCHAR(255);
    DECLARE pk_column VARCHAR(255);
    DECLARE sql_stmt TEXT;
    DECLARE table_count INT DEFAULT 0;
    DECLARE success_count INT DEFAULT 0;
    DECLARE error_count INT DEFAULT 0;
    
    -- Cursor to iterate through all tables with TenantId column
    DECLARE table_cursor CURSOR FOR
        SELECT DISTINCT TABLE_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND COLUMN_NAME = 'TenantId'
          AND TABLE_NAME != 'tenants'
        ORDER BY TABLE_NAME;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN table_cursor;
    
    table_loop: LOOP
        FETCH table_cursor INTO table_name;
        IF done THEN
            LEAVE table_loop;
        END IF;
        
        SET table_count = table_count + 1;
        
        -- Get primary key column for this table
        SELECT COLUMN_NAME INTO pk_column
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = table_name
          AND CONSTRAINT_NAME = 'PRIMARY'
        LIMIT 1;
        
        -- If no primary key found, try common ID columns
        IF pk_column IS NULL THEN
            -- Try common primary key names
            IF EXISTS (SELECT 1 FROM information_schema.COLUMNS 
                      WHERE TABLE_SCHEMA = DATABASE() 
                      AND TABLE_NAME = table_name 
                      AND COLUMN_NAME = 'id') THEN
                SET pk_column = 'id';
            ELSEIF EXISTS (SELECT 1 FROM information_schema.COLUMNS 
                          WHERE TABLE_SCHEMA = DATABASE() 
                          AND TABLE_NAME = table_name 
                          AND COLUMN_NAME = CONCAT(table_name, '_id')) THEN
                SET pk_column = CONCAT(table_name, '_id');
            ELSE
                -- Skip this table if no primary key found
                SELECT CONCAT('⚠️  Skipping ', table_name, ': No primary key found') AS message;
                SET error_count = error_count + 1;
                ITERATE table_loop;
            END IF;
        END IF;
        
        -- Build and execute UPDATE statement
        SET sql_stmt = CONCAT(
            'UPDATE `', table_name, '` ',
            'SET TenantId = CASE ',
            '    WHEN (CAST(`', pk_column, '` AS UNSIGNED) % 2) = 0 THEN 1 ',
            '    ELSE 2 ',
            'END ',
            'WHERE TenantId IS NULL'
        );
        
        -- Execute the statement
        BEGIN
            DECLARE EXIT HANDLER FOR SQLEXCEPTION
            BEGIN
                GET DIAGNOSTICS CONDITION 1
                    @sqlstate = RETURNED_SQLSTATE,
                    @errno = MYSQL_ERRNO,
                    @text = MESSAGE_TEXT;
                SELECT CONCAT('❌ Error updating ', table_name, ': ', @text) AS message;
                SET error_count = error_count + 1;
            END;
            
            SET @sql = sql_stmt;
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            
            -- Get affected rows
            SELECT ROW_COUNT() INTO @affected_rows;
            
            IF @affected_rows > 0 THEN
                SELECT CONCAT('✅ ', table_name, ': Updated ', @affected_rows, ' records') AS message;
                SET success_count = success_count + 1;
            ELSE
                SELECT CONCAT('ℹ️  ', table_name, ': No records to update (all have TenantId)') AS message;
                SET success_count = success_count + 1;
            END IF;
        END;
        
    END LOOP;
    
    CLOSE table_cursor;
    
    -- Summary - Use separate SELECT statements
    SELECT '============================================================' AS separator;
    SELECT CONCAT('SUMMARY: Processed ', table_count, ' table(s)') AS summary;
    SELECT CONCAT('✅ Success: ', success_count) AS success;
    SELECT CONCAT('❌ Errors: ', error_count) AS errors;
    SELECT '============================================================' AS separator_end;
END$$

DELIMITER ;

-- ============================================================================
-- RUN THE PROCEDURE
-- ============================================================================

CALL populate_tenantid_for_all_tables();

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Show distribution for key tables
SELECT 
    'rfps' AS table_name,
    TenantId,
    COUNT(*) AS record_count
FROM rfps
WHERE TenantId IN (1, 2)
GROUP BY TenantId
UNION ALL
SELECT 
    'vendors',
    TenantId,
    COUNT(*)
FROM vendors
WHERE TenantId IN (1, 2)
GROUP BY TenantId
UNION ALL
SELECT 
    'vendor_contracts',
    TenantId,
    COUNT(*)
FROM vendor_contracts
WHERE TenantId IN (1, 2)
GROUP BY TenantId
UNION ALL
SELECT 
    'rfp_evaluation_criteria',
    TenantId,
    COUNT(*)
FROM rfp_evaluation_criteria
WHERE TenantId IN (1, 2)
GROUP BY TenantId
ORDER BY table_name, TenantId;

-- Check for any NULL TenantId values (should be 0 after running)
SELECT 
    TABLE_NAME,
    COUNT(*) AS total_records,
    SUM(CASE WHEN TenantId IS NULL THEN 1 ELSE 0 END) AS null_tenant_count
FROM (
    SELECT 'rfps' AS TABLE_NAME, TenantId FROM rfps
    UNION ALL
    SELECT 'vendors', TenantId FROM vendors
    UNION ALL
    SELECT 'vendor_contracts', TenantId FROM vendor_contracts
    UNION ALL
    SELECT 'rfp_evaluation_criteria', TenantId FROM rfp_evaluation_criteria
) AS combined
GROUP BY TABLE_NAME;

-- ============================================================================
-- CLEANUP: Drop the procedure (optional)
-- ============================================================================

-- DROP PROCEDURE IF EXISTS populate_tenantid_for_all_tables;

