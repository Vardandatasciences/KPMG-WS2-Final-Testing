"""
Debug script to check password hash in database
Run this to verify the password for UserId 11
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import Users
from django.contrib.auth.hashers import check_password, make_password

# Get user
user_id = 11
user = Users.objects.get(UserId=user_id)

print(f"\n{'='*70}")
print(f"PASSWORD DEBUG FOR USER {user_id}")
print(f"{'='*70}")
print(f"UserId: {user.UserId}")
print(f"UserName (encrypted): {user.UserName[:50]}...")
print(f"Email: {user.Email[:50] if user.Email else 'None'}...")
print(f"\nPassword field value:")
print(f"  First 100 chars: {user.Password[:100]}")
print(f"  Length: {len(user.Password)} characters")
print(f"  Starts with 'pbkdf2_': {user.Password.startswith('pbkdf2_')}")
print(f"  Starts with 'gAAAAA' (encrypted): {user.Password.startswith('gAAAAA')}")

# Test password verification
test_password = input(f"\nEnter password to test (or press Enter to skip): ").strip()
if test_password:
    result = check_password(test_password, user.Password)
    print(f"\n✅ Password check result: {result}")
    if result:
        print(f"✅ Password '{test_password}' matches the hash!")
    else:
        print(f"❌ Password '{test_password}' does NOT match the hash")
        
    # Show what the hash should look like
    correct_hash = make_password(test_password)
    print(f"\nExpected hash format: {correct_hash[:80]}...")
    print(f"Actual hash in DB:    {user.Password[:80]}...")

print(f"\n{'='*70}\n")
