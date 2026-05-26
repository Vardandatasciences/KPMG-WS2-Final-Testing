# Enterprise Multi-Tenancy Implementation Plan

## Project Overview
Transform existing basic multi-tenancy into a complete enterprise-grade Tenant Module using Shared Database + Shared Tables architecture.

**Current State:** 20 items exist | **Target State:** 88 total items  
**Gap:** 68 items need implementation

---

## Phase 1: Foundation (Models & Migrations)
**Priority:** CRITICAL  
**Duration:** 3-4 days  
**Status:** ⏳ Not Started

### 1.1 Fix Existing Models

| Model | Change | Location |
|-------|--------|----------|
| `Entity` | Add `tenant` FK | `grc/models.py` line ~2543 |
| `RBAC` | Add `tenant` FK | `grc/models.py` line ~2054 |
| `Tenant` | Expand `status` choices | `grc/models.py` line ~73 |

**Code Changes:**
```python
# Add to Entity model:
tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, db_column='TenantId',
                           related_name='entities', null=True, blank=True)

# Add to RBAC model:
tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, db_column='TenantId',
                          related_name='rbac_records', null=True, blank=True)

# Update Tenant.status choices:
STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('onboarding', 'Onboarding'),
    ('configuration_pending', 'Configuration Pending'),
    ('security_setup_pending', 'Security Setup Pending'),
    ('active', 'Active'),
    ('suspended', 'Suspended'),
    ('inactive', 'Inactive'),
    ('archived', 'Archived'),
]
```

### 1.2 New Models (8 Tables)

#### Model 1: BusinessUnit
**File:** `grc/models.py`  
**Fields:**
```python
class BusinessUnit(EncryptedFieldsMixin, models.Model):
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, db_column='TenantId')
    entity = models.ForeignKey('Entity', on_delete=models.CASCADE, db_column='EntityId')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    head = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True, blank=True)
    parent_bu = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, default='active')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'business_units'
```

#### Model 2: TenantUserMapping
**File:** `grc/models.py`  
**Fields:**
```python
class TenantUserMapping(EncryptedFieldsMixin, models.Model):
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, db_column='TenantId')
    user = models.ForeignKey('Users', on_delete=models.CASCADE, db_column='UserId')
    role = models.CharField(max_length=100)  # GRC Administrator, Viewer, etc.
    is_primary = models.BooleanField(default=False)
    assigned_by = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True, related_name='tenant_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='active')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_user_mapping'
        unique_together = ['tenant', 'user']
```

#### Model 3: UserEntityMapping
**File:** `grc/models.py`  
**Fields:**
```python
class UserEntityMapping(EncryptedFieldsMixin, models.Model):
    ACCESS_LEVELS = [
        ('read', 'Read Only'),
        ('write', 'Read Write'),
        ('admin', 'Admin'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', on_delete=models.CASCADE, db_column='UserId')
    entity = models.ForeignKey('Entity', on_delete=models.CASCADE)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, db_column='TenantId')
    role = models.CharField(max_length=100)
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVELS, default='read')
    assigned_by = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True, related_name='entity_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='active')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_entity_mapping'
        unique_together = ['user', 'entity']
```

#### Model 4: TenantModule
**File:** `grc/models.py`  
**Fields:**
```python
class TenantModule(EncryptedFieldsMixin, models.Model):
    MODULE_CHOICES = [
        ('framework', 'Framework'),
        ('policy', 'Policy'),
        ('compliance', 'Compliance'),
        ('audit', 'Audit'),
        ('risk', 'Risk'),
        ('incident', 'Incident'),
        ('event', 'Event'),
    ]
    
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, db_column='TenantId')
    module_code = models.CharField(max_length=50, choices=MODULE_CHOICES)
    is_enabled = models.BooleanField(default=True)
    license_tier = models.CharField(max_length=50, default='basic')
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    user_limit = models.IntegerField(null=True, blank=True)
    storage_limit_gb = models.IntegerField(null=True, blank=True)
    api_limit = models.IntegerField(null=True, blank=True)
    ai_limit = models.IntegerField(null=True, blank=True)
    configured_by = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True)
    configured_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_modules'
        unique_together = ['tenant', 'module_code']
```

