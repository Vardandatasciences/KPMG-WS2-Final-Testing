# Exact Table Names Requiring TenantId

Based on actual models in the TPRM backend, here are **ALL tables** that need `TenantId` added.

## 🔴 CRITICAL - Must Add First

1. **`users`** - Users table (already done if you ran add_tenant_to_users.sql)

## 📦 RFP Module Tables

2. **`rfps`** - Main RFP table
3. **`rfp_evaluation_criteria`** - RFP evaluation criteria
4. **`file_storage`** - Files uploaded for RFPs
5. **`s3_files`** - S3 file references
6. **`rfp_evaluation_scores`** - RFP evaluation scores
7. **`rfp_evaluator_assignments`** - Evaluator assignments
8. **`rfp_committee`** - RFP committee members
9. **`rfp_final_evaluation`** - Final evaluation results
10. **`rfp_versions`** - RFP version history
11. **`rfp_change_requests`** - RFP change requests
12. **`rfp_version_comparisons`** - Version comparison data
13. **`rfp_unmatched_vendors`** - Unmatched vendors for RFP
14. **`rfp_vendor_invitations`** - Vendor invitations for RFP
15. **`rfp_vendor_selections`** - Vendor selections for RFP
16. **`rfp_responses`** - Vendor responses to RFPs
17. **`rfp_award_notifications`** - Award notifications
18. **`rfp_type_custom_fields`** - Custom fields for RFP types

## 📄 Contracts Module Tables

19. **`vendors`** - Vendor information (shared with other modules)
20. **`vendor_contracts`** - Vendor contracts
21. **`contract_terms`** - Contract terms
22. **`contract_clauses`** - Contract clauses
23. **`vendor_contacts`** - Vendor contact information
24. **`contract_amendments`** - Contract amendments
25. **`contract_renewals`** - Contract renewals
26. **`contract_approvals`** - Contract approval records

## 🏢 Vendor Module Tables (apps/vendor_core)

27. **`vendor_categories`** - Vendor categories (if tenant-specific)
28. **`vendor_lifecycle_stages`** - Vendor lifecycle stages
29. **`temp_vendor`** - Temporary vendor records
30. **`external_screening_results`** - External screening results
31. **`screening_matches`** - Screening matches
32. **`lifecycle_tracker`** - Lifecycle tracking
33. **`vendor_documents`** - Vendor documents

## ⚠️ Risk Analysis Module Tables

34. **`risk_tprm`** - Risk analysis records (used by multiple modules)
   - Used by: `risk_analysis`, `risk_analysis_vendor`, `rfp_risk_analysis`, `contract_risk_analysis`

## ✅ Compliance Module Tables

35. **`frameworks`** - Compliance frameworks (if tenant-specific)
36. **`compliance_mapping`** - Compliance mapping to SLAs

## 🔍 Audits Module Tables

37. **`audits`** - Audit records
38. **`static_questionnaires`** - Static audit questionnaires
39. **`audit_versions`** - Audit version history
40. **`audit_findings`** - Audit findings
41. **`audit_reports`** - Audit reports

## 🔍 Contract Audits Module Tables

42. **`contract_audits`** - Contract audit records
43. **`contract_static_questionnaires`** - Contract audit questionnaires
44. **`contract_audit_versions`** - Contract audit versions
45. **`contract_audit_findings`** - Contract audit findings
46. **`contract_audit_reports`** - Contract audit reports

## 🛡️ BCP/DRP Module Tables

47. **`bcp_drp_plans`** - BCP/DRP plans (table name is `bcp_drp_plans`, not `plan`)
48. **`bcp_extracted_details`** - BCP extracted details
49. **`drp_extracted_details`** - DRP extracted details
50. **`bcp_drp_evaluations`** - BCP/DRP evaluations
51. **`test_questionnaires`** - Test questionnaires
52. **`test_questions`** - Test questions
53. **`test_assignments_responses`** - Test assignment responses
54. **`bcp_drp_approvals`** - BCP/DRP approval records
55. **`questionnaire_templates`** - Questionnaire templates

## 📊 SLAs Module Tables

56. **`vendor_slas`** - Vendor SLAs (table name is `vendor_slas`, not `slas`)
57. **`sla_metrics`** - SLA metrics
58. **`sla_documents`** - SLA documents
59. **`sla_compliance`** - SLA compliance records
60. **`sla_violations`** - SLA violations
61. **`sla_reviews`** - SLA reviews
62. **`sla_approvals`** - SLA approval records

## 🔐 RBAC Module Tables

