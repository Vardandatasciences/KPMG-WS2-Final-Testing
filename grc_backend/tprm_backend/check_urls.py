#!/usr/bin/env python
"""
Quick script to verify URL patterns are in the correct order
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vendor_guard_hub.settings')
django.setup()

from django.urls import resolve, Resolver404
from django.conf import settings

# Test URLs that should work
test_urls = [
    '/api/tprm/v1/vendor-dashboard/screening-match-rate/',
    '/api/tprm/v1/vendor-dashboard/questionnaire-overdue-rate/',
    '/api/tprm/v1/vendor-dashboard/kpi-categories/',
    '/api/tprm/v1/vendor-dashboard/alerts/',
    '/api/tprm/v1/vendor-dashboard/vendor-registration-time/',
    '/api/tprm/v1/vendor-dashboard/vendor-acceptance-time/',
    '/api/tprm/v1/vendor-dashboard/vendor-registration-completion-rate/',
]

print("=" * 80)
print("Testing Vendor Dashboard URL Resolution")
print("=" * 80)

for url in test_urls:
    try:
        match = resolve(url)
        print(f"✅ {url}")
        print(f"   → View: {match.func}")
        print(f"   → URL Name: {match.url_name}")
        print()
    except Resolver404 as e:
        print(f"❌ {url}")
        print(f"   → ERROR: {e}")
        print()

print("=" * 80)
print("If all URLs show ❌, Django server needs to be restarted!")
print("=" * 80)



