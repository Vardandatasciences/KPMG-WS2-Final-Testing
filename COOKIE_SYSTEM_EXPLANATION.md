# Cookie System Explanation & Troubleshooting Guide

## How the Cookie System Works

### Overview
The cookie system is a GDPR-compliant cookie consent management system that allows users to control which types of cookies they accept on the website.

### Architecture Flow

```
User visits website
    ↓
CookieBanner component checks localStorage
    ↓
If preferences NOT saved → Show banner
    ↓
User clicks "Accept All", "Reject All", or "Customize"
    ↓
Frontend (CookieBanner.vue) calls cookieService.savePreferences()
    ↓
cookieService makes POST request to /api/cookie/preferences/save/
    ↓
Backend (cookie_views.py) receives request
    ↓
Backend saves to database (cookie_preferences table in grc2 database)
    ↓
Backend returns success response
    ↓
Frontend saves to localStorage and hides banner
```

### Components

#### 1. **Frontend Components**

**CookieBanner.vue** (`grc_frontend/src/components/Cookie/CookieBanner.vue`)
- Displays the cookie consent banner at the bottom of the page
- Shows when user first visits (if preferences not saved)
- Provides three options:
  - **Accept All**: Enables all cookie types
  - **Reject All**: Only essential cookies (default)
  - **Customize**: Opens modal to select individual cookie types

**CookiePolicy.vue** (`grc_frontend/src/components/Cookie/CookiePolicy.vue`)
- Full cookie policy page accessible at `/cookie-policy`
- Explains what each cookie type does
- Provides link to manage preferences

#### 2. **Frontend Service**

**cookieService.js** (`grc_frontend/src/services/cookieService.js`)
- Handles all API communication with backend
- Methods:
  - `savePreferences(preferences)` - Saves preferences to backend
  - `getPreferences(userId, sessionId)` - Retrieves saved preferences
  - `getSessionId()` - Gets or creates session ID from localStorage
  - `hasPreferencesSaved()` - Checks if preferences have been saved
  - `markPreferencesSaved()` - Marks preferences as saved in localStorage

#### 3. **Backend API**

**cookie_views.py** (`grc_backend/grc/routes/Cookie/cookie_views.py`)
- `save_cookie_preferences(request)` - POST endpoint to save preferences
- `get_cookie_preferences(request)` - GET endpoint to retrieve preferences

**URLs** (`grc_backend/grc/urls.py`)
- `POST /api/cookie/preferences/save/` - Save preferences
- `GET /api/cookie/preferences/` - Get preferences

#### 4. **Database Model**

**CookiePreferences** (`grc_backend/grc/models.py`)
- Table: `cookie_preferences` in `grc2` database
- Fields:
  - `PreferenceId` (Primary Key, Auto Increment)
  - `UserId` (Foreign Key to Users, nullable)
  - `SessionId` (VARCHAR 255, for anonymous users)
  - `EssentialCookies` (Boolean, always true)
  - `FunctionalCookies` (Boolean)
  - `AnalyticsCookies` (Boolean)
  - `MarketingCookies` (Boolean)
  - `PreferencesSaved` (Boolean)
  - `IpAddress` (VARCHAR 50)
  - `UserAgent` (TEXT)
  - `CreatedAt` (DateTime)
  - `UpdatedAt` (DateTime)

### Cookie Types

1. **Essential Cookies** (Always enabled, cannot be disabled)
   - Required for website functionality
   - Session management, authentication, security

2. **Functional Cookies** (Optional)
   - Enhanced functionality and personalization
   - Language preferences, UI customization

3. **Analytics Cookies** (Optional)
   - Website usage analytics
   - Performance monitoring, user behavior tracking

4. **Marketing Cookies** (Optional)
   - Advertising and marketing
   - Ad targeting, campaign tracking

### Data Storage

#### Database (Primary Storage)
- Stored in `cookie_preferences` table in `grc2` database
- Persists across sessions
- Can be linked to user account (if logged in) or session ID (if anonymous)

#### LocalStorage (Secondary Storage)
- `cookie_preferences_saved`: Boolean flag indicating if preferences were saved
- `cookie_session_id`: Unique session identifier for anonymous users
- `cookie_preferences`: JSON object with current preferences (for quick access)

### How to Debug "Not Saving to Database" Issue

#### Step 1: Check Browser Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for messages starting with `🍪 [CookieBanner]` or `❌`
4. Check for any error messages

#### Step 2: Check Network Tab
1. Open browser DevTools (F12)
2. Go to Network tab
3. Click "Accept All" or "Reject All" in cookie banner
4. Look for request to `/api/cookie/preferences/save/`
5. Check:
   - **Status Code**: Should be 200 (OK)
   - **Request Payload**: Should contain preferences data
   - **Response**: Should have `status: 'success'`

