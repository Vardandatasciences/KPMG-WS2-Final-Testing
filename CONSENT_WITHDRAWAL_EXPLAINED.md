# Consent Withdrawal - Complete Guide

## What is Consent Withdrawal?

**Consent Withdrawal** is the ability for users to revoke (take back) consent they previously gave for specific actions in the GRC system. This is a fundamental privacy right required by GDPR (General Data Protection Regulation) Article 7(3).

### Simple Analogy
Think of it like this:
- **Giving Consent** = You sign a contract saying "Yes, I agree to this"
- **Withdrawing Consent** = You cancel that contract and say "No, I no longer agree"

## Why is it Important?

1. **Legal Requirement**: GDPR mandates that withdrawing consent must be as easy as giving it
2. **User Control**: Users should have full control over their data and consent
3. **Privacy Rights**: Users can change their mind at any time
4. **Compliance**: Organizations must respect withdrawal requests immediately

---

## How It Works in the System

### 1. **User Flow**

```
User Journey:
┌─────────────────────────────────────────────────────────┐
│ 1. User previously gave consent for "Create Policy"     │
│    ✅ Consent recorded in database                       │
├─────────────────────────────────────────────────────────┤
│ 2. User goes to: User Profile → "My Consents" tab      │
│    📋 Sees list of all active consents                  │
├─────────────────────────────────────────────────────────┤
│ 3. User clicks "Withdraw" on a specific consent         │
│    ⚠️ Confirmation modal appears                         │
├─────────────────────────────────────────────────────────┤
│ 4. User confirms withdrawal (optional reason)           │
│    ✅ Withdrawal recorded in database                   │
├─────────────────────────────────────────────────────────┤
│ 5. System immediately stops using that consent          │
│    🚫 User must provide new consent before action       │
└─────────────────────────────────────────────────────────┘
```

### 2. **Technical Flow**

#### When User Withdraws Consent:

```
Frontend (User clicks "Withdraw")
    ↓
API Call: POST /api/consent/withdraw/
    ↓
Backend creates ConsentWithdrawal record
    ↓
Database stores:
    - User ID
    - Action Type (e.g., "create_policy")
    - Timestamp
    - IP Address
    - User Agent
    - Optional Reason
    ↓
Response sent to frontend
    ↓
UI updates to show consent as withdrawn
```

#### When User Tries to Perform Action After Withdrawal:

```
User clicks "Create Policy"
    ↓
System checks: check_consent_required()
    ↓
Backend checks:
    1. Is consent required? (Yes)
    2. Does user have active consent?
       - Looks for last acceptance
       - Looks for withdrawals after that acceptance
       - If withdrawal exists → No active consent
    ↓
Result: No active consent found
    ↓
Consent modal appears again
    ↓
User must provide NEW consent to proceed
```

---

## What Happens When Consent is Withdrawn?

### Immediate Effects:

1. **Consent Status Changes**
   - The consent is marked as "withdrawn" in the database
   - System recognizes there is no longer active consent
   - User cannot perform the action without new consent

2. **Database Record Created**
   ```sql
   INSERT INTO consent_withdrawal (
       UserId, ActionType, FrameworkId, 
       WithdrawnAt, IpAddress, UserAgent, Reason
   ) VALUES (...)
   ```

3. **Audit Trail Maintained**
   - Original acceptance is NOT deleted (for compliance)
   - Withdrawal is recorded as a separate event
   - Complete history is preserved

### What Happens Next Time User Tries the Action:

**Before Withdrawal:**
```
User → "Create Policy" → ✅ Has active consent → Action proceeds
```

**After Withdrawal:**
```
User → "Create Policy" → ❌ No active consent → Consent modal appears
User → Provides new consent → ✅ New consent recorded → Action proceeds
```

---

## Database Structure

### Consent Acceptance Table
Stores when users **gave** consent:
```sql
consent_acceptance
├── AcceptanceId
├── UserId
├── ActionType (e.g., "create_policy")
├── AcceptedAt (timestamp)
└── ... other fields
```

### Consent Withdrawal Table
Stores when users **withdrew** consent:
```sql
consent_withdrawal
├── WithdrawalId
├── UserId
├── ActionType (e.g., "create_policy")
├── WithdrawnAt (timestamp)
├── Reason (optional)
└── ... other fields
```

### How System Determines Active Consent:

```python
# Pseudo-code logic
def has_active_consent(user_id, action_type):
    # Get last acceptance
    last_acceptance = get_last_acceptance(user_id, action_type)
    
    if not last_acceptance:
        return False  # Never gave consent
    
    # Get last withdrawal (if any)
    last_withdrawal = get_last_withdrawal(user_id, action_type)
    
    if not last_withdrawal:
        return True  # Gave consent, never withdrew
    
    # Check if withdrawal happened after acceptance
    if last_withdrawal.withdrawn_at > last_acceptance.accepted_at:
        return False  # Consent was withdrawn
    else:
        return True  # Acceptance happened after withdrawal (new consent)
```

---

## Example Scenarios

### Scenario 1: Simple Withdrawal

**Timeline:**
```
Jan 15, 2024 10:00 AM - User gives consent for "Create Policy"
Jan 20, 2024 02:00 PM - User withdraws consent for "Create Policy"
Jan 25, 2024 11:00 AM - User tries to create policy
```

**What Happens:**
- ✅ Jan 15: Consent recorded
- ✅ Jan 20: Withdrawal recorded
- ❌ Jan 25: System checks consent → Finds withdrawal → Shows consent modal again

