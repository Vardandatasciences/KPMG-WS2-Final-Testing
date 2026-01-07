# TPRM Multi-Tenancy - Next Steps After Creating Tenants Table

## ✅ Step 1: Add TenantId to Users Table (REQUIRED FIRST)

**Why**: Users need to be linked to tenants so the system knows which tenant a user belongs to.

### SQL Script:

```sql
-- Add TenantId column to users table
ALTER TABLE users 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_users_tenant_id (TenantId);

-- Create a default tenant for existing users
INSERT INTO tenants (Name, Subdomain, LicenseKey, SubscriptionTier, Status, MaxUsers, StorageLimitGB, Settings)
VALUES ('Default Tenant', 'default', 'DEFAULT-LICENSE-TPRM', 'enterprise', 'active', 1000, 1000, '{}');

-- Get the default tenant ID (note it down)
SET @default_tenant_id = LAST_INSERT_ID();

-- Assign all existing users to default tenant
UPDATE users SET TenantId = @default_tenant_id WHERE TenantId IS NULL;
```

**Execute this SQL in your TPRM database.**

---

## ✅ Step 2: Create Core Tenant Infrastructure Files

### 2.1 Create Tenant Context Manager

**File**: `grc_backend/tprm_backend/core/tenant_context.py`

```python
"""
Tenant Context Manager for Automatic Tenant ID Assignment
"""
import threading
from contextlib import contextmanager

_thread_local = threading.local()

def set_current_tenant(tenant_id):
    """Set the current tenant_id in thread-local storage"""
    _thread_local.tenant_id = tenant_id

def get_current_tenant():
    """Get the current tenant_id from thread-local storage"""
    return getattr(_thread_local, 'tenant_id', None)

def clear_current_tenant():
    """Clear the current tenant_id from thread-local storage"""
    if hasattr(_thread_local, 'tenant_id'):
        delattr(_thread_local, 'tenant_id')

@contextmanager
def tenant_context(tenant_id):
    """Context manager to set tenant_id for a block of code"""
    old_tenant_id = get_current_tenant()
    set_current_tenant(tenant_id)
    try:
        yield
    finally:
        if old_tenant_id is not None:
            set_current_tenant(old_tenant_id)
        else:
            clear_current_tenant()
```

### 2.2 Create Tenant Utilities

**File**: `grc_backend/tprm_backend/core/tenant_utils.py`

```python
"""
Tenant Utilities for Multi-Tenancy Support
"""
import logging
from functools import wraps
from django.http import JsonResponse
from django.db.models import QuerySet

logger = logging.getLogger(__name__)

def get_tenant_id_from_request(request):
    """Get tenant_id from request object"""
    if hasattr(request, 'tenant_id'):
        return request.tenant_id
    elif hasattr(request, 'tenant') and request.tenant:
        return request.tenant.tenant_id
    return None

def require_tenant(view_func):
    """
    Decorator to ensure request has tenant context
    Returns 403 error if tenant is not found
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'tenant') or request.tenant is None:
            logger.warning(f"[Tenant Utils] Tenant required but not found for {request.method} {request.path}")
            return JsonResponse({
                'error': 'Tenant context not found',
                'detail': 'This endpoint requires tenant authentication'
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

def tenant_filter(view_func):
    """
    Decorator to automatically add tenant filtering to view function
    Adds 'tenant_id' to request for easy filtering
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Add tenant_id to request
        if hasattr(request, 'tenant') and request.tenant:
            request.tenant_id = request.tenant.tenant_id
        else:
            # Try to get tenant from user
            tenant_id = None
            if hasattr(request, 'user') and request.user:
                try:
                    # Get user_id from request
                    user_id = None
                    if hasattr(request.user, 'userid'):
                        user_id = request.user.userid
                    elif hasattr(request.user, 'id'):
                        user_id = request.user.id
                    elif hasattr(request.user, 'UserId'):
                        user_id = request.user.UserId
                    elif hasattr(request.user, 'user_id'):
                        user_id = request.user.user_id
                    
                    # Extract from JWT if available
                    if not user_id:
                        auth_header = request.headers.get('Authorization', '')
                        if auth_header.startswith('Bearer '):
                            try:
                                import jwt
                                from django.conf import settings
                                token = auth_header.split(' ')[1]
                                secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
                                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                                if payload and 'user_id' in payload:
                                    user_id = payload['user_id']
                            except:
                                pass
                    
                    # Get tenant from user - try different User models
                    if user_id:
                        # Try mfa_auth.User first (most common in TPRM)
                        try:
                            from mfa_auth.models import User
                            user = User.objects.get(userid=user_id)
                            if hasattr(user, 'tenant_id'):
                                tenant_id = user.tenant_id
                            elif hasattr(user, 'tenant') and user.tenant:
                                tenant_id = user.tenant.tenant_id
                        except:
                            # Try other User models if mfa_auth doesn't work
                            try:
                                from bcpdrp.models import Users
                                user = Users.objects.get(user_id=user_id)
                                if hasattr(user, 'tenant_id'):
                                    tenant_id = user.tenant_id
                                elif hasattr(user, 'tenant') and user.tenant:
                                    tenant_id = user.tenant.tenant_id
                            except:
                                pass
                except Exception as e:
                    logger.error(f"[Tenant Utils] Error extracting tenant: {e}")
            
            request.tenant_id = tenant_id
        
        return view_func(request, *args, **kwargs)
    return wrapper

def get_tenant_aware_queryset(model, request):
    """Get a queryset filtered by tenant from request"""
    tenant_id = get_tenant_id_from_request(request)
    if tenant_id and hasattr(model, 'tenant'):
        return model.objects.filter(tenant_id=tenant_id)
    else:
        return model.objects.all()

def validate_tenant_access(request, obj):
    """Validate that user has access to object based on tenant"""
    tenant_id = get_tenant_id_from_request(request)
    if tenant_id is None:
        return False
    if not hasattr(obj, 'tenant_id'):
        return True  # Allow access if object doesn't have tenant_id
    return obj.tenant_id == tenant_id
```

