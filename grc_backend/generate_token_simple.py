"""
Simple token generator without emojis for Windows compatibility.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.hashers import check_password, make_password
from grc.models import Users
from grc.authentication import generate_jwt_tokens

# Configuration
USERNAME = "radha.sharma"
PASSWORD = "Priya@123"
LOGIN_TYPE = "username"

def authenticate_user(username, password, login_type='username'):
    """Authenticate a user with username/email and password."""
    try:
        if login_type == 'userid':
            user_id = int(username)
            user = Users.objects.get(UserId=user_id)
        else:
            user = Users.find_by_username(username)
            if not user:
                return None
        
        # Check hashed password
        if check_password(password, user.Password):
            return user
        # Backward compatibility: check plain text password
        elif user.Password == password:
            user.Password = make_password(password)
            user.save(update_fields=['Password'])
            print(f"[WARNING] Password for user {user.UserName} was stored in plain text and has been hashed.")
            return user
        else:
            return None
            
    except (Users.DoesNotExist, ValueError) as e:
        return None
    except Exception as e:
        print(f"[ERROR] Error during authentication: {str(e)}")
        return None


def main():
    """Generate JWT tokens for configured user."""
    print("=" * 70)
    print("GRC Session Token Generator for Postman Testing")
    print("=" * 70)
    print()
    
    # Authenticate user
    print(f"[INFO] Authenticating user: {USERNAME} (type: {LOGIN_TYPE})...")
    user = authenticate_user(USERNAME, PASSWORD, LOGIN_TYPE)
    
    if not user:
        print("[ERROR] Authentication failed: Invalid username or password")
        sys.exit(1)
    
    print(f"[OK] User authenticated successfully!")
    print(f"   User ID: {user.UserId}")
    print(f"   Username: {user.UserName}")
    print(f"   Email: {getattr(user, 'Email', 'N/A')}")
    
    # Display tenant information
    if user.tenant:
        print(f"   Tenant ID: {user.tenant.tenant_id}")
        print(f"   Tenant Name: {user.tenant.name}")
    else:
        print("   [WARNING] No tenant assigned!")
    print()
    
    # Generate JWT tokens
    print("[INFO] Generating JWT tokens...")
    try:
        tokens = generate_jwt_tokens(user)
        print("[OK] Tokens generated successfully!")
        print()
        
        print("=" * 70)
        print("TOKENS FOR POSTMAN")
        print("=" * 70)
        print()
        
        print("1. ACCESS TOKEN (Use in Authorization Header):")
        print("-" * 70)
        print(f"Authorization: Bearer {tokens['access']}")
        print()
        print("COPY THIS TOKEN:")
        print(tokens['access'])
        print()
        
        print("-" * 70)
        print()
        
        print("2. REFRESH TOKEN:")
        print("-" * 70)
        print(tokens['refresh'])
        print()
        
        print("3. SESSION TOKEN (UUID):")
        print("-" * 70)
        print(tokens['session_token'])
        print()
        
        print("4. TOKEN EXPIRY:")
        print("-" * 70)
        print(f"   Access Token Expires: {tokens['access_token_expires']}")
        print(f"   Refresh Token Expires: {tokens['refresh_token_expires']}")
        print()
        
        print("=" * 70)
        print("POSTMAN SETUP INSTRUCTIONS")
        print("=" * 70)
        print()
        print("1. Copy the ACCESS TOKEN above")
        print("2. In Postman, go to your request")
        print("3. Click on the 'Authorization' tab")
        print("4. Select 'Bearer Token' as the Type")
        print("5. Paste the token in the Token field")
        print()
        print("=" * 70)
        print("[OK] Ready for testing!")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] Error generating tokens: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
