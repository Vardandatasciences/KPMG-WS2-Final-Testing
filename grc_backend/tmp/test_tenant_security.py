import sys
import os
import json
from unittest.mock import MagicMock

# Setup Django environment
project_root = os.path.join(os.getcwd())
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from grc.tenant_utils import require_tenant
from django.http import JsonResponse, HttpRequest

def test_require_tenant_logic():
    print("--- Testing require_tenant security hardening ---")
    
    # 1. Mock a standard user with tenant_id = 1
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.tenant_id = 1
    mock_user.UserId = 123
    
    @require_tenant
    def mock_view(request):
        return JsonResponse({'status': 'success', 'tenant_id': request.tenant_id})

    # Test Case A: Valid request (no tenant_id passed, should resolve from user)
    request_a = HttpRequest()
    request_a.user = mock_user
    request_a.method = 'GET'
    response_a = mock_view(request_a)
    print(f"Test A (Valid): Status {response_a.status_code}, Body {response_a.content}")
    assert response_a.status_code == 200
    assert json.loads(response_a.content)['tenant_id'] == 1

    # Test Case B: Tampered request (User ID 1 passed tenant_id=2 in body)
    request_b = HttpRequest()
    request_b.user = mock_user
    request_b.method = 'POST'
    request_b.content_type = 'application/json'
    request_b.data = {'tenant_id': 2}
    
    # Mocking the JSON body parsing logic in our wrapper
    request_b._body = json.dumps({'tenant_id': 2}).encode('utf-8')
    
    response_b = mock_view(request_b)
    print(f"Test B (Tampered): Status {response_b.status_code}, Body {response_b.content}")
    assert response_b.status_code == 403
    assert b'Tenant context mismatch' in response_b.content

    # Test Case C: Matching client tenant_id (User ID 1 passed tenant_id=1)
    request_c = HttpRequest()
    request_c.user = mock_user
    request_c.method = 'POST'
    request_c.data = {'tenant_id': 1}
    response_c = mock_view(request_c)
    print(f"Test C (Matching): Status {response_c.status_code}, Body {response_c.content}")
    assert response_c.status_code == 200
    assert json.loads(response_c.content)['tenant_id'] == 1

    print("\n[SUCCESS] Verification: Tenant context mismatch is correctly blocked.")

if __name__ == "__main__":
    try:
        test_require_tenant_logic()
    except Exception as e:
        print(f"[FAILED] Verification: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