#### Model 5: TenantSecuritySettings
**File:** `grc/models.py`  
**Fields:**
```python
class TenantSecuritySettings(EncryptedFieldsMixin, models.Model):
    id = models.AutoField(primary_key=True)
    tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE, db_column='TenantId', related_name='security_settings')
    
    # MFA
    mfa_required = models.BooleanField(default=False)
    mfa_methods = models.JSONField(default=list, help_text="['email', 'totp']")
    
    # SSO
    sso_enabled = models.BooleanField(default=False)
    sso_provider = models.CharField(max_length=50, null=True, blank=True)
    sso_config = models.JSONField(default=dict)
    
    # Access Control
    allowed_email_domains = models.JSONField(default=list, help_text="['company.com', 'subsidiary.com']")
    ip_restriction_enabled = models.BooleanField(default=False)
    allowed_ip_ranges = models.JSONField(default=list, help_text="['192.168.1.0/24', '10.0.0.0/8']")
    
    # Session & Password
    session_timeout_minutes = models.IntegerField(default=30)
    password_expiry_days = models.IntegerField(default=90)
    
    # Export
    export_allowed = models.BooleanField(default=True)
    export_requires_approval = models.BooleanField(default=False)
    
    # Audit
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'tenant_security_settings'
```

#### Model 6: TenantBranding
**File:** `grc/models.py`  
**Fields:**
```python
class TenantBranding(EncryptedFieldsMixin, models.Model):
    id = models.AutoField(primary_key=True)
    tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE, db_column='TenantId', related_name='branding')
    
    # Assets
    logo_url = models.CharField(max_length=500, null=True, blank=True)
    favicon_url = models.CharField(max_length=500, null=True, blank=True)
    
    # Colors
    primary_color = models.CharField(max_length=7, default='#1976D2')  # Hex
    secondary_color = models.CharField(max_length=7, default='#424242')
    accent_color = models.CharField(max_length=7, default='#82B1FF')
    
    # Customization
    custom_css = models.TextField(null=True, blank=True)
    login_page_custom_html = models.TextField(null=True, blank=True)
    
    # Email
    email_template_logo = models.CharField(max_length=500, null=True, blank=True)
    email_footer_text = models.TextField(null=True, blank=True)
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'tenant_branding'
```

#### Model 7: TenantAuditLog
**File:** `grc/models.py`  
**Fields:**
```python
class TenantAuditLog(EncryptedFieldsMixin, models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('ACTIVATE', 'Activate'),
        ('SUSPEND', 'Suspend'),
        ('ARCHIVE', 'Archive'),
        ('MAP_USER', 'Map User'),
        ('UNMAP_USER', 'Unmap User'),
        ('ENABLE_MODULE', 'Enable Module'),
        ('DISABLE_MODULE', 'Disable Module'),
    ]
    
    ENTITY_CHOICES = [
        ('tenant', 'Tenant'),
        ('entity', 'Entity'),
        ('business_unit', 'Business Unit'),
        ('department', 'Department'),
        ('user', 'User'),
        ('module', 'Module'),
        ('security', 'Security Settings'),
        ('branding', 'Branding'),
        ('support_access', 'Support Access'),
    ]
    
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, db_column='TenantId')
    
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=50, choices=ENTITY_CHOICES)
    entity_id = models.IntegerField()
    entity_name = models.CharField(max_length=255)
    
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    performed_by = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'tenant_audit_log'
        ordering = ['-performed_at']
```

#### Model 8: SupportAccessRequest
**File:** `grc/models.py`  
**Fields:**
```python
class SupportAccessRequest(EncryptedFieldsMixin, models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('revoked', 'Revoked'),
        ('expired', 'Expired'),
    ]
    
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, db_column='TenantId')
    
    support_user = models.ForeignKey('Users', on_delete=models.CASCADE, related_name='support_access_requests')
    request_reason = models.TextField()
    requested_at = models.DateTimeField(auto_now_add=True)
    
    approved_by = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_support_access')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    access_token = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    last_used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'support_access_request'
```

