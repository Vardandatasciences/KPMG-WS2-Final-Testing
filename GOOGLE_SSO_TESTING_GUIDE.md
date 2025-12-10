# Google SSO Testing Guide

This guide will help you test and verify that Google Single Sign-On (SSO) is working correctly.

## Prerequisites

1. **Google Cloud Console Setup**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to "APIs & Services" > "Credentials"
   - Create OAuth 2.0 Client ID credentials
   - Add authorized redirect URIs:
     - Development: `http://localhost:8000/api/google/oauth-callback/`
     - Production: `https://grc-backend.vardaands.com/api/google/oauth-callback/`

2. **Environment Variables**
   Make sure these are set in your `.env` file or environment:
   ```bash
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   FRONTEND_URL=http://localhost:8080  # or your production frontend URL
   ```

## Testing Steps

### 1. Check Backend Configuration

**Test the OAuth initiate endpoint:**
```bash
# Using curl
curl -X GET http://localhost:8000/api/google/oauth/ \
  -H "Content-Type: application/json"

# Expected response:
# {
#   "status": "success",
#   "authorization_url": "https://accounts.google.com/o/oauth2/auth?..."
# }
```

**Check settings are loaded:**
```python
# In Django shell (python manage.py shell)
from django.conf import settings
print(f"Google Client ID: {settings.GOOGLE_CLIENT_ID[:20]}...")
print(f"Google Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
print(f"Google Scopes: {settings.GOOGLE_SCOPES}")
```

### 2. Test Frontend Login Button

1. **Start your development servers:**
   ```bash
   # Backend (Terminal 1)
   cd grc_backend
   python manage.py runserver

   # Frontend (Terminal 2)
   cd grc_frontend
   npm run serve
   ```

2. **Navigate to login page:**
   - Open browser: `http://localhost:8080/login`
   - You should see:
     - Regular login form
     - A divider with "or"
     - "Sign in with Google" button with Google logo

3. **Click "Sign in with Google" button:**
   - Should redirect to Google OAuth consent screen
   - Select your Google account
   - Grant permissions

### 3. Verify OAuth Flow

**Check browser console (F12):**
- Look for: `🔐 [AuthService] Initiating Google OAuth SSO...`
- Should redirect to Google login page

**After Google authentication:**
- Should redirect back to: `http://localhost:8080/auth/google/callback?access_token=...`
- Check console for: `🔐 [AuthService] Handling Google OAuth callback...`
- Should see: `🔐 Google SSO Login successful!`

### 4. Check Backend Logs

**Look for these log messages:**
```
INFO: Google OAuth initiated - redirecting to: https://accounts.google.com/...
INFO: Google OAuth callback - email: user@example.com, google_id: 123456789
INFO: ✅ GOOGLE SSO LOGIN SUCCESS: User username (ID: 1) logged in successfully
```

**If errors occur, check for:**
```
ERROR: Google OAuth initiate error: ...
ERROR: Google OAuth callback error: ...
```

### 5. Verify User Creation/Login

**Check database:**
```sql
-- Check if user was created/updated
SELECT UserId, UserName, Email, FirstName, LastName, IsActive 
FROM users 
WHERE Email = 'your-google-email@example.com';
```

**Check localStorage (Browser DevTools > Application > Local Storage):**
- `access_token` - Should be present
- `refresh_token` - Should be present
- `user` - Should contain user object
- `isAuthenticated` - Should be "true"
- `is_logged_in` - Should be "true"

### 6. Test Complete Flow

1. **New User Flow:**
   - Use a Google account that doesn't exist in your system
   - Should create new user automatically
   - Should prompt for consent if needed
   - Should redirect to home page after consent

2. **Existing User Flow:**
   - Use a Google account that already exists
   - Should log in directly
   - Should skip user creation

3. **License Validation:**
   - User must have a valid license key
   - Check logs for license verification messages

### 7. Common Issues & Solutions

#### Issue: "Google OAuth is not configured"
**Solution:**
- Check environment variables are set
- Restart Django server after setting env vars
- Verify in Django shell: `settings.GOOGLE_CLIENT_ID`

