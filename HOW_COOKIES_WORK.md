# How the Cookie System Works - Complete Guide

## Overview

The cookie system is a GDPR-compliant cookie consent management system that allows users to control which types of cookies they accept on the website. It stores preferences both in the browser (localStorage) and in the database for persistence.

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER VISITS WEBSITE                      │
└───────────────────────┬───────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  CookieBanner Component Checks localStorage                 │
│  - cookie_preferences_saved flag?                            │
│  - cookie_preferences data?                                 │
└───────────────────────┬───────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
   NOT SAVED                      ALREADY SAVED
        │                               │
        ▼                               ▼
┌───────────────┐              ┌──────────────────┐
│ Show Banner   │              │ Check Database   │
│ at Bottom     │              │ for Preferences  │
└───────┬───────┘              └────────┬─────────┘
        │                               │
        ▼                               ▼
┌───────────────────────────────────────────────┐
│  USER CLICKS:                                 │
│  - "Accept All" → All cookies enabled         │
│  - "Reject All" → Only essential enabled      │
│  - "Customize" → Opens modal for selection    │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: CookieBanner.vue                                 │
│  - Gets user_id from localStorage (if logged in)            │
│  - Gets session_id from localStorage (or generates new)     │
│  - Calls cookieService.savePreferences()                    │
└───────────────────────┬───────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: cookieService.js                                 │
│  - Makes POST request to /api/cookie/preferences/save/       │
│  - Sends: { user_id, session_id, cookie preferences }       │
└───────────────────────┬───────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend: cookie_views.py                                   │
│  - Receives request data                                    │
│  - Validates user_id (if provided)                          │
│  - Finds existing preference by user_id OR session_id       │
│  - Creates new OR updates existing                          │
│  - Saves to database (cookie_preferences table)             │
└───────────────────────┬───────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Database: cookie_preferences table (grc2 database)         │
│  - PreferenceId (Primary Key)                               │
│  - UserId (Foreign Key to Users, nullable)                 │
│  - SessionId (for anonymous users)                          │
│  - Cookie type preferences (Essential, Functional, etc.)   │
│  - PreferencesSaved flag                                    │
│  - IP Address, User Agent, Timestamps                      │
└───────────────────────┬───────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend Returns Success Response                           │
└───────────────────────┬───────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: CookieBanner.vue                                 │
│  - Saves to localStorage (for quick access)                 │
│  - Sets cookie_preferences_saved flag                       │
│  - Hides banner                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Components Breakdown

### 1. **Frontend Components**

#### **CookieBanner.vue** (`grc_frontend/src/components/Cookie/CookieBanner.vue`)
- **Purpose**: Displays the cookie consent banner
- **When it shows**: 
  - On first visit (if preferences not saved)
  - When user clicks "Manage Cookie Preferences" link
- **Features**:
  - Three action buttons: "Accept All", "Reject All", "Customize"
  - Customize modal with toggles for each cookie type
  - Essential cookies are always enabled (cannot be disabled)
  - Auto-hides after preferences are saved
  - Automatically links session-based preferences to user after login

#### **CookiePolicy.vue** (`grc_frontend/src/components/Cookie/CookiePolicy.vue`)
- **Purpose**: Full cookie policy page
- **Route**: `/cookie-policy`
- **Features**:
  - Detailed explanation of each cookie type
  - Link to manage preferences
  - Accessible without authentication

### 2. **Frontend Service**

#### **cookieService.js** (`grc_frontend/src/services/cookieService.js`)
- **Methods**:
  - `savePreferences(preferences)` - Saves preferences to backend
  - `getPreferences(userId, sessionId)` - Retrieves saved preferences
  - `getSessionId()` - Gets or creates session ID from localStorage
  - `hasPreferencesSaved()` - Checks if preferences have been saved
  - `markPreferencesSaved()` - Marks preferences as saved
  - `getLocalPreferences()` - Gets preferences from localStorage
  - `saveLocalPreferences(preferences)` - Saves preferences to localStorage

### 3. **Backend API**

#### **cookie_views.py** (`grc_backend/grc/routes/Cookie/cookie_views.py`)
- **Endpoints**:
  - `POST /api/cookie/preferences/save/` - Save or update preferences
  - `GET /api/cookie/preferences/` - Get preferences by user_id or session_id

#### **Logic Flow**:
1. Receives request with `user_id` (optional) and `session_id` (optional)
2. Validates `user_id` if provided (checks if user exists)
3. Finds existing preference:
   - First by `user_id` (if provided)
   - Then by `session_id` (if no user_id match found)
4. If existing found:
   - Updates all fields
   - **Links to user if user_id provided and preference had NULL user_id**
5. If not found:
   - Creates new preference with provided data

### 4. **Database Model**

