-- =============================================================================
-- MULTITENANCY TEST DATA  — 4 Organisations
-- Organisations : Apollo Hospitals, Vardaan Data Sciences, JSW Steel, IndBank
-- Password      : All test users → Test@1234  (auto-hashed on first login)
-- Run order     : Execute top-to-bottom in a single session
-- Safe to re-run: Uses INSERT IGNORE / ON DUPLICATE KEY where possible
-- =============================================================================

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = '';

-- =============================================================================
-- IDEMPOTENT CLEANUP — Remove previous seed rows so re-running never duplicates
-- Identified by known subdomains / license_keys / codes set in this script
-- =============================================================================
SET SQL_SAFE_UPDATES = 0;

DELETE FROM tenant_user_mapping
WHERE id > 0 AND TenantId IN (SELECT TenantId FROM tenants WHERE Subdomain IN ('apollo','vardaan','jsw','indbank'));

DELETE FROM users
WHERE UserId > 0 AND license_key IN (
    'USR-APL-ADM-001','USR-APL-CMP-002','USR-APL-RSK-003','USR-APL-ANA-004',
    'USR-VAR-ADM-001','USR-VAR-CMP-002','USR-VAR-RSK-003','USR-VAR-USR-004',
    'USR-JSW-ADM-001','USR-JSW-CMP-002','USR-JSW-RSK-003','USR-JSW-AUD-004','USR-JSW-ANA-005',
    'USR-IND-ADM-001','USR-IND-CMP-002','USR-IND-RSK-003','USR-IND-AUD-004'
);

DELETE FROM business_units
WHERE id > 0 AND code IN (
    'APL-HO-CLIN','APL-HO-IT','APL-HO-FIN','APL-NZ-OPS','APL-NZ-HR',
    'VAR-HO-ENG','VAR-HO-DG','VAR-RD-AI','VAR-RD-SEC',
    'JSW-HO-STRAT','JSW-HO-HSE','JSW-HO-LEG','JSW-VJN-BF','JSW-VJN-QA',
    'IND-HO-RISK','IND-HO-COMP','IND-HO-ITSEC','IND-NR-RB','IND-NR-SME'
);

DELETE FROM frameworks
WHERE FrameworkId > 0 AND FrameworkName IN (
    'Apollo GRC Framework','Vardaan GRC Framework','JSW GRC Framework','IndBank GRC Framework',
    'ISO 27001 - Information Security','NIST Cybersecurity Framework','SOC 2 Type II'
);

SET SQL_SAFE_UPDATES = 1;

-- =============================================================================
-- PRE-REQUISITE — Add EntityCode + Description columns (MySQL 5.7+ compatible)
-- Uses a stored procedure so the script is safe to re-run without errors
-- =============================================================================
DROP PROCEDURE IF EXISTS _add_mainentities_cols;
DELIMITER $$
CREATE PROCEDURE _add_mainentities_cols()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'mainentities'
          AND COLUMN_NAME  = 'EntityCode'
    ) THEN
        ALTER TABLE mainentities
            ADD COLUMN EntityCode VARCHAR(100) NULL DEFAULT NULL AFTER EntityName;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'mainentities'
          AND COLUMN_NAME  = 'Description'
    ) THEN
        ALTER TABLE mainentities
            ADD COLUMN Description TEXT NULL DEFAULT NULL AFTER EntityType;
    END IF;
END$$
DELIMITER ;
CALL _add_mainentities_cols();
DROP PROCEDURE IF EXISTS _add_mainentities_cols;

-- =============================================================================
-- SECTION 0 — Domain rows (prerequisite for Framework)
-- =============================================================================
INSERT IGNORE INTO domain (domain_name, isActive) VALUES
    ('Healthcare',     'Y'),
    ('Technology',     'Y'),
    ('Manufacturing',  'Y'),
    ('Banking',        'Y');

-- =============================================================================
-- SECTION 1 — TENANTS
-- =============================================================================
INSERT IGNORE INTO tenants
    (Name, Subdomain, LicenseKey, SubscriptionTier, Status,
     MaxUsers, StorageLimitGB, Settings,
     PrimaryContactEmail, PrimaryContactName, PrimaryContactPhone,
     CreatedAt, UpdatedAt)
VALUES
    ('Apollo Hospitals Group',  'apollo',   'LIC-APOLLO-2025-ENT',   'enterprise',    'active', 100, 50,  '{}', 'grc@apollohospitals.com',  'Ravi Sharma',   '+91-9810001001', NOW(), NOW()),
    ('Vardaan Data Sciences',   'vardaan',  'LIC-VARDAAN-2025-PRO',  'professional',  'active',  50, 20,  '{}', 'grc@vardaands.com',         'Ankit Mehta',   '+91-9820002002', NOW(), NOW()),
    ('JSW Steel Ltd',           'jsw',      'LIC-JSW-2025-ENT',      'enterprise',    'active', 200, 100, '{}', 'grc@jsw.in',                'Priya Nair',    '+91-9830003003', NOW(), NOW()),
    ('IndBank Ltd',             'indbank',  'LIC-INDBANK-2025-PRO',  'professional',  'active',  75, 30,  '{}', 'grc@indbank.co.in',         'Sunita Verma',  '+91-9840004004', NOW(), NOW());

-- Capture IDs
SET @t_apollo   = (SELECT TenantId FROM tenants WHERE Subdomain = 'apollo'  LIMIT 1);
SET @t_vardaan  = (SELECT TenantId FROM tenants WHERE Subdomain = 'vardaan' LIMIT 1);
SET @t_jsw      = (SELECT TenantId FROM tenants WHERE Subdomain = 'jsw'     LIMIT 1);
SET @t_indbank  = (SELECT TenantId FROM tenants WHERE Subdomain = 'indbank' LIMIT 1);

