# Session Cookie Age vs Session Logout - Key Differences

## Overview

In the GRC system, there are **two separate but related concepts** that control when users are logged out:

1. **SESSION_COOKIE_AGE** - Django session cookie expiration time
2. **Session Logout** - The actual logout process that happens when authentication fails

---

## 1. SESSION_COOKIE_AGE (Django Session Cookie)

### What It Is:
- **Setting**: `SESSION_COOKIE_AGE = 7200` (2 hours in seconds)
- **Location**: `grc_backend/backend/settings.py`
- **Purpose**: Controls when the Django session cookie expires

### How It Works:

```
User Logs In
    ↓
Django creates session in database
    ↓
Session cookie (grc_sessionid) sent to browser
    ↓
Cookie expires after SESSION_COOKIE_AGE (2 hours)
```

### Important Points:

1. **With `SESSION_SAVE_EVERY_REQUEST = True`**:
   - Session is **extended** on every request
   - Cookie expiration is **reset** each time user makes a request
   - User stays logged in as long as they're **active**

2. **Inactivity Behavior**:
   - If user is **inactive** for 2 hours → Cookie expires
   - If user is **active** (making requests) → Cookie keeps extending
   - Cookie expiration = **2 hours of inactivity**, not 2 hours total

3. **What Happens When Cookie Expires**:
   - Browser stops sending the session cookie
   - Django can't find the session
   - **But user might still be logged in via JWT tokens!**

---

## 2. Session Logout (Actual Logout Process)

### What It Is:
- **Process**: The actual logout that happens when authentication fails
- **Triggers**: Multiple scenarios can cause logout
- **Purpose**: Securely end user's session and clear authentication

### How It Works:

```
Authentication Check Fails
    ↓
System detects user is not authenticated
    ↓
Logout process initiated
    ↓
- Clear JWT tokens from localStorage
- Clear session data from server
- Delete session cookie
- Redirect to login page
```

### Triggers for Logout:

1. **Manual Logout**:
   - User clicks "Logout" button
   - Explicit logout request sent to server
   - All authentication cleared immediately

2. **JWT Token Expiration**:
   - Access token expires (currently 1 hour)
   - Refresh token fails or expires (7 days)
   - Frontend can't refresh tokens
   - User is logged out

3. **Session Cookie Expiration** (if using session-based auth):
   - Session cookie expires after inactivity
   - Server can't find session
   - User is logged out

4. **Server-Side Session Deletion**:
   - Session deleted from database
   - Session invalidated on server
   - User is logged out

---

## Key Differences

| Aspect | SESSION_COOKIE_AGE | Session Logout |
|--------|-------------------|----------------|
| **What it controls** | Cookie expiration time | Actual logout process |
| **When it happens** | After inactivity period | When auth fails |
| **Can be extended** | Yes (with SESSION_SAVE_EVERY_REQUEST) | No (once logged out, must login again) |
| **User experience** | Cookie expires silently | User is redirected to login |
| **Affects** | Django session cookie only | All authentication (JWT + Session) |
| **Current setting** | 2 hours (7200 seconds) | Depends on JWT token expiration |

---

## How They Work Together in GRC System

### Current Configuration:

```python
# Django Session
SESSION_COOKIE_AGE = 7200  # 2 hours
SESSION_SAVE_EVERY_REQUEST = True  # Extends on every request

# JWT Tokens
JWT_ACCESS_TOKEN_LIFETIME = 1 hour
JWT_REFRESH_TOKEN_LIFETIME = 7 days
```

### Authentication Flow:

```
┌─────────────────────────────────────────────────────────┐
│                    USER LOGS IN                         │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────┐              ┌──────────────────┐
│ Django Session│              │   JWT Tokens     │
│ Cookie Created│              │   Generated      │
│ (2 hour age)  │              │   (1 hour exp)   │
└───────┬───────┘              └────────┬─────────┘
        │                               │
        │                               │
        ▼                               ▼
┌─────────────────────────────────────────────────────────┐
│              USER MAKES API REQUESTS                    │
└───────────────────────┬─────────────────────────────────┘
        │                               │
        │                               │
        ▼                               ▼
┌───────────────┐              ┌──────────────────┐
│ Session Cookie│              │   JWT Token      │
│ Extended      │              │   Auto-refreshed │
│ (reset timer) │              │   (before exp)   │
└───────┬───────┘              └────────┬─────────┘
        │                               │
        │                               │
        ▼                               ▼
┌─────────────────────────────────────────────────────────┐
│              USER INACTIVE FOR 2 HOURS                  │
└───────────────────────┬─────────────────────────────────┘
        │                               │
        │                               │
        ▼                               ▼
┌───────────────┐              ┌──────────────────┐
│ Session Cookie│              │   JWT Token      │
│ EXPIRES       │              │   Still Valid    │
│ (no requests) │              │   (if refreshed) │
└───────┬───────┘              └────────┬─────────┘
        │                               │
        │                               │
        ▼                               ▼
┌─────────────────────────────────────────────────────────┐
│         USER TRIES TO MAKE REQUEST                      │
└───────────────────────┬─────────────────────────────────┘
        │                               │
        │                               │
        ▼                               ▼
┌───────────────┐              ┌──────────────────┐
│ Session Auth  │              │   JWT Auth       │
│ Fails         │              │   Works          │
│ (no cookie)   │              │   (if valid)     │
└───────┬───────┘              └────────┬─────────┘
        │                               │
        │                               │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  If BOTH fail → LOGOUT        │
        │  If JWT works → STAY LOGGED IN│
        └───────────────────────────────┘
```