63. **`rbac_tprm`** - RBAC permissions for TPRM
64. **`AccessRequestTPRM`** - Access requests

## 📝 RFP Approval Module Tables

65. **`approval_workflows`** - Approval workflow definitions
66. **`approval_requests`** - Approval requests
67. **`approval_stages`** - Approval stages
68. **`approval_comments`** - Approval comments
69. **`approval_request_versions`** - Approval request versions

## 📧 Notifications Module Tables

70. **`notifications`** - User notifications (if tenant-specific)

## 🔎 Global Search Module Tables

71. **`search_index`** - Search index (if tenant-specific)
72. **`search_analytics`** - Search analytics (if tenant-specific)

## 📝 OCR Module Tables

73. **`documents`** - OCR documents
74. **`ocr_results`** - OCR results
75. **`extracted_data`** - Extracted data from OCR

## 🚀 Quick Access Module Tables

76. **`quick_access_favorites`** - Quick access favorites (if tenant-specific)
77. **`grc_logs`** - GRC logs (if tenant-specific)

## 🔐 MFA Auth Module Tables

78. **`mfa_email_challenges`** - MFA email challenges (if tenant-specific)
79. **`mfa_audit_log`** - MFA audit logs (if tenant-specific)

## 🏢 Vendor Apps Module Tables

### apps/vendor_risk
80. **`vendor_risk_assessments`** - Vendor risk assessments
81. **`vendor_risk_factors`** - Vendor risk factors
82. **`vendor_risk_thresholds`** - Vendor risk thresholds

### apps/vendor_questionnaire
83. **`questionnaires`** - Questionnaires
84. **`questionnaire_questions`** - Questionnaire questions
85. **`questionnaire_responses`** - Questionnaire responses
86. **`questionnaire_assignments`** - Questionnaire assignments
87. **`questionnaire_response_submissions`** - Response submissions

### apps/vendor_lifecycle
88. **`vendor_approvals`** - Vendor approvals
89. **`vendor_status_history`** - Vendor status history

### apps/vendor_dashboard
90. **`vendor_notifications`** - Vendor notifications
91. **`vendor_audit_log`** - Vendor audit logs
92. **`vendor_bcp_plans`** - Vendor BCP plans
93. **`vendor_screening_matches`** - Vendor screening matches

### apps/vendor_approval
94. **`tprm_risk`** - TPRM risk records

## ❌ Tables That DO NOT Need TenantId

- **`tenants`** - The tenant table itself
- **`dropdown`** - Dropdown values (usually shared across tenants)
- **`users`** - Already has TenantId (done separately)

---

## 📋 Summary by Priority

### Phase 1: Critical (5 tables)
1. `users` ✅ (already done)
2. `rfps`
3. `vendors`
4. `vendor_contracts`
5. `rbac_tprm`

### Phase 2: High Priority (15 tables)
6. `approval_workflows`
7. `approval_requests`
8. `approval_stages`
9. `risk_tprm`
10. `compliance_mapping`
11. `audits`
12. `contract_audits`
13. `bcp_drp_plans`
14. `bcp_drp_approvals`
15. `vendor_slas`
16. `rfp_evaluation_criteria`
17. `file_storage`
18. `vendor_contacts`
19. `contract_terms`
20. `contract_clauses`

### Phase 3: Medium Priority (20 tables)
21. `approval_comments`
22. `approval_request_versions`
23. `rfp_versions`
24. `rfp_responses`
25. `rfp_vendor_invitations`
26. `contract_amendments`
27. `contract_renewals`
28. `contract_approvals`
29. `sla_metrics`
30. `sla_violations`
31. `sla_approvals`
32. `audit_versions`
33. `audit_findings`
34. `audit_reports`
35. `contract_audit_versions`
36. `contract_audit_findings`
37. `contract_audit_reports`
38. `questionnaire_templates`
39. `vendor_categories`
40. `AccessRequestTPRM`

### Phase 4: Additional Tables (Remaining ~50 tables)
All other tables from the complete list above.

---

## 🎯 Total Count

**Approximately 94 tables** need TenantId added (excluding system tables).

---

## 📝 Notes

1. **Table Name Variations**: Some models might use different table names. Always verify with:
   ```sql
   SHOW TABLES;
   ```

2. **Shared Tables**: Some tables like `vendors` are used by multiple modules - only add TenantId once.

3. **Risk Table**: `risk_tprm` is used by multiple risk analysis modules - only add TenantId once.

4. **Managed vs Unmanaged**: Some models have `managed = False`, meaning Django doesn't manage them. You still need to add TenantId via SQL.

---

**Last Updated**: Based on actual models in TPRM backend


