# Automated Multi-Tenancy HTTP Test Script

This script makes actual HTTP requests to test multitenancy across all modules. It verifies tenant isolation by testing with multiple tenants and checking cross-tenant access prevention.

## Features

- ✅ Tests all modules (Policy, Compliance, Framework, Risk, Incident, Audit, Events)
- ✅ Tests with multiple tenants simultaneously
- ✅ Verifies cross-tenant access prevention
- ✅ Makes real HTTP requests to your API
- ✅ Beautiful formatted output with color coding
- ✅ Automatic user discovery from database
- ✅ Configurable endpoints and timeouts

## Prerequisites

1. **Django server must be running**
   ```bash
   python manage.py runserver
   ```

2. **Test users must exist in database**
   - At least 2 users from different tenants
   - Users should have valid passwords

3. **CAPTCHA may need to be disabled for testing**
   - The script uses a test CAPTCHA token
   - You may need to temporarily disable CAPTCHA verification in `grc/authentication.py` for testing

## Usage

### Basic Usage (Auto-detect users)

```bash
cd grc_backend
python test_multitenancy_http.py
```

The script will automatically find users from different tenants in your database.

### Specify Users

```bash
python test_multitenancy_http.py --tenant-a user1 --tenant-b user2
```

### Specify Passwords

```bash
python test_multitenancy_http.py \
  --tenant-a user1 \
  --tenant-b user2 \
  --password-a password1 \
  --password-b password2
```

### Custom Base URL

```bash
python test_multitenancy_http.py --base-url http://localhost:8000
```

### Custom Timeout

```bash
python test_multitenancy_http.py --timeout 60
```

## Command Line Options

```
--base-url      Base URL of the API server (default: http://localhost:8000)
--tenant-a      Username for Tenant A
--tenant-b      Username for Tenant B
--password-a    Password for Tenant A
--password-b    Password for Tenant B
--timeout       Request timeout in seconds (default: 30)
```

## What It Tests

For each module, the script:

1. **Logs in as Tenant A** and lists items
2. **Logs in as Tenant B** and lists items
3. **Tests cross-tenant access prevention**:
   - Tenant B tries to access Tenant A's data
   - Should be blocked (403/404) or return empty/denied

## Modules Tested

- **Policy**: `/api/frameworks/`
- **Compliance**: `/api/compliance/frameworks/`
- **Framework**: `/api/frameworks/`
- **Risk**: `/api/risk-instances/`
- **Risk (ViewSet)**: `/api/risks/`
- **Incident**: `/api/incident-incidents/`
- **Incident (ViewSet)**: `/api/incidents/`
- **Audit**: `/api/audits/`
- **Events**: `/api/events/list/`

## Output

The script provides color-coded output:

- ✅ **Green**: Success
- ⚠️ **Yellow**: Warning (non-critical issues)
- ❌ **Red**: Error/Failure
- ℹ️ **Blue**: Information

## Example Output

```
======================================================================
🔐 MULTITENANCY TESTING SCRIPT
======================================================================

ℹ️  Checking server connection...
✅ Server is running

💡 TIP: If you get CAPTCHA errors, you can disable it for testing.

======================================================================
📊 TESTING MODULES
======================================================================

----------------------------------------------------------------------
📦 Testing Policy Module
----------------------------------------------------------------------
ℹ️  Tenant A - Logging in as radha.sharma...
✅ Logged in as radha.sharma (Tenant ID: 1)
ℹ️  Tenant A - Listing Policy items...
✅ Tenant A - Policy: Got 36 items

ℹ️  Tenant B - Logging in as vikram.patel...
✅ Logged in as vikram.patel (Tenant ID: 2)
ℹ️  Tenant B - Listing Policy items...
✅ Tenant B - Policy: Got 36 items

ℹ️  Testing cross-tenant access prevention (Tenant B accessing Tenant A's item ID: 1)...
✅ Policy: Cross-tenant access correctly blocked (403/404)
```

## Troubleshooting

### CAPTCHA Errors

If you get CAPTCHA verification errors, you can temporarily disable CAPTCHA in `grc/authentication.py`:

```python
# In jwt_login function, comment out or modify:
if not verify_recaptcha(captcha_token):
    # return Response({'status': 'error', ...}, ...)  # Comment this out
    pass  # Allow login for testing
```

### Timeout Errors

If requests timeout, increase the timeout:

```bash
python test_multitenancy_http.py --timeout 60
```

### No Users Found

Create test users in different tenants:

```python
from grc.models import Tenant, Users

tenant1 = Tenant.objects.create(name='Tenant A', subdomain='tenant-a')
tenant2 = Tenant.objects.create(name='Tenant B', subdomain='tenant-b')

user1 = Users.objects.create(
    UserName='user1',
    Password='password1',  # Or use make_password for hashed
    tenant=tenant1
)

user2 = Users.objects.create(
    UserName='user2',
    Password='password2',
    tenant=tenant2
)
```

### Endpoint Not Found

If endpoints return 404, check:
- Server is running
- URL patterns match in `grc/urls.py`
- Module endpoints are configured in the script

## Integration with CI/CD

You can integrate this script into your CI/CD pipeline:

```bash
#!/bin/bash
# Start server in background
python manage.py runserver &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Run tests
python test_multitenancy_http.py --tenant-a user1 --tenant-b user2

# Capture exit code
EXIT_CODE=$?

# Stop server
kill $SERVER_PID

exit $EXIT_CODE
```

## Notes

- The script uses JWT authentication by default
- Falls back to session-based authentication if JWT fails
- Automatically extracts tenant_id from user model
- Handles various response formats (list, dict with 'data', etc.)
- Tests both list and detail endpoints

## See Also

- `test_multitenancy.py` - Database-level multitenancy tests
- `test_multitenancy_api.py` - API-level multitenancy tests
- `run_multitenancy_tests.py` - Test runner for database tests

