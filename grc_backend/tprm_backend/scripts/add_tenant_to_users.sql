-- ============================================================================
-- Add TenantId to Users Table for TPRM Multi-Tenancy
-- ============================================================================

-- Step 1: Add TenantId column to users table
ALTER TABLE users 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_users_tenant_id (TenantId);

-- Step 2: Create a default tenant for existing users (if not exists)
-- Check if default tenant already exists
SET @default_tenant_exists = (SELECT COUNT(*) FROM tenants WHERE Subdomain = 'default');

-- Only create default tenant if it doesn't exist
SET @sql = IF(@default_tenant_exists = 0,
    'INSERT INTO tenants (Name, Subdomain, LicenseKey, SubscriptionTier, Status, MaxUsers, StorageLimitGB, Settings)
     VALUES (''Default Tenant'', ''default'', ''DEFAULT-LICENSE-TPRM'', ''enterprise'', ''active'', 1000, 1000, ''{}'')',
    'SELECT ''Default tenant already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Step 3: Get the default tenant ID
SET @default_tenant_id = (SELECT TenantId FROM tenants WHERE Subdomain = 'default' LIMIT 1);

-- Step 4: Assign all existing users to default tenant (only if TenantId is NULL)
UPDATE users 
SET TenantId = @default_tenant_id 
WHERE TenantId IS NULL;

-- Step 5: Verify the changes
SELECT 
    COUNT(*) AS total_users,
    COUNT(TenantId) AS users_with_tenant,
    COUNT(*) - COUNT(TenantId) AS users_without_tenant
FROM users;

-- Show sample of users with their tenant
SELECT 
    u.UserId,
    u.UserName,
    u.Email,
    t.Name AS TenantName,
    t.Subdomain
FROM users u
LEFT JOIN tenants t ON u.TenantId = t.TenantId
LIMIT 10;

