-- ============================================================================
-- INDIVIDUAL SQL INSERT QUERIES FOR GRC AND TPRM RBAC TABLES
-- ============================================================================
-- Replace <USER_ID>, <USER_NAME>, and <FRAMEWORK_ID> with actual values
-- ============================================================================

-- ============================================================================
-- GRC RBAC TABLE - Individual INSERT Query
-- ============================================================================

INSERT INTO rbac (
    UserId,
    UserName,
    Role,
    FrameworkId,
    IsActive,
    -- Compliance Module View Permissions
    ViewAllCompliance,
    -- Policy Module View Permissions
    ViewAllPolicy,
    -- Audit Module View Permissions
    ViewAuditReports,
    -- Risk Module View Permissions
    ViewAllRisk,
    -- Incident Module View Permissions
    ViewAllIncident,
    -- Event Module View Permissions
    ViewAllEvents,
    CreatedAt,
    UpdatedAt
)
VALUES (
    <USER_ID>,                          -- Replace with actual User ID
    '<USER_NAME>',                      -- Replace with actual User Name (e.g., 'john.doe')
    'End User',                         -- Default role for Google SSO users
    <FRAMEWORK_ID>,                     -- Replace with actual Framework ID (get from: SELECT FrameworkId FROM framework LIMIT 1)
    'Y',                                -- IsActive
    1,                                  -- ViewAllCompliance = True
    1,                                  -- ViewAllPolicy = True
    1,                                  -- ViewAuditReports = True
    1,                                  -- ViewAllRisk = True
    1,                                  -- ViewAllIncident = True
    1,                                  -- ViewAllEvents = True
    NOW(),                             -- CreatedAt
    NOW()                               -- UpdatedAt
);

-- ============================================================================
-- TPRM RBAC TABLE - Individual INSERT Query
-- ============================================================================

