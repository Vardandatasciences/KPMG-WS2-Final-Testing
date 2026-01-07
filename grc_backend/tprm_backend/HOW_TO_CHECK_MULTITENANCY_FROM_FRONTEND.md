# How to Check Multitenancy from Frontend Application

This guide explains how to verify that multitenancy is working correctly from the frontend application (user interface).

## 🎯 Overview

Multitenancy ensures that each organization (tenant) only sees and can access their own data. This guide shows you how to verify this from the browser/application interface.

## 📋 Prerequisites

1. **Multiple Tenants**: You need at least 2 tenants in the system
2. **Multiple Users**: At least 2 users, each belonging to different tenants
3. **Test Data**: Create some test data (RFPs, Vendors, Contracts, etc.) for each tenant
4. **Browser Tools**: Use browser DevTools to inspect network requests

## 🔍 Method 1: Visual Verification (Easiest)

### Step 1: Login as User from Tenant 1

1. Open the application in your browser
2. Login with a user account that belongs to **Tenant 1**
3. Navigate to different modules:
   - **RFP Module**: Go to RFP list page
   - **Vendor Module**: Go to Vendor list page
   - **Contracts Module**: Go to Contracts list page
   - **SLA Module**: Go to SLA list page
   - **BCP/DRP Module**: Go to Plans list page
   - **Compliance Module**: Go to Frameworks list page

4. **Note down the data you see**:
   - Count of records (e.g., "5 RFPs", "10 Vendors")
   - Specific record IDs or names
   - Any unique identifiers

### Step 2: Login as User from Tenant 2

1. **Logout** from Tenant 1 user account
2. **Login** with a user account that belongs to **Tenant 2**
3. Navigate to the **same modules** as Step 1
4. **Compare the data**:
   - ✅ **CORRECT**: You should see **DIFFERENT** data (different records, different counts)
   - ❌ **WRONG**: If you see the **SAME** data as Tenant 1, multitenancy is NOT working

### Step 3: Create New Records

1. While logged in as **Tenant 1** user:
   - Create a new RFP (e.g., "Tenant 1 Test RFP")
   - Create a new Vendor (e.g., "Tenant 1 Test Vendor")
   - Create a new Contract (e.g., "Tenant 1 Test Contract")

2. **Logout** and **Login** as **Tenant 2** user:
   - Check RFP list - You should **NOT** see "Tenant 1 Test RFP"
   - Check Vendor list - You should **NOT** see "Tenant 1 Test Vendor"
   - Check Contract list - You should **NOT** see "Tenant 1 Test Contract"

3. Create new records as **Tenant 2** user:
   - Create "Tenant 2 Test RFP"
   - Create "Tenant 2 Test Vendor"

4. **Logout** and **Login** back as **Tenant 1** user:
   - You should **NOT** see Tenant 2's records
   - You should **ONLY** see Tenant 1's records

## 🔍 Method 2: Browser DevTools Inspection (Advanced)

### Step 1: Open Browser DevTools

1. Open your browser (Chrome, Firefox, Edge)
2. Press `F12` or `Right-click → Inspect`
3. Go to **Network** tab
4. Make sure **Preserve log** is checked

### Step 2: Login and Capture API Requests

1. **Login** as Tenant 1 user
2. Navigate to a module (e.g., RFP list)
3. In Network tab, find the API request (e.g., `/api/rfp/` or `/api/tprm/rfp/`)
4. Click on the request to see details

### Step 3: Check Request Headers

Look at the **Request Headers** section:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

