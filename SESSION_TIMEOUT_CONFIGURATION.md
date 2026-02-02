# Session Timeout Configuration Guide

This document explains how to configure session timeout settings using environment variables.

## Overview

Session timeout configuration has been moved from hardcoded values to environment variables, allowing you to:
- Enable/disable session timeout
- Configure the timeout duration
- Set warning time before expiration

## Backend Configuration

### Environment Variables

Add these variables to your `.env` file in the `grc_backend` directory:

```bash
# Enable/disable session timeout feature
# Set to 'true' to enable session timeout, 'false' to disable
# Default: true
SESSION_TIMEOUT_ENABLED=true

# Session timeout duration in seconds
# Examples:
#   1800 = 30 minutes
#   3600 = 1 hour (default)
#   7200 = 2 hours
#   10800 = 3 hours
#   14400 = 4 hours
#   28800 = 8 hours
#   86400 = 24 hours (1 day)
# Default: 3600 (1 hour)
SESSION_TIMEOUT_SECONDS=3600
```

### Files Modified

- `grc_backend/backend/settings.py`: Reads `SESSION_TIMEOUT_ENABLED` and `SESSION_TIMEOUT_SECONDS` from environment
- `grc_backend/grc/middleware.py`: Uses settings to enable/disable and configure session timeout middleware

## Frontend Configuration

### Environment Variables

Add these variables to your `.env` file in the `grc_frontend` directory (or set them in your build process):

```bash
# Enable/disable session timeout feature
# Set to 'true' to enable session timeout, 'false' to disable
# Default: true
VUE_APP_SESSION_TIMEOUT_ENABLED=true

# Session timeout duration in seconds
# Must match SESSION_TIMEOUT_SECONDS in backend .env file
# Examples:
#   1800 = 30 minutes
#   3600 = 1 hour (default)
#   7200 = 2 hours
#   10800 = 3 hours
#   14400 = 4 hours
#   28800 = 8 hours
#   86400 = 24 hours (1 day)
# Default: 3600 (1 hour)
VUE_APP_SESSION_TIMEOUT_SECONDS=3600

# Show warning this many seconds before session expiration
# Default: 5 seconds
VUE_APP_SESSION_WARNING_SECONDS=5
```

**Important:** Frontend environment variables in Vue.js must be prefixed with `VUE_APP_` to be accessible in the application.

### Files Modified

- `grc_frontend/src/config/api.js`: Exports session timeout configuration constants
- `grc_frontend/src/services/sessionTimeoutService.js`: Uses configuration from api.js

## Usage Examples

### Disable Session Timeout

**Backend `.env`:**
```bash
SESSION_TIMEOUT_ENABLED=false
```

**Frontend `.env`:**
```bash
VUE_APP_SESSION_TIMEOUT_ENABLED=false
```

### Set 2 Hour Timeout

**Backend `.env`:**
```bash
SESSION_TIMEOUT_ENABLED=true
SESSION_TIMEOUT_SECONDS=7200
```

**Frontend `.env`:**
```bash
VUE_APP_SESSION_TIMEOUT_ENABLED=true
VUE_APP_SESSION_TIMEOUT_SECONDS=7200
```

### Set 8 Hour Timeout with 10 Second Warning

**Backend `.env`:**
```bash
SESSION_TIMEOUT_ENABLED=true
SESSION_TIMEOUT_SECONDS=28800
```

**Frontend `.env`:**
```bash
VUE_APP_SESSION_TIMEOUT_ENABLED=true
VUE_APP_SESSION_TIMEOUT_SECONDS=28800
VUE_APP_SESSION_WARNING_SECONDS=10
```

## Important Notes

1. **Synchronization**: The `SESSION_TIMEOUT_SECONDS` value in the backend should match `VUE_APP_SESSION_TIMEOUT_SECONDS` in the frontend to ensure consistent behavior.

2. **Restart Required**: After changing environment variables:
   - Backend: Restart the Django server
   - Frontend: Rebuild the application (or restart dev server if using hot reload)

3. **Default Values**: If environment variables are not set, the system will use these defaults:
   - `SESSION_TIMEOUT_ENABLED`: `true` (enabled)
   - `SESSION_TIMEOUT_SECONDS`: `3600` (1 hour)
   - `SESSION_WARNING_SECONDS`: `5` (5 seconds)

4. **Security**: Longer session timeouts may pose security risks. Consider your security requirements when setting timeout values.

## Troubleshooting

### Session timeout not working

1. Check that environment variables are set correctly
2. Verify that `SESSION_TIMEOUT_ENABLED=true` in both backend and frontend
3. Ensure backend server has been restarted after changing `.env`
4. Check browser console for any errors related to session timeout service

### Frontend not reading environment variables

1. Ensure variables are prefixed with `VUE_APP_`
2. Rebuild the frontend application (environment variables are baked in at build time)
3. Check that variables are in the correct `.env` file location

### Mismatched timeout values

If backend and frontend have different timeout values, users may be logged out unexpectedly or see incorrect countdown timers. Always keep both values synchronized.
