# How Cookies Are Used in the GRC System

## Overview

The GRC (Governance, Risk & Compliance) system uses cookies and browser storage (localStorage/sessionStorage) for multiple critical functions including authentication, session management, user preferences, and GDPR compliance.

---

## 1. Authentication & Session Management

### JWT Token Storage (localStorage)

**Purpose**: Secure authentication and authorization

**What's Stored**:
- `access_token` - JWT access token for API authentication
- `refresh_token` - JWT refresh token for token renewal
- `access_token_expires` - Expiration timestamp for access token
- `refresh_token_expires` - Expiration timestamp for refresh token

**How It Works**:
1. **Login Process**:
   ```javascript
   // User logs in → Backend validates credentials
   // Backend returns JWT tokens → Frontend stores in localStorage
   localStorage.setItem('access_token', access_token)
   localStorage.setItem('refresh_token', refresh_token)
   ```

2. **Automatic Token Refresh**:
   - System checks token expiration every 5 minutes
   - If token expires in < 10 minutes, automatically refreshes
   - Uses refresh token to get new access token
   - Updates localStorage with new tokens

3. **Request Authentication**:
   - Every API request includes: `Authorization: Bearer {access_token}`
   - Axios interceptor automatically adds token to headers
   - If token expired (401 error), automatically refreshes and retries

**Location**: `grc_frontend/src/services/authService.js`

---

## 2. User Session Data (localStorage)

**Purpose**: Store user information for quick access without API calls

**What's Stored**:
- `user_id` - User's unique identifier
- `user` - Complete user object (JSON stringified)
- `user_email` - User's email address
- `user_name` - Username
- `user_full_name` - Full name (FirstName + LastName)
- `isAuthenticated` - Authentication status flag
- `is_logged_in` - Login status flag

**How It Works**:
```javascript
// After successful login
localStorage.setItem('user_id', user.UserId.toString())
localStorage.setItem('user', JSON.stringify(user))
localStorage.setItem('user_email', user.Email)
localStorage.setItem('user_name', user.UserName)
localStorage.setItem('is_logged_in', 'true')
```

**Usage Throughout System**:
- User identification in API requests
- Displaying user information in UI
- Access control checks
- Personalization features

**Location**: `grc_frontend/src/services/authService.js`, `grc_frontend/src/utils/accessUtils.js`

---

## 3. Django Session Cookies (Backend)

**Purpose**: Server-side session management for Django backend

