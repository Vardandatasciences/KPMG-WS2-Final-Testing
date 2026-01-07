# Complete Multi-Tenancy Verification Checklist for All TPRM Modules

## 🎯 Testing Strategy

**For each module:**
1. Login as **Tenant 1 User** → Check data
2. **Logout** → Login as **Tenant 2 User** → Check data
3. **Verify**: Different data for each tenant
4. **Create** new records in Tenant 1 → **Verify** Tenant 2 cannot see them
5. **Create** new records in Tenant 2 → **Verify** Tenant 1 cannot see them

---

## 1. ✅ RFP Module

### Pages/Views to Check:

#### **RFP List & Management**
- [ ] **RFP List Page** (`/rfp-list` or `/tprm/rfp-list`)
  - List shows only tenant's RFPs
  - Count is different for each tenant
  - Search/filter works within tenant only
  - **API Endpoint**: `GET /api/tprm/rfp/rfps/`

- [ ] **RFP Dashboard** (`/rfp-dashboard` or `/tprm/rfp-dashboard`)
  - Statistics show only tenant's data
  - Charts/graphs show tenant-specific metrics
  - **API Endpoint**: Check dashboard API calls

- [ ] **Create RFP** (`/rfp-creation` or `/tprm/rfp-creation`)
  - New RFP is assigned to correct tenant
  - Created RFP appears only for creating tenant
  - **API Endpoint**: `POST /api/tprm/rfp/rfps/`

- [ ] **RFP Details/View** (Access via RFP List → View button)
  - Can only view own tenant's RFPs
  - 404/403 error when accessing other tenant's RFP by direct ID
  - **API Endpoint**: `GET /api/tprm/rfp/rfps/{id}/`

- [ ] **Edit RFP** (Access via RFP List → Edit)
  - Can only edit own tenant's RFPs
  - Cannot edit other tenant's RFPs
  - **API Endpoint**: `PATCH /api/tprm/rfp/rfps/{id}/`

#### **RFP Workflow**
- [ ] **RFP Approval Workflow** (`/rfp-approval` or `/tprm/rfp-approval`)
  - Approval requests show only tenant's RFPs
  - Approvers can only see tenant's requests
  - **API Endpoint**: Check approval-related endpoints

- [ ] **RFP Evaluation** (`/rfp-evaluation` or `/tprm/rfp-evaluation`)
  - Evaluations show only tenant's RFPs
  - Evaluators can only evaluate tenant's RFPs
  - **API Endpoint**: `GET /api/tprm/rfp/rfp-evaluation-scores/`

- [ ] **Vendor Selection** (`/rfp-vendor-selection` or `/tprm/rfp-vendor-selection`)
  - Vendors shown are tenant's vendors only
  - Cannot select vendors from other tenants
  - **API Endpoint**: `GET /api/tprm/rfp/rfps/{id}/vendors/`

- [ ] **RFP Responses** (Access via RFP Details)
  - Responses show only for tenant's RFPs
  - Vendors can only respond to tenant's RFPs
  - **API Endpoint**: `GET /api/tprm/rfp/rfp-responses-list/`

- [ ] **Consensus & Award** (`/rfp-consensus` or `/tprm/rfp-consensus`)
  - Award decisions show only tenant's data
  - **API Endpoint**: Check consensus/award endpoints

- [ ] **RFP Comparison** (`/rfp-comparison` or `/tprm/rfp-comparison`)
  - Can only compare tenant's RFPs
  - **API Endpoint**: Check comparison endpoints

- [ ] **RFP Analytics** (`/rfp-analytics` or `/tprm/rfp-analytics`)
  - Analytics show only tenant's data
  - **API Endpoint**: `GET /api/tprm/rfp/kpi/*`

#### **RFP Documents & Files**
- [ ] **RFP Documents** (`/tprm/rfp/:id/documents`)
  - Documents show only for tenant's RFPs
  - Cannot access other tenant's documents

- [ ] **RFP Downloads** (PDF/Word)
  - Downloads work only for tenant's RFPs
  - 404/403 for other tenant's RFPs

#### **RFP Analytics & Reports**
- [ ] **RFP KPI Dashboard**
  - KPIs show only tenant's metrics
  - Charts reflect tenant-specific data

- [ ] **RFP Reports**
  - Reports contain only tenant's data

---

## 2. ✅ Vendor Management Modules

### **Vendor Core Module**
- [ ] **Vendor List** (`/vendors` or `/tprm/vendors`)
  - Shows only tenant's vendors
  - Search/filter works within tenant
  - **API Endpoint**: `GET /api/tprm/vendor-core/vendors/`

