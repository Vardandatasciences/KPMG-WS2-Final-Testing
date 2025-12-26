# Data Encryption Implementation Guide

## How to See Plain Text Later: Encryption vs Hashing

### Key Concept

**Hashing (One-Way):**
- ❌ **CANNOT** retrieve plain text later
- Used for: Passwords, OTPs
- Example: `hash("password123")` → `"$pbkdf2$..."` (can't reverse this)

**Encryption (Two-Way):**
- ✅ **CAN** retrieve plain text later
- Used for: Email, Phone, Address (data you need to read later)
- Example: `encrypt("user@example.com")` → `"gAAAAABh..."` → `decrypt()` → `"user@example.com"`

---

## Implementation Example

### Step 1: Add Encryption to Your Models

Here's how to encrypt sensitive fields in your `Users` model:

```python
# grc/models.py
from django.db import models
from grc.utils.data_encryption import encrypt_data, decrypt_data

class Users(models.Model):
    UserId = models.AutoField(primary_key=True)
    UserName = models.CharField(max_length=255)
    Password = models.CharField(max_length=255)  # Already hashed (one-way)
    
    # These fields will be encrypted (two-way)
    Email = models.CharField(max_length=255)  # Changed from EmailField to store encrypted
    PhoneNumber = models.CharField(max_length=255, null=True, blank=True)
    Address = models.TextField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        """Override save to encrypt sensitive fields before storing"""
        # Encrypt sensitive fields if they're not already encrypted
        if self.Email and not self._is_encrypted(self.Email):
            self.Email = encrypt_data(self.Email)
        if self.PhoneNumber and not self._is_encrypted(self.PhoneNumber):
            self.PhoneNumber = encrypt_data(self.PhoneNumber)
        if self.Address and not self._is_encrypted(self.Address):
            self.Address = encrypt_data(self.Address)
        
        super().save(*args, **kwargs)
    
    def _is_encrypted(self, text):
        """Check if text is already encrypted"""
        from grc.utils.data_encryption import is_encrypted_data
        return is_encrypted_data(text) if text else False
    
    @property
    def email_plain(self):
        """Get plain text email (decrypted)"""
        return decrypt_data(self.Email)
    
    @property
    def phone_plain(self):
        """Get plain text phone number (decrypted)"""
        return decrypt_data(self.PhoneNumber)
    
    @property
    def address_plain(self):
        """Get plain text address (decrypted)"""
        return decrypt_data(self.Address)
```

### Step 2: Use in Your Code

```python
# When creating/updating a user
user = Users.objects.get(UserId=1)

# Save (automatically encrypts)
user.Email = "user@example.com"  # Plain text
user.PhoneNumber = "+1234567890"  # Plain text
user.save()  # Automatically encrypted before saving

# Retrieve plain text later
print(user.email_plain)  # Output: "user@example.com"
print(user.phone_plain)  # Output: "+1234567890"

# Or decrypt manually
from grc.utils.data_encryption import decrypt_data
plain_email = decrypt_data(user.Email)
print(plain_email)  # Output: "user@example.com"
```

### Step 3: In API Views

```python
# grc/views.py or your API view
from grc.utils.data_encryption import decrypt_data, encrypt_data

@api_view(['GET'])
def get_user_profile(request, user_id):
    user = Users.objects.get(UserId=user_id)
    
    # Return decrypted data to the frontend
    return Response({
        'userId': user.UserId,
        'userName': user.UserName,
        'email': decrypt_data(user.Email),  # Decrypt to show plain text
        'phoneNumber': decrypt_data(user.PhoneNumber),  # Decrypt to show plain text
        'address': decrypt_data(user.Address),  # Decrypt to show plain text
    })

@api_view(['POST'])
def update_user_profile(request, user_id):
    user = Users.objects.get(UserId=user_id)
    
    # Encrypt before saving (or let model's save() method handle it)
    if 'email' in request.data:
        user.Email = encrypt_data(request.data['email'])
    if 'phoneNumber' in request.data:
        user.PhoneNumber = encrypt_data(request.data['phoneNumber'])
    
    user.save()
    return Response({'success': True})
```

---

## Configuration

### 1. Set Encryption Key

Add to your `.env` file:

```bash
# Generate a key using Python:
# from cryptography.fernet import Fernet
# print(Fernet.generate_key().decode())

GRC_ENCRYPTION_KEY=your-base64-encoded-fernet-key-here
```

Or add to `backend/settings.py`:

```python
# backend/settings.py
GRC_ENCRYPTION_KEY = os.environ.get('GRC_ENCRYPTION_KEY', '')
```

### 2. Generate an Encryption Key

Run this Python code to generate a key:

```python
from cryptography.fernet import Fernet

# Generate a new encryption key
key = Fernet.generate_key()
print("Your encryption key:")
print(key.decode())
print("\nAdd this to your .env file as:")
print(f"GRC_ENCRYPTION_KEY={key.decode()}")
```

**IMPORTANT:** Save this key securely! If you lose it, you cannot decrypt your data.

---

## Complete Example: Encrypted User Model

```python
# grc/models.py
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from grc.utils.data_encryption import encrypt_data, decrypt_data, is_encrypted_data

class Users(models.Model):
    UserId = models.AutoField(primary_key=True)
    UserName = models.CharField(max_length=255)
    Password = models.CharField(max_length=255)  # Hashed (one-way, can't reverse)
    Email = models.CharField(max_length=255)  # Encrypted (two-way, can decrypt)
    PhoneNumber = models.CharField(max_length=255, null=True, blank=True)  # Encrypted
    Address = models.TextField(null=True, blank=True)  # Encrypted
    FirstName = models.CharField(max_length=255)
    LastName = models.CharField(max_length=255)
    
    def save(self, *args, **kwargs):
        """Encrypt sensitive fields before saving"""
        # Encrypt email
        if self.Email and not is_encrypted_data(self.Email):
            self.Email = encrypt_data(self.Email)
        
        # Encrypt phone
        if self.PhoneNumber and not is_encrypted_data(self.PhoneNumber):
            self.PhoneNumber = encrypt_data(self.PhoneNumber)
        
        # Encrypt address
        if self.Address and not is_encrypted_data(self.Address):
            self.Address = encrypt_data(self.Address)
        
        # Hash password (one-way, different from encryption)
        if hasattr(self, '_password') and self._password:
            self.Password = make_password(self._password)
        
        super().save(*args, **kwargs)
    
    # Properties to access decrypted data
    @property
    def email_plain(self):
        """Get decrypted email"""
        return decrypt_data(self.Email) if self.Email else None
    
    @property
    def phone_plain(self):
        """Get decrypted phone number"""
        return decrypt_data(self.PhoneNumber) if self.PhoneNumber else None
    
    @property
    def address_plain(self):
        """Get decrypted address"""
        return decrypt_data(self.Address) if self.Address else None
    
    def set_password(self, plain_password):
        """Set password (hashed, not encrypted)"""
        self.Password = make_password(plain_password)
    
    def check_password(self, plain_password):
        """Verify password"""
        return check_password(plain_password, self.Password)
```

---

## Usage Examples

### Example 1: Create User with Encrypted Data

```python
# Create new user
user = Users(
    UserName="john_doe",
    Email="john@example.com",  # Will be encrypted on save
    PhoneNumber="+1234567890",  # Will be encrypted on save
    Address="123 Main St, City",  # Will be encrypted on save
    FirstName="John",
    LastName="Doe"
)
user.set_password("SecurePassword123")  # Will be hashed
user.save()

# Database now contains:
# Email: "gAAAAABh..." (encrypted)
# PhoneNumber: "gAAAAABh..." (encrypted)
# Address: "gAAAAABh..." (encrypted)
# Password: "$pbkdf2$..." (hashed)
```

### Example 2: Retrieve and Display Plain Text

```python
# Get user from database
user = Users.objects.get(UserId=1)

# Access encrypted fields (still encrypted in database)
print(user.Email)  # Output: "gAAAAABh..." (encrypted)

# Access plain text using properties
print(user.email_plain)  # Output: "john@example.com" (decrypted!)
print(user.phone_plain)  # Output: "+1234567890" (decrypted!)
print(user.address_plain)  # Output: "123 Main St, City" (decrypted!)

# Or decrypt manually
from grc.utils.data_encryption import decrypt_data
email = decrypt_data(user.Email)
print(email)  # Output: "john@example.com"
```

### Example 3: Search/Filter by Encrypted Fields

```python
# Searching encrypted fields requires special handling
# Option 1: Decrypt all and filter in Python (not efficient for large datasets)
users = Users.objects.all()
matching_users = [u for u in users if decrypt_data(u.Email) == "john@example.com"]

# Option 2: Store a hash for search (recommended)
# Add an EmailHash field that stores SHA256 hash of email for searching
from hashlib import sha256

def search_user_by_email(email):
    email_hash = sha256(email.encode()).hexdigest()
    return Users.objects.filter(EmailHash=email_hash)
```

---

## Migration Strategy

### Migrating Existing Plain Text Data

If you have existing plain text data, you can migrate it:

```python
# Migration script: migrate_encrypt_users.py
from grc.models import Users
from grc.utils.data_encryption import encrypt_data, is_encrypted_data

def migrate_encrypt_user_data():
    """Encrypt all existing plain text user data"""
    users = Users.objects.all()
    
    for user in users:
        updated = False
        
        # Encrypt email if not already encrypted
        if user.Email and not is_encrypted_data(user.Email):
            user.Email = encrypt_data(user.Email)
            updated = True
        
        # Encrypt phone if not already encrypted
        if user.PhoneNumber and not is_encrypted_data(user.PhoneNumber):
            user.PhoneNumber = encrypt_data(user.PhoneNumber)
            updated = True
        
        # Encrypt address if not already encrypted
        if user.Address and not is_encrypted_data(user.Address):
            user.Address = encrypt_data(user.Address)
            updated = True
        
        if updated:
            user.save()
            print(f"Encrypted data for user {user.UserId}")
    
    print("Migration complete!")

# Run this script once to encrypt existing data
if __name__ == "__main__":
    migrate_encrypt_user_data()
```

---

## Key Management

### Production Best Practices

1. **Store Key Securely:**
   - Use environment variables (not in code)
   - Use a secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)
   - Never commit keys to version control

2. **Key Rotation:**
   - Plan for key rotation (requires re-encrypting all data)
   - Keep old keys for decrypting old data during transition

3. **Backup Keys:**
   - Backup encryption keys securely
   - If key is lost, encrypted data cannot be recovered

---

## Summary

| Operation | Hash (Passwords) | Encrypt (Email/Phone) |
|-----------|------------------|----------------------|
| Store | `make_password("pass")` | `encrypt_data("email")` |
| Retrieve | ❌ Cannot retrieve | ✅ `decrypt_data(email)` |
| Verify | `check_password(input, hash)` | N/A (just decrypt) |
| Reverse | ❌ Impossible | ✅ Possible with key |

**Remember:**
- **Passwords** = Hash (one-way, can't see plain text)
- **Email/Phone/Address** = Encrypt (two-way, can see plain text later)

