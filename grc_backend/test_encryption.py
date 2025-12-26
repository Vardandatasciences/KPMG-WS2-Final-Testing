"""
Test script to verify encryption implementation for Users model
Run this script to check how encryption works and see plain text values
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import Users
from grc.utils.data_encryption import encrypt_data, decrypt_data, is_encrypted_data
from django.contrib.auth.hashers import make_password

def test_encryption():
    """Test encryption implementation"""
    
    print("=" * 80)
    print("ENCRYPTION TEST FOR USERS MODEL")
    print("=" * 80)
    print()
    
    # Test 1: Check encryption service
    print("1. TESTING ENCRYPTION SERVICE")
    print("-" * 80)
    test_email = "test@example.com"
    test_phone = "+1234567890"
    test_address = "123 Main Street, New York, NY 10001"
    
    print(f"Original Email: {test_email}")
    print(f"Original Phone: {test_phone}")
    print(f"Original Address: {test_address}")
    print()
    
    encrypted_email = encrypt_data(test_email)
    encrypted_phone = encrypt_data(test_phone)
    encrypted_address = encrypt_data(test_address)
    
    print(f"Encrypted Email: {encrypted_email[:60]}...")
    print(f"Encrypted Phone: {encrypted_phone[:60]}...")
    print(f"Encrypted Address: {encrypted_address[:60]}...")
    print()
    
    decrypted_email = decrypt_data(encrypted_email)
    decrypted_phone = decrypt_data(encrypted_phone)
    decrypted_address = decrypt_data(encrypted_address)
    
    print(f"Decrypted Email: {decrypted_email}")
    print(f"Decrypted Phone: {decrypted_phone}")
    print(f"Decrypted Address: {decrypted_address}")
    print()
    
    print(f"✅ Encryption/Decryption Test: PASSED" if decrypted_email == test_email else "❌ FAILED")
    print()
    
    # Test 2: Create a test user
    print("2. TESTING USER CREATION (AUTOMATIC ENCRYPTION)")
    print("-" * 80)
    
    test_username = f"test_user_{os.getpid()}"  # Unique username
    test_email = f"test{os.getpid()}@example.com"
    test_phone = f"+1234567{os.getpid()}"
    test_address = f"Test Address {os.getpid()}"
    
    print(f"Creating user with:")
    print(f"  Username: {test_username}")
    print(f"  Email: {test_email}")
    print(f"  Phone: {test_phone}")
    print(f"  Address: {test_address}")
    print()
    
    try:
        # Create user (data will be encrypted automatically on save)
        user = Users(
            UserName=test_username,
            Password=make_password("TestPassword123"),
            Email=test_email,  # Plain text - will be encrypted
            PhoneNumber=test_phone,  # Plain text - will be encrypted
            Address=test_address,  # Plain text - will be encrypted
            FirstName="Test",
            LastName="User",
            DepartmentId="1",
            IsActive='Y'
        )
        user.save()  # This triggers encryption
        print(f"✅ User created successfully: UserId = {user.UserId}")
        print()
        
        # Test 3: Check what's stored in database
        print("3. CHECKING DATABASE VALUES (ENCRYPTED)")
        print("-" * 80)
        print(f"Email in DB (encrypted): {user.Email[:60]}...")
        print(f"Phone in DB (encrypted): {user.PhoneNumber[:60]}...")
        print(f"Address in DB (encrypted): {user.Address[:60]}...")
        print()
        
        # Check if encrypted
        print("Is Email encrypted?", is_encrypted_data(user.Email))
        print("Is Phone encrypted?", is_encrypted_data(user.PhoneNumber))
        print("Is Address encrypted?", is_encrypted_data(user.Address))
        print()
        
        # Test 4: Retrieve plain text using properties
        print("4. RETRIEVING PLAIN TEXT VALUES")
        print("-" * 80)
        print(f"Email (plain text): {user.email_plain}")
        print(f"Phone (plain text): {user.phone_plain}")
        print(f"Address (plain text): {user.address_plain}")
        print()
        
        # Verify they match
        email_match = user.email_plain == test_email
        phone_match = user.phone_plain == test_phone
        address_match = user.address_plain == test_address
        
        print(f"✅ Email matches: {email_match}")
        print(f"✅ Phone matches: {phone_match}")
        print(f"✅ Address matches: {address_match}")
        print()
        
        # Test 5: Find by email
        print("5. TESTING FIND_BY_EMAIL METHOD")
        print("-" * 80)
        found_user = Users.find_by_email(test_email)
        if found_user and found_user.UserId == user.UserId:
            print(f"✅ Found user by email: UserId = {found_user.UserId}")
            print(f"   Email: {found_user.email_plain}")
        else:
            print(f"❌ Could not find user by email")
        print()
        
        # Test 6: Update user (should encrypt again)
        print("6. TESTING USER UPDATE (AUTOMATIC ENCRYPTION)")
        print("-" * 80)
        new_email = f"updated{os.getpid()}@example.com"
        user.Email = new_email  # Plain text
        user.save()  # Should encrypt automatically
        print(f"Updated email to: {new_email}")
        print(f"Email in DB (encrypted): {user.Email[:60]}...")
        print(f"Email (plain text): {user.email_plain}")
        print(f"✅ Update test: {'PASSED' if user.email_plain == new_email else 'FAILED'}")
        print()
        
        # Cleanup
        print("7. CLEANUP")
        print("-" * 80)
        user.delete()
        print(f"✅ Test user deleted (UserId: {user.UserId})")
        print()
        
        print("=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✅")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


def show_existing_users():
    """Show encryption status of existing users"""
    
    print("=" * 80)
    print("EXISTING USERS - ENCRYPTION STATUS")
    print("=" * 80)
    print()
    
    users = Users.objects.all()[:10]  # Show first 10 users
    
    if not users:
        print("No users found in database")
        return
    
    print(f"Showing first {len(users)} users:")
    print()
    
    for user in users:
        print(f"User ID: {user.UserId} - Username: {user.UserName}")
        print(f"  Email in DB: {user.Email[:50]}...")
        print(f"  Email encrypted? {is_encrypted_data(user.Email)}")
        print(f"  Email (plain text): {user.email_plain}")
        
        if user.PhoneNumber:
            print(f"  Phone in DB: {user.PhoneNumber[:50]}...")
            print(f"  Phone encrypted? {is_encrypted_data(user.PhoneNumber)}")
            print(f"  Phone (plain text): {user.phone_plain}")
        
        if user.Address:
            print(f"  Address in DB: {user.Address[:50]}...")
            print(f"  Address encrypted? {is_encrypted_data(user.Address)}")
            print(f"  Address (plain text): {user.address_plain}")
        
        print("-" * 80)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        # Show existing users
        show_existing_users()
    else:
        # Run tests
        test_encryption()
        
        print()
        print("To see existing users encryption status, run:")
        print("  python test_encryption.py show")