-- =============================================================================
-- SECTION 2 — FRAMEWORKS  (1 per tenant, required by entities / departments)
-- =============================================================================
SET @d_health  = (SELECT domain_id FROM domain WHERE domain_name = 'Healthcare'    LIMIT 1);
SET @d_tech    = (SELECT domain_id FROM domain WHERE domain_name = 'Technology'    LIMIT 1);
SET @d_mfg     = (SELECT domain_id FROM domain WHERE domain_name = 'Manufacturing' LIMIT 1);
SET @d_bank    = (SELECT domain_id FROM domain WHERE domain_name = 'Banking'       LIMIT 1);

INSERT IGNORE INTO frameworks
    (TenantId, domainId, FrameworkName, CurrentVersion, FrameworkDescription,
     EffectiveDate, CreatedByName, CreatedByDate, Category, Status, ActiveInactive,
     Reviewer, InternalExternal)
VALUES
    (@t_apollo,  @d_health, 'Apollo GRC Framework',  1.0, 'Enterprise GRC framework for Apollo Hospitals Group',  '2025-01-01', 'Ravi Sharma',  '2025-01-01', 'Healthcare',    'Active', 'Active', 'Ravi Sharma',  'Internal'),
    (@t_vardaan, @d_tech,   'Vardaan GRC Framework', 1.0, 'Enterprise GRC framework for Vardaan Data Sciences',   '2025-01-01', 'Ankit Mehta',  '2025-01-01', 'Technology',    'Active', 'Active', 'Ankit Mehta',  'Internal'),
    (@t_jsw,     @d_mfg,    'JSW GRC Framework',     1.0, 'Enterprise GRC framework for JSW Steel Ltd',           '2025-01-01', 'Priya Nair',   '2025-01-01', 'Manufacturing', 'Active', 'Active', 'Priya Nair',   'Internal'),
    (@t_indbank, @d_bank,   'IndBank GRC Framework', 1.0, 'Enterprise GRC framework for IndBank Ltd',             '2025-01-01', 'Sunita Verma', '2025-01-01', 'Banking',       'Active', 'Active', 'Sunita Verma', 'Internal'),
    (NULL, NULL, 'ISO 27001 - Information Security',  1.0, 'International standard for information security management systems', '2025-01-01', 'Platform Admin', '2025-01-01', 'Security',      'Approved', 'Active', 'Platform Admin', 'Internal'),
    (NULL, NULL, 'NIST Cybersecurity Framework',      1.0, 'NIST framework for improving critical infrastructure cybersecurity',  '2025-01-01', 'Platform Admin', '2025-01-01', 'Cybersecurity', 'Approved', 'Active', 'Platform Admin', 'Internal'),
    (NULL, NULL, 'SOC 2 Type II',                     1.0, 'Service Organization Control 2 compliance framework',               '2025-01-01', 'Platform Admin', '2025-01-01', 'Compliance',    'Approved', 'Active', 'Platform Admin', 'Internal');

SET @f_apollo   = (SELECT FrameworkId FROM frameworks WHERE TenantId = @t_apollo  ORDER BY FrameworkId DESC LIMIT 1);
SET @f_vardaan  = (SELECT FrameworkId FROM frameworks WHERE TenantId = @t_vardaan ORDER BY FrameworkId DESC LIMIT 1);
SET @f_jsw      = (SELECT FrameworkId FROM frameworks WHERE TenantId = @t_jsw     ORDER BY FrameworkId DESC LIMIT 1);
SET @f_indbank  = (SELECT FrameworkId FROM frameworks WHERE TenantId = @t_indbank ORDER BY FrameworkId DESC LIMIT 1);

-- =============================================================================
-- SECTION 3 — MAIN ENTITIES  (table: mainentities — used by user_entity_mapping)
-- 5 entities per organisation  (Head Office + 4 regional/business units)
-- =============================================================================
INSERT IGNORE INTO mainentities
    (EntityName, EntityCode, EntityType, Description, ParentEntityId, LocationId, IsActive, CreatedDate, FrameworkId)
VALUES
-- ── Apollo (5) ──────────────────────────────────────────────────────────────
    ('Apollo Head Office',             'APL-HQ',  'HeadOffice', 'Apollo Hospitals Group – Corporate Head Office',             NULL, 1, 1, NOW(), @f_apollo),
    ('Apollo Hospitals – North Zone',  'APL-NZ',  'Regional',   'North Zone regional hospitals covering Delhi & NCR',         NULL, 1, 1, NOW(), @f_apollo),
    ('Apollo Hospitals – South Zone',  'APL-SZ',  'Regional',   'South Zone regional hospitals covering Chennai & Bangalore', NULL, 1, 1, NOW(), @f_apollo),
    ('Apollo Diagnostics',             'APL-DX',  'Subsidiary', 'Diagnostics and imaging subsidiary',                         NULL, 1, 1, NOW(), @f_apollo),
    ('Apollo Pharmacies',              'APL-PH',  'Subsidiary', 'Retail pharmacy chain subsidiary',                           NULL, 1, 1, NOW(), @f_apollo),
-- ── Vardaan (4) ──────────────────────────────────────────────────────────────
    ('Vardaan Head Office',            'VAR-HQ',  'HeadOffice', 'Vardaan Data Sciences – Corporate Head Office',              NULL, 1, 1, NOW(), @f_vardaan),
    ('Vardaan R&D Centre',             'VAR-RD',  'Department', 'Research & Development Centre – AI and Data Science',        NULL, 1, 1, NOW(), @f_vardaan),
    ('Vardaan Cloud Services',         'VAR-CS',  'Subsidiary', 'Cloud infrastructure and managed services subsidiary',       NULL, 1, 1, NOW(), @f_vardaan),
    ('Vardaan Analytics Division',     'VAR-AN',  'Department', 'Business analytics and intelligence division',               NULL, 1, 1, NOW(), @f_vardaan),
