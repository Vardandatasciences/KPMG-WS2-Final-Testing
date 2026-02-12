#!/usr/bin/env python
"""
WhatsApp Access Token Update Script

This script helps you update the WhatsApp access token in the sys_params table
when your token expires or needs to be refreshed.

Usage:
    python update_whatsapp_token.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection
import getpass


def get_existing_configs():
    """Get all existing WhatsApp configurations from sys_params"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Product_Name, Access_Token, Phone_Number_ID, Phone_Number
                FROM sys_params 
                WHERE Access_Token IS NOT NULL AND Access_Token != ''
                ORDER BY Product_Name
            """)
            results = cursor.fetchall()
            return results
    except Exception as e:
        print(f"❌ Error fetching existing configs: {str(e)}")
        return []


def update_token(access_token, phone_number_id=None, product_name=None):
    """Update access token in sys_params table"""
    try:
        with connection.cursor() as cursor:
            if product_name:
                # Update by Product_Name
                if phone_number_id:
                    cursor.execute("""
                        UPDATE sys_params 
                        SET Access_Token = %s, Phone_Number_ID = %s
                        WHERE Product_Name = %s
                    """, [access_token, phone_number_id, product_name])
                else:
                    cursor.execute("""
                        UPDATE sys_params 
                        SET Access_Token = %s
                        WHERE Product_Name = %s
                    """, [access_token, product_name])
            else:
                # Update first available config
                if phone_number_id:
                    cursor.execute("""
                        UPDATE sys_params 
                        SET Access_Token = %s, Phone_Number_ID = %s
                        WHERE Access_Token IS NOT NULL AND Access_Token != ''
                        LIMIT 1
                    """, [access_token, phone_number_id])
                else:
                    cursor.execute("""
                        UPDATE sys_params 
                        SET Access_Token = %s
                        WHERE Access_Token IS NOT NULL AND Access_Token != ''
                        LIMIT 1
                    """, [access_token])
            
            connection.commit()
            return True
    except Exception as e:
        print(f"❌ Error updating token: {str(e)}")
        connection.rollback()
        return False


def verify_token(access_token):
    """Basic validation of token format"""
    if not access_token:
        return False, "Token cannot be empty"
    
    if len(access_token) < 50:
        return False, "Token seems too short (should be 200+ characters)"
    
    if not access_token.startswith('EAA'):
        return False, "Warning: Token doesn't start with 'EAA' - verify it's correct"
    
    return True, "Token format looks valid"


def main():
    print("=" * 60)
    print("WhatsApp Access Token Update Script")
    print("=" * 60)
    print()
    
    # Show existing configurations
    existing_configs = get_existing_configs()
    if existing_configs:
        print("📋 Existing WhatsApp Configurations:")
        print("-" * 60)
        for i, (product_name, token, phone_id, phone_num) in enumerate(existing_configs, 1):
            token_preview = f"{token[:10]}...{token[-10:]}" if token and len(token) > 20 else "N/A"
            print(f"{i}. Product: {product_name or 'N/A'}")
            print(f"   Token: {token_preview} (length: {len(token) if token else 0})")
            print(f"   Phone Number ID: {phone_id or 'N/A'}")
            print(f"   Phone Number: {phone_num or 'N/A'}")
            print()
    else:
        print("⚠️  No existing WhatsApp configurations found in sys_params")
        print()
    
    # Get new token
    print("📝 Enter New Access Token")
    print("-" * 60)
    print("You can get this from: https://developers.facebook.com/apps/")
    print("Go to: WhatsApp > API Setup > Access tokens")
    print()
    new_token = getpass.getpass("New Access Token: ").strip()
    
    if not new_token:
        print("❌ Token cannot be empty. Exiting.")
        return
    
    # Validate token format
    is_valid, message = verify_token(new_token)
    if not is_valid:
        print(f"⚠️  {message}")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("❌ Aborted.")
            return
    
    # Get product name (optional)
    product_name = None
    if existing_configs and len(existing_configs) > 1:
        print()
        print("📦 Multiple configurations found. Which one to update?")
        print("   (Press Enter to update the first one)")
        product_input = input("Product Name (optional): ").strip()
        if product_input:
            product_name = product_input
    
    # Get phone number ID (optional)
    print()
    phone_number_id = input("Phone Number ID (optional, press Enter to skip): ").strip()
    if not phone_number_id:
        phone_number_id = None
    
    # Confirm update
    print()
    print("=" * 60)
    print("📋 Update Summary:")
    print(f"   Product Name: {product_name or 'First available config'}")
    print(f"   Token: {new_token[:10]}...{new_token[-10:]} (length: {len(new_token)})")
    if phone_number_id:
        print(f"   Phone Number ID: {phone_number_id}")
    print("=" * 60)
    print()
    
    confirm = input("⚠️  Confirm update? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Update cancelled.")
        return
    
    # Update token
    print()
    print("🔄 Updating token in database...")
    success = update_token(new_token, phone_number_id, product_name)
    
    if success:
        print("✅ Token updated successfully!")
        print()
        print("📝 Next steps:")
        print("   1. Restart your Django application (if needed)")
        print("   2. Test sending a WhatsApp message/OTP")
        print("   3. Check logs to verify it's working")
    else:
        print("❌ Failed to update token. Check the error message above.")
        print()
        print("💡 You can also update manually using SQL:")
        if product_name:
            print(f"   UPDATE sys_params SET Access_Token = '{new_token[:20]}...' WHERE Product_Name = '{product_name}';")
        else:
            print(f"   UPDATE sys_params SET Access_Token = '{new_token[:20]}...' WHERE Access_Token IS NOT NULL LIMIT 1;")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