### 2.3 Create Tenant Middleware

**File**: `grc_backend/tprm_backend/core/tenant_middleware.py`

```python
"""
Tenant Context Middleware for Multi-Tenancy Support
"""
import logging
import jwt
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from .models import Tenant

logger = logging.getLogger(__name__)

class TenantContextMiddleware(MiddlewareMixin):
    """Middleware to set tenant context on every request"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        logger.info("✅ TPRM Tenant Context Middleware loaded")
    
    def process_request(self, request):
        """Extract tenant from request and add to request.tenant"""
        # Skip tenant resolution for certain public paths
        skip_paths = [
            '/api/login/',
            '/api/jwt/login/',
            '/api/tprm/login/',
            '/api/register/',
            '/admin/',
            '/static/',
            '/media/',
            '/api/test-connection/',
        ]
        
        path = request.path_info
        if any(path.startswith(skip_path) for skip_path in skip_paths):
            request.tenant = None
            request.tenant_id = None
            return None
        
        # Try to get tenant from different sources
        tenant = None
        
        # 1. Try to get tenant from subdomain
        tenant = self._get_tenant_from_subdomain(request)
        
        # 2. If not found, try JWT token
        if not tenant:
            tenant = self._get_tenant_from_jwt(request)
        
        # 3. If not found, try authenticated user
        if not tenant and hasattr(request, 'user') and request.user:
            tenant = self._get_tenant_from_user(request.user)
        
        # Set tenant on request
        request.tenant = tenant
        request.tenant_id = tenant.tenant_id if tenant else None
        
        # Set tenant context for automatic tenant_id assignment
        if tenant:
            from .tenant_context import set_current_tenant
            set_current_tenant(tenant.tenant_id)
            logger.debug(f"[Tenant Middleware] Resolved tenant: {tenant.name} (ID: {tenant.tenant_id})")
        else:
            from .tenant_context import clear_current_tenant
            clear_current_tenant()
        
        return None
    
    def _get_tenant_from_subdomain(self, request):
        """Extract tenant from subdomain"""
        try:
            host = request.get_host().split(':')[0]
            parts = host.split('.')
            if len(parts) >= 3:
                subdomain = parts[0]
                if subdomain in ['www', 'api', 'admin']:
                    return None
                tenant = Tenant.objects.filter(subdomain=subdomain, status='active').first()
                if tenant:
                    return tenant
        except Exception as e:
            logger.error(f"[Tenant Middleware] Error extracting tenant from subdomain: {e}")
        return None
    
    def _get_tenant_from_jwt(self, request):
        """Extract tenant from JWT token"""
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                tenant_id = payload.get('tenant_id')
                if tenant_id:
                    tenant = Tenant.objects.filter(tenant_id=tenant_id, status='active').first()
                    if tenant:
                        return tenant
        except Exception as e:
            logger.debug(f"[Tenant Middleware] Error extracting tenant from JWT: {e}")
        return None
    
    def _get_tenant_from_user(self, user):
        """Extract tenant from authenticated user"""
        try:
            # Try different User models
            user_id = None
            if hasattr(user, 'userid'):
                user_id = user.userid
            elif hasattr(user, 'id'):
                user_id = user.id
            elif hasattr(user, 'UserId'):
                user_id = user.UserId
            elif hasattr(user, 'user_id'):
                user_id = user.user_id
            
            if user_id:
                # Try mfa_auth.User first
                try:
                    from mfa_auth.models import User
                    db_user = User.objects.select_related('tenant').filter(userid=user_id).first()
                    if db_user and db_user.tenant and db_user.tenant.status == 'active':
                        return db_user.tenant
                except:
                    # Try bcpdrp.Users
                    try:
                        from bcpdrp.models import Users
                        db_user = Users.objects.select_related('tenant').filter(user_id=user_id).first()
                        if db_user and db_user.tenant and db_user.tenant.status == 'active':
                            return db_user.tenant
                    except:
                        pass
        except Exception as e:
            logger.error(f"[Tenant Middleware] Error extracting tenant from user: {e}")
        return None
```

