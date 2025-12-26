# How to Check Encryption and See Plain Text Values

## Quick Guide

This guide shows you:
1. ✅ How data is saved (encryption process)
2. ✅ How to check if encryption is working
3. ✅ How to retrieve and see plain text values

---

## 1. How Data is Saved (Automatic Encryption)

### Step-by-Step Process

When you create or update a user, encryption happens **automatically**:

```python
from grc.models import Users
from django.contrib.auth.hashers import make_password

# Step 1: Create user object with plain text data
user = Users(
    UserName="john_doe",
    Password=make_password("SecurePassword123"),
    Email="john@example.com",        # ← Plain text
    PhoneNumber="+1234567890",        # ← Plain text
    Address="123 Main St, NY"         # ← Plain text
)

# Step 2: Save (triggers automatic encryption)
user.save()  # ← Email, PhoneNumber, Address are encrypted here automatically

# Step 3: Database now contains encrypted values
# user.Email = "gAAAAABh..." (encrypted)
# user.PhoneNumber = "gAAAAABh..." (encrypted)
# user.Address = "gAAAAABh..." (encrypted)
```

### What Happens in the `save()` Method

The `Users` model automatically:

1. **Checks if data is already encrypted** (for backward compatibility)
2. **Encrypts plain text data** if not encrypted
3. **Saves encrypted data** to database
4. **Returns success** (encryption is transparent)

---

## 2. How to Check if Encryption is Working

### Method 1: Run the Test Script

```bash
cd grc_backend
python test_encryption.py
```

This will:
- ✅ Create a test user
- ✅ Show encrypted values in database
- ✅ Show decrypted plain text values
- ✅ Verify encryption/decryption works correctly

### Method 2: Check Existing Users

```bash
python test_encryption.py show
```

This shows the encryption status of existing users in your database.

### Method 3: Manual Check in Python/Django Shell

```python
# Start Django shell
python manage.py shell

# Import models
from grc.models import Users
from grc.utils.data_encryption import is_encrypted_data

# Get a user
user = Users.objects.get(UserId=1)

# Check if encrypted
print("Email encrypted?", is_encrypted_data(user.Email))
print("Phone encrypted?", is_encrypted_data(user.PhoneNumber))
print("Address encrypted?", is_encrypted_data(user.Address))

# Encrypted data looks like: "gAAAAABh..."
# Plain text looks like: "user@example.com"
```

---

## 3. How to See Original Plain Text Values

### ✅ Method 1: Using Properties (Recommended)

The `Users` model provides properties that automatically decrypt data:

```python
from grc.models import Users

# Get user
user = Users.objects.get(UserId=1)

# Access plain text values using properties
print(user.email_plain)    # "john@example.com" ✅
print(user.phone_plain)    # "+1234567890" ✅
print(user.address_plain)  # "123 Main St, NY" ✅

# These properties decrypt the data automatically
```

### ✅ Method 2: Using Decryption Function Directly

```python
from grc.models import Users
from grc.utils.data_encryption import decrypt_data

# Get user
user = Users.objects.get(UserId=1)

# Decrypt manually
email = decrypt_data(user.Email)
phone = decrypt_data(user.PhoneNumber)
address = decrypt_data(user.Address)

print(email)    # "john@example.com" ✅
print(phone)    # "+1234567890" ✅
print(address)  # "123 Main St, NY" ✅
```

### ❌ DON'T Do This (Shows Encrypted Data)

```python
user = Users.objects.get(UserId=1)

# These show ENCRYPTED values (not what you want)
print(user.Email)        # "gAAAAABh..." ❌ (encrypted)
print(user.PhoneNumber)  # "gAAAAABh..." ❌ (encrypted)
print(user.Address)      # "gAAAAABh..." ❌ (encrypted)
```

---

## 4. Complete Example: Full Workflow

```python
from grc.models import Users
from django.contrib.auth.hashers import make_password

# ============================================
# CREATE USER (Plain Text → Encrypted)
# ============================================
print("1. Creating user with plain text data...")
user = Users(
    UserName="alice",
    Password=make_password("Password123"),
    Email="alice@example.com",      # Plain text
    PhoneNumber="+1234567890",       # Plain text
    Address="456 Oak Ave"            # Plain text
)
user.save()
print(f"   ✅ User created: UserId = {user.UserId}")

# ============================================
# CHECK DATABASE VALUES (Should be Encrypted)
# ============================================
print("\n2. Checking database values...")
print(f"   Email in DB: {user.Email[:50]}...")           # Encrypted
print(f"   Phone in DB: {user.PhoneNumber[:50]}...")     # Encrypted
print(f"   Address in DB: {user.Address[:50]}...")       # Encrypted

# ============================================
# RETRIEVE PLAIN TEXT (Encrypted → Plain Text)
# ============================================
print("\n3. Retrieving plain text values...")
print(f"   Email (plain): {user.email_plain}")           # "alice@example.com" ✅
print(f"   Phone (plain): {user.phone_plain}")           # "+1234567890" ✅
print(f"   Address (plain): {user.address_plain}")       # "456 Oak Ave" ✅

# ============================================
# UPDATE USER (Auto-encryption on Save)
# ============================================
print("\n4. Updating user email...")
user.Email = "alice.new@example.com"  # Plain text
user.save()  # Automatically encrypts
print(f"   ✅ Email updated")
print(f"   Email (plain): {user.email_plain}")  # "alice.new@example.com" ✅

# ============================================
# FIND USER BY EMAIL
# ============================================
print("\n5. Finding user by email...")
found_user = Users.find_by_email("alice.new@example.com")
if found_user:
    print(f"   ✅ Found user: {found_user.UserName}")
    print(f"   Email: {found_user.email_plain}")
```

