-- ============================================================================
-- Find Primary Key Columns for All Tables with TenantId
-- ============================================================================
-- Run this query first to see the actual primary key column names
-- Then update the populate script with correct column names
-- ============================================================================

SELECT 
    t.TABLE_NAME,
    k.COLUMN_NAME AS primary_key_column,
    c.DATA_TYPE AS pk_data_type
FROM information_schema.TABLES t
INNER JOIN information_schema.KEY_COLUMN_USAGE k
    ON t.TABLE_SCHEMA = k.TABLE_SCHEMA
    AND t.TABLE_NAME = k.TABLE_NAME
    AND k.CONSTRAINT_NAME = 'PRIMARY'
INNER JOIN information_schema.COLUMNS c
    ON t.TABLE_SCHEMA = c.TABLE_SCHEMA
    AND t.TABLE_NAME = c.TABLE_NAME
    AND k.COLUMN_NAME = c.COLUMN_NAME
WHERE t.TABLE_SCHEMA = DATABASE()
  AND t.TABLE_NAME IN (
      SELECT DISTINCT TABLE_NAME
      FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND COLUMN_NAME = 'TenantId'
        AND TABLE_NAME != 'tenants'
  )
ORDER BY t.TABLE_NAME;