- [ ] **Vendor Details** (`/vendors/:id` or `/tprm/vendors/:id`)
  - Can only view own tenant's vendors
  - 404/403 for other tenant's vendors
  - **API Endpoint**: `GET /api/tprm/vendor-core/vendors/{id}/`

- [ ] **Vendor Registration** (`/vendor-registration` or `/tprm/vendor-registration`)
  - New vendor assigned to correct tenant
  - Appears only for creating tenant
  - **API Endpoint**: `POST /api/tprm/vendor-core/vendors/`

- [ ] **Vendor Dashboard** (`/vendor-dashboard` or `/tprm/vendor-dashboard`)
  - Statistics show only tenant's vendors
  - Metrics are tenant-specific
  - **API Endpoint**: Check vendor dashboard endpoints

### **Vendor Approval Module**
- [ ] **Vendor Approval Dashboard** (`/vendor-approval-dashboard` or `/tprm/vendor-approval-dashboard`)
  - Shows only tenant's pending approvals
  - Approvers see only tenant's requests
  - **API Endpoint**: Check vendor approval endpoints

- [ ] **Vendor Approval Workflow** (`/vendor-approval-workflow-creator`)
  - Approval decisions affect only tenant's vendors
  - **API Endpoint**: Check workflow endpoints

- [ ] **My Vendor Approvals** (`/vendor-my-approvals` or `/tprm/vendor-my-approvals`)
  - Shows only tenant's approval requests
  - **API Endpoint**: Check my approvals endpoints

### **Vendor Lifecycle Module**
- [ ] **Vendor Lifecycle** (`/vendor-lifecycle` or `/tprm/vendor-lifecycle`)
  - Lifecycle data shows only tenant's vendors
  - Stage transitions are tenant-specific
  - **API Endpoint**: Check vendor lifecycle endpoints

### **Vendor Risk Module**
- [ ] **Vendor Risk Scoring** (`/vendor-risk-scoring` or `/tprm/vendor-risk-scoring`)
  - Risk assessments show only tenant's vendors
  - Risk scores are tenant-specific
  - **API Endpoint**: Check vendor risk endpoints

### **Vendor Questionnaire Module**
- [ ] **Vendor Questionnaire** (`/vendor-questionnaire` or `/tprm/vendor-questionnaire`)
  - Questionnaires show only tenant's vendors
  - Responses are tenant-specific
  - **API Endpoint**: Check vendor questionnaire endpoints

- [ ] **Vendor Questionnaire Assignment** (`/vendor-questionnaire-assignment`)
  - Assignments show only tenant's vendors
  - **API Endpoint**: Check assignment endpoints

### **Vendor Dashboard Module**
- [ ] **Vendor KPI Dashboard** (`/vendor-kpi-dashboard` or `/tprm/vendor-kpi-dashboard`)
  - All metrics show only tenant's vendors
  - Charts/graphs are tenant-specific
  - **API Endpoint**: Check vendor KPI endpoints

---

## 3. ✅ Contracts Module

- [ ] **Contract List** (`/contracts` or `/tprm/contracts`)
  - Shows only tenant's contracts
  - Different count for each tenant
  - **API Endpoint**: `GET /api/tprm/contracts/contracts/`

- [ ] **Contract Dashboard** (`/contractdashboard` or `/tprm/contractdashboard`)
  - Statistics show only tenant's contracts
  - Metrics are tenant-specific
  - **API Endpoint**: Check contract dashboard endpoints

- [ ] **Contract Details** (`/contracts/:id` or `/tprm/contracts/:id`)
  - Can only view own tenant's contracts
  - 404/403 for other tenant's contracts
  - **API Endpoint**: `GET /api/tprm/contracts/contracts/{id}/`

- [ ] **Create Contract** (`/contracts/create` or `/tprm/contracts/create`)
  - New contract assigned to correct tenant
  - Appears only for creating tenant
  - **API Endpoint**: `POST /api/tprm/contracts/contracts/`

- [ ] **Edit Contract** (`/contracts/:id/edit` or `/tprm/contracts/:id/edit`)
  - Can only edit own tenant's contracts
  - **API Endpoint**: `PATCH /api/tprm/contracts/contracts/{id}/`

- [ ] **Contract Approval** (`/my-contract-approvals` or `/tprm/my-contract-approvals`)
  - Approval requests show only tenant's contracts
  - **API Endpoint**: Check contract approval endpoints

