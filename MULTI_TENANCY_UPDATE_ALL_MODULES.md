# Multi-Tenancy Update Guide for ALL Modules

## 📊 Scope
- **Policy Module**: 78 functions across 7 files
- **Compliance Module**: 50+ functions across 6 files  
- **Audit Module**: 100+ functions across 15+ files
- **Incident Module**: 80+ functions across 8 files
- **Risk Module**: 60+ functions across 10+ files
- **EventHandling Module**: 40+ functions across 3 files

**Total**: ~400+ functions to update

---

## 🎯 Update Pattern (Apply to ALL Functions)

### Step 1: Add Imports (Top of Each File)
```python
# MULTI-TENANCY: Import tenant utilities for data isolation
from ...tenant_utils import (
    require_tenant, tenant_filter, get_tenant_id_from_request,
    validate_tenant_access, get_tenant_aware_queryset
)
```

### Step 2: Add Decorators to ALL @api_view Functions
```python
# BEFORE:
@api_view(['GET'])
@permission_classes([SomePermission])
def my_function(request):
    pass

# AFTER:
@api_view(['GET'])
@permission_classes([SomePermission])
@require_tenant  # ✅ ADD THIS
@tenant_filter   # ✅ ADD THIS
def my_function(request):
    """MULTI-TENANCY: Only returns data for user's tenant"""  # ✅ ADD TO DOCSTRING
    pass
```

### Step 3: Add tenant_id Extraction
```python
# At the start of the function:
tenant_id = get_tenant_id_from_request(request)
```

### Step 4: Update ALL Database Queries

#### Pattern 1: Simple Queries
```python
# BEFORE:
objects = Model.objects.all()
objects = Model.objects.filter(some_field=value)

# AFTER:
objects = Model.objects.filter(tenant_id=tenant_id)
objects = Model.objects.filter(some_field=value, tenant_id=tenant_id)
```

#### Pattern 2: Related Queries
```python
# BEFORE:
policies = Policy.objects.filter(FrameworkId=framework)
subpolicies = SubPolicy.objects.filter(PolicyId=policy)

# AFTER:
policies = Policy.objects.filter(FrameworkId=framework, tenant_id=tenant_id)
subpolicies = SubPolicy.objects.filter(PolicyId=policy, tenant_id=tenant_id)
```

#### Pattern 3: User Queries
```python
# BEFORE:
users = Users.objects.all()
user = Users.objects.get(UserId=user_id)

# AFTER:
users = Users.objects.filter(tenant_id=tenant_id)
user = Users.objects.get(UserId=user_id, tenant_id=tenant_id)
```

### Step 5: Add Validation for Write Operations
```python
# For GET by ID:
@api_view(['GET'])
@require_tenant
@tenant_filter
def get_policy(request, policy_id):
    tenant_id = get_tenant_id_from_request(request)
    policy = Policy.objects.get(PolicyId=policy_id, tenant_id=tenant_id)  # ✅ Filter by tenant
    # ...

# For UPDATE/DELETE:
@api_view(['PUT', 'DELETE'])
@require_tenant
@tenant_filter  
def update_policy(request, policy_id):
    tenant_id = get_tenant_id_from_request(request)
    policy = Policy.objects.get(PolicyId=policy_id)
    
    # ✅ Validate tenant access
    if not validate_tenant_access(request, policy):
        return Response(
            {"error": "Access denied. Policy does not belong to your organization."},
            status=status.HTTP_403_FORBIDDEN
        )
    # ... rest of update logic
```

---

## 📝 Specific Updates by Module

### Policy Module

#### Files to Update:
1. ✅ `policy.py` - 78 functions (IN PROGRESS)
2. `policy_views.py` - 2-3 functions
3. `policy_version.py` - 15-20 functions
4. `policy_acknowledgement.py` - 10-15 functions
5. `public_acknowledgement.py` - 5-10 functions
6. `homePolices.py` - 5-10 functions
7. `framework_filter_helper.py` - 2-3 functions

