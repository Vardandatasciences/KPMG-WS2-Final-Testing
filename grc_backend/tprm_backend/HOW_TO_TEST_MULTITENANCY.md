# How to Test Multi-Tenancy Implementation

This guide explains how to verify that the multi-tenancy implementation for TPRM is working correctly.

## Quick Test Script

Run the automated test script:

```bash
cd grc_backend
python manage.py shell < tprm_backend/core/test_tenant_implementation.py
```

Or interactively:

```bash
python manage.py shell
>>> exec(open('tprm_backend/core/test_tenant_implementation.py').read())
```

## Manual Testing Steps

### 1. Verify Tenant Context Functions

```python
python manage.py shell

from tprm_backend.core.tenant_context import set_current_tenant, get_current_tenant, clear_current_tenant

# Test setting tenant
set_current_tenant(1)
print(get_current_tenant())  # Should print: 1

# Test clearing
clear_current_tenant()
print(get_current_tenant())  # Should print: None
```

### 2. Verify Tenant Model Exists

```python
from tprm_backend.core.models import Tenant

# Check if tenants exist
tenants = Tenant.objects.all()
print(f"Found {tenants.count()} tenant(s)")

# View a tenant
if tenants.exists():
    tenant = tenants.first()
    print(f"Tenant: {tenant.name} (ID: {tenant.tenant_id}, Subdomain: {tenant.subdomain})")
```

### 3. Test Tenant Signals (Auto-assignment)

```python
from tprm_backend.core.models import Tenant
from tprm_backend.core.tenant_context import set_current_tenant
from tprm_backend.rfp.models import RFP

# Get or create a test tenant
tenant = Tenant.objects.first()
if not tenant:
    tenant = Tenant.objects.create(
        name="Test Tenant",
        subdomain="test",
        status="active"
    )

# Set tenant context
set_current_tenant(tenant.tenant_id)

# Create an RFP - tenant should be auto-assigned
rfp = RFP.objects.create(
    rfp_title="Test RFP",
    description="Testing tenant auto-assignment",
    rfp_type="Test",
    created_by=1,
    status="DRAFT"
)

# Verify tenant was auto-assigned
print(f"RFP tenant_id: {rfp.tenant_id}")
print(f"Expected tenant_id: {tenant.tenant_id}")
assert rfp.tenant_id == tenant.tenant_id, "Tenant should be auto-assigned!"

# Clean up
rfp.delete()
```

### 4. Test Tenant Filtering in Views

#### Option A: Using Django Test Client

```python
from django.test import Client
from django.contrib.auth import get_user_model
from tprm_backend.core.models import Tenant

# Create test client
client = Client()

# Create a tenant
tenant = Tenant.objects.create(
    name="Test Tenant",
    subdomain="test",
    status="active"
)

# Make a request with tenant in JWT or subdomain
# The middleware should extract tenant and set it on request

# Example: Test RFP list endpoint
response = client.get('/api/rfp/')
# Check that response only contains RFPs for the current tenant
```

#### Option B: Using Tenant Utilities Directly

```python
from tprm_backend.core.tenant_utils import get_tenant_aware_queryset, filter_queryset_by_tenant
from tprm_backend.rfp.models import RFP
from tprm_backend.core.models import Tenant

# Get a tenant
tenant = Tenant.objects.first()

# Test filter_queryset_by_tenant
all_rfps = RFP.objects.all()
filtered = filter_queryset_by_tenant(all_rfps, tenant.tenant_id)
print(f"Total RFPs: {all_rfps.count()}")
print(f"Filtered RFPs for tenant {tenant.tenant_id}: {filtered.count()}")

# Verify all filtered RFPs belong to the tenant
for rfp in filtered:
    assert rfp.tenant_id == tenant.tenant_id, f"RFP {rfp.rfp_id} doesn't belong to tenant!"
```

### 5. Test Middleware Registration

