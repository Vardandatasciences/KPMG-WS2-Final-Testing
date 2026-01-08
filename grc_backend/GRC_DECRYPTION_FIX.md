# GRC Decryption Fix - Complete Implementation

## Problem
Encrypted data (like `gAAAAABpXq_xQT3Z...`) was showing in the UI instead of decrypted plain text for:
- Risk Register List (risk titles showing encrypted strings)
- Sidebar username (showing encrypted strings)

## Root Cause
1. **GRC serializers** were using `serializers.ModelSerializer` instead of auto-decrypting serializers
2. **Raw SQL queries** in `RiskViewSet.list()` and `get_all_risks_for_dropdown()` were bypassing serializers and returning encrypted data directly
3. **User profile endpoints** were not decrypting all encrypted fields

## Solution Implemented

### 1. Created Auto-Decrypting Serializer for GRC
**File:** `grc_backend/grc/utils/base_serializer.py`
- Created `AutoDecryptingModelSerializer` that automatically decrypts encrypted fields
- Uses `_plain` properties from `EncryptedFieldsMixin`
- Falls back to manual decryption if `_plain` properties don't exist

### 2. Updated Critical Serializers
**File:** `grc_backend/grc/serializers.py`
- ✅ `RiskSerializer` → Now uses `AutoDecryptingModelSerializer`
- ✅ `UserSerializer` → Now uses `AutoDecryptingModelSerializer`
- ✅ `RiskInstanceSerializer` → Now uses `AutoDecryptingModelSerializer`

### 3. Fixed Raw SQL Queries
**File:** `grc_backend/grc/routes/Risk/risk_views.py`

#### Fixed `RiskViewSet.list()` method:
- Added decryption logic for encrypted fields from raw SQL results
- Decrypts: `RiskTitle`, `RiskDescription`, `PossibleDamage`, `BusinessImpact`, `RiskMitigation`, `CreatedBy`, `CreatedByName`

#### Fixed `get_all_risks_for_dropdown()` function:
- This is the **main endpoint** used by the frontend (`/api/risks-for-dropdown/`)
- Added decryption logic for all encrypted fields
- Decrypts risk data before returning to frontend

### 4. Fixed User Profile Endpoints
**File:** `grc_backend/grc/routes/Global/user_profile.py`

#### Fixed `get_user_profile()`:
- Now decrypts all encrypted user fields: `UserName`, `FirstName`, `LastName`, `Email`, `PhoneNumber`, `Address`
- Uses `_plain` properties with fallback to manual decryption

#### Fixed `get_current_user()`:
- Decrypts username from RBAC and Users models
- Ensures username is decrypted before sending to frontend

**File:** `grc_backend/grc/routes/EventHandling/event_views.py`

#### Fixed `get_current_user()`:
- Decrypts all user fields before returning

## Testing

### To Verify the Fix:

1. **Restart Django Server** (CRITICAL!)
   ```bash
   # Stop the server (Ctrl+C)
   # Then restart:
   cd grc_backend
   python manage.py runserver
   ```

2. **Test Risk Register List:**
   - Navigate to Risk Register List in the UI
   - Verify risk titles show plain text (not `gAAAAAB...`)
   - Check browser console for any errors

3. **Test Sidebar Username:**
   - Check sidebar username display
   - Verify it shows plain text (not encrypted string)
   - Clear browser cache/localStorage if needed

4. **Test API Endpoints Directly:**
   ```bash
   # Test risks-for-dropdown endpoint
   curl http://localhost:8000/api/risks-for-dropdown/
   
   # Test current user endpoint
   curl http://localhost:8000/api/current-user/
   ```

## Files Modified

1. ✅ `grc_backend/grc/utils/base_serializer.py` (NEW FILE)
2. ✅ `grc_backend/grc/serializers.py`
3. ✅ `grc_backend/grc/routes/Risk/risk_views.py`
4. ✅ `grc_backend/grc/routes/Global/user_profile.py`
5. ✅ `grc_backend/grc/routes/EventHandling/event_views.py`

## Important Notes

- **Server restart is required** for changes to take effect
- The decryption uses `_plain` properties from `EncryptedFieldsMixin`
- If decryption fails, the original (possibly encrypted) value is returned (fail-safe)
- All encrypted fields are configured in `grc_backend/grc/utils/encryption_config.py`

## Troubleshooting

If decryption still doesn't work:

1. **Check if server was restarted** - Changes won't take effect until restart
2. **Check browser cache** - Clear cache and localStorage
3. **Check encryption config** - Verify fields are listed in `encryption_config.py`
4. **Check logs** - Look for decryption warnings in Django logs
5. **Verify encryption key** - Ensure `GRC_ENCRYPTION_KEY` is set correctly

## Next Steps

If issues persist:
1. Check Django logs for decryption errors
2. Verify the encryption key is correct
3. Test decryption manually using the encryption service
4. Check if data is actually encrypted in the database


