# Multi-Tenancy Implementation Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [Database Schema](#database-schema)
3. [Model Structure](#model-structure)
4. [Tenant ID Extraction](#tenant-id-extraction)
5. [Decorators](#decorators)
6. [Query Filtering](#query-filtering)
7. [Code Examples](#code-examples)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Multi-tenancy in this GRC platform ensures that each organization (tenant) can only access their own data. This is achieved by:

1. **Storing `TenantId` in every table** that needs tenant isolation
2. **Extracting `tenant_id` from authenticated user** on every request
3. **Filtering all database queries** by `tenant_id`
4. **Validating access** before allowing modifications

### Key Principle

> **Every database query MUST include `tenant_id` filtering to prevent cross-tenant data access.**

---

## Database Schema

### Tenant Table

```sql
CREATE TABLE tenant (
    TenantId INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(255),
    Subdomain VARCHAR(100) UNIQUE,
    LicenseKey VARCHAR(100) UNIQUE,
    SubscriptionTier VARCHAR(50),
    ...
);
```

### Tenant-Aware Tables

Every table that needs tenant isolation includes a `TenantId` column:

```sql
-- Example: frameworks table
CREATE TABLE frameworks (
    FrameworkId INT PRIMARY KEY,
    TenantId INT,  -- Foreign key to tenant table
    FrameworkName VARCHAR(255),
    ...
    FOREIGN KEY (TenantId) REFERENCES tenant(TenantId)
);

-- Example: policies table
CREATE TABLE policies (
    PolicyId INT PRIMARY KEY,
    TenantId INT,  -- Foreign key to tenant table
    PolicyName VARCHAR(255),
    ...
    FOREIGN KEY (TenantId) REFERENCES tenant(TenantId)
);
```

**Important**: The database column is `TenantId` (capital T), but Django ORM uses `tenant_id` (lowercase with underscore).

---

## Model Structure

### 1. Tenant Model

```python
class Tenant(models.Model):
    tenant_id = models.AutoField(primary_key=True, db_column='TenantId')
    name = models.CharField(max_length=255, db_column='Name')
    subdomain = models.CharField(max_length=100, unique=True, db_column='Subdomain')
    license_key = models.CharField(max_length=100, unique=True, null=True, db_column='LicenseKey')
    ...
```

### 2. TenantAwareModel (Abstract Base Class)

Models that need tenant isolation can inherit from `TenantAwareModel`:

```python
class TenantAwareModel(models.Model):
    """
    Abstract base model that automatically sets tenant_id when creating records.
    """
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Override save to automatically set tenant_id if not already set"""
        if hasattr(self, 'tenant') and self.tenant is None and self.pk is None:
            from .tenant_context import get_current_tenant
            tenant_id = get_current_tenant()
            if tenant_id:
                tenant = Tenant.objects.get(tenant_id=tenant_id)
                self.tenant = tenant
        super().save(*args, **kwargs)
```

### 3. Models with Tenant ForeignKey

All tenant-aware models have a ForeignKey to Tenant:

```python
class Framework(models.Model):
    FrameworkId = models.AutoField(primary_key=True)
    
    # MULTI-TENANCY: Link framework to tenant
    tenant = models.ForeignKey(
        'Tenant', 
        on_delete=models.CASCADE, 
        db_column='TenantId',
        related_name='frameworks',
        null=True,
        blank=True
    )
    FrameworkName = models.CharField(max_length=255)
    ...
```

**Note**: Django ORM uses `tenant_id` (lowercase) to access the ForeignKey ID, even though the database column is `TenantId`.

---

## Tenant ID Extraction

### Flow Diagram

```
Request → JWT Token/Session → Extract user_id → Lookup User → Get tenant_id → Set on request
```

### Step-by-Step Process

1. **User Authentication**
   - User logs in via `/api/jwt/login/` or `/api/login/`
   - JWT token is generated containing `user_id`
   - Token is stored in `Authorization: Bearer <token>` header

2. **Request Processing**
   - Request arrives at API endpoint
   - `@tenant_filter` decorator extracts `tenant_id`:
     - First, checks if `request.tenant` exists (set by middleware)
     - If not, extracts `user_id` from:
       - `request.user.UserId`
       - `request.user.id`
       - JWT token payload
     - Looks up user in database: `Users.objects.get(UserId=user_id)`
     - Gets `tenant_id` from user: `user.tenant_id` or `user.tenant.tenant_id`
     - Sets `request.tenant_id` for use in view

3. **Query Filtering**
   - View function uses `request.tenant_id` to filter queries
   - All queries include `.filter(tenant_id=tenant_id)`

### Code: Tenant ID Extraction

```python
# In tenant_utils.py - tenant_filter decorator
def tenant_filter(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if hasattr(request, 'tenant') and request.tenant:
            request.tenant_id = request.tenant.tenant_id
        else:
            # Extract user_id from request
            user_id = None
            if hasattr(request.user, 'UserId'):
                user_id = request.user.UserId
            elif hasattr(request.user, 'id'):
                user_id = request.user.id
            
            # Extract from JWT if available
            if not user_id:
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
                    payload = verify_jwt_token(token)
                    if payload and 'user_id' in payload:
                        user_id = payload['user_id']
            
            # Get tenant from user
            if user_id:
                user = Users.objects.get(UserId=user_id)
                tenant_id = user.tenant_id  # or user.tenant.tenant_id
                request.tenant_id = tenant_id
        
        return view_func(request, *args, **kwargs)
    return wrapper
```

---

## Decorators

### 1. `@require_tenant`

**Purpose**: Ensures that a tenant context exists before processing the request.

**Behavior**: Returns 403 error if tenant is not found.

```python
@require_tenant
@api_view(['GET'])
def my_view(request):
    # This code only runs if tenant exists
    tenant = request.tenant
    ...
```

**Implementation**:
```python
def require_tenant(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'tenant') or request.tenant is None:
            return JsonResponse({
                'error': 'Tenant context not found',
                'detail': 'This endpoint requires tenant authentication'
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper
```

### 2. `@tenant_filter`

**Purpose**: Automatically extracts `tenant_id` from the authenticated user and sets it on the request.

**Behavior**: 
- Extracts `user_id` from JWT token or request.user
- Looks up user in database
- Gets `tenant_id` from user
- Sets `request.tenant_id` for use in view

```python
@tenant_filter
@api_view(['GET'])
def list_frameworks(request):
    tenant_id = request.tenant_id  # Automatically set by decorator
    frameworks = Framework.objects.filter(tenant_id=tenant_id)
    ...
```

**Implementation**: See "Tenant ID Extraction" section above.

### 3. Combined Usage

**Always use both decorators together**:

```python
@require_tenant  # Ensures tenant exists
@tenant_filter   # Extracts and sets tenant_id
@api_view(['GET'])
def my_view(request):
    tenant_id = get_tenant_id_from_request(request)
    # Now you can safely filter by tenant_id
    ...
```

**Decorator Order**: `@require_tenant` should be **above** `@tenant_filter` in the decorator stack.

---

## Query Filtering

### Pattern 1: Direct Filtering (Most Common)

```python
@require_tenant
@tenant_filter
@api_view(['GET'])
def list_frameworks(request):
    tenant_id = get_tenant_id_from_request(request)
    
    # Filter by tenant_id
    frameworks = Framework.objects.filter(tenant_id=tenant_id)
    
    return Response(frameworks)
```

### Pattern 2: Using Helper Function

```python
from ...tenant_utils import get_tenant_aware_queryset

@require_tenant
@tenant_filter
@api_view(['GET'])
def list_frameworks(request):
    # Helper function automatically filters by tenant
    frameworks = get_tenant_aware_queryset(Framework, request)
    
    return Response(frameworks)
```

### Pattern 3: Filtering Existing QuerySet

```python
from ...tenant_utils import filter_queryset_by_tenant

@require_tenant
@tenant_filter
@api_view(['GET'])
def list_frameworks(request):
    tenant_id = get_tenant_id_from_request(request)
    
    # Start with base queryset
    frameworks = Framework.objects.all()
    
    # Apply tenant filter
    frameworks = filter_queryset_by_tenant(frameworks, tenant_id)
    
    return Response(frameworks)
```

### Pattern 4: Raw SQL Queries

**Important**: When using raw SQL, use `TenantId` (capital T) to match database column name.

```python
@require_tenant
@tenant_filter
@api_view(['GET'])
def get_audits(request):
    tenant_id = get_tenant_id_from_request(request)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM audit a
            WHERE a.TenantId = %s  -- Note: TenantId (capital T)
        """, [tenant_id])
        
        audits = cursor.fetchall()
    
    return Response(audits)
```

### Pattern 5: Creating New Records

```python
@require_tenant
@tenant_filter
@api_view(['POST'])
def create_framework(request):
    tenant_id = get_tenant_id_from_request(request)
    
    # Option 1: Explicitly set tenant_id
    framework = Framework.objects.create(
        FrameworkName=request.data['name'],
        tenant_id=tenant_id  # Set tenant_id explicitly
    )
    
    # Option 2: Use helper function
    from ...tenant_utils import create_with_tenant
    framework = create_with_tenant(Framework, request, FrameworkName=request.data['name'])
    
    return Response(framework)
```

### Pattern 6: Updating Records (with Validation)

```python
@require_tenant
@tenant_filter
@api_view(['PUT'])
def update_framework(request, framework_id):
    tenant_id = get_tenant_id_from_request(request)
    
    # Get framework filtered by tenant
    framework = Framework.objects.get(
        FrameworkId=framework_id,
        tenant_id=tenant_id  # Ensures tenant isolation
    )
    
    # Update fields
    framework.FrameworkName = request.data['name']
    framework.save()
    
    return Response(framework)
```

### Pattern 7: Validating Access Before Modification

```python
from ...tenant_utils import validate_tenant_access

@require_tenant
@tenant_filter
@api_view(['PUT'])
def update_framework(request, framework_id):
    framework = Framework.objects.get(FrameworkId=framework_id)
    
    # Validate tenant access
    if not validate_tenant_access(request, framework):
        return Response({
            'error': 'Access denied'
        }, status=403)
    
    # Proceed with update
    framework.FrameworkName = request.data['name']
    framework.save()
    
    return Response(framework)
```

---

## Code Examples

### Example 1: List Endpoint (Framework)

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from ...models import Framework
from ...tenant_utils import require_tenant, tenant_filter, get_tenant_id_from_request

@api_view(['GET'])
@permission_classes([PolicyViewPermission])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def framework_list(request):
    """
    Get all frameworks for the current tenant
    MULTI-TENANCY: Only returns frameworks belonging to the user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    if tenant_id is None:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
    # MULTI-TENANCY: Filter by tenant_id
    frameworks = Framework.objects.filter(tenant_id=tenant_id)
    
    # Serialize and return
    framework_data = [{
        'id': fw.FrameworkId,
        'name': fw.FrameworkName,
        ...
    } for fw in frameworks]
    
    return Response(framework_data)
```

### Example 2: Detail Endpoint (Incident)

```python
@api_view(['GET'])
@require_tenant
@tenant_filter
def incident_by_id(request, incident_id):
    """
    Get incident by ID
    MULTI-TENANCY: Only returns incident if it belongs to user's tenant
    """
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # MULTI-TENANCY: Filter by tenant_id
        incident = Incident.objects.get(
            IncidentId=incident_id,
            tenant_id=tenant_id
        )
        
        return Response({
            'id': incident.IncidentId,
            'title': incident.IncidentTitle,
            ...
        })
    except Incident.DoesNotExist:
        return Response({
            'error': 'Incident not found'
        }, status=404)
```

### Example 3: Create Endpoint (Policy)

```python
@api_view(['POST'])
@require_tenant
@tenant_filter
def create_policy(request):
    """
    Create a new policy
    MULTI-TENANCY: Automatically assigns policy to user's tenant
    """
    tenant_id = get_tenant_id_from_request(request)
    
    # MULTI-TENANCY: Set tenant_id when creating
    policy = Policy.objects.create(
        PolicyName=request.data['name'],
        PolicyDescription=request.data['description'],
        tenant_id=tenant_id  # Set tenant explicitly
    )
    
    return Response({
        'id': policy.PolicyId,
        'name': policy.PolicyName,
        ...
    }, status=201)
```

### Example 4: Raw SQL Query (Audit)

```python
@api_view(['GET'])
@require_tenant
@tenant_filter
def get_all_audits(request):
    """
    Get all audits using raw SQL
    MULTI-TENANCY: Filters by TenantId in SQL query
    """
    tenant_id = get_tenant_id_from_request(request)
    
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Note: Use TenantId (capital T) in SQL to match database column
        cursor.execute("""
            SELECT 
                a.AuditId,
                a.Title,
                ...
            FROM audit a
            WHERE a.TenantId = %s  -- MULTI-TENANCY: Filter by tenant
            ORDER BY a.AuditId DESC
        """, [tenant_id])
        
        columns = [col[0] for col in cursor.description]
        audits = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return Response(audits)
```

---

## Best Practices

### ✅ DO

1. **Always use both decorators**:
   ```python
   @require_tenant
   @tenant_filter
   @api_view(['GET'])
   ```

2. **Always filter queries by tenant_id**:
   ```python
   frameworks = Framework.objects.filter(tenant_id=tenant_id)
   ```

3. **Validate tenant_id is not None**:
   ```python
   if tenant_id is None:
       return Response({'error': 'Tenant context not found'}, status=403)
   ```

4. **Use tenant_id in raw SQL queries**:
   ```sql
   WHERE a.TenantId = %s  -- Note: TenantId (capital T)
   ```

5. **Set tenant_id when creating records**:
   ```python
   obj = Model.objects.create(..., tenant_id=tenant_id)
   ```

6. **Validate access before modifications**:
   ```python
   if not validate_tenant_access(request, obj):
       return Response({'error': 'Access denied'}, status=403)
   ```

### ❌ DON'T

1. **Don't skip tenant filtering**:
   ```python
   # ❌ BAD - No tenant filter
   frameworks = Framework.objects.all()
   
   # ✅ GOOD - Filtered by tenant
   frameworks = Framework.objects.filter(tenant_id=tenant_id)
   ```

2. **Don't use wrong column name in SQL**:
   ```sql
   -- ❌ BAD - Wrong column name
   WHERE a.tenant_id = %s
   
   -- ✅ GOOD - Correct column name
   WHERE a.TenantId = %s
   ```

3. **Don't forget to set tenant_id on create**:
   ```python
   # ❌ BAD - No tenant_id
   policy = Policy.objects.create(PolicyName='Test')
   
   # ✅ GOOD - tenant_id set
   policy = Policy.objects.create(PolicyName='Test', tenant_id=tenant_id)
   ```

4. **Don't trust user-provided IDs without tenant check**:
   ```python
   # ❌ BAD - No tenant validation
   framework = Framework.objects.get(FrameworkId=id)
   
   # ✅ GOOD - Tenant validated
   framework = Framework.objects.get(FrameworkId=id, tenant_id=tenant_id)
   ```

---

## Troubleshooting

### Issue: Both tenants see the same data

**Symptom**: Different tenants get identical query results.

**Causes**:
1. Missing `@tenant_filter` decorator
2. `tenant_id` is `None` in queries
3. Query doesn't include `.filter(tenant_id=tenant_id)`

**Solution**:
```python
# Check if tenant_id is being extracted
tenant_id = get_tenant_id_from_request(request)
print(f"DEBUG: tenant_id = {tenant_id}")  # Should not be None

# Ensure query is filtered
frameworks = Framework.objects.filter(tenant_id=tenant_id)  # Must include this
```

### Issue: 403 "Tenant context not found"

**Symptom**: All requests return 403 error.

**Causes**:
1. User doesn't have `tenant_id` set in database
2. JWT token doesn't contain `user_id`
3. `@tenant_filter` decorator not working

**Solution**:
```python
# Check user has tenant_id
user = Users.objects.get(UserId=user_id)
print(f"DEBUG: user.tenant_id = {user.tenant_id}")  # Should not be None

# Check JWT token
token = request.headers.get('Authorization', '').split(' ')[1]
payload = verify_jwt_token(token)
print(f"DEBUG: payload = {payload}")  # Should contain user_id
```

### Issue: SQL Error "Unknown column 'a.tenant_id'"

**Symptom**: Raw SQL queries fail with column not found error.

**Cause**: Using wrong column name in SQL (should be `TenantId`, not `tenant_id`).

**Solution**:
```sql
-- ❌ Wrong
WHERE a.tenant_id = %s

-- ✅ Correct
WHERE a.TenantId = %s
```

### Issue: New records don't get tenant_id

**Symptom**: Created records have `tenant_id = NULL`.

**Causes**:
1. Not setting `tenant_id` explicitly
2. Model doesn't inherit from `TenantAwareModel`
3. `tenant_context` not set

**Solution**:
```python
# Always set tenant_id explicitly
obj = Model.objects.create(..., tenant_id=tenant_id)

# Or use helper
from ...tenant_utils import create_with_tenant
obj = create_with_tenant(Model, request, ...)
```

---

## Summary

Multi-tenancy in this platform works by:

1. **Database Level**: Every tenant-aware table has a `TenantId` column
2. **Model Level**: Models have a `tenant` ForeignKey field (maps to `tenant_id` in ORM)
3. **Request Level**: `@tenant_filter` decorator extracts `tenant_id` from authenticated user
4. **Query Level**: All queries include `.filter(tenant_id=tenant_id)`
5. **Validation Level**: `validate_tenant_access()` ensures users can only access their tenant's data

**Key Takeaway**: 
> **Every database query MUST filter by `tenant_id` to ensure data isolation between tenants.**

---

## Related Files

- `grc_backend/grc/tenant_utils.py` - Core multitenancy utilities
- `grc_backend/grc/models.py` - Tenant model and TenantAwareModel
- `grc_backend/grc/routes/Policy/policy.py` - Example implementation
- `grc_backend/grc/routes/Incident/incident_views.py` - Example implementation
- `grc_backend/test_multitenancy_http.py` - Automated testing script

---

**Last Updated**: January 2026
**Version**: 1.0

