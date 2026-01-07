-- ============================================================================
-- Add TenantId Column to All Remaining TPRM Module Tables
-- ============================================================================
-- This script adds TenantId column, foreign key, and index to all remaining modules
-- (RFP module is excluded as it has its own script)
-- No UPDATE statements included - you need to populate TenantId values separately
-- ============================================================================

-- ============================================================================
-- CONTRACTS MODULE TABLES
-- ============================================================================

-- 1. vendors - Vendor information (shared with other modules)
ALTER TABLE vendors 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendors_tenant_id (TenantId);

-- 2. vendor_contracts - Vendor contracts
ALTER TABLE vendor_contracts 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_contracts_tenant_id (TenantId);

-- 3. contract_terms - Contract terms
ALTER TABLE contract_terms 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_terms_tenant_id (TenantId);

-- 4. contract_clauses - Contract clauses
ALTER TABLE contract_clauses 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_clauses_tenant_id (TenantId);

-- 5. vendor_contacts - Vendor contact information
ALTER TABLE vendor_contacts 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_contacts_tenant_id (TenantId);

-- 6. contract_amendments - Contract amendments
ALTER TABLE contract_amendments 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_amendments_tenant_id (TenantId);

-- 7. contract_renewals - Contract renewals
ALTER TABLE contract_renewals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_renewals_tenant_id (TenantId);

-- 8. contract_approvals - Contract approval records
ALTER TABLE contract_approvals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_approvals_tenant_id (TenantId);

-- ============================================================================
-- VENDOR CORE MODULE TABLES (apps/vendor_core)
-- ============================================================================

-- 9. vendor_categories - Vendor categories (if tenant-specific)
ALTER TABLE vendor_categories 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_categories_tenant_id (TenantId);

-- 10. vendor_lifecycle_stages - Vendor lifecycle stages
ALTER TABLE vendor_lifecycle_stages 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_lifecycle_stages_tenant_id (TenantId);

-- 11. temp_vendor - Temporary vendor records
ALTER TABLE temp_vendor 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_temp_vendor_tenant_id (TenantId);

-- 12. external_screening_results - External screening results
ALTER TABLE external_screening_results 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_external_screening_results_tenant_id (TenantId);

-- 13. screening_matches - Screening matches
ALTER TABLE screening_matches 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_screening_matches_tenant_id (TenantId);

-- 14. lifecycle_tracker - Lifecycle tracking
ALTER TABLE lifecycle_tracker 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_lifecycle_tracker_tenant_id (TenantId);

-- 15. vendor_documents - Vendor documents
ALTER TABLE vendor_documents 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_documents_tenant_id (TenantId);

-- ============================================================================
-- RISK ANALYSIS MODULE TABLES
-- ============================================================================

-- 16. risk_tprm - Risk analysis records (used by multiple modules)
ALTER TABLE risk_tprm 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_risk_tprm_tenant_id (TenantId);

-- ============================================================================
-- COMPLIANCE MODULE TABLES
-- ============================================================================

-- 17. frameworks - Compliance frameworks (if tenant-specific)
ALTER TABLE frameworks 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_frameworks_tenant_id (TenantId);

-- 18. compliance_mapping - Compliance mapping to SLAs
ALTER TABLE compliance_mapping 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_compliance_mapping_tenant_id (TenantId);

-- ============================================================================
-- AUDITS MODULE TABLES
-- ============================================================================

-- 19. audits - Audit records
ALTER TABLE audits 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_audits_tenant_id (TenantId);

-- 20. static_questionnaires - Static audit questionnaires
ALTER TABLE static_questionnaires 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_static_questionnaires_tenant_id (TenantId);

-- 21. audit_versions - Audit version history
ALTER TABLE audit_versions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_audit_versions_tenant_id (TenantId);

-- 22. audit_findings - Audit findings
ALTER TABLE audit_findings 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_audit_findings_tenant_id (TenantId);

-- 23. audit_reports - Audit reports
ALTER TABLE audit_reports 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_audit_reports_tenant_id (TenantId);

-- ============================================================================
-- CONTRACT AUDITS MODULE TABLES
-- ============================================================================

-- 24. contract_audits - Contract audit records
ALTER TABLE contract_audits 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_audits_tenant_id (TenantId);

-- 25. contract_static_questionnaires - Contract audit questionnaires
ALTER TABLE contract_static_questionnaires 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_static_questionnaires_tenant_id (TenantId);

-- 26. contract_audit_versions - Contract audit versions
ALTER TABLE contract_audit_versions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_audit_versions_tenant_id (TenantId);

