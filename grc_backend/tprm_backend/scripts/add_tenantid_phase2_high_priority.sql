-- ============================================================================
-- PHASE 2: Add TenantId to HIGH PRIORITY Tables
-- ============================================================================
-- Run this after Phase 1 is complete
-- ============================================================================

SET @default_tenant_id = (SELECT TenantId FROM tenants WHERE Subdomain = 'default' LIMIT 1);

-- ============================================================================
-- RFP APPROVAL TABLES
-- ============================================================================

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

-- ============================================================================
-- RISK ANALYSIS TABLES
-- ============================================================================

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

-- ============================================================================
-- COMPLIANCE TABLE
-- ============================================================================

ALTER TABLE compliance 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_compliance_tenant_id (TenantId);

UPDATE compliance SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- AUDITS TABLES
-- ============================================================================

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
-- VERIFICATION
-- ============================================================================
SELECT 
    'approval_workflows' AS table_name,
    COUNT(*) AS total_records,
    COUNT(TenantId) AS records_with_tenant
FROM approval_workflows
UNION ALL
SELECT 'approval_requests', COUNT(*), COUNT(TenantId) FROM approval_requests
UNION ALL
SELECT 'approval_stages', COUNT(*), COUNT(TenantId) FROM approval_stages
UNION ALL
SELECT 'risk_analysis', COUNT(*), COUNT(TenantId) FROM risk_analysis
UNION ALL
SELECT 'vendor_risk_analysis', COUNT(*), COUNT(TenantId) FROM vendor_risk_analysis
UNION ALL
SELECT 'compliance', COUNT(*), COUNT(TenantId) FROM compliance
UNION ALL
SELECT 'audits', COUNT(*), COUNT(TenantId) FROM audits
UNION ALL
SELECT 'audits_contract', COUNT(*), COUNT(TenantId) FROM audits_contract;

