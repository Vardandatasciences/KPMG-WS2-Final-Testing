import json
from django.test import RequestFactory
from grc.routes.Framework.frameworks import get_approved_active_frameworks
from grc.models import Users

# Create a mock request
factory = RequestFactory()
request = factory.get('/api/frameworks/approved-active/')

# Mock user and tenant (Admin user ID 280, Tenant ID 2)
user = Users.objects.get(UserId=280)
request.user = user
request.tenant_id = 2
request.tenant = type('SimpleTenant', (), {'tenant_id': 2, 'id': 2})()

# Call the view
response = get_approved_active_frameworks(request)

print(f'Status Code: {response.status_code}')
print(f'Data: {json.dumps(response.data, indent=2) if hasattr(response, "data") else response.content}')