-- 27. contract_audit_findings - Contract audit findings
ALTER TABLE contract_audit_findings 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_audit_findings_tenant_id (TenantId);

-- 28. contract_audit_reports - Contract audit reports
ALTER TABLE contract_audit_reports 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_audit_reports_tenant_id (TenantId);

-- ============================================================================
-- BCP/DRP MODULE TABLES
-- ============================================================================

-- 29. bcp_drp_plans - BCP/DRP plans
ALTER TABLE bcp_drp_plans 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_bcp_drp_plans_tenant_id (TenantId);

-- 30. bcp_extracted_details - BCP extracted details
ALTER TABLE bcp_extracted_details 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_bcp_extracted_details_tenant_id (TenantId);

-- 31. drp_extracted_details - DRP extracted details
ALTER TABLE drp_extracted_details 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_drp_extracted_details_tenant_id (TenantId);

-- 32. bcp_drp_evaluations - BCP/DRP evaluations
ALTER TABLE bcp_drp_evaluations 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_bcp_drp_evaluations_tenant_id (TenantId);

-- 33. test_questionnaires - Test questionnaires
ALTER TABLE test_questionnaires 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_test_questionnaires_tenant_id (TenantId);

-- 34. test_questions - Test questions
ALTER TABLE test_questions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_test_questions_tenant_id (TenantId);

-- 35. test_assignments_responses - Test assignment responses
ALTER TABLE test_assignments_responses 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_test_assignments_responses_tenant_id (TenantId);

-- 36. bcp_drp_approvals - BCP/DRP approval records
ALTER TABLE bcp_drp_approvals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_bcp_drp_approvals_tenant_id (TenantId);

-- 37. questionnaire_templates - Questionnaire templates
ALTER TABLE questionnaire_templates 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaire_templates_tenant_id (TenantId);

-- ============================================================================
-- SLAs MODULE TABLES
-- ============================================================================

-- 38. vendor_slas - Vendor SLAs
ALTER TABLE vendor_slas 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_slas_tenant_id (TenantId);

-- 39. sla_metrics - SLA metrics
ALTER TABLE sla_metrics 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_metrics_tenant_id (TenantId);

-- 40. sla_documents - SLA documents
ALTER TABLE sla_documents 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_documents_tenant_id (TenantId);

-- 41. sla_compliance - SLA compliance records
ALTER TABLE sla_compliance 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_compliance_tenant_id (TenantId);

-- 42. sla_violations - SLA violations
ALTER TABLE sla_violations 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_violations_tenant_id (TenantId);

-- 43. sla_reviews - SLA reviews
ALTER TABLE sla_reviews 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_reviews_tenant_id (TenantId);

-- 44. sla_approvals - SLA approval records
ALTER TABLE sla_approvals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_approvals_tenant_id (TenantId);

-- ============================================================================
-- RBAC MODULE TABLES
-- ============================================================================

-- 45. rbac_tprm - RBAC permissions for TPRM
ALTER TABLE rbac_tprm 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rbac_tprm_tenant_id (TenantId);

-- 46. AccessRequestTPRM - Access requests
ALTER TABLE AccessRequestTPRM 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_AccessRequestTPRM_tenant_id (TenantId);

-- ============================================================================
-- VENDOR RISK MODULE TABLES (apps/vendor_risk)
-- ============================================================================

-- 47. vendor_risk_assessments - Vendor risk assessments
ALTER TABLE vendor_risk_assessments 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_risk_assessments_tenant_id (TenantId);

-- 48. vendor_risk_factors - Vendor risk factors
ALTER TABLE vendor_risk_factors 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_risk_factors_tenant_id (TenantId);

-- 49. vendor_risk_thresholds - Vendor risk thresholds
ALTER TABLE vendor_risk_thresholds 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_risk_thresholds_tenant_id (TenantId);

-- ============================================================================
-- VENDOR QUESTIONNAIRE MODULE TABLES (apps/vendor_questionnaire)
-- ============================================================================

-- 50. questionnaires - Questionnaires
ALTER TABLE questionnaires 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaires_tenant_id (TenantId);

-- 51. questionnaire_questions - Questionnaire questions
ALTER TABLE questionnaire_questions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaire_questions_tenant_id (TenantId);

-- 52. questionnaire_responses - Questionnaire responses
ALTER TABLE questionnaire_responses 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaire_responses_tenant_id (TenantId);

