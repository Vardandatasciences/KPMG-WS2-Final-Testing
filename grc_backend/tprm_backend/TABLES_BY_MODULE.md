# Tables Requiring TenantId - Organized by Module

## 🔴 CRITICAL (Must Add First)

1. `users`

---

## 📦 RFP Module

2. `rfps`
3. `rfp_evaluation_criteria`
4. `file_storage`
5. `s3_files`
6. `rfp_evaluation_scores`
7. `rfp_evaluator_assignments`
8. `rfp_committee`
9. `rfp_final_evaluation`
10. `rfp_versions`
11. `rfp_change_requests`
12. `rfp_version_comparisons`
13. `rfp_unmatched_vendors`
14. `rfp_vendor_invitations`
15. `rfp_vendor_selections`
16. `rfp_responses`
17. `rfp_award_notifications`
18. `rfp_type_custom_fields`

---

## 📝 RFP Approval Module

19. `approval_workflows`
20. `approval_requests`
21. `approval_stages`
22. `approval_comments`
23. `approval_request_versions`

---

## 📄 Contracts Module

24. `vendors`
25. `vendor_contracts`
26. `contract_terms`
27. `contract_clauses`
28. `vendor_contacts`
29. `contract_amendments`
30. `contract_renewals`
31. `contract_approvals`

---

## 🏢 Vendor Core Module

32. `vendor_categories`
33. `vendor_lifecycle_stages`
34. `temp_vendor`
35. `external_screening_results`
36. `screening_matches`
37. `lifecycle_tracker`
38. `vendor_documents`

---

## ⚠️ Risk Analysis Module

39. `risk_tprm`

---

## ✅ Compliance Module

40. `compliance_mapping`

---

## 🔍 Audits Module

41. `audits`
42. `static_questionnaires`
43. `audit_versions`
44. `audit_findings`
45. `audit_reports`

---

## 🔍 Contract Audits Module

46. `contract_audits`
47. `contract_static_questionnaires`
48. `contract_audit_versions`
49. `contract_audit_findings`
50. `contract_audit_reports`

---

## 🛡️ BCP/DRP Module

51. `bcp_drp_plans`
52. `bcp_extracted_details`
53. `drp_extracted_details`
54. `bcp_drp_evaluations`
55. `test_questionnaires`
56. `test_questions`
57. `test_assignments_responses`
58. `bcp_drp_approvals`
59. `questionnaire_templates`

---

## 📊 SLAs Module

60. `vendor_slas`
61. `sla_metrics`
62. `sla_documents`
63. `sla_compliance`
64. `sla_violations`
65. `sla_reviews`
66. `sla_approvals`

---

## 🔐 RBAC Module

67. `rbac_tprm`
68. `AccessRequestTPRM`

---

## 🏢 Vendor Risk Module (apps/vendor_risk)

69. `vendor_risk_assessments`
70. `vendor_risk_factors`
71. `vendor_risk_thresholds`

---

## 🏢 Vendor Questionnaire Module (apps/vendor_questionnaire)

72. `questionnaires`
73. `questionnaire_questions`
74. `questionnaire_responses`
75. `questionnaire_assignments`
76. `questionnaire_response_submissions`

---

## 🏢 Vendor Lifecycle Module (apps/vendor_lifecycle)

77. `vendor_approvals`
78. `vendor_status_history`

---

## 🏢 Vendor Dashboard Module (apps/vendor_dashboard)

79. `vendor_notifications`
80. `vendor_audit_log`
81. `vendor_bcp_plans`
82. `vendor_screening_matches`

---

## 🏢 Vendor Approval Module (apps/vendor_approval)

83. `tprm_risk`

---

## 📧 Notifications Module

84. `notifications`

---

## 🔎 Global Search Module

85. `search_index`
86. `search_analytics`

---

## 📝 OCR Module

87. `documents`
88. `ocr_results`
89. `extracted_data`

---

## 🚀 Quick Access Module

90. `quick_access_favorites`
91. `grc_logs`

---

## 🔐 MFA Auth Module

92. `mfa_email_challenges`
93. `mfa_audit_log`

---

## ⚙️ Optional (Review if tenant-specific)

94. `frameworks` - Only if frameworks are tenant-specific (usually shared)

---

## 📊 Summary

**Total: 94 tables** (including optional frameworks)

**Breakdown:**
- RFP Module: 18 tables
- Contracts Module: 8 tables
- RFP Approval: 5 tables
- Audits: 10 tables
- BCP/DRP: 9 tables
- SLAs: 7 tables
- Vendor Apps: 15 tables
- Other Modules: 22 tables

---

**Note**: Some tables like `vendors` are used by multiple modules - only add TenantId once.