#### **CookiePreferences Model** (`grc_backend/grc/models.py`)
- **Table**: `cookie_preferences` in `grc2` database
- **Fields**:
  - `PreferenceId` (Primary Key, Auto Increment)
  - `UserId` (Foreign Key to Users, **nullable** - for anonymous users)
  - `SessionId` (VARCHAR 255, for anonymous users)
  - `EssentialCookies` (Boolean, default: True)
  - `FunctionalCookies` (Boolean, default: False)
  - `AnalyticsCookies` (Boolean, default: False)
  - `MarketingCookies` (Boolean, default: False)
  - `PreferencesSaved` (Boolean, default: False)
  - `IpAddress` (VARCHAR 50)
  - `UserAgent` (TEXT)
  - `CreatedAt` (DateTime, auto-set)
  - `UpdatedAt` (DateTime, auto-updated)

---

## Cookie Types Explained

### 1. **Essential Cookies** (Always Enabled)
- **Purpose**: Required for website functionality
- **Examples**: 
  - Session management
  - Authentication tokens
  - Security features
- **Can be disabled?**: No (always enabled)
- **GDPR Status**: No consent required (necessary for service)

### 2. **Functional Cookies** (Optional)
- **Purpose**: Enhanced functionality and personalization
- **Examples**:
  - Language preferences
  - Region settings
  - UI customization
- **Can be disabled?**: Yes
- **GDPR Status**: Consent required

### 3. **Analytics Cookies** (Optional)
- **Purpose**: Website usage analytics
- **Examples**:
  - Page views
  - Time spent on pages
  - Navigation patterns
  - Error tracking
- **Can be disabled?**: Yes
- **GDPR Status**: Consent required

### 4. **Marketing Cookies** (Optional)
- **Purpose**: Advertising and marketing
- **Examples**:
  - Ad targeting
  - Campaign tracking
  - Conversion measurement
- **Can be disabled?**: Yes
- **GDPR Status**: Consent required

---

## Data Storage Strategy

### **Dual Storage Approach**

#### 1. **Database (Primary Storage)**
- **Location**: `cookie_preferences` table in `grc2` database
- **Purpose**: Persistent, server-side storage
- **Advantages**:
  - Persists across devices (if user logs in)
  - Can be linked to user account
  - Audit trail (IP, User Agent, timestamps)
  - GDPR compliance (proof of consent)

#### 2. **localStorage (Secondary Storage)**
- **Purpose**: Quick access, client-side cache
- **Stored Items**:
  - `cookie_preferences_saved`: Boolean flag
  - `cookie_session_id`: Unique session identifier
  - `cookie_preferences`: JSON object with preferences
- **Advantages**:
  - Fast access (no API call needed)
  - Works offline
  - Reduces server load

---

## User ID Linking Logic

### **Problem**: 
When a user accepts cookies **before logging in**, the preferences are saved with `session_id` only and `user_id = NULL`. After login, we need to link these preferences to the user.

### **Solution**:

#### **Backend Logic** (`cookie_views.py`):
1. When saving preferences with `user_id`:
   - First checks for existing preference by `user_id`
   - If not found, checks for existing preference by `session_id` with `user_id = NULL`
   - If found, **updates the existing preference to link it to the user**
   - This ensures session-based preferences are linked after login

#### **Frontend Logic** (`CookieBanner.vue`):
1. **On Component Mount**:
   - Checks if user is logged in
   - If logged in, calls `linkPreferencesToUser()`
   
2. **On Auth Change**:
   - Listens for `authChanged` event
   - When user logs in, automatically links preferences
   
3. **Periodic Check**:
   - Runs every 5 seconds for first 30 seconds after mount
   - Checks if user_id is available and links preferences

4. **linkPreferencesToUser() Function**:
   - Gets `user_id` from localStorage
   - Gets `session_id` from localStorage
   - Calls API to get preferences by `session_id`
   - If preferences exist with no `user_id`, saves them again with `user_id`
   - Backend automatically links them

---

## Why UserId Might Not Be Saved

### **Common Scenarios**:

1. **User accepts cookies before logging in**:
   - Preferences saved with `session_id` only
   - `user_id = NULL` in database
   - **Solution**: Automatic linking after login (should work automatically)

2. **User logs in but linking doesn't happen**:
   - `linkPreferencesToUser()` might not be running
   - `user_id` might not be in localStorage yet
   - **Solution**: Added delays and periodic checks

3. **localStorage.clear() on login**:
   - Login process clears all localStorage
   - Cookie preferences lost from localStorage
   - **Solution**: Preserve cookie preferences during login (FIXED)

4. **User accepts cookies while logged in**:
   - Should save with `user_id` immediately
   - **If not working**: Check if `user_id` is in localStorage

---

## Testing the System

### **Test Scenario 1: Accept Cookies Before Login**
1. Clear browser data (or use incognito)
2. Visit website (not logged in)
3. Accept cookies → Should save with `session_id`, `user_id = NULL`
4. Check database: `SELECT * FROM cookie_preferences WHERE SessionId = '...'`
5. Log in
6. Wait 2-3 seconds
7. Check database again: `user_id` should now be populated