- [ ] **Contract Documents** (Access via Contract Details)
  - Documents show only for tenant's contracts
  - Cannot access other tenant's documents
  - **API Endpoint**: Check document endpoints

- [ ] **Contract OCR/NLP Analysis**
  - Analysis results are tenant-specific
  - **API Endpoint**: Check OCR/NLP endpoints

- [ ] **Contract Renewals** (`/contracts/:id/renewal`)
  - Renewals show only tenant's contracts
  - **API Endpoint**: Check renewal endpoints

- [ ] **Contract Comparison** (`/contract-comparison` or `/tprm/contract-comparison`)
  - Can only compare tenant's contracts
  - **API Endpoint**: Check comparison endpoints

- [ ] **Contract KPI Dashboard** (`/contract-kpi-dashboard` or `/tprm/contract-kpi-dashboard`)
  - KPIs show only tenant's contracts
  - **API Endpoint**: Check contract KPI endpoints

---

## 4. ✅ SLA (Service Level Agreement) Module

- [ ] **SLA List** (`/slas` or `/tprm/slas`)
  - Shows only tenant's SLAs
  - Different count for each tenant
  - **API Endpoint**: `GET /api/tprm/slas/slas/`

- [ ] **SLA Dashboard** (`/dashboard` or `/tprm/dashboard` - SLA Dashboard)
  - Statistics show only tenant's SLAs
  - Compliance metrics are tenant-specific
  - **API Endpoint**: Check SLA dashboard endpoints

- [ ] **SLA Details** (`/slas/:id` or `/tprm/slas/:id`)
  - Can only view own tenant's SLAs
  - 404/403 for other tenant's SLAs
  - **API Endpoint**: `GET /api/tprm/slas/slas/{id}/`

- [ ] **Create SLA** (`/slas/create` or `/tprm/slas/create`)
  - New SLA assigned to correct tenant
  - Appears only for creating tenant
  - **API Endpoint**: `POST /api/tprm/slas/slas/`

- [ ] **Edit SLA** (`/slas/:id/edit` or `/tprm/slas/:id/edit`)
  - Can only edit own tenant's SLAs
  - **API Endpoint**: `PATCH /api/tprm/slas/slas/{id}/`

- [ ] **Active SLAs** (`/slas/active` or `/tprm/slas/active`)
  - Shows only tenant's active SLAs
  - **API Endpoint**: Check active SLAs endpoint

- [ ] **Expiring SLAs** (`/slas/expiring` or `/tprm/slas/expiring`)
  - Shows only tenant's expiring SLAs
  - **API Endpoint**: Check expiring SLAs endpoint

- [ ] **SLA Renewals** (`/slas/renew` or `/tprm/slas/renew`)
  - Renewals show only tenant's SLAs
  - **API Endpoint**: Check renewal endpoints

- [ ] **SLA Approvals** (`/slas/approvals` or `/tprm/slas/approvals`)
  - Approval requests show only tenant's SLAs
  - **API Endpoint**: Check SLA approval endpoints

- [ ] **Performance Dashboard** (`/performance` or `/tprm/performance`)
  - Performance metrics show only tenant's SLAs
  - **API Endpoint**: Check performance endpoints

- [ ] **KPI Dashboard** (`/kpi-dashboard` or `/tprm/kpi-dashboard`)
  - KPIs show only tenant's SLAs
  - **API Endpoint**: Check KPI endpoints

---

## 5. ✅ BCP/DRP (Business Continuity/Disaster Recovery) Module

- [ ] **BCP Dashboard** (`/bcp/dashboard` or `/tprm/bcp/dashboard`)
  - Statistics show only tenant's plans
  - Metrics are tenant-specific
  - **API Endpoint**: Check BCP dashboard endpoints

- [ ] **BCP Vendor Upload** (`/bcp/vendor-upload` or `/tprm/bcp/vendor-upload`)
  - Vendors shown are tenant's vendors only
  - **API Endpoint**: Check vendor upload endpoints

- [ ] **BCP Plan Submission OCR** (`/bcp/plan-submission-ocr`)
  - OCR results are tenant-specific
  - **API Endpoint**: Check OCR endpoints

- [ ] **BCP Plan Evaluation** (`/bcp/evaluation` or `/tprm/bcp/evaluation`)
  - Evaluations show only tenant's plans
  - **API Endpoint**: Check evaluation endpoints

- [ ] **BCP Library** (`/bcp/library` or `/tprm/bcp/library`)
  - Library items show only tenant's plans
  - **API Endpoint**: Check library endpoints

