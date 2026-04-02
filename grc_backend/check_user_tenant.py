"""
Script to check if a user has a tenant assigned and decode their JWT token
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import Users, Tenant
import jwt
from django.conf import settings

def check_user_tenant(username):
    """Check if user has tenant assigned"""
    try:
        user = Users.find_by_username(username)
        if not user:
            print(f"❌ User '{username}' not found")
            return
        
        print("=" * 70)
        print(f"USER: {username}")
        print("=" * 70)
        print(f"User ID: {user.UserId}")
        print(f"Username: {user.UserName}")
        print(f"Email: {getattr(user, 'Email', 'N/A')}")
        print()
        
        if user.tenant:
            print("[OK] TENANT ASSIGNED:")
            print(f"   Tenant ID: {user.tenant.tenant_id}")
            print(f"   Tenant Name: {user.tenant.name}")
            print(f"   Tenant Status: {user.tenant.status}")
        else:
            print("[ERROR] NO TENANT ASSIGNED")
            print("   This user needs a tenant assigned!")
        print()
        
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()


def decode_token(token_string):
    """Decode JWT token to check if it contains tenant_id"""
    try:
        print("=" * 70)
        print("DECODING YOUR CURRENT TOKEN")
        print("=" * 70)
        
        verification_key = getattr(settings, 'JWT_VERIFYING_KEY', None) or getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
        payload = jwt.decode(
            token_string,
            verification_key,
            algorithms=getattr(settings, 'JWT_ALLOWED_ALGORITHMS', [getattr(settings, 'JWT_ALGORITHM', 'RS256')]),
            issuer=getattr(settings, 'JWT_ISSUER', None),
            audience=getattr(settings, 'JWT_AUDIENCE', None),
        )
        
        print("Token Payload:")
        for key, value in payload.items():
            print(f"  {key}: {value}")
        print()
        
        if 'tenant_id' in payload and payload['tenant_id']:
            print(f"[OK] Token contains tenant_id: {payload['tenant_id']}")
        else:
            print("[ERROR] Token DOES NOT contain tenant_id!")
            print("   You need to REGENERATE your token!")
        print()
        
    except jwt.ExpiredSignatureError:
        print("[ERROR] Token has expired")
    except Exception as e:
        print(f"[ERROR] Error decoding token: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check the user priya.gupta
    username = "priya.gupta"
    check_user_tenant(username)
    
    print("=" * 70)
    print("TO CHECK YOUR CURRENT TOKEN:")
    print("=" * 70)
    print("Paste your current JWT token below and uncomment the line:")
    print()
    print('# YOUR_TOKEN = "paste_your_token_here"')
    print('# decode_token(YOUR_TOKEN)')
    print()
    print("=" * 70)
    print("TO FIX THE ISSUE:")
    print("=" * 70)
    print("1. Run: python generate_session_token.py")
    print("2. Copy the NEW access token")
    print("3. Update your Postman Authorization header with the NEW token")
    print("=" * 70)