-- ── JSW (5) ──────────────────────────────────────────────────────────────────
    ('JSW Head Office',                'JSW-HQ',  'HeadOffice', 'JSW Steel Ltd – Corporate Head Office, Mumbai',              NULL, 1, 1, NOW(), @f_jsw),
    ('JSW Steel – Vijayanagar Plant',  'JSW-VJN', 'Plant',      'Vijayanagar integrated steel plant, Bellary Karnataka',      NULL, 1, 1, NOW(), @f_jsw),
    ('JSW Steel – Dolvi Plant',        'JSW-DLV', 'Plant',      'Dolvi integrated steel complex, Raigad Maharashtra',         NULL, 1, 1, NOW(), @f_jsw),
    ('JSW Energy',                     'JSW-EN',  'Subsidiary', 'Power generation and energy subsidiary',                     NULL, 1, 1, NOW(), @f_jsw),
    ('JSW Cement',                     'JSW-CM',  'Subsidiary', 'Cement manufacturing subsidiary',                            NULL, 1, 1, NOW(), @f_jsw),
-- ── IndBank (4) ──────────────────────────────────────────────────────────────
    ('IndBank Head Office',            'IND-HQ',  'HeadOffice', 'IndBank Ltd – Corporate Head Office, Mumbai',                NULL, 1, 1, NOW(), @f_indbank),
    ('IndBank – North Region',         'IND-NR',  'Regional',   'North regional banking offices covering Delhi & UP',         NULL, 1, 1, NOW(), @f_indbank),
    ('IndBank – South Region',         'IND-SR',  'Regional',   'South regional banking offices covering Chennai & Kerala',   NULL, 1, 1, NOW(), @f_indbank),
    ('IndBank Treasury & Markets',     'IND-TM',  'Department', 'Treasury, capital markets and forex division',               NULL, 1, 1, NOW(), @f_indbank);

-- Capture first entity ID per tenant (used for FK links below)
SET @me_apollo_1   = (SELECT Id FROM mainentities WHERE FrameworkId = @f_apollo  ORDER BY Id LIMIT 1);
SET @me_apollo_2   = (SELECT Id FROM mainentities WHERE FrameworkId = @f_apollo  ORDER BY Id LIMIT 1 OFFSET 1);
SET @me_vardaan_1  = (SELECT Id FROM mainentities WHERE FrameworkId = @f_vardaan ORDER BY Id LIMIT 1);
SET @me_jsw_1      = (SELECT Id FROM mainentities WHERE FrameworkId = @f_jsw     ORDER BY Id LIMIT 1);
SET @me_jsw_2      = (SELECT Id FROM mainentities WHERE FrameworkId = @f_jsw     ORDER BY Id LIMIT 1 OFFSET 1);
SET @me_indbank_1  = (SELECT Id FROM mainentities WHERE FrameworkId = @f_indbank ORDER BY Id LIMIT 1);

-- SECTION 4 — ENTITIES table removed (not used; business_units references mainentities directly)

-- =============================================================================
-- SECTION 5 — USERS  (4 users per tenant, plain-text passwords auto-hashed on first login)
-- Usernames are plaintext — login works via find_by_username() plaintext fallback
-- password = Test@1234
-- =============================================================================
INSERT IGNORE INTO users
    (TenantId, UserName, Password, Email, FirstName, LastName,
     DepartmentId, IsActive, consent_accepted, license_key,
     CreatedAt, UpdatedAt)
VALUES
-- ── Apollo (UserId auto) ──────────────────────────────────────────────────────
    (@t_apollo, 'apollo_admin',      'Test@1234', 'apollo.admin@apollohospitals.com',      'Ravi',     'Sharma',   'DEPT-APL-001', 'Y', '1', 'USR-APL-ADM-001', NOW(), NOW()),
    (@t_apollo, 'apollo_compliance', 'Test@1234', 'apollo.compliance@apollohospitals.com', 'Meena',    'Pillai',   'DEPT-APL-001', 'Y', '1', 'USR-APL-CMP-002', NOW(), NOW()),
    (@t_apollo, 'apollo_risk',       'Test@1234', 'apollo.risk@apollohospitals.com',       'Suresh',   'Kumar',    'DEPT-APL-002', 'Y', '1', 'USR-APL-RSK-003', NOW(), NOW()),
    (@t_apollo, 'apollo_analyst',    'Test@1234', 'apollo.analyst@apollohospitals.com',    'Kavitha',  'Iyer',     'DEPT-APL-002', 'Y', '1', 'USR-APL-ANA-004', NOW(), NOW()),
-- ── Vardaan ──────────────────────────────────────────────────────────────────
    (@t_vardaan, 'vardaan_admin',      'Test@1234', 'admin@vardaands.com',       'Ankit',    'Mehta',    'DEPT-VAR-001', 'Y', '1', 'USR-VAR-ADM-001', NOW(), NOW()),
    (@t_vardaan, 'vardaan_compliance', 'Test@1234', 'compliance@vardaands.com',  'Pooja',    'Srinivas', 'DEPT-VAR-001', 'Y', '1', 'USR-VAR-CMP-002', NOW(), NOW()),
    (@t_vardaan, 'vardaan_risk',       'Test@1234', 'risk@vardaands.com',        'Rahul',    'Joshi',    'DEPT-VAR-002', 'Y', '1', 'USR-VAR-RSK-003', NOW(), NOW()),
    (@t_vardaan, 'vardaan_enduser',    'Test@1234', 'user@vardaands.com',        'Sneha',    'Patil',    'DEPT-VAR-002', 'Y', '1', 'USR-VAR-USR-004', NOW(), NOW()),
