-- ============================================================================
-- Add TenantId to All TPRM Tables for Multi-Tenancy
-- ============================================================================
-- This script adds TenantId column, foreign key, and index to all tenant-aware tables
-- Run this script in your TPRM database
-- ============================================================================

-- Set the default tenant ID (should already exist from add_tenant_to_users.sql)
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
-- PHASE 1: CRITICAL TABLES (Do These First)
-- ============================================================================

-- 1. Users table (ALREADY DONE if you ran add_tenant_to_users.sql)
-- Uncomment if you haven't run it yet:
-- ALTER TABLE users 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_users_tenant_id (TenantId);
-- UPDATE users SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- 2. RFPs table (check if table is 'rfp' or 'rfps')
ALTER TABLE rfps 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfps_tenant_id (TenantId);

UPDATE rfps SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- 3. Vendors table
ALTER TABLE vendors 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendors_tenant_id (TenantId);

UPDATE vendors SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- 4. Contracts table (check if table is 'contracts' or 'vendor_contracts')
ALTER TABLE contracts 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contracts_tenant_id (TenantId);

UPDATE contracts SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- 5. RBAC TPRM table
ALTER TABLE rbac_tprm 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rbac_tprm_tenant_id (TenantId);

UPDATE rbac_tprm SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 2: HIGH PRIORITY TABLES
-- ============================================================================

-- RFP Approval Tables
ALTER TABLE approval_workflows 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_workflows_tenant_id (TenantId);

UPDATE approval_workflows SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE approval_requests 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_requests_tenant_id (TenantId);

UPDATE approval_requests SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE approval_stages 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_stages_tenant_id (TenantId);

UPDATE approval_stages SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- Risk Analysis Tables
ALTER TABLE risk_analysis 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_risk_analysis_tenant_id (TenantId);

UPDATE risk_analysis SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_risk_analysis 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_risk_analysis_tenant_id (TenantId);

UPDATE vendor_risk_analysis SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- Compliance Table
ALTER TABLE compliance 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_compliance_tenant_id (TenantId);

UPDATE compliance SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- Audits Tables
ALTER TABLE audits 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_audits_tenant_id (TenantId);

UPDATE audits SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE audits_contract 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_audits_contract_tenant_id (TenantId);

UPDATE audits_contract SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 3: MEDIUM PRIORITY TABLES
-- ============================================================================

-- SLAs Table
ALTER TABLE slas 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_slas_tenant_id (TenantId);

UPDATE slas SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- BCP/DRP Tables
ALTER TABLE plan 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_plan_tenant_id (TenantId);

UPDATE plan SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE bcp_drp_approvals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_bcp_drp_approvals_tenant_id (TenantId);

UPDATE bcp_drp_approvals SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- RFP Related Tables
ALTER TABLE rfp_evaluation_criteria 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_evaluation_criteria_tenant_id (TenantId);

UPDATE rfp_evaluation_criteria SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE file_storage 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_file_storage_tenant_id (TenantId);

UPDATE file_storage SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- Contract Related Tables
ALTER TABLE vendor_contacts 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_contacts_tenant_id (TenantId);

UPDATE vendor_contacts SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE contract_terms 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_terms_tenant_id (TenantId);

UPDATE contract_terms SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE contract_clauses 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_clauses_tenant_id (TenantId);

UPDATE contract_clauses SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE contract_approval 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_approval_tenant_id (TenantId);

UPDATE contract_approval SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- Access Requests
ALTER TABLE AccessRequestTPRM 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_AccessRequestTPRM_tenant_id (TenantId);

UPDATE AccessRequestTPRM SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 4: ADDITIONAL TABLES (If They Exist)
-- ============================================================================

-- RFP Additional Tables (uncomment if these tables exist)
-- ALTER TABLE rfp_versions 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_rfp_versions_tenant_id (TenantId);
-- UPDATE rfp_versions SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ALTER TABLE rfp_responses 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_rfp_responses_tenant_id (TenantId);
-- UPDATE rfp_responses SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ALTER TABLE rfp_invitations 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_rfp_invitations_tenant_id (TenantId);
-- UPDATE rfp_invitations SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- Contract Additional Tables
-- ALTER TABLE contract_amendments 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_contract_amendments_tenant_id (TenantId);
-- UPDATE contract_amendments SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ALTER TABLE contract_renewals 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_contract_renewals_tenant_id (TenantId);
-- UPDATE contract_renewals SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- Vendor Additional Tables
-- ALTER TABLE vendor_categories 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_vendor_categories_tenant_id (TenantId);
-- UPDATE vendor_categories SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ALTER TABLE vendor_assessments 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_vendor_assessments_tenant_id (TenantId);
-- UPDATE vendor_assessments SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- Risk Analysis Additional Tables
-- ALTER TABLE rfp_risk_analysis 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_rfp_risk_analysis_tenant_id (TenantId);
-- UPDATE rfp_risk_analysis SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ALTER TABLE contract_risk_analysis 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_contract_risk_analysis_tenant_id (TenantId);
-- UPDATE contract_risk_analysis SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- Notifications (if tenant-specific)
-- ALTER TABLE notifications 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_notifications_tenant_id (TenantId);
-- UPDATE notifications SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- Analytics (if tenant-specific)
-- ALTER TABLE analytics_events 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_analytics_events_tenant_id (TenantId);
-- UPDATE analytics_events SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check which tables have TenantId column
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND COLUMN_NAME = 'TenantId'
ORDER BY TABLE_NAME;

-- Count records per tenant (should show all in default tenant)
SELECT 
    'rfps' AS table_name,
    COUNT(*) AS total_records,
    COUNT(TenantId) AS records_with_tenant,
    COUNT(*) - COUNT(TenantId) AS records_without_tenant
FROM rfps
UNION ALL
SELECT 'vendors', COUNT(*), COUNT(TenantId), COUNT(*) - COUNT(TenantId) FROM vendors
UNION ALL
SELECT 'contracts', COUNT(*), COUNT(TenantId), COUNT(*) - COUNT(TenantId) FROM contracts
UNION ALL
SELECT 'rbac_tprm', COUNT(*), COUNT(TenantId), COUNT(*) - COUNT(TenantId) FROM rbac_tprm
UNION ALL
SELECT 'approval_workflows', COUNT(*), COUNT(TenantId), COUNT(*) - COUNT(TenantId) FROM approval_workflows
UNION ALL
SELECT 'approval_requests', COUNT(*), COUNT(TenantId), COUNT(*) - COUNT(TenantId) FROM approval_requests
UNION ALL
SELECT 'risk_analysis', COUNT(*), COUNT(TenantId), COUNT(*) - COUNT(TenantId) FROM risk_analysis
UNION ALL
SELECT 'compliance', COUNT(*), COUNT(TenantId), COUNT(*) - COUNT(TenantId) FROM compliance
UNION ALL
SELECT 'audits', COUNT(*), COUNT(TenantId), COUNT(*) - COUNT(TenantId) FROM audits;

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================
-- Note: If any table doesn't exist, the ALTER statement will fail.
-- Comment out or remove tables that don't exist in your database.
-- ============================================================================

