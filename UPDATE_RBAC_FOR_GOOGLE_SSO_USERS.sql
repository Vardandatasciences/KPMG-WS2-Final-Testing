-- ============================================================================
-- SQL Queries to Update RBAC Tables for Google SSO Users
-- ============================================================================
-- This script updates both GRC and TPRM RBAC tables to assign view permissions
-- to users who have logged in via Google SSO
-- ============================================================================

-- ============================================================================
-- GRC RBAC TABLE UPDATES
-- ============================================================================

-- Option 1: Update existing RBAC entries to add view permissions
-- This updates users who already have RBAC entries
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
        -- Add user IDs here, or use a condition to identify Google SSO users
        -- Example: SELECT UserId FROM users WHERE Email LIKE '%@gmail.com'
    )
    AND (
        ViewAllCompliance = 0 OR
        ViewAllPolicy = 0 OR
        ViewAuditReports = 0 OR
        ViewAllRisk = 0 OR
        ViewAllIncident = 0 OR
        ViewAllEvents = 0
    );

-- Option 2: Insert new RBAC entries for users who don't have any RBAC entry
-- Replace <UserId>, <UserName>, and <FrameworkId> with actual values
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
    u.FrameworkId,
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
    u.UserId NOT IN (SELECT DISTINCT UserId FROM rbac)
    -- Add condition to identify Google SSO users if needed
    -- Example: AND u.Email LIKE '%@gmail.com'
    AND u.IsActive = 'Y';

-- Option 3: Update ALL users to have view permissions (use with caution)
UPDATE rbac
SET 
    ViewAllCompliance = 1,
    ViewAllPolicy = 1,
    ViewAuditReports = 1,
    ViewAllRisk = 1,
    ViewAllIncident = 1,
    ViewAllEvents = 1,
    UpdatedAt = NOW()
WHERE IsActive = 'Y';

-- ============================================================================
-- TPRM RBAC TABLE UPDATES
-- ============================================================================

-- Option 1: Update existing TPRM RBAC entries to add view permissions
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
        -- Add user IDs here, or use a condition to identify Google SSO users
    )
    AND IsActive = 'Y';

-- Option 2: Insert new TPRM RBAC entries for users who don't have any entry
-- Note: This assumes users table exists in TPRM database or you can join from GRC database
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
    u.UserId NOT IN (SELECT DISTINCT UserId FROM rbac_tprm)
    AND u.IsActive = 'Y';

-- ============================================================================
-- QUERIES TO IDENTIFY GOOGLE SSO USERS
-- ============================================================================

-- Find users who might be Google SSO users (by email domain)
SELECT 
    UserId,
    UserName,
    Email,
    FirstName,
    LastName,
    IsActive
FROM users
WHERE 
    Email LIKE '%@gmail.com'
    OR Email LIKE '%@googlemail.com'
ORDER BY UserId;

-- Check which users have RBAC entries
SELECT 
    u.UserId,
    u.UserName,
    u.Email,
    CASE WHEN r.rbac_id IS NOT NULL THEN 'Yes' ELSE 'No' END AS HasGRCRBAC,
    CASE WHEN t.rbac_id IS NOT NULL THEN 'Yes' ELSE 'No' END AS HasTPRMRBAC
FROM users u
LEFT JOIN rbac r ON u.UserId = r.UserId
LEFT JOIN rbac_tprm t ON u.UserId = t.UserId
WHERE u.IsActive = 'Y'
ORDER BY u.UserId;

-- ============================================================================
-- QUERIES TO VERIFY PERMISSIONS
-- ============================================================================

-- Verify GRC RBAC view permissions
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
WHERE r.IsActive = 'Y'
ORDER BY r.UserId;

-- Verify TPRM RBAC view permissions
SELECT 
    t.rbac_id,
    t.UserId,
    t.UserName,
    t.Role,
    t.ViewRFP,
    t.ViewVendors,
    t.ViewContracts,
    t.ViewSLA,
    t.ViewPerformance
FROM rbac_tprm t
WHERE t.IsActive = 'Y'
ORDER BY t.UserId;

