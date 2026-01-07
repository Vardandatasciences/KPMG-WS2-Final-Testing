# TPRM Multi-Tenancy Implementation Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Implementation Steps](#implementation-steps)
4. [Database Schema Changes](#database-schema-changes)
5. [Backend Implementation](#backend-implementation)
6. [Frontend Implementation](#frontend-implementation)
7. [Testing Strategy](#testing-strategy)
8. [Migration Guide](#migration-guide)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This document provides a comprehensive guide for implementing multi-tenancy in the TPRM (Third-Party Risk Management) system, following the same pattern used in the GRC system. Multi-tenancy ensures that each organization (tenant) can only access their own data, providing complete data isolation.

### Quick Start - Create Tenants Table

**Yes, you can use the exact same `tenants` table schema from GRC!** This ensures consistency across both systems.

To create the tenants table in TPRM database, you can either:

1. **Run the SQL script**:
   ```bash
   mysql -u your_user -p your_tprm_database < grc_backend/tprm_backend/scripts/create_tenants_table.sql
   ```

2. **Or execute the SQL directly** (see Database Schema Changes section below)

The table name is `tenants` (plural) to match GRC, and all foreign key references should use `tenants(TenantId)`.

### Key Principles

1. **Every tenant-aware table MUST have a `TenantId` column**
2. **All database queries MUST filter by `tenant_id`**
3. **Tenant context is extracted from authenticated user on every request**
4. **All data creation MUST assign the correct `tenant_id`**

### Scope

This implementation covers all TPRM modules:
- **RFP** (Request for Proposal)
- **Contracts**
- **Vendors**
- **Risk Analysis**
- **Compliance**
- **Audits**
- **BCP/DRP** (Business Continuity Planning / Disaster Recovery Planning)
- **SLAs** (Service Level Agreements)
- **RBAC** (Role-Based Access Control)

---

## Architecture

### Multi-Tenancy Flow

```
Request → JWT Token/Session → Extract user_id → Lookup User → Get tenant_id → 
Set on request → Filter all queries by tenant_id → Return tenant-specific data
```

### Components

1. **Tenant Model**: Stores tenant information
2. **Tenant Middleware**: Extracts tenant from request
3. **Tenant Utilities**: Helper functions and decorators
4. **Tenant Context**: Thread-local storage for automatic tenant assignment
5. **Model Updates**: Add `tenant` ForeignKey to all tenant-aware models

---

## Implementation Steps

### Phase 1: Core Infrastructure (Week 1)

1. ✅ Create Tenant model
2. ✅ Create tenant utilities (`tenant_utils.py`)
3. ✅ Create tenant context manager (`tenant_context.py`)
4. ✅ Create tenant middleware (`tenant_middleware.py`)
5. ✅ Update User model to include `tenant` ForeignKey

### Phase 2: Database Migration (Week 1-2)

1. ✅ Add `TenantId` column to all tenant-aware tables
2. ✅ Create foreign key constraints
3. ✅ Migrate existing data (assign default tenant)
4. ✅ Update indexes for performance

### Phase 3: Model Updates (Week 2-3)

1. ✅ Update RFP models
2. ✅ Update Contract models
3. ✅ Update Vendor models
4. ✅ Update Risk Analysis models
5. ✅ Update Compliance models
6. ✅ Update Audit models
7. ✅ Update BCP/DRP models
8. ✅ Update SLA models
9. ✅ Update RBAC models

### Phase 4: View Updates (Week 3-4)

1. ✅ Add decorators to all views
2. ✅ Update all queries to filter by tenant_id
3. ✅ Update create operations to set tenant_id
4. ✅ Update update/delete operations to validate tenant access

### Phase 5: Frontend Updates (Week 4-5)

1. ✅ Update API configuration
2. ✅ Ensure JWT tokens include tenant context
3. ✅ Update error handling for tenant-related errors

### Phase 6: Testing & Validation (Week 5-6)

1. ✅ Unit tests for tenant isolation
2. ✅ Integration tests
3. ✅ Security audit
4. ✅ Performance testing

---

## Database Schema Changes

### 1. Create Tenant Table

Use the same schema as GRC for consistency:

```sql
CREATE TABLE `tenants` (
  `TenantId` int NOT NULL AUTO_INCREMENT,
  `Name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Subdomain` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `LicenseKey` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `SubscriptionTier` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'starter',
  `Status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'trial',
  `MaxUsers` int NOT NULL DEFAULT '10',
  `StorageLimitGB` int NOT NULL DEFAULT '10',
  `CreatedAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `UpdatedAt` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `TrialEndsAt` datetime(6) DEFAULT NULL,
  `Settings` json NOT NULL,
  `PrimaryContactEmail` varchar(254) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `PrimaryContactName` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `PrimaryContactPhone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`TenantId`),
  UNIQUE KEY `uniq_tenants_subdomain` (`Subdomain`),
  UNIQUE KEY `uniq_tenants_licensekey` (`LicenseKey`),
  KEY `idx_tenants_status` (`Status`),
  CONSTRAINT `chk_tenants_status` CHECK ((`Status` in (_utf8mb4'trial',_utf8mb4'active',_utf8mb4'suspended',_utf8mb4'cancelled'))),
  CONSTRAINT `chk_tenants_subscriptiontier` CHECK ((`SubscriptionTier` in (_utf8mb4'starter',_utf8mb4'professional',_utf8mb4'enterprise')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Note**: The table name is `tenants` (plural) to match GRC. All foreign key references should use `tenants(TenantId)`.

**Quick Start**: You can run the SQL script directly:
```bash
mysql -u your_user -p your_database < grc_backend/tprm_backend/scripts/create_tenants_table.sql
```

Or execute the SQL directly in your MySQL client.

### 2. Add TenantId to Users Table

```sql
ALTER TABLE users 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);
```

### 3. Add TenantId to All Tenant-Aware Tables

#### RFP Module

```sql
-- RFP table
ALTER TABLE rfp 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);

-- RFP Evaluation Criteria
ALTER TABLE rfp_evaluation_criteria 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);

-- File Storage
ALTER TABLE file_storage 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);
```

#### Contracts Module

```sql
-- Contracts table
ALTER TABLE contracts 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);

-- Contract Approval
ALTER TABLE contract_approval 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);
```

#### Vendors Module

```sql
-- Vendors table
ALTER TABLE vendors 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);

-- Vendor Categories
ALTER TABLE vendor_categories 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);
```

#### Risk Analysis Module

```sql
-- Risk Analysis table
ALTER TABLE risk_analysis 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);

-- Vendor Risk Analysis
ALTER TABLE vendor_risk_analysis 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);
```

#### Compliance Module

```sql
-- Compliance table
ALTER TABLE compliance 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);
```

#### Audits Module

```sql
-- Audits table
ALTER TABLE audits 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);

-- Contract Audits
ALTER TABLE audits_contract 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);
```

#### BCP/DRP Module

```sql
-- BCP/DRP Plans
ALTER TABLE plan 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);

-- BCP/DRP Approvals
ALTER TABLE bcp_drp_approvals 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);
```

#### SLAs Module

```sql
-- SLAs table
ALTER TABLE slas 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);
```

#### RBAC Module

```sql
-- RBAC TPRM
ALTER TABLE rbac_tprm 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);

-- Access Requests
ALTER TABLE AccessRequestTPRM 
ADD COLUMN TenantId INT NULL,
ADD FOREIGN KEY (TenantId) REFERENCES tenants(TenantId) ON DELETE CASCADE,
ADD INDEX idx_tenant_id (TenantId);
```

### 4. Data Migration Script

```sql
-- Assign all existing data to a default tenant
-- First, create a default tenant
INSERT INTO tenants (Name, Subdomain, LicenseKey, SubscriptionTier, Status, MaxUsers, StorageLimitGB, Settings)
VALUES ('Default Tenant', 'default', 'DEFAULT-LICENSE', 'enterprise', 'active', 1000, 1000, '{}');

-- Get the default tenant ID
SET @default_tenant_id = LAST_INSERT_ID();

-- Update all users to belong to default tenant
UPDATE users SET TenantId = @default_tenant_id WHERE TenantId IS NULL;

-- Update all tenant-aware tables
UPDATE rfp SET TenantId = @default_tenant_id WHERE TenantId IS NULL;
UPDATE contracts SET TenantId = @default_tenant_id WHERE TenantId IS NULL;
UPDATE vendors SET TenantId = @default_tenant_id WHERE TenantId IS NULL;
-- ... repeat for all tables
```

---

## Backend Implementation

### Step 1: Create Core Tenant Infrastructure

#### 1.1 Create Tenant Model

**File**: `grc_backend/tprm_backend/core/models.py` (or create new `tenant/models.py`)

```python
from django.db import models

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
                try:
                    tenant = Tenant.objects.get(tenant_id=tenant_id)
                    self.tenant = tenant
                except Tenant.DoesNotExist:
                    pass
        super().save(*args, **kwargs)

class Tenant(models.Model):
    """
    Tenant model for multi-tenancy support.
    Each tenant represents an organization/company using the TPRM platform.
    Matches the GRC tenants table schema exactly.
    """
    tenant_id = models.AutoField(primary_key=True, db_column='TenantId')
    name = models.CharField(max_length=255, db_column='Name', help_text="Organization/Company Name")
    subdomain = models.CharField(max_length=100, unique=True, db_column='Subdomain', 
                                  help_text="Unique subdomain for tenant")
    license_key = models.CharField(max_length=100, unique=True, null=True, blank=True, db_column='LicenseKey')
    subscription_tier = models.CharField(max_length=50, default='starter', db_column='SubscriptionTier',
                                        choices=[
                                            ('starter', 'Starter'),
                                            ('professional', 'Professional'),
                                            ('enterprise', 'Enterprise')
                                        ])
    status = models.CharField(max_length=20, default='trial', db_column='Status',
                             choices=[
                                 ('trial', 'Trial'),
                                 ('active', 'Active'),
                                 ('suspended', 'Suspended'),
                                 ('cancelled', 'Cancelled')
                             ])
    max_users = models.IntegerField(default=10, db_column='MaxUsers')
    storage_limit_gb = models.IntegerField(default=10, db_column='StorageLimitGB')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')
    trial_ends_at = models.DateTimeField(null=True, blank=True, db_column='TrialEndsAt')
    settings = models.JSONField(default=dict, db_column='Settings')
    primary_contact_email = models.EmailField(max_length=254, null=True, blank=True, db_column='PrimaryContactEmail')
    primary_contact_name = models.CharField(max_length=255, null=True, blank=True, db_column='PrimaryContactName')
    primary_contact_phone = models.CharField(max_length=50, null=True, blank=True, db_column='PrimaryContactPhone')
    
    class Meta:
        db_table = 'tenants'  # Note: table name is 'tenants' (plural) to match GRC
        ordering = ['name']
        indexes = [
            models.Index(fields=['subdomain'], name='uniq_tenants_subdomain'),
            models.Index(fields=['license_key'], name='uniq_tenants_licensekey'),
            models.Index(fields=['status'], name='idx_tenants_status'),
        ]
    
    def __str__(self):
        return self.name
```

#### 1.2 Create Tenant Context Manager

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

#### 1.3 Create Tenant Utilities

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
                    
                    # Get tenant from user
                    if user_id:
                        # Import Users model - adjust import path based on your structure
                        from mfa_auth.models import User
                        try:
                            user = User.objects.get(userid=user_id)
                            if hasattr(user, 'tenant_id'):
                                tenant_id = user.tenant_id
                            elif hasattr(user, 'tenant') and user.tenant:
                                tenant_id = user.tenant.tenant_id
                        except User.DoesNotExist:
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

#### 1.4 Create Tenant Middleware

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
            # Import Users model - adjust based on your structure
            from mfa_auth.models import User
            if hasattr(user, 'tenant') and user.tenant:
                if user.tenant.status == 'active':
                    return user.tenant
            elif hasattr(user, 'userid'):
                db_user = User.objects.select_related('tenant').filter(userid=user.userid).first()
                if db_user and db_user.tenant and db_user.tenant.status == 'active':
                    return db_user.tenant
        except Exception as e:
            logger.error(f"[Tenant Middleware] Error extracting tenant from user: {e}")
        return None
```

### Step 2: Update Settings

**File**: `grc_backend/tprm_backend/config/settings.py`

```python
# Add to MIDDLEWARE
MIDDLEWARE = [
    # ... other middleware
    'core.tenant_middleware.TenantContextMiddleware',  # Add this
    # ... rest of middleware
]
```

### Step 3: Update User Model

**File**: `grc_backend/tprm_backend/mfa_auth/models.py` (or wherever User model is)

```python
from django.db import models
from core.models import Tenant

class User(models.Model):
    # ... existing fields ...
    
    # MULTI-TENANCY: Add tenant ForeignKey
    tenant = models.ForeignKey(
        'core.Tenant',  # or 'Tenant' if in same app
        on_delete=models.CASCADE,
        db_column='TenantId',
        related_name='users',
        null=True,
        blank=True
    )
    
    # ... rest of model ...
```

### Step 4: Update Models

#### Example: RFP Model

**File**: `grc_backend/tprm_backend/rfp/models.py`

```python
from django.db import models
from core.models import TenantAwareModel, Tenant

class RFP(TenantAwareModel):  # Inherit from TenantAwareModel
    # ... existing fields ...
    
    # MULTI-TENANCY: Add tenant ForeignKey
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        db_column='TenantId',
        related_name='rfps',
        null=True,
        blank=True
    )
    
    # ... rest of model ...
```

#### Example: Contract Model

**File**: `grc_backend/tprm_backend/contracts/models.py`

```python
from django.db import models
from core.models import TenantAwareModel, Tenant

class Vendor(TenantAwareModel):
    # ... existing fields ...
    
    # MULTI-TENANCY: Add tenant ForeignKey
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        db_column='TenantId',
        related_name='vendors',
        null=True,
        blank=True
    )
    
    # ... rest of model ...
```

**Repeat this pattern for ALL tenant-aware models.**

### Step 5: Update Views

#### Example: RFP Views

**File**: `grc_backend/tprm_backend/rfp/views.py`

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.tenant_utils import require_tenant, tenant_filter, get_tenant_id_from_request
from .models import RFP

@api_view(['GET'])
@require_tenant  # MULTI-TENANCY: Ensure tenant exists
@tenant_filter   # MULTI-TENANCY: Extract tenant_id
def list_rfps(request):
    """
    List all RFPs for the current tenant
    MULTI-TENANCY: Only returns RFPs belonging to the user's tenant
    """
    tenant_id = get_tenant_id_from_request(request)
    
    if tenant_id is None:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
    # MULTI-TENANCY: Filter by tenant_id
    rfps = RFP.objects.filter(tenant_id=tenant_id)
    
    # Serialize and return
    data = [{
        'id': rfp.rfp_id,
        'title': rfp.rfp_title,
        # ... other fields
    } for rfp in rfps]
    
    return Response(data)

@api_view(['POST'])
@require_tenant
@tenant_filter
def create_rfp(request):
    """
    Create a new RFP
    MULTI-TENANCY: Automatically assigns RFP to user's tenant
    """
    tenant_id = get_tenant_id_from_request(request)
    
    if tenant_id is None:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
    # MULTI-TENANCY: Set tenant_id when creating
    rfp = RFP.objects.create(
        rfp_title=request.data['title'],
        description=request.data['description'],
        tenant_id=tenant_id  # Set tenant explicitly
    )
    
    return Response({
        'id': rfp.rfp_id,
        'title': rfp.rfp_title,
        # ... other fields
    }, status=201)

@api_view(['GET'])
@require_tenant
@tenant_filter
def get_rfp(request, rfp_id):
    """
    Get RFP by ID
    MULTI-TENANCY: Only returns RFP if it belongs to user's tenant
    """
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # MULTI-TENANCY: Filter by tenant_id
        rfp = RFP.objects.get(
            rfp_id=rfp_id,
            tenant_id=tenant_id
        )
        
        return Response({
            'id': rfp.rfp_id,
            'title': rfp.rfp_title,
            # ... other fields
        })
    except RFP.DoesNotExist:
        return Response({
            'error': 'RFP not found'
        }, status=404)

@api_view(['PUT'])
@require_tenant
@tenant_filter
def update_rfp(request, rfp_id):
    """
    Update RFP
    MULTI-TENANCY: Only allows update if RFP belongs to user's tenant
    """
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # MULTI-TENANCY: Filter by tenant_id
        rfp = RFP.objects.get(
            rfp_id=rfp_id,
            tenant_id=tenant_id
        )
        
        # Update fields
        rfp.rfp_title = request.data.get('title', rfp.rfp_title)
        rfp.description = request.data.get('description', rfp.description)
        rfp.save()
        
        return Response({
            'id': rfp.rfp_id,
            'title': rfp.rfp_title,
            # ... other fields
        })
    except RFP.DoesNotExist:
        return Response({
            'error': 'RFP not found'
        }, status=404)
```

**Apply this pattern to ALL views in ALL modules.**

### Step 6: Update Raw SQL Queries

If you have raw SQL queries, make sure to include `TenantId` filtering:

```python
@require_tenant
@tenant_filter
@api_view(['GET'])
def get_rfps_raw_sql(request):
    """Example with raw SQL"""
    tenant_id = get_tenant_id_from_request(request)
    
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Note: Use TenantId (capital T) in SQL to match database column
        cursor.execute("""
            SELECT * FROM rfp
            WHERE TenantId = %s  -- MULTI-TENANCY: Filter by tenant
        """, [tenant_id])
        
        columns = [col[0] for col in cursor.description]
        rfps = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return Response(rfps)
```

---

## Frontend Implementation

### Step 1: Update API Configuration

**File**: `grc_frontend/tprm_frontend/src/config/api.js`

The frontend should already be sending JWT tokens in the Authorization header. Ensure that:

1. JWT tokens are included in all API requests
2. Error handling for 403 (tenant context not found) is implemented
3. User is redirected to login if tenant context is missing

**No major changes needed** - the frontend already uses JWT authentication which will be used by the backend to extract tenant information.

### Step 2: Update Error Handling

Ensure the frontend handles tenant-related errors:

```javascript
// In api.js or axios interceptor
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 403) {
      const errorData = error.response.data;
      if (errorData?.error === 'Tenant context not found') {
        // Handle tenant context error
        console.error('Tenant context not found - redirecting to login');
        localStorage.clear();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

---

## Testing Strategy

### 1. Unit Tests

Create test file: `grc_backend/tprm_backend/test_tprm_multitenancy.py`

```python
"""
Multi-Tenancy Tests for TPRM
"""
import os
import django
from django.conf import settings

if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from django.test import TestCase, TransactionTestCase
from core.models import Tenant
from rfp.models import RFP
from contracts.models import Vendor
from core.tenant_context import set_current_tenant, clear_current_tenant

class TPRMMultiTenancyTestCase(TransactionTestCase):
    """Test suite for TPRM multi-tenancy"""
    
    def setUp(self):
        """Set up test data with multiple tenants"""
        # Create test tenants
        self.tenant1 = Tenant.objects.create(
            name="Test Company A",
            subdomain="testcompanya",
            license_key="TEST-LICENSE-A",
            status="active"
        )
        
        self.tenant2 = Tenant.objects.create(
            name="Test Company B",
            subdomain="testcompanyb",
            license_key="TEST-LICENSE-B",
            status="active"
        )
        
        # Create RFPs for each tenant
        set_current_tenant(self.tenant1.tenant_id)
        self.rfp1 = RFP.objects.create(
            rfp_title="RFP A",
            description="Test RFP for tenant 1",
            tenant_id=self.tenant1.tenant_id
        )
        
        set_current_tenant(self.tenant2.tenant_id)
        self.rfp2 = RFP.objects.create(
            rfp_title="RFP B",
            description="Test RFP for tenant 2",
            tenant_id=self.tenant2.tenant_id
        )
    
    def test_tenant_isolation_rfp(self):
        """Test that tenants can only see their own RFPs"""
        set_current_tenant(self.tenant1.tenant_id)
        rfps1 = RFP.objects.filter(tenant_id=self.tenant1.tenant_id)
        self.assertEqual(rfps1.count(), 1)
        self.assertEqual(rfps1.first().rfp_title, "RFP A")
        
        set_current_tenant(self.tenant2.tenant_id)
        rfps2 = RFP.objects.filter(tenant_id=self.tenant2.tenant_id)
        self.assertEqual(rfps2.count(), 1)
        self.assertEqual(rfps2.first().rfp_title, "RFP B")
        
        # Verify tenant1 cannot see tenant2's RFPs
        set_current_tenant(self.tenant1.tenant_id)
        cross_tenant_rfp = RFP.objects.filter(
            rfp_id=self.rfp2.rfp_id,
            tenant_id=self.tenant1.tenant_id
        ).first()
        self.assertIsNone(cross_tenant_rfp)
    
    def tearDown(self):
        """Clean up"""
        clear_current_tenant()
```

### 2. Integration Tests

Test API endpoints with different tenants to ensure isolation.

### 3. Security Audit

- Verify all endpoints filter by tenant_id
- Test cross-tenant access attempts
- Verify tenant_id cannot be overridden by user input

---

## Migration Guide

### Pre-Migration Checklist

1. ✅ Backup database
2. ✅ Review all models that need tenant_id
3. ✅ Plan data migration strategy
4. ✅ Schedule maintenance window
5. ✅ Prepare rollback plan

### Migration Steps

1. **Create Tenant table**
   ```bash
   python manage.py makemigrations core
   python manage.py migrate core
   ```

2. **Add TenantId to Users table**
   ```bash
   python manage.py makemigrations mfa_auth
   python manage.py migrate mfa_auth
   ```

3. **Add TenantId to all other tables**
   ```bash
   python manage.py makemigrations rfp contracts vendors risk_analysis compliance audits bcpdrp slas rbac
   python manage.py migrate
   ```

4. **Run data migration script** (assign existing data to default tenant)

5. **Update all models** (add tenant ForeignKey)

6. **Update all views** (add decorators and filtering)

7. **Test thoroughly**

8. **Deploy to production**

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
   rfps = RFP.objects.filter(tenant_id=tenant_id)
   ```

3. **Always set tenant_id when creating**:
   ```python
   rfp = RFP.objects.create(..., tenant_id=tenant_id)
   ```

4. **Validate tenant access before modifications**:
   ```python
   rfp = RFP.objects.get(rfp_id=id, tenant_id=tenant_id)
   ```

5. **Use TenantId (capital T) in raw SQL**:
   ```sql
   WHERE TenantId = %s
   ```

### ❌ DON'T

1. **Don't skip tenant filtering**:
   ```python
   # ❌ BAD
   rfps = RFP.objects.all()
   
   # ✅ GOOD
   rfps = RFP.objects.filter(tenant_id=tenant_id)
   ```

2. **Don't trust user-provided IDs without tenant check**:
   ```python
   # ❌ BAD
   rfp = RFP.objects.get(rfp_id=id)
   
   # ✅ GOOD
   rfp = RFP.objects.get(rfp_id=id, tenant_id=tenant_id)
   ```

3. **Don't forget to set tenant_id on create**:
   ```python
   # ❌ BAD
   rfp = RFP.objects.create(rfp_title='Test')
   
   # ✅ GOOD
   rfp = RFP.objects.create(rfp_title='Test', tenant_id=tenant_id)
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
rfps = RFP.objects.filter(tenant_id=tenant_id)  # Must include this
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
user = User.objects.get(userid=user_id)
print(f"DEBUG: user.tenant_id = {user.tenant_id}")  # Should not be None

# Check JWT token
token = request.headers.get('Authorization', '').split(' ')[1]
payload = jwt.decode(token, secret_key, algorithms=['HS256'])
print(f"DEBUG: payload = {payload}")  # Should contain user_id
```

### Issue: SQL Error "Unknown column 'tenant_id'"

**Symptom**: Raw SQL queries fail with column not found error.

**Cause**: Using wrong column name in SQL (should be `TenantId`, not `tenant_id`).

**Solution**:
```sql
-- ❌ Wrong
WHERE tenant_id = %s

-- ✅ Correct
WHERE TenantId = %s
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
rfp = RFP.objects.create(..., tenant_id=tenant_id)
```

---

## Summary

Multi-tenancy in TPRM works by:

1. **Database Level**: Every tenant-aware table has a `TenantId` column
2. **Model Level**: Models have a `tenant` ForeignKey field (maps to `tenant_id` in ORM)
3. **Request Level**: `@tenant_filter` decorator extracts `tenant_id` from authenticated user
4. **Query Level**: All queries include `.filter(tenant_id=tenant_id)`
5. **Validation Level**: `validate_tenant_access()` ensures users can only access their tenant's data

**Key Takeaway**: 
> **Every database query MUST filter by `tenant_id` to ensure data isolation between tenants.**

---

## Related Files

- `grc_backend/tprm_backend/core/models.py` - Tenant model and TenantAwareModel
- `grc_backend/tprm_backend/core/tenant_utils.py` - Core multitenancy utilities
- `grc_backend/tprm_backend/core/tenant_context.py` - Tenant context manager
- `grc_backend/tprm_backend/core/tenant_middleware.py` - Tenant middleware
- `grc_backend/tprm_backend/test_tprm_multitenancy.py` - Automated testing script

---

**Last Updated**: January 2026  
**Version**: 1.0

