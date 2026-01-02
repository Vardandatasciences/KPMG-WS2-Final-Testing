# Certification Action Checklist

Quick reference checklist for certification readiness.

## 🔴 CRITICAL - Do Before Certification

### Security Configuration
- [ ] Remove all hardcoded secrets from `backend/settings.py`
- [ ] Set `DEBUG = False` (use environment variable)
- [ ] Set `SESSION_COOKIE_SECURE = True`
- [ ] Set `CSRF_COOKIE_SECURE = True`
- [ ] Set `SECURE_SSL_REDIRECT = True`
- [ ] Set `SECURE_HSTS_SECONDS = 31536000`
- [ ] Set `CORS_ALLOW_ALL_ORIGINS = False`
- [ ] Configure `CORS_ALLOWED_ORIGINS` properly

### Authentication & Authorization
- [ ] Enable RBAC: `RBAC_CONFIG['ENABLE_RBAC'] = True`
- [ ] Disable RBAC bypass: `RBAC_DECORATOR_BYPASS = False`
- [ ] Change `DEFAULT_PERMISSION_CLASSES` to `IsAuthenticated`
- [ ] Remove `SECRET_KEY` default value
- [ ] Require all OAuth secrets via environment variables

### Code Cleanup
- [ ] Remove all `print()` statements (found 1913+ instances)
- [ ] Replace print statements with proper logging
- [ ] Remove or secure debug endpoints
- [ ] Clean up TODO/FIXME comments
- [ ] Remove commented-out code

### Testing
- [ ] Create unit tests for authentication
- [ ] Create unit tests for authorization/RBAC
- [ ] Create integration tests for all API endpoints
- [ ] Add tests for error handling
- [ ] Achieve 80%+ code coverage
- [ ] Run security tests (SQL injection, XSS, CSRF)

### Database
- [ ] Enable migrations for TPRM modules
- [ ] Create migration history
- [ ] Document migration process
- [ ] Set up automated backups
- [ ] Test backup restoration

### Documentation
- [ ] Complete Swagger/OpenAPI documentation
- [ ] Document all API endpoints
- [ ] Create deployment guide
- [ ] Create configuration guide
- [ ] Create security hardening guide

## 🟡 HIGH PRIORITY - Should Fix

### Error Handling
- [ ] Create centralized error handler
- [ ] Standardize error response format
- [ ] Remove sensitive data from error messages
- [ ] Add proper exception logging

### Input Validation
- [ ] Add validation to all API endpoints
- [ ] Use DRF serializers for all inputs
- [ ] Validate file uploads (type, size, content)
- [ ] Sanitize all user inputs

### Rate Limiting
- [ ] Add rate limiting to authentication endpoints
- [ ] Add rate limiting to API endpoints
- [ ] Add rate limiting to file upload endpoints
- [ ] Configure rate limit headers

### Monitoring & Logging
- [ ] Set up centralized logging
- [ ] Add application monitoring
- [ ] Add security event monitoring
- [ ] Configure alerts for critical errors

## 🟢 MEDIUM PRIORITY - Nice to Have

### Code Quality
- [ ] Add type hints to critical functions
- [ ] Refactor duplicate code
- [ ] Improve code organization
- [ ] Add code comments for complex logic

### Performance
- [ ] Optimize database queries
- [ ] Add database indexing
- [ ] Implement caching where appropriate
- [ ] Add performance monitoring

---

## Quick Fixes - Files to Update Immediately

### 1. `backend/settings.py`
```python
# Line 60
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")  # Remove default
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY required")

# Line 63
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Line 394
CORS_ALLOW_ALL_ORIGINS = False

# Line 257-258
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG

# Line 471-474
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0

# Line 265-271
RBAC_CONFIG = {
    'ENABLE_RBAC': True,  # Enable
    ...
}
RBAC_DECORATOR_BYPASS = False  # Disable bypass

# Line 502
'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.IsAuthenticated',
],
```

### 2. Environment Variables (.env)
Create `.env` file with:
```bash
DJANGO_SECRET_KEY=<generate-strong-key>
DEBUG=False
DB_NAME=grc2
DB_USER=<username>
DB_PASSWORD=<password>
DB_HOST=<host>
# ... all other secrets
```

### 3. Remove Hardcoded Secrets
Search and remove defaults from:
- `AZURE_AD_CLIENT_SECRET`
- `JIRA_CLIENT_SECRET`
- `GOOGLE_CLIENT_SECRET`
- `BAMBOOHR_CLIENT_SECRET`
- Any other secrets with defaults

---

## Testing Checklist

### Unit Tests
- [ ] Authentication tests
- [ ] Authorization/RBAC tests
- [ ] Input validation tests
- [ ] Business logic tests
- [ ] Security function tests

### Integration Tests
- [ ] API endpoint tests
- [ ] Database operation tests
- [ ] File upload tests
- [ ] Integration workflow tests

### Security Tests
- [ ] SQL injection tests
- [ ] XSS tests
- [ ] CSRF tests
- [ ] Authentication bypass tests
- [ ] Authorization bypass tests

---

## Before Deployment

- [ ] All critical items completed
- [ ] All high priority items completed
- [ ] Test suite passing (80%+ coverage)
- [ ] Security testing completed
- [ ] Code review completed
- [ ] Documentation reviewed
- [ ] Production environment configured
- [ ] Monitoring configured
- [ ] Backups configured and tested
- [ ] Disaster recovery plan documented

---

**Priority Legend:**
- 🔴 Critical - Must fix before certification
- 🟡 High - Should fix before certification
- 🟢 Medium - Nice to have, can be done later