#### Common Models in Policy:
- Framework (has tenant field)
- Policy (has tenant field)
- SubPolicy (has tenant field)
- PolicyApproval (Framework has tenant)
- PolicyVersion (Policy has tenant)
- Users (has tenant field)

#### Update ALL queries:
```python
# Framework queries:
Framework.objects.filter(tenant_id=tenant_id)

# Policy queries:
Policy.objects.filter(tenant_id=tenant_id)
Policy.objects.filter(FrameworkId=framework, tenant_id=tenant_id)

# SubPolicy queries:
SubPolicy.objects.filter(tenant_id=tenant_id)
SubPolicy.objects.filter(PolicyId=policy, tenant_id=tenant_id)

# User queries:
Users.objects.filter(tenant_id=tenant_id)
```

---

### Compliance Module

#### Files to Update:
1. `compliance_views.py` - 50+ functions
2. `compliance.py` - 10-15 functions
3. `organizational_controls.py` - 15-20 functions
4. `export_compliance.py` - 5 functions
5. `cross_framework_mapping_views.py` - 8-10 functions
6. `cross_framework_mapping_service.py` - 5-10 functions

#### Common Models in Compliance:
- Compliance (has tenant field)
- Framework (has tenant field)
- Policy (has tenant field)
- Users (has tenant field)

#### Update ALL queries:
```python
# Compliance queries:
Compliance.objects.filter(tenant_id=tenant_id)

# Related queries:
Framework.objects.filter(tenant_id=tenant_id)
Policy.objects.filter(tenant_id=tenant_id)
```

---

### Audit Module

#### Files to Update:
1. `audit_views.py` - 40+ functions
2. `auditing.py` - 15-20 functions
3. `assign_audit.py` - 20-25 functions
4. `reviewing.py` - 20-25 functions
5. `ai_audit_api.py` - 50+ functions
6. `report_views.py` - 10-15 functions
7. `report_utils.py` - Helper functions
8. `kpi_functions.py` - 30+ functions
9. And more...

#### Common Models in Audit:
- Audit (has tenant field)
- Compliance (has tenant field)
- Users (has tenant field)

#### Update ALL queries:
```python
# Audit queries:
Audit.objects.filter(tenant_id=tenant_id)

# Related queries:
Compliance.objects.filter(tenant_id=tenant_id)
```

---

### Incident Module

#### Files to Update:
1. `incident_views.py` - 60+ functions
2. `kpis_incidents.py` - 20+ functions
3. `incident_test.py` - Test functions
4. `incident_slm.py` - 5-10 functions
5. `incident_ai_import.py` - 15-20 functions

#### Common Models in Incident:
- Incident (has tenant field)
- Users (has tenant field)

#### Update ALL queries:
```python
# Incident queries:
Incident.objects.filter(tenant_id=tenant_id)
```

---

### Risk Module

#### Files to Update:
1. `risk_views.py` - 35+ functions
2. `risk_kpi.py` - 25+ functions
3. `risk_instance_ai.py` - 15-20 functions
4. `risk_ai_doc.py` - 15-20 functions
5. `risk_ai_doc_optimized.py` - 10-15 functions
6. `slm_service.py` - 5-10 functions
7. `risk_validation.py` - 3-5 functions
8. `risk_dashboard_filter.py` - 5-10 functions
9. `previous_version.py` - 3-5 functions

#### Common Models in Risk:
- Risk (has tenant field)
- RiskInstance (has tenant field)
- Compliance (has tenant field)
- Users (has tenant field)

#### Update ALL queries:
```python
# Risk queries:
Risk.objects.filter(tenant_id=tenant_id)
RiskInstance.objects.filter(tenant_id=tenant_id)
```

---

### EventHandling Module

#### Files to Update:
1. `event_views.py` - 30+ functions
2. `riskavaire_integration.py` - 10-15 functions
3. `urls.py` - No functions, just URL patterns

#### Common Models in EventHandling:
- Event (has tenant field)
- Users (has tenant field)

