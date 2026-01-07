-- ============================================================================
-- Add TenantId Column to Vendor Risk Module Tables
-- ============================================================================
-- This script adds TenantId column, foreign key, and index to all Vendor Risk module tables
-- TenantId will be NULL by default - you can update records later as needed
-- ============================================================================

-- ============================================================================
-- VENDOR RISK ASSESSMENT TABLES
-- ============================================================================

-- 1. vendor_risk_assessments - Main vendor risk assessments table
ALTER TABLE vendor_risk_assessments 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_risk_assessments_tenant_id (TenantId);

-- 2. vendor_risk_factors - Risk factors for assessments
ALTER TABLE vendor_risk_factors 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_risk_factors_tenant_id (TenantId);

-- 3. vendor_risk_thresholds - Risk thresholds by category
ALTER TABLE vendor_risk_thresholds 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_risk_thresholds_tenant_id (TenantId);

-- 4. risk_tprm - General risk TPRM records
ALTER TABLE risk_tprm 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_risk_tprm_tenant_id (TenantId);

-- 5. vendor_lifecycle_stages - Vendor lifecycle stages
ALTER TABLE vendor_lifecycle_stages 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_lifecycle_stages_tenant_id (TenantId);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these queries to verify the TenantId column was added successfully

-- Check all tables have TenantId column
SELECT 
    'vendor_risk_assessments' AS table_name,
    COUNT(*) AS total_records,
    COUNT(TenantId) AS records_with_tenant,
    COUNT(*) - COUNT(TenantId) AS records_without_tenant
FROM vendor_risk_assessments
UNION ALL
SELECT 
    'vendor_risk_factors',
    COUNT(*),
    COUNT(TenantId),
    COUNT(*) - COUNT(TenantId)
FROM vendor_risk_factors
UNION ALL
SELECT 
    'vendor_risk_thresholds',
    COUNT(*),
    COUNT(TenantId),
    COUNT(*) - COUNT(TenantId)
FROM vendor_risk_thresholds
UNION ALL
SELECT 
    'risk_tprm',
    COUNT(*),
    COUNT(TenantId),
    COUNT(*) - COUNT(TenantId)
FROM risk_tprm
UNION ALL
SELECT 
    'vendor_lifecycle_stages',
    COUNT(*),
    COUNT(TenantId),
    COUNT(*) - COUNT(TenantId)
FROM vendor_lifecycle_stages;

-- Verify foreign key constraints exist
SELECT 
    TABLE_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME IN (
        'vendor_risk_assessments',
        'vendor_risk_factors',
        'vendor_risk_thresholds',
        'risk_tprm',
        'vendor_lifecycle_stages'
    )
    AND REFERENCED_TABLE_NAME = 'tenants'
    AND REFERENCED_COLUMN_NAME = 'TenantId';

-- Verify indexes exist
SHOW INDEX FROM vendor_risk_assessments WHERE Column_name = 'TenantId';
SHOW INDEX FROM vendor_risk_factors WHERE Column_name = 'TenantId';
SHOW INDEX FROM vendor_risk_thresholds WHERE Column_name = 'TenantId';
SHOW INDEX FROM risk_tprm WHERE Column_name = 'TenantId';
SHOW INDEX FROM vendor_lifecycle_stages WHERE Column_name = 'TenantId';

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. All TenantId columns are set to NULL initially
-- 2. You can update records to assign them to tenants later as needed
-- 3. You can make TenantId NOT NULL later if needed (after ensuring all records have a tenant)
-- 4. The foreign key constraint ensures referential integrity
-- 5. The index improves query performance when filtering by tenant
-- 6. To assign records to tenants, update them manually:
--    UPDATE vendor_risk_assessments SET TenantId = <tenant_id> WHERE <condition>;
-- ============================================================================

