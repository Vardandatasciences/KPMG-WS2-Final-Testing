# Policy Module Multi-Tenancy Update Instructions

## Quick Reference for Manual Updates

### For EVERY function in Policy module, apply these changes:

### 1. Add Decorators (After @permission_classes):
```python
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
```

### 2. Add at start of function:
```python
tenant_id = get_tenant_id_from_request(request)
```

### 3. Update ALL queries in the function:

**Framework:**
- `Framework.objects.all()` → `Framework.objects.filter(tenant_id=tenant_id)`
- `Framework.objects.filter(...)` → `Framework.objects.filter(..., tenant_id=tenant_id)`
- `Framework.objects.get(pk=id)` → `Framework.objects.get(pk=id, tenant_id=tenant_id)`

**Policy:**
- `Policy.objects.all()` → `Policy.objects.filter(tenant_id=tenant_id)`
- `Policy.objects.filter(...)` → `Policy.objects.filter(..., tenant_id=tenant_id)`
- `Policy.objects.get(pk=id)` → `Policy.objects.get(pk=id, tenant_id=tenant_id)`

**SubPolicy:**
- `SubPolicy.objects.all()` → `SubPolicy.objects.filter(tenant_id=tenant_id)`
- `SubPolicy.objects.filter(...)` → `SubPolicy.objects.filter(..., tenant_id=tenant_id)`

**Users:**
- `Users.objects.filter(...)` → `Users.objects.filter(..., tenant_id=tenant_id)`
- `Users.objects.get(UserId=id)` → `Users.objects.get(UserId=id, tenant_id=tenant_id)`

**PolicyApproval** (related through Policy):
- `PolicyApproval.objects.filter(...)` → Add `PolicyId__tenant_id=tenant_id`

### 4. For UPDATE/DELETE operations, add validation:
```python
obj = Model.objects.get(pk=id)
if not validate_tenant_access(request, obj):
    return Response(
        {"error": "Access denied. Object does not belong to your organization."},
        status=status.HTTP_403_FORBIDDEN
    )
```

---

## I'll continue with systematic updates now...

