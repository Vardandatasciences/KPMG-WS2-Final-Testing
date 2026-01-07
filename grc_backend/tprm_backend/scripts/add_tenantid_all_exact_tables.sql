-- ============================================================================
-- Add TenantId to ALL TPRM Tables (Based on Actual Models)
-- ============================================================================
-- This script adds TenantId to all tables found in the TPRM models
-- ============================================================================

SET @default_tenant_id = (SELECT TenantId FROM tenants WHERE Subdomain = 'default' LIMIT 1);

-- If default tenant doesn't exist, create it
SET @default_exists = (SELECT COUNT(*) FROM tenants WHERE Subdomain = 'default');
SET @sql = IF(@default_exists = 0,
    'INSERT INTO tenants (Name, Subdomain, LicenseKey, SubscriptionTier, Status, MaxUsers, StorageLimitGB, Settings)
     VALUES (''Default Tenant'', ''default'', ''DEFAULT-LICENSE-TPRM'', ''enterprise'', ''active'', 1000, 1000, ''{}'')',
    'SELECT ''Default tenant already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @default_tenant_id = (SELECT TenantId FROM tenants WHERE Subdomain = 'default' LIMIT 1);

-- ============================================================================
-- PHASE 1: CRITICAL TABLES
-- ============================================================================

-- 1. Users (if not already done)
-- ALTER TABLE users 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_users_tenant_id (TenantId);
-- UPDATE users SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- 2. RFPs
ALTER TABLE rfps 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfps_tenant_id (TenantId);
UPDATE rfps SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- 3. Vendors
ALTER TABLE vendors 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendors_tenant_id (TenantId);
UPDATE vendors SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- 4. Vendor Contracts
ALTER TABLE vendor_contracts 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_contracts_tenant_id (TenantId);
UPDATE vendor_contracts SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- 5. RBAC TPRM
ALTER TABLE rbac_tprm 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rbac_tprm_tenant_id (TenantId);
UPDATE rbac_tprm SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 2: HIGH PRIORITY - RFP MODULE
-- ============================================================================

ALTER TABLE rfp_evaluation_criteria 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_evaluation_criteria_tenant_id (TenantId);
UPDATE rfp_evaluation_criteria SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE file_storage 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_file_storage_tenant_id (TenantId);
UPDATE file_storage SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE s3_files 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_s3_files_tenant_id (TenantId);
UPDATE s3_files SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_evaluation_scores 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_evaluation_scores_tenant_id (TenantId);
UPDATE rfp_evaluation_scores SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_evaluator_assignments 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_evaluator_assignments_tenant_id (TenantId);
UPDATE rfp_evaluator_assignments SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_committee 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_committee_tenant_id (TenantId);
UPDATE rfp_committee SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_final_evaluation 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_final_evaluation_tenant_id (TenantId);
UPDATE rfp_final_evaluation SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_versions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_versions_tenant_id (TenantId);
UPDATE rfp_versions SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_change_requests 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_change_requests_tenant_id (TenantId);
UPDATE rfp_change_requests SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_version_comparisons 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_version_comparisons_tenant_id (TenantId);
UPDATE rfp_version_comparisons SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_unmatched_vendors 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_unmatched_vendors_tenant_id (TenantId);
UPDATE rfp_unmatched_vendors SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_vendor_invitations 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_vendor_invitations_tenant_id (TenantId);
UPDATE rfp_vendor_invitations SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_vendor_selections 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_vendor_selections_tenant_id (TenantId);
UPDATE rfp_vendor_selections SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_responses 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_responses_tenant_id (TenantId);
UPDATE rfp_responses SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_award_notifications 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_award_notifications_tenant_id (TenantId);
UPDATE rfp_award_notifications SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE rfp_type_custom_fields 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_type_custom_fields_tenant_id (TenantId);
UPDATE rfp_type_custom_fields SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 2: HIGH PRIORITY - CONTRACTS MODULE
-- ============================================================================

ALTER TABLE contract_terms 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_terms_tenant_id (TenantId);
UPDATE contract_terms SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE contract_clauses 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_clauses_tenant_id (TenantId);
UPDATE contract_clauses SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_contacts 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_contacts_tenant_id (TenantId);
UPDATE vendor_contacts SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE contract_amendments 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_amendments_tenant_id (TenantId);
UPDATE contract_amendments SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE contract_renewals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_renewals_tenant_id (TenantId);
UPDATE contract_renewals SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE contract_approvals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_approvals_tenant_id (TenantId);
UPDATE contract_approvals SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 2: HIGH PRIORITY - RFP APPROVAL MODULE
-- ============================================================================

ALTER TABLE approval_workflows 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_workflows_tenant_id (TenantId);
UPDATE approval_workflows SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE approval_requests 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_requests_tenant_id (TenantId);
UPDATE approval_requests SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE approval_stages 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_stages_tenant_id (TenantId);
UPDATE approval_stages SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE approval_comments 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_comments_tenant_id (TenantId);
UPDATE approval_comments SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE approval_request_versions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_request_versions_tenant_id (TenantId);
UPDATE approval_request_versions SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 2: HIGH PRIORITY - RISK ANALYSIS
-- ============================================================================

ALTER TABLE risk_tprm 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_risk_tprm_tenant_id (TenantId);
UPDATE risk_tprm SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 2: HIGH PRIORITY - COMPLIANCE
-- ============================================================================

ALTER TABLE compliance_mapping 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_compliance_mapping_tenant_id (TenantId);
UPDATE compliance_mapping SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 2: HIGH PRIORITY - AUDITS
-- ============================================================================

ALTER TABLE audits 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_audits_tenant_id (TenantId);
UPDATE audits SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE static_questionnaires 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_static_questionnaires_tenant_id (TenantId);
UPDATE static_questionnaires SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE audit_versions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_audit_versions_tenant_id (TenantId);
UPDATE audit_versions SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE audit_findings 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_audit_findings_tenant_id (TenantId);
UPDATE audit_findings SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE audit_reports 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_audit_reports_tenant_id (TenantId);
UPDATE audit_reports SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 2: HIGH PRIORITY - CONTRACT AUDITS
-- ============================================================================

ALTER TABLE contract_audits 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_audits_tenant_id (TenantId);
UPDATE contract_audits SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE contract_static_questionnaires 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_static_questionnaires_tenant_id (TenantId);
UPDATE contract_static_questionnaires SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE contract_audit_versions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_audit_versions_tenant_id (TenantId);
UPDATE contract_audit_versions SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE contract_audit_findings 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_audit_findings_tenant_id (TenantId);
UPDATE contract_audit_findings SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE contract_audit_reports 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_contract_audit_reports_tenant_id (TenantId);
UPDATE contract_audit_reports SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 2: HIGH PRIORITY - BCP/DRP
-- ============================================================================

ALTER TABLE bcp_drp_plans 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_bcp_drp_plans_tenant_id (TenantId);
UPDATE bcp_drp_plans SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE bcp_extracted_details 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_bcp_extracted_details_tenant_id (TenantId);
UPDATE bcp_extracted_details SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE drp_extracted_details 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_drp_extracted_details_tenant_id (TenantId);
UPDATE drp_extracted_details SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE bcp_drp_evaluations 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_bcp_drp_evaluations_tenant_id (TenantId);
UPDATE bcp_drp_evaluations SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE test_questionnaires 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_test_questionnaires_tenant_id (TenantId);
UPDATE test_questionnaires SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE test_questions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_test_questions_tenant_id (TenantId);
UPDATE test_questions SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE test_assignments_responses 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_test_assignments_responses_tenant_id (TenantId);
UPDATE test_assignments_responses SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE bcp_drp_approvals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_bcp_drp_approvals_tenant_id (TenantId);
UPDATE bcp_drp_approvals SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE questionnaire_templates 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaire_templates_tenant_id (TenantId);
UPDATE questionnaire_templates SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 2: HIGH PRIORITY - SLAs
-- ============================================================================

ALTER TABLE vendor_slas 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_slas_tenant_id (TenantId);
UPDATE vendor_slas SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE sla_metrics 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_metrics_tenant_id (TenantId);
UPDATE sla_metrics SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE sla_documents 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_documents_tenant_id (TenantId);
UPDATE sla_documents SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE sla_compliance 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_compliance_tenant_id (TenantId);
UPDATE sla_compliance SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE sla_violations 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_violations_tenant_id (TenantId);
UPDATE sla_violations SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE sla_reviews 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_reviews_tenant_id (TenantId);
UPDATE sla_reviews SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE sla_approvals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_sla_approvals_tenant_id (TenantId);
UPDATE sla_approvals SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 3: MEDIUM PRIORITY - VENDOR MODULE
-- ============================================================================

ALTER TABLE vendor_categories 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_categories_tenant_id (TenantId);
UPDATE vendor_categories SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_lifecycle_stages 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_lifecycle_stages_tenant_id (TenantId);
UPDATE vendor_lifecycle_stages SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE temp_vendor 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_temp_vendor_tenant_id (TenantId);
UPDATE temp_vendor SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE external_screening_results 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_external_screening_results_tenant_id (TenantId);
UPDATE external_screening_results SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE screening_matches 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_screening_matches_tenant_id (TenantId);
UPDATE screening_matches SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE lifecycle_tracker 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_lifecycle_tracker_tenant_id (TenantId);
UPDATE lifecycle_tracker SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_documents 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_documents_tenant_id (TenantId);
UPDATE vendor_documents SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 3: MEDIUM PRIORITY - VENDOR APPS
-- ============================================================================

ALTER TABLE vendor_risk_assessments 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_risk_assessments_tenant_id (TenantId);
UPDATE vendor_risk_assessments SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_risk_factors 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_risk_factors_tenant_id (TenantId);
UPDATE vendor_risk_factors SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_risk_thresholds 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_risk_thresholds_tenant_id (TenantId);
UPDATE vendor_risk_thresholds SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE questionnaires 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaires_tenant_id (TenantId);
UPDATE questionnaires SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE questionnaire_questions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaire_questions_tenant_id (TenantId);
UPDATE questionnaire_questions SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE questionnaire_responses 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaire_responses_tenant_id (TenantId);
UPDATE questionnaire_responses SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE questionnaire_assignments 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaire_assignments_tenant_id (TenantId);
UPDATE questionnaire_assignments SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE questionnaire_response_submissions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_questionnaire_response_submissions_tenant_id (TenantId);
UPDATE questionnaire_response_submissions SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_approvals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_approvals_tenant_id (TenantId);
UPDATE vendor_approvals SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_status_history 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_status_history_tenant_id (TenantId);
UPDATE vendor_status_history SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_notifications 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_notifications_tenant_id (TenantId);
UPDATE vendor_notifications SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_audit_log 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_audit_log_tenant_id (TenantId);
UPDATE vendor_audit_log SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_bcp_plans 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_bcp_plans_tenant_id (TenantId);
UPDATE vendor_bcp_plans SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE vendor_screening_matches 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_vendor_screening_matches_tenant_id (TenantId);
UPDATE vendor_screening_matches SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE tprm_risk 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tprm_risk_tenant_id (TenantId);
UPDATE tprm_risk SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- PHASE 3: MEDIUM PRIORITY - OTHER MODULES
-- ============================================================================

ALTER TABLE AccessRequestTPRM 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_AccessRequestTPRM_tenant_id (TenantId);
UPDATE AccessRequestTPRM SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE notifications 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_notifications_tenant_id (TenantId);
UPDATE notifications SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE search_index 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_search_index_tenant_id (TenantId);
UPDATE search_index SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE search_analytics 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_search_analytics_tenant_id (TenantId);
UPDATE search_analytics SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE documents 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_documents_tenant_id (TenantId);
UPDATE documents SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE ocr_results 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_ocr_results_tenant_id (TenantId);
UPDATE ocr_results SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE extracted_data 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_extracted_data_tenant_id (TenantId);
UPDATE extracted_data SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE quick_access_favorites 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_quick_access_favorites_tenant_id (TenantId);
UPDATE quick_access_favorites SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE grc_logs 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_grc_logs_tenant_id (TenantId);
UPDATE grc_logs SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE mfa_email_challenges 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_mfa_email_challenges_tenant_id (TenantId);
UPDATE mfa_email_challenges SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

ALTER TABLE mfa_audit_log 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_mfa_audit_log_tenant_id (TenantId);
UPDATE mfa_audit_log SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- OPTIONAL: Frameworks (if tenant-specific)
-- ============================================================================
-- Uncomment if frameworks should be tenant-specific:
-- ALTER TABLE frameworks 
-- ADD COLUMN TenantId INT NULL,
-- ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
-- ADD INDEX idx_frameworks_tenant_id (TenantId);
-- UPDATE frameworks SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check which tables have TenantId column
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND COLUMN_NAME = 'TenantId'
ORDER BY TABLE_NAME;

-- Count records per tenant for major tables
SELECT 
    'rfps' AS table_name,
    COUNT(*) AS total_records,
    COUNT(TenantId) AS records_with_tenant
FROM rfps
UNION ALL
SELECT 'vendors', COUNT(*), COUNT(TenantId) FROM vendors
UNION ALL
SELECT 'vendor_contracts', COUNT(*), COUNT(TenantId) FROM vendor_contracts
UNION ALL
SELECT 'rbac_tprm', COUNT(*), COUNT(TenantId) FROM rbac_tprm
UNION ALL
SELECT 'approval_workflows', COUNT(*), COUNT(TenantId) FROM approval_workflows
UNION ALL
SELECT 'approval_requests', COUNT(*), COUNT(TenantId) FROM approval_requests
UNION ALL
SELECT 'risk_tprm', COUNT(*), COUNT(TenantId) FROM risk_tprm
UNION ALL
SELECT 'audits', COUNT(*), COUNT(TenantId) FROM audits
UNION ALL
SELECT 'bcp_drp_plans', COUNT(*), COUNT(TenantId) FROM bcp_drp_plans
UNION ALL
SELECT 'vendor_slas', COUNT(*), COUNT(TenantId) FROM vendor_slas;