-- ── JSW ──────────────────────────────────────────────────────────────────────
    (@t_jsw, 'jsw_admin',      'Test@1234', 'grc.admin@jsw.in',       'Priya',    'Nair',     'DEPT-JSW-001', 'Y', '1', 'USR-JSW-ADM-001', NOW(), NOW()),
    (@t_jsw, 'jsw_compliance', 'Test@1234', 'compliance@jsw.in',      'Vikram',   'Rao',      'DEPT-JSW-001', 'Y', '1', 'USR-JSW-CMP-002', NOW(), NOW()),
    (@t_jsw, 'jsw_risk',       'Test@1234', 'risk@jsw.in',            'Deepa',    'Reddy',    'DEPT-JSW-002', 'Y', '1', 'USR-JSW-RSK-003', NOW(), NOW()),
    (@t_jsw, 'jsw_audit',      'Test@1234', 'audit@jsw.in',           'Arun',     'Bhat',     'DEPT-JSW-003', 'Y', '1', 'USR-JSW-AUD-004', NOW(), NOW()),
    (@t_jsw, 'jsw_analyst',    'Test@1234', 'analyst@jsw.in',         'Rekha',    'Shetty',   'DEPT-JSW-003', 'Y', '1', 'USR-JSW-ANA-005', NOW(), NOW()),
-- ── IndBank ──────────────────────────────────────────────────────────────────
    (@t_indbank, 'indbank_admin',      'Test@1234', 'grc.admin@indbank.co.in',   'Sunita',   'Verma',    'DEPT-IND-001', 'Y', '1', 'USR-IND-ADM-001', NOW(), NOW()),
    (@t_indbank, 'indbank_compliance', 'Test@1234', 'compliance@indbank.co.in',  'Mohan',    'Das',      'DEPT-IND-001', 'Y', '1', 'USR-IND-CMP-002', NOW(), NOW()),
    (@t_indbank, 'indbank_risk',       'Test@1234', 'risk@indbank.co.in',        'Lalitha',  'Gopalan',  'DEPT-IND-002', 'Y', '1', 'USR-IND-RSK-003', NOW(), NOW()),
    (@t_indbank, 'indbank_audit',      'Test@1234', 'audit@indbank.co.in',       'Venkat',   'Krishnan', 'DEPT-IND-002', 'Y', '1', 'USR-IND-AUD-004', NOW(), NOW());

-- Also populate username_hash & email_hash (SHA-256 of lowercase value)
UPDATE users SET
    username_hash = SHA2(LOWER(UserName), 256),
    email_hash    = SHA2(LOWER(Email),    256)
WHERE username_hash IS NULL AND TenantId IN (@t_apollo, @t_vardaan, @t_jsw, @t_indbank);

-- Capture user IDs for FK links
SET @u_apollo_admin      = (SELECT UserId FROM users WHERE UserName = 'apollo_admin'      AND TenantId = @t_apollo   LIMIT 1);
SET @u_apollo_compliance = (SELECT UserId FROM users WHERE UserName = 'apollo_compliance' AND TenantId = @t_apollo   LIMIT 1);
SET @u_apollo_risk       = (SELECT UserId FROM users WHERE UserName = 'apollo_risk'       AND TenantId = @t_apollo   LIMIT 1);
SET @u_apollo_analyst    = (SELECT UserId FROM users WHERE UserName = 'apollo_analyst'    AND TenantId = @t_apollo   LIMIT 1);

SET @u_vardaan_admin      = (SELECT UserId FROM users WHERE UserName = 'vardaan_admin'      AND TenantId = @t_vardaan  LIMIT 1);
SET @u_vardaan_compliance = (SELECT UserId FROM users WHERE UserName = 'vardaan_compliance' AND TenantId = @t_vardaan  LIMIT 1);
SET @u_vardaan_risk       = (SELECT UserId FROM users WHERE UserName = 'vardaan_risk'       AND TenantId = @t_vardaan  LIMIT 1);

SET @u_jsw_admin      = (SELECT UserId FROM users WHERE UserName = 'jsw_admin'      AND TenantId = @t_jsw      LIMIT 1);
SET @u_jsw_compliance = (SELECT UserId FROM users WHERE UserName = 'jsw_compliance' AND TenantId = @t_jsw      LIMIT 1);
SET @u_jsw_risk       = (SELECT UserId FROM users WHERE UserName = 'jsw_risk'       AND TenantId = @t_jsw      LIMIT 1);
SET @u_jsw_audit      = (SELECT UserId FROM users WHERE UserName = 'jsw_audit'      AND TenantId = @t_jsw      LIMIT 1);

SET @u_indbank_admin      = (SELECT UserId FROM users WHERE UserName = 'indbank_admin'      AND TenantId = @t_indbank  LIMIT 1);
SET @u_indbank_compliance = (SELECT UserId FROM users WHERE UserName = 'indbank_compliance' AND TenantId = @t_indbank  LIMIT 1);
SET @u_indbank_risk       = (SELECT UserId FROM users WHERE UserName = 'indbank_risk'       AND TenantId = @t_indbank  LIMIT 1);
SET @u_indbank_audit      = (SELECT UserId FROM users WHERE UserName = 'indbank_audit'      AND TenantId = @t_indbank  LIMIT 1);

-- =============================================================================
-- SECTION 5B — TENANT USER MAPPINGS  (maps each user to their tenant)
-- =============================================================================
INSERT IGNORE INTO tenant_user_mapping
    (TenantId, UserId, role, is_primary, status, is_deleted, created_at, updated_at)