### 1.3 Generate Migrations

```bash
# Terminal commands:
cd grc_backend
python manage.py makemigrations grc --name add_multitenancy_enhancement
python manage.py migrate
```

### 1.4 Data Migration Scripts

**Script 1:** Populate TenantModule for existing tenants
```python
# grc/migrations/populate_tenant_modules.py
MODULES = ['framework', 'policy', 'compliance', 'audit', 'risk', 'incident', 'event']

for tenant in Tenant.objects.all():
    for module in MODULES:
        TenantModule.objects.get_or_create(
            tenant=tenant,
            module_code=module,
            defaults={'is_enabled': True, 'license_tier': 'enterprise'}
        )
```

**Script 2:** Populate default security settings
```python
for tenant in Tenant.objects.all():
    TenantSecuritySettings.objects.get_or_create(
        tenant=tenant,
        defaults={'mfa_required': False, 'session_timeout_minutes': 30}
    )
```

**Script 3:** Backfill Entity.tenant_id
```python
# Infer from related departments/users
for dept in Department.objects.filter(tenant__isnull=False):
    Entity.objects.filter(Id=dept.EntityId).update(tenant=dept.tenant)
```

---

## Phase 2: Backend APIs
**Priority:** HIGH  
**Duration:** 5-6 days  
**Status:** ⏳ Not Started

### 2.1 Register Existing Tenant APIs

**File:** `grc/urls.py` (add routes)

```python
from .routes.Global import tenant_views

urlpatterns += [
    # Tenant CRUD
    path('api/tenants/', tenant_views.list_tenants, name='list-tenants'),
    path('api/tenants/create/', tenant_views.create_tenant, name='create-tenant'),
    path('api/tenants/<int:tenant_id>/', tenant_views.get_tenant, name='get-tenant'),
    path('api/tenants/<int:tenant_id>/update/', tenant_views.update_tenant, name='update-tenant'),
    
    # Lifecycle
    path('api/tenants/<int:tenant_id>/activate/', tenant_views.activate_tenant, name='activate-tenant'),
    path('api/tenants/<int:tenant_id>/suspend/', tenant_views.suspend_tenant, name='suspend-tenant'),
    path('api/tenants/<int:tenant_id>/archive/', tenant_views.archive_tenant, name='archive-tenant'),
    
    # Audit
    path('api/tenants/<int:tenant_id>/audit-logs/', tenant_views.get_tenant_audit_logs, name='tenant-audit-logs'),
]
```

### 2.2 Entity Management APIs

**New File:** `grc/routes/Global/entity_views.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tenants/{tenant_id}/entities/` | POST | Create entity |
| `/api/tenants/{tenant_id}/entities/` | GET | List entities |
| `/api/tenants/{tenant_id}/entities/tree/` | GET | Get hierarchy tree |
| `/api/entities/{entity_id}/` | GET | Get entity details |
| `/api/entities/{entity_id}/` | PUT | Update entity |
| `/api/entities/{entity_id}/` | DELETE | Soft delete entity |
| `/api/entities/{entity_id}/users/` | GET | Get users in entity |

**Implementation Pattern:**
```python
@api_view(['POST'])
@require_tenant
def create_entity(request, tenant_id):
    # Validate user has access to this tenant
    # Validate tenant exists and is active
    # Create entity with tenant_id
    # Log to TenantAuditLog
    return Response({'id': entity.id, 'status': 'created'})
```

### 2.3 Business Unit APIs

**New File:** `grc/routes/Global/business_unit_views.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/entities/{entity_id}/business-units/` | POST | Create BU |
| `/api/entities/{entity_id}/business-units/` | GET | List BUs |
| `/api/business-units/{bu_id}/` | GET | Get BU |
| `/api/business-units/{bu_id}/` | PUT | Update BU |
| `/api/business-units/{bu_id}/` | DELETE | Soft delete BU |

### 2.4 Department APIs

