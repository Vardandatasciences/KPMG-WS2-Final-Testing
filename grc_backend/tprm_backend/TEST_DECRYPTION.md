# Testing TPRM Encryption/Decryption

## Quick Test in Django Shell

```python
python manage.py shell

# Test 1: Check if encryption is working
from tprm_backend.bcpdrp.models import Plan

# Get a plan
plan = Plan.objects.first()

# Check encrypted value (should show encrypted string starting with gAAAAA)
print("Encrypted plan_name:", plan.plan_name)

# Check decrypted value (should show plain text)
print("Decrypted plan_name:", plan.plan_name_plain)

# Test 2: Check if mixin has decryption method
print("Has _get_decrypted_value?", hasattr(plan, '_get_decrypted_value'))

# Test 3: Manual decryption
from tprm_backend.utils.data_encryption import decrypt_data
print("Manual decrypt:", decrypt_data(plan.plan_name))
```

## Test All Encrypted Fields

```python
# Get encrypted fields for model
encrypted_fields = plan.get_encrypted_fields()
print("Encrypted fields for Plan:", encrypted_fields)

# Test each field
for field in encrypted_fields:
    if hasattr(plan, field):
        encrypted_value = getattr(plan, field)
        plain_property = f"{field}_plain"
        
        if hasattr(plan, plain_property):
            decrypted_value = getattr(plan, plain_property)
            print(f"{field}: {encrypted_value[:20]}... => {decrypted_value}")
        else:
            print(f"WARNING: {plain_property} not found!")
```

## Test in Serializer

```python
# In your serializer
class PlanSerializer(serializers.ModelSerializer):
    # Use SerializerMethodField for decrypted values
    plan_name = serializers.SerializerMethodField()
    strategy_name = serializers.SerializerMethodField()
    
    def get_plan_name(self, obj):
        # Option 1: Use _plain property
        return obj.plan_name_plain
        
        # Option 2: Manual decryption
        from tprm_backend.utils.data_encryption import decrypt_data
        return decrypt_data(obj.plan_name)
    
    def get_strategy_name(self, obj):
        return obj.strategy_name_plain
```

## Common Issues and Solutions

### Issue 1: _plain property returns encrypted data
**Cause:** `__getattribute__` method not working correctly
**Solution:** Use manual decryption in serializer

```python
from tprm_backend.utils.data_encryption import decrypt_data

@property
def plan_name_decrypted(self):
    return decrypt_data(self.plan_name)
```

### Issue 2: AttributeError when accessing _plain
**Cause:** Model doesn't inherit from TPRMEncryptedFieldsMixin
**Solution:** Add mixin to model

```python
from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin

class MyModel(TPRMEncryptedFieldsMixin, models.Model):
    # ...
```

### Issue 3: Field not configured in encryption_config.py
**Cause:** Field not added to TPRM_ENCRYPTED_FIELDS_CONFIG
**Solution:** Add field to config

```python
# In encryption_config.py
TPRM_ENCRYPTED_FIELDS_CONFIG = {
    'MyModel': [
        'sensitive_field',
    ],
}
```

## Verification Checklist

- [ ] Model inherits from `TPRMEncryptedFieldsMixin`
- [ ] Fields are listed in `encryption_config.py`
- [ ] Data is encrypted in database (starts with `gAAAAA`)
- [ ] `_plain` properties return decrypted values
- [ ] Serializers use decrypted values
- [ ] Views return decrypted data to frontend