- [ ] **BCP Questionnaire Library** (`/bcp/questionnaire-library`)
  - Questionnaires show only tenant's plans
  - **API Endpoint**: Check questionnaire library endpoints

- [ ] **BCP Questionnaire Builder** (`/bcp/questionnaire-builder`)
  - Can only build questionnaires for tenant
  - **API Endpoint**: Check questionnaire builder endpoints

- [ ] **BCP Questionnaire Workflow** (`/bcp/questionnaire-workflow`)
  - Workflows show only tenant's questionnaires
  - **API Endpoint**: Check workflow endpoints

- [ ] **BCP My Approvals** (`/bcp/my-approvals` or `/tprm/bcp/my-approvals`)
  - Approvals show only tenant's plans
  - **API Endpoint**: Check approval endpoints

- [ ] **BCP Vendor Hub** (`/bcp/vendor-hub` or `/tprm/bcp/vendor-hub`)
  - Vendors shown are tenant's vendors only
  - **API Endpoint**: Check vendor hub endpoints

- [ ] **BCP Vendor Overview** (`/bcp/vendor-overview/:vendorId`)
  - Can only view tenant's vendors
  - **API Endpoint**: Check vendor overview endpoints

- [ ] **BCP KPI Dashboard** (`/bcp/kpi-dashboard` or `/tprm/bcp/kpi-dashboard`)
  - KPIs show only tenant's plans
  - **API Endpoint**: Check BCP KPI endpoints

- [ ] **BCP Risk Analytics** (`/bcp/risk-analytics` or `/tprm/bcp/risk-analytics`)
  - Risk data shows only tenant's plans
  - **API Endpoint**: Check risk analytics endpoints

---

## 6. ✅ Compliance Module

- [ ] **Compliance Frameworks List** (Check compliance routes)
  - Shows only tenant's frameworks
  - Different count for each tenant
  - **API Endpoint**: `GET /api/tprm/compliance/frameworks/`

- [ ] **Framework Details** (Access via compliance list)
  - Can only view own tenant's frameworks
  - 404/403 for other tenant's frameworks
  - **API Endpoint**: `GET /api/tprm/compliance/frameworks/{id}/`

- [ ] **Create Framework** (Check compliance create route)
  - New framework assigned to correct tenant
  - Appears only for creating tenant
  - **API Endpoint**: `POST /api/tprm/compliance/frameworks/`

- [ ] **Compliance Reports** (Check compliance reports route)
  - Reports contain only tenant's data
  - **API Endpoint**: Check compliance report endpoints

- [ ] **Compliance Dashboard** (Check compliance dashboard route)
  - Statistics show only tenant's compliance data
  - **API Endpoint**: Check compliance dashboard endpoints

---

## 7. ✅ Risk Analysis Module

- [ ] **Risk Assessments List** (Check risk analysis routes)
  - Shows only tenant's risk assessments
  - Different count for each tenant
  - **API Endpoint**: `GET /api/tprm/risk-analysis/risks/`

- [ ] **Risk Assessment Details** (Access via risk list)
  - Can only view own tenant's assessments
  - 404/403 for other tenant's assessments
  - **API Endpoint**: `GET /api/tprm/risk-analysis/risks/{id}/`

- [ ] **Create Risk Assessment** (Check risk create route)
  - New assessment assigned to correct tenant
  - Appears only for creating tenant
  - **API Endpoint**: `POST /api/tprm/risk-analysis/risks/`

- [ ] **Risk Dashboard** (Check risk dashboard route)
  - Statistics show only tenant's risks
  - Risk scores are tenant-specific
  - **API Endpoint**: Check risk dashboard endpoints

- [ ] **Risk Mitigation Plans** (Check risk mitigation routes)
  - Plans show only tenant's risks
  - **API Endpoint**: Check risk mitigation endpoints

---

## 8. ✅ Audits Module

- [ ] **Audit Dashboard** (`/audit/dashboard` or `/tprm/audit/dashboard`)
  - Statistics show only tenant's audits
  - Audit results are tenant-specific
  - **API Endpoint**: Check audit dashboard endpoints

- [ ] **Audits List** (`/audit` or `/tprm/audit`)
  - Shows only tenant's audits
  - Different count for each tenant
  - **API Endpoint**: `GET /api/tprm/audits/audits/`

- [ ] **My Audits** (`/audit/my-audits` or `/tprm/audit/my-audits`)
  - Shows only tenant's audits assigned to user
  - **API Endpoint**: Check my audits endpoints

