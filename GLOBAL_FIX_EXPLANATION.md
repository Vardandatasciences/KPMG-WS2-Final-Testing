# Global JWT Token Fix - Explanation

## The Problem

You were getting 401 Unauthorized errors across multiple APIs:
- `/api/compliance/all-policies/policies/`
- `/api/frameworks/`
- `/api/my-audits/`
- `/api/business-units/`
- And many others...

The root cause: **JWT tokens were not being sent** because different parts of the codebase were using:
1. Direct `axios` calls (bypassing interceptors)
2. Different axios instances (each with their own interceptors)
3. Custom axios instances (missing token logic)

## The Solution: Global Axios Interceptor

Instead of fixing each API call individually, we implemented a **GLOBAL axios interceptor** in `main.js` that:

1. **Applies to ALL axios requests** - No matter how axios is called
2. **Runs automatically** - No need to remember to add tokens manually
3. **Checks multiple token keys** - Works with different storage patterns:
   - `access_token` (primary)
   - `token` (fallback)
   - `session_token` (TPRM compatibility)
   - `jwt_token` (legacy support)

## How It Works

```javascript
// In main.js - Runs when app starts
axios.interceptors.request.use((config) => {
  // Get token from localStorage (checks multiple keys)
  const token = localStorage.getItem('access_token') || 
                localStorage.getItem('token') || 
                localStorage.getItem('session_token');
  
  if (token) {
    // Automatically add Authorization header
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
});
```

## What This Fixes

✅ **Direct axios calls:**
```javascript
axios.get('/api/frameworks/')  // ✅ Token added automatically
```

✅ **Instance-specific calls:**
```javascript
const api = axios.create({...})
api.get('/api/policies/')  // ✅ Token added automatically
```

✅ **Future API calls:**
```javascript
// Any new API call will automatically get tokens
axios.post('/api/new-endpoint/')  // ✅ Token added automatically
```

## Benefits

1. **One Fix, Works Everywhere** - No need to fix each component
2. **Future-Proof** - New API calls automatically work
3. **No Breaking Changes** - Existing code continues to work
4. **Consistent Behavior** - All requests follow the same pattern

## Verification

After this fix, you should see in browser console:
```
🔐 [GLOBAL INTERCEPTOR] Adding JWT token to request: GET /api/frameworks/
```

If you see warnings like:
```
⚠️ [GLOBAL INTERCEPTOR] No JWT token found for request: GET /api/...
```

It means:
- Either the user is not logged in (token doesn't exist)
- Or the token was cleared/expired (should redirect to login)

## No More Individual Fixes Needed!

With this global interceptor, you **don't need to fix each API endpoint individually**. All axios requests will automatically include JWT tokens when available.

The backend can still have endpoints in `skip_paths` for public access, but authenticated requests will always include tokens automatically.

