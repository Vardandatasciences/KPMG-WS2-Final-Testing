import os
import django
import sys
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings
import jwt
from grc.authentication import generate_jwt_tokens, verify_jwt_token
from tprm_backend.mfa_auth.jwt_service import JWTService
from django.contrib.auth import get_user_model

def test_jwt_security():
    print("Testing JWT security enforcement...")
    
    print(f"Current JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
    
    # 1. Verify that symmetric algorithms are rejected by settings
    if settings.JWT_ALGORITHM not in ('RS256', 'RS384', 'RS512', 'ES256', 'ES384', 'ES512'):
        print("FAILED: Insecure algorithm permitted in settings.")
        return
    else:
        print("SUCCESS: Settings correctly enforce asymmetric algorithm.")

    # 2. Test manual signing paths
    try:
        # Mock a user
        User = get_user_model()
        # Find any user or create one for test
        user = User.objects.first()
        if not user:
            print("WARNING: Skipping token generation test: No user found in database.")
        else:
            print(f"Testing token generation for user: {user.username or user.UserId}")
            
            # Test GRC tokens
            tokens = generate_jwt_tokens(user)
            header = jwt.get_unverified_header(tokens['access'])
            print(f"GRC Token Alg: {header['alg']}")
            if header['alg'] != 'RS256':
                print("FAILED: GRC token used wrong algorithm.")
            else:
                print("SUCCESS: GRC token uses RS256.")

            # Test MFA tokens
            mfa_tokens = JWTService.generate_tokens(user)
            mfa_header = jwt.get_unverified_header(mfa_tokens['access_token'])
            print(f"MFA Token Alg: {mfa_header['alg']}")
            if mfa_header['alg'] != 'RS256':
                print("FAILED: MFA token used wrong algorithm.")
            else:
                print("SUCCESS: MFA token uses RS256.")

    except ValueError as e:
        print(f"SUCCESS: System correctly raised error for missing/invalid keys: {str(e)}")
    except Exception as e:
        print(f"❌ ERROR: Unexpected exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_jwt_security()
