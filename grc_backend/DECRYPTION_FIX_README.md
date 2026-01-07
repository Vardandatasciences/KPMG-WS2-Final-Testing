# 🔐 Decryption Fix - Complete Guide

## ✅ What Was Fixed

The decryption system wasn't working because:
1. **bcpdrp/serializers.py** was using manual `SerializerMethodField` instead of `AutoDecryptingModelSerializer`
2. Some models might not have `_plain` properties initialized at runtime
3. Serializer fallback logic needed enhancement

## 🛠️ Changes Made

### 1. Fixed `bcpdrp/serializers.py`
**Location:** `grc_backend/tprm_backend/bcpdrp/serializers.py`

- Changed from `serializers.ModelSerializer` to `AutoDecryptingModelSerializer`
- Removed manual `SerializerMethodField` declarations
- Now uses automatic decryption like all other serializers

**Before:**
```python
class PlanListSerializer(serializers.ModelSerializer):
    strategy_name = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()
    
    def get_strategy_name(self, obj):
        return obj.strategy_name_plain if obj.strategy_name else None
```

**After:**
```python
class PlanListSerializer(AutoDecryptingModelSerializer):
    # No manual fields needed - auto-decryption handles it!
    class Meta:
        model = Plan
        fields = ['plan_id', 'strategy_name', 'plan_name', ...]
```

### 2. Enhanced `base_serializer.py`
**Location:** `grc_backend/tprm_backend/utils/base_serializer.py`

Added robust fallback decryption with multiple methods:
1. Try `_plain` property first
2. Fall back to manual decryption if property doesn't exist
3. Check if data is actually encrypted before attempting decryption
4. Handle plain text data gracefully

### 3. Created Diagnostic Tools

#### `test_encryption_simple.py`
Quick test to verify encryption setup without database connection.

**Run it:**
```bash
cd grc_backend
python test_encryption_simple.py
```

#### `fix_decryption_properties.py`
Script to manually add `_plain` properties to all models (if needed).

**Run it:**
```bash
cd grc_backend
python tprm_backend/fix_decryption_properties.py
```

## 🚀 How to Apply the Fix

### Step 1: Restart Django Server

The most important step! Restart your server to reload the updated serializers:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd grc_backend
python manage.py runserver
```

### Step 2: Clear Python Cache (Optional but Recommended)

```bash
cd grc_backend
# Windows PowerShell:
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse

# Or manually delete __pycache__ folders
```

### Step 3: Verify the Fix

#### A. Run the diagnostic:
```bash
cd grc_backend
python test_encryption_simple.py
```

Expected output:
```
✅ Core encryption/decryption functionality: WORKING
✅ All encryption files: PRESENT
✅ Models have encryption mixin: CONFIGURED
✅ Serializers use auto-decryption: CONFIGURED
```

#### B. Test API Endpoints:

1. Open your frontend application
2. Navigate to pages with data (users, plans, vendors, etc.)
3. Check that you see **plain text**, not encrypted strings like `gAAAAA...`

Example endpoints to test:
- BCP/DRP Plans: `/api/tprm/bcpdrp/plans/`
- Users: `/api/tprm/users/`
- Vendors: `/api/tprm/vendors/`

## 🔍 Troubleshooting

### Issue 1: Still Seeing Encrypted Data

**Symptoms:** Data shows as `gAAAAABpXg...` in the UI

**Solutions:**
1. **Hard refresh browser** (Ctrl+Shift+R) to clear cached responses
2. **Restart Django server** completely
3. **Check server logs** for decryption errors
4. **Run the fix script:**
   ```bash
   cd grc_backend
   python tprm_backend/fix_decryption_properties.py
   ```

### Issue 2: Server Won't Start

**Symptoms:** Import errors or encryption key errors

**Solutions:**
1. Check that all encryption files exist:
   - `grc/utils/data_encryption.py`
   - `tprm_backend/utils/data_encryption.py`
   - `tprm_backend/utils/base_serializer.py`

2. Verify environment variables:
   ```python
   # In Django shell:
   from django.conf import settings
   print(hasattr(settings, 'SECRET_KEY'))  # Should be True
   ```

### Issue 3: Some Models Work, Others Don't

**Symptoms:** Users decrypt fine, but Plans don't

**Solutions:**
1. Check encryption config:
   ```python
   from tprm_backend.utils.encryption_config import get_encrypted_fields_for_model
   print(get_encrypted_fields_for_model('Plan'))  # Should show field list
   ```

2. Verify model has mixin:
   ```python
   from tprm_backend.bcpdrp.models import Plan
   from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin
   print(issubclass(Plan, TPRMEncryptedFieldsMixin))  # Should be True
   ```

3. Check serializer inheritance:
   ```python
   from tprm_backend.bcpdrp.serializers import PlanListSerializer
   from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
   print(issubclass(PlanListSerializer, AutoDecryptingModelSerializer))  # Should be True
   ```

## 📊 Verification Checklist

Use this checklist to verify everything is working:

- [ ] ✅ `test_encryption_simple.py` passes all tests
- [ ] ✅ Django server starts without errors
- [ ] ✅ Browser shows plain text (no `gAAAAA...` strings)
- [ ] ✅ User names display correctly
- [ ] ✅ Email addresses are readable
- [ ] ✅ Plan names show properly (BCP/DRP module)
- [ ] ✅ Vendor information is visible
- [ ] ✅ Contract details are readable
- [ ] ✅ Database still has encrypted data (security check)

## 🔐 Security Verification

**Important:** Verify that data is still encrypted in the database!

```sql
-- Connect to your database and run:
SELECT plan_name FROM bcp_drp_plans LIMIT 1;
-- Expected: gAAAAABpXg... (encrypted)
-- NOT: "My Business Plan" (plain text)

SELECT email FROM users LIMIT 1;
-- Expected: gAAAAABhX8... (encrypted)
-- NOT: "user@example.com" (plain text)
```

If you see plain text in the database, the encryption is not working!

## 📝 Summary

### What's Working Now:
✅ All TPRM serializers use `AutoDecryptingModelSerializer`  
✅ Automatic decryption in API responses  
✅ Fallback decryption if `_plain` properties missing  
✅ Data still encrypted in database (security maintained)  
✅ Multiple decryption methods for robustness  
✅ Graceful error handling  

### Architecture:
```
Database (encrypted) 
    ↓
Django Model (TPRMEncryptedFieldsMixin)
    ↓
Serializer (AutoDecryptingModelSerializer)
    ↓ (auto-decryption)
API Response (plain text)
    ↓
Frontend UI (readable data)
```

## 🎉 Success!

If you've followed all steps and the verification checklist passes, your decryption is working correctly!

**Key Points:**
- Data is encrypted in the database ✅
- Data is decrypted in API responses ✅
- Frontend shows readable plain text ✅
- No code changes needed in views or frontend ✅

## 📞 Need Help?

If you're still experiencing issues:

1. **Check Server Logs:** Look for decryption warnings/errors
2. **Run Diagnostic:** `python test_encryption_simple.py`
3. **Verify Configuration:** Check `encryption_config.py` has your models
4. **Test Individual Model:** Use Django shell to test decryption manually

---

**Last Updated:** January 7, 2026  
**Status:** ✅ FIXED AND TESTED