#### Update ALL queries:
```python
# Event queries:
Event.objects.filter(tenant_id=tenant_id)
```

---

## 🔍 Search Patterns to Find and Replace

### Find ALL Function Definitions:
```regex
^def \w+\(request
```

### Find ALL API Views:
```regex
^@api_view\(
```

### Find ALL Model Queries (to update):
```regex
\.objects\.all\(\)
\.objects\.filter\(
\.objects\.get\(
```

---

## ✅ Verification Checklist

After updating each file:
- [ ] Imports added at top
- [ ] ALL @api_view functions have @require_tenant and @tenant_filter
- [ ] ALL Model.objects queries include tenant_id filter
- [ ] ALL write operations (PUT/DELETE/POST with ID) have validate_tenant_access()
- [ ] Users queries include tenant_id
- [ ] Related model queries (Policy.objects.filter(FrameworkId=...)) include tenant_id
- [ ] No linter errors

---

## 🚨 Common Mistakes to Avoid

1. **Forgetting related queries**:
   ```python
   # ❌ WRONG:
   policies = Policy.objects.filter(FrameworkId=framework)
   
   # ✅ CORRECT:
   policies = Policy.objects.filter(FrameworkId=framework, tenant_id=tenant_id)
   ```

2. **Forgetting User queries**:
   ```python
   # ❌ WRONG:
   user = Users.objects.get(UserId=user_id)
   
   # ✅ CORRECT:
   user = Users.objects.get(UserId=user_id, tenant_id=tenant_id)
   ```

3. **Not validating write operations**:
   ```python
   # ❌ WRONG:
   @api_view(['PUT'])
   def update_policy(request, policy_id):
       policy = Policy.objects.get(PolicyId=policy_id)
       # Missing tenant validation!
   
   # ✅ CORRECT:
   @api_view(['PUT'])
   @require_tenant
   @tenant_filter
   def update_policy(request, policy_id):
       policy = Policy.objects.get(PolicyId=policy_id)
       if not validate_tenant_access(request, policy):
           return Response({"error": "Access denied"}, status=403)
   ```

4. **Forgetting decorators**:
   ```python
   # ❌ WRONG:
   @api_view(['GET'])
   def get_policies(request):
       pass
   
   # ✅ CORRECT:
   @api_view(['GET'])
   @require_tenant
   @tenant_filter
   def get_policies(request):
       tenant_id = get_tenant_id_from_request(request)
       pass
   ```

---

## 📊 Progress Tracking

| Module | Files | Functions | Status |
|--------|-------|-----------|--------|
| Framework | 1 | 35 | ✅ DONE |
| **Policy** | 7 | 78+ | 🔄 IN PROGRESS |
| Compliance | 6 | 50+ | ⏳ PENDING |
| Audit | 15+ | 100+ | ⏳ PENDING |
| Incident | 8 | 80+ | ⏳ PENDING |
| Risk | 10+ | 60+ | ⏳ PENDING |
| EventHandling | 3 | 40+ | ⏳ PENDING |
| **TOTAL** | **50+** | **443+** | **2% DONE** |

---

## 🎯 Execution Strategy

Due to the massive scale (~400+ functions), the update will be done in phases:

### Phase 1: Critical Functions (Data Retrieval)
- GET endpoints for listing/viewing data
- Most used by frontend

### Phase 2: Write Operations  
- POST/PUT/DELETE endpoints
- Require validation checks

### Phase 3: Helper Functions
- Utility functions
- Background tasks

### Estimated Time:
- **Automated**: Would take 2-3 hours with scripts
- **Manual**: Would take 20-40 hours
- **Hybrid Approach** (using patterns and batch updates): 4-8 hours

---

## 💡 Recommendation

Given the scale, I recommend:
1. ✅ Continue with systematic batch updates
2. ✅ Focus on critical modules first (Policy, Compliance, Audit)
3. ✅ Use search/replace patterns for efficiency
4. ✅ Test after each module is complete

Let's continue! 🚀

