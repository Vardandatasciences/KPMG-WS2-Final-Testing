# 🔧 Fix All TPRM Serializers - Automated Solution

## ✅ Solution: Use Base Serializer with Auto-Decryption

Instead of manually updating 27 serializer files, create a **base serializer** that automatically handles decryption!

---

## 📝 Implementation

### Step 1: Create Auto-Decrypting Base Serializer

Create file: `tprm_backend/utils/base_serializer.py`

```python
"""
Base serializer with automatic decryption support for encrypted fields.
"""
from rest_framework import serializers
from .encryption_config import get_encrypted_fields_for_model


class AutoDecryptingModelSerializer(serializers.ModelSerializer):
    """
    Base ModelSerializer that automatically decrypts encrypted fields.
    
    Usage:
        class MySerializer(AutoDecryptingModelSerializer):
            class Meta:
                model = MyModel
                fields = '__all__'
    
    The serializer will automatically:
    1. Detect which fields are encrypted (from encryption_config.py)
    2. Return decrypted values using _plain properties
    3. Handle null values gracefully
    """
    
    def to_representation(self, instance):
        """
        Override to_representation to automatically decrypt encrypted fields.
        """
        # Get the normal representation
        ret = super().to_representation(instance)
        
        # Get encrypted fields for this model
        model_name = instance.__class__.__name__
        encrypted_fields = get_encrypted_fields_for_model(model_name)
        
        # Replace encrypted values with decrypted ones
        for field_name in encrypted_fields:
            if field_name in ret:
                # Try to get decrypted value using _plain property
                plain_property = f"{field_name}_plain"
                if hasattr(instance, plain_property):
                    try:
                        decrypted_value = getattr(instance, plain_property)
                        ret[field_name] = decrypted_value
                    except Exception:
                        # If decryption fails, keep original value
                        pass
        
        return ret
```

### Step 2: Update All Serializers

**Option A: Global Replace (Recommended)**

Find and replace in all serializer files:
- Find: `serializers.ModelSerializer`
- Replace with: `AutoDecryptingModelSerializer`

Add import at the top of each file:
```python
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
```

**Option B: Manual Update (If needed)**

For each serializer file, replace:
```python
# OLD
from rest_framework import serializers

class MySerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'
```

With:
```python
# NEW
from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer

class MySerializer(AutoDecryptingModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'
```

---

## 🎯 Files to Update (27 Total)

### High Priority (User/Vendor Data)
1. ✅ `bcpdrp/serializers.py` - Already manually fixed
2. ❌ `users/serializers.py`
3. ❌ `apps/vendor_core/serializers.py`
4. ❌ `vendors/serializers.py` (if exists)
5. ❌ `mfa_auth/serializers.py`

### Medium Priority (Business Data)
6. ❌ `contracts/serializers.py`
7. ❌ `slas/serializers.py`
8. ❌ `rfp/serializers.py`
9. ❌ `audits/serializers.py`
10. ❌ `audits_contract/serializers.py`
11. ❌ `contracts/contractapproval/serializers.py`

### Standard Priority (Supporting Data)
12. ❌ `risk_analysis/serializers.py`
13. ❌ `risk_analysis_vendor/serializers.py`
14. ❌ `rfp_risk_analysis/serializers.py`
15. ❌ `contract_risk_analysis/serializers.py`
16. ❌ `database/rfp_risk_analysis/risk_analysis/serializers.py`
17. ❌ `slas/slaapproval/serializers.py`
18. ❌ `compliance/serializers.py`
19. ❌ `notifications/serializers.py`
20. ❌ `ocr_app/serializers.py`
21. ❌ `core/serializers.py`
22. ❌ `admin_access/serializers.py`
23. ❌ `quick_access/serializers.py`
24. ❌ `global_search/serializers.py`
25. ❌ `apps/vendor_questionnaire/serializers.py`
26. ❌ `apps/vendor_lifecycle/serializers.py`
27. ❌ `apps/vendor_risk/serializers.py`
28. ❌ `rfp_old/serializers.py`