**New File:** `grc/routes/Global/department_views.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/business-units/{bu_id}/departments/` | POST | Create department |
| `/api/business-units/{bu_id}/departments/` | GET | List departments |
| `/api/departments/{dept_id}/` | PUT | Update department |
| `/api/departments/{dept_id}/assign-user/` | POST | Assign user to department |

### 2.5 User Mapping APIs

**New File:** `grc/routes/Global/user_mapping_views.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tenants/{tenant_id}/map-user/` | POST | Add user to tenant |
| `/api/tenants/{tenant_id}/unmap-user/{user_id}/` | DELETE | Remove user from tenant |
| `/api/tenants/{tenant_id}/set-primary-user/{user_id}/` | PUT | Set primary tenant |
| `/api/entities/{entity_id}/map-user/` | POST | Add user to entity |
| `/api/users/{user_id}/tenants/` | GET | Get user's tenants |
| `/api/users/{user_id}/entities/` | GET | Get user's entities |

### 2.6 Module Management APIs

**New File:** `grc/routes/Global/module_views.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tenants/{tenant_id}/modules/` | GET | Get enabled modules |
| `/api/tenants/{tenant_id}/modules/` | PUT | Update modules |
| `/api/modules/available/` | GET | List all available modules |
| `/api/tenants/{tenant_id}/module-status/{module}/` | GET | Check if module enabled |

### 2.7 Security Settings APIs

**New File:** `grc/routes/Global/security_settings_views.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tenants/{tenant_id}/security-settings/` | GET | Get settings |
| `/api/tenants/{tenant_id}/security-settings/` | PUT | Update settings |
| `/api/tenants/{tenant_id}/test-ip-restriction/` | POST | Test IP against rules |
| `/api/tenants/{tenant_id}/security-audit/` | GET | Security change history |

### 2.8 Branding APIs

**New File:** `grc/routes/Global/branding_views.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tenants/{tenant_id}/branding/` | GET | Get branding |
| `/api/tenants/{tenant_id}/branding/` | PUT | Update branding |
| `/api/tenants/{tenant_id}/branding/upload-logo/` | POST | Upload logo |
| `/api/public/branding/{tenant_id}/` | GET | Public branding (unauth) |

### 2.9 Support Access APIs

**New File:** `grc/routes/Global/support_access_views.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/support-access/request/` | POST | Request access |
| `/api/tenant-admins/{tenant_id}/support-requests/` | GET | View pending requests |
| `/api/support-access/{request_id}/approve/` | POST | Approve request |
| `/api/support-access/{request_id}/revoke/` | POST | Revoke request |
| `/api/support-access/my-accesses/` | GET | View my active accesses |
| `/api/tenants/{tenant_id}/support-history/` | GET | Access history |

---

## Phase 3: Middleware & Access Control
**Priority:** HIGH  
**Duration:** 4-5 days  
**Status:** ⏳ Not Started

### 3.1 Enhanced Tenant Middleware

**File:** `grc/tenant_middleware.py` (update)

**Additions:**
```python
class TenantContextMiddleware:
    def process_request(self, request):
        # Existing: resolve tenant
        # NEW: Resolve entity_id from JWT
        # NEW: Resolve BU_id, dept_id from JWT
        # NEW: Validate user belongs to tenant via TenantUserMapping
        # NEW: Check tenant status gates (block if not ACTIVE)
        
        entity_id = self._get_entity_from_jwt(request)
        request.entity_id = entity_id
        
        # Validate user-tenant mapping
        if not self._validate_user_tenant_mapping(request.user, request.tenant_id):
            return JsonResponse({'error': 'User not mapped to tenant'}, status=403)
```

### 3.2 Module Enforcement Middleware

**New File:** `grc/module_middleware.py`

