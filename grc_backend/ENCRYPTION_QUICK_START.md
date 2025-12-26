# Encryption Quick Start Guide 🚀

## Visual Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     HOW DATA FLOWS                              │
└─────────────────────────────────────────────────────────────────┘

1. SAVING DATA (Plain Text → Encrypted)
   ─────────────────────────────────────
   
   You write:                    Database stores:
   ┌──────────────┐              ┌──────────────┐
   │ Plain Text   │   save()     │  Encrypted   │
   │              │ ──────────→  │              │
   │ Email:       │              │ Email:       │
   │ user@ex.com  │   (auto)     │ gAAAAABh...  │
   └──────────────┘              └──────────────┘


2. READING DATA (Encrypted → Plain Text)
   ──────────────────────────────────────
   
   Database has:                 You get:
   ┌──────────────┐              ┌──────────────┐
   │  Encrypted   │  *_plain     │ Plain Text   │
   │              │ ──────────→  │              │
   │ Email:       │  (auto)      │ Email:       │
   │ gAAAAABh...  │              │ user@ex.com  │
   └──────────────┘              └──────────────┘
```

---

## 🎯 Quick Answers

### Q1: How to Check if Encryption Works?

**Run the test script:**
```bash
cd grc_backend
python test_encryption.py
```

This will show you:
- ✅ Data being encrypted
- ✅ Encrypted values in database
- ✅ Plain text values after decryption

---

### Q2: How Does Data Get Saved?

**It's AUTOMATIC!** You just save normally:

```python
# Step 1: Create user with plain text
user = Users(
    Email="user@example.com",      # ← You write plain text
    PhoneNumber="+1234567890",      # ← You write plain text
    Address="123 Main St"           # ← You write plain text
)

# Step 2: Save (encryption happens automatically)
user.save()  # ← Encrypts Email, PhoneNumber, Address automatically!

# Step 3: Done! Database now has encrypted data
```

**What happens in `save()` method:**
1. Checks if data is already encrypted
2. If not encrypted → Encrypts it
3. Saves encrypted data to database
4. You don't need to do anything!

---

### Q3: How to See Original Plain Text Values?

**Use the `*_plain` properties:**

```python
user = Users.objects.get(UserId=1)

# ✅ CORRECT - Shows plain text
print(user.email_plain)    # "user@example.com" ✅
print(user.phone_plain)    # "+1234567890" ✅
print(user.address_plain)  # "123 Main St" ✅

# ❌ WRONG - Shows encrypted data
print(user.Email)          # "gAAAAABh..." ❌ (encrypted)
print(user.PhoneNumber)    # "gAAAAABh..." ❌ (encrypted)
print(user.Address)        # "gAAAAABh..." ❌ (encrypted)
```

---

## 📝 Complete Example

```python
from grc.models import Users
from django.contrib.auth.hashers import make_password

# ──────────────────────────────────────────────────────────
# CREATE USER (Plain Text → Encrypted)
# ──────────────────────────────────────────────────────────
print("1. Creating user...")
user = Users(
    UserName="john",
    Password=make_password("Pass123"),
    Email="john@example.com",        # Plain text
    PhoneNumber="+1234567890",        # Plain text
    Address="123 Main St"              # Plain text
)
user.save()  # ← Encrypts automatically

print(f"   User ID: {user.UserId}")
print(f"   Email in DB: {user.Email[:50]}...")  # Encrypted


# ──────────────────────────────────────────────────────────
# READ PLAIN TEXT (Encrypted → Plain Text)
# ──────────────────────────────────────────────────────────
print("\n2. Getting plain text values...")
print(f"   Email: {user.email_plain}")        # "john@example.com" ✅
print(f"   Phone: {user.phone_plain}")        # "+1234567890" ✅
print(f"   Address: {user.address_plain}")    # "123 Main St" ✅


# ──────────────────────────────────────────────────────────
# UPDATE USER (Plain Text → Encrypted)
# ──────────────────────────────────────────────────────────
print("\n3. Updating email...")
user.Email = "john.new@example.com"  # Plain text
user.save()  # ← Encrypts automatically
print(f"   New email (plain): {user.email_plain}")  # "john.new@example.com" ✅
```

---

## 🧪 Testing Checklist

Run these to verify everything works:

### Test 1: Create and Check
```python
from grc.models import Users
from grc.utils.data_encryption import is_encrypted_data

user = Users.objects.get(UserId=1)  # Get any user

# Check encryption
print("Email encrypted?", is_encrypted_data(user.Email))
print("Phone encrypted?", is_encrypted_data(user.PhoneNumber))

# Get plain text
print("Email:", user.email_plain)
print("Phone:", user.phone_plain)
```

### Test 2: Create New User
```python
from grc.models import Users
from django.contrib.auth.hashers import make_password

user = Users(
    UserName="test",
    Password=make_password("pass"),
    Email="test@example.com",
    PhoneNumber="+1234567890",
    DepartmentId="1"
)
user.save()

# Verify encryption
from grc.utils.data_encryption import is_encrypted_data
assert is_encrypted_data(user.Email)  # Should be True
assert user.email_plain == "test@example.com"  # Should match

print("✅ Test passed!")
user.delete()  # Cleanup
```

---

## 🔑 Key Points to Remember

1. **Saving**: Use plain text → Encryption is automatic ✅
2. **Reading**: Use `*_plain` properties → Decryption is automatic ✅
3. **Searching**: Use `find_by_email()` → Handles encryption ✅
4. **Testing**: Run `python test_encryption.py` ✅

---

## 📚 Files Created

- `test_encryption.py` - Test script to verify encryption
- `HOW_TO_CHECK_AND_USE_ENCRYPTION.md` - Detailed guide
- `ENCRYPTION_QUICK_START.md` - This quick start guide

---

## 🚨 Common Mistakes to Avoid

❌ **Don't do this:**
```python
print(user.Email)  # Shows encrypted data
```

✅ **Do this instead:**
```python
print(user.email_plain)  # Shows plain text
```

---

**Need more help?** Check `HOW_TO_CHECK_AND_USE_ENCRYPTION.md` for detailed examples!

