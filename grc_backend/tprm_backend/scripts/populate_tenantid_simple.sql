-- ============================================================================
-- Populate TenantId for Existing Records - SIMPLE VERSION
-- ============================================================================
-- This version only updates tables that are known to exist
-- Run this if the dynamic version has issues
-- ============================================================================

-- Verify tenants exist
SELECT TenantId, Name, Subdomain, Status 
FROM tenants 
WHERE TenantId IN (1, 2)
ORDER BY TenantId;

-- ============================================================================
-- RFP MODULE TABLES (only if they exist)
-- ============================================================================

-- 1. rfps
UPDATE rfps 
SET TenantId = CASE 
    WHEN (rfp_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 2. rfp_evaluation_criteria
UPDATE rfp_evaluation_criteria 
SET TenantId = CASE 
    WHEN (criteria_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 3. s3_files (if exists)
-- UPDATE s3_files 
-- SET TenantId = CASE 
--     WHEN (id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 4. rfp_evaluation_scores
-- UPDATE rfp_evaluation_scores 
-- SET TenantId = CASE 
--     WHEN (score_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 5. rfp_evaluator_assignments
-- UPDATE rfp_evaluator_assignments 
-- SET TenantId = CASE 
--     WHEN (assignment_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 6. rfp_committee
-- UPDATE rfp_committee 
-- SET TenantId = CASE 
--     WHEN (committee_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 7. rfp_final_evaluation
-- UPDATE rfp_final_evaluation 
-- SET TenantId = CASE 
--     WHEN (evaluation_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 8. rfp_versions
-- UPDATE rfp_versions 
-- SET TenantId = CASE 
--     WHEN (CAST(SUBSTRING(version_id, -1) AS UNSIGNED) % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 9. rfp_change_requests
-- UPDATE rfp_change_requests 
-- SET TenantId = CASE 
--     WHEN (change_request_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 10. rfp_version_comparisons
-- UPDATE rfp_version_comparisons 
-- SET TenantId = CASE 
--     WHEN (comparison_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 11. rfp_unmatched_vendors
-- UPDATE rfp_unmatched_vendors 
-- SET TenantId = CASE 
--     WHEN (unmatched_vendor_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 12. rfp_vendor_invitations
-- UPDATE rfp_vendor_invitations 
-- SET TenantId = CASE 
--     WHEN (invitation_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 13. rfp_vendor_selections
-- UPDATE rfp_vendor_selections 
-- SET TenantId = CASE 
--     WHEN (selection_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 14. rfp_responses
-- UPDATE rfp_responses 
-- SET TenantId = CASE 
--     WHEN (response_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 15. rfp_award_notifications
-- UPDATE rfp_award_notifications 
-- SET TenantId = CASE 
--     WHEN (notification_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 16. rfp_type_custom_fields
-- UPDATE rfp_type_custom_fields 
-- SET TenantId = CASE 
--     WHEN (rfp_type_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- ============================================================================
-- CONTRACTS MODULE TABLES
-- ============================================================================

-- 17. vendors
UPDATE vendors 
SET TenantId = CASE 
    WHEN (vendor_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 18. vendor_contracts
UPDATE vendor_contracts 
SET TenantId = CASE 
    WHEN (contract_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 19. contract_terms
-- UPDATE contract_terms 
-- SET TenantId = CASE 
--     WHEN (term_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 20. contract_clauses
-- UPDATE contract_clauses 
-- SET TenantId = CASE 
--     WHEN (clause_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 21. vendor_contacts
-- UPDATE vendor_contacts 
-- SET TenantId = CASE 
--     WHEN (contact_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check distribution
SELECT 
    'rfps' AS table_name,
    TenantId,
    COUNT(*) AS record_count
FROM rfps
WHERE TenantId IN (1, 2)
GROUP BY TenantId
UNION ALL
SELECT 
    'vendors',
    TenantId,
    COUNT(*)
FROM vendors
WHERE TenantId IN (1, 2)
GROUP BY TenantId
UNION ALL
SELECT 
    'vendor_contracts',
    TenantId,
    COUNT(*)
FROM vendor_contracts
WHERE TenantId IN (1, 2)
GROUP BY TenantId
UNION ALL
SELECT 
    'rfp_evaluation_criteria',
    TenantId,
    COUNT(*)
FROM rfp_evaluation_criteria
WHERE TenantId IN (1, 2)
GROUP BY TenantId
ORDER BY table_name, TenantId;

-- Check for NULL values
SELECT 
    'rfps' AS table_name,
    COUNT(*) AS null_count
FROM rfps
WHERE TenantId IS NULL
UNION ALL
SELECT 
    'vendors',
    COUNT(*)
FROM vendors
WHERE TenantId IS NULL
UNION ALL
SELECT 
    'vendor_contracts',
    COUNT(*)
FROM vendor_contracts
WHERE TenantId IS NULL
UNION ALL
SELECT 
    'rfp_evaluation_criteria',
    COUNT(*)
FROM rfp_evaluation_criteria
WHERE TenantId IS NULL;