#### Step 3: Check Backend Logs
1. Check Django server console/terminal
2. Look for log messages starting with `[Cookie]`
3. Check for any error messages or exceptions

#### Step 4: Verify Database Connection
1. Check if Django can connect to `grc2` database
2. Verify database credentials in `backend/settings.py`
3. Test database connection:
   ```python
   python manage.py dbshell
   SELECT * FROM cookie_preferences;
   ```

#### Step 5: Check API Endpoint
1. Test the endpoint directly:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/cookie/preferences/save/ \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "test-123",
       "essential_cookies": true,
       "functional_cookies": false,
       "analytics_cookies": false,
       "marketing_cookies": false,
       "preferences_saved": true
     }'
   ```

#### Step 6: Check Model/Database Issues
1. Verify the table exists:
   ```sql
   SHOW TABLES LIKE 'cookie_preferences';
   ```
2. Check table structure:
   ```sql
   DESCRIBE cookie_preferences;
   ```
3. Verify Django can access the model:
   ```python
   python manage.py shell
   >>> from grc.models import CookiePreferences
   >>> CookiePreferences.objects.all()
   ```

### Common Issues & Solutions

#### Issue 1: Preferences not saving
**Symptoms**: Banner keeps appearing, no data in database

**Possible Causes**:
- API endpoint not accessible (CORS, routing issue)
- Database connection issue
- Model not using correct database
- Error in backend code (check logs)

**Solution**:
- Check backend logs for errors
- Verify API endpoint is registered in `urls.py`
- Test database connection
- Check browser console for API errors

#### Issue 2: Preferences saved but not persisting
**Symptoms**: Data appears in database but banner shows again on refresh

**Possible Causes**:
- `checkBannerVisibility()` not checking database correctly
- localStorage flag not being set
- Session ID mismatch

**Solution**:
- Check `checkBannerVisibility()` function
- Verify localStorage is being set
- Check session ID consistency

#### Issue 3: Database connection error
**Symptoms**: Backend logs show database errors

**Possible Causes**:
- Wrong database credentials
- Database server not running
- Network connectivity issues
- Database router misconfiguration

**Solution**:
- Verify database settings in `settings.py`
- Check database server status
- Verify network connectivity
- Check database router configuration

### Testing the Cookie System

#### Manual Test Steps:
1. Clear browser localStorage (or use incognito mode)
2. Visit the website
3. Cookie banner should appear
4. Click "Accept All"
5. Check browser console for success message
6. Check database: `SELECT * FROM cookie_preferences;`
7. Refresh page - banner should NOT appear
8. Check cookie policy page - should be accessible

#### Automated Test (if needed):
```javascript
// In browser console
localStorage.clear()
location.reload()
// Banner should appear
```

### API Request/Response Format

#### Save Preferences Request:
```json
POST /api/cookie/preferences/save/
{
  "user_id": 1,  // Optional, if user is logged in
  "session_id": "abc-123-def-456",  // Optional, auto-generated if not provided
  "essential_cookies": true,
  "functional_cookies": true,
  "analytics_cookies": false,
  "marketing_cookies": false,
  "preferences_saved": true
}
```

#### Save Preferences Response:
```json
{
  "status": "success",
  "message": "Cookie preferences saved successfully",
  "data": {
    "preference_id": 1,
    "user_id": 1,
    "session_id": "abc-123-def-456",
    "essential_cookies": true,
    "functional_cookies": true,
    "analytics_cookies": false,
    "marketing_cookies": false,
    "preferences_saved": true,
    "created_at": "2025-12-09T14:37:00Z",
    "updated_at": "2025-12-09T14:37:00Z"
  }
}
```

#### Get Preferences Request:
```
GET /api/cookie/preferences/?user_id=1
GET /api/cookie/preferences/?session_id=abc-123-def-456
```

#### Get Preferences Response:
```json
{
  "status": "success",
  "data": {
    "preference_id": 1,
    "user_id": 1,
    "session_id": "abc-123-def-456",
    "essential_cookies": true,
    "functional_cookies": true,
    "analytics_cookies": false,
    "marketing_cookies": false,
    "preferences_saved": true,
    "created_at": "2025-12-09T14:37:00Z",
    "updated_at": "2025-12-09T14:37:00Z"
  }
}
```

### Next Steps to Fix "Not Saving" Issue

1. **Check Backend Logs**: Look for `[Cookie]` log messages when you click "Accept All"
2. **Check Browser Console**: Look for `🍪 [CookieBanner]` messages
3. **Check Network Tab**: Verify the POST request is being made and what response you get
4. **Test Database**: Manually insert a record to verify database access works
5. **Check Database Router**: Ensure CookiePreferences model uses the default (grc2) database

If you see specific error messages, share them and I can help debug further!

