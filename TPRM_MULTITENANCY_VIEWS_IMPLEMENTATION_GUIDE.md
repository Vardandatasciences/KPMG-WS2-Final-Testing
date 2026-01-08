# TPRM Multitenancy Views Implementation Guide

This guide provides step-by-step instructions for adding tenant filtering to all TPRM views.

## ✅ Completed Modules

1. **RFP Module** - Partially completed
   - ✅ RFPViewSet - `get_queryset()` uses `get_tenant_aware_queryset()`
   - ✅ RFPViewSet - `create()` and `perform_create()` set `tenant_id`
   - ✅ RFPEvaluationCriteriaViewSet - `get_queryset()` filters by tenant
   - ✅ RFPEvaluationCriteriaViewSet - `perform_create()` sets `tenant_id`
   - ✅ RFPTypeCustomFieldsViewSet - `get_queryset()` filters by tenant
   - ✅ `get_primary_contacts()` - Added decorators and tenant filtering
   - ⚠️ Other `@api_view` functions in RFP module still need updates

2. **Contracts Module** - Partially completed
   - ✅ `contract_list()` - Added decorators and tenant filtering
   - ✅ `contract_create()` - Added decorators and tenant_id assignment
   - ✅ `contract_detail()` - Added decorators and tenant filtering
   - ✅ `contract_comprehensive_detail()` - Added decorators and tenant filtering
   - ✅ `contract_update()` - Added decorators and tenant filtering
   - ⚠️ `contract_delete()`, `contract_archive()`, `contract_restore()`, and other functions still need updates

---

## Implementation Pattern

### Step 1: Import Tenant Utilities

Add these imports at the top of your views file:

```python
# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    filter_queryset_by_tenant,
    get_tenant_aware_queryset,
    require_tenant,
    tenant_filter
)
```

### Step 2: Add Decorators to @api_view Functions

For all `@api_view` functions, add the tenant decorators:

```python
@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_xxx_required('permission_name')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def my_view(request, ...):
    """View description
    MULTI-TENANCY: Only returns data belonging to the tenant
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'success': False,
            'error': 'Tenant context not found'
        }, status=403)
    
    # Your existing code...
```

### Step 3: Update ViewSets

For ViewSets, update `get_queryset()` and `perform_create()`:

```python
class MyViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    
    def get_queryset(self):
        """
        Filter by tenant
        MULTI-TENANCY: Only returns records belonging to the tenant
        """
        # MULTI-TENANCY: Filter by tenant
        return get_tenant_aware_queryset(MyModel, self.request)
    
    def perform_create(self, serializer):
        """
        Set tenant_id when creating records
        MULTI-TENANCY: Automatically assigns tenant_id
        """
        # MULTI-TENANCY: Get tenant_id from request
        tenant_id = get_tenant_id_from_request(self.request)
        serializer.save(tenant_id=tenant_id)
```

### Step 4: Update Queries

Update all queries to filter by `tenant_id`:

```python
# ❌ Bad - Returns all tenants' data
queryset = MyModel.objects.all()

# ✅ Good - Filters by tenant
tenant_id = get_tenant_id_from_request(request)
queryset = MyModel.objects.filter(tenant_id=tenant_id)
```

### Step 5: Update Raw SQL Queries

For raw SQL queries, add `WHERE TenantId = %s`:

```python
# ❌ Bad - No tenant filter
cursor.execute("""
    SELECT * FROM my_table
    WHERE status = 'active'
""")

# ✅ Good - Includes tenant filter
tenant_id = get_tenant_id_from_request(request)
cursor.execute("""
    SELECT * FROM my_table
    WHERE status = 'active'
    AND TenantId = %s
""", [tenant_id])
```

### Step 6: Update Create Operations

Ensure `tenant_id` is set when creating records:

```python
# Option 1: Set in serializer.save()
serializer.save(tenant_id=tenant_id)

# Option 2: Add to data before serialization
data = request.data.copy()
data['tenant_id'] = tenant_id
serializer = MySerializer(data=data)

# Option 3: Use TenantAwareModel (if model inherits from it)
# tenant_id will be auto-assigned from context
obj = MyModel.objects.create(...)
```

---

## Remaining Modules to Update

### Priority 1: Core Business Modules

#### 1. Contracts Module (`contracts/views.py`)
- [x] `contract_list()` ✅
- [x] `contract_create()` ✅
- [x] `contract_detail()` ✅
- [x] `contract_comprehensive_detail()` ✅
- [x] `contract_update()` ✅
- [ ] `contract_delete()` - Add decorators and tenant filter
- [ ] `contract_archive()` - Add decorators and tenant filter
- [ ] `contract_restore()` - Add decorators and tenant filter
- [ ] `contract_stats()` - Add decorators and tenant filter
- [ ] `contract_amendments_kpi()` - Add decorators and tenant filter
- [ ] `contracts_expiring_soon_kpi()` - Add decorators and tenant filter
- [ ] `average_contract_value_by_type_kpi()` - Add decorators and tenant filter
- [ ] All other contract-related functions

