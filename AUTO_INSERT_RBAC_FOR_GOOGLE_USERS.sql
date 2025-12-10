-- ============================================================================
-- AUTOMATIC RBAC INSERT QUERIES FOR GOOGLE SSO USERS
-- ============================================================================
-- These queries automatically create RBAC entries for users who logged in via Google SSO
-- They check the users table and create RBAC entries only for users who don't have them yet
-- ============================================================================

-- ============================================================================
-- STEP 1: GRC RBAC - Insert for Google SSO users who don't have RBAC entries
-- ============================================================================

INSERT INTO grc2.rbac (
    UserId,
    UserName,
    Role,
    FrameworkId,
    IsActive,
    ViewAllCompliance,
    ViewAllPolicy,
    ViewAuditReports,
    ViewAllRisk,
    ViewAllIncident,
    ViewAllEvents,
    CreatedAt,
    UpdatedAt
)
SELECT 
    u.UserId,
    u.UserName,
    'End User' AS Role,
    COALESCE(
        (SELECT FrameworkId FROM grc2.framework LIMIT 1),
        u.FrameworkId,
        1
    ) AS FrameworkId,
    'Y' AS IsActive,
    1 AS ViewAllCompliance,      -- View permission only
    1 AS ViewAllPolicy,           -- View permission only
    1 AS ViewAuditReports,        -- View permission only
    1 AS ViewAllRisk,             -- View permission only
    1 AS ViewAllIncident,         -- View permission only
    1 AS ViewAllEvents,           -- View permission only
    NOW() AS CreatedAt,
    NOW() AS UpdatedAt
FROM grc2.users u
WHERE 
    u.IsActive = 'Y'
    -- Identify Google SSO users by email domain
    AND (
        u.Email LIKE '%@gmail.com' 
        OR u.Email LIKE '%@googlemail.com'
        -- Add other indicators if you have them, e.g.:
        -- OR u.Password IS NULL  -- If Google SSO users don't have passwords
        -- OR u.session_token IS NOT NULL  -- If Google SSO users have session tokens
    )
    -- Only insert if user doesn't already have a GRC RBAC entry
    AND u.UserId NOT IN (
        SELECT DISTINCT UserId 
        FROM grc2.rbac 
        WHERE IsActive = 'Y'
    );

-- ============================================================================
-- STEP 2: TPRM RBAC - Insert for Google SSO users who don't have TPRM RBAC entries
-- ============================================================================

INSERT INTO grc2.rbac_tprm (
    UserId,
    UserName,
    Role,
    IsActive,
    -- RFP View Permissions
    ViewRFP,
    ViewRFPResponses,
    ViewRFPApprovalStatus,
    ViewRFPVersions,
    ViewRFPVersion,
    ViewRFPResponseScores,
    ViewRFPAnalytics,
    ViewRFPAuditTrail,
    -- Vendor View Permissions
    ViewVendors,
    ViewAvailableVendors,
    ViewContactsDocuments,
    -- Risk View Permissions
    ViewRiskProfile,
    ViewLifecycleHistory,
    ViewQuestionnaires,
    ViewRiskAssessments,
    ViewScreeningResults,
    ViewVendorRiskScores,
    ViewIdentifiedRisks,
    ViewRiskMitigationStatus,
    -- Contract View Permissions
    ViewVendorContracts,
    ListContracts,
    ListContractTerms,
    ListContractRenewals,
    -- Compliance View Permissions
    ViewComplianceStatusOfPlans,
    ViewDocumentAccessLogs,
    ViewAuditLogs,
    ViewComplianceAuditResults,
    -- Incident Response View Permissions
    ViewIncidentResponsePlans,
    -- SLA/Performance View Permissions
    ViewSLA,
    ViewPerformance,
    ViewAlerts,
    ViewDashboardTrend,
    -- BCP/DRP View Permissions
    ViewPlansAndDocuments,
    ViewBCPDRPPlanStatus,
    ViewVendorSubmittedDocuments,
    ViewDocumentStatusHistory,
    CreatedAt,
    UpdatedAt
)
SELECT 
    u.UserId,
    u.UserName,
    'End User' AS Role,
    'Y' AS IsActive,
    -- RFP View Permissions (all set to 1 = True)
    1 AS ViewRFP,
    1 AS ViewRFPResponses,
    1 AS ViewRFPApprovalStatus,
    1 AS ViewRFPVersions,
    1 AS ViewRFPVersion,
    1 AS ViewRFPResponseScores,
    1 AS ViewRFPAnalytics,
    1 AS ViewRFPAuditTrail,
    -- Vendor View Permissions (all set to 1 = True)
    1 AS ViewVendors,
    1 AS ViewAvailableVendors,
    1 AS ViewContactsDocuments,
    -- Risk View Permissions (all set to 1 = True)
    1 AS ViewRiskProfile,
    1 AS ViewLifecycleHistory,
    1 AS ViewQuestionnaires,
    1 AS ViewRiskAssessments,
    1 AS ViewScreeningResults,
    1 AS ViewVendorRiskScores,
    1 AS ViewIdentifiedRisks,
    1 AS ViewRiskMitigationStatus,
    -- Contract View Permissions (all set to 1 = True)
    1 AS ViewVendorContracts,
    1 AS ListContracts,
    1 AS ListContractTerms,
    1 AS ListContractRenewals,
    -- Compliance View Permissions (all set to 1 = True)
    1 AS ViewComplianceStatusOfPlans,
    1 AS ViewDocumentAccessLogs,
    1 AS ViewAuditLogs,
    1 AS ViewComplianceAuditResults,
    -- Incident Response View Permissions (all set to 1 = True)
    1 AS ViewIncidentResponsePlans,
    -- SLA/Performance View Permissions (all set to 1 = True)
    1 AS ViewSLA,
    1 AS ViewPerformance,
    1 AS ViewAlerts,
    1 AS ViewDashboardTrend,
    -- BCP/DRP View Permissions (all set to 1 = True)
    1 AS ViewPlansAndDocuments,
    1 AS ViewBCPDRPPlanStatus,
    1 AS ViewVendorSubmittedDocuments,
    1 AS ViewDocumentStatusHistory,
    NOW() AS CreatedAt,
    NOW() AS UpdatedAt