**Configuration** (`grc_backend/backend/settings.py`):
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_NAME = 'grc_sessionid'
SESSION_COOKIE_AGE = 86400  # 1 day
SESSION_COOKIE_HTTPONLY = False  # Allow JavaScript access
SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'
```

**What's Stored in Session**:
- `user_id` - GRC user ID
- `username` - Username
- `grc_user_id` - Backup key for RBAC
- `grc_username` - GRC username
- `grc_framework_selected` - Selected framework ID
- `selected_framework_id` - Framework selection

**How It Works**:
1. User logs in → Django creates session
2. Session ID stored in cookie: `grc_sessionid`
3. Session data stored in database (`django_session` table)
4. Every request includes session cookie
5. Backend retrieves user info from session

**Location**: `grc_backend/grc/authentication.py`, `grc_backend/backend/settings.py`

---

## 4. Cookie Preferences Management (GDPR Compliance)

**Purpose**: GDPR-compliant cookie consent management

### Storage Locations:

#### A. Database Storage (Primary)
**Table**: `cookie_preferences` in `grc2` database

**Fields**:
- `PreferenceId` - Primary key
- `UserId` - User ID (nullable, linked after login)
- `SessionId` - Session identifier (for anonymous users)
- `EssentialCookies` - Always true (required)
- `FunctionalCookies` - User preference
- `AnalyticsCookies` - User preference
- `MarketingCookies` - User preference
- `PreferencesSaved` - Boolean flag
- `IpAddress` - User's IP address
- `UserAgent` - Browser user agent
- `CreatedAt` - Timestamp
- `UpdatedAt` - Timestamp

#### B. localStorage (Secondary/Cache)
**Stored Items**:
- `cookie_preferences_saved` - Boolean flag
- `cookie_session_id` - Unique session identifier
- `cookie_preferences` - JSON object with preferences

### How It Works:

1. **User Visits Website**:
   - Cookie banner appears if preferences not saved
   - User can: Accept All, Reject All, or Customize

2. **User Accepts/Rejects**:
   ```javascript
   // Preferences saved to both localStorage and database
   localStorage.setItem('cookie_preferences_saved', 'true')
   localStorage.setItem('cookie_preferences', JSON.stringify(preferences))
   // API call saves to database
   await cookieService.savePreferences(preferences)
   ```

3. **Linking to User Account**:
   - If user accepts cookies **before login**: Saved with `SessionId` only, `UserId = NULL`
   - After login: System automatically links preferences to user
   - Backend updates all session-based preferences with `UserId`

4. **Preference Retrieval**:
   - First checks localStorage (fast, no API call)
   - If not found, checks database by `user_id` or `session_id`
   - Updates localStorage with retrieved preferences

**Location**: 
- Frontend: `grc_frontend/src/components/Cookie/CookieBanner.vue`
- Backend: `grc_backend/grc/routes/Cookie/cookie_views.py`
- Service: `grc_frontend/src/services/cookieService.js`

---

## 5. Framework Selection (Session Storage)

**Purpose**: Remember user's selected framework across sessions

**What's Stored**:
- `selected_framework_id` - Currently selected framework
- `grc_framework_selected` - Framework selection state

**Storage Locations**:
1. **Backend Session** (Django):
   ```python
   request.session['selected_framework_id'] = framework_id
   request.session['grc_framework_selected'] = framework_id
   ```

2. **Frontend localStorage**:
   ```javascript
   localStorage.setItem('selected_framework_id', frameworkId)
   ```

**How It Works**:
- User selects framework → Stored in both backend session and localStorage
- On page load → System checks localStorage first, then backend session
- Persists across browser sessions (if "Remember Me" enabled)

**Location**: `grc_frontend/src/store/modules/framework.js`

---

## 6. Data Fetching Flags (localStorage)

**Purpose**: Optimize performance by tracking what data has been fetched

**What's Stored**:
- `all_data_fetched` - Flag indicating all initial data loaded
- `data_fetch_time` - Timestamp of last data fetch
- `data_fetch_duration` - How long data fetch took
- `incident_data_fetched` - Incident data loaded flag
- `risk_data_fetched` - Risk data loaded flag
- `integrations_data_fetched` - Integrations data loaded flag
- `tree_data_fetched` - Tree/policy data loaded flag

**How It Works**:
- After login, system prefetches critical data
- Sets flags in localStorage to prevent duplicate fetches
- Components check flags before making API calls
- Improves performance and reduces server load

**Location**: `grc_frontend/src/services/authService.js`

---

## 7. CSRF Protection (Cookies)

**Purpose**: Prevent Cross-Site Request Forgery attacks

**Configuration**:
```python
CSRF_COOKIE_SECURE = False  # True in production with HTTPS
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access
```

**How It Works**:
- Django automatically sets CSRF cookie on first request
- Cookie name: `csrftoken`
- Frontend includes CSRF token in request headers
- Backend validates token on POST/PUT/DELETE requests

**Location**: `grc_backend/backend/settings.py`

---

## 8. Remember Me Functionality

**Purpose**: Keep user logged in across browser sessions

**What's Stored**:
- `remember_me` - Boolean flag
- If enabled: Tokens persist longer, session doesn't expire on browser close

**How It Works**:
```javascript
if (rememberMe) {
  localStorage.setItem('remember_me', 'true')
  // Tokens stored with longer expiration
}
```

---

## Cookie Types in GRC System

### 1. Essential Cookies (Always Enabled)
- **Session cookies** (`grc_sessionid`) - Django session management
- **CSRF cookies** (`csrftoken`) - Security protection
- **Authentication tokens** (localStorage) - JWT tokens

### 2. Functional Cookies (Optional)
- **Framework selection** - Remember selected framework
- **UI preferences** - Theme, layout, language
- **User preferences** - Custom settings

### 3. Analytics Cookies (Optional)
- **Usage tracking** - Page views, navigation patterns
- **Performance monitoring** - Load times, errors
- **Feature usage** - Which features are used most

### 4. Marketing Cookies (Optional)
- **Campaign tracking** - Marketing campaign effectiveness
- **Ad targeting** - Relevant content (if applicable)

---

## Security Considerations

### 1. Token Security
- JWT tokens stored in localStorage (accessible to JavaScript)
- Tokens have expiration times
- Automatic refresh prevents token theft window
- Refresh tokens rotated on each refresh

### 2. Session Security
- Session cookies use `SameSite=Lax` to prevent CSRF
- Session data stored server-side (database)
- Sessions expire after 24 hours of inactivity

### 3. Cookie Preferences
- User consent tracked in database (audit trail)
- IP address and user agent logged
- Preferences linked to user account after login
- GDPR-compliant consent management

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    USER LOGS IN                         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Backend Validates Credentials & Generates JWT Tokens  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Frontend Stores in localStorage:                        │
│  - access_token                                         │
│  - refresh_token                                        │
│  - user_id                                              │
│  - user (object)                                        │
│  - is_logged_in = true                                  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Django Creates Session & Sets Cookie:                  │
│  - grc_sessionid (cookie)                              │
│  - Session data in database                             │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  User Accepts Cookie Preferences                       │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Preferences Saved:                                     │
│  - localStorage (cookie_preferences)                   │
│  - Database (cookie_preferences table)                 │
│  - Linked to user_id after login                        │
└─────────────────────────────────────────────────────────┘
```

---

## Key Files Reference

### Frontend:
- `grc_frontend/src/services/authService.js` - Authentication & token management
- `grc_frontend/src/components/Cookie/CookieBanner.vue` - Cookie consent UI
- `grc_frontend/src/services/cookieService.js` - Cookie preferences API
- `grc_frontend/src/utils/accessUtils.js` - Session utilities
- `grc_frontend/src/store/modules/framework.js` - Framework selection

### Backend:
- `grc_backend/grc/authentication.py` - Login & session creation
- `grc_backend/grc/routes/Cookie/cookie_views.py` - Cookie preferences API
- `grc_backend/grc/models.py` - CookiePreferences model
- `grc_backend/backend/settings.py` - Session & cookie configuration

---

## Summary

Cookies and browser storage in the GRC system serve multiple critical functions:

1. **Authentication**: JWT tokens for secure API access
2. **Session Management**: Django sessions for server-side state
3. **User Data**: Quick access to user information
4. **GDPR Compliance**: Cookie consent tracking and management
5. **Preferences**: Framework selection, UI preferences
6. **Performance**: Data fetching optimization flags
7. **Security**: CSRF protection, secure token handling

The system uses a combination of:
- **Cookies** (HTTP cookies) for Django sessions and CSRF tokens
- **localStorage** for JWT tokens, user data, and preferences
- **Database** for persistent storage of cookie preferences and sessions

All cookie usage is GDPR-compliant with user consent management and audit trails.