-- ============================================================================
-- QUICK UPDATE FOR SPECIFIC USER
-- ============================================================================

-- Replace <USER_ID> with actual user ID

-- GRC RBAC Update
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

-- TPRM RBAC Update
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
-- BULK UPDATE FOR ALL ACTIVE USERS (Use with caution!)
-- ============================================================================

-- GRC: Add view permissions to all active users who don't have them
UPDATE rbac
SET 
    ViewAllCompliance = COALESCE(ViewAllCompliance, 1),
    ViewAllPolicy = COALESCE(ViewAllPolicy, 1),
    ViewAuditReports = COALESCE(ViewAuditReports, 1),
    ViewAllRisk = COALESCE(ViewAllRisk, 1),
    ViewAllIncident = COALESCE(ViewAllIncident, 1),
    ViewAllEvents = COALESCE(ViewAllEvents, 1),
    UpdatedAt = NOW()
WHERE IsActive = 'Y';

-- TPRM: Add view permissions to all active users who don't have them
UPDATE rbac_tprm
SET 
    ViewRFP = COALESCE(ViewRFP, 1),
    ViewRFPResponses = COALESCE(ViewRFPResponses, 1),
    ViewRFPApprovalStatus = COALESCE(ViewRFPApprovalStatus, 1),
    ViewRFPVersions = COALESCE(ViewRFPVersions, 1),
    ViewRFPVersion = COALESCE(ViewRFPVersion, 1),
    ViewRFPResponseScores = COALESCE(ViewRFPResponseScores, 1),
    ViewRFPAnalytics = COALESCE(ViewRFPAnalytics, 1),
    ViewRFPAuditTrail = COALESCE(ViewRFPAuditTrail, 1),
    ViewVendors = COALESCE(ViewVendors, 1),
    ViewContactsDocuments = COALESCE(ViewContactsDocuments, 1),
    ViewRiskProfile = COALESCE(ViewRiskProfile, 1),
    ViewLifecycleHistory = COALESCE(ViewLifecycleHistory, 1),
    ViewQuestionnaires = COALESCE(ViewQuestionnaires, 1),
    ViewRiskAssessments = COALESCE(ViewRiskAssessments, 1),
    ViewScreeningResults = COALESCE(ViewScreeningResults, 1),
    ViewVendorContracts = COALESCE(ViewVendorContracts, 1),
    ViewAvailableVendors = COALESCE(ViewAvailableVendors, 1),
    ViewVendorRiskScores = COALESCE(ViewVendorRiskScores, 1),
    ViewIdentifiedRisks = COALESCE(ViewIdentifiedRisks, 1),
    ViewRiskMitigationStatus = COALESCE(ViewRiskMitigationStatus, 1),
    ViewComplianceStatusOfPlans = COALESCE(ViewComplianceStatusOfPlans, 1),
    ViewDocumentAccessLogs = COALESCE(ViewDocumentAccessLogs, 1),
    ViewAuditLogs = COALESCE(ViewAuditLogs, 1),
    ViewComplianceAuditResults = COALESCE(ViewComplianceAuditResults, 1),
    ViewIncidentResponsePlans = COALESCE(ViewIncidentResponsePlans, 1),
    ViewSLA = COALESCE(ViewSLA, 1),
    ViewPerformance = COALESCE(ViewPerformance, 1),
    ViewAlerts = COALESCE(ViewAlerts, 1),
    ViewDashboardTrend = COALESCE(ViewDashboardTrend, 1),
    ViewPlansAndDocuments = COALESCE(ViewPlansAndDocuments, 1),
    ViewBCPDRPPlanStatus = COALESCE(ViewBCPDRPPlanStatus, 1),
    ViewVendorSubmittedDocuments = COALESCE(ViewVendorSubmittedDocuments, 1),
    ViewDocumentStatusHistory = COALESCE(ViewDocumentStatusHistory, 1),
    ListContracts = COALESCE(ListContracts, 1),
    ListContractTerms = COALESCE(ListContractTerms, 1),
    ListContractRenewals = COALESCE(ListContractRenewals, 1),
    UpdatedAt = NOW()
WHERE IsActive = 'Y';

