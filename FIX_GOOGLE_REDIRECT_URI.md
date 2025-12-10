# Fix Google OAuth Redirect URI Mismatch

## Current Issue

Your Google Cloud Console has:
```
http://localhost:8000/accounts/google/login/callback/
```

But your backend expects:
```
http://localhost:8000/api/google/oauth-callback/
```

## Solution: Update Google Cloud Console

### Step-by-Step Instructions:

1. **In Google Cloud Console** (the page you're currently viewing):
   - Find the "Authorized redirect URIs" section
   - You'll see: `http://localhost:8000/accounts/google/login/callback/`

2. **Click the "X" or delete button** next to the existing URI to remove it

3. **Click "+ Add URI"** button

4. **Enter the correct URI:**
   ```
   http://localhost:8000/api/google/oauth-callback/
   ```
   ⚠️ **Important**: 
   - Use `/api/google/oauth-callback/` (not `/accounts/google/login/callback/`)
   - Include the trailing slash `/`
   - Use `http://` (not `https://`) for localhost

5. **Click "SAVE"** at the bottom of the page

6. **Wait 1-2 minutes** for changes to propagate

7. **Try the Google login again**

## Alternative: Add Both URIs

If you want to keep the old URI for other purposes, you can:
- Keep: `http://localhost:8000/accounts/google/login/callback/`
- Add: `http://localhost:8000/api/google/oauth-callback/`

Both URIs can coexist in the list.

## For Production

When deploying to production, also add:
```
https://grc-backend.vardaands.com/api/google/oauth-callback/
```

## Verification

After updating, you should see in Google Cloud Console:
- ✅ `http://localhost:8000/api/google/oauth-callback/` in the "Authorized redirect URIs" list

Then try the Google login again - it should work!

