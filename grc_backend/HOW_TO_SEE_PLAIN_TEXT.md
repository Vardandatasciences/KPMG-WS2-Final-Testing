# How to See Plain Text Later - Quick Answer

## Your Question: "How can we see later the plain text?"

**Answer:** Use **ENCRYPTION** (not hashing) for data you need to retrieve later.

---

## Quick Comparison

| Method | Can See Plain Text Later? | Use For |
|--------|--------------------------|---------|
| **Hashing** | ❌ **NO** - One-way only | Passwords, OTPs |
| **Encryption** | ✅ **YES** - Two-way | Email, Phone, Address |

---

## Simple Example

### Step 1: Encrypt When Saving

```python
from grc.utils.data_encryption import encrypt_data

# Save encrypted data
user.Email = encrypt_data("user@example.com")
user.save()  # Database stores: "gAAAAABh..." (encrypted)
```

### Step 2: Decrypt When Reading

```python
from grc.utils.data_encryption import decrypt_data

# Retrieve and decrypt
user = Users.objects.get(UserId=1)
plain_email = decrypt_data(user.Email)
print(plain_email)  # Output: "user@example.com" ✅
```

---

## Code You Can Use Right Now

```python
# Import the functions
from grc.utils.data_encryption import encrypt_data, decrypt_data

# ENCRYPT (when saving to database)
encrypted_email = encrypt_data("john@example.com")
user.Email = encrypted_email
user.save()

# DECRYPT (when you need to see the plain text)
plain_text = decrypt_data(user.Email)
print(plain_text)  # Shows: "john@example.com"
```

---

## Complete Example in Your Models

```python
from django.db import models
from grc.utils.data_encryption import encrypt_data, decrypt_data

class Users(models.Model):
    Email = models.CharField(max_length=255)
    
    def save(self, *args, **kwargs):
        # Encrypt before saving
        if self.Email:
            self.Email = encrypt_data(self.Email)
        super().save(*args, **kwargs)
    
    @property
    def email_plain(self):
        # Decrypt to see plain text
        return decrypt_data(self.Email)
```

**Usage:**
```python
# Save
user = Users(Email="john@example.com")
user.save()  # Stored encrypted

# Read
user = Users.objects.get(UserId=1)
print(user.email_plain)  # Shows: "john@example.com"
```

---

## Key Points

1. ✅ **Encryption** = Can encrypt AND decrypt (see plain text later)
2. ❌ **Hashing** = Can only verify, cannot see plain text
3. 🔑 **You need the encryption key** to decrypt (store it securely!)

---

## Files Created

1. `grc/utils/data_encryption.py` - Encryption service
2. `ENCRYPTION_IMPLEMENTATION_GUIDE.md` - Detailed guide
3. `encryption_demo.py` - Demo script you can run

---

## Run the Demo

```bash
cd grc_backend
python encryption_demo.py
```

This will show you exactly how encryption/decryption works!