-- 53. questionnaire_assignments - Questionnaire assignments
ALTER TABLE questionnaire_assignments 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaire_assignments_tenant_id (TenantId);

-- 54. questionnaire_response_submissions - Response submissions
ALTER TABLE questionnaire_response_submissions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaire_response_submissions_tenant_id (TenantId);

-- ============================================================================
-- VENDOR LIFECYCLE MODULE TABLES (apps/vendor_lifecycle)
-- ============================================================================

-- 55. vendor_approvals - Vendor approvals
ALTER TABLE vendor_approvals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_approvals_tenant_id (TenantId);

-- 56. vendor_status_history - Vendor status history
ALTER TABLE vendor_status_history 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_status_history_tenant_id (TenantId);

-- ============================================================================
-- VENDOR DASHBOARD MODULE TABLES (apps/vendor_dashboard)
-- ============================================================================

-- 57. vendor_notifications - Vendor notifications
ALTER TABLE vendor_notifications 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_notifications_tenant_id (TenantId);

-- 58. vendor_audit_log - Vendor audit logs
ALTER TABLE vendor_audit_log 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_audit_log_tenant_id (TenantId);

-- 59. vendor_bcp_plans - Vendor BCP plans
ALTER TABLE vendor_bcp_plans 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_bcp_plans_tenant_id (TenantId);

-- 60. vendor_screening_matches - Vendor screening matches
ALTER TABLE vendor_screening_matches 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_screening_matches_tenant_id (TenantId);

-- ============================================================================
-- VENDOR APPROVAL MODULE TABLES (apps/vendor_approval)
-- ============================================================================

-- 61. tprm_risk - TPRM risk records
ALTER TABLE tprm_risk 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tprm_risk_tenant_id (TenantId);

-- ============================================================================
-- NOTIFICATIONS MODULE TABLES
-- ============================================================================

-- 62. notifications - User notifications (if tenant-specific)
ALTER TABLE notifications 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_notifications_tenant_id (TenantId);

-- ============================================================================
-- GLOBAL SEARCH MODULE TABLES
-- ============================================================================

-- 63. search_index - Search index (if tenant-specific)
ALTER TABLE search_index 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_search_index_tenant_id (TenantId);

-- 64. search_analytics - Search analytics (if tenant-specific)
ALTER TABLE search_analytics 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_search_analytics_tenant_id (TenantId);

-- ============================================================================
-- OCR MODULE TABLES
-- ============================================================================

-- 65. documents - OCR documents
ALTER TABLE documents 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_documents_tenant_id (TenantId);

-- 66. ocr_results - OCR results
ALTER TABLE ocr_results 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_ocr_results_tenant_id (TenantId);

-- 67. extracted_data - Extracted data from OCR
ALTER TABLE extracted_data 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_extracted_data_tenant_id (TenantId);

-- ============================================================================
-- QUICK ACCESS MODULE TABLES
-- ============================================================================

-- 68. quick_access_favorites - Quick access favorites (if tenant-specific)
ALTER TABLE quick_access_favorites 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_quick_access_favorites_tenant_id (TenantId);

-- 69. grc_logs - GRC logs (if tenant-specific)
ALTER TABLE grc_logs 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_grc_logs_tenant_id (TenantId);

-- ============================================================================
-- MFA AUTH MODULE TABLES
-- ============================================================================

-- 70. mfa_email_challenges - MFA email challenges (if tenant-specific)
ALTER TABLE mfa_email_challenges 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_mfa_email_challenges_tenant_id (TenantId);

-- 71. mfa_audit_log - MFA audit logs (if tenant-specific)
ALTER TABLE mfa_audit_log 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_mfa_audit_log_tenant_id (TenantId);

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Total Tables: 71
--   - Contracts Module: 8 tables
--   - Vendor Core Module: 7 tables
--   - Risk Analysis Module: 1 table
--   - Compliance Module: 2 tables
--   - Audits Module: 5 tables
--   - Contract Audits Module: 5 tables
--   - BCP/DRP Module: 9 tables
--   - SLAs Module: 7 tables
--   - RBAC Module: 2 tables
--   - Vendor Risk Module: 3 tables
--   - Vendor Questionnaire Module: 5 tables
--   - Vendor Lifecycle Module: 2 tables
--   - Vendor Dashboard Module: 4 tables
--   - Vendor Approval Module: 1 table
--   - Notifications Module: 1 table
--   - Global Search Module: 2 tables
--   - OCR Module: 3 tables
--   - Quick Access Module: 2 tables
--   - MFA Auth Module: 2 tables
-- ============================================================================

