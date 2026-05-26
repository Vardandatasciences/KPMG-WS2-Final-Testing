-- =============================================================================
-- PHASE 1: Enterprise Multi-Tenancy SQL
-- Database: test_grc
-- Run order: execute top to bottom
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1.2  NEW TABLE: business_units
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS business_units (
    id              INT            NOT NULL AUTO_INCREMENT,
    name            VARCHAR(255)   NOT NULL,
    code            VARCHAR(50)    NOT NULL UNIQUE,
    description     LONGTEXT,
    status          VARCHAR(20)    NOT NULL DEFAULT 'active',
    is_deleted      TINYINT(1)     NOT NULL DEFAULT 0,
    created_at      DATETIME(6)    NOT NULL,
    updated_at      DATETIME(6)    NOT NULL,
    TenantId        INT            NOT NULL,
    EntityId        INT            NOT NULL,
    HeadUserId      INT            DEFAULT NULL,
    ParentBUId      INT            DEFAULT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_bu_tenant
        FOREIGN KEY (TenantId)   REFERENCES tenants(TenantId)     ON DELETE CASCADE,
    CONSTRAINT fk_bu_entity
        FOREIGN KEY (EntityId)   REFERENCES mainentities(Id)       ON DELETE CASCADE,
    CONSTRAINT fk_bu_head
        FOREIGN KEY (HeadUserId) REFERENCES users(UserId)          ON DELETE SET NULL,
    CONSTRAINT fk_bu_parent
        FOREIGN KEY (ParentBUId) REFERENCES business_units(id)     ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -----------------------------------------------------------------------------
-- 1.2  NEW TABLE: tenant_user_mapping
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_user_mapping (
    id              INT            NOT NULL AUTO_INCREMENT,
    role            VARCHAR(100)   NOT NULL,
    is_primary      TINYINT(1)     NOT NULL DEFAULT 0,
    assigned_at     DATETIME(6)    NOT NULL,
    status          VARCHAR(20)    NOT NULL DEFAULT 'active',
    is_deleted      TINYINT(1)     NOT NULL DEFAULT 0,
    created_at      DATETIME(6)    NOT NULL,
    updated_at      DATETIME(6)    NOT NULL,
    TenantId        INT            NOT NULL,
    UserId          INT            NOT NULL,
    AssignedById    INT            DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_tenant_user (TenantId, UserId),
    CONSTRAINT fk_tum_tenant
        FOREIGN KEY (TenantId)     REFERENCES tenants(TenantId) ON DELETE CASCADE,
    CONSTRAINT fk_tum_user
        FOREIGN KEY (UserId)       REFERENCES users(UserId)     ON DELETE CASCADE,
    CONSTRAINT fk_tum_assigned_by
        FOREIGN KEY (AssignedById) REFERENCES users(UserId)     ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -----------------------------------------------------------------------------
-- 1.2  NEW TABLE: mainentities
--      Core entity registry per tenant/framework — referenced by user_entity_mapping
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mainentities (
    Id              INT             NOT NULL AUTO_INCREMENT,
    EntityName      VARCHAR(1000)   NOT NULL,
    EntityCode      VARCHAR(100)    DEFAULT NULL,
    EntityType      VARCHAR(255)    NOT NULL,
    Description     LONGTEXT        DEFAULT NULL,
    ParentEntityId  INT             DEFAULT NULL,
    LocationId      INT             NOT NULL DEFAULT 1,
    IsActive        TINYINT(1)      NOT NULL DEFAULT 1,
    CreatedDate     DATETIME(6)     NOT NULL,
    retentionExpiry DATE            DEFAULT NULL,
    FrameworkId     INT             NOT NULL,
    PRIMARY KEY (Id),
    KEY idx_me_framework (FrameworkId),
    CONSTRAINT fk_me_framework
        FOREIGN KEY (FrameworkId) REFERENCES frameworks(FrameworkId) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -----------------------------------------------------------------------------
-- 1.2  NEW TABLE: user_entity_mapping
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_entity_mapping (
    id              INT            NOT NULL AUTO_INCREMENT,
    role            VARCHAR(100)   NOT NULL,
    access_level    VARCHAR(20)    NOT NULL DEFAULT 'read',
    assigned_at     DATETIME(6)    NOT NULL,
    status          VARCHAR(20)    NOT NULL DEFAULT 'active',
    is_deleted      TINYINT(1)     NOT NULL DEFAULT 0,
    created_at      DATETIME(6)    NOT NULL,
    updated_at      DATETIME(6)    NOT NULL,
    UserId          INT            NOT NULL,
    EntityId        INT            NOT NULL,
    TenantId        INT            NOT NULL,
    AssignedById    INT            DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_user_entity (UserId, EntityId),
    CONSTRAINT fk_uem_user
        FOREIGN KEY (UserId)       REFERENCES users(UserId)        ON DELETE CASCADE,
    CONSTRAINT fk_uem_entity
        FOREIGN KEY (EntityId)     REFERENCES mainentities(Id)     ON DELETE CASCADE,
    CONSTRAINT fk_uem_tenant
        FOREIGN KEY (TenantId)     REFERENCES tenants(TenantId)    ON DELETE CASCADE,
    CONSTRAINT fk_uem_assigned_by
        FOREIGN KEY (AssignedById) REFERENCES users(UserId)        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -----------------------------------------------------------------------------
-- 1.2  NEW TABLE: tenant_modules
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_modules (
    id                  INT            NOT NULL AUTO_INCREMENT,
    module_code         VARCHAR(50)    NOT NULL,
    is_enabled          TINYINT(1)     NOT NULL DEFAULT 1,
    license_tier        VARCHAR(50)    NOT NULL DEFAULT 'basic',
    effective_from      DATE           DEFAULT NULL,
    effective_to        DATE           DEFAULT NULL,
    user_limit          INT            DEFAULT NULL,
    storage_limit_gb    INT            DEFAULT NULL,
    api_limit           INT            DEFAULT NULL,
    ai_limit            INT            DEFAULT NULL,
    configured_at       DATETIME(6)    NOT NULL,
    created_at          DATETIME(6)    NOT NULL,
    updated_at          DATETIME(6)    NOT NULL,
    TenantId            INT            NOT NULL,
    ConfiguredById      INT            DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_tenant_module (TenantId, module_code),
    CONSTRAINT fk_tm_tenant
        FOREIGN KEY (TenantId)       REFERENCES tenants(TenantId) ON DELETE CASCADE,
    CONSTRAINT fk_tm_configured_by
        FOREIGN KEY (ConfiguredById) REFERENCES users(UserId)     ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -----------------------------------------------------------------------------
-- 1.2  NEW TABLE: tenant_security_settings
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_security_settings (
    id                          INT            NOT NULL AUTO_INCREMENT,
    mfa_required                TINYINT(1)     NOT NULL DEFAULT 0,
    mfa_methods                 JSON           NOT NULL,
    sso_enabled                 TINYINT(1)     NOT NULL DEFAULT 0,
    sso_provider                VARCHAR(50)    DEFAULT NULL,
    sso_config                  JSON           NOT NULL,
    allowed_email_domains       JSON           NOT NULL,
    ip_restriction_enabled      TINYINT(1)     NOT NULL DEFAULT 0,
    allowed_ip_ranges           JSON           NOT NULL,
    session_timeout_minutes     INT            NOT NULL DEFAULT 30,
    password_expiry_days        INT            NOT NULL DEFAULT 90,
    export_allowed              TINYINT(1)     NOT NULL DEFAULT 1,
    export_requires_approval    TINYINT(1)     NOT NULL DEFAULT 0,
    updated_at                  DATETIME(6)    NOT NULL,
    TenantId                    INT            NOT NULL,
    UpdatedById                 INT            DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_security_tenant (TenantId),
    CONSTRAINT fk_tss_tenant
        FOREIGN KEY (TenantId)    REFERENCES tenants(TenantId) ON DELETE CASCADE,
    CONSTRAINT fk_tss_updated_by
        FOREIGN KEY (UpdatedById) REFERENCES users(UserId)     ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -----------------------------------------------------------------------------
-- 1.2  NEW TABLE: tenant_branding
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_branding (
    id                      INT            NOT NULL AUTO_INCREMENT,
    logo_url                VARCHAR(500)   DEFAULT NULL,
    favicon_url             VARCHAR(500)   DEFAULT NULL,
    primary_color           VARCHAR(7)     NOT NULL DEFAULT '#1976D2',
    secondary_color         VARCHAR(7)     NOT NULL DEFAULT '#424242',
    accent_color            VARCHAR(7)     NOT NULL DEFAULT '#82B1FF',
    custom_css              LONGTEXT,
    login_page_custom_html  LONGTEXT,
    email_template_logo     VARCHAR(500)   DEFAULT NULL,
    email_footer_text       LONGTEXT,
    updated_at              DATETIME(6)    NOT NULL,
    TenantId                INT            NOT NULL,
    UpdatedById             INT            DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_branding_tenant (TenantId),
    CONSTRAINT fk_tb_tenant
        FOREIGN KEY (TenantId)    REFERENCES tenants(TenantId) ON DELETE CASCADE,
    CONSTRAINT fk_tb_updated_by
        FOREIGN KEY (UpdatedById) REFERENCES users(UserId)     ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -----------------------------------------------------------------------------
-- 1.2  NEW TABLE: tenant_audit_log
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_audit_log (
    id              INT            NOT NULL AUTO_INCREMENT,
    action_type     VARCHAR(50)    NOT NULL,
    entity_type     VARCHAR(50)    NOT NULL,
    entity_id       INT            NOT NULL,
    entity_name     VARCHAR(255)   NOT NULL,
    old_value       JSON           DEFAULT NULL,
    new_value       JSON           DEFAULT NULL,
    performed_at    DATETIME(6)    NOT NULL,
    ip_address      VARCHAR(45)    DEFAULT NULL,
    user_agent      LONGTEXT,
    TenantId        INT            NOT NULL,
    PerformedById   INT            DEFAULT NULL,
    PRIMARY KEY (id),
    KEY idx_tal_tenant    (TenantId),
    KEY idx_tal_performer (PerformedById),
    CONSTRAINT fk_tal_tenant
        FOREIGN KEY (TenantId)      REFERENCES tenants(TenantId) ON DELETE CASCADE,
    CONSTRAINT fk_tal_performed_by
        FOREIGN KEY (PerformedById) REFERENCES users(UserId)     ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -----------------------------------------------------------------------------
-- 1.2  NEW TABLE: support_access_request
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS support_access_request (
    id              INT            NOT NULL AUTO_INCREMENT,
    request_reason  LONGTEXT       NOT NULL,
    requested_at    DATETIME(6)    NOT NULL,
    approved_at     DATETIME(6)    DEFAULT NULL,
    valid_from      DATETIME(6)    DEFAULT NULL,
    valid_to        DATETIME(6)    DEFAULT NULL,
    status          VARCHAR(20)    NOT NULL DEFAULT 'pending',
    access_token    VARCHAR(255)   DEFAULT NULL UNIQUE,
    last_used_at    DATETIME(6)    DEFAULT NULL,
    is_active       TINYINT(1)     NOT NULL DEFAULT 1,
    created_at      DATETIME(6)    NOT NULL,
    updated_at      DATETIME(6)    NOT NULL,
    TenantId        INT            NOT NULL,
    SupportUserId   INT            NOT NULL,
    ApprovedById    INT            DEFAULT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_sar_tenant
        FOREIGN KEY (TenantId)      REFERENCES tenants(TenantId) ON DELETE CASCADE,
    CONSTRAINT fk_sar_support_user
        FOREIGN KEY (SupportUserId) REFERENCES users(UserId)     ON DELETE CASCADE,
    CONSTRAINT fk_sar_approved_by
        FOREIGN KEY (ApprovedById)  REFERENCES users(UserId)     ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -----------------------------------------------------------------------------
-- 1.4  DATA: Populate tenant_modules for all existing tenants
-- (uses INSERT IGNORE - safe to re-run if rows already exist)
-- -----------------------------------------------------------------------------
INSERT IGNORE INTO tenant_modules
    (module_code, is_enabled, license_tier, configured_at, created_at, updated_at, TenantId)
SELECT
    m.module_code, 1, 'enterprise', NOW(), NOW(), NOW(), t.TenantId
FROM tenants t
CROSS JOIN (
    SELECT 'framework'  AS module_code UNION ALL
    SELECT 'policy'                    UNION ALL
    SELECT 'compliance'                UNION ALL
    SELECT 'audit'                     UNION ALL
    SELECT 'risk'                      UNION ALL
    SELECT 'incident'                  UNION ALL
    SELECT 'event'
) m;


-- -----------------------------------------------------------------------------
-- 1.4  DATA: Populate tenant_security_settings for all existing tenants
-- (uses INSERT IGNORE - safe to re-run if rows already exist)
-- -----------------------------------------------------------------------------
INSERT IGNORE INTO tenant_security_settings
    (mfa_required, mfa_methods, sso_enabled, sso_config,
     allowed_email_domains, ip_restriction_enabled, allowed_ip_ranges,
     session_timeout_minutes, password_expiry_days,
     export_allowed, export_requires_approval, updated_at, TenantId)
SELECT
    0, '[]', 0, '{}', '[]', 0, '[]', 30, 90, 1, 0, NOW(), TenantId
FROM tenants;

USE grc_test;

CREATE TABLE IF NOT EXISTS framework_tenant_mapping (
    id           INT         NOT NULL AUTO_INCREMENT PRIMARY KEY,
    FrameworkId  INT         NOT NULL,
    TenantId     INT         NOT NULL,
    is_active    TINYINT(1)  NOT NULL DEFAULT 1,
    created_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_framework_tenant (FrameworkId, TenantId),
    CONSTRAINT ftm_framework_fk FOREIGN KEY (FrameworkId) REFERENCES frameworks (FrameworkId) ON DELETE CASCADE,
    CONSTRAINT ftm_tenant_fk    FOREIGN KEY (TenantId)    REFERENCES tenants    (TenantId)    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO framework_tenant_mapping (FrameworkId, TenantId, is_active)
SELECT FrameworkId, TenantId, 1
FROM frameworks
WHERE TenantId IS NOT NULL;

INSERT IGNORE INTO framework_tenant_mapping (FrameworkId, TenantId, is_active)
SELECT f.FrameworkId, t.TenantId, 1
FROM frameworks f
JOIN tenants t ON t.Status = 'active'
WHERE f.TenantId IS NULL;



SELECT t.Name AS tenant, f.FrameworkName, m.is_active
FROM framework_tenant_mapping m
JOIN frameworks f ON f.FrameworkId = m.FrameworkId
JOIN tenants    t ON t.TenantId    = m.TenantId
ORDER BY t.Name, f.FrameworkName;