```python
from django.conf import settings

# Check if TPRM tenant middleware is registered
middleware = settings.MIDDLEWARE
tprm_middleware = [mw for mw in middleware if 'tprm_backend.core.tenant_middleware' in mw]

if tprm_middleware:
    print("✅ TPRM tenant middleware is registered:")
    for mw in tprm_middleware:
        print(f"   - {mw}")
else:
    print("❌ TPRM tenant middleware NOT found in settings!")
```

### 6. Test via API Endpoints

#### Using curl with JWT token:

```bash
# 1. Login and get JWT token (should include tenant_id in payload)
curl -X POST http://localhost:8000/api/tprm/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# 2. Use token to access RFP endpoint
curl -X GET http://localhost:8000/api/rfp/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# The middleware should extract tenant from JWT and filter results
```

#### Using subdomain:

```bash
# Access via subdomain (if configured)
curl -X GET http://test.localhost:8000/api/rfp/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Middleware should extract tenant from subdomain 'test'
```

### 7. Verify Database Schema

Check that tenant fields exist in database:

```sql
-- Check RFP table has TenantId column
DESCRIBE rfps;

-- Check that TenantId column exists
SHOW COLUMNS FROM rfps LIKE 'TenantId';

-- Count RFPs by tenant
SELECT TenantId, COUNT(*) as count 
FROM rfps 
GROUP BY TenantId;
```

### 8. Test in Django Admin

1. Go to Django admin: `http://localhost:8000/admin/`
2. Navigate to RFP section
3. Create a new RFP
4. Check that `tenant` field is automatically populated (if tenant context is set)

## Common Issues and Solutions

### Issue: Tenant signals not working

**Solution:**
1. Verify `tprm_backend.core` is in `INSTALLED_APPS`
2. Check that `apps.py` exists and imports `tenant_signals`
3. Restart Django server to reload apps

```python
# Verify apps.py
from tprm_backend.core import apps
print(apps.CoreConfig.ready)
```

### Issue: Middleware not setting tenant

**Solution:**
1. Check middleware order in settings (should be after authentication)
2. Verify JWT token includes `tenant_id` claim
3. Check subdomain configuration
4. Look at Django logs for middleware debug messages

### Issue: Views returning all records (not filtered)

**Solution:**
1. Verify views use `get_tenant_aware_queryset()` or `filter_queryset_by_tenant()`
2. Check that `request.tenant_id` is set by middleware
3. Verify models have `tenant` ForeignKey field

### Issue: Tenant auto-assignment not working

**Solution:**
1. Ensure tenant context is set: `set_current_tenant(tenant_id)`
2. Verify signal is registered (check apps.py)
3. Check that model has `tenant` field with `null=True, blank=True`
4. Ensure you're creating a NEW record (pk is None)

## Debugging Tips

### Enable Debug Logging

Add to `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'tprm_backend.core.tenant_middleware': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'tprm_backend.core.tenant_signals': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Check Current Tenant in View

```python
from tprm_backend.core.tenant_context import get_current_tenant
from tprm_backend.core.tenant_utils import get_tenant_id_from_request

def my_view(request):
    # Method 1: From request (set by middleware)
    tenant_id = get_tenant_id_from_request(request)
    
    # Method 2: From context
    tenant_id = get_current_tenant()
    
    print(f"Current tenant: {tenant_id}")
    return Response({"tenant_id": tenant_id})
```

## Expected Behavior

✅ **Working correctly when:**
- New records automatically get `tenant_id` assigned
- Queries are filtered by tenant
- Middleware extracts tenant from request
- Each tenant only sees their own data

❌ **Not working when:**
- All tenants see all data
- Tenant_id is always None
- Middleware errors in logs
- Signals not firing

## Next Steps

After verifying everything works:

1. **Run migrations** to ensure database schema is up to date
2. **Test with multiple tenants** to verify isolation
3. **Test edge cases** (no tenant, invalid tenant, etc.)
4. **Add tenant filtering to other views** as needed
5. **Monitor logs** in production for tenant-related issues

