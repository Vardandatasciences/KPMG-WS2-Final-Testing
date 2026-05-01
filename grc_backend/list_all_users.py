from grc.models import Users
for u in Users.objects.all():
    try:
        print(f"ID: {u.UserId}, Name: {u.UserName}, Tenant: {u.tenant_id if hasattr(u, 'tenant_id') else 'N/A'}")
    except:
        pass