```python
class ModuleEnforcementMiddleware(MiddlewareMixin):
    """Block API calls for disabled modules"""
    
    MODULE_PATHS = {
        '/api/framework': 'framework',
        '/api/policy': 'policy',
        '/api/compliance': 'compliance',
        '/api/audit': 'audit',
        '/api/risk': 'risk',
        '/api/incident': 'incident',
        '/api/event': 'event',
    }
    
    def process_request(self, request):
        # Skip for superadmin/platform admin
        if self._is_platform_admin(request.user):
            return None
            
        # Check if path matches a module
        module_code = self._get_module_from_path(request.path)
        if not module_code:
            return None
            
        # Check if module enabled for tenant
        tenant_id = get_tenant_id_from_request(request)
        if not self._is_module_enabled(tenant_id, module_code):
            return JsonResponse({
                'error': 'Module not enabled for this tenant',
                'module': module_code
            }, status=403)
```

### 3.3 Entity Access Middleware

**New File:** `grc/entity_middleware.py`

```python
class EntityAccessMiddleware(MiddlewareMixin):
    """Validate user has access to selected entity"""
    
    def process_request(self, request):
        entity_id = request.GET.get('entity_id') or request.POST.get('entity_id')
        if not entity_id:
            return None
            
        user_id = request.user.UserId
        tenant_id = get_tenant_id_from_request(request)
        
        # Check UserEntityMapping
        if not UserEntityMapping.objects.filter(
            user_id=user_id,
            entity_id=entity_id,
            tenant_id=tenant_id,
            status='active'
        ).exists():
            return JsonResponse({
                'error': 'Access denied to this entity'
            }, status=403)
```

### 3.4 Security Enforcement Middleware

**New File:** `grc/security_middleware.py`

```python
class TenantSecurityMiddleware(MiddlewareMixin):
    """Enforce tenant-level security settings"""
    
    def process_request(self, request):
        tenant_id = get_tenant_id_from_request(request)
        if not tenant_id:
            return None
            
        settings = TenantSecuritySettings.objects.filter(tenant_id=tenant_id).first()
        if not settings:
            return None
            
        # Check IP restriction
        if settings.ip_restriction_enabled:
            client_ip = self._get_client_ip(request)
            if not self._is_ip_allowed(client_ip, settings.allowed_ip_ranges):
                return JsonResponse({'error': 'IP not allowed'}, status=403)
```

### 3.5 Updated Login Response

**File:** `grc/authentication.py` (update `jwt_login()`)

**Current Response:**
```json
{
  "access": "...",
  "refresh": "...",
  "tenant_id": 1,
  "tenant_name": "Acme Corp"
}
```

**New Response:**
```json
{
  "access": "...",
  "refresh": "...",
  "tenant_id": 1,
  "tenant_name": "Acme Corp",
  "allowed_tenants": [
    {"id": 1, "name": "Acme Corp", "role": "Admin"},
    {"id": 2, "name": "Subsidiary", "role": "Viewer"}
  ],
  "allowed_entities": [
    {"id": 1, "name": "Headquarters", "access_level": "admin"},
    {"id": 2, "name": "Branch Office", "access_level": "read"}
  ],
  "selected_entity_id": 1,
  "roles": ["GRC Administrator", "Compliance Manager"],
  "permissions": ["create_policy", "edit_compliance", "view_audit"],
  "enabled_modules": ["framework", "policy", "compliance", "audit"],
  "security_settings": {
    "mfa_required": false,
    "session_timeout_minutes": 30,
    "password_expiry_days": 90
  },
  "branding": {
    "logo_url": "https://...",
    "primary_color": "#1976D2",
    "secondary_color": "#424242"
  }
}
```

---

## Phase 4: Frontend Implementation
**Priority:** MEDIUM  
**Duration:** 7-8 days  
**Status:** ⏳ Not Started

### 4.1 Global State Management

**New File:** `grc_frontend/src/stores/tenant.js`