---

## 5. In API Views/Endpoints

When returning data to the frontend, use the plain text properties:

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from grc.models import Users

@api_view(['GET'])
def get_user_profile(request, user_id):
    user = Users.objects.get(UserId=user_id)
    
    return Response({
        'userId': user.UserId,
        'username': user.UserName,
        'email': user.email_plain,      # ✅ Use plain text
        'phoneNumber': user.phone_plain,  # ✅ Use plain text
        'address': user.address_plain,    # ✅ Use plain text
    })
```

---

## 6. Common Scenarios

### Scenario 1: Creating New User

```python
# ✅ Correct way
user = Users(
    Email="newuser@example.com",  # Plain text (will be encrypted)
    PhoneNumber="+1234567890",     # Plain text (will be encrypted)
    # ... other fields
)
user.save()  # Encrypts automatically

# Access plain text later
print(user.email_plain)  # "newuser@example.com" ✅
```

### Scenario 2: Updating User Email

```python
# ✅ Correct way
user = Users.objects.get(UserId=1)
user.Email = "updated@example.com"  # Plain text
user.save()  # Encrypts automatically

# Access plain text
print(user.email_plain)  # "updated@example.com" ✅
```

### Scenario 3: Searching by Email

```python
# ✅ Correct way (handles encryption)
user = Users.find_by_email("user@example.com")
if user:
    print(user.email_plain)  # Plain text ✅

# ❌ Wrong way (won't work with encrypted data)
# user = Users.objects.get(Email="user@example.com")  # Won't find encrypted email
```

### Scenario 4: Displaying User Data

```python
# ✅ Correct way
user = Users.objects.get(UserId=1)

# Use plain text properties
data = {
    'email': user.email_plain,        # ✅
    'phone': user.phone_plain,        # ✅
    'address': user.address_plain     # ✅
}

# ❌ Wrong way
data = {
    'email': user.Email,        # ❌ Encrypted value
    'phone': user.PhoneNumber,  # ❌ Encrypted value
    'address': user.Address     # ❌ Encrypted value
}
```

---

## 7. Troubleshooting

### Problem: Getting encrypted values instead of plain text

**Solution:** Use the `*_plain` properties:
```python
# Wrong
print(user.Email)  # Encrypted

# Right
print(user.email_plain)  # Plain text ✅
```

### Problem: Can't find user by email

**Solution:** Use `find_by_email()` method:
```python
# Wrong
user = Users.objects.get(Email="user@example.com")

# Right
user = Users.find_by_email("user@example.com") ✅
```

### Problem: Data not encrypting on save

**Check:**
1. Is `GRC_ENCRYPTION_KEY` set in environment variables?
2. Is the encryption service imported correctly?
3. Check logs for encryption errors

### Problem: Decryption fails

**Possible causes:**
1. Wrong encryption key
2. Data is already plain text (backward compatibility)
3. Corrupted encrypted data

The system handles backward compatibility automatically - if decryption fails, it returns the original value (assumes plain text).

---

## 8. Quick Reference

| Task | Code |
|------|------|
| **Create user** | `user = Users(Email="x", ...); user.save()` |
| **Get plain text email** | `user.email_plain` ✅ |
| **Get plain text phone** | `user.phone_plain` ✅ |
| **Get plain text address** | `user.address_plain` ✅ |
| **Find by email** | `Users.find_by_email("x")` ✅ |
| **Check if encrypted** | `is_encrypted_data(user.Email)` |
| **Manual decrypt** | `decrypt_data(user.Email)` |

---

## Summary

✅ **Saving**: Just use plain text - encryption is automatic
✅ **Reading**: Use `*_plain` properties to get decrypted values
✅ **Searching**: Use `find_by_email()` method
✅ **Testing**: Run `python test_encryption.py`

The encryption is **transparent** - you work with plain text, the system handles encryption/decryption automatically!