- [ ] **Create Audit** (`/audit/create` or `/tprm/audit/create`)
  - New audit assigned to correct tenant
  - Appears only for creating tenant
  - **API Endpoint**: `POST /api/tprm/audits/audits/`

- [ ] **Audit Execution** (`/audit/:auditId` or `/tprm/audit/:auditId`)
  - Can only execute own tenant's audits
  - 404/403 for other tenant's audits
  - **API Endpoint**: `GET /api/tprm/audits/audits/{id}/`

- [ ] **Audit Review** (`/audit/:auditId/review` or `/tprm/audit/:auditId/review`)
  - Can only review own tenant's audits
  - **API Endpoint**: Check audit review endpoints

- [ ] **Audit Reports** (`/audit/reports` or `/tprm/audit/reports`)
  - Reports contain only tenant's audits
  - **API Endpoint**: Check audit report endpoints

---

## 9. ✅ Contract Audits Module

- [ ] **Contract Audits List** (`/contract-audit/all` or `/tprm/contract-audit/all`)
  - Shows only tenant's contract audits
  - Different count for each tenant
  - **API Endpoint**: `GET /api/tprm/audits-contract/contract-audits/`

- [ ] **Contract Audit Dashboard** (Check contract audit dashboard route)
  - Statistics show only tenant's contract audits
  - **API Endpoint**: Check contract audit dashboard endpoints

- [ ] **Create Contract Audit** (`/contract-audit/create` or `/tprm/contract-audit/create`)
  - New audit assigned to correct tenant
  - **API Endpoint**: `POST /api/tprm/audits-contract/contract-audits/`

- [ ] **Contract Audit Execution** (`/contract-audit/:auditId/execute`)
  - Can only execute own tenant's contract audits
  - 404/403 for other tenant's audits
  - **API Endpoint**: Check contract audit execution endpoints

- [ ] **Contract Audit Review** (`/contract-audit/:auditId/review`)
  - Can only review own tenant's contract audits
  - **API Endpoint**: Check contract audit review endpoints

- [ ] **Contract Audit Reports** (`/contract-audit/reports` or `/tprm/contract-audit/reports`)
  - Reports contain only tenant's contract audits
  - **API Endpoint**: Check contract audit report endpoints

---

## 10. ✅ Contract Risk Analysis Module

- [ ] **Contract Risk Analysis List** (Check contract risk routes)
  - Shows only tenant's contract risk analyses
  - Different count for each tenant
  - **API Endpoint**: `GET /api/tprm/contract-risk-analysis/risks/`

- [ ] **Risk Analysis Details** (Access via risk list)
  - Can only view own tenant's analyses
  - 404/403 for other tenant's analyses
  - **API Endpoint**: `GET /api/tprm/contract-risk-analysis/risks/{id}/`

- [ ] **Create Risk Analysis** (Check contract risk create route)
  - New analysis assigned to correct tenant
  - **API Endpoint**: `POST /api/tprm/contract-risk-analysis/risks/`

- [ ] **Contract Risk Dashboard** (Check contract risk dashboard route)
  - Statistics show only tenant's contract risks
  - **API Endpoint**: Check contract risk dashboard endpoints

---

## 11. ✅ Global Search Module

- [ ] **Global Search Results** (Check global search functionality)
  - Search returns only tenant's data
  - Cannot find other tenant's records
  - Search across all modules is tenant-filtered
  - **API Endpoint**: `GET /api/tprm/global-search/search/`
  - **Test**: Search for records created in Tenant 1, verify Tenant 2 cannot find them

---

## 12. ✅ Notifications Module

- [ ] **Notifications List** (`/notifications` or `/tprm/notifications`)
  - Shows only tenant's notifications
  - Different notifications for each tenant
  - **API Endpoint**: `GET /api/tprm/notifications/notifications/`
  - **Test**: Create notification in Tenant 1, verify Tenant 2 doesn't see it

- [ ] **Notification Details** (Access via notifications list)
  - Can only view own tenant's notifications
  - **API Endpoint**: `GET /api/tprm/notifications/notifications/{id}/`

---

## 13. ✅ Quick Access Module

- [ ] **Quick Access Dashboard** (`/quick-access` or `/tprm/quick-access`)
  - Shows only tenant's quick access items
  - Different items for each tenant
  - **API Endpoint**: `GET /api/tprm/quick-access/quick-access-items/`
  - **Test**: Create quick access item in Tenant 1, verify Tenant 2 doesn't see it

---

