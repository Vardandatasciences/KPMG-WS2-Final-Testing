-- ============================================================================
-- PHASE 3: Add TenantId to MEDIUM PRIORITY Tables
-- ============================================================================
-- Run this after Phase 2 is complete
-- ============================================================================

SET @default_tenant_id = (SELECT TenantId FROM tenants WHERE Subdomain = 'default' LIMIT 1);

-- ============================================================================
-- SLAs TABLE
-- ============================================================================
ALTER TABLE slas 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_slas_tenant_id (TenantId);

UPDATE slas SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- BCP/DRP TABLES
-- ============================================================================
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

-- ============================================================================
-- RFP RELATED TABLES
-- ============================================================================
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

-- ============================================================================
-- CONTRACT RELATED TABLES
-- ============================================================================
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

-- ============================================================================
-- ACCESS REQUESTS
-- ============================================================================
ALTER TABLE AccessRequestTPRM 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_AccessRequestTPRM_tenant_id (TenantId);

UPDATE AccessRequestTPRM SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- VERIFICATION
-- ============================================================================
SELECT 
    'slas' AS table_name,
    COUNT(*) AS total_records,
    COUNT(TenantId) AS records_with_tenant
FROM slas
UNION ALL
SELECT 'plan', COUNT(*), COUNT(TenantId) FROM plan
UNION ALL
SELECT 'bcp_drp_approvals', COUNT(*), COUNT(TenantId) FROM bcp_drp_approvals
UNION ALL
SELECT 'rfp_evaluation_criteria', COUNT(*), COUNT(TenantId) FROM rfp_evaluation_criteria
UNION ALL
SELECT 'file_storage', COUNT(*), COUNT(TenantId) FROM file_storage
UNION ALL
SELECT 'vendor_contacts', COUNT(*), COUNT(TenantId) FROM vendor_contacts
UNION ALL
SELECT 'contract_terms', COUNT(*), COUNT(TenantId) FROM contract_terms
UNION ALL
SELECT 'contract_clauses', COUNT(*), COUNT(TenantId) FROM contract_clauses
UNION ALL
SELECT 'contract_approval', COUNT(*), COUNT(TenantId) FROM contract_approval
UNION ALL
SELECT 'AccessRequestTPRM', COUNT(*), COUNT(TenantId) FROM AccessRequestTPRM;

