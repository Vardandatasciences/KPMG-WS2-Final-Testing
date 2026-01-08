# TenantId Column Guide - Which Tables Should Have TenantId

## ✅ Tables That SHOULD Have TenantId

These tables store **tenant-specific business data** and MUST have TenantId for multi-tenancy:

### Core Business Data Tables
- ✅ `users` - User accounts (each user belongs to a tenant)
- ✅ `vendors` - Vendor information
- ✅ `vendor_contracts` - Vendor contracts
- ✅ `vendor_documents` - Vendor documents
- ✅ `vendor_categories` - Vendor categories (tenant-specific configuration)
- ✅ `temp_vendor` - Temporary vendor registrations
- ✅ `rfps` - Request for Proposals
- ✅ `rfp_evaluation_criteria` - RFP evaluation criteria
- ✅ All RFP-related tables (rfp_responses, rfp_vendor_invitations, etc.)

### Approval & Workflow Tables
- ✅ `approval_workflows` - Approval workflow definitions
- ✅ `approval_requests` - Approval requests
- ✅ `approval_stages` - Approval stages
- ✅ `approval_comments` - Approval comments
- ✅ `contract_approvals` - Contract approvals
- ✅ `sla_approvals` - SLA approvals
- ✅ `bcp_drp_approvals` - BCP/DRP approvals

### Audit & Compliance Tables
- ✅ `audits` - Audit records
- ✅ `audit_versions` - Audit versions
- ✅ `audit_findings` - Audit findings
- ✅ `audit_reports` - Audit reports
- ✅ `contract_audits` - Contract audits
- ✅ `contract_audit_versions` - Contract audit versions
- ✅ `contract_audit_findings` - Contract audit findings
- ✅ `contract_audit_reports` - Contract audit reports
- ✅ `static_questionnaires` - Static questionnaires
- ✅ `contract_static_questionnaires` - Contract static questionnaires
- ✅ `compliance_mapping` - Compliance mappings
- ✅ `frameworks` - Compliance frameworks

### Risk & Assessment Tables
- ✅ `risk_tprm` - Risk records
- ✅ `vendor_risk_assessments` - Vendor risk assessments
- ✅ `vendor_risk_factors` - Vendor risk factors
- ✅ `vendor_risk_thresholds` - Vendor risk thresholds
- ✅ `screening_matches` - Screening matches
- ✅ `external_screening_results` - External screening results

### Questionnaire Tables
- ✅ `questionnaires` - Questionnaires
- ✅ `questionnaire_questions` - Questionnaire questions
- ✅ `questionnaire_responses` - Questionnaire responses
- ✅ `questionnaire_assignments` - Questionnaire assignments
- ✅ `questionnaire_response_submissions` - Questionnaire response submissions
- ✅ `test_questionnaires` - Test questionnaires (BCP/DRP)
- ✅ `test_questions` - Test questions

### BCP/DRP Tables
- ✅ `bcp_drp_plans` - BCP/DRP plans
- ✅ `bcp_extracted_details` - BCP extracted details
- ✅ `drp_extracted_details` - DRP extracted details
- ✅ `bcp_drp_evaluations` - BCP/DRP evaluations
- ✅ `test_assignments_responses` - Test assignment responses
- ✅ `questionnaire_templates` - Questionnaire templates

### SLA Tables
- ✅ `vendor_slas` - Vendor SLAs
- ✅ `sla_metrics` - SLA metrics
- ✅ `sla_documents` - SLA documents
- ✅ `sla_compliance` - SLA compliance records
- ✅ `sla_violations` - SLA violations
- ✅ `sla_reviews` - SLA reviews

### RBAC & Access Control
- ✅ `rbac_tprm` - RBAC permissions
- ✅ `AccessRequestTPRM` - Access requests

### Search & Analytics
- ✅ `search_index` - Search index (tenant-specific search data)
- ✅ `search_analytics` - Search analytics (tenant-specific analytics)

### User Preferences
- ✅ `quick_access_favorites` - Quick access favorites (user-specific, tenant-aware)

### Vendor Lifecycle
- ✅ `vendor_lifecycle_stages` - Vendor lifecycle stages (tenant-specific configuration)

---

## ❌ Tables That Should NOT Have TenantId

These tables are **system-level** or **shared across tenants**:

### System Tables
- ❌ `tenants` - The tenant table itself (no TenantId needed)
- ❌ `django_migrations` - Django migration tracking
- ❌ `django_content_type` - Django content types
- ❌ `django_session` - Django sessions

### Lookup/Reference Tables (if shared)
- ❌ `dropdown` - If this is a system-wide dropdown (but check - it might be tenant-specific)
  - **Note**: If dropdown values are tenant-specific, it SHOULD have TenantId
  - **Decision**: Check your business requirements

### Audit/Log Tables (if system-wide)
- ❌ System audit logs (if they track system-level events, not tenant events)
  - **Note**: If audit logs are tenant-specific, they SHOULD have TenantId

---

## 🔍 How to Determine if a Table Needs TenantId

### Questions to Ask:

1. **Is this data tenant-specific?**
   - If YES → Add TenantId
   - If NO → Don't add TenantId

2. **Can different tenants have different values for this table?**
   - If YES → Add TenantId
   - If NO → Don't add TenantId

3. **Is this a system configuration table shared by all tenants?**
   - If YES → Don't add TenantId
   - If NO → Add TenantId

4. **Is this a lookup/reference table?**
   - If tenant-specific → Add TenantId
   - If system-wide → Don't add TenantId

---

## 📝 Summary

**Rule of Thumb:**
- ✅ **Business data** → Add TenantId
- ✅ **User-generated content** → Add TenantId
- ✅ **Tenant-specific configuration** → Add TenantId
- ❌ **System tables** → Don't add TenantId
- ❌ **Shared lookup tables** → Don't add TenantId (unless tenant-specific)

**When in doubt:** Add TenantId. It's easier to filter by tenant than to add it later.

