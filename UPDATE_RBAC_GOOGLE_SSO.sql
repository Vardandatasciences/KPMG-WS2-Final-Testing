-- ============================================================================
-- SQL Queries to Update RBAC Tables for Google SSO Users
-- ============================================================================
-- Use these queries to manually update RBAC permissions for users who logged in via Google SSO
-- ============================================================================

-- ============================================================================
-- STEP 1: GRC RBAC TABLE - Update View Permissions
-- ============================================================================

-- Update existing GRC RBAC entries (for users who already have RBAC entries)
UPDATE rbac
SET 
    ViewAllCompliance = 1,
    ViewAllPolicy = 1,
    ViewAuditReports = 1,
    ViewAllRisk = 1,
    ViewAllIncident = 1,
    ViewAllEvents = 1,
    UpdatedAt = NOW()
WHERE 
    UserId IN (
        -- Replace with actual User IDs, for example:
        -- 1, 2, 3
        -- Or use a subquery to find Google SSO users:
        SELECT UserId FROM users WHERE Email LIKE '%@gmail.com'
    )
    AND IsActive = 'Y';

-- Insert new GRC RBAC entries (for users who don't have any RBAC entry)
-- Note: Replace <FrameworkId> with an actual Framework ID from your database
INSERT INTO rbac (
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
    (SELECT FrameworkId FROM framework LIMIT 1) AS FrameworkId,  -- Use first available framework
    'Y' AS IsActive,
    1 AS ViewAllCompliance,
    1 AS ViewAllPolicy,
    1 AS ViewAuditReports,
    1 AS ViewAllRisk,
    1 AS ViewAllIncident,
    1 AS ViewAllEvents,
    NOW() AS CreatedAt,
    NOW() AS UpdatedAt
FROM users u
WHERE 
    u.UserId NOT IN (SELECT DISTINCT UserId FROM rbac WHERE IsActive = 'Y')
    AND u.IsActive = 'Y'
    -- Uncomment to filter for Google SSO users only:
    -- AND (u.Email LIKE '%@gmail.com' OR u.Email LIKE '%@googlemail.com');

-- ============================================================================
-- STEP 2: TPRM RBAC TABLE - Update View Permissions
-- ============================================================================

-- Update existing TPRM RBAC entries
UPDATE rbac_tprm
SET 
    ViewRFP = 1,
    ViewRFPResponses = 1,
    ViewRFPApprovalStatus = 1,
    ViewRFPVersions = 1,
    ViewRFPVersion = 1,
    ViewRFPResponseScores = 1,
    ViewRFPAnalytics = 1,
    ViewRFPAuditTrail = 1,
    ViewVendors = 1,
    ViewContactsDocuments = 1,
    ViewRiskProfile = 1,
    ViewLifecycleHistory = 1,
    ViewQuestionnaires = 1,
    ViewRiskAssessments = 1,
    ViewScreeningResults = 1,
    ViewVendorContracts = 1,
    ViewAvailableVendors = 1,
    ViewVendorRiskScores = 1,
    ViewIdentifiedRisks = 1,
    ViewRiskMitigationStatus = 1,
    ViewComplianceStatusOfPlans = 1,
    ViewDocumentAccessLogs = 1,
    ViewAuditLogs = 1,
    ViewComplianceAuditResults = 1,
    ViewIncidentResponsePlans = 1,
    ViewSLA = 1,
    ViewPerformance = 1,
    ViewAlerts = 1,
    ViewDashboardTrend = 1,
    ViewPlansAndDocuments = 1,
    ViewBCPDRPPlanStatus = 1,
    ViewVendorSubmittedDocuments = 1,
    ViewDocumentStatusHistory = 1,
    ListContracts = 1,
    ListContractTerms = 1,
    ListContractRenewals = 1,
    UpdatedAt = NOW()
WHERE 
    UserId IN (
        -- Replace with actual User IDs, for example:
        -- 1, 2, 3
        -- Or use a subquery to find Google SSO users:
        SELECT UserId FROM users WHERE Email LIKE '%@gmail.com'
    )
    AND IsActive = 'Y';

-- Insert new TPRM RBAC entries (for users who don't have any TPRM RBAC entry)
INSERT INTO rbac_tprm (
    UserId,
    UserName,
    Role,
    IsActive,
    ViewRFP,
    ViewRFPResponses,
    ViewRFPApprovalStatus,
    ViewRFPVersions,
    ViewRFPVersion,
    ViewRFPResponseScores,
    ViewRFPAnalytics,
    ViewRFPAuditTrail,
    ViewVendors,
    ViewContactsDocuments,
    ViewRiskProfile,
    ViewLifecycleHistory,
    ViewQuestionnaires,
    ViewRiskAssessments,
    ViewScreeningResults,
    ViewVendorContracts,
    ViewAvailableVendors,
    ViewVendorRiskScores,
    ViewIdentifiedRisks,
    ViewRiskMitigationStatus,
    ViewComplianceStatusOfPlans,
    ViewDocumentAccessLogs,
    ViewAuditLogs,
    ViewComplianceAuditResults,
    ViewIncidentResponsePlans,
    ViewSLA,
    ViewPerformance,
    ViewAlerts,
    ViewDashboardTrend,
    ViewPlansAndDocuments,
    ViewBCPDRPPlanStatus,
    ViewVendorSubmittedDocuments,
    ViewDocumentStatusHistory,
    ListContracts,
    ListContractTerms,
    ListContractRenewals,
    CreatedAt,
    UpdatedAt
)
SELECT 
    u.UserId,
    u.UserName,
    'End User' AS Role,
    'Y' AS IsActive,
    1 AS ViewRFP,
    1 AS ViewRFPResponses,
    1 AS ViewRFPApprovalStatus,
    1 AS ViewRFPVersions,
    1 AS ViewRFPVersion,
    1 AS ViewRFPResponseScores,
    1 AS ViewRFPAnalytics,
    1 AS ViewRFPAuditTrail,
    1 AS ViewVendors,
    1 AS ViewContactsDocuments,
    1 AS ViewRiskProfile,
    1 AS ViewLifecycleHistory,
    1 AS ViewQuestionnaires,
    1 AS ViewRiskAssessments,
    1 AS ViewScreeningResults,
    1 AS ViewVendorContracts,
    1 AS ViewAvailableVendors,
    1 AS ViewVendorRiskScores,
    1 AS ViewIdentifiedRisks,
    1 AS ViewRiskMitigationStatus,
    1 AS ViewComplianceStatusOfPlans,
    1 AS ViewDocumentAccessLogs,
    1 AS ViewAuditLogs,
    1 AS ViewComplianceAuditResults,
    1 AS ViewIncidentResponsePlans,
    1 AS ViewSLA,
    1 AS ViewPerformance,
    1 AS ViewAlerts,
    1 AS ViewDashboardTrend,
    1 AS ViewPlansAndDocuments,
    1 AS ViewBCPDRPPlanStatus,
    1 AS ViewVendorSubmittedDocuments,
    1 AS ViewDocumentStatusHistory,
    1 AS ListContracts,
    1 AS ListContractTerms,
    1 AS ListContractRenewals,
    NOW() AS CreatedAt,
    NOW() AS UpdatedAt
FROM users u
WHERE 
    u.UserId NOT IN (SELECT DISTINCT UserId FROM rbac_tprm WHERE IsActive = 'Y')
    AND u.IsActive = 'Y'
    -- Uncomment to filter for Google SSO users only:
    -- AND (u.Email LIKE '%@gmail.com' OR u.Email LIKE '%@googlemail.com');

-- ============================================================================
-- QUICK UPDATE FOR A SPECIFIC USER (Replace <USER_ID> with actual ID)
-- ============================================================================

-- GRC RBAC Update for specific user
UPDATE rbac
SET 
    ViewAllCompliance = 1,
    ViewAllPolicy = 1,
    ViewAuditReports = 1,
    ViewAllRisk = 1,
    ViewAllIncident = 1,
    ViewAllEvents = 1,
    UpdatedAt = NOW()
WHERE UserId = <USER_ID> AND IsActive = 'Y';

-- TPRM RBAC Update for specific user
UPDATE rbac_tprm
SET 
    ViewRFP = 1,
    ViewRFPResponses = 1,
    ViewRFPApprovalStatus = 1,
    ViewRFPVersions = 1,
    ViewRFPVersion = 1,
    ViewRFPResponseScores = 1,
    ViewRFPAnalytics = 1,
    ViewRFPAuditTrail = 1,
    ViewVendors = 1,
    ViewContactsDocuments = 1,
    ViewRiskProfile = 1,
    ViewLifecycleHistory = 1,
    ViewQuestionnaires = 1,
    ViewRiskAssessments = 1,
    ViewScreeningResults = 1,
    ViewVendorContracts = 1,
    ViewAvailableVendors = 1,
    ViewVendorRiskScores = 1,
    ViewIdentifiedRisks = 1,
    ViewRiskMitigationStatus = 1,
    ViewComplianceStatusOfPlans = 1,
    ViewDocumentAccessLogs = 1,
    ViewAuditLogs = 1,
    ViewComplianceAuditResults = 1,
    ViewIncidentResponsePlans = 1,
    ViewSLA = 1,
    ViewPerformance = 1,
    ViewAlerts = 1,
    ViewDashboardTrend = 1,
    ViewPlansAndDocuments = 1,
    ViewBCPDRPPlanStatus = 1,
    ViewVendorSubmittedDocuments = 1,
    ViewDocumentStatusHistory = 1,
    ListContracts = 1,
    ListContractTerms = 1,
    ListContractRenewals = 1,
    UpdatedAt = NOW()
WHERE UserId = <USER_ID> AND IsActive = 'Y';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check which users have RBAC entries
SELECT 
    u.UserId,
    u.UserName,
    u.Email,
    CASE WHEN r.rbac_id IS NOT NULL THEN 'Yes' ELSE 'No' END AS HasGRCRBAC,
    CASE WHEN t.rbac_id IS NOT NULL THEN 'Yes' ELSE 'No' END AS HasTPRMRBAC
FROM users u
LEFT JOIN rbac r ON u.UserId = r.UserId AND r.IsActive = 'Y'
LEFT JOIN rbac_tprm t ON u.UserId = t.UserId AND t.IsActive = 'Y'
WHERE u.IsActive = 'Y'
ORDER BY u.UserId;

-- Verify GRC RBAC view permissions for a specific user
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
FROM rbac r
WHERE r.UserId = <USER_ID> AND r.IsActive = 'Y';

-- Verify TPRM RBAC view permissions for a specific user
SELECT 
    t.rbac_id,
    t.UserId,
    t.UserName,
    t.Role,
    t.ViewRFP,
    t.ViewVendors,
    t.ViewVendorContracts,
    t.ViewSLA,
    t.ViewPerformance,
    t.ViewAlerts
FROM rbac_tprm t
WHERE t.UserId = <USER_ID> AND t.IsActive = 'Y';

