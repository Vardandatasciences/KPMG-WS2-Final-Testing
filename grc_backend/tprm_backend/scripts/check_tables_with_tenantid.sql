-- ============================================================================
-- Check Which Tables Have TenantId Column
-- ============================================================================
-- Run this query FIRST to see which tables actually have TenantId column
-- Then comment out tables in populate script that don't have TenantId
-- ============================================================================

SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND COLUMN_NAME = 'TenantId'
  AND TABLE_NAME != 'tenants'
ORDER BY TABLE_NAME;

-- ============================================================================
-- Tables WITHOUT TenantId Column (for reference)
-- ============================================================================
-- Run this to see tables that should have TenantId but don't yet

SELECT 
    t.TABLE_NAME,
    'Missing TenantId column' AS status
FROM information_schema.TABLES t
WHERE t.TABLE_SCHEMA = DATABASE()
  AND t.TABLE_TYPE = 'BASE TABLE'
  AND t.TABLE_NAME NOT IN (
      SELECT DISTINCT TABLE_NAME
      FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND COLUMN_NAME = 'TenantId'
  )
  AND t.TABLE_NAME NOT IN ('tenants', 'django_migrations', 'django_content_type', 'django_session')
ORDER BY t.TABLE_NAME;

