-- ============================================================================
-- PHASE 1: Add TenantId to CRITICAL Tables Only
-- ============================================================================
-- Run this first for the most important tables
-- ============================================================================

-- Set the default tenant ID
SET @default_tenant_id = (SELECT TenantId FROM tenants WHERE Subdomain = 'default' LIMIT 1);

-- If default tenant doesn't exist, create it
SET @default_exists = (SELECT COUNT(*) FROM tenants WHERE Subdomain = 'default');
SET @sql = IF(@default_exists = 0,
    'INSERT INTO tenants (Name, Subdomain, LicenseKey, SubscriptionTier, Status, MaxUsers, StorageLimitGB, Settings)
     VALUES (''Default Tenant'', ''default'', ''DEFAULT-LICENSE-TPRM'', ''enterprise'', ''active'', 1000, 1000, ''{}'')',
    'SELECT ''Default tenant already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @default_tenant_id = (SELECT TenantId FROM tenants WHERE Subdomain = 'default' LIMIT 1);

-- ============================================================================
-- 1. USERS TABLE (Required First)
-- ============================================================================
ALTER TABLE users 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_users_tenant_id (TenantId);

UPDATE users SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- 2. RFPS TABLE
-- ============================================================================
-- Note: Check if your table is named 'rfp' or 'rfps' and adjust accordingly
ALTER TABLE rfps 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfps_tenant_id (TenantId);

UPDATE rfps SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- 3. VENDORS TABLE
-- ============================================================================
ALTER TABLE vendors 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendors_tenant_id (TenantId);

UPDATE vendors SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- 4. CONTRACTS TABLE
-- ============================================================================
-- Note: Check if your table is named 'contracts' or 'vendor_contracts' and adjust
ALTER TABLE contracts 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contracts_tenant_id (TenantId);

UPDATE contracts SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- 5. RBAC TPRM TABLE
-- ============================================================================
ALTER TABLE rbac_tprm 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rbac_tprm_tenant_id (TenantId);

UPDATE rbac_tprm SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- VERIFICATION
-- ============================================================================
SELECT 
    'users' AS table_name,
    COUNT(*) AS total_records,
    COUNT(TenantId) AS records_with_tenant
FROM users
UNION ALL
SELECT 'rfps', COUNT(*), COUNT(TenantId) FROM rfps
UNION ALL
SELECT 'vendors', COUNT(*), COUNT(TenantId) FROM vendors
UNION ALL
SELECT 'contracts', COUNT(*), COUNT(TenantId) FROM contracts
UNION ALL
SELECT 'rbac_tprm', COUNT(*), COUNT(TenantId) FROM rbac_tprm;

