# TPRM Multi-Tenancy Implementation Checklist

## Quick Reference Checklist

Use this checklist to track your progress implementing multi-tenancy across all TPRM modules.

---

## Phase 1: Core Infrastructure ✅

- [ ] Create `core/models.py` with `Tenant` and `TenantAwareModel`
- [ ] Create `core/tenant_context.py` with context manager
- [ ] Create `core/tenant_utils.py` with decorators and helpers
- [ ] Create `core/tenant_middleware.py` with middleware
- [ ] Add middleware to `config/settings.py` MIDDLEWARE list
- [ ] Create database migration for `tenant` table
- [ ] Run migration: `python manage.py migrate core`

---

## Phase 2: Database Schema ✅

### Users Table
- [ ] Add `TenantId` column to `users` table
- [ ] Add foreign key constraint
- [ ] Add index on `TenantId`
- [ ] Create migration
- [ ] Run migration

### RFP Module
- [ ] Add `TenantId` to `rfp` table
- [ ] Add `TenantId` to `rfp_evaluation_criteria` table
- [ ] Add `TenantId` to `file_storage` table
- [ ] Add foreign keys and indexes
- [ ] Create migrations
- [ ] Run migrations

### Contracts Module
- [ ] Add `TenantId` to `contracts` table (or `vendors` table)
- [ ] Add `TenantId` to `contract_approval` table
- [ ] Add foreign keys and indexes
- [ ] Create migrations
- [ ] Run migrations

### Vendors Module
- [ ] Add `TenantId` to `vendors` table
- [ ] Add `TenantId` to `vendor_categories` table
- [ ] Add foreign keys and indexes
- [ ] Create migrations
- [ ] Run migrations

### Risk Analysis Module
- [ ] Add `TenantId` to `risk_analysis` table
- [ ] Add `TenantId` to `vendor_risk_analysis` table
- [ ] Add foreign keys and indexes
- [ ] Create migrations
- [ ] Run migrations

### Compliance Module
- [ ] Add `TenantId` to `compliance` table
- [ ] Add foreign keys and indexes
- [ ] Create migrations
- [ ] Run migrations

### Audits Module
- [ ] Add `TenantId` to `audits` table
- [ ] Add `TenantId` to `audits_contract` table
- [ ] Add foreign keys and indexes
- [ ] Create migrations
- [ ] Run migrations

### BCP/DRP Module
- [ ] Add `TenantId` to `plan` table
- [ ] Add `TenantId` to `bcp_drp_approvals` table
- [ ] Add foreign keys and indexes
- [ ] Create migrations
- [ ] Run migrations

### SLAs Module
- [ ] Add `TenantId` to `slas` table
- [ ] Add foreign keys and indexes
- [ ] Create migrations
- [ ] Run migrations

### RBAC Module
- [ ] Add `TenantId` to `rbac_tprm` table
- [ ] Add `TenantId` to `AccessRequestTPRM` table
- [ ] Add foreign keys and indexes
- [ ] Create migrations
- [ ] Run migrations

### Data Migration
- [ ] Create default tenant
- [ ] Assign all existing users to default tenant
- [ ] Assign all existing data to default tenant
- [ ] Verify data integrity

---

## Phase 3: Model Updates ✅

### User Model
- [ ] Add `tenant` ForeignKey to User model
- [ ] Update model to inherit from TenantAwareModel (if applicable)
- [ ] Test model creation

### RFP Models
- [ ] Update `RFP` model - add `tenant` ForeignKey
- [ ] Update `RFPEvaluationCriteria` model - add `tenant` ForeignKey
- [ ] Update `FileStorage` model - add `tenant` ForeignKey
- [ ] Make models inherit from `TenantAwareModel`
- [ ] Test model creation

### Contract Models
- [ ] Update `Vendor` model - add `tenant` ForeignKey
- [ ] Update `Contract` model - add `tenant` ForeignKey (if exists)
- [ ] Update approval models - add `tenant` ForeignKey
- [ ] Make models inherit from `TenantAwareModel`
- [ ] Test model creation

