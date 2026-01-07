# Field-Level Encryption Implementation Guide

## Overview

This system implements **automatic field-level encryption** for all models in the GRC application. Data is encrypted before being saved to the database and automatically decrypted when retrieved through serializers or accessed via `_plain` properties.

## Architecture

### Components

1. **Encryption Configuration** (`utils/encryption_config.py`)
   - Defines which fields should be encrypted for each model
   - Centralized configuration for easy maintenance

2. **EncryptedFieldsMixin** (`utils/encrypted_fields_mixin.py`)
   - Base mixin applied to all models
   - Automatically encrypts configured fields on `save()`
   - Provides `_plain` properties for decrypted access

3. **EncryptedFieldsSerializerMixin** (`utils/encrypted_serializer_mixin.py`)
   - Serializer mixin for DRF
   - Automatically decrypts fields in API responses

4. **Data Encryption Service** (`utils/data_encryption.py`)
   - Core encryption/decryption functionality
   - Uses Fernet symmetric encryption (AES-128 in CBC mode)
   - Supports enterprise key management (AWS Secrets Manager)

## How It Works

### 1. Saving Data (Encryption)

When you save a model instance:

```python
user = Users(
    Email="user@example.com",
    PhoneNumber="1234567890",
    Address="123 Main St"
)
user.save()  # Fields are automatically encrypted before saving
```

The `EncryptedFieldsMixin.save()` method:
- Checks configuration for encrypted fields
- Encrypts values if not already encrypted
- Saves to database

**Result in Database:**
```
Email: gAAAAABhX8K3mN5pQr9sT2vW7xY0zA3bC6dE9fG...
PhoneNumber: gAAAAABhX8K4nO6qRsTuW8xY1zA4bD...
Address: gAAAAABhX8K5oP7rStVvX9yZ2zA5bE...
```

### 2. Accessing Data (Decryption)

#### Option A: Using `_plain` Properties

```python
user = Users.objects.get(UserId=1)

# Access encrypted value (from database)
print(user.Email)  # gAAAAABhX8K3mN5pQr9sT2vW7xY0zA3bC6dE9fG...

# Access decrypted value
print(user.email_plain)  # user@example.com
print(user.phone_plain)  # 1234567890
print(user.address_plain)  # 123 Main St
```

#### Option B: Using Serializers (Automatic Decryption)

```python
from grc.serializers import UsersSerializer

user = Users.objects.get(UserId=1)
serializer = UsersSerializer(user)

# Serialized data automatically has decrypted values
print(serializer.data['Email'])  # user@example.com (decrypted)
```

#### Option C: Manual Decryption

```python
from grc.utils.data_encryption import decrypt_data

user = Users.objects.get(UserId=1)
decrypted_email = decrypt_data(user.Email)
print(decrypted_email)  # user@example.com
```

## Configuration

### Adding Fields to Encryption List

Edit `grc_backend/grc/utils/encryption_config.py`:

```python
ENCRYPTED_FIELDS_CONFIG = {
    'Users': [
        'Email',
        'PhoneNumber',
        'Address',
        # Add more fields here
    ],
    'Policy': [
        'PolicyName',
        'PolicyDescription',
        # Add more fields here
    ],
    # Add more models...
}
```

### Fields That Should NOT Be Encrypted

Do NOT encrypt:
- **Primary keys** (AutoField, BigAutoField)
- **Foreign keys** (ForeignKey, OneToOneField)
- **Dates/DateTime** (DateField, DateTimeField, TimeField)
- **Booleans** (BooleanField)
- **Numbers used as IDs** (IntegerField, BigIntegerField)
- **Passwords** (should use hashing, not encryption)

### Fields That CAN Be Encrypted

- **CharField** (if contains sensitive data)
- **TextField** (if contains sensitive data)
- **EmailField**
- **URLField** (if sensitive)
- **JSONField** (encrypt as string if needed)

## Migration: Encrypting Existing Data

### Step 1: Preview Changes (Dry Run)

```bash
python manage.py encrypt_existing_data --dry-run
```

This shows what would be encrypted without making changes.

### Step 2: Encrypt All Data

```bash
python manage.py encrypt_existing_data
```

This encrypts all plain text data in the database.

### Step 3: Encrypt Specific Model/Field

```bash
# Encrypt all configured fields for Users model
python manage.py encrypt_existing_data --model Users

# Encrypt specific field
python manage.py encrypt_existing_data --model Users --field Email

# Force re-encrypt (even if already encrypted)
python manage.py encrypt_existing_data --model Users --force
```

### Step 4: Verify Encryption

```python
# In Django shell
from grc.models import Users
from grc.utils.data_encryption import is_encrypted_data

user = Users.objects.first()
print(is_encrypted_data(user.Email))  # Should return True
print(user.email_plain)  # Should show decrypted email
```

## Using in Serializers

### Option 1: Use Existing Serializers (Already Updated)

All serializers automatically decrypt fields if they inherit from `EncryptedFieldsSerializerMixin`:

```python
from rest_framework import serializers
from grc.utils.encrypted_serializer_mixin import EncryptedFieldsSerializerMixin
from grc.models import Users

class UsersSerializer(EncryptedFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'
```

### Option 2: Manual Decryption in Serializers

