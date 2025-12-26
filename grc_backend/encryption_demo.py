"""
Simple demonstration script showing how encryption/decryption works
Run this to see how you can encrypt data and decrypt it later to see plain text
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.utils.data_encryption import encrypt_data, decrypt_data

def demo_encryption():
    """Demonstrate encryption and decryption"""
    
    print("=" * 60)
    print("ENCRYPTION/DECRYPTION DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Original plain text data
    original_email = "user@example.com"
    original_phone = "+1234567890"
    original_address = "123 Main Street, New York, NY 10001"
    
    print("1. ORIGINAL PLAIN TEXT DATA:")
    print(f"   Email: {original_email}")
    print(f"   Phone: {original_phone}")
    print(f"   Address: {original_address}")
    print()
    
    # Encrypt the data
    print("2. ENCRYPTING DATA...")
    encrypted_email = encrypt_data(original_email)
    encrypted_phone = encrypt_data(original_phone)
    encrypted_address = encrypt_data(original_address)
    
    print("   Encrypted Email:", encrypted_email[:50] + "..." if len(encrypted_email) > 50 else encrypted_email)
    print("   Encrypted Phone:", encrypted_phone[:50] + "..." if len(encrypted_phone) > 50 else encrypted_phone)
    print("   Encrypted Address:", encrypted_address[:50] + "..." if len(encrypted_address) > 50 else encrypted_address)
    print()
    print("   ^ This is what gets stored in the database")
    print()
    
    # Decrypt to retrieve plain text
    print("3. DECRYPTING TO RETRIEVE PLAIN TEXT...")
    decrypted_email = decrypt_data(encrypted_email)
    decrypted_phone = decrypt_data(encrypted_phone)
    decrypted_address = decrypt_data(encrypted_address)
    
    print("   Decrypted Email:", decrypted_email)
    print("   Decrypted Phone:", decrypted_phone)
    print("   Decrypted Address:", decrypted_address)
    print()
    
    # Verify they match
    print("4. VERIFICATION:")
    print(f"   Email matches: {original_email == decrypted_email}")
    print(f"   Phone matches: {original_phone == decrypted_phone}")
    print(f"   Address matches: {original_address == decrypted_address}")
    print()
    
    print("=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print("✅ You CAN encrypt data and decrypt it later")
    print("✅ The plain text is retrievable (this is encryption)")
    print("❌ Hashing is different - you CANNOT reverse hashes")
    print("=" * 60)


if __name__ == "__main__":
    try:
        demo_encryption()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Set up Django environment")
        print("2. Installed cryptography: pip install cryptography")
        print("3. Set GRC_ENCRYPTION_KEY in settings or .env file")

