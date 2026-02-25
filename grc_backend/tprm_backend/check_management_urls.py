#!/usr/bin/env python
"""
Diagnostic script to check if management URLs can be imported and loaded
"""
import os
import sys
import django

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vendor_guard_hub.settings')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

# Test 1: Check if management app is in INSTALLED_APPS
from django.conf import settings
if 'tprm_backend.apps.management' in settings.INSTALLED_APPS:
    print("✅ Management app is in INSTALLED_APPS")
else:
    print("❌ Management app is NOT in INSTALLED_APPS")
    print(f"INSTALLED_APPS: {[app for app in settings.INSTALLED_APPS if 'management' in app]}")

# Test 2: Try to import management URLs
print("\n" + "="*80)
print("Testing management URLs import...")
print("="*80)
try:
    from tprm_backend.apps.management.urls import urlpatterns as mgmt_urls
    print(f"✅ Management URLs imported successfully")
    print(f"   Found {len(mgmt_urls)} URL patterns:")
    for pattern in mgmt_urls:
        print(f"   - {pattern.pattern}")
except ImportError as e:
    print(f"❌ Failed to import management URLs: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ Error importing management URLs: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Try to import views
print("\n" + "="*80)
print("Testing management views import...")
print("="*80)
try:
    from tprm_backend.apps.management.views import AllVendorsListView, VendorDetailView
    print("✅ Management views imported successfully")
except ImportError as e:
    print(f"❌ Failed to import management views: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ Error importing management views: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check if URLs are in main urlpatterns
print("\n" + "="*80)
print("Testing URL resolution...")
print("="*80)
from django.urls import resolve, Resolver404

test_urls = [
    '/api/v1/management/test/',
    '/api/v1/management/health/',
    '/api/v1/management/vendors/all/',
]

for url in test_urls:
    try:
        match = resolve(url)
        print(f"✅ {url}")
        print(f"   → View: {match.func}")
        print(f"   → URL Name: {match.url_name}")
    except Resolver404:
        print(f"❌ {url} - NOT FOUND (404)")
    except Exception as e:
        print(f"❌ {url} - ERROR: {e}")

print("\n" + "="*80)
print("Diagnostic complete!")
print("="*80)
print("\nIf URLs show ❌, Django server needs to be restarted.")
print("Run: python manage.py runserver")