```javascript
import { defineStore } from 'pinia'

export const useTenantStore = defineStore('tenant', {
  state: () => ({
    currentTenant: null,
    currentEntity: null,
    allowedTenants: [],
    allowedEntities: [],
    enabledModules: [],
    securitySettings: {},
    branding: {},
    roles: [],
    permissions: []
  }),
  
  getters: {
    hasModuleAccess: (state) => (moduleCode) => {
      return state.enabledModules.includes(moduleCode)
    },
    isTenantAdmin: (state) => {
      return state.roles.includes('GRC Administrator')
    },
    canAccessEntity: (state) => (entityId) => {
      return state.allowedEntities.some(e => e.id === entityId)
    }
  },
  
  actions: {
    async fetchTenantContext() {
      const response = await tenantService.getMyTenantContext()
      this.currentTenant = response.data.current_tenant
      this.currentEntity = response.data.selected_entity
      this.allowedTenants = response.data.allowed_tenants
      this.allowedEntities = response.data.allowed_entities
      this.enabledModules = response.data.enabled_modules
      this.securitySettings = response.data.security_settings
      this.branding = response.data.branding
      this.roles = response.data.roles
      this.permissions = response.data.permissions
    },
    
    async switchTenant(tenantId) {
      await tenantService.switchTenant(tenantId)
      await this.fetchTenantContext()
    },
    
    async switchEntity(entityId) {
      this.currentEntity = this.allowedEntities.find(e => e.id === entityId)
      localStorage.setItem('selected_entity_id', entityId)
    }
  }
})
```

### 4.2 Tenant Admin Pages

**File Structure:**
```
grc_frontend/src/components/TenantAdmin/
├── TenantList.vue
├── TenantCreate.vue
├── TenantDetail.vue
│   └── tabs/
│       ├── Overview.vue
│       ├── Entities.vue
│       ├── BusinessUnits.vue
│       ├── Departments.vue
│       ├── Users.vue
│       ├── Roles.vue
│       ├── Modules.vue
│       ├── Security.vue
│       ├── Branding.vue
│       ├── Workflows.vue
│       ├── License.vue
│       ├── AuditLogs.vue
│       └── SupportAccess.vue
├── EntityTree.vue
└── TenantSwitcher.vue
```

**Component: TenantList.vue**
```vue
<template>
  <div class="tenant-list">
    <v-data-table
      :headers="headers"
      :items="tenants"
      :loading="loading"
    >
      <template #item.status="{ item }">
        <v-chip :color="getStatusColor(item.status)">
          {{ item.status }}
        </v-chip>
      </template>
      
      <template #item.actions="{ item }">
        <v-btn icon @click="viewTenant(item)">
          <v-icon>mdi-eye</v-icon>
        </v-btn>
        <v-btn icon @click="editTenant(item)" v-if="isPlatformAdmin">
          <v-icon>mdi-pencil</v-icon>
        </v-btn>
        <v-btn icon @click="activateTenant(item)" v-if="item.status === 'configuration_pending'">
          <v-icon color="success">mdi-check-circle</v-icon>
        </v-btn>
      </template>
    </v-data-table>
  </div>
</template>
```

### 4.3 Header/Layout Updates

**File:** `grc_frontend/src/components/Layout/AppHeader.vue` (update)

```vue
<template>
  <v-app-bar>
    <!-- Existing items -->
    
    <!-- NEW: Tenant Switcher -->
    <TenantSwitcher 
      v-if="allowedTenants.length > 1"
      :tenants="allowedTenants"
      :current="currentTenant"
      @switch="switchTenant"
    />
    
    <!-- NEW: Entity Switcher -->
    <EntitySwitcher
      v-if="allowedEntities.length > 1"
      :entities="allowedEntities"
      :current="currentEntity"
      @switch="switchEntity"
    />
  </v-app-bar>
</template>
```

**File:** `grc_frontend/src/components/Layout/Sidebar.vue` (update)

```vue
<template>
  <v-navigation-drawer>
    <v-list>
      <!-- Filter by enabled modules -->
      <v-list-item
        v-for="item in filteredMenuItems"
        :key="item.path"
        :to="item.path"
        v-show="hasModuleAccess(item.module)"
      >
        <v-list-item-icon>
          <v-icon>{{ item.icon }}</v-icon>
        </v-list-item-icon>
        <v-list-item-title>{{ item.title }}</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-navigation-drawer>
</template>

<script>
computed: {
  filteredMenuItems() {
    return this.menuItems.filter(item => {
      // Check if module is enabled for tenant
      return this.tenantStore.hasModuleAccess(item.module)
    })
  }
}
</script>
```