### **Test Scenario 2: Accept Cookies After Login**
1. Log in first
2. Visit website
3. Accept cookies → Should save with both `user_id` and `session_id`
4. Check database: `user_id` should be set immediately

### **Test Scenario 3: Update Preferences**
1. Accept cookies (any scenario)
2. Click "Customize" or visit cookie policy page
3. Change preferences
4. Save → Should update existing record (not create new)

---

## Debugging Steps

### **If UserId is Not Being Saved**:

1. **Check Browser Console**:
   ```javascript
   // In browser console
   localStorage.getItem('user_id')  // Should return user ID if logged in
   localStorage.getItem('cookie_session_id')  // Should return session ID
   ```

2. **Check Network Tab**:
   - Find request to `/api/cookie/preferences/save/`
   - Check Request Payload:
     ```json
     {
       "user_id": 2,  // Should be present if logged in
       "session_id": "...",
       "essential_cookies": true,
       ...
     }
     ```
   - Check Response:
     ```json
     {
       "status": "success",
       "data": {
         "user_id": 2,  // Should match request
         ...
       }
     }
     ```

3. **Check Backend Logs**:
   - Look for `[Cookie]` messages
   - Check if "Found user: X - Username" appears
   - Check if "Linking preference" messages appear

4. **Check Database Directly**:
   ```sql
   -- Check latest preferences
   SELECT * FROM cookie_preferences 
   ORDER BY CreatedAt DESC 
   LIMIT 5;
   
   -- Check if user exists
   SELECT UserId, UserName FROM users WHERE UserId = 2;
   ```

5. **Manual Test**:
   ```javascript
   // In browser console (while logged in)
   const cookieService = await import('/src/services/cookieService.js').then(m => m.default)
   const userId = localStorage.getItem('user_id')
   const sessionId = cookieService.getSessionId()
   console.log('User ID:', userId)
   console.log('Session ID:', sessionId)
   
   // Try to link preferences
   const response = await cookieService.getPreferences(parseInt(userId), sessionId)
   console.log('Preferences:', response)
   ```

---

## Current Implementation Status

### ✅ **Working**:
- Cookie banner displays correctly
- Preferences save to database
- Session-based preferences work
- Cookie policy page accessible
- Preferences persist in localStorage

### ⚠️ **Needs Attention**:
- **UserId linking after login** - Should work but may need testing
- **Periodic linking check** - Added but may need tuning

### 🔧 **Recent Fixes**:
1. Added cookie endpoints to middleware skip list (fixed 401 error)
2. Enhanced backend logic to link session-based preferences to users
3. Added periodic check to link preferences after login
4. Preserved cookie preferences during login (localStorage.clear() fix)

---

## API Endpoints

### **Save Preferences**
```
POST /api/cookie/preferences/save/
Content-Type: application/json

Request Body:
{
  "user_id": 2,              // Optional, if user is logged in
  "session_id": "abc-123",   // Optional, auto-generated if not provided
  "essential_cookies": true,
  "functional_cookies": false,
  "analytics_cookies": false,
  "marketing_cookies": false,
  "preferences_saved": true
}

Response:
{
  "status": "success",
  "message": "Cookie preferences saved successfully",
  "data": {
    "preference_id": 1,
    "user_id": 2,            // Should match request
    "session_id": "abc-123",
    "essential_cookies": true,
    "functional_cookies": false,
    "analytics_cookies": false,
    "marketing_cookies": false,
    "preferences_saved": true,
    "created_at": "2025-12-09T15:00:00Z",
    "updated_at": "2025-12-09T15:00:00Z"
  }
}
```

### **Get Preferences**
```
GET /api/cookie/preferences/?user_id=2
GET /api/cookie/preferences/?session_id=abc-123

Response:
{
  "status": "success",
  "data": {
    "preference_id": 1,
    "user_id": 2,            // NULL if not linked to user
    "session_id": "abc-123",
    "essential_cookies": true,
    "functional_cookies": false,
    "analytics_cookies": false,
    "marketing_cookies": false,
    "preferences_saved": true,
    "created_at": "2025-12-09T15:00:00Z",
    "updated_at": "2025-12-09T15:00:00Z"
  }
}
```

---

## Next Steps to Fix UserId Issue

1. **Test the linking function manually**:
   - Log in
   - Open browser console
   - Check if `linkPreferencesToUser()` is being called
   - Check backend logs for linking messages

2. **Verify user_id is in localStorage**:
   - After login, check: `localStorage.getItem('user_id')`
   - Should return a number (e.g., "2")

3. **Check if preferences are being found**:
   - Backend should log: "Found session-based preference X to link to user Y"

4. **Manual database update** (temporary fix):
   ```sql
   -- Link existing preferences to a user (replace 2 with actual user ID)
   UPDATE cookie_preferences 
   SET UserId = 2, UpdatedAt = NOW()
   WHERE UserId IS NULL 
   AND SessionId = 'your-session-id-here';
   ```

The system should now properly link preferences to users after login. If it's still not working, check the browser console and backend logs for the detailed logging messages I added.