---

## ✅ Benefits of AutoDecryptingModelSerializer

### 1. **Automatic** - No manual field mapping needed
```python
# Just use it like normal ModelSerializer
class UserSerializer(AutoDecryptingModelSerializer):
    class Meta:
        model = User
        fields = '__all__'  # Encrypted fields automatically decrypted!
```

### 2. **Centralized** - One place to maintain decryption logic
- All encryption logic in `base_serializer.py`
- Easy to update/debug
- Consistent across all modules

### 3. **Backward Compatible** - Works with existing serializers
- Non-encrypted fields work normally
- Can still use `SerializerMethodField` for custom logic
- No breaking changes

### 4. **Safe** - Handles errors gracefully
- Null values handled
- Decryption failures don't break serialization
- Falls back to original value if needed

---

## 🧪 Testing

### Test 1: Verify Auto-Decryption
```python
from tprm_backend.users.models import User
from tprm_backend.users.serializers import UserSerializer

user = User.objects.first()

# Check encrypted in DB
print("Encrypted:", user.email)  # gAAAAA...

# Check serializer decrypts
serializer = UserSerializer(user)
print("Serialized:", serializer.data['email'])  # Should be plain text ✅
```

### Test 2: API Endpoint
```bash
curl http://localhost:8000/api/users/1/

# Response should show decrypted data
{
    "user_id": 1,
    "email": "user@example.com",  # ✅ Decrypted
    "first_name": "John",  # ✅ Decrypted
    "last_name": "Doe"  # ✅ Decrypted
}
```

---

## 📊 Progress Tracker

Create checklist as you update each file:

```python
# utils/check_serializers.py
"""Check which serializers use AutoDecryptingModelSerializer"""
import os
import re

SERIALIZER_FILES = [
    'bcpdrp/serializers.py',
    'users/serializers.py',
    'apps/vendor_core/serializers.py',
    # ... add all 27 files
]

for file_path in SERIALIZER_FILES:
    full_path = f'tprm_backend/{file_path}'
    if os.path.exists(full_path):
        with open(full_path, 'r') as f:
            content = f.read()
            if 'AutoDecryptingModelSerializer' in content:
                print(f"✅ {file_path}")
            elif 'ModelSerializer' in content:
                print(f"❌ {file_path} - Needs update")
            else:
                print(f"⚠️  {file_path} - No ModelSerializer found")
```

---

## 🚀 Quick Start

1. **Create base_serializer.py** (code above)
2. **Test with one file first** (e.g., users/serializers.py)
3. **If working, update all 27 files**
4. **Test each API endpoint**
5. **Mark complete** ✅

---

## 💡 Alternative: Per-Module Approach

If you prefer to update manually, use this template for each file:

```python
from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import MyModel

# OLD WAY (returns encrypted data)
class MySerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'

# NEW WAY (returns decrypted data)
class MySerializer(AutoDecryptingModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'
```

---

## 📋 Verification Checklist

After updating all serializers:

- [ ] Created `utils/base_serializer.py`
- [ ] Updated all 27 serializer files
- [ ] Tested users module API
- [ ] Tested vendors module API
- [ ] Tested BCP/DRP module API
- [ ] Tested contracts module API
- [ ] Tested SLAs module API
- [ ] Tested RFP module API
- [ ] Tested audits module API
- [ ] Tested risk analysis modules API
- [ ] Tested notifications API
- [ ] Tested MFA auth API
- [ ] All API endpoints return decrypted data
- [ ] No errors in console/logs
- [ ] Frontend displays data correctly

---

## 🎉 Expected Result

After implementing this solution:

- ✅ All encrypted data in database
- ✅ All API responses show decrypted data
- ✅ No manual `SerializerMethodField` needed for encrypted fields
- ✅ Consistent behavior across all modules
- ✅ Easy to maintain and extend

---

**Next Step: Create `base_serializer.py` and start updating serializers!**