### 4.4 Services

**New File:** `grc_frontend/src/services/tenantService.js`

```javascript
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export const tenantService = {
  // Tenant CRUD
  createTenant(data) {
    return axios.post(`${API_BASE_URL}/api/tenants/create/`, data)
  },
  
  listTenants(params = {}) {
    return axios.get(`${API_BASE_URL}/api/tenants/`, { params })
  },
  
  getTenant(tenantId) {
    return axios.get(`${API_BASE_URL}/api/tenants/${tenantId}/`)
  },
  
  updateTenant(tenantId, data) {
    return axios.put(`${API_BASE_URL}/api/tenants/${tenantId}/`, data)
  },
  
  activateTenant(tenantId) {
    return axios.post(`${API_BASE_URL}/api/tenants/${tenantId}/activate/`)
  },
  
  suspendTenant(tenantId) {
    return axios.post(`${API_BASE_URL}/api/tenants/${tenantId}/suspend/`)
  },
  
  // Entities
  createEntity(tenantId, data) {
    return axios.post(`${API_BASE_URL}/api/tenants/${tenantId}/entities/`, data)
  },
  
  getEntityTree(tenantId) {
    return axios.get(`${API_BASE_URL}/api/tenants/${tenantId}/entities/tree/`)
  },
  
  // User Mapping
  mapUserToTenant(tenantId, userId, role) {
    return axios.post(`${API_BASE_URL}/api/tenants/${tenantId}/map-user/`, { user_id: userId, role })
  },
  
  getMyTenantContext() {
    return axios.get(`${API_BASE_URL}/api/users/me/tenant-context/`)
  },
  
  switchTenant(tenantId) {
    return axios.post(`${API_BASE_URL}/api/users/me/switch-tenant/`, { tenant_id: tenantId })
  }
}
```

---

## Phase 5: Testing & Validation
**Priority:** CRITICAL  
**Duration:** 3-4 days  
**Status:** ⏳ Not Started

### 5.1 Unit Tests

**File:** `grc_backend/grc/tests/test_tenant_models.py`

```python
def test_tenant_soft_delete():
    tenant = Tenant.objects.create(name="Test", subdomain="test")
    tenant.is_deleted = True
    tenant.save()
    assert Tenant.objects.filter(is_deleted=False).count() == 0

def test_entity_hierarchy():
    parent = Entity.objects.create(name="Parent", tenant=tenant)
    child = Entity.objects.create(name="Child", tenant=tenant, ParentEntityId=parent.Id)
    assert child.ParentEntityId == parent.Id

def test_user_tenant_mapping_uniqueness():
    # Should enforce unique_together on tenant+user
    TenantUserMapping.objects.create(tenant=tenant, user=user, role="Admin")
    with pytest.raises(IntegrityError):
        TenantUserMapping.objects.create(tenant=tenant, user=user, role="Viewer")
```

### 5.2 Integration Tests

**File:** `grc_backend/grc/tests/test_cross_tenant_isolation.py`

```python
def test_user_cannot_access_other_tenant_data():
    user_a = Users.objects.create(tenant=tenant_a)
    framework = Framework.objects.create(tenant=tenant_b, name="Private")
    
    # User A tries to access Tenant B's framework
    response = client.get(f'/api/frameworks/{framework.FrameworkId}/')
    assert response.status_code == 403

def test_disabled_module_returns_403():
    TenantModule.objects.filter(tenant=tenant, module_code='risk').update(is_enabled=False)
    
    response = client.get('/api/system-risks/')
    assert response.status_code == 403
    assert 'Module not enabled' in response.json()['error']
```

### 5.3 Security Tests

**File:** `grc_backend/grc/tests/test_tenant_security.py`

