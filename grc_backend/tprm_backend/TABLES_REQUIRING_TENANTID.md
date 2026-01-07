# Tables Requiring TenantId for Multi-Tenancy

This document lists **ALL tables** that need the `TenantId` column added for multi-tenancy implementation.

## 📋 Quick Summary

**Total Tables**: ~50+ tables across all TPRM modules

**Rule of Thumb**: 
- ✅ **ADD TenantId** to tables that store business data (RFPs, Contracts, Vendors, etc.)
- ✅ **ADD TenantId** to tables that store user-generated content
- ✅ **ADD TenantId** to configuration tables that are tenant-specific
- ❌ **DO NOT ADD** to system tables (users, tenants, dropdowns, etc. - but users DOES need it)
- ❌ **DO NOT ADD** to lookup/reference tables that are shared across tenants (unless they're tenant-specific)

---

## 🔴 CRITICAL - Must Have TenantId

### 1. Users Table (REQUIRED FIRST)
```sql
ALTER TABLE users 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_users_tenant_id (TenantId);
```

---

## 📦 RFP Module

### Core RFP Tables
- ✅ `rfps` (or `rfp`) - Main RFP table
- ✅ `rfp_evaluation_criteria` - RFP evaluation criteria
- ✅ `file_storage` - Files uploaded for RFPs
- ✅ `rfp_versions` - RFP version history (if exists)
- ✅ `rfp_version_comparisons` - Version comparison data (if exists)
- ✅ `rfp_responses` - Vendor responses to RFPs (if exists)
- ✅ `rfp_vendors` - Vendors linked to RFPs (if exists)
- ✅ `rfp_invitations` - RFP invitations sent to vendors (if exists)

### RFP Approval Tables
- ✅ `approval_workflows` - Approval workflow definitions
- ✅ `approval_requests` - Approval requests
- ✅ `approval_stages` - Approval stages
- ✅ `approval_comments` - Comments on approvals (if exists)
- ✅ `approval_assignments` - User assignments to approvals (if exists)

---

## 📄 Contracts Module

### Core Contract Tables
- ✅ `vendors` - Vendor information
- ✅ `vendor_contracts` (or `contracts`) - Vendor contracts
- ✅ `contract_terms` - Contract terms
- ✅ `contract_clauses` - Contract clauses
- ✅ `vendor_contacts` - Vendor contact information
- ✅ `contract_amendments` - Contract amendments
- ✅ `contract_renewals` - Contract renewals
- ✅ `contract_approval` - Contract approval records

### Contract Risk Analysis
- ✅ `contract_risk_analysis` - Contract risk analysis results (if exists)
- ✅ `contract_entities` - Entities extracted from contracts (if exists)

---

## 🏢 Vendors Module

### Core Vendor Tables
- ✅ `vendors` - Main vendors table (already listed above, but important)
- ✅ `vendor_categories` - Vendor categories (if tenant-specific)
- ✅ `vendor_assessments` - Vendor assessments (if exists)
- ✅ `vendor_questionnaires` - Vendor questionnaires (if exists)
- ✅ `vendor_risk_assessments` - Vendor risk assessments (if exists)
- ✅ `vendor_lifecycle` - Vendor lifecycle stages (if exists)
- ✅ `vendor_dashboard_data` - Vendor dashboard data (if exists)
- ✅ `vendor_approvals` - Vendor approval records (if exists)

---

## ⚠️ Risk Analysis Module

### Risk Tables
- ✅ `risk_analysis` - Risk analysis records
- ✅ `vendor_risk_analysis` - Vendor-specific risk analysis
- ✅ `rfp_risk_analysis` - RFP risk analysis (if exists)
- ✅ `contract_risk_analysis` - Contract risk analysis (if exists)
- ✅ `risk_findings` - Risk findings (if exists)
- ✅ `risk_recommendations` - Risk recommendations (if exists)

---

## ✅ Compliance Module

### Compliance Tables
- ✅ `compliance` - Compliance records
- ✅ `compliance_assessments` - Compliance assessments (if exists)
- ✅ `compliance_frameworks` - Compliance frameworks (if tenant-specific)
- ✅ `compliance_requirements` - Compliance requirements (if exists)
- ✅ `compliance_reports` - Compliance reports (if exists)

---

## 🔍 Audits Module

### Audit Tables
- ✅ `audits` - Audit records
- ✅ `audits_contract` - Contract audits
- ✅ `audit_findings` - Audit findings (if exists)
- ✅ `audit_recommendations` - Audit recommendations (if exists)
- ✅ `audit_reports` - Audit reports (if exists)

---

## 🛡️ BCP/DRP Module

### BCP/DRP Tables
- ✅ `plan` - BCP/DRP plans
- ✅ `bcp_drp_approvals` - BCP/DRP approval records
- ✅ `questionnaire_template` - Questionnaire templates (if tenant-specific)
- ✅ `bcp_drp_assessments` - BCP/DRP assessments (if exists)
- ✅ `bcp_drp_scenarios` - BCP/DRP scenarios (if exists)

---

## 📊 SLAs Module

### SLA Tables
- ✅ `slas` (or `vendor_sla`) - Service Level Agreements
- ✅ `sla_metrics` - SLA metrics (if exists)
- ✅ `sla_performance` - SLA performance records (if exists)
- ✅ `sla_approvals` - SLA approval records (if exists)
- ✅ `sla_violations` - SLA violations (if exists)

---

## 🔐 RBAC Module

### RBAC Tables
- ✅ `rbac_tprm` - RBAC permissions for TPRM
- ✅ `AccessRequestTPRM` - Access requests
- ✅ `rbac_roles` - RBAC roles (if tenant-specific)
- ✅ `rbac_permissions` - RBAC permissions (if tenant-specific)

---

## 📧 Notifications Module

### Notification Tables
- ✅ `notifications` - User notifications (if tenant-specific)
- ✅ `notification_templates` - Notification templates (if tenant-specific)
- ✅ `notification_preferences` - User notification preferences (if exists)

---

## 🔎 Global Search Module

### Search Tables
- ✅ `global_search_index` - Search index (if tenant-specific)
- ✅ `search_history` - User search history (if exists)

---

## 📈 Analytics Module

### Analytics Tables
- ✅ `analytics_events` - Analytics events (if tenant-specific)
- ✅ `analytics_reports` - Analytics reports (if exists)
- ✅ `performance_metrics` - Performance metrics (if exists)

---

## 🚀 Quick Access Module

### Quick Access Tables
- ✅ `quick_access_items` - Quick access items (if exists)
- ✅ `user_dashboards` - User dashboard configurations (if exists)

---

## 📝 OCR Module

### OCR Tables
- ✅ `ocr_documents` - OCR processed documents (if exists)
- ✅ `ocr_results` - OCR results (if exists)

---

## ⚙️ Admin Access Module

### Admin Tables
- ✅ `admin_access_logs` - Admin access logs (if tenant-specific)
- ✅ `admin_settings` - Admin settings (if tenant-specific)

---

## ❓ Tables That MAY Need TenantId (Review)

### Configuration Tables (Review Case-by-Case)
- ⚠️ `dropdown` - Dropdown values (ONLY if tenant-specific, usually shared)
- ⚠️ `settings` - System settings (ONLY if tenant-specific)
- ⚠️ `configurations` - System configurations (ONLY if tenant-specific)

### Lookup Tables (Usually Shared)
- ❌ `countries` - Country list (usually shared)
- ❌ `currencies` - Currency list (usually shared)
- ❌ `industries` - Industry list (usually shared, unless tenant-specific)

---

## 📝 SQL Script Template

For each table, use this pattern:

```sql
-- Example: Adding TenantId to rfp table
ALTER TABLE rfp 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_rfp_tenant_id (TenantId);

-- After adding TenantId, assign existing data to default tenant
SET @default_tenant_id = (SELECT TenantId FROM tenants WHERE Subdomain = 'default' LIMIT 1);
UPDATE rfp SET TenantId = @default_tenant_id WHERE TenantId IS NULL;
```

---

## ✅ Priority Order

### Phase 1 (CRITICAL - Do First)
1. ✅ `users` - **MUST DO FIRST**
2. ✅ `rfps` (or `rfp`)
3. ✅ `vendors`
4. ✅ `vendor_contracts` (or `contracts`)
5. ✅ `rbac_tprm`

### Phase 2 (High Priority)
6. ✅ `approval_workflows`
7. ✅ `approval_requests`
8. ✅ `risk_analysis`
9. ✅ `compliance`
10. ✅ `audits`

### Phase 3 (Medium Priority)
11. ✅ `slas`
12. ✅ `plan` (BCP/DRP)
13. ✅ `rfp_evaluation_criteria`
14. ✅ `file_storage`
15. ✅ `vendor_contacts`

### Phase 4 (Lower Priority - Complete the rest)
16. ✅ All remaining tables from the list above

---

## 🔍 How to Verify Which Tables Exist

Run this SQL to see all tables in your database:

```sql
-- List all tables
SHOW TABLES;

-- Or get table names with row counts
SELECT 
    TABLE_NAME,
    TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'your_database_name'
ORDER BY TABLE_NAME;
```

---

## 📋 Checklist

Use this checklist to track which tables you've updated:

### Phase 1 - Critical
- [ ] `users`
- [ ] `rfps` (or `rfp`)
- [ ] `vendors`
- [ ] `vendor_contracts` (or `contracts`)
- [ ] `rbac_tprm`

### Phase 2 - High Priority
- [ ] `approval_workflows`
- [ ] `approval_requests`
- [ ] `approval_stages`
- [ ] `risk_analysis`
- [ ] `vendor_risk_analysis`
- [ ] `compliance`
- [ ] `audits`
- [ ] `audits_contract`

### Phase 3 - Medium Priority
- [ ] `slas` (or `vendor_sla`)
- [ ] `plan`
- [ ] `bcp_drp_approvals`
- [ ] `rfp_evaluation_criteria`
- [ ] `file_storage`
- [ ] `vendor_contacts`
- [ ] `contract_terms`
- [ ] `contract_clauses`
- [ ] `AccessRequestTPRM`

### Phase 4 - Complete List
- [ ] All other tables from the comprehensive list above

---

## 🚨 Important Notes

1. **Table Names May Vary**: Some tables might have different names (e.g., `rfp` vs `rfps`, `contracts` vs `vendor_contracts`). Check your actual database schema.

2. **Foreign Key Constraints**: Always add foreign key constraints to ensure data integrity:
   ```sql
   ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE
   ```

3. **Indexes**: Always add indexes on `TenantId` for performance:
   ```sql
   ADD INDEX idx_table_name_tenant_id (TenantId)
   ```

4. **Data Migration**: After adding `TenantId`, assign all existing records to the default tenant:
   ```sql
   UPDATE table_name SET TenantId = @default_tenant_id WHERE TenantId IS NULL;
   ```

5. **NULL Values**: Start with `NULL` allowed, then after data migration, you can make it `NOT NULL` if needed.

---

**Last Updated**: January 2026