```python
class UsersSerializer(serializers.ModelSerializer):
    email_plain = serializers.SerializerMethodField()
    
    def get_email_plain(self, obj):
        from grc.utils.data_encryption import decrypt_data
        return decrypt_data(obj.Email)
    
    class Meta:
        model = Users
        fields = ['UserId', 'Email', 'email_plain', ...]
```

## Security Considerations

### Encryption Key Management

**Development:**
- Keys are generated from Django `SECRET_KEY`
- Stored in environment or settings

**Production:**
- Use AWS Secrets Manager or environment variables
- Set `GRC_ENCRYPTION_KEY` environment variable
- Use a secure key management service (KMS)

### Generating Encryption Keys

```python
from cryptography.fernet import Fernet

# Generate a new key
key = Fernet.generate_key()
print(key.decode())  # Save this to your key management system

# Example output:
# dGVzdGtleToxMjM0NTY3ODkwYWJjZGVmZ2hpams=
```

### Key Rotation

If you need to rotate keys:

1. **Generate new key**
2. **Re-encrypt all data** using the migration command
3. **Update key** in your key management system
4. **Restart application**

## API Usage Examples

### Creating Encrypted Data

```python
# POST /api/users/
{
    "UserName": "johndoe",
    "Email": "john@example.com",  # Will be encrypted on save
    "PhoneNumber": "1234567890",  # Will be encrypted on save
    "Address": "123 Main St"      # Will be encrypted on save
}
```

### Retrieving Decrypted Data

```python
# GET /api/users/1/
# Response automatically has decrypted values:
{
    "UserId": 1,
    "Email": "john@example.com",  # Decrypted automatically
    "PhoneNumber": "1234567890",  # Decrypted automatically
    "Address": "123 Main St"      # Decrypted automatically
}
```

### Searching/Filtering

**Important:** You cannot directly search encrypted fields. Options:

1. **Search by non-encrypted fields** (IDs, dates, status)
2. **Use hash-based search fields** (add a separate hash field for searching)
3. **Decrypt and filter in application code** (not recommended for large datasets)

```python
# ❌ This won't work (encrypted field):
Users.objects.filter(Email="john@example.com")

# ✅ This works (non-encrypted field):
Users.objects.filter(UserId=1)
Users.objects.filter(IsActive='Y')

# ✅ Using the find_by_email method (if available):
user = Users.find_by_email("john@example.com")
```

## Performance Considerations

### Encryption Overhead

- **Encryption/Decryption:** ~0.1-1ms per field (negligible for most use cases)
- **Database size:** Encrypted data is ~30% larger
- **Query performance:** No impact on indexed fields (IDs, dates)

### Best Practices

1. **Only encrypt sensitive fields** (don't encrypt everything)
2. **Use indexes on non-encrypted fields** for searching
3. **Cache decrypted values** if accessed frequently
4. **Batch operations** when encrypting existing data

## Troubleshooting

### Data Not Encrypting

1. **Check configuration:**
   ```python
   from grc.utils.encryption_config import get_encrypted_fields_for_model
   print(get_encrypted_fields_for_model('Users'))
   ```

2. **Verify mixin is applied:**
   ```python
   from grc.models import Users
   print(EncryptedFieldsMixin in Users.__mro__)
   ```

3. **Check encryption key:**
   ```python
   from grc.utils.data_encryption import get_encryption_service
   service = get_encryption_service()
   # Service should initialize without errors
   ```

### Decryption Failing

1. **Check if data is encrypted:**
   ```python
   from grc.utils.data_encryption import is_encrypted_data
   print(is_encrypted_data(user.Email))
   ```

2. **Verify encryption key** (must match key used for encryption)

3. **Check for backward compatibility** (plain text data should still work)

### MySQL Workbench Shows Encrypted Data

This is **EXPECTED and CORRECT** behavior! 

- MySQL Workbench shows encrypted strings (e.g., `gAAAAABh...`)
- Application automatically decrypts when accessing data
- Use `_plain` properties or serializers to see decrypted values

## Testing

### Unit Test Example

```python
from django.test import TestCase
from grc.models import Users
from grc.utils.data_encryption import is_encrypted_data, decrypt_data

class EncryptionTestCase(TestCase):
    def test_user_email_encryption(self):
        user = Users.objects.create(
            UserName="testuser",
            Email="test@example.com",
            Password="hashedpassword"
        )
        
        # Email should be encrypted in database
        self.assertTrue(is_encrypted_data(user.Email))
        
        # Should be able to decrypt
        self.assertEqual(user.email_plain, "test@example.com")
        
        # Direct field access returns encrypted value
        self.assertNotEqual(user.Email, "test@example.com")
```

## Migration Checklist

- [ ] Review encryption configuration for all models
- [ ] Backup database before encryption
- [ ] Run dry-run to preview changes
- [ ] Encrypt existing data using management command
- [ ] Verify encryption is working (check sample records)
- [ ] Update serializers if needed
- [ ] Test API endpoints return decrypted data
- [ ] Update frontend to handle decrypted data
- [ ] Document any search/filter limitations
- [ ] Set up proper key management for production

## Support

For issues or questions:
1. Check this documentation
2. Review `encryption_config.py` for field configuration
3. Check Django logs for encryption/decryption errors
4. Verify encryption key is properly configured


