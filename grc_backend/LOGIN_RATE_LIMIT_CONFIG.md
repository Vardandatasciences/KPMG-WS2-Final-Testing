# Login Rate Limiting Configuration

## Overview
The login rate limiting has been made configurable to support performance testing while maintaining security in production.

**Current Status**: Rate limit is set to **200 attempts per minute** for all IPs (for KPMG performance testing).  
**⚠️ IMPORTANT**: Revert to 10 after testing is complete (see settings.py line 622).

## Configuration Options

### Environment Variables

Add these to your `.env` file:

#### Option 1: Increase Limit for All IPs (Simple)
```env
# Increase login attempts limit for all IPs (useful during performance testing)
LOGIN_RATE_LIMIT_PER_IP=200
```

#### Option 2: Whitelist Test IPs with Multiplier (Recommended for Production Testing)
```env
# Specify test IPs (comma-separated)
LOGIN_RATE_LIMIT_TEST_IPS=192.168.1.100,10.0.0.50,203.0.113.42

# Apply multiplier to test IPs (e.g., 20 = 200 attempts/min for test IPs)
# Other IPs will still use the default limit of 10 attempts/min
LOGIN_RATE_LIMIT_TEST_MULTIPLIER=20
```

#### Option 3: Customize Time Window
```env
# Change the time window (default: 60 seconds = 1 minute)
LOGIN_RATE_LIMIT_WINDOW_SECONDS=120  # 2 minutes
```

### Current Configuration (KPMG Testing)
- `LOGIN_RATE_LIMIT_PER_IP`: **200** (temporarily increased from 10 for performance testing)
- `LOGIN_RATE_LIMIT_WINDOW_SECONDS`: 60 (1 minute)
- `LOGIN_RATE_LIMIT_TEST_IPS`: (empty - no test IPs)
- `LOGIN_RATE_LIMIT_TEST_MULTIPLIER`: 1 (no multiplier)

### Production Default Values (to revert after testing)
- `LOGIN_RATE_LIMIT_PER_IP`: 10 (attempts per window)
- `LOGIN_RATE_LIMIT_WINDOW_SECONDS`: 60 (1 minute)
- `LOGIN_RATE_LIMIT_TEST_IPS`: (empty - no test IPs)
- `LOGIN_RATE_LIMIT_TEST_MULTIPLIER`: 1 (no multiplier)

## How It Works

1. **Default Behavior**: All IPs are limited to 10 login attempts per minute
2. **Test IP Whitelist**: If an IP is in `LOGIN_RATE_LIMIT_TEST_IPS`, it gets the limit multiplied by `LOGIN_RATE_LIMIT_TEST_MULTIPLIER`
3. **Global Override**: If you set `LOGIN_RATE_LIMIT_PER_IP` to a higher value, ALL IPs get that limit

## Example Scenarios

### Scenario 1: KPMG Performance Testing
```env
# KPMG test IPs get 200 attempts/min, others stay at 10/min
LOGIN_RATE_LIMIT_TEST_IPS=203.0.113.42,203.0.113.43
LOGIN_RATE_LIMIT_TEST_MULTIPLIER=20
```

### Scenario 2: Temporary Testing Period
```env
# All IPs get 200 attempts/min during testing
LOGIN_RATE_LIMIT_PER_IP=200
```

### Scenario 3: Production (Default)
```env
# No configuration needed - uses secure defaults
# All IPs: 10 attempts/min
```

## Files Modified

1. `grc_backend/backend/settings.py` - Added configuration variables
2. `grc_backend/grc/views.py` - Updated `login_user()` function
3. `grc_backend/grc/authentication.py` - Updated `jwt_login()` function

## Important Notes

⚠️ **Security Warning**: 
- Always revert test configurations after performance testing
- Test IP whitelist is safer than global limit increase
- Monitor logs for any abuse patterns

✅ **Best Practices**:
- Use test IP whitelist approach for production environments
- Document which IPs are whitelisted and why
- Set a reminder to remove test configurations after testing
- Consider using different values for different environments (dev/staging/prod)

## Testing

After configuration:
1. Restart Django server
2. Test with a whitelisted IP - should allow higher limit
3. Test with a non-whitelisted IP - should use default limit
4. Check logs for debug messages about test IP detection

## Reverting Changes After KPMG Testing

**To revert to production defaults (10 attempts/min):**

1. Open `grc_backend/backend/settings.py`
2. Find line 622: `LOGIN_RATE_LIMIT_PER_IP = int(os.environ.get('LOGIN_RATE_LIMIT_PER_IP', '200'))`
3. Change it to: `LOGIN_RATE_LIMIT_PER_IP = int(os.environ.get('LOGIN_RATE_LIMIT_PER_IP', '10'))`
4. Remove or update the TODO comment
5. Restart the server

**OR** if using environment variable override:
- Remove or comment out `LOGIN_RATE_LIMIT_PER_IP=200` from `.env` file
- Restart the server
