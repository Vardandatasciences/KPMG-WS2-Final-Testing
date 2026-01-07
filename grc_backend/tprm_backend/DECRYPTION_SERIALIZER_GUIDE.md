# TPRM Decryption in Serializers - Complete Guide

## Problem
Data is encrypted in the database (✅ working), but serializers return encrypted data to the frontend (❌ not working).

## Solution
Update all `ModelSerializer` classes to use `SerializerMethodField` for encrypted fields and access `_plain` properties.

---

## ✅ FIXED: BCP/DRP Serializers

### File: `bcpdrp/serializers.py`

**Updated Serializers:**
1. ✅ `PlanListSerializer` - decrypts `strategy_name`, `plan_name`, `plan_scope`
2. ✅ `QuestionSerializer` - decrypts `question_text`
3. ✅ `QuestionnaireListSerializer` - decrypts `title`, `description`
4. ✅ `QuestionnaireDetailSerializer` - decrypts `title`, `description`, `reviewer_comment`
5. ✅ `UserSerializer` - decrypts `user_name`, `email`, `first_name`, `last_name`

---

## 🔧 Pattern to Follow

### Before (Returns Encrypted Data ❌)
```python
class MySerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = ['id', 'name', 'email', 'description']  # These return encrypted!
```

### After (Returns Decrypted Data ✅)
```python
class MySerializer(serializers.ModelSerializer):
    # Override encrypted fields with SerializerMethodField
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    
    class Meta:
        model = MyModel
        fields = ['id', 'name', 'email', 'description']
    
    def get_name(self, obj):
        """Return decrypted name"""
        return obj.name_plain if obj.name else None
    
    def get_email(self, obj):
        """Return decrypted email"""
        return obj.email_plain if obj.email else None
    
    def get_description(self, obj):
        """Return decrypted description"""
        return obj.description_plain if obj.description else None
```

---

## 📝 Step-by-Step Process

### Step 1: Identify Encrypted Fields
Check `utils/encryption_config.py` for your model:

```python
TPRM_ENCRYPTED_FIELDS_CONFIG = {
    'MyModel': [
        'name',
        'email',
        'description',
    ],
}
```

### Step 2: Update Serializer
For each encrypted field in the serializer:

1. Add `SerializerMethodField` declaration
2. Add `get_<field_name>` method that returns `obj.<field_name>_plain`

### Step 3: Test
```python
# In Django shell or API response
from myapp.models import MyModel
from myapp.serializers import MySerializer

obj = MyModel.objects.first()
serializer = MySerializer(obj)
print(serializer.data)  # Should show decrypted data
```

---

## 🎯 All TPRM Modules That Need Updates

### Priority 1: CRITICAL (User-facing data) 🔴

#### 1. **users/serializers.py**
- Models: `User`, `UserProfile`, `UserSession`
- Encrypted fields: `phone`, `email`, `first_name`, `last_name`, `bio`, `ip_address`, `user_agent`

#### 2. **mfa_auth/** (if has serializers)
- Models: `User`, `MfaEmailChallenge`, `MfaAuditLog`
- Encrypted fields: Check `encryption_config.py`

#### 3. **vendors/serializers.py**
- Models: `Vendor`, `VendorContact`, `VendorDocument`, etc.
- Encrypted fields: `company_name`, `legal_name`, `tax_id`, `email`, `phone`, etc.

### Priority 2: HIGH (Business data) 🟠

#### 4. **contracts/serializers.py**
- Models: `Contract`
- Encrypted fields: Contract details, terms, etc.

#### 5. **slas/serializers.py**
- Models: `VendorSLA`
- Encrypted fields: SLA details, metrics, etc.

#### 6. **rfp/serializers.py**
- Models: `RFP`
- Encrypted fields: RFP details

#### 7. **audits/serializers.py**
- Models: `Audit`, `AuditFinding`, `AuditReport`
- Encrypted fields: `title`, `scope`, `evidence_comments`, `findings`, etc.

#### 8. **audits_contract/serializers.py**
- Models: `ContractAudit`, `ContractAuditFinding`
- Encrypted fields: Similar to audits

### Priority 3: MEDIUM (Supporting data) 🟡

#### 9. **risk_analysis/serializers.py** (4 modules)
- Models: `Risk`
- Encrypted fields: `title`, `description`, `ai_explanation`

#### 10. **rfp_approval/serializers.py**
- Models: `ApprovalWorkflows`, `ApprovalRequests`, `ApprovalStages`, `ApprovalComments`
- Encrypted fields: Workflow details, comments, etc.

#### 11. **slas/slaapproval/serializers.py**
- Models: `SLAApproval`
- Encrypted fields: Approval details

#### 12. **compliance/serializers.py**
- Models: `Framework`, `ComplianceMapping`
- Encrypted fields: Descriptions, URLs

#### 13. **notifications/serializers.py**
- Models: `Notification`
- Encrypted fields: `title`, `message`