#### Issue: "Redirect URI mismatch"
**Solution:**
- Verify redirect URI in Google Cloud Console matches exactly:
  - `http://localhost:8000/api/google/oauth-callback/` (development)
  - `https://grc-backend.vardaands.com/api/google/oauth-callback/` (production)
- Check for trailing slashes - they must match exactly

#### Issue: "Invalid state parameter"
**Solution:**
- This is CSRF protection working
- Make sure cookies/sessions are enabled
- Check browser allows cookies for your domain

#### Issue: "No framework configured"
**Solution:**
- Ensure at least one Framework exists in database
- Check: `SELECT * FROM frameworks LIMIT 1;`

#### Issue: "License verification failed"
**Solution:**
- User needs a valid license key assigned
- Check `users.license_key` field
- Verify licensing system is accessible

### 8. API Endpoint Testing

**Test OAuth Initiate:**
```bash
curl -X GET "http://localhost:8000/api/google/oauth/" \
  -H "Content-Type: application/json" \
  -c cookies.txt
```

**Expected Response:**
```json
{
  "status": "success",
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?client_id=..."
}
```

### 9. Frontend Component Check

**Verify Google button is visible:**
- Open browser DevTools
- Inspect the "Sign in with Google" button
- Should have class: `google-sso-button`
- Should have Google logo SVG icon

**Check callback component:**
- Navigate directly to: `http://localhost:8080/auth/google/callback`
- Should show loading state or error (if no tokens)

### 10. Network Tab Verification

**Open Browser DevTools > Network tab:**

1. **Click "Sign in with Google":**
   - Should see: `GET /api/google/oauth/` → 200 OK
   - Response should contain `authorization_url`

2. **After Google redirect:**
   - Should see: `GET /api/google/oauth-callback/?code=...&state=...` → 302 Redirect
   - Redirect should go to frontend callback URL

3. **Frontend callback:**
   - Should see: `GET /api/jwt/verify/` → 200 OK
   - Should authenticate successfully

## Quick Test Checklist

- [ ] Google Client ID and Secret are set in environment
- [ ] Redirect URI is configured in Google Cloud Console
- [ ] Backend server is running
- [ ] Frontend server is running
- [ ] "Sign in with Google" button appears on login page
- [ ] Clicking button redirects to Google login
- [ ] After Google login, redirects back to app
- [ ] User is logged in (check localStorage)
- [ ] User can access protected routes
- [ ] License validation works (if enabled)
- [ ] Consent flow works (if user hasn't accepted)

## Debug Commands

**Check Django settings:**
```python
python manage.py shell
>>> from django.conf import settings
>>> print(settings.GOOGLE_CLIENT_ID)
>>> print(settings.GOOGLE_REDIRECT_URI)
```

**Check session state:**
```python
# In Django shell during OAuth flow
>>> from django.contrib.sessions.models import Session
>>> session = Session.objects.get(session_key='your_session_key')
>>> print(session.get_decoded())
```

**Test OAuth flow manually:**
1. Visit: `http://localhost:8000/api/google/oauth/`
2. Copy the `authorization_url` from response
3. Open in browser and complete Google login
4. Check the callback URL parameters

## Production Checklist

Before deploying to production:

- [ ] Update `GOOGLE_REDIRECT_URI` to production URL
- [ ] Add production redirect URI in Google Cloud Console
- [ ] Set `FRONTEND_URL` to production frontend URL
- [ ] Enable HTTPS (required for OAuth)
- [ ] Test with production Google account
- [ ] Verify license validation works
- [ ] Check error handling and logging
- [ ] Test with multiple Google accounts
- [ ] Verify user creation works correctly
- [ ] Test consent flow

## Support

If you encounter issues:
1. Check Django logs: `python manage.py runserver` output
2. Check browser console for JavaScript errors
3. Check Network tab for failed requests
4. Verify all environment variables are set
5. Ensure Google Cloud Console configuration matches

