"""
Standalone script to generate session tokens for Postman testing.

Usage:
    python generate_session_token.py

This script authenticates a user and generates JWT tokens (access token, refresh token, and session token)
that can be used for API testing in Postman.

cTOKEN EXPIRY:
    - Access Token: 3 days
    - Refresh Token: 7 days
    (Configured in grc/authentication.py)

CONFIGURATION:
    Edit the variables below to set your username and password.
"""

import os
import sys
import django

# ============================================================================
# CONFIGURATION - Edit these variables with your credentials
# ============================================================================
USERNAME = "priya.gupta"  # Enter your username or email
PASSWORD = "Priya@123"   # Enter your password
LOGIN_TYPE = "username"           # Use "username" or "userid"
# ============================================================================

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.hashers import check_password, make_password
from grc.models import Users
from grc.authentication import generate_jwt_tokens


def authenticate_user(username, password, login_type='username'):
    """
    Authenticate a user with username/email and password.
    
    Args:
        username: Username or user ID
        password: Plain text password
        login_type: 'username' or 'userid'
    
    Returns:
        User object if authenticated, None otherwise
    """
    try:
        if login_type == 'userid':
            # Login with User ID
            user_id = int(username)
            user = Users.objects.get(UserId=user_id)
        else:
            # Login with Username (handles encrypted usernames)
            user = Users.find_by_username(username)
            if not user:
                return None
        
        # Check hashed password
        if check_password(password, user.Password):
            return user
        # Backward compatibility: check plain text password
        elif user.Password == password:
            # Migrate to hashed password
            user.Password = make_password(password)
            user.save(update_fields=['Password'])
            print(f"⚠️  Password for user {user.UserName} was stored in plain text and has been hashed.")
            return user
        else:
            return None
            
    except (Users.DoesNotExist, ValueError) as e:
        return None
    except Exception as e:
        print(f"❌ Error during authentication: {str(e)}")
        return None


def generate_tokens_for_user(username, password, login_type='username'):
    """
    Generate JWT tokens for a user after authentication.
    
    Args:
        username: Username or user ID
        password: Plain text password
        login_type: 'username' or 'userid'
    
    Returns:
        Dictionary with tokens or None if authentication fails
    """
    print("=" * 70)
    print("🔐 GRC Session Token Generator for Postman Testing")
    print("=" * 70)
    print()
    
    # Authenticate user
    print(f"🔍 Authenticating user: {username} (type: {login_type})...")
    user = authenticate_user(username, password, login_type)
    
    if not user:
        print("❌ Authentication failed: Invalid username or password")
        return None
    
    print(f"✅ User authenticated successfully!")
    print(f"   User ID: {user.UserId}")
    print(f"   Username: {user.UserName}")
    print(f"   Email: {getattr(user, 'Email', 'N/A')}")
    print()
    
    # Check if user is active
    is_active = user.IsActive
    if isinstance(is_active, str):
        is_active = is_active.upper() == 'Y'
    
    if not is_active:
        print("⚠️  Warning: User is not active (IsActive != 'Y')")
        print("   The token will still be generated, but login may be restricted.")
        print()
    
    # Generate JWT tokens
    print("🔑 Generating JWT tokens...")
    try:
        tokens = generate_jwt_tokens(user)
        print("✅ Tokens generated successfully!")
        print()
        
        return {
            'user': user,
            'tokens': tokens
        }
    except Exception as e:
        print(f"❌ Error generating tokens: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def print_tokens_for_postman(tokens_data):
    """
    Print tokens in a format suitable for Postman.
    
    Args:
        tokens_data: Dictionary with 'user' and 'tokens' keys
    """
    if not tokens_data:
        return
    
    user = tokens_data['user']
    tokens = tokens_data['tokens']
    
    print("=" * 70)
    print("📋 TOKENS FOR POSTMAN")
    print("=" * 70)
    print()
    
    print("1️⃣  ACCESS TOKEN (Use in Authorization Header):")
    print("-" * 70)
    print(f"   Authorization: Bearer {tokens['access']}")
    print()
    
    print("2️⃣  REFRESH TOKEN (Use for token refresh):")
    print("-" * 70)
    print(f"   {tokens['refresh']}")
    print()
    
    print("3️⃣  SESSION TOKEN (UUID):")
    print("-" * 70)
    print(f"   {tokens['session_token']}")
    print()
    
    print("4️⃣  TOKEN EXPIRY:")
    print("-" * 70)
    print(f"   Access Token Expires: {tokens['access_token_expires']}")
    print(f"   Refresh Token Expires: {tokens['refresh_token_expires']}")
    print()
    
    print("=" * 70)
    print("📝 POSTMAN SETUP INSTRUCTIONS")
    print("=" * 70)
    print()
    print("1. Open Postman")
    print("2. Go to your request")
    print("3. Click on the 'Authorization' tab")
    print("4. Select 'Bearer Token' as the Type")
    print(f"5. Paste this token in the Token field:")
    print()
    print(f"   {tokens['access']}")
    print()
    print("6. Or use this in the Headers tab:")
    print(f"   Key: Authorization")
    print(f"   Value: Bearer {tokens['access']}")
    print()
    print("=" * 70)
    print("✅ Ready for testing!")
    print("=" * 70)


def main():
    """Main function to generate tokens using configured credentials."""
    # Get credentials from configuration variables
    username = USERNAME
    password = PASSWORD
    login_type = LOGIN_TYPE
    
    # Validate configuration
    if username == "your_username_here" or not username:
        print("=" * 70)
        print("❌ ERROR: Username not configured")
        print("=" * 70)
        print("Please edit the USERNAME variable at the top of this script.")
        sys.exit(1)
    
    if password == "your_password_here" or not password:
        print("=" * 70)
        print("❌ ERROR: Password not configured")
        print("=" * 70)
        print("Please edit the PASSWORD variable at the top of this script.")
        sys.exit(1)
    
    # Generate tokens
    tokens_data = generate_tokens_for_user(username, password, login_type)
    
    if tokens_data:
        print_tokens_for_postman(tokens_data)
    else:
        print()
        print("=" * 70)
        print("❌ Failed to generate tokens")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