### Vendor Models
- [ ] Update all vendor-related models - add `tenant` ForeignKey
- [ ] Make models inherit from `TenantAwareModel`
- [ ] Test model creation

### Risk Analysis Models
- [ ] Update risk analysis models - add `tenant` ForeignKey
- [ ] Make models inherit from `TenantAwareModel`
- [ ] Test model creation

### Compliance Models
- [ ] Update compliance models - add `tenant` ForeignKey
- [ ] Make models inherit from `TenantAwareModel`
- [ ] Test model creation

### Audit Models
- [ ] Update audit models - add `tenant` ForeignKey
- [ ] Make models inherit from `TenantAwareModel`
- [ ] Test model creation

### BCP/DRP Models
- [ ] Update BCP/DRP models - add `tenant` ForeignKey
- [ ] Make models inherit from `TenantAwareModel`
- [ ] Test model creation

### SLA Models
- [ ] Update SLA models - add `tenant` ForeignKey
- [ ] Make models inherit from `TenantAwareModel`
- [ ] Test model creation

### RBAC Models
- [ ] Update RBAC models - add `tenant` ForeignKey
- [ ] Make models inherit from `TenantAwareModel`
- [ ] Test model creation

---

## Phase 4: View Updates ✅

### RFP Views
- [ ] Add `@require_tenant` decorator to all views
- [ ] Add `@tenant_filter` decorator to all views
- [ ] Update all GET queries to filter by `tenant_id`
- [ ] Update all POST/CREATE to set `tenant_id`
- [ ] Update all PUT/UPDATE to filter by `tenant_id`
- [ ] Update all DELETE to filter by `tenant_id`
- [ ] Update raw SQL queries to include `TenantId` filter
- [ ] Test all endpoints

### Contract Views
- [ ] Add `@require_tenant` decorator to all views
- [ ] Add `@tenant_filter` decorator to all views
- [ ] Update all queries to filter by `tenant_id`
- [ ] Update all create operations to set `tenant_id`
- [ ] Update raw SQL queries
- [ ] Test all endpoints

### Vendor Views
- [ ] Add `@require_tenant` decorator to all views
- [ ] Add `@tenant_filter` decorator to all views
- [ ] Update all queries to filter by `tenant_id`
- [ ] Update all create operations to set `tenant_id`
- [ ] Update raw SQL queries
- [ ] Test all endpoints

### Risk Analysis Views
- [ ] Add `@require_tenant` decorator to all views
- [ ] Add `@tenant_filter` decorator to all views
- [ ] Update all queries to filter by `tenant_id`
- [ ] Update all create operations to set `tenant_id`
- [ ] Update raw SQL queries
- [ ] Test all endpoints

### Compliance Views
- [ ] Add `@require_tenant` decorator to all views
- [ ] Add `@tenant_filter` decorator to all views
- [ ] Update all queries to filter by `tenant_id`
- [ ] Update all create operations to set `tenant_id`
- [ ] Update raw SQL queries
- [ ] Test all endpoints

### Audit Views
- [ ] Add `@require_tenant` decorator to all views
- [ ] Add `@tenant_filter` decorator to all views
- [ ] Update all queries to filter by `tenant_id`
- [ ] Update all create operations to set `tenant_id`
- [ ] Update raw SQL queries
- [ ] Test all endpoints

### BCP/DRP Views
- [ ] Add `@require_tenant` decorator to all views
- [ ] Add `@tenant_filter` decorator to all views
- [ ] Update all queries to filter by `tenant_id`
- [ ] Update all create operations to set `tenant_id`
- [ ] Update raw SQL queries
- [ ] Test all endpoints

### SLA Views
- [ ] Add `@require_tenant` decorator to all views
- [ ] Add `@tenant_filter` decorator to all views
- [ ] Update all queries to filter by `tenant_id`
- [ ] Update all create operations to set `tenant_id`
- [ ] Update raw SQL queries
- [ ] Test all endpoints