FROM grc2.users u
WHERE 
    u.IsActive = 'Y'
    -- Identify Google SSO users by email domain
    AND (
        u.Email LIKE '%@gmail.com' 
        OR u.Email LIKE '%@googlemail.com'
        -- Add other indicators if you have them
    )
    -- Only insert if user doesn't already have a TPRM RBAC entry
    AND u.UserId NOT IN (
        SELECT DISTINCT UserId 
        FROM grc2.rbac_tprm 
        WHERE IsActive = 'Y'
    );

-- ============================================================================
-- ALTERNATIVE: If you want to identify Google SSO users differently
-- ============================================================================

-- Option 1: By password field (if Google SSO users have NULL or empty passwords)
/*
INSERT INTO grc2.rbac (...)
SELECT ...
FROM grc2.users u
WHERE 
    u.IsActive = 'Y'
    AND (u.Password IS NULL OR u.Password = '')
    AND u.UserId NOT IN (SELECT DISTINCT UserId FROM grc2.rbac WHERE IsActive = 'Y');
*/

-- Option 2: By specific users (if you know the UserIds)
/*
INSERT INTO grc2.rbac (...)
SELECT ...
FROM grc2.users u
WHERE 
    u.IsActive = 'Y'
    AND u.UserId IN (50, 51, 52, ...)  -- Replace with actual User IDs
    AND u.UserId NOT IN (SELECT DISTINCT UserId FROM grc2.rbac WHERE IsActive = 'Y');
*/

-- Option 3: All active users (use with caution!)
/*
INSERT INTO grc2.rbac (...)
SELECT ...
FROM grc2.users u
WHERE 
    u.IsActive = 'Y'
    AND u.UserId NOT IN (SELECT DISTINCT UserId FROM grc2.rbac WHERE IsActive = 'Y');
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check which Google SSO users have RBAC entries
SELECT 
    u.UserId,
    u.UserName,
    u.Email,
    CASE WHEN r.rbac_id IS NOT NULL THEN 'Yes' ELSE 'No' END AS HasGRCRBAC,
    CASE WHEN t.rbac_id IS NOT NULL THEN 'Yes' ELSE 'No' END AS HasTPRMRBAC
FROM grc2.users u
LEFT JOIN grc2.rbac r ON u.UserId = r.UserId AND r.IsActive = 'Y'
LEFT JOIN grc2.rbac_tprm t ON u.UserId = t.UserId AND t.IsActive = 'Y'
WHERE 
    u.IsActive = 'Y'
    AND (
        u.Email LIKE '%@gmail.com' 
        OR u.Email LIKE '%@googlemail.com'
    )
ORDER BY u.UserId;

-- Verify GRC RBAC view permissions for Google SSO users
SELECT 
    r.rbac_id,
    r.UserId,
    r.UserName,
    r.Role,
    r.ViewAllCompliance,
    r.ViewAllPolicy,
    r.ViewAuditReports,
    r.ViewAllRisk,
    r.ViewAllIncident,
    r.ViewAllEvents
FROM grc2.rbac r
INNER JOIN grc2.users u ON r.UserId = u.UserId
WHERE 
    r.IsActive = 'Y'
    AND u.IsActive = 'Y'
    AND (
        u.Email LIKE '%@gmail.com' 
        OR u.Email LIKE '%@googlemail.com'
    )
ORDER BY r.UserId;

-- Verify TPRM RBAC view permissions for Google SSO users
SELECT 
    t.rbac_id,
    t.UserId,
    t.UserName,
    t.Role,
    t.ViewRFP,
    t.ViewVendors,
    t.ViewVendorContracts,
    t.ViewSLA,
    t.ViewPerformance
FROM grc2.rbac_tprm t
INNER JOIN grc2.users u ON t.UserId = u.UserId
WHERE 
    t.IsActive = 'Y'
    AND u.IsActive = 'Y'
    AND (
        u.Email LIKE '%@gmail.com' 
        OR u.Email LIKE '%@googlemail.com'
    )
ORDER BY t.UserId;