The JWT token should contain `tenant_id` in its payload. You can decode it at [jwt.io](https://jwt.io) to verify.

### Step 4: Check Response Data

Look at the **Response** section:

1. **Check the data returned**:
   ```json
   {
     "results": [
       {"rfp_id": 1, "rfp_title": "Tenant 1 RFP", ...},
       {"rfp_id": 2, "rfp_title": "Tenant 1 RFP 2", ...}
     ],
     "count": 2
   }
   ```

2. **Verify**:
   - All records should belong to Tenant 1
   - No records from other tenants should appear

### Step 5: Compare with Different Tenant

1. **Logout** and **Login** as Tenant 2 user
2. Make the **same API request** (e.g., `/api/rfp/`)
3. **Compare responses**:
   - ✅ **CORRECT**: Different records in response
   - ❌ **WRONG**: Same records as Tenant 1

## 🔍 Method 3: Database Verification (Most Reliable)

### Step 1: Check Database Directly

1. Connect to your database (MySQL/PostgreSQL)
2. Run these queries:

```sql
-- Check RFPs by tenant
SELECT TenantId, COUNT(*) as count, GROUP_CONCAT(rfp_title) as titles
FROM rfps
GROUP BY TenantId;

-- Check Vendors by tenant
SELECT TenantId, COUNT(*) as count
FROM vendors
GROUP BY TenantId;

-- Check Contracts by tenant
SELECT TenantId, COUNT(*) as count
FROM vendor_contracts
GROUP BY TenantId;

-- Check BCP/DRP Plans by tenant
SELECT TenantId, COUNT(*) as count
FROM bcp_drp_plans
GROUP BY TenantId;
```

### Step 2: Verify Tenant Isolation

- Each tenant should have their own records
- No records should have `TenantId = NULL` (unless intentionally allowed)
- Record counts should match what you see in the frontend

## 🧪 Test Scenarios

### Scenario 1: Data Isolation Test

**Objective**: Verify tenants cannot see each other's data

**Steps**:
1. Login as **Tenant 1 User**
2. Create 5 RFPs
3. Logout
4. Login as **Tenant 2 User**
5. Check RFP list - should see 0 RFPs (or only Tenant 2's RFPs)
6. ✅ **PASS**: Tenant 2 cannot see Tenant 1's RFPs

### Scenario 2: Cross-Tenant Access Prevention

**Objective**: Verify users cannot access other tenant's records by ID

**Steps**:
1. Login as **Tenant 1 User**
2. Create an RFP and note its ID (e.g., RFP ID = 100)
3. Logout
4. Login as **Tenant 2 User**
5. Try to access RFP ID 100 directly: `/api/rfp/100/`
6. ✅ **PASS**: Should return 404 Not Found or 403 Forbidden
7. ❌ **FAIL**: If RFP details are returned, multitenancy is broken

### Scenario 3: Create Record Test

**Objective**: Verify new records are assigned to correct tenant

**Steps**:
1. Login as **Tenant 1 User**
2. Create a new Vendor
3. Check database: `SELECT TenantId FROM vendors WHERE vendor_id = <new_id>`
4. ✅ **PASS**: `TenantId` should match Tenant 1's ID
5. ❌ **FAIL**: If `TenantId` is NULL or wrong tenant, multitenancy is broken

### Scenario 4: Search and Filter Test

**Objective**: Verify search/filter only returns tenant's data

**Steps**:
1. Login as **Tenant 1 User**
2. Create an RFP with title "Special Test RFP"
3. Logout
4. Login as **Tenant 2 User**
5. Search for "Special Test RFP"
6. ✅ **PASS**: Should return 0 results
7. ❌ **FAIL**: If Tenant 2 can find Tenant 1's RFP, multitenancy is broken

### Scenario 5: Dashboard/Statistics Test

**Objective**: Verify dashboards show only tenant's data

**Steps**:
1. Login as **Tenant 1 User**
2. Note dashboard statistics (e.g., "5 Active RFPs", "10 Vendors")
3. Logout
4. Login as **Tenant 2 User**
5. Check dashboard statistics
6. ✅ **PASS**: Should show different numbers (Tenant 2's data)
7. ❌ **FAIL**: If same statistics appear, multitenancy is broken

## 🔧 Troubleshooting

### Issue: Both tenants see the same data

**Possible Causes**:
1. JWT token doesn't include `tenant_id`
2. Middleware not extracting tenant from request
3. Views not filtering by `tenant_id`
4. User belongs to wrong tenant

**Solution**:
1. Check JWT token payload (decode at jwt.io)
2. Check browser console for errors
3. Check network requests - verify `tenant_id` is in request
4. Verify user's tenant assignment in database

### Issue: Cannot create records

**Possible Causes**:
1. `tenant_id` is NULL
2. `@require_tenant` decorator blocking request
3. Missing tenant context

**Solution**:
1. Check browser console for 403 errors
2. Verify JWT token includes `tenant_id`
3. Check network request - should have Authorization header

### Issue: Records created but belong to wrong tenant

**Possible Causes**:
1. `tenant_id` not set on object creation
2. Wrong tenant_id extracted from request

**Solution**:
1. Check database - verify `TenantId` column value
2. Check view code - ensure `tenant_id=tenant_id` in `create()` calls
3. Verify JWT token has correct `tenant_id`

## 📊 What to Check in Each Module

### RFP Module
- ✅ RFP list shows only tenant's RFPs
- ✅ Cannot access other tenant's RFP by ID
- ✅ New RFPs are assigned to correct tenant
- ✅ RFP search only finds tenant's RFPs
- ✅ RFP statistics show only tenant's data

### Vendor Module
- ✅ Vendor list shows only tenant's vendors
- ✅ Cannot access other tenant's vendor by ID
- ✅ New vendors are assigned to correct tenant
- ✅ Vendor screening results are tenant-scoped
- ✅ Vendor dashboard shows only tenant's metrics

### Contracts Module
- ✅ Contract list shows only tenant's contracts
- ✅ Cannot access other tenant's contract by ID
- ✅ New contracts are assigned to correct tenant
- ✅ Contract terms/clauses are tenant-scoped
- ✅ Contract statistics show only tenant's data

### SLA Module
- ✅ SLA list shows only tenant's SLAs
- ✅ Cannot access other tenant's SLA by ID
- ✅ New SLAs are assigned to correct tenant
- ✅ SLA metrics are tenant-scoped

### BCP/DRP Module
- ✅ Plans list shows only tenant's plans
- ✅ Cannot access other tenant's plan by ID
- ✅ New plans are assigned to correct tenant
- ✅ Questionnaires are tenant-scoped
- ✅ Evaluations are tenant-scoped

### Compliance Module
- ✅ Frameworks list shows only tenant's frameworks
- ✅ Cannot access other tenant's framework by ID
- ✅ New frameworks are assigned to correct tenant
- ✅ Compliance mappings are tenant-scoped

### Risk Analysis Modules
- ✅ Risks list shows only tenant's risks
- ✅ Cannot access other tenant's risk by ID
- ✅ New risks are assigned to correct tenant
- ✅ Risk statistics show only tenant's data

## 🎯 Quick Checklist

Use this checklist to verify multitenancy:

- [ ] Login as Tenant 1 → See Tenant 1's data only
- [ ] Login as Tenant 2 → See Tenant 2's data only (different from Tenant 1)
- [ ] Create record as Tenant 1 → Record appears only for Tenant 1
- [ ] Create record as Tenant 2 → Record appears only for Tenant 2
- [ ] Try to access Tenant 1's record ID as Tenant 2 → Should fail (404/403)
- [ ] Search as Tenant 1 → Only finds Tenant 1's records
- [ ] Search as Tenant 2 → Only finds Tenant 2's records
- [ ] Dashboard as Tenant 1 → Shows Tenant 1's statistics
- [ ] Dashboard as Tenant 2 → Shows Tenant 2's statistics (different)
- [ ] All modules (RFP, Vendor, Contracts, SLA, BCP/DRP, Compliance, Risk) → Tenant isolation working

## 🔐 Security Verification

### Test Unauthorized Access

1. **Get a record ID** from Tenant 1 (e.g., RFP ID = 100)
2. **Login as Tenant 2**
3. **Try to access** `/api/rfp/100/` directly
4. ✅ **Should return**: 404 Not Found or 403 Forbidden
5. ❌ **Should NOT return**: RFP details

### Test API Direct Access

1. **Get JWT token** for Tenant 1
2. **Modify request** to try accessing Tenant 2's data
3. ✅ **Should fail**: Even with valid token, cannot access other tenant's data

## 📝 Expected Behavior Summary

### ✅ Working Correctly

- Each tenant sees **ONLY** their own data
- Cannot access other tenant's records by ID
- New records are **automatically** assigned to correct tenant
- Search/filter returns **ONLY** tenant's data
- Statistics/dashboards show **ONLY** tenant's metrics
- API returns 403/404 when trying to access other tenant's data

### ❌ Not Working (Security Risk)

- All tenants see **ALL** data (no isolation)
- Can access other tenant's records by ID
- New records have `tenant_id = NULL`
- Search finds records from all tenants
- Statistics show data from all tenants
- API returns data from other tenants

## 🚨 Red Flags to Watch For

If you see any of these, multitenancy is **NOT** working:

1. **Same data for all tenants** - All users see identical lists
2. **Can access other tenant's records** - Direct ID access works across tenants
3. **NULL tenant_id** - New records have no tenant assignment
4. **Cross-tenant search results** - Search finds other tenant's records
5. **Shared statistics** - Dashboards show same numbers for all tenants
6. **No 403/404 errors** - Accessing other tenant's data succeeds

## 📞 Next Steps

If multitenancy is **NOT** working:

1. Check browser console for errors
2. Check network requests - verify `tenant_id` in JWT
3. Check database - verify `TenantId` column values
4. Review backend logs for tenant-related errors
5. Verify middleware is registered in `settings.py`
6. Check that views have `@require_tenant` decorator

## 🎓 Understanding the Flow

```
Frontend Request
    ↓
JWT Token (contains tenant_id)
    ↓
Backend Middleware (extracts tenant_id)
    ↓
View Function (filters by tenant_id)
    ↓
Database Query (WHERE TenantId = tenant_id)
    ↓
Response (only tenant's data)
    ↓
Frontend Display (tenant-specific data)
```

## 💡 Pro Tips

1. **Use Incognito/Private Browsing**: Test with multiple tenants simultaneously
2. **Browser Extensions**: Use REST client extensions to test API directly
3. **Database Monitoring**: Watch database queries in real-time
4. **Log Analysis**: Check backend logs for tenant filtering messages
5. **Automated Testing**: Create test scripts to verify tenant isolation

---

**Remember**: Multitenancy is a **security feature**. If it's not working, **data from one organization could leak to another organization** - this is a critical security issue!