## 14. ✅ OCR Module

- [ ] **OCR Processing** (Check OCR routes)
  - OCR results are tenant-specific
  - Documents processed are tenant-filtered
  - **API Endpoint**: Check OCR processing endpoints
  - **Test**: Upload document in Tenant 1, verify Tenant 2 cannot access extracted data

---

## 🔍 Common Checks for ALL Modules

### **List/Index Pages**
- [ ] Different record counts for each tenant
- [ ] Different records (no overlap)
- [ ] Search/filter works within tenant only
- [ ] Pagination shows only tenant's records

### **Detail/View Pages**
- [ ] Can view own tenant's records ✅
- [ ] Cannot view other tenant's records (404/403) ✅
- [ ] Direct ID access blocked for other tenants

### **Create Pages**
- [ ] New records assigned to correct tenant
- [ ] Created records appear only for creating tenant
- [ ] Cannot create records for other tenants

### **Edit/Update Pages**
- [ ] Can edit own tenant's records ✅
- [ ] Cannot edit other tenant's records (404/403) ✅
- [ ] Updates affect only tenant's records

### **Delete Operations**
- [ ] Can delete own tenant's records ✅
- [ ] Cannot delete other tenant's records (404/403) ✅

### **Dashboards & Analytics**
- [ ] Statistics show only tenant's data
- [ ] Charts/graphs reflect tenant-specific metrics
- [ ] KPIs are tenant-specific
- [ ] Reports contain only tenant's data

### **File/Document Operations**
- [ ] Can download own tenant's files ✅
- [ ] Cannot download other tenant's files (404/403) ✅
- [ ] Uploads are assigned to correct tenant

### **Search & Filter**
- [ ] Search finds only tenant's records
- [ ] Filters work within tenant scope
- [ ] Cannot find other tenant's records

---

## 🚨 Critical Security Checks

### **Direct ID Access**
- [ ] Try accessing other tenant's record by ID directly
- [ ] Should get 404 or 403 error
- [ ] Should NOT be able to view/edit/delete

### **API Endpoint Testing**
- [ ] Check Network tab in DevTools
- [ ] Verify API responses contain only tenant's data
- [ ] Verify JWT token includes `tenant_id`
- [ ] Verify backend logs show tenant filtering

### **Cross-Tenant Data Leakage**
- [ ] Create record in Tenant 1
- [ ] Login as Tenant 2
- [ ] Verify Tenant 2 cannot see Tenant 1's record
- [ ] Try direct ID access - should fail

---

## 📊 Testing Matrix

| Module | List Page | Detail Page | Create | Edit | Delete | Dashboard | Search |
|--------|-----------|-------------|--------|------|--------|-----------|--------|
| RFP | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Vendor | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Contracts | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| SLA | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| BCP/DRP | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Compliance | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Risk Analysis | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Audits | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

**Legend:**
- ⬜ = Not tested
- ✅ = Passed (tenant isolation working)
- ❌ = Failed (tenant isolation broken)

---

## 🔧 Quick Test Script

### Step 1: Prepare Test Data
1. Login as **Tenant 1 Admin**
2. Create test records in each module:
   - "Tenant 1 Test RFP"
   - "Tenant 1 Test Vendor"
   - "Tenant 1 Test Contract"
   - etc.

### Step 2: Verify Tenant 1 Isolation
1. Stay logged in as Tenant 1
2. Verify all test records are visible
3. Note the counts

### Step 3: Test Tenant 2
1. **Logout**
2. Login as **Tenant 2 Admin**
3. **Verify**:
   - Tenant 1's test records are **NOT** visible
   - Different counts
   - Can create own records

### Step 4: Cross-Tenant Access Test
1. As Tenant 2, try to access Tenant 1's record by direct ID
2. Should get **404** or **403** error
3. Should **NOT** be able to view/edit/delete

---

## 📝 Notes

- Test with at least **2 different tenants**
- Use **different browsers** or **incognito mode** for parallel testing
- Check **browser console** for errors
- Check **Network tab** for API responses
- Check **backend logs** for tenant filtering messages

---

## ✅ Sign-Off

After completing all checks:

- [ ] All modules tested
- [ ] All pages verified
- [ ] No cross-tenant data leakage
- [ ] All security checks passed
- [ ] Documentation updated

**Tested by:** _________________  
**Date:** _________________  
**Tenants Tested:** Tenant 1 (ID: ___), Tenant 2 (ID: ___)

---

**Remember**: Multi-tenancy is a **security feature**. Any failure should be reported immediately!