VALUES
-- ── Apollo ───────────────────────────────────────────────────────────────────
    (@t_apollo, @u_apollo_admin,      'GRC Administrator',  1, 'active', 0, NOW(), NOW()),
    (@t_apollo, @u_apollo_compliance, 'Compliance Manager', 0, 'active', 0, NOW(), NOW()),
    (@t_apollo, @u_apollo_risk,       'Risk Manager',       0, 'active', 0, NOW(), NOW()),
    (@t_apollo, @u_apollo_analyst,    'Viewer',             0, 'active', 0, NOW(), NOW()),
-- ── Vardaan ──────────────────────────────────────────────────────────────────
    (@t_vardaan, @u_vardaan_admin,      'GRC Administrator',  1, 'active', 0, NOW(), NOW()),
    (@t_vardaan, @u_vardaan_compliance, 'Compliance Manager', 0, 'active', 0, NOW(), NOW()),
    (@t_vardaan, @u_vardaan_risk,       'Risk Manager',       0, 'active', 0, NOW(), NOW()),
-- ── JSW ──────────────────────────────────────────────────────────────────────
    (@t_jsw, @u_jsw_admin,      'GRC Administrator',  1, 'active', 0, NOW(), NOW()),
    (@t_jsw, @u_jsw_compliance, 'Compliance Manager', 0, 'active', 0, NOW(), NOW()),
    (@t_jsw, @u_jsw_risk,       'Risk Manager',       0, 'active', 0, NOW(), NOW()),
    (@t_jsw, @u_jsw_audit,      'Auditor',            0, 'active', 0, NOW(), NOW()),
-- ── IndBank ──────────────────────────────────────────────────────────────────
    (@t_indbank, @u_indbank_admin,      'GRC Administrator',  1, 'active', 0, NOW(), NOW()),
    (@t_indbank, @u_indbank_compliance, 'Compliance Manager', 0, 'active', 0, NOW(), NOW()),
    (@t_indbank, @u_indbank_risk,       'Risk Manager',       0, 'active', 0, NOW(), NOW()),
    (@t_indbank, @u_indbank_audit,      'Auditor',            0, 'active', 0, NOW(), NOW());

-- =============================================================================
-- SECTION 6 — RBAC  (one role-record per user per role)
-- GRC Administrator → all permissions enabled
-- Compliance Manager → compliance + policy permissions
-- Risk Manager → risk permissions
-- Audit Manager → audit permissions
-- End User / Analyst → read-only
-- =============================================================================
INSERT IGNORE INTO rbac
    (TenantId, UserId, UserName, Role,
     CreateCompliance, EditCompliance, ApproveCompliance, ViewAllCompliance, CompliancePerformanceAnalytics,
     CreatePolicy, EditPolicy, ApprovePolicy, CreateFramework, ApproveFramework, ViewAllPolicy, PolicyPerformanceAnalytics,
     AssignAudit, ConductAudit, ReviewAudit, ViewAuditReports, AuditPerformanceAnalytics,
     CreateRisk, EditRisk, ApproveRisk, AssignRisk, EvaluateAssignedRisk, ViewAllRisk, RiskPerformanceAnalytics,
     CreateIncident, EditIncident, AssignIncident, EvaluateAssignedIncident, EscalateToRisk,
     ViewAllIncident, IncidentPerformanceAnalytics,
     CreateEvent, EditEvent, ApproveEvent, RejectEvent, ArchiveEvent, ViewAllEvents, ViewModuleEvents, EventPerformanceAnalytics,
     IsActive, CreatedAt, UpdatedAt)
VALUES
-- ═══════════════════════ APOLLO ═══════════════════════════════════════════════
-- apollo_admin → GRC Administrator (all permissions)
    (@t_apollo, @u_apollo_admin, 'apollo_admin', 'GRC Administrator',
     1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1,1, 'Y', NOW(), NOW()),
-- apollo_compliance → Compliance Manager
    (@t_apollo, @u_apollo_compliance, 'apollo_compliance', 'Compliance Manager',
     1,1,1,1,1, 1,1,1,0,0,1,1, 0,0,1,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,1,0, 'Y', NOW(), NOW()),
-- apollo_risk → Risk Manager
    (@t_apollo, @u_apollo_risk, 'apollo_risk', 'Risk Manager',
     0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,1,1,0, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1, 0,0,0,0,0,1,1,0, 'Y', NOW(), NOW()),
-- apollo_analyst → End User
    (@t_apollo, @u_apollo_analyst, 'apollo_analyst', 'End User',
     0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,1,0, 'Y', NOW(), NOW()),

-- ═══════════════════════ VARDAAN ══════════════════════════════════════════════
    (@t_vardaan, @u_vardaan_admin, 'vardaan_admin', 'GRC Administrator',
     1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1,1, 'Y', NOW(), NOW()),
    (@t_vardaan, @u_vardaan_compliance, 'vardaan_compliance', 'Compliance Manager',
     1,1,1,1,1, 1,1,1,0,0,1,1, 0,0,1,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,1,0, 'Y', NOW(), NOW()),
    (@t_vardaan, @u_vardaan_risk, 'vardaan_risk', 'Risk Manager',
     0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,1,1,0, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1, 0,0,0,0,0,1,1,0, 'Y', NOW(), NOW()),

