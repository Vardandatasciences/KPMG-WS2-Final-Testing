from grc.models import Users
u = Users.objects.filter(UserName_plain='Admin').first()
if not u:
    # Try searching by hashed username if possible, or just list all with Admin-like names
    for user in Users.objects.all():
        if 'Admin' in str(user.UserName):
            u = user
            break
print(f'User: {u.UserName if u else "None"}, Tenant: {u.tenant_id if u and hasattr(u, "tenant_id") else "None"}')
