-- ============================================================================
-- Add TenantId Column to RFP Module Tables
-- ============================================================================
-- This script adds TenantId column, foreign key, and index to all RFP module tables
-- No UPDATE statements included - you need to populate TenantId values separately
-- ============================================================================

-- ============================================================================
-- RFP CORE MODULE TABLES (from rfp/models.py)
-- ============================================================================

-- 1. rfps - Main RFP table
ALTER TABLE rfps 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfps_tenant_id (TenantId);

-- 2. rfp_evaluation_criteria - RFP evaluation criteria
ALTER TABLE rfp_evaluation_criteria 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_evaluation_criteria_tenant_id (TenantId);

-- 3. file_storage - Files uploaded for RFPs
ALTER TABLE file_storage 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_file_storage_tenant_id (TenantId);

-- 4. s3_files - S3 file references
ALTER TABLE s3_files 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_s3_files_tenant_id (TenantId);

-- 5. rfp_evaluation_scores - RFP evaluation scores
ALTER TABLE rfp_evaluation_scores 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_evaluation_scores_tenant_id (TenantId);

-- 6. rfp_evaluator_assignments - Evaluator assignments
ALTER TABLE rfp_evaluator_assignments 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_evaluator_assignments_tenant_id (TenantId);

-- 7. rfp_committee - RFP committee members
ALTER TABLE rfp_committee 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_committee_tenant_id (TenantId);

-- 8. rfp_final_evaluation - Final evaluation results
ALTER TABLE rfp_final_evaluation 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_final_evaluation_tenant_id (TenantId);

-- 9. rfp_versions - RFP version history
ALTER TABLE rfp_versions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_versions_tenant_id (TenantId);

-- 10. rfp_change_requests - RFP change requests
ALTER TABLE rfp_change_requests 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_change_requests_tenant_id (TenantId);

-- 11. rfp_version_comparisons - Version comparison data
ALTER TABLE rfp_version_comparisons 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_version_comparisons_tenant_id (TenantId);

-- 12. rfp_unmatched_vendors - Unmatched vendors for RFP
ALTER TABLE rfp_unmatched_vendors 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_unmatched_vendors_tenant_id (TenantId);

-- 13. rfp_vendor_invitations - Vendor invitations for RFP
ALTER TABLE rfp_vendor_invitations 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_vendor_invitations_tenant_id (TenantId);

-- 14. rfp_vendor_selections - Vendor selections for RFP
ALTER TABLE rfp_vendor_selections 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_vendor_selections_tenant_id (TenantId);

-- 15. rfp_responses - Vendor responses to RFPs
ALTER TABLE rfp_responses 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_responses_tenant_id (TenantId);

-- 16. rfp_award_notifications - Award notifications
ALTER TABLE rfp_award_notifications 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_award_notifications_tenant_id (TenantId);

-- 17. rfp_type_custom_fields - Custom fields for RFP types
ALTER TABLE rfp_type_custom_fields 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_type_custom_fields_tenant_id (TenantId);

-- ============================================================================
-- RFP APPROVAL MODULE TABLES (from rfp_approval/models.py)
-- ============================================================================

-- 18. approval_workflows - Approval workflow definitions
ALTER TABLE approval_workflows 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_workflows_tenant_id (TenantId);

-- 19. approval_requests - Approval requests
ALTER TABLE approval_requests 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_requests_tenant_id (TenantId);

-- 20. approval_stages - Approval stages
ALTER TABLE approval_stages 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_stages_tenant_id (TenantId);

-- 21. approval_comments - Approval comments
ALTER TABLE approval_comments 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_comments_tenant_id (TenantId);

-- 22. approval_request_versions - Approval request versions
ALTER TABLE approval_request_versions 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_approval_request_versions_tenant_id (TenantId);

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Total Tables: 22
--   - RFP Core Module: 17 tables
--   - RFP Approval Module: 5 tables
-- ============================================================================

