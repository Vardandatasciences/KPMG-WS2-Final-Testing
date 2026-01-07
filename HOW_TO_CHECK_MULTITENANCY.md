# How to Check Multitenancy from the Application

This guide provides comprehensive methods to verify and check multitenancy implementation in the GRC/TPRM application.

---

## Table of Contents

1. [Quick Checks](#quick-checks)
2. [Application-Level Checks](#application-level-checks)
3. [Database-Level Checks](#database-level-checks)
4. [API-Level Checks](#api-level-checks)
5. [Code-Level Verification](#code-level-verification)
6. [Testing Methods](#testing-methods)
7. [Troubleshooting](#troubleshooting)

---

## Quick Checks

### 1. Check Current Tenant Context

**In Django Shell:**
```python
python manage.py shell

from tprm_backend.core.tenant_context import get_current_tenant
from tprm_backend.core.models import Tenant

# Check current tenant
current_tenant = get_current_tenant()
print(f"Current tenant ID: {current_tenant}")

# List all tenants
tenants = Tenant.objects.all()
for tenant in tenants:
    print(f"Tenant ID: {tenant.tenant_id}, Name: {tenant.name}, Subdomain: {tenant.subdomain}")
```

**In API View/Function:**
```python
from tprm_backend.core.tenant_utils import get_tenant_id_from_request

def my_view(request):
    tenant_id = get_tenant_id_from_request(request)
    print(f"Request tenant ID: {tenant_id}")
    
    # Or directly from request
    if hasattr(request, 'tenant_id'):
        print(f"Tenant ID: {request.tenant_id}")
    
    if hasattr(request, 'tenant') and request.tenant:
        print(f"Tenant: {request.tenant.name} (ID: {request.tenant.tenant_id})")
```

### 2. Check User's Tenant Assignment

```python
from mfa_auth.models import User

# Get user and check tenant
user = User.objects.get(userid=1)
print(f"User: {user.username}")
print(f"User tenant_id: {user.tenant_id}")

# Check if user has tenant relationship
if hasattr(user, 'tenant') and user.tenant:
    print(f"Tenant: {user.tenant.name}")
```

---

## Application-Level Checks

### 1. Check Middleware Registration

**Verify middleware is active:**
```python
from django.conf import settings

# Check if tenant middleware is registered
middleware_list = settings.MIDDLEWARE
for mw in middleware_list:
    if 'tenant_middleware' in mw:
        print(f"✅ Tenant middleware found: {mw}")
```

**Expected middleware:**
- `tprm_backend.core.tenant_middleware.TenantContextMiddleware` (for TPRM)
- `grc.tenant_middleware.TenantContextMiddleware` (for GRC)

### 2. Check Tenant Context in Request

**In any view function:**
```python
from django.http import JsonResponse
from tprm_backend.core.tenant_utils import get_tenant_id_from_request

@api_view(['GET'])
def check_tenant_view(request):
    """Debug endpoint to check tenant context"""
    tenant_id = get_tenant_id_from_request(request)
    
    response_data = {
        'has_tenant_id': hasattr(request, 'tenant_id'),
        'tenant_id': getattr(request, 'tenant_id', None),
        'has_tenant': hasattr(request, 'tenant'),
        'tenant_name': request.tenant.name if hasattr(request, 'tenant') and request.tenant else None,
        'user_id': getattr(request.user, 'userid', None) if hasattr(request, 'user') else None,
    }
    
    return JsonResponse(response_data)
```

### 3. Check Decorator Usage

**Verify decorators are applied:**
```python
# Check if views use tenant decorators
from tprm_backend.core.tenant_utils import tenant_filter, require_tenant

@require_tenant  # Ensures tenant exists
@tenant_filter   # Adds tenant_id to request
@api_view(['GET'])
def my_protected_view(request):
    tenant_id = request.tenant_id
    # Your code here
    pass
```

---

## Database-Level Checks

### 1. Check Tenant Distribution in Tables

**SQL Query to check tenant distribution:**
```sql
-- Check tenant distribution in a specific table
SELECT TenantId, COUNT(*) as record_count 
FROM contracts 
GROUP BY TenantId 
ORDER BY TenantId;

-- Check for records without tenant_id (should be NULL or 0)
SELECT COUNT(*) as records_without_tenant
FROM contracts
WHERE TenantId IS NULL;

-- Check tenant distribution across multiple tables
SELECT 
    'contracts' as table_name,
    TenantId,
    COUNT(*) as count
FROM contracts
GROUP BY TenantId
UNION ALL
SELECT 
    'rfps' as table_name,
    TenantId,
    COUNT(*) as count
FROM rfps
GROUP BY TenantId;
```

### 2. Check Tenant Isolation

**Verify data isolation:**
```sql
-- Get all records for a specific tenant
SELECT * FROM contracts WHERE TenantId = 1;

-- Check if tenant 1 can see tenant 2's data (should return 0 rows)
SELECT * FROM contracts 
WHERE TenantId = 1 
AND ContractId IN (
    SELECT ContractId FROM contracts WHERE TenantId = 2
);
```

### 3. Check Foreign Key Relationships

```sql
-- Verify tenant foreign keys exist
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE REFERENCED_TABLE_NAME = 'tenants'
AND REFERENCED_COLUMN_NAME = 'TenantId';
```

---

## API-Level Checks

### 1. Test Tenant Isolation via HTTP Requests

**Using Python requests:**
```python
import requests

# Login and get JWT token for tenant 1
login_response = requests.post('http://localhost:8000/api/tprm/login/', {
    'username': 'user1@tenant1.com',
    'password': 'password'
})
token1 = login_response.json()['token']

# Get data for tenant 1
headers1 = {'Authorization': f'Bearer {token1}'}
response1 = requests.get('http://localhost:8000/api/tprm/contracts/list/', headers=headers1)
print(f"Tenant 1 contracts: {len(response1.json())}")

# Login and get JWT token for tenant 2
login_response2 = requests.post('http://localhost:8000/api/tprm/login/', {
    'username': 'user2@tenant2.com',
    'password': 'password'
})
token2 = login_response2.json()['token']

# Get data for tenant 2
headers2 = {'Authorization': f'Bearer {token2}'}
response2 = requests.get('http://localhost:8000/api/tprm/contracts/list/', headers=headers2)
print(f"Tenant 2 contracts: {len(response2.json())}")

# Verify they see different data
assert response1.json() != response2.json(), "Tenants should see different data!"
```

### 2. Test Cross-Tenant Access Prevention

```python
import requests

# Get token for tenant 1
token1 = get_token_for_tenant1()

# Try to access tenant 2's contract by ID
contract_id_from_tenant2 = 123  # ID that belongs to tenant 2
headers = {'Authorization': f'Bearer {token1}'}
response = requests.get(
    f'http://localhost:8000/api/tprm/contracts/{contract_id_from_tenant2}/',
    headers=headers
)

# Should return 403 or 404, not 200
assert response.status_code in [403, 404], "Cross-tenant access should be blocked!"
```

### 3. Check API Response Headers

```python
import requests

response = requests.get('http://localhost:8000/api/tprm/contracts/list/', 
                       headers={'Authorization': 'Bearer YOUR_TOKEN'})

# Check if response includes tenant information (if implemented)
print(f"Status: {response.status_code}")
print(f"Headers: {response.headers}")
print(f"Data count: {len(response.json())}")
```

---

## Code-Level Verification

### 1. Check Model Tenant Field

**Verify models have tenant field:**
```python
from tprm_backend.contracts.models import Contract

# Check if model has tenant field
print(f"Has tenant field: {hasattr(Contract, 'tenant')}")
print(f"Has tenant_id: {hasattr(Contract, 'tenant_id')}")

# Check model fields
for field in Contract._meta.get_fields():
    if 'tenant' in field.name.lower():
        print(f"Tenant field: {field.name}, Type: {type(field)}")
```

### 2. Check Query Filtering

**Verify queries include tenant filtering:**
```python
from tprm_backend.contracts.models import Contract
from tprm_backend.core.tenant_context import set_current_tenant

# Set tenant context
set_current_tenant(1)

# Check if queries are filtered
contracts = Contract.objects.all()
print(f"SQL Query: {contracts.query}")

# Should include WHERE TenantId = 1
# If not, queries are not properly filtered!
```

### 3. Check View Function Implementation

**Verify views filter by tenant:**
```python
# Good implementation
@tenant_filter
@api_view(['GET'])
def contract_list(request):
    tenant_id = request.tenant_id  # ✅ Gets tenant_id from request
    contracts = Contract.objects.filter(tenant_id=tenant_id)  # ✅ Filters by tenant
    return Response([...])

# Bad implementation (missing tenant filter)
@api_view(['GET'])
def contract_list_bad(request):
    contracts = Contract.objects.all()  # ❌ No tenant filtering!
    return Response([...])
```

### 4. Check TenantAwareModel Usage

```python
from tprm_backend.core.models import TenantAwareModel

# Check if model inherits from TenantAwareModel
class MyModel(TenantAwareModel):  # ✅ Good
    pass

# Check if tenant is auto-assigned
from tprm_backend.core.tenant_context import set_current_tenant

set_current_tenant(1)
obj = MyModel.objects.create(...)  # tenant_id should be auto-assigned
print(f"Auto-assigned tenant_id: {obj.tenant_id}")  # Should be 1
```

---

## Testing Methods

### 1. Run Automated Test Suite

**Run TPRM tenant tests:**
```bash
cd grc_backend
python manage.py shell < tprm_backend/core/test_tenant_implementation.py
```

**Run comprehensive multitenancy tests:**
```bash
# Run database-level tests
python manage.py test test_multitenancy

# Run API-level tests
python manage.py test test_multitenancy_api

# Run HTTP tests
python test_multitenancy_http.py
```

### 2. Manual Testing Checklist

**✅ Tenant Context Tests:**
- [ ] User login sets correct tenant context
- [ ] JWT token contains user_id
- [ ] Request has `tenant_id` attribute
- [ ] Request has `tenant` object

**✅ Data Isolation Tests:**
- [ ] Tenant 1 sees only Tenant 1's data
- [ ] Tenant 2 sees only Tenant 2's data
- [ ] Cross-tenant access returns 403/404
- [ ] Query counts differ between tenants

**✅ Data Creation Tests:**
- [ ] New records get correct tenant_id
- [ ] TenantAwareModel auto-assigns tenant
- [ ] Manual tenant assignment works

**✅ Query Filtering Tests:**
- [ ] All queries include `tenant_id` filter
- [ ] List endpoints return only tenant's data
- [ ] Detail endpoints enforce tenant check
- [ ] Aggregate queries are tenant-scoped

### 3. Create Test Script

**Custom test script:**
```python
# test_my_multitenancy.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from tprm_backend.core.models import Tenant
from tprm_backend.contracts.models import Contract
from tprm_backend.core.tenant_context import set_current_tenant, get_current_tenant

def test_tenant_isolation():
    """Test that tenants see only their own data"""
    print("\n" + "="*60)
    print("TESTING TENANT ISOLATION")
    print("="*60)
    
    # Get two tenants
    tenant1 = Tenant.objects.first()
    tenant2 = Tenant.objects.filter(tenant_id__gt=tenant1.tenant_id).first()
    
    if not tenant1 or not tenant2:
        print("❌ Need at least 2 tenants for testing")
        return
    
    # Test tenant 1
    set_current_tenant(tenant1.tenant_id)
    contracts1 = Contract.objects.filter(tenant_id=tenant1.tenant_id)
    print(f"\n✅ Tenant {tenant1.tenant_id} ({tenant1.name}):")
    print(f"   Contracts: {contracts1.count()}")
    
    # Test tenant 2
    set_current_tenant(tenant2.tenant_id)
    contracts2 = Contract.objects.filter(tenant_id=tenant2.tenant_id)
    print(f"\n✅ Tenant {tenant2.tenant_id} ({tenant2.name}):")
    print(f"   Contracts: {contracts2.count()}")
    
    # Verify isolation
    tenant1_ids = set(contracts1.values_list('contract_id', flat=True))
    tenant2_ids = set(contracts2.values_list('contract_id', flat=True))
    overlap = tenant1_ids & tenant2_ids
    
    if overlap:
        print(f"\n❌ ISOLATION FAILED: {len(overlap)} contracts shared between tenants!")
        print(f"   Shared IDs: {list(overlap)[:5]}")
    else:
        print(f"\n✅ ISOLATION PASSED: No shared contracts between tenants")

if __name__ == '__main__':
    test_tenant_isolation()
```

---

## Troubleshooting

### Issue: `tenant_id` is `None` in requests

**Symptoms:**
- All queries return all data (no filtering)
- `request.tenant_id` is `None`
- 403 errors on protected endpoints

**Solutions:**

1. **Check user has tenant_id:**
```python
from mfa_auth.models import User

user = User.objects.get(userid=user_id)
print(f"User tenant_id: {user.tenant_id}")

# If None, assign tenant:
user.tenant_id = 1
user.save()
```

2. **Check JWT token:**
```python
import jwt
from django.conf import settings

token = request.headers.get('Authorization', '').split(' ')[1]
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
print(f"JWT payload: {payload}")  # Should contain user_id
```

3. **Check middleware:**
```python
# Verify middleware is in settings
from django.conf import settings
print('TenantContextMiddleware' in str(settings.MIDDLEWARE))
```

### Issue: Queries return all tenants' data

**Symptoms:**
- Queries don't filter by tenant_id
- All tenants see the same data

**Solutions:**

1. **Verify query includes tenant filter:**
```python
# ❌ Bad
contracts = Contract.objects.all()

# ✅ Good
contracts = Contract.objects.filter(tenant_id=request.tenant_id)
```

2. **Use tenant_filter decorator:**
```python
@tenant_filter
@api_view(['GET'])
def my_view(request):
    tenant_id = request.tenant_id  # Now available
    contracts = Contract.objects.filter(tenant_id=tenant_id)
```

### Issue: New records don't get tenant_id

**Symptoms:**
- Created records have `tenant_id = NULL`
- Records not associated with tenant

**Solutions:**

1. **Set tenant explicitly:**
```python
contract = Contract.objects.create(
    tenant_id=request.tenant_id,  # ✅ Explicit
    ...
)
```

2. **Use TenantAwareModel:**
```python
class Contract(TenantAwareModel):  # ✅ Auto-assigns tenant
    ...
```

3. **Set tenant context:**
```python
from tprm_backend.core.tenant_context import set_current_tenant

set_current_tenant(request.tenant_id)
contract = Contract.objects.create(...)  # Auto-assigned
```

### Issue: SQL Error "Unknown column 'tenant_id'"

**Symptoms:**
- Raw SQL queries fail
- Column name mismatch

**Solutions:**

1. **Use correct column name in SQL:**
```sql
-- ❌ Wrong (Django ORM uses tenant_id)
WHERE tenant_id = %s

-- ✅ Correct (Database uses TenantId)
WHERE TenantId = %s
```

2. **Use Django ORM instead:**
```python
# ✅ Use ORM (handles column name automatically)
Contract.objects.filter(tenant_id=tenant_id)
```

---

## Summary Checklist

Use this checklist to verify multitenancy is working:

- [ ] **Tenant Model exists** and has records
- [ ] **Users have tenant_id** assigned
- [ ] **Middleware is registered** in settings
- [ ] **Models have tenant field** (ForeignKey to Tenant)
- [ ] **Views use @tenant_filter** decorator
- [ ] **Queries filter by tenant_id** (`.filter(tenant_id=...)`)
- [ ] **New records get tenant_id** assigned
- [ ] **Cross-tenant access is blocked** (403/404)
- [ ] **Database has TenantId column** in all tenant-aware tables
- [ ] **Test suite passes** all multitenancy tests

---

## Quick Reference

### Get Tenant from Request
```python
from tprm_backend.core.tenant_utils import get_tenant_id_from_request

tenant_id = get_tenant_id_from_request(request)
```

### Filter QuerySet by Tenant
```python
from tprm_backend.core.tenant_utils import filter_queryset_by_tenant

queryset = Contract.objects.all()
filtered = filter_queryset_by_tenant(queryset, tenant_id)
```

### Check Tenant Access
```python
from tprm_backend.core.tenant_utils import validate_tenant_access

if validate_tenant_access(request, contract):
    # User has access
    pass
```

### Set Tenant Context
```python
from tprm_backend.core.tenant_context import set_current_tenant, get_current_tenant

set_current_tenant(1)
current = get_current_tenant()  # Returns 1
```

---

## Related Files

- `tprm_backend/core/models.py` - Tenant model and TenantAwareModel
- `tprm_backend/core/tenant_utils.py` - Tenant utilities and decorators
- `tprm_backend/core/tenant_context.py` - Tenant context management
- `tprm_backend/core/tenant_middleware.py` - Tenant middleware
- `tprm_backend/core/test_tenant_implementation.py` - Test script

---

**Last Updated:** 2025-01-XX
**Version:** 1.0