-- ═══════════════════════ JSW ══════════════════════════════════════════════════
    (@t_jsw, @u_jsw_admin, 'jsw_admin', 'GRC Administrator',
     1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1,1, 'Y', NOW(), NOW()),
    (@t_jsw, @u_jsw_compliance, 'jsw_compliance', 'Compliance Manager',
     1,1,1,1,1, 1,1,1,0,0,1,1, 0,0,1,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,1,0, 'Y', NOW(), NOW()),
    (@t_jsw, @u_jsw_risk, 'jsw_risk', 'Risk Manager',
     0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,1,1,0, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1, 0,0,0,0,0,1,1,0, 'Y', NOW(), NOW()),
    (@t_jsw, @u_jsw_audit, 'jsw_audit', 'Audit Manager',
     0,0,0,1,0, 0,0,0,0,0,1,0, 1,1,1,1,1, 0,0,0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,1,0, 'Y', NOW(), NOW()),

-- ═══════════════════════ INDBANK ══════════════════════════════════════════════
    (@t_indbank, @u_indbank_admin, 'indbank_admin', 'GRC Administrator',
     1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1,1, 'Y', NOW(), NOW()),
    (@t_indbank, @u_indbank_compliance, 'indbank_compliance', 'Compliance Manager',
     1,1,1,1,1, 1,1,1,0,0,1,1, 0,0,1,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,1,0, 'Y', NOW(), NOW()),
    (@t_indbank, @u_indbank_risk, 'indbank_risk', 'Risk Manager',
     0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,1,1,0, 1,1,1,1,1,1,1, 1,1,1,1,1,1,1, 0,0,0,0,0,1,1,0, 'Y', NOW(), NOW()),
    (@t_indbank, @u_indbank_audit, 'indbank_audit', 'Audit Manager',
     0,0,0,1,0, 0,0,0,0,0,1,0, 1,1,1,1,1, 0,0,0,0,0,1,0, 0,0,0,0,0,1,0, 0,0,0,0,0,1,1,0, 'Y', NOW(), NOW());

-- =============================================================================
-- SECTION 7 — TENANT USER MAPPING
-- =============================================================================
INSERT IGNORE INTO tenant_user_mapping
    (TenantId, UserId, role, is_primary, assigned_at, status, is_deleted, created_at, updated_at)
VALUES
    (@t_apollo,  @u_apollo_admin,      'GRC Administrator',  1, NOW(), 'active', 0, NOW(), NOW()),
    (@t_apollo,  @u_apollo_compliance, 'Compliance Manager', 0, NOW(), 'active', 0, NOW(), NOW()),
    (@t_apollo,  @u_apollo_risk,       'Risk Manager',       0, NOW(), 'active', 0, NOW(), NOW()),
    (@t_apollo,  @u_apollo_analyst,    'End User',           0, NOW(), 'active', 0, NOW(), NOW()),

    (@t_vardaan, @u_vardaan_admin,      'GRC Administrator',  1, NOW(), 'active', 0, NOW(), NOW()),
    (@t_vardaan, @u_vardaan_compliance, 'Compliance Manager', 0, NOW(), 'active', 0, NOW(), NOW()),
    (@t_vardaan, @u_vardaan_risk,       'Risk Manager',       0, NOW(), 'active', 0, NOW(), NOW()),

    (@t_jsw, @u_jsw_admin,      'GRC Administrator', 1, NOW(), 'active', 0, NOW(), NOW()),
    (@t_jsw, @u_jsw_compliance, 'Compliance Manager',0, NOW(), 'active', 0, NOW(), NOW()),
    (@t_jsw, @u_jsw_risk,       'Risk Manager',      0, NOW(), 'active', 0, NOW(), NOW()),
    (@t_jsw, @u_jsw_audit,      'Audit Manager',     0, NOW(), 'active', 0, NOW(), NOW()),

    (@t_indbank, @u_indbank_admin,      'GRC Administrator',  1, NOW(), 'active', 0, NOW(), NOW()),
    (@t_indbank, @u_indbank_compliance, 'Compliance Manager', 0, NOW(), 'active', 0, NOW(), NOW()),
    (@t_indbank, @u_indbank_risk,       'Risk Manager',       0, NOW(), 'active', 0, NOW(), NOW()),
    (@t_indbank, @u_indbank_audit,      'Audit Manager',      0, NOW(), 'active', 0, NOW(), NOW());

-- =============================================================================
-- SECTION 8 — USER ENTITY MAPPING  (links users to mainentities)
-- admin → all entities (admin), others → head office + 1 regional (read/write)
-- =============================================================================
INSERT IGNORE INTO user_entity_mapping
    (UserId, EntityId, TenantId, role, access_level, assigned_at, status, is_deleted, created_at, updated_at)
