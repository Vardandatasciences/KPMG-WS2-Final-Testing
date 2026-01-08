-- ============================================================================
-- Populate TenantId for Existing Records in All Tables
-- ============================================================================
-- This script distributes existing records between Tenant 1 and Tenant 2
-- Run this AFTER TenantId columns have been added to all tables
-- ============================================================================
-- 
-- ASSUMPTION: You have 2 tenants with TenantId = 1 and TenantId = 2
-- ============================================================================

-- Verify tenants exist
SELECT 
    TenantId, 
    Name, 
    Subdomain, 
    Status 
FROM tenants 
WHERE TenantId IN (1, 2)
ORDER BY TenantId;

-- ============================================================================
-- DISTRIBUTION STRATEGY: Alternate between Tenant 1 and Tenant 2
-- ============================================================================
-- Records are distributed using MOD operation:
-- - Even row numbers (0, 2, 4...) -> Tenant 1
-- - Odd row numbers (1, 3, 5...) -> Tenant 2
-- ============================================================================

-- ============================================================================
-- RFP MODULE TABLES
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

-- 3. file_storage
UPDATE file_storage 
SET TenantId = CASE 
    WHEN (id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 4. s3_files
UPDATE s3_files 
SET TenantId = CASE 
    WHEN (id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 5. rfp_evaluation_scores
UPDATE rfp_evaluation_scores 
SET TenantId = CASE 
    WHEN (score_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 6. rfp_evaluator_assignments
UPDATE rfp_evaluator_assignments 
SET TenantId = CASE 
    WHEN (assignment_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 7. rfp_committee
UPDATE rfp_committee 
SET TenantId = CASE 
    WHEN (committee_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 8. rfp_final_evaluation
UPDATE rfp_final_evaluation 
SET TenantId = CASE 
    WHEN (evaluation_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 9. rfp_versions
UPDATE rfp_versions 
SET TenantId = CASE 
    WHEN (CAST(SUBSTRING(version_id, -1) AS UNSIGNED) % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 10. rfp_change_requests
UPDATE rfp_change_requests 
SET TenantId = CASE 
    WHEN (change_request_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 11. rfp_version_comparisons
UPDATE rfp_version_comparisons 
SET TenantId = CASE 
    WHEN (comparison_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 12. rfp_unmatched_vendors
UPDATE rfp_unmatched_vendors 
SET TenantId = CASE 
    WHEN (unmatched_vendor_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 13. rfp_vendor_invitations
UPDATE rfp_vendor_invitations 
SET TenantId = CASE 
    WHEN (invitation_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 14. rfp_vendor_selections
UPDATE rfp_vendor_selections 
SET TenantId = CASE 
    WHEN (selection_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 15. rfp_responses
UPDATE rfp_responses 
SET TenantId = CASE 
    WHEN (response_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 16. rfp_award_notifications
UPDATE rfp_award_notifications 
SET TenantId = CASE 
    WHEN (notification_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 17. rfp_type_custom_fields
UPDATE rfp_type_custom_fields 
SET TenantId = CASE 
    WHEN (rfp_type_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- RFP APPROVAL MODULE TABLES
-- ============================================================================

-- 18. approval_workflows
UPDATE approval_workflows 
SET TenantId = CASE 
    WHEN (workflow_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 19. approval_requests
UPDATE approval_requests 
SET TenantId = CASE 
    WHEN (request_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 20. approval_stages
UPDATE approval_stages 
SET TenantId = CASE 
    WHEN (stage_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 21. approval_comments
UPDATE approval_comments 
SET TenantId = CASE 
    WHEN (comment_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 22. approval_request_versions
UPDATE approval_request_versions 
SET TenantId = CASE 
    WHEN (version_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- CONTRACTS MODULE TABLES
-- ============================================================================

-- 23. vendors
UPDATE vendors 
SET TenantId = CASE 
    WHEN (vendor_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 24. vendor_contracts
UPDATE vendor_contracts 
SET TenantId = CASE 
    WHEN (contract_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 25. contract_terms
UPDATE contract_terms 
SET TenantId = CASE 
    WHEN (term_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 26. contract_clauses
UPDATE contract_clauses 
SET TenantId = CASE 
    WHEN (clause_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 27. vendor_contacts
UPDATE vendor_contacts 
SET TenantId = CASE 
    WHEN (contact_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 28. contract_amendments
UPDATE contract_amendments 
SET TenantId = CASE 
    WHEN (amendment_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 29. contract_renewals
UPDATE contract_renewals 
SET TenantId = CASE 
    WHEN (renewal_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 30. contract_approvals
UPDATE contract_approvals 
SET TenantId = CASE 
    WHEN (approval_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- BCP/DRP MODULE TABLES
-- ============================================================================

-- 31. dropdown
UPDATE dropdown 
SET TenantId = CASE 
    WHEN (id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 32. bcp_drp_plans
UPDATE bcp_drp_plans 
SET TenantId = CASE 
    WHEN (plan_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 33. bcp_extracted_details
UPDATE bcp_extracted_details 
SET TenantId = CASE 
    WHEN (detail_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 34. drp_extracted_details
UPDATE drp_extracted_details 
SET TenantId = CASE 
    WHEN (detail_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 35. bcp_drp_evaluations
UPDATE bcp_drp_evaluations 
SET TenantId = CASE 
    WHEN (evaluation_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 36. test_questionnaires
UPDATE test_questionnaires 
SET TenantId = CASE 
    WHEN (questionnaire_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 37. test_questions
UPDATE test_questions 
SET TenantId = CASE 
    WHEN (question_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 38. test_assignments_responses
UPDATE test_assignments_responses 
SET TenantId = CASE 
    WHEN (response_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 39. bcp_drp_approvals
UPDATE bcp_drp_approvals 
SET TenantId = CASE 
    WHEN (approval_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 40. questionnaire_templates
UPDATE questionnaire_templates 
SET TenantId = CASE 
    WHEN (template_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- AUDITS MODULE TABLES
-- ============================================================================

-- 41. audits
UPDATE audits 
SET TenantId = CASE 
    WHEN (audit_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 42. static_questionnaires
UPDATE static_questionnaires 
SET TenantId = CASE 
    WHEN (questionnaire_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 43. audit_versions
UPDATE audit_versions 
SET TenantId = CASE 
    WHEN (version_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 44. audit_findings
UPDATE audit_findings 
SET TenantId = CASE 
    WHEN (finding_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 45. audit_reports
UPDATE audit_reports 
SET TenantId = CASE 
    WHEN (report_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- COMPLIANCE MODULE TABLES
-- ============================================================================

-- 46. compliance_mapping
UPDATE compliance_mapping 
SET TenantId = CASE 
    WHEN (mapping_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- RISK ANALYSIS MODULE TABLES
-- ============================================================================

-- 47. risk_tprm
UPDATE risk_tprm 
SET TenantId = CASE 
    WHEN (risk_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- SLAS MODULE TABLES
-- ============================================================================

-- 48. vendor_slas
UPDATE vendor_slas 
SET TenantId = CASE 
    WHEN (sla_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 49. sla_metrics
UPDATE sla_metrics 
SET TenantId = CASE 
    WHEN (metric_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 50. sla_documents
UPDATE sla_documents 
SET TenantId = CASE 
    WHEN (document_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- VENDOR RISK MODULE TABLES
-- ============================================================================

-- 51. vendor_risk_assessments
UPDATE vendor_risk_assessments 
SET TenantId = CASE 
    WHEN (assessment_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 52. vendor_risk_factors
UPDATE vendor_risk_factors 
SET TenantId = CASE 
    WHEN (factor_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 53. vendor_risk_thresholds
UPDATE vendor_risk_thresholds 
SET TenantId = CASE 
    WHEN (threshold_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 54. vendor_lifecycle_stages
UPDATE vendor_lifecycle_stages 
SET TenantId = CASE 
    WHEN (stage_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify the distribution

-- Summary by table and tenant
SELECT 
    'rfps' AS table_name,
    TenantId,
    COUNT(*) AS record_count
FROM rfps
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
ORDER BY table_name, TenantId;

-- Check for any NULL TenantId values (should be 0 after running this script)
SELECT 
    'rfps' AS table_name,
    COUNT(*) AS null_tenant_count
FROM rfps
WHERE TenantId IS NULL
UNION ALL
SELECT 
    'rfp_evaluation_criteria',
    COUNT(*)
FROM rfp_evaluation_criteria
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
WHERE TenantId IS NULL;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. This script distributes records evenly between Tenant 1 and Tenant 2
-- 2. Distribution is based on primary key MOD 2 operation
-- 3. If you need different distribution logic, modify the CASE statements
-- 4. Run verification queries after execution to confirm distribution
-- 5. If a table doesn't exist or doesn't have TenantId column, that UPDATE will fail silently
-- 6. You can run this script multiple times safely (it only updates NULL values)
-- ============================================================================