```python
def test_bola_protection():
    # User belongs to tenant 1, tries to access tenant 2's data
    response = client.get('/api/tenants/2/entities/', headers={'X-Tenant-Id': '2'})
    assert response.status_code == 403

def test_suspended_tenant_login_blocked():
    tenant.status = 'suspended'
    tenant.save()
    
    response = client.post('/api/jwt/login/', {'username': 'user', 'password': 'pass'})
    assert response.status_code == 403
    assert 'Tenant suspended' in response.json()['error']

def test_ip_restriction_enforcement():
    settings = TenantSecuritySettings.objects.get(tenant=tenant)
    settings.ip_restriction_enabled = True
    settings.allowed_ip_ranges = ['192.168.1.0/24']
    settings.save()
    
    # Request from blocked IP
    response = client.get('/api/frameworks/', REMOTE_ADDR='10.0.0.1')
    assert response.status_code == 403
```

### 5.4 E2E Tests

**File:** `grc_frontend/tests/e2e/tenant-admin.spec.js`

```javascript
test('create tenant and verify activation gates', async ({ page }) => {
  await page.goto('/tenant-admin')
  await page.click('[data-testid="create-tenant-btn"]')
  
  // Try to activate without completing required fields
  await page.fill('[name="name"]', 'Test Tenant')
  await page.click('[data-testid="activate-btn"]')
  
  // Should show error about missing entity
  await expect(page.locator('.error-message')).toContainText('At least one entity required')
})
```

---

## Phase 6: Deployment & Migration
**Priority:** MEDIUM  
**Duration:** 2 days  
**Status:** ⏳ Not Started

### 6.1 Feature Flags

**File:** `backend/settings.py`

```python
# Multi-tenancy feature flags
MULTITENANCY_ENHANCED = os.getenv('MULTITENANCY_ENHANCED', 'True') == 'True'
ENFORCE_ENTITY_ACCESS = os.getenv('ENFORCE_ENTITY_ACCESS', 'False') == 'True'
ENFORCE_MODULE_ACCESS = os.getenv('ENFORCE_MODULE_ACCESS', 'False') == 'True'
ENFORCE_TENANT_SECURITY = os.getenv('ENFORCE_TENANT_SECURITY', 'False') == 'True'
```

### 6.2 Deployment Checklist

- [ ] Backup database
- [ ] Run migrations in staging
- [ ] Run data migration scripts
- [ ] Verify tenant isolation with test queries
- [ ] Enable feature flags gradually
- [ ] Monitor error logs for 48 hours
- [ ] Rollback plan ready

---

## Implementation Timeline

| Week | Phase | Focus | Deliverables |
|------|-------|-------|--------------|
| Week 1 | Phase 1 | Models & Migrations | 8 new tables, 3 model fixes, data migration scripts |
| Week 2 | Phase 2 | Backend APIs | 40+ API endpoints, URL routing |
| Week 3 | Phase 3 | Middleware | 4 new middleware classes, login response update |
| Week 4 | Phase 4 | Frontend | Tenant admin UI, entity tree, switchers |
| Week 5 | Phase 4 cont + Phase 5 | Finish frontend + Testing | All UI components, unit/integration/security tests |
| Week 6 | Phase 6 | Deployment | Feature flags, monitoring, bug fixes |

---

## Critical Dependencies

```
Models → APIs → Frontend
       ↓
    Middleware (depends on both)
       ↓
    Testing (covers all)
```

**Blocking Order:**
1. Models must be done before APIs
2. APIs must be done before Frontend
3. Middleware depends on Models + APIs
4. Login response update affects Frontend auth flow
5. Data migration must run after model migrations
6. Testing must cover all middleware changes (security critical)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Code Coverage | >85% for new code |
| Cross-tenant leakage tests | 100% pass |
| API response time (p95) | <200ms |
| Tenant switch time | <500ms |
| Zero data corruption incidents | Maintain through deployment |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Data migration failure | Full DB backup, rollback scripts, dry-run in staging |
| Performance degradation | Feature flags to disable, query optimization, caching |
| Cross-tenant data leak | Comprehensive security tests, code review for all tenant filters |
| Breaking existing functionality | Gradual rollout with feature flags, extensive regression testing |
| User confusion | In-app guidance, admin documentation, training materials |

---

**Document Version:** 1.0  
**Created:** 2026-05-15  
**Status:** Ready for Implementation