VALUES
-- Apollo admin → all 5 entities
    (@u_apollo_admin, @me_apollo_1,     @t_apollo, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_apollo_admin, @me_apollo_1 + 1, @t_apollo, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_apollo_admin, @me_apollo_1 + 2, @t_apollo, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_apollo_admin, @me_apollo_1 + 3, @t_apollo, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_apollo_admin, @me_apollo_1 + 4, @t_apollo, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
-- Apollo compliance → head office + south zone
    (@u_apollo_compliance, @me_apollo_1,     @t_apollo, 'Compliance Manager', 'write', NOW(), 'active', 0, NOW(), NOW()),
    (@u_apollo_compliance, @me_apollo_1 + 2, @t_apollo, 'Compliance Manager', 'write', NOW(), 'active', 0, NOW(), NOW()),
-- Apollo risk → head office + north zone
    (@u_apollo_risk, @me_apollo_1,     @t_apollo, 'Risk Manager', 'write', NOW(), 'active', 0, NOW(), NOW()),
    (@u_apollo_risk, @me_apollo_1 + 1, @t_apollo, 'Risk Manager', 'write', NOW(), 'active', 0, NOW(), NOW()),
-- Apollo analyst → head office (read)
    (@u_apollo_analyst, @me_apollo_1, @t_apollo, 'End User', 'read', NOW(), 'active', 0, NOW(), NOW()),

-- Vardaan admin → all 4 entities
    (@u_vardaan_admin, @me_vardaan_1,     @t_vardaan, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_vardaan_admin, @me_vardaan_1 + 1, @t_vardaan, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_vardaan_admin, @me_vardaan_1 + 2, @t_vardaan, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_vardaan_admin, @me_vardaan_1 + 3, @t_vardaan, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_vardaan_compliance, @me_vardaan_1,     @t_vardaan, 'Compliance Manager', 'write', NOW(), 'active', 0, NOW(), NOW()),
    (@u_vardaan_compliance, @me_vardaan_1 + 1, @t_vardaan, 'Compliance Manager', 'write', NOW(), 'active', 0, NOW(), NOW()),
    (@u_vardaan_risk, @me_vardaan_1, @t_vardaan, 'Risk Manager', 'write', NOW(), 'active', 0, NOW(), NOW()),

-- JSW admin → all 5 entities
    (@u_jsw_admin, @me_jsw_1,     @t_jsw, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_jsw_admin, @me_jsw_1 + 1, @t_jsw, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_jsw_admin, @me_jsw_1 + 2, @t_jsw, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_jsw_admin, @me_jsw_1 + 3, @t_jsw, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_jsw_admin, @me_jsw_1 + 4, @t_jsw, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_jsw_compliance, @me_jsw_1,     @t_jsw, 'Compliance Manager', 'write', NOW(), 'active', 0, NOW(), NOW()),
    (@u_jsw_risk,       @me_jsw_1,     @t_jsw, 'Risk Manager',       'write', NOW(), 'active', 0, NOW(), NOW()),
    (@u_jsw_risk,       @me_jsw_1 + 1, @t_jsw, 'Risk Manager',       'write', NOW(), 'active', 0, NOW(), NOW()),
    (@u_jsw_audit,      @me_jsw_1,     @t_jsw, 'Audit Manager',      'write', NOW(), 'active', 0, NOW(), NOW()),
    (@u_jsw_audit,      @me_jsw_1 + 2, @t_jsw, 'Audit Manager',      'write', NOW(), 'active', 0, NOW(), NOW()),

-- IndBank admin → all 4 entities
    (@u_indbank_admin, @me_indbank_1,     @t_indbank, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_indbank_admin, @me_indbank_1 + 1, @t_indbank, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_indbank_admin, @me_indbank_1 + 2, @t_indbank, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_indbank_admin, @me_indbank_1 + 3, @t_indbank, 'GRC Administrator', 'admin', NOW(), 'active', 0, NOW(), NOW()),
    (@u_indbank_compliance, @me_indbank_1,     @t_indbank, 'Compliance Manager', 'write', NOW(), 'active', 0, NOW(), NOW()),
    (@u_indbank_risk,       @me_indbank_1,     @t_indbank, 'Risk Manager',       'write', NOW(), 'active', 0, NOW(), NOW()),
    (@u_indbank_audit,      @me_indbank_1,     @t_indbank, 'Audit Manager',      'write', NOW(), 'active', 0, NOW(), NOW()),
    (@u_indbank_audit,      @me_indbank_1 + 1, @t_indbank, 'Audit Manager',      'write', NOW(), 'active', 0, NOW(), NOW());

-- =============================================================================
-- SECTION 9 — BUSINESS UNITS  (2-3 per entity, references mainentities.Id)
-- =============================================================================
INSERT IGNORE INTO business_units
    (TenantId, EntityId, name, code, description, status, is_deleted, created_at, updated_at)
VALUES
-- Apollo – Head Office BUs
    (@t_apollo, @me_apollo_1, 'Clinical Operations',    'APL-HO-CLIN',  'Clinical operations management',           'active', 0, NOW(), NOW()),
    (@t_apollo, @me_apollo_1, 'IT & Digital Health',    'APL-HO-IT',    'Information technology and digital health', 'active', 0, NOW(), NOW()),
    (@t_apollo, @me_apollo_1, 'Finance & Compliance',   'APL-HO-FIN',   'Finance, compliance and regulatory',        'active', 0, NOW(), NOW()),
-- Apollo – North Zone BUs
    (@t_apollo, @me_apollo_2, 'North Operations',       'APL-NZ-OPS',   'North zone hospital operations',            'active', 0, NOW(), NOW()),
    (@t_apollo, @me_apollo_2, 'North HR',               'APL-NZ-HR',    'Human resources – north zone',              'active', 0, NOW(), NOW()),

-- Vardaan – Head Office BUs
    (@t_vardaan, @me_vardaan_1, 'Product Engineering',  'VAR-HO-ENG',   'Core product engineering',                  'active', 0, NOW(), NOW()),
    (@t_vardaan, @me_vardaan_1, 'Data Governance',      'VAR-HO-DG',    'Data governance and privacy',               'active', 0, NOW(), NOW()),
-- Vardaan – R&D Centre BUs  (@me_vardaan_1 + 1 = second mainentity for vardaan)
    (@t_vardaan, @me_vardaan_1 + 1, 'AI Research',      'VAR-RD-AI',    'Artificial intelligence research',          'active', 0, NOW(), NOW()),
    (@t_vardaan, @me_vardaan_1 + 1, 'Security Lab',     'VAR-RD-SEC',   'Cyber security research lab',               'active', 0, NOW(), NOW()),

-- JSW – Head Office BUs
    (@t_jsw, @me_jsw_1, 'Corporate Strategy',           'JSW-HO-STRAT', 'Corporate strategy and planning',           'active', 0, NOW(), NOW()),
    (@t_jsw, @me_jsw_1, 'HSE',                          'JSW-HO-HSE',   'Health, safety and environment',            'active', 0, NOW(), NOW()),
    (@t_jsw, @me_jsw_1, 'Legal & Compliance',           'JSW-HO-LEG',   'Legal and compliance affairs',              'active', 0, NOW(), NOW()),
-- JSW – Vijayanagar Plant BUs
    (@t_jsw, @me_jsw_2, 'Blast Furnace Ops',            'JSW-VJN-BF',   'Blast furnace operations',                  'active', 0, NOW(), NOW()),
    (@t_jsw, @me_jsw_2, 'Quality Assurance',            'JSW-VJN-QA',   'Quality assurance and control',             'active', 0, NOW(), NOW()),

-- IndBank – Head Office BUs
    (@t_indbank, @me_indbank_1, 'Risk Management',      'IND-HO-RISK',  'Enterprise risk management',                'active', 0, NOW(), NOW()),
    (@t_indbank, @me_indbank_1, 'Compliance',           'IND-HO-COMP',  'Regulatory compliance and audit',           'active', 0, NOW(), NOW()),
    (@t_indbank, @me_indbank_1, 'IT Security',          'IND-HO-ITSEC', 'IT security and cyber risk',                'active', 0, NOW(), NOW()),
-- IndBank – North Region BUs
    (@t_indbank, @me_indbank_1 + 1, 'Retail Banking',   'IND-NR-RB',    'Retail banking operations',                 'active', 0, NOW(), NOW()),
    (@t_indbank, @me_indbank_1 + 1, 'SME Banking',      'IND-NR-SME',   'SME and MSME banking',                      'active', 0, NOW(), NOW());

-- =============================================================================
-- SECTION 10 — TENANT MODULES  (all 7 modules enabled for each tenant)
-- =============================================================================
INSERT IGNORE INTO tenant_modules
    (TenantId, module_code, is_enabled, license_tier, configured_at, created_at, updated_at)
SELECT
    t.TenantId, m.module_code, 1, t.SubscriptionTier, NOW(), NOW(), NOW()
FROM tenants t
CROSS JOIN (
    SELECT 'framework'  AS module_code UNION ALL
    SELECT 'policy'                    UNION ALL
    SELECT 'compliance'                UNION ALL
    SELECT 'audit'                     UNION ALL
    SELECT 'risk'                      UNION ALL
    SELECT 'incident'                  UNION ALL
    SELECT 'event'
) m
WHERE t.Subdomain IN ('apollo', 'vardaan', 'jsw', 'indbank');

-- =============================================================================
-- SECTION 11 — TENANT SECURITY SETTINGS  (one row per tenant)
-- =============================================================================
INSERT IGNORE INTO tenant_security_settings
    (TenantId, mfa_required, mfa_methods, sso_enabled, sso_config,
     allowed_email_domains, ip_restriction_enabled, allowed_ip_ranges,
     session_timeout_minutes, password_expiry_days,
     export_allowed, export_requires_approval, updated_at)
VALUES
    (@t_apollo,  0, '["totp","email"]', 0, '{}', '["apollohospitals.com"]', 0, '[]', 30, 90, 1, 0, NOW()),
    (@t_vardaan, 0, '["totp"]',         0, '{}', '["vardaands.com"]',       0, '[]', 60, 90, 1, 0, NOW()),
    (@t_jsw,     0, '["totp","sms"]',   0, '{}', '["jsw.in"]',              0, '[]', 30, 60, 1, 1, NOW()),
    (@t_indbank, 1, '["totp","sms"]',   0, '{}', '["indbank.co.in"]',       0, '[]', 15, 30, 1, 1, NOW());

-- =============================================================================
-- SECTION 12 — TENANT BRANDING  (one row per tenant)
-- =============================================================================
INSERT IGNORE INTO tenant_branding
    (TenantId, logo_url, favicon_url, primary_color, secondary_color, accent_color,
     email_footer_text, updated_at)
VALUES
    (@t_apollo,  'https://cdn.apollohospitals.com/logo.png',    'https://cdn.apollohospitals.com/favicon.ico', '#0057A8', '#004080', '#FF6B35', 'Apollo Hospitals Group | GRC Platform',         NOW()),
    (@t_vardaan, 'https://cdn.vardaands.com/logo.png',          'https://cdn.vardaands.com/favicon.ico',       '#2D6A4F', '#1B4332', '#52B788', 'Vardaan Data Sciences | GRC Platform',          NOW()),
    (@t_jsw,     'https://cdn.jsw.in/logo.png',                 'https://cdn.jsw.in/favicon.ico',             '#C0392B', '#922B21', '#F1948A', 'JSW Steel Ltd | GRC Platform',                  NOW()),
    (@t_indbank, 'https://cdn.indbank.co.in/logo.png',          'https://cdn.indbank.co.in/favicon.ico',      '#154360', '#1A5276', '#5DADE2', 'IndBank Ltd | GRC Platform',                    NOW());

-- =============================================================================
-- DONE — Re-enable FK checks
-- =============================================================================
SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- QUICK VERIFICATION QUERIES  (run these to confirm data is correct)
-- =============================================================================
/*
SELECT t.TenantId, t.Name, t.Subdomain, t.Status,
       COUNT(DISTINCT u.UserId)  AS users,
       COUNT(DISTINCT tm.id)     AS modules,
       COUNT(DISTINCT me.Id)     AS entities
FROM tenants t
LEFT JOIN users u               ON u.TenantId  = t.TenantId
LEFT JOIN tenant_modules tm     ON tm.TenantId = t.TenantId AND tm.is_enabled = 1
LEFT JOIN mainentities me       ON me.FrameworkId IN (SELECT FrameworkId FROM frameworks WHERE TenantId = t.TenantId)
WHERE t.Subdomain IN ('apollo','vardaan','jsw','indbank')
GROUP BY t.TenantId, t.Name, t.Subdomain, t.Status;
*/
