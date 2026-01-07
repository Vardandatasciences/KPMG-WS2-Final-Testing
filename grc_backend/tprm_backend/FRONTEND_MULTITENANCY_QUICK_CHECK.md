# Frontend Multitenancy Quick Check Guide

## ⚡ Quick 5-Minute Test

### Step 1: Login as Tenant 1 User
1. Login to application
2. Go to **RFP List** page
3. **Count** how many RFPs you see (e.g., "5 RFPs")
4. **Note** one RFP title (e.g., "Q1 2024 RFP")

### Step 2: Login as Tenant 2 User
1. **Logout** from Tenant 1
2. **Login** as Tenant 2 user
3. Go to **RFP List** page
4. **Compare**:
   - ✅ **PASS**: Different count, different RFPs
   - ❌ **FAIL**: Same count, same RFPs (multitenancy broken!)

### Step 3: Create Test Record
1. As **Tenant 1**: Create "Tenant 1 Test RFP"
2. **Logout** and **Login** as **Tenant 2**
3. Check RFP list
4. ✅ **PASS**: "Tenant 1 Test RFP" should **NOT** appear
5. ❌ **FAIL**: If it appears, multitenancy broken!

---

## 🔍 Browser DevTools Quick Check

### Check Network Request

1. Open DevTools (`F12`)
2. Go to **Network** tab
3. Login and navigate to any module
4. Find API request (e.g., `/api/rfp/`)
5. Click request → Check **Response** tab
6. Verify data belongs to your tenant only

### Check JWT Token

1. In Network tab, find any authenticated request
2. Click request → **Headers** tab
3. Find `Authorization: Bearer <token>`
4. Copy token and decode at [jwt.io](https://jwt.io)
5. Verify token contains `tenant_id` field

---

## ✅ Checklist (Check All Modules)

Test each module with 2 different tenants:

- [ ] **RFP Module**: Different RFPs for each tenant
- [ ] **Vendor Module**: Different vendors for each tenant
- [ ] **Contracts Module**: Different contracts for each tenant
- [ ] **SLA Module**: Different SLAs for each tenant
- [ ] **BCP/DRP Module**: Different plans for each tenant
- [ ] **Compliance Module**: Different frameworks for each tenant
- [ ] **Risk Analysis**: Different risks for each tenant

---

## 🚨 Red Flags (Multitenancy NOT Working)

If you see any of these, **STOP** and report the issue:

1. ❌ **Same data for all tenants** - All users see identical lists
2. ❌ **Can access other tenant's records** - Direct ID access works
3. ❌ **Cross-tenant search results** - Search finds other tenant's data
4. ❌ **Shared statistics** - Dashboards show same numbers
5. ❌ **No 403/404 errors** - Accessing other tenant's data succeeds

---

## 📊 Expected Results

### ✅ Working Correctly

| Action | Tenant 1 | Tenant 2 |
|--------|----------|----------|
| RFP List | 5 RFPs | 3 RFPs (different) |
| Vendor List | 10 Vendors | 7 Vendors (different) |
| Create RFP | Appears for Tenant 1 only | Appears for Tenant 2 only |
| Access RFP ID 100 | ✅ Works (if Tenant 1's) | ❌ 404 (if Tenant 1's) |
| Search "Test" | Finds Tenant 1's only | Finds Tenant 2's only |

### ❌ NOT Working (Security Risk!)

| Action | Tenant 1 | Tenant 2 |
|--------|----------|----------|
| RFP List | 5 RFPs | 5 RFPs (same!) |
| Vendor List | 10 Vendors | 10 Vendors (same!) |
| Create RFP | Appears for both | Appears for both |
| Access RFP ID 100 | ✅ Works | ✅ Works (should fail!) |
| Search "Test" | Finds all tenants | Finds all tenants |

---

## 🔧 Quick Troubleshooting

### Problem: Both tenants see same data

**Check**:
1. Browser console for errors
2. Network request - JWT token has `tenant_id`?
3. Database - records have `TenantId` set?

### Problem: Cannot create records

**Check**:
1. Browser console - 403 errors?
2. Network request - Authorization header present?
3. JWT token valid and includes `tenant_id`?

### Problem: Records created but wrong tenant

**Check**:
1. Database - `TenantId` column value
2. JWT token - correct `tenant_id` in payload?

---

## 📱 Mobile App Testing

Same principles apply:

1. Login as Tenant 1 → Check data
2. Logout → Login as Tenant 2 → Check data
3. Verify different data for each tenant
4. Create records and verify isolation

---

## 🎯 Key Points to Remember

1. **Each tenant = Separate organization**
2. **Data must be isolated** - No sharing between tenants
3. **Security critical** - Data leak = Security breach
4. **Test with 2+ tenants** - Always verify isolation
5. **Check all modules** - RFP, Vendor, Contracts, SLA, BCP/DRP, Compliance, Risk

---

## 📞 Need Help?

If multitenancy is not working:

1. Check detailed guide: `HOW_TO_CHECK_MULTITENANCY_FROM_FRONTEND.md`
2. Check backend logs for tenant-related errors
3. Verify JWT token includes `tenant_id`
4. Check database `TenantId` column values
5. Contact development team with:
   - Screenshots of issue
   - Browser console errors
   - Network request details
   - Tenant IDs being tested

---

**Remember**: Multitenancy is a **security feature**. If broken, **report immediately**!

