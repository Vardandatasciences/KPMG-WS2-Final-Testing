# GRC Database: Data Hashing and Encryption Analysis

## Overview

This document provides a comprehensive analysis of sensitive data stored in the GRC database, current protection mechanisms, and recommendations for data hashing/encryption.

---

## Important Terminology

### Hashing vs Encryption

1. **Hashing (One-way)**
   - Used for: Passwords, OTPs
   - Purpose: Verify data integrity, cannot be reversed
   - Method: `hash(input)` → produces unique hash
   - Verification: `hash(new_input) == stored_hash`
   - Examples: PBKDF2-SHA256, SHA-256, bcrypt
   - **You cannot "unhash"** - you can only verify by hashing the input

2. **Encryption (Two-way)**
   - Used for: Sensitive data that needs to be retrieved (emails, phone numbers, addresses)
   - Purpose: Protect data while allowing retrieval
   - Method: `encrypt(data, key)` → encrypted data
   - Retrieval: `decrypt(encrypted_data, key)` → original data
   - Examples: AES-256, Fernet (symmetric encryption)
   - **You can decrypt** (if you have the key)

---

## Current Protection Status

### ✅ Currently Protected (Hashed)

1. **Passwords**
   - **Model**: `Users.Password`
   - **Method**: Django's `make_password()` - PBKDF2-SHA256
   - **Status**: ✅ Properly hashed
   - **Location**: `grc/models.py:16`
   - **Verification**: Uses `check_password()` in authentication

2. **Password History**
   - **Model**: `PasswordLog.OldPassword`, `PasswordLog.NewPassword`
   - **Method**: Hashed passwords stored
   - **Status**: ✅ Properly hashed
   - **Location**: `grc/models.py:1023-1024`

3. **OTPs (One-Time Passwords)**
   - **Model**: `MfaEmailChallenge.OtpHash`
   - **Method**: SHA-256 hashing
   - **Status**: ✅ Properly hashed
   - **Location**: `grc/models.py:2973, 3002-3010`

---

### ⚠️ Sensitive Data NOT Currently Encrypted

The following fields contain potentially sensitive personal information (PII) but are stored in **plain text**:

#### Users Table (`Users` model)

1. **Email Address**
   - **Field**: `Users.Email`
   - **Type**: `EmailField(max_length=100)`
   - **Risk Level**: 🔴 High (PII)
   - **Recommendation**: Consider encryption for GDPR/privacy compliance
   - **Location**: `grc/models.py:19`

2. **Phone Number**
   - **Field**: `Users.PhoneNumber`
   - **Type**: `CharField(max_length=20)`
   - **Risk Level**: 🔴 High (PII)
   - **Recommendation**: Consider encryption
   - **Location**: `grc/models.py:22`

3. **Address**
   - **Field**: `Users.Address`
   - **Type**: `TextField`
   - **Risk Level**: 🔴 High (PII)
   - **Recommendation**: Consider encryption
   - **Location**: `grc/models.py:23`

4. **Session Token**
   - **Field**: `Users.session_token`
   - **Type**: `CharField(max_length=1045)`
   - **Risk Level**: 🟠 Medium-High (Security)
   - **Recommendation**: Should be hashed (if stored) or use JWT
   - **Location**: `grc/models.py:26`

5. **License Key**
   - **Field**: `Users.license_key`
   - **Type**: `CharField(max_length=100)`
   - **Risk Level**: 🟠 Medium (Business)
   - **Recommendation**: Consider encryption
   - **Location**: `grc/models.py:28`

6. **First Name / Last Name**
   - **Fields**: `Users.FirstName`, `Users.LastName`
   - **Type**: `CharField(max_length=255)`
   - **Risk Level**: 🟡 Medium (PII)
   - **Recommendation**: Consider encryption based on compliance requirements
   - **Location**: `grc/models.py:20-21`

7. **User Name**
   - **Field**: `Users.UserName`
   - **Type**: `CharField(max_length=255)`
   - **Risk Level**: 🟡 Low-Medium (Often used for login)
   - **Recommendation**: Usually kept plain text for authentication
   - **Location**: `grc/models.py:15`

#### Logs and Audit Tables

8. **IP Addresses**
   - **Fields**: 
     - `GRCLog.IPAddress`
     - `PasswordLog.IPAddress`
     - `MfaEmailChallenge.IpAddress`
     - `MfaLoginAttempt.IpAddress`
     - Various other log models
   - **Type**: `CharField(max_length=45)` or similar
   - **Risk Level**: 🟡 Medium (Privacy concern)
   - **Recommendation**: Consider hashing or pseudonymization
   - **Location**: Multiple locations in `grc/models.py`

9. **User Agent**
   - **Field**: `PasswordLog.UserAgent`
   - **Type**: `TextField`
   - **Risk Level**: 🟢 Low (Can contain device info)
   - **Recommendation**: Usually kept plain text, but could mask

10. **Additional Info (JSON)**
    - **Fields**: Various `AdditionalInfo` JSON fields in log models
    - **Type**: `JSONField`
    - **Risk Level**: 🔴 High (May contain sensitive data)
    - **Recommendation**: Review content, encrypt if contains PII
    - **Location**: Multiple log models

---

## Data Inventory Fields

Several models include a `data_inventory` JSON field that maps field labels to data types:
- `personal` - Personal identifiable information
- `confidential` - Confidential business data
- `regular` - Regular/non-sensitive data

**Models with data_inventory:**
- `Framework.data_inventory`
- `Policy.data_inventory`
- `SubPolicy.data_inventory`
- `Compliance.data_inventory`
- `Audit.data_inventory`
- `Risk.data_inventory`
- `Incident.data_inventory`

