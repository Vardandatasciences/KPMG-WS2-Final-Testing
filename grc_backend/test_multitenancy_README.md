# Multi-Tenancy Test Suite

This directory contains comprehensive test scripts to verify that multitenancy is properly implemented across all modules.

## Test Files

### 1. `test_multitenancy.py`
**Database-level tests** that verify:
- Tenant isolation at the model/query level
- Cross-tenant access prevention
- Automatic tenant assignment
- Query filtering by tenant_id
- Decorator functionality

### 2. `test_multitenancy_api.py`
**API-level tests** that verify:
- Endpoint tenant isolation
- HTTP request handling with tenant context
- Create/Update/Delete operations with tenant isolation
- Query count verification

### 3. `run_multitenancy_tests.py`
**Test runner script** that:
- Runs all multitenancy tests
- Generates detailed reports
- Supports filtering by module
- Generates HTML reports

## Usage

### Run All Tests
```bash
# Using Django test runner
python manage.py test test_multitenancy
python manage.py test test_multitenancy_api

# Using custom test runner
python run_multitenancy_tests.py

# With verbose output
python run_multitenancy_tests.py --verbose

# Generate HTML report
python run_multitenancy_tests.py --report report.html
```

### Run Specific Module Tests
```bash
python run_multitenancy_tests.py --module Policy
python run_multitenancy_tests.py --module Incident
```

### Run Individual Test Files
```bash
python test_multitenancy.py
python test_multitenancy_api.py
```

## Test Coverage

The test suite covers:

### ✅ Core Functionality
- [x] Tenant isolation (each tenant sees only their data)
- [x] Cross-tenant access prevention
- [x] Automatic tenant assignment on create
- [x] Query filtering by tenant_id
- [x] Decorator functionality (@require_tenant, @tenant_filter)

### ✅ Module Coverage
- [x] Framework module
- [x] Policy module
- [x] Compliance module
- [x] Incident module
- [x] Risk module
- [x] Audit module
- [x] EventHandling module
- [x] User module

### ✅ Operation Types
- [x] List operations (GET /list)
- [x] Detail operations (GET /detail)
- [x] Create operations (POST /create)
- [x] Update operations (PUT/PATCH /update)
- [x] Delete operations (DELETE /delete)

## Test Scenarios

### 1. Tenant Isolation Tests
- Verify tenants can only see their own data
- Verify tenants cannot access other tenants' data
- Verify query counts are correct per tenant

### 2. Cross-Tenant Access Prevention
- Attempt to access other tenant's data by ID
- Verify 403/404 responses for unauthorized access
- Verify queries return empty results for cross-tenant access

### 3. Automatic Tenant Assignment
- Create records without explicit tenant assignment
- Verify tenant is automatically assigned from context
- Verify tenant assignment works correctly

### 4. Query Filtering
- Verify all queries include tenant_id filter
- Verify related object queries respect tenant isolation
- Verify aggregate queries are tenant-scoped

### 5. Decorator Tests
- Test @require_tenant blocks requests without tenant
- Test @tenant_filter adds tenant_id to request
- Test decorators work together correctly

## Expected Results

All tests should pass with:
- ✅ 100% success rate for tenant isolation
- ✅ 0 cross-tenant data leaks
- ✅ All queries properly filtered
- ✅ All decorators working correctly

## Troubleshooting

### Tests Failing?

1. **Check Database State**
   ```bash
   python manage.py migrate
   ```

2. **Verify Tenant Setup**
   - Ensure Tenant model has correct fields
   - Verify tenant_id is being set correctly

3. **Check Middleware**
   - Verify TenantContextMiddleware is active
   - Check tenant resolution logic

4. **Review Decorators**
   - Ensure @require_tenant and @tenant_filter are applied
   - Verify tenant_id extraction works

### Common Issues

**Issue**: Tests fail with "Tenant context not found"
- **Solution**: Ensure TenantContextMiddleware is in MIDDLEWARE settings

**Issue**: Tests show cross-tenant data
- **Solution**: Verify all queries include `tenant_id=tenant_id` filter

**Issue**: New records not getting tenant assigned
- **Solution**: Check TenantAwareModel.save() method is working

## Continuous Integration

Add to CI/CD pipeline:
```yaml
# .github/workflows/test.yml
- name: Run Multitenancy Tests
  run: |
    python run_multitenancy_tests.py --report test-report.html
```

## Reporting

The test suite generates:
- Console output with test results
- Optional HTML report with detailed failure information
- Summary statistics (pass rate, failure count, etc.)

## Maintenance

When adding new modules:
1. Add test cases to `test_multitenancy.py`
2. Add API tests to `test_multitenancy_api.py`
3. Update this README with new coverage

## Support

For issues or questions:
- Check test output for specific error messages
- Review tenant_utils.py for decorator implementation
- Verify models have tenant field properly configured