### RBAC Views
- [ ] Add `@require_tenant` decorator to all views
- [ ] Add `@tenant_filter` decorator to all views
- [ ] Update all queries to filter by `tenant_id`
- [ ] Update all create operations to set `tenant_id`
- [ ] Update raw SQL queries
- [ ] Test all endpoints

---

## Phase 5: Frontend Updates ✅

- [ ] Verify JWT tokens are sent in all API requests
- [ ] Update error handling for 403 (tenant context not found)
- [ ] Test login flow with tenant context
- [ ] Test all API endpoints from frontend
- [ ] Verify tenant isolation in UI

---

## Phase 6: Testing ✅

### Unit Tests
- [ ] Create `test_tprm_multitenancy.py`
- [ ] Test tenant isolation for RFP
- [ ] Test tenant isolation for Contracts
- [ ] Test tenant isolation for Vendors
- [ ] Test tenant isolation for Risk Analysis
- [ ] Test tenant isolation for Compliance
- [ ] Test tenant isolation for Audits
- [ ] Test tenant isolation for BCP/DRP
- [ ] Test tenant isolation for SLAs
- [ ] Test tenant isolation for RBAC
- [ ] Test cross-tenant access prevention
- [ ] Test automatic tenant assignment

### Integration Tests
- [ ] Test API endpoints with multiple tenants
- [ ] Test tenant switching
- [ ] Test data isolation
- [ ] Test error handling

### Security Audit
- [ ] Verify all endpoints filter by tenant_id
- [ ] Test cross-tenant access attempts
- [ ] Verify tenant_id cannot be overridden
- [ ] Test SQL injection prevention
- [ ] Review access control

### Performance Testing
- [ ] Test query performance with tenant filtering
- [ ] Test with large datasets
- [ ] Verify indexes are being used
- [ ] Test concurrent requests

---

## Phase 7: Documentation ✅

- [ ] Update API documentation
- [ ] Update developer documentation
- [ ] Create migration guide
- [ ] Document tenant management procedures
- [ ] Create troubleshooting guide

---

## Phase 8: Deployment ✅

- [ ] Backup production database
- [ ] Run migrations in staging
- [ ] Test in staging environment
- [ ] Schedule maintenance window
- [ ] Run migrations in production
- [ ] Verify data integrity
- [ ] Monitor for errors
- [ ] Rollback plan ready

---

## Quick Code Patterns

### View Pattern
```python
@require_tenant
@tenant_filter
@api_view(['GET'])
def my_view(request):
    tenant_id = get_tenant_id_from_request(request)
    items = MyModel.objects.filter(tenant_id=tenant_id)
    return Response(items)
```

### Create Pattern
```python
@require_tenant
@tenant_filter
@api_view(['POST'])
def create_item(request):
    tenant_id = get_tenant_id_from_request(request)
    item = MyModel.objects.create(
        ...,
        tenant_id=tenant_id
    )
    return Response(item)
```

### Update Pattern
```python
@require_tenant
@tenant_filter
@api_view(['PUT'])
def update_item(request, item_id):
    tenant_id = get_tenant_id_from_request(request)
    item = MyModel.objects.get(
        id=item_id,
        tenant_id=tenant_id
    )
    # Update fields
    item.save()
    return Response(item)
```

### Raw SQL Pattern
```sql
SELECT * FROM table_name
WHERE TenantId = %s  -- Note: TenantId (capital T)
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Both tenants see same data | Add `.filter(tenant_id=tenant_id)` to query |
| 403 Tenant context not found | Check user has tenant_id set, verify JWT token |
| SQL error: unknown column | Use `TenantId` (capital T) in SQL, not `tenant_id` |
| New records have NULL tenant_id | Set `tenant_id` explicitly in create, or inherit from TenantAwareModel |
| Cross-tenant access | Always filter by tenant_id in get/update/delete operations |

---

**Last Updated**: January 2026