INSERT INTO rbac_tprm (
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
VALUES (
    <USER_ID>,                          -- Replace with actual User ID
    '<USER_NAME>',                      -- Replace with actual User Name (e.g., 'john.doe')
    'End User',                         -- Default role for Google SSO users
    'Y',                                -- IsActive
    -- RFP View Permissions
    1,                                  -- ViewRFP = True
    1,                                  -- ViewRFPResponses = True
    1,                                  -- ViewRFPApprovalStatus = True
    1,                                  -- ViewRFPVersions = True
    1,                                  -- ViewRFPVersion = True
    1,                                  -- ViewRFPResponseScores = True
    1,                                  -- ViewRFPAnalytics = True
    1,                                  -- ViewRFPAuditTrail = True
    -- Vendor View Permissions
    1,                                  -- ViewVendors = True
    1,                                  -- ViewAvailableVendors = True
    1,                                  -- ViewContactsDocuments = True
    -- Risk View Permissions
    1,                                  -- ViewRiskProfile = True
    1,                                  -- ViewLifecycleHistory = True
    1,                                  -- ViewQuestionnaires = True
    1,                                  -- ViewRiskAssessments = True
    1,                                  -- ViewScreeningResults = True
    1,                                  -- ViewVendorRiskScores = True
    1,                                  -- ViewIdentifiedRisks = True
    1,                                  -- ViewRiskMitigationStatus = True
    -- Contract View Permissions
    1,                                  -- ViewVendorContracts = True
    1,                                  -- ListContracts = True
    1,                                  -- ListContractTerms = True
    1,                                  -- ListContractRenewals = True
    -- Compliance View Permissions
    1,                                  -- ViewComplianceStatusOfPlans = True
    1,                                  -- ViewDocumentAccessLogs = True
    1,                                  -- ViewAuditLogs = True
    1,                                  -- ViewComplianceAuditResults = True
    -- Incident Response View Permissions
    1,                                  -- ViewIncidentResponsePlans = True
    -- SLA/Performance View Permissions
    1,                                  -- ViewSLA = True
    1,                                  -- ViewPerformance = True
    1,                                  -- ViewAlerts = True
    1,                                  -- ViewDashboardTrend = True
    -- BCP/DRP View Permissions
    1,                                  -- ViewPlansAndDocuments = True
    1,                                  -- ViewBCPDRPPlanStatus = True
    1,                                  -- ViewVendorSubmittedDocuments = True
    1,                                  -- ViewDocumentStatusHistory = True
    NOW(),                             -- CreatedAt
    NOW()                               -- UpdatedAt
);

-- ============================================================================
-- EXAMPLE: How to use these queries
-- ============================================================================

-- Step 1: Get the User ID and Framework ID
-- SELECT UserId, UserName FROM users WHERE Email = 'user@example.com';
-- SELECT FrameworkId FROM framework LIMIT 1;

-- Step 2: Replace the placeholders in the queries above:
-- <USER_ID> → Replace with actual User ID (e.g., 123)
-- <USER_NAME> → Replace with actual User Name (e.g., 'john.doe')
-- <FRAMEWORK_ID> → Replace with actual Framework ID (e.g., 1)

-- Step 3: Execute the GRC RBAC INSERT query
-- Step 4: Execute the TPRM RBAC INSERT query

-- ============================================================================
-- EXAMPLE WITH ACTUAL VALUES (Replace with your values)
-- ============================================================================

-- GRC RBAC Example:
/*
INSERT INTO rbac (
    UserId, UserName, Role, FrameworkId, IsActive,
    ViewAllCompliance, ViewAllPolicy, ViewAuditReports,
    ViewAllRisk, ViewAllIncident, ViewAllEvents,
    CreatedAt, UpdatedAt
)
VALUES (
    123,                    -- User ID
    'john.doe',            -- User Name
    'End User',            -- Role
    1,                     -- Framework ID
    'Y',                   -- IsActive
    1, 1, 1, 1, 1, 1,      -- All view permissions = True
    NOW(), NOW()
);
*/

-- TPRM RBAC Example:
/*
INSERT INTO rbac_tprm (
    UserId, UserName, Role, IsActive,
    ViewRFP, ViewRFPResponses, ViewRFPApprovalStatus, ViewRFPVersions,
    ViewRFPVersion, ViewRFPResponseScores, ViewRFPAnalytics, ViewRFPAuditTrail,
    ViewVendors, ViewAvailableVendors, ViewContactsDocuments,
    ViewRiskProfile, ViewLifecycleHistory, ViewQuestionnaires, ViewRiskAssessments,
    ViewScreeningResults, ViewVendorRiskScores, ViewIdentifiedRisks,
    ViewRiskMitigationStatus, ViewVendorContracts, ListContracts,
    ListContractTerms, ListContractRenewals, ViewComplianceStatusOfPlans,
    ViewDocumentAccessLogs, ViewAuditLogs, ViewComplianceAuditResults,
    ViewIncidentResponsePlans, ViewSLA, ViewPerformance, ViewAlerts,
    ViewDashboardTrend, ViewPlansAndDocuments, ViewBCPDRPPlanStatus,
    ViewVendorSubmittedDocuments, ViewDocumentStatusHistory,
    CreatedAt, UpdatedAt
)
VALUES (
    123,                    -- User ID
    'john.doe',            -- User Name
    'End User',            -- Role
    'Y',                   -- IsActive
    1, 1, 1, 1, 1, 1, 1, 1,  -- RFP permissions
    1, 1, 1,               -- Vendor permissions
    1, 1, 1, 1, 1, 1, 1, 1, -- Risk permissions
    1, 1, 1, 1,            -- Contract permissions
    1, 1, 1, 1,            -- Compliance permissions
    1,                      -- Incident permissions
    1, 1, 1, 1,            -- SLA/Performance permissions
    1, 1, 1, 1,            -- BCP/DRP permissions
    NOW(), NOW()
);
*/