#### 14. **ocr_app/serializers.py**
- Models: `Document`, `OcrResult`, `ExtractedData`
- Encrypted fields: Document content, OCR text

#### 15. **apps/vendor_core/** (if has serializers)
- Models: All vendor core models
- Encrypted fields: Vendor data

---

## 🛠️ Automated Helper Script

Create a script to help update serializers:

```python
# utils/update_serializers.py
from .encryption_config import TPRM_ENCRYPTED_FIELDS_CONFIG

def generate_serializer_methods(model_name):
    """Generate SerializerMethodField code for a model"""
    fields = TPRM_ENCRYPTED_FIELDS_CONFIG.get(model_name, [])
    
    if not fields:
        return "# No encrypted fields for this model"
    
    # Generate field declarations
    declarations = []
    for field in fields:
        declarations.append(f"    {field} = serializers.SerializerMethodField()")
    
    # Generate getter methods
    methods = []
    for field in fields:
        methods.append(f"")
        methods.append(f"    def get_{field}(self, obj):")
        methods.append(f"        \"\"\"Return decrypted {field}\"\"\"")
        methods.append(f"        return obj.{field}_plain if obj.{field} else None")
    
    return "\n".join(declarations) + "\n" + "\n".join(methods)

# Usage:
print(generate_serializer_methods('Risk'))
```

---

## ✅ Verification

### Test Each Serializer
```python
# Test in Django shell
from myapp.models import MyModel
from myapp.serializers import MySerializer

# Get instance
obj = MyModel.objects.first()

# Check encrypted in DB
print("Encrypted in DB:", obj.name)  # Should start with gAAAAA

# Check decrypted via _plain
print("Decrypted via _plain:", obj.name_plain)  # Should be plain text

# Check serializer output
serializer = MySerializer(obj)
print("Serializer output:", serializer.data['name'])  # Should be plain text ✅
```

### Test API Endpoint
```bash
# Call your API
curl http://localhost:8000/api/plans/

# Check response - should show decrypted data
{
    "plan_id": 12,
    "plan_name": "enrytion",  # ✅ Decrypted (plain text)
    "strategy_name": "Account Management"  # ✅ Decrypted
}
```

---

## 📋 Checklist for Each Module

- [ ] Identify all `ModelSerializer` classes in the module
- [ ] Check which fields are encrypted (from `encryption_config.py`)
- [ ] Add `SerializerMethodField` for each encrypted field
- [ ] Add `get_<field>` method that returns `obj.<field>_plain`
- [ ] Test serializer output shows decrypted data
- [ ] Test API endpoint returns decrypted data
- [ ] Document changes

---

## 🚨 Common Mistakes to Avoid

### ❌ Mistake 1: Forgetting to check null values
```python
def get_name(self, obj):
    return obj.name_plain  # Error if name is None!
```

### ✅ Correct:
```python
def get_name(self, obj):
    return obj.name_plain if obj.name else None
```

### ❌ Mistake 2: Not importing SerializerMethodField
```python
from rest_framework import serializers  # ✅ This is correct
```

### ❌ Mistake 3: Typo in method name
```python
name = serializers.SerializerMethodField()

def get_names(self, obj):  # ❌ Should be get_name (singular)
    return obj.name_plain
```

---

## 📊 Progress Tracking

| Module | Serializers File | Status | Encrypted Fields |
|--------|-----------------|--------|------------------|
| bcpdrp | ✅ DONE | Complete | plan_name, strategy_name, etc. |
| users | ❌ TODO | Pending | phone, email, first_name, last_name |
| vendors | ❌ TODO | Pending | company_name, legal_name, tax_id |
| contracts | ❌ TODO | Pending | contract details |
| slas | ❌ TODO | Pending | SLA details |
| rfp | ❌ TODO | Pending | RFP details |
| audits | ❌ TODO | Pending | audit findings |
| audits_contract | ❌ TODO | Pending | contract audit findings |
| risk_analysis | ❌ TODO | Pending | title, description, ai_explanation |
| risk_analysis_vendor | ❌ TODO | Pending | title, description |
| rfp_risk_analysis | ❌ TODO | Pending | title, description |
| contract_risk_analysis | ❌ TODO | Pending | title, description |
| rfp_approval | ❌ TODO | Pending | workflow details |
| slas/slaapproval | ❌ TODO | Pending | approval details |
| compliance | ❌ TODO | Pending | framework descriptions |
| notifications | ❌ TODO | Pending | title, message |
| ocr_app | ❌ TODO | Pending | OCR text, document content |
| mfa_auth | ❌ TODO | Pending | user data, IP addresses |
| vendor_core | ❌ TODO | Pending | vendor data |

---

## 🎯 Next Steps

1. ✅ BCP/DRP serializers updated
2. ⏭️ Update all other serializers following the same pattern
3. ⏭️ Test each module's API endpoints
4. ⏭️ Update frontend if needed to handle new response structure

---

**Remember:** The `_plain` properties are automatically available thanks to `TPRMEncryptedFieldsMixin`. You just need to use them in serializers!

