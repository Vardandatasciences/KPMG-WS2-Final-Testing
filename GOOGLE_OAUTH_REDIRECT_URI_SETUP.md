# Google OAuth Redirect URI Configuration

## Backend Redirect URI

The backend uses the following redirect URI based on your environment:

### Development (Local)
```
http://localhost:8000/api/google/oauth-callback/
```

### Production
```
https://grc-backend.vardaands.com/api/google/oauth-callback/
```

## How to Configure in Google Cloud Console

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Select your project

2. **Navigate to Credentials**
   - Go to: **APIs & Services** → **Credentials**
   - Find your OAuth 2.0 Client ID
   - Click on it to edit

3. **Add Authorized Redirect URIs**
   - Scroll down to **"Authorized redirect URIs"**
   - Click **"+ ADD URI"**
   - Add these EXACT URIs (one at a time):
     - `http://localhost:8000/api/google/oauth-callback/`
     - `https://grc-backend.vardaands.com/api/google/oauth-callback/`
   - **IMPORTANT**: Include the trailing slash `/` at the end
   - Click **"SAVE"**

4. **Verify the Configuration**
   - Make sure both URIs are listed
   - Check for typos (especially trailing slashes)
   - Wait 1-2 minutes for changes to propagate

## Common Mistakes to Avoid

❌ **Wrong**: `http://localhost:8000/api/google/oauth-callback` (missing trailing slash)
❌ **Wrong**: `http://localhost:8000/api/google/oauth-callback/` (wrong port)
❌ **Wrong**: `https://localhost:8000/api/google/oauth-callback/` (https instead of http for localhost)
✅ **Correct**: `http://localhost:8000/api/google/oauth-callback/`

## Check Your Current Configuration

To verify what redirect URI your backend is using, you can:

1. **Check environment variable:**
   ```bash
   echo $GOOGLE_REDIRECT_URI
   ```

2. **Check Django settings (in Django shell):**
   ```python
   python manage.py shell
   >>> from django.conf import settings
   >>> print(settings.GOOGLE_REDIRECT_URI)
   ```

3. **Check the actual OAuth request:**
   - Open browser DevTools → Network tab
   - Click "Sign in with Google"
   - Look at the redirect URL in the request
   - The `redirect_uri` parameter should match what's in Google Cloud Console

## Testing After Configuration

1. **Wait 1-2 minutes** after saving in Google Cloud Console
2. **Clear browser cache** (or use incognito mode)
3. **Try the Google login again**
4. **Check the error** - if you still get `redirect_uri_mismatch`, double-check:
   - The URI in Google Cloud Console matches exactly
   - You're using the correct environment (dev vs production)
   - The trailing slash is present

## Troubleshooting

### Still getting redirect_uri_mismatch?

1. **Check the exact error URL:**
   - The error page URL contains the redirect_uri that was sent
   - Decode it and compare with Google Cloud Console

2. **Verify environment:**
   - Make sure `USE_LOCAL_DEVELOPMENT` is set correctly
   - Or set `GOOGLE_REDIRECT_URI` explicitly in your `.env` file

3. **Check for typos:**
   - Copy-paste the URI from this document
   - Don't manually type it

4. **Wait for propagation:**
   - Google changes can take 1-2 minutes to propagate
   - Try again after waiting

## Environment Variable Override

If you want to override the default redirect URI, set it in your `.env` file:

```bash
GOOGLE_REDIRECT_URI=http://localhost:8000/api/google/oauth-callback/
```

Or for production:
```bash
GOOGLE_REDIRECT_URI=https://grc-backend.vardaands.com/api/google/oauth-callback/
```

Make sure to add the same URI to Google Cloud Console!

