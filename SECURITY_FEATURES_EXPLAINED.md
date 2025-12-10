# Security Features Explained - Simple Guide

This document explains what each security feature means in plain language.

---

## 1. Cookie Banner 🍪

**What it is:**
A popup or banner that appears when you first visit a website asking for permission to use cookies.

**Why it's needed:**
- Cookies are small files websites store on your computer
- Some cookies are essential (like remembering you're logged in)
- Others are for tracking/analytics (like Google Analytics)
- Laws (GDPR, ePrivacy) require websites to ask permission before using non-essential cookies

**What it does:**
- Shows a banner when you first visit: "We use cookies. Accept/Reject/Customize"
- Lets you choose which types of cookies to allow
- Remembers your choice so it doesn't ask every time
- Links to a cookie policy explaining what each cookie does

**Example:**
```
┌─────────────────────────────────────┐
│ 🍪 We use cookies on this site       │
│                                     │
│ [Accept All] [Reject] [Customize]  │
│                                     │
│ Learn more in our Cookie Policy →  │
└─────────────────────────────────────┘
```

**Current Status:** ❌ Not implemented - Only documentation exists

---

## 2. Consent - Obtain ✅

**What it is:**
The process of asking users for permission before doing certain actions (like creating a policy or uploading a file).

**Why it's needed:**
- GDPR and other privacy laws require explicit consent for data processing
- Users must understand what they're agreeing to
- Organizations need proof that consent was given

**What it does:**
- Before you create a policy, upload a document, etc., a popup appears
- Shows what action you're about to do
- Asks: "Do you consent to this action?"
- Records your "Yes" with timestamp, IP address, and what you agreed to
- Stores this record for compliance/audit purposes

**Example Flow:**
1. User clicks "Create New Policy"
2. System shows: "You are about to create a policy. This will be recorded for compliance. Do you consent?"
3. User clicks "I Consent"
4. System records: User ID, timestamp, IP address, action type
5. Policy creation proceeds

**Current Status:** ✅ Fully implemented in GRC system

**Where it's used:**
- Creating policies, audits, incidents, risks
- Uploading files in various modules
- Any action that processes personal data

---

## 3. Consent - Record 📝

**What it is:**
The database system that stores a permanent record of every time a user gave consent.

**Why it's needed:**
- Legal requirement: Must be able to prove consent was given
- Audit trail: Shows who consented, when, and to what
- Compliance: Regulators can check these records during audits

**What it does:**
- Every time someone gives consent, it creates a database record
- Stores: Who (user ID), What (action type), When (timestamp), Where (IP address), How (user agent/browser)
- Creates an audit trail that can't be easily deleted
- Allows admins to see all consent history

**Example Record:**
```
User: John Doe (ID: 123)
Action: Create Policy
Consented: 2024-01-15 10:30:45
IP Address: 192.168.1.100
Browser: Chrome 120.0
Framework: ISO 27001
```

**Current Status:** ✅ Fully implemented - All consent acceptances are recorded

**Key Point:** This is the "paper trail" that proves consent was obtained legally.

---

## 4. Consent - Withdraw ❌

**What it is:**
The ability for users to take back (revoke) consent they previously gave.

**Why it's needed:**
- GDPR Article 7(3): Users have the right to withdraw consent at any time
- Must be as easy to withdraw as it was to give consent
- When withdrawn, data processing must stop immediately

**What it should do:**
- User goes to Settings → Privacy → My Consents
- Sees list of all consents they've given
- Clicks "Withdraw" on any consent
- System immediately stops processing data based on that consent
- Records the withdrawal with timestamp
- Sends confirmation email

**Example:**
```
My Consents:
┌─────────────────────────────────────────────┐
│ ✅ Create Policy Consent                    │
│    Given: Jan 15, 2024                      │
│    [Withdraw Consent]                       │
├─────────────────────────────────────────────┤
│ ✅ Upload Audit Files Consent               │
│    Given: Jan 10, 2024                      │
│    [Withdraw Consent]                       │
└─────────────────────────────────────────────┘
```

**Current Status:** ❌ Not implemented - Users cannot withdraw consent

**Problem:** This is a legal requirement (GDPR) but is missing from the system.

---

## 5. Special Permissions (Apps) 📱

**What it is:**
Permissions that mobile apps or web apps request to access device features (camera, microphone, location, contacts, etc.).

**Why it's needed:**
- Mobile apps often need access to device features
- Users should control what apps can access
- Privacy laws require apps to explain why they need permissions

**What it does:**
- App asks: "This app wants to access your camera. Allow/Deny?"
- Explains why: "To scan documents and upload them"
- User can grant or deny
- User can change permissions later in settings
- App should work even if permission is denied (with reduced functionality)

**Examples:**
- **Camera:** "Allow app to take photos for document scanning?"
- **Location:** "Allow app to access your location for vendor mapping?"
- **Microphone:** "Allow app to record audio for incident reports?"
- **Contacts:** "Allow app to access contacts for user lookup?"

**Current Status:** ❌ Not implemented - No device permission handling

**Note:** This is different from application-level permissions (RBAC). This is about device-level permissions for mobile/web apps.

---

## 6. Session Logout 🚪

**What it is:**
The process of securely ending a user's login session.

**Why it's needed:**
- Security: Prevents unauthorized access if someone else uses your computer
- Prevents session hijacking
- Compliance: Many standards require proper session management

**What it does:**
- User clicks "Logout" button
- System invalidates the session on the server
- Deletes authentication tokens
- Clears session data from server
- Clears cookies/tokens from browser
- Redirects user to login page
- Logs the logout event for security monitoring

**Types of Logout:**
1. **Manual Logout:** User clicks logout button
2. **Automatic Timeout:** Session expires after inactivity (e.g., 30 minutes)
3. **Force Logout:** Admin can force logout of a user

**Current Status:** ✅ Fully implemented - Multiple logout mechanisms exist

**Features:**
- Server-side session invalidation
- Token revocation
- Automatic session timeout
- Logout event logging

---

## 7. Incorrect Login Attempts 🔒

**What it is:**
Security system that tracks failed login attempts and locks accounts after too many wrong passwords.

**Why it's needed:**
- Prevents brute force attacks (hackers trying thousands of password combinations)
- Protects user accounts from unauthorized access
- Security best practice

**What it does:**
- Tracks every failed login attempt
- Counts how many times someone tries wrong password
- After 5 failed attempts: Locks account for 15 minutes
- Also limits attempts per IP address (10 per minute)
- Clears counter on successful login
- Shows user: "3/5 attempts remaining" or "Account locked for 12 minutes"

**Example Flow:**
1. Hacker tries password "123456" → ❌ Failed (1/5)
2. Tries "password" → ❌ Failed (2/5)
3. Tries "admin123" → ❌ Failed (3/5)
4. Tries "qwerty" → ❌ Failed (4/5)
5. Tries "letmein" → ❌ Failed (5/5)
6. **Account locked for 15 minutes** 🔒
7. Even correct password won't work until lockout expires

**Current Status:** ✅ Fully implemented - Rate limiting and account lockout active

**Protection Levels:**
- **Per User:** 5 failed attempts = 15 min lockout
- **Per IP:** 10 attempts per minute = temporary block

---

## 8. Secure Logon 🔐

**What it is:**
Advanced authentication methods beyond just username/password to make login more secure.

**Why it's needed:**
- Passwords can be stolen, guessed, or phished
- Multi-factor authentication (MFA) adds extra security layer
- Industry best practice for sensitive systems

**What it includes:**
1. **Strong Passwords:** Requirements like minimum length, complexity
2. **Multi-Factor Authentication (MFA):** 
   - Something you know (password)
   - Something you have (phone with code)
   - Something you are (fingerprint)
3. **Secure Protocols:** HTTPS, encrypted connections
4. **Password Policies:** Regular password changes, complexity rules

**MFA Example:**
1. User enters username and password ✅
2. System sends code to user's email/phone
3. User enters the code ✅
4. Login successful

**Current Status:** ⚠️ Partially implemented
- MFA code exists in TPRM backend but is **disabled**
- No MFA in GRC main system
- Only password-based authentication is active

**What's Missing:**
- MFA not enforced (currently disabled)
- No strong password policy enforcement
- No 2FA requirement for sensitive accounts

---

## Quick Reference Table

| Feature | What It Does | Real-World Example |
|---------|-------------|-------------------|
| **Cookie Banner** | Asks permission to use cookies | "Accept cookies?" popup on websites |
| **Consent - Obtain** | Asks permission before actions | "Do you consent to create this policy?" |
| **Consent - Record** | Saves proof of consent | Database record: "User X consented on Jan 15" |
| **Consent - Withdraw** | Lets users revoke consent | "Remove my consent" button in settings |
| **Special Permissions** | App asks for camera/location access | "Allow app to access camera?" on phone |
| **Session Logout** | Safely ends login session | "Logout" button that clears your session |
| **Incorrect Login Attempts** | Locks account after wrong passwords | "Account locked after 5 failed attempts" |
| **Secure Logon** | Extra security for login (MFA) | "Enter code sent to your phone" after password |

---

## Why These Matter

**Legal Compliance:**
- GDPR, CCPA, ePrivacy Directive require many of these features
- Missing features = potential legal violations and fines

**Security:**
- Protects user data and prevents unauthorized access
- Industry best practices for enterprise systems

**User Trust:**
- Users expect control over their data and privacy
- Transparent consent and easy withdrawal builds trust

**Audit Requirements:**
- Regulators need to see proof of compliance
- Consent records provide audit trail

---

## Priority for Implementation

**High Priority (Legal Requirements):**
1. ✅ Consent - Obtain (Done)
2. ✅ Consent - Record (Done)
3. ❌ Consent - Withdraw (Missing - GDPR requirement)
4. ❌ Cookie Banner (Missing - ePrivacy/GDPR requirement)

**Medium Priority (Security Best Practice):**
5. ⚠️ Secure Logon - Enable MFA (Partially done, needs activation)
6. ✅ Incorrect Login Attempts (Done)
7. ✅ Session Logout (Done)

**Low Priority (If Needed):**
8. ❌ Special Permissions (Only if mobile apps are planned)

