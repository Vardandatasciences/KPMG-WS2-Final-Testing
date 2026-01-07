-- ============================================================================
-- Populate TenantId for Existing Records - Individual Table Updates
-- ============================================================================
-- This script has individual UPDATE statements for each table
-- Simply comment out or remove tables that don't exist in your database
-- 
-- IMPORTANT: Before running this script, check which tables have TenantId:
-- Run: check_tables_with_tenantid.sql first
-- Then comment out tables that don't have TenantId column
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

-- 3. s3_files
UPDATE s3_files 
SET TenantId = CASE 
    WHEN (id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 4. rfp_evaluation_scores
UPDATE rfp_evaluation_scores 
SET TenantId = CASE 
    WHEN (score_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 5. rfp_evaluator_assignments
UPDATE rfp_evaluator_assignments 
SET TenantId = CASE 
    WHEN (assignment_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 6. rfp_committee
UPDATE rfp_committee 
SET TenantId = CASE 
    WHEN (committee_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 7. rfp_final_evaluation
UPDATE rfp_final_evaluation 
SET TenantId = CASE 
    WHEN (final_eval_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 8. rfp_versions (VARCHAR PK - use last character)
UPDATE rfp_versions 
SET TenantId = CASE 
    WHEN (CAST(SUBSTRING(version_id, -1) AS UNSIGNED) % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 9. rfp_change_requests (VARCHAR PK - use last character)
UPDATE rfp_change_requests 
SET TenantId = CASE 
    WHEN (CAST(SUBSTRING(change_request_id, -1) AS UNSIGNED) % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 10. rfp_version_comparisons (VARCHAR PK - use last character)
UPDATE rfp_version_comparisons 
SET TenantId = CASE 
    WHEN (CAST(SUBSTRING(comparison_id, -1) AS UNSIGNED) % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 11. rfp_unmatched_vendors
UPDATE rfp_unmatched_vendors 
SET TenantId = CASE 
    WHEN (unmatched_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 12. rfp_vendor_invitations
UPDATE rfp_vendor_invitations 
SET TenantId = CASE 
    WHEN (invitation_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 13. rfp_vendor_selections
UPDATE rfp_vendor_selections 
SET TenantId = CASE 
    WHEN (selection_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 14. rfp_responses
UPDATE rfp_responses 
SET TenantId = CASE 
    WHEN (response_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 15. rfp_award_notifications
UPDATE rfp_award_notifications 
SET TenantId = CASE 
    WHEN (notification_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 16. rfp_type_custom_fields
UPDATE rfp_type_custom_fields 
SET TenantId = CASE 
    WHEN (rfp_type_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- RFP APPROVAL MODULE TABLES
-- ============================================================================

-- 17. approval_workflows (VARCHAR PK - use last character)
UPDATE approval_workflows 
SET TenantId = CASE 
    WHEN (CAST(SUBSTRING(workflow_id, -1) AS UNSIGNED) % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 18. approval_requests (VARCHAR PK - use last character)
UPDATE approval_requests 
SET TenantId = CASE 
    WHEN (CAST(SUBSTRING(approval_id, -1) AS UNSIGNED) % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 19. approval_stages (VARCHAR PK - use last character)
UPDATE approval_stages 
SET TenantId = CASE 
    WHEN (CAST(SUBSTRING(stage_id, -1) AS UNSIGNED) % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 20. approval_comments (VARCHAR PK - use last character)
UPDATE approval_comments 
SET TenantId = CASE 
    WHEN (CAST(SUBSTRING(comment_id, -1) AS UNSIGNED) % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 21. approval_request_versions (VARCHAR PK - use last character)
UPDATE approval_request_versions 
SET TenantId = CASE 
    WHEN (CAST(SUBSTRING(version_id, -1) AS UNSIGNED) % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- CONTRACTS MODULE TABLES
-- ============================================================================

-- 22. vendors
UPDATE vendors 
SET TenantId = CASE 
    WHEN (vendor_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 23. vendor_contracts
UPDATE vendor_contracts 
SET TenantId = CASE 
    WHEN (contract_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 24. contract_terms
UPDATE contract_terms 
SET TenantId = CASE 
    WHEN (term_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 25. contract_clauses
UPDATE contract_clauses 
SET TenantId = CASE 
    WHEN (clause_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 26. vendor_contacts
UPDATE vendor_contacts 
SET TenantId = CASE 
    WHEN (contact_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 27. contract_amendments
UPDATE contract_amendments 
SET TenantId = CASE 
    WHEN (amendment_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 28. contract_renewals
UPDATE contract_renewals 
SET TenantId = CASE 
    WHEN (renewal_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 29. contract_approvals
UPDATE contract_approvals 
SET TenantId = CASE 
    WHEN (approval_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- BCP/DRP MODULE TABLES
-- ============================================================================

-- 30. dropdown (COMMENTED OUT - TenantId column may not exist yet)
-- UPDATE dropdown 
-- SET TenantId = CASE 
--     WHEN (id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 31. bcp_drp_plans
UPDATE bcp_drp_plans 
SET TenantId = CASE 
    WHEN (plan_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 32. bcp_extracted_details
UPDATE bcp_extracted_details 
SET TenantId = CASE 
    WHEN (plan_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 33. drp_extracted_details
UPDATE drp_extracted_details 
SET TenantId = CASE 
    WHEN (plan_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 34. bcp_drp_evaluations
UPDATE bcp_drp_evaluations 
SET TenantId = CASE 
    WHEN (evaluation_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 35. test_questionnaires
UPDATE test_questionnaires 
SET TenantId = CASE 
    WHEN (questionnaire_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 36. test_questions
UPDATE test_questions 
SET TenantId = CASE 
    WHEN (question_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 37. test_assignments_responses
UPDATE test_assignments_responses 
SET TenantId = CASE 
    WHEN (assignment_response_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 38. bcp_drp_approvals
UPDATE bcp_drp_approvals 
SET TenantId = CASE 
    WHEN (approval_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 39. questionnaire_templates
UPDATE questionnaire_templates 
SET TenantId = CASE 
    WHEN (template_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- AUDITS MODULE TABLES
-- ============================================================================

-- 40. audits
UPDATE audits 
SET TenantId = CASE 
    WHEN (audit_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 41. static_questionnaires
UPDATE static_questionnaires 
SET TenantId = CASE 
    WHEN (question_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 42. audit_versions
UPDATE audit_versions 
SET TenantId = CASE 
    WHEN (version_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 43. audit_findings
UPDATE audit_findings 
SET TenantId = CASE 
    WHEN (audit_finding_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 44. audit_reports
UPDATE audit_reports 
SET TenantId = CASE 
    WHEN (report_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- COMPLIANCE MODULE TABLES
-- ============================================================================

-- 45. compliance_mapping
UPDATE compliance_mapping 
SET TenantId = CASE 
    WHEN (mapping_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- RISK ANALYSIS MODULE TABLES
-- ============================================================================

-- 46. risk_tprm (VARCHAR PK - use last character)
UPDATE risk_tprm 
SET TenantId = CASE 
    WHEN (CAST(SUBSTRING(id, -1) AS UNSIGNED) % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- SLAS MODULE TABLES
-- ============================================================================

-- 47. vendor_slas
UPDATE vendor_slas 
SET TenantId = CASE 
    WHEN (sla_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 48. sla_metrics
UPDATE sla_metrics 
SET TenantId = CASE 
    WHEN (metric_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 49. sla_documents
UPDATE sla_documents 
SET TenantId = CASE 
    WHEN (document_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- VENDOR RISK MODULE TABLES
-- ============================================================================

-- 50. vendor_risk_assessments (COMMENTED OUT - table may not exist)
-- UPDATE vendor_risk_assessments 
-- SET TenantId = CASE 
--     WHEN (assessment_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 51. vendor_risk_factors (COMMENTED OUT - table may not exist)
-- UPDATE vendor_risk_factors 
-- SET TenantId = CASE 
--     WHEN (factor_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 52. vendor_risk_thresholds (COMMENTED OUT - table may not exist)
-- UPDATE vendor_risk_thresholds 
-- SET TenantId = CASE 
--     WHEN (threshold_id % 2) = 0 THEN 1 
--     ELSE 2 
-- END
-- WHERE TenantId IS NULL;

-- 53. vendor_lifecycle_stages
UPDATE vendor_lifecycle_stages 
SET TenantId = CASE 
    WHEN (stage_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- ADDITIONAL TABLES THAT NEED TenantId
-- ============================================================================

-- 54. vendor_documents
UPDATE vendor_documents 
SET TenantId = CASE 
    WHEN (document_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 55. vendor_categories
UPDATE vendor_categories 
SET TenantId = CASE 
    WHEN (category_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 56. users
UPDATE users 
SET TenantId = CASE 
    WHEN (UserId % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 57. temp_vendor
UPDATE temp_vendor 
SET TenantId = CASE 
    WHEN (id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 58. sla_approvals
UPDATE sla_approvals 
SET TenantId = CASE 
    WHEN (approval_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 59. search_index
UPDATE search_index 
SET TenantId = CASE 
    WHEN (id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 60. search_analytics
UPDATE search_analytics 
SET TenantId = CASE 
    WHEN (id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 61. contract_audit_findings
UPDATE contract_audit_findings 
SET TenantId = CASE 
    WHEN (audit_finding_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 62. AccessRequestTPRM
UPDATE AccessRequestTPRM 
SET TenantId = CASE 
    WHEN (id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 63. contract_audit_reports
UPDATE contract_audit_reports 
SET TenantId = CASE 
    WHEN (report_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 64. contract_audit_versions
UPDATE contract_audit_versions 
SET TenantId = CASE 
    WHEN (version_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 65. contract_audits
UPDATE contract_audits 
SET TenantId = CASE 
    WHEN (audit_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 66. contract_static_questionnaires
UPDATE contract_static_questionnaires 
SET TenantId = CASE 
    WHEN (question_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 67. frameworks
UPDATE frameworks 
SET TenantId = CASE 
    WHEN (FrameworkId % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 68. questionnaire_assignments
UPDATE questionnaire_assignments 
SET TenantId = CASE 
    WHEN (assignment_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 69. questionnaire_questions
UPDATE questionnaire_questions 
SET TenantId = CASE 
    WHEN (question_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 70. questionnaire_response_submissions
UPDATE questionnaire_response_submissions 
SET TenantId = CASE 
    WHEN (response_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 71. questionnaires
UPDATE questionnaires 
SET TenantId = CASE 
    WHEN (questionnaire_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 72. quick_access_favorites
UPDATE quick_access_favorites 
SET TenantId = CASE 
    WHEN (id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 73. rbac_tprm
UPDATE rbac_tprm 
SET TenantId = CASE 
    WHEN (RBACId % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- 74. screening_matches
UPDATE screening_matches 
SET TenantId = CASE 
    WHEN (match_id % 2) = 0 THEN 1 
    ELSE 2 
END
WHERE TenantId IS NULL;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

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

-- Check for any NULL TenantId values (should be 0 after running)
SELECT 
    'rfps' AS table_name,
    COUNT(*) AS null_count
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
-- 1. If a table doesn't exist, MySQL will show an error - just skip that table
-- 2. If you get an error for a specific table, comment it out with --
-- 3. Distribution: Even PK values -> Tenant 1, Odd PK values -> Tenant 2
-- 4. Safe to run multiple times (only updates NULL values)
-- ============================================================================

