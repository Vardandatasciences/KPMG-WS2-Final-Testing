# Quick Start: Multi-Tenancy Testing

## 🚀 Quick Run

### Option 1: Run All Tests (Recommended)
```bash
cd grc_backend
python run_multitenancy_tests.py
```

### Option 2: Run with Verbose Output
```bash
python run_multitenancy_tests.py --verbose
```

### Option 3: Generate HTML Report
```bash
python run_multitenancy_tests.py --report multitenancy_report.html
```

### Option 4: Using Django Test Runner
```bash
python manage.py test test_multitenancy
python manage.py test test_multitenancy_api
```

## 📋 What Gets Tested

The test suite automatically verifies:

1. **Tenant Isolation**
   - ✅ Each tenant can only see their own data
   - ✅ Tenants cannot access other tenants' data
   - ✅ Query results are properly filtered

2. **Data Operations**
   - ✅ Create operations assign correct tenant
   - ✅ Update operations respect tenant boundaries
   - ✅ Delete operations respect tenant boundaries
   - ✅ List operations return only tenant's data

3. **Security**
   - ✅ Cross-tenant access is blocked
   - ✅ Decorators enforce tenant requirements
   - ✅ Queries include tenant_id filter

4. **Modules Tested**
   - ✅ Framework
   - ✅ Policy
   - ✅ Compliance
   - ✅ Incident
   - ✅ Risk
   - ✅ Audit
   - ✅ EventHandling
   - ✅ Users

## 📊 Expected Output

```
================================================================================
MULTITENANCY TEST SUITE
================================================================================
Started at: 2025-01-XX XX:XX:XX
Verbosity: 1
================================================================================

[TEST] Testing Framework Tenant Isolation...
✅ Framework tenant isolation: PASSED

[TEST] Testing Policy Tenant Isolation...
✅ Policy tenant isolation: PASSED

...

================================================================================
TEST SUMMARY
================================================================================
Total tests: 15
Passed: 15
Failed: 0
Errors: 0
Success rate: 100.0%
================================================================================
```

## 🔧 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'grc'"
**Solution**: Make sure you're in the `grc_backend` directory and Django is properly set up.

### Issue: "Database connection error"
**Solution**: 
```bash
python manage.py migrate
```

### Issue: Tests fail with "Tenant context not found"
**Solution**: Verify that `TenantContextMiddleware` is in your `MIDDLEWARE` settings.

## 📝 Customization

### Test Specific Module
```bash
python run_multitenancy_tests.py --module Incident
```

### Add More Test Cases
Edit `test_multitenancy.py` and add new test methods following the pattern:
```python
def test_your_feature(self):
    """Test description"""
    print("\n[TEST] Testing Your Feature...")
    # Your test code here
    print("✅ Your feature: PASSED")
```

## 🎯 Integration with CI/CD

Add to your CI pipeline:
```yaml
- name: Test Multitenancy
  run: |
    cd grc_backend
    python run_multitenancy_tests.py --report test-report.html
```

## 📚 Full Documentation

See `test_multitenancy_README.md` for complete documentation.