This suggests the system is tracking which fields contain sensitive data, but **encryption is not automatically applied** based on these classifications.

---

## Existing Encryption Infrastructure

The codebase already has some encryption utilities:

1. **Vendor TPRM System**
   - Location: `tprm_backend/database/vendor_sqlalchemy_manager.py`
   - Methods: `vendor_encrypt_sensitive_data()`, `vendor_decrypt_sensitive_data()`
   - Technology: Fernet (symmetric encryption)
   - Uses: `VENDOR_ENCRYPTION_KEY` from settings

2. **Data Masking Service**
   - Location: `grc/routes/Global/data_masking.py`
   - Purpose: Masking for display (one-way, non-reversible)
   - Methods: `mask_email()`, `mask_phone()`, `mask_address()`, `mask_name()`
   - **Note**: This is for display purposes only, not for storage

---

## Recommendations

### Immediate Actions

1. **Review Compliance Requirements**
   - Check GDPR, CCPA, and other applicable privacy regulations
   - Determine which fields must be encrypted at rest

2. **Implement Encryption for PII Fields**
   - Email addresses (if required by compliance)
   - Phone numbers (if required by compliance)
   - Addresses (if required by compliance)
   - Consider using Fernet encryption (like the vendor system)

3. **Hash Session Tokens**
   - Session tokens should not be stored in plain text
   - Consider using JWT tokens instead (which don't need storage)

### Implementation Considerations

#### Option 1: Field-Level Encryption
- Encrypt individual fields using Fernet/AES-256
- Pros: Granular control, selective encryption
- Cons: More complex queries, performance overhead

#### Option 2: Database-Level Encryption
- Use database encryption features (e.g., MySQL encryption at rest)
- Pros: Transparent, no application changes
- Cons: Less granular control

#### Option 3: Application-Level Encryption with Model Methods
- Create custom model methods to encrypt/decrypt fields
- Override `save()` and property methods
- Pros: Flexible, application-controlled
- Cons: Requires code changes

### Fields That Should NOT Be Encrypted

- **User IDs**: Needed for relationships and queries
- **Timestamps**: Needed for auditing and queries
- **Status fields**: Needed for filtering and queries
- **Foreign keys**: Needed for database relationships

---

## Current Code Examples

### Password Hashing (Current Implementation)
```python
from django.contrib.auth.hashers import make_password, check_password

# When creating/updating password
user.Password = make_password(plain_password)

# When verifying password
if check_password(provided_password, user.Password):
    # Password is correct
    pass
```

### OTP Hashing (Current Implementation)
```python
import hashlib

# When storing OTP
hashed_otp = hashlib.sha256(otp.encode()).digest()
challenge.OtpHash = hashed_otp

# When verifying OTP
if hashlib.sha256(provided_otp.encode()).digest() == challenge.OtpHash:
    # OTP is correct
    pass
```

### Vendor System Encryption (Reference Implementation)
```python
from cryptography.fernet import Fernet

# Encryption
def vendor_encrypt_sensitive_data(self, data: str) -> str:
    fernet = Fernet(self.vendor_encryption_key)
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data.decode()

# Decryption
def vendor_decrypt_sensitive_data(self, encrypted_data: str) -> str:
    fernet = Fernet(self.vendor_encryption_key)
    decrypted_data = fernet.decrypt(encrypted_data.encode())
    return decrypted_data.decode()
```

---

## Summary Table

| Field | Model | Current Protection | Risk Level | Recommendation |
|-------|-------|-------------------|------------|----------------|
| Password | Users | ✅ Hashed (PBKDF2) | - | Keep as-is |
| Email | Users | ❌ Plain text | 🔴 High | Consider encryption |
| PhoneNumber | Users | ❌ Plain text | 🔴 High | Consider encryption |
| Address | Users | ❌ Plain text | 🔴 High | Consider encryption |
| session_token | Users | ❌ Plain text | 🟠 Medium | Hash or use JWT |
| license_key | Users | ❌ Plain text | 🟠 Medium | Consider encryption |
| FirstName/LastName | Users | ❌ Plain text | 🟡 Medium | Review compliance needs |
| IPAddress | Logs | ❌ Plain text | 🟡 Medium | Consider hashing |
| OTP | MfaEmailChallenge | ✅ Hashed (SHA-256) | - | Keep as-is |

---

## Next Steps

1. **Determine Requirements**: Review regulatory/compliance requirements
2. **Design Encryption Strategy**: Choose encryption approach (field-level vs database-level)
3. **Implement Encryption Service**: Create reusable encryption/decryption utilities
4. **Migrate Existing Data**: Encrypt existing plain-text sensitive data
5. **Update Models**: Add encryption/decryption to model save/retrieve methods
6. **Update API Endpoints**: Ensure encrypted fields are properly handled in views
7. **Testing**: Verify encryption/decryption works correctly
8. **Documentation**: Update API documentation for developers

---

## Questions to Answer

1. **What is the regulatory requirement?**
   - GDPR? CCPA? Industry-specific (HIPAA, PCI-DSS)?
   - What data must be encrypted vs. can remain plain text?

2. **What is the performance impact?**
   - Can the system handle encryption/decryption overhead?
   - Will encrypted fields still allow efficient queries?

3. **Key Management**
   - Where will encryption keys be stored?
   - How will keys be rotated?
   - Who has access to keys?

4. **Backward Compatibility**
   - How to handle existing plain-text data?
   - Migration strategy?

---

*Generated: Analysis of GRC Database Models*
*Last Updated: Based on current codebase structure*

