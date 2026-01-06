# Quick Start: HTTP Multi-Tenancy Testing

## 🚀 Quick Start

1. **Start your Django server** (in a separate terminal):
   ```bash
   python manage.py runserver
   ```

2. **Run the test script**:
   ```bash
   python test_multitenancy_http.py
   ```

That's it! The script will:
- ✅ Automatically find users from different tenants
- ✅ Test all modules
- ✅ Verify cross-tenant isolation
- ✅ Show you a beautiful report

## 📋 Prerequisites

- Django server running on `http://localhost:8000`
- At least 2 users in database from different tenants
- CAPTCHA may need to be disabled (see below)

## 🔧 Disable CAPTCHA for Testing

If you get CAPTCHA errors, temporarily disable it in `grc/authentication.py`:

```python
# In jwt_login function, around line 685:
# Comment out or modify:
# if not verify_recaptcha(captcha_token):
#     return Response({
#         'status': 'error',
#         'message': 'CAPTCHA verification failed. Please try again.'
#     }, status=status.HTTP_400_BAD_REQUEST)

# Add this for testing:
if captcha_token and captcha_token != 'test-captcha-token-disabled':
    if not verify_recaptcha(captcha_token):
        return Response({
            'status': 'error',
            'message': 'CAPTCHA verification failed. Please try again.'
        }, status=status.HTTP_400_BAD_REQUEST)
```

## 📝 Example Usage

### Basic (auto-detect users)
```bash
python test_multitenancy_http.py
```

### Specify users
```bash
python test_multitenancy_http.py --tenant-a radha.sharma --tenant-b vikram.patel
```

### With passwords
```bash
python test_multitenancy_http.py \
  --tenant-a user1 \
  --tenant-b user2 \
  --password-a pass1 \
  --password-b pass2
```

## 📊 What Gets Tested

- ✅ Policy Module
- ✅ Compliance Module  
- ✅ Framework Module
- ✅ Risk Module
- ✅ Incident Module
- ✅ Audit Module
- ✅ Events Module

For each module:
1. Lists items for Tenant A
2. Lists items for Tenant B
3. Tests that Tenant B cannot access Tenant A's data

## 🎯 Expected Output

You should see:
- ✅ Green checkmarks for successful tests
- ⚠️ Yellow warnings for non-critical issues
- ❌ Red errors for failures

At the end, you'll get a summary:
```
✅ Passed: X
❌ Failed: Y
⚠️  Warnings: Z
```

## 🐛 Troubleshooting

**"Server is not running"**
- Start Django: `python manage.py runserver`

**"No users found"**
- Create test users in different tenants
- Or specify users: `--tenant-a user1 --tenant-b user2`

**"CAPTCHA verification failed"**
- Disable CAPTCHA (see above) or use real CAPTCHA tokens

**"Timeout"**
- Increase timeout: `--timeout 60`

## 📚 More Info

See `TEST_MULTITENANCY_HTTP_README.md` for detailed documentation.

