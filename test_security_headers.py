"""
Test script to verify Enterprise Security Headers are working
Run this after starting your Django server: python manage.py runserver
"""

import requests
import sys

def test_security_headers(url='http://127.0.0.1:8000'):
    """Test security headers on a public endpoint"""
    
    # Try a few endpoints that don't require authentication
    test_endpoints = [
        '/api/frameworks/',  # Framework endpoint
        '/api/test-connection/',  # Test connection endpoint
        '/api/jwt/verify/',  # JWT verify endpoint
    ]
    
    print("=" * 70)
    print("ENTERPRISE SECURITY HEADERS TEST")
    print("=" * 70)
    print(f"\nTesting server at: {url}")
    print("\nMake sure your Django server is running: python manage.py runserver")
    print("-" * 70)
    
    security_headers_required = [
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection',
        'Referrer-Policy',
        'Content-Security-Policy',
        'Permissions-Policy',
        'Cross-Origin-Embedder-Policy',
        'Cross-Origin-Opener-Policy',
        'Cross-Origin-Resource-Policy',
    ]
    
    security_headers_optional = [
        'Strict-Transport-Security',  # Only in production
    ]
    
    success_count = 0
    total_tests = 0
    
    for endpoint in test_endpoints:
        full_url = f"{url}{endpoint}"
        print(f"\n📡 Testing: {full_url}")
        
        try:
            # Send GET request with timeout
            response = requests.get(full_url, timeout=5, allow_redirects=False)
            
            print(f"   Status Code: {response.status_code}")
            
            # Check required headers
            headers_found = []
            headers_missing = []
            
            for header in security_headers_required:
                total_tests += 1
                if header in response.headers:
                    headers_found.append(header)
                    success_count += 1
                    print(f"   ✅ {header}: {response.headers[header][:80]}...")
                else:
                    headers_missing.append(header)
                    print(f"   ❌ {header}: MISSING")
            
            # Check optional headers
            for header in security_headers_optional:
                if header in response.headers:
                    print(f"   ✅ {header}: {response.headers[header]}")
                else:
                    print(f"   ℹ️  {header}: Not set (expected in development)")
            
            if headers_missing:
                print(f"\n   ⚠️  Missing {len(headers_missing)} header(s): {', '.join(headers_missing)}")
            else:
                print(f"\n   ✅ All required security headers present!")
            
            # Show a few more headers for debugging
            print(f"\n   📋 All Response Headers:")
            for key, value in sorted(response.headers.items()):
                if key.startswith('X-') or key in security_headers_required or key in security_headers_optional:
                    print(f"      {key}: {value[:100]}")
            
            break  # If one endpoint works, we're good
            
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION ERROR: Server not running or not accessible")
            print(f"   💡 Make sure Django server is running: python manage.py runserver")
            return False
        except requests.exceptions.Timeout:
            print(f"   ⏱️  TIMEOUT: Server took too long to respond")
            return False
        except requests.exceptions.RequestException as e:
            print(f"   ❌ ERROR: {str(e)}")
            continue
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Headers Found: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n✅ SUCCESS: All security headers are present!")
        print("🎉 Enterprise Security Headers middleware is working correctly!")
        return True
    elif success_count > 0:
        print(f"\n⚠️  PARTIAL: {success_count}/{total_tests} headers found")
        print("Some headers may be missing. Check the output above.")
        return False
    else:
        print("\n❌ FAILED: No security headers found")
        print("The middleware may not be loaded. Check:")
        print("  1. Is the server running?")
        print("  2. Is EnterpriseSecurityHeadersMiddleware in settings.py MIDDLEWARE list?")
        print("  3. Check for any middleware errors in server logs")
        return False


if __name__ == "__main__":
    # Allow custom URL
    url = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000'
    
    success = test_security_headers(url)
    sys.exit(0 if success else 1)
