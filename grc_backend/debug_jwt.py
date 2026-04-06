import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.backends import TokenBackend

print("--- JWT SETTINGS ---")
print(f"JWT_ALGORITHM: {getattr(settings, 'JWT_ALGORITHM', 'N/A')}")
# print(f"JWT_SIGNING_KEY (First 30): {getattr(settings, 'JWT_SIGNING_KEY', '')[:30]}")
# print(f"JWT_VERIFYING_KEY (First 30): {getattr(settings, 'JWT_VERIFYING_KEY', '')[:30]}")

try:
    print("Testing TokenBackend directly...")
    backend = TokenBackend(
        algorithm=settings.SIMPLE_JWT['ALGORITHM'],
        signing_key=settings.SIMPLE_JWT['SIGNING_KEY'],
        verifying_key=settings.SIMPLE_JWT['VERIFYING_KEY'],
    )
    print("SUCCESS: TokenBackend initialized!")
except Exception as e:
    print(f"FAILURE: TokenBackend initialization error: {str(e)}")

try:
    from django.contrib.auth.models import User
    # Create or get a test user (mocked or from DB)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.first()
    if user:
        print(f"Testing RefreshToken for user: {user.UserName}")
        refresh = RefreshToken.for_user(user)
        print("SUCCESS: RefreshToken generated!")
        print(f"Access Token: {str(refresh.access_token)[:50]}...")
    else:
        print("No users in database, skipping RefreshToken test.")
except Exception as e:
    print(f"FAILURE: RefreshToken generation error: {str(e)}")