---

## Important Scenarios

### Scenario 1: Active User
- **User is actively using the system**
- **Session Cookie**: Extended on every request (never expires)
- **JWT Token**: Auto-refreshed before expiration
- **Result**: User stays logged in indefinitely

### Scenario 2: Inactive User (2 hours)
- **User is inactive for 2 hours**
- **Session Cookie**: Expires (no requests to extend it)
- **JWT Token**: May still be valid (if within 1 hour) or expired
- **Result**: 
  - If JWT token is valid → User can still make requests
  - If JWT token expired → User is logged out

### Scenario 3: JWT Token Expires First
- **User is active but JWT token expires (1 hour)**
- **Session Cookie**: Still valid (extended by requests)
- **JWT Token**: Expired
- **Result**: 
  - Frontend tries to refresh token
  - If refresh succeeds → User stays logged in
  - If refresh fails → User is logged out

### Scenario 4: Both Expire
- **User inactive for 2+ hours**
- **Session Cookie**: Expired
- **JWT Token**: Expired (and refresh token may be expired)
- **Result**: User is **definitely logged out**

---

## Why Two Systems?

### Django Session (Cookie):
- **Server-side state management**
- **Framework selection** stored in session
- **RBAC permissions** can use session
- **OAuth integrations** use session

### JWT Tokens:
- **Stateless authentication**
- **API requests** use JWT tokens
- **Mobile/SPA friendly**
- **Can work without cookies**

### Combined Approach:
- **Redundancy**: If one fails, other can still work
- **Flexibility**: Different parts of system can use different auth methods
- **Security**: Multiple layers of authentication

---

## Summary

| Question | Answer |
|----------|--------|
| **What is SESSION_COOKIE_AGE?** | Time (in seconds) before Django session cookie expires |
| **What is Session Logout?** | The actual process of ending user's authenticated session |
| **When does cookie expire?** | After 2 hours of **inactivity** (if SESSION_SAVE_EVERY_REQUEST = True) |
| **When does user get logged out?** | When **both** session cookie AND JWT tokens fail |
| **Can user stay logged in longer?** | Yes, if they're active (cookie extends) and JWT refreshes |
| **What happens after 2 hours inactive?** | Cookie expires, but user might still be logged in via JWT |

---

## Current Settings in Your System

```python
# Backend Settings (grc_backend/backend/settings.py)
SESSION_COOKIE_AGE = 7200  # 2 hours
SESSION_SAVE_EVERY_REQUEST = True  # Extends on every request

# JWT Settings (grc_backend/grc/authentication.py)
JWT_ACCESS_TOKEN_LIFETIME = 1 hour
JWT_REFRESH_TOKEN_LIFETIME = 7 days
```

**This means:**
- User will be logged out after **2 hours of inactivity** (session cookie expires)
- OR after **JWT refresh token expires** (7 days)
- OR if user manually logs out
- Active users can stay logged in indefinitely (cookie extends, JWT refreshes)

---

## Recommendations

1. **SESSION_COOKIE_AGE = 7200 (2 hours)** ✅
   - Good for security (forces logout after inactivity)
   - Extends with activity (good user experience)

2. **JWT_ACCESS_TOKEN_LIFETIME = 1 hour** ✅
   - Good security practice (short-lived tokens)
   - Auto-refreshes before expiration

3. **SESSION_SAVE_EVERY_REQUEST = True** ✅
   - Keeps active users logged in
   - Only inactive users get logged out

**Result**: Users are logged out after **2 hours of inactivity**, but active users stay logged in as long as they're using the system.