### Scenario 2: Withdraw and Re-consent

**Timeline:**
```
Jan 15, 2024 - User gives consent
Jan 20, 2024 - User withdraws consent
Jan 25, 2024 - User gives NEW consent
Jan 30, 2024 - User tries to create policy
```

**What Happens:**
- ✅ Jan 15: First consent recorded
- ✅ Jan 20: Withdrawal recorded
- ✅ Jan 25: New consent recorded (this one is active)
- ✅ Jan 30: System checks → Finds new consent (after withdrawal) → Action proceeds

### Scenario 3: Withdraw All Consents

**User Action:**
- Clicks "Withdraw All Consents" button
- System creates withdrawal records for ALL active consents
- All actions now require new consent

**Result:**
- User must provide consent again for each action they want to perform
- Complete audit trail of all withdrawals is maintained

---

## API Endpoints

### 1. Withdraw Single Consent
```http
POST /api/consent/withdraw/
Content-Type: application/json

{
  "user_id": 123,
  "action_type": "create_policy",
  "framework_id": 1,
  "reason": "No longer needed"  // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Consent withdrawn successfully",
  "data": {
    "withdrawal_id": 456,
    "user_id": 123,
    "action_type": "create_policy",
    "withdrawn_at": "2024-01-20T14:00:00Z"
  }
}
```

### 2. Withdraw All Consents
```http
POST /api/consent/withdraw-all/
Content-Type: application/json

{
  "user_id": 123,
  "framework_id": 1,  // Optional - if not provided, withdraws from all frameworks
  "reason": "Privacy concerns"  // Optional
}
```

### 3. Check Consent Status
```http
GET /api/consent/status/123/?framework_id=1&action_type=create_policy
```

**Response:**
```json
{
  "status": "success",
  "action_type": "create_policy",
  "has_active_consent": false,
  "last_accepted": {
    "acceptance_id": 789,
    "accepted_at": "2024-01-15T10:00:00Z"
  },
  "last_withdrawn": {
    "withdrawal_id": 456,
    "withdrawn_at": "2024-01-20T14:00:00Z"
  }
}
```

---

## Frontend UI

### User Profile → "My Consents" Tab

**Active Consents Section:**
```
┌─────────────────────────────────────────────────────┐
│ ✅ Create Policy                                     │
│    Framework: ISO 27001                              │
│    Accepted: Jan 15, 2024 10:00 AM                   │
│    [Withdraw]                                        │
├─────────────────────────────────────────────────────┤
│ ✅ Upload in Audit                                   │
│    Framework: ISO 27001                              │
│    Accepted: Jan 10, 2024 02:30 PM                  │
│    [Withdraw]                                        │
└─────────────────────────────────────────────────────┘

[Withdraw All Consents]  ← Button at top
```

**Withdrawal History Section:**
```
┌─────────────────────────────────────────────────────┐
│ ❌ Create Policy (Withdrawn)                         │
│    Framework: ISO 27001                             │
│    Withdrawn: Jan 20, 2024 02:00 PM                 │
│    Reason: No longer needed                          │
└─────────────────────────────────────────────────────┘
```

---

## Key Points

### ✅ What Withdrawal Does:
- Records the withdrawal in database
- Immediately invalidates the consent
- Requires new consent for future actions
- Maintains complete audit trail
- Respects user's privacy rights

### ❌ What Withdrawal Does NOT Do:
- Does NOT delete the original acceptance record (for compliance)
- Does NOT automatically delete any data already processed
- Does NOT prevent user from giving new consent later
- Does NOT affect other users' consents

### 🔒 Privacy & Compliance:
- All withdrawals are logged with timestamp, IP, and user agent
- Complete history is maintained for audit purposes
- Users can see their withdrawal history
- System respects GDPR requirements

---

## Technical Implementation Details

### Backend Model
```python
class ConsentWithdrawal(models.Model):
    withdrawal_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)
    withdrawn_at = models.DateTimeField(auto_now_add=True)
    framework = models.ForeignKey('Framework', on_delete=models.CASCADE)
    reason = models.TextField(null=True, blank=True)
    # ... audit fields (IP, user agent, etc.)
```

### Consent Checking Logic
```python
def check_consent_required(action_type, user_id, framework_id):
    # 1. Check if consent is required for this action
    config = ConsentConfiguration.objects.get(...)
    if not config.is_enabled:
        return {"required": False}
    
    # 2. Check if user has active consent
    last_acceptance = ConsentAcceptance.objects.filter(
        user_id=user_id,
        action_type=action_type
    ).order_by('-accepted_at').first()
    
    if not last_acceptance:
        return {"required": True, "has_active_consent": False}
    
    # 3. Check if consent was withdrawn
    last_withdrawal = ConsentWithdrawal.objects.filter(
        user_id=user_id,
        action_type=action_type,
        withdrawn_at__gt=last_acceptance.accepted_at
    ).first()
    
    has_active_consent = last_withdrawal is None
    
    return {
        "required": True,
        "has_active_consent": has_active_consent
    }
```

---

## Summary

**Consent Withdrawal** is a privacy feature that allows users to revoke previously given consent. When withdrawn:

1. ✅ The withdrawal is recorded in the database
2. ✅ The consent is immediately invalidated
3. ✅ User must provide new consent to perform the action
4. ✅ Complete audit trail is maintained
5. ✅ System respects GDPR requirements

It's like canceling a permission you previously granted - you can always grant it again later, but the system will ask you again.