#### 2. RFP Module (`rfp/views.py`)
- [x] `RFPViewSet` ✅
- [x] `RFPEvaluationCriteriaViewSet` ✅
- [x] `RFPTypeCustomFieldsViewSet` ✅
- [x] `get_primary_contacts()` ✅
- [ ] `DocumentUploadView` - Add tenant filtering
- [ ] `MergeDocumentsView` - Add tenant filtering
- [ ] `AwardNotificationView` - Add tenant filtering
- [ ] `AwardResponseView` - Add tenant filtering
- [ ] `VendorCredentialsView` - Add tenant filtering
- [ ] `get_invitations_by_rfp()` - Add decorators and tenant filter
- [ ] `get_invitation_stats()` - Add decorators and tenant filter
- [ ] `create_vendor_invitations()` - Add decorators and tenant filter
- [ ] `send_vendor_invitations()` - Add decorators and tenant filter
- [ ] `acknowledge_invitation()` - Add decorators and tenant filter
- [ ] `decline_invitation()` - Add decorators and tenant filter
- [ ] `vendor_selection()` - Add decorators and tenant filter
- [ ] `vendor_manual_entry()` - Add decorators and tenant filter
- [ ] `vendor_bulk_upload()` - Add decorators and tenant filter
- [ ] All other RFP-related functions

#### 3. Vendor Module (`apps/vendor_core/views.py`)
- [ ] All ViewSets - Add `get_queryset()` with tenant filtering
- [ ] All `@api_view` functions - Add decorators and tenant filtering
- [ ] All create operations - Set `tenant_id`

#### 4. BCP/DRP Module (`bcpdrp/views.py`)
- [ ] All ViewSets - Add `get_queryset()` with tenant filtering
- [ ] All `@api_view` functions - Add decorators and tenant filtering
- [ ] All create operations - Set `tenant_id`

#### 5. SLA Module (`slas/views.py`)
- [ ] All ViewSets - Add `get_queryset()` with tenant filtering
- [ ] All `@api_view` functions - Add decorators and tenant filtering
- [ ] All create operations - Set `tenant_id`

### Priority 2: Supporting Modules

#### 6. Audits Module (`audits/views.py`)
- [ ] All ViewSets and functions - Add tenant filtering

#### 7. Compliance Module (`compliance/views.py`)
- [ ] All ViewSets and functions - Add tenant filtering

#### 8. Risk Analysis Module (`risk_analysis/views.py`)
- [ ] All ViewSets and functions - Add tenant filtering

#### 9. RFP Approval Module (`rfp_approval/views.py`)
- [ ] All ViewSets and functions - Add tenant filtering

#### 10. Other Modules
- [ ] `global_search/views.py`
- [ ] `notifications/views.py`
- [ ] `mfa_auth/views.py`
- [ ] `quick_access/views.py`
- [ ] `ocr_app/views.py`
- [ ] All vendor app modules (`apps/vendor_*`)

---

## Example: Complete Function Update

### Before (No Tenant Filtering):
```python
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
def contract_list(request):
    """List all contracts"""
    queryset = VendorContract.objects.all()
    # ... rest of code
```

### After (With Tenant Filtering):
```python
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_contract_required('ListContracts')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def contract_list(request):
    """List all contracts
    MULTI-TENANCY: Only returns contracts belonging to the tenant
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'success': False,
            'error': 'Tenant context not found'
        }, status=403)
    
    # MULTI-TENANCY: Filter by tenant_id
    queryset = VendorContract.objects.filter(tenant_id=tenant_id)
    # ... rest of code
```

---

## Testing Checklist

After updating each module, test:

1. **Tenant Isolation:**
   - [ ] Tenant 1 can only see Tenant 1's data
   - [ ] Tenant 2 can only see Tenant 2's data
   - [ ] Cross-tenant access returns 403/404

2. **Create Operations:**
   - [ ] New records get correct `tenant_id`
   - [ ] Records are associated with correct tenant

3. **Update Operations:**
   - [ ] Can only update own tenant's records
   - [ ] Cannot update other tenant's records

4. **Delete Operations:**
   - [ ] Can only delete own tenant's records
   - [ ] Cannot delete other tenant's records

5. **List Operations:**
   - [ ] Only returns records for current tenant
   - [ ] Counts are correct per tenant

---

## Quick Reference

### Decorators Order
```python
@api_view(['GET'])
@authentication_classes([...])
@permission_classes([...])
@rbac_xxx_required('permission')
@require_tenant  # Must be before @tenant_filter
@tenant_filter   # Must be after @require_tenant
def my_view(request):
    ...
```

### Get Tenant ID
```python
tenant_id = get_tenant_id_from_request(request)
if not tenant_id:
    return Response({'error': 'Tenant context not found'}, status=403)
```

### Filter QuerySet
```python
# Option 1: Using helper function
queryset = get_tenant_aware_queryset(MyModel, request)

# Option 2: Manual filtering
tenant_id = get_tenant_id_from_request(request)
queryset = MyModel.objects.filter(tenant_id=tenant_id)
```

### Set Tenant on Create
```python
# In serializer.save()
serializer.save(tenant_id=tenant_id)

# In data dict
data['tenant_id'] = tenant_id
```

### SQL Query Filter
```python
tenant_id = get_tenant_id_from_request(request)
cursor.execute("""
    SELECT * FROM my_table
    WHERE TenantId = %s
""", [tenant_id])
```

---

## Notes

1. **Decorator Order Matters:** `@require_tenant` must come before `@tenant_filter`
2. **Database Column Name:** Use `TenantId` (capital T) in SQL, `tenant_id` (lowercase) in Django ORM
3. **Null Checks:** Always check if `tenant_id` is `None` before using it
4. **Error Responses:** Return 403 for missing tenant context
5. **Testing:** Test with multiple tenants to verify isolation

---

**Last Updated:** 2025-01-XX  
**Status:** In Progress - Core modules partially complete