### 2.4 Update Settings to Add Middleware

**File**: `grc_backend/tprm_backend/config/settings.py`

Add the middleware to the `MIDDLEWARE` list (usually near the top, after security middleware):

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ... other middleware ...
    'core.tenant_middleware.TenantContextMiddleware',  # ADD THIS LINE
    # ... rest of middleware ...
]
```

---

## ✅ Step 3: Update User Models to Include Tenant ForeignKey

You have multiple User models in different modules. Update the main one(s) you use:

### 3.1 Update mfa_auth User Model (if this is your main auth model)

**File**: `grc_backend/tprm_backend/mfa_auth/models.py`

Add to your User model:

```python
from core.models import Tenant

class User(models.Model):
    # ... existing fields ...
    
    # MULTI-TENANCY: Add tenant ForeignKey
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        db_column='TenantId',
        related_name='users',
        null=True,
        blank=True
    )
    
    # ... rest of model ...
```

### 3.2 Update bcpdrp Users Model (if used)

**File**: `grc_backend/tprm_backend/bcpdrp/models.py`

Add to Users model:

```python
from core.models import Tenant

class Users(models.Model):
    # ... existing fields ...
    
    # MULTI-TENANCY: Add tenant ForeignKey
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        db_column='TenantId',
        related_name='bcp_users',
        null=True,
        blank=True
    )
    
    # ... rest of model ...
```

---

## ✅ Step 4: Create Django Migration for User Model

After updating the User model(s), create and run migrations:

```bash
# Create migration
python manage.py makemigrations mfa_auth  # or bcpdrp, or both

# Review the migration file to ensure it's correct

# Run migration
python manage.py migrate
```

---

## ✅ Step 5: Test Basic Setup

Create a simple test to verify everything works:

```python
# Test in Django shell: python manage.py shell

from core.models import Tenant
from mfa_auth.models import User  # or your User model

# Check tenants table
tenants = Tenant.objects.all()
print(f"Tenants: {list(tenants)}")

# Check users have tenant_id
users = User.objects.all()
for user in users[:5]:
    print(f"User {user.userid}: tenant_id = {getattr(user, 'tenant_id', 'NOT SET')}")
```

---

## 📋 Summary Checklist

- [ ] ✅ Step 1: Add TenantId to users table (SQL executed)
- [ ] ✅ Step 2.1: Create `core/tenant_context.py`
- [ ] ✅ Step 2.2: Create `core/tenant_utils.py`
- [ ] ✅ Step 2.3: Create `core/tenant_middleware.py`
- [ ] ✅ Step 2.4: Add middleware to `config/settings.py`
- [ ] ✅ Step 3: Update User model(s) with tenant ForeignKey
- [ ] ✅ Step 4: Create and run migrations
- [ ] ✅ Step 5: Test basic setup

---

## 🚀 Next Steps After This

Once Steps 1-5 are complete, you'll need to:

1. **Add TenantId to all tenant-aware tables** (RFP, Contracts, Vendors, etc.)
2. **Update all models** to include tenant ForeignKey
3. **Update all views** to filter by tenant_id
4. **Test tenant isolation**

See `TPRM_MULTITENANCY_IMPLEMENTATION.md` for detailed instructions on these steps.

---

**Questions?** Refer to the main implementation guide: `TPRM_MULTITENANCY_IMPLEMENTATION.md`

