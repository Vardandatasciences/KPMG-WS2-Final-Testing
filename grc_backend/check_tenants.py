from grc.models import Users, Framework
print('--- Users ---')
for u in Users.objects.all()[:10]:
    print(f'ID: {u.UserId}, Name: {u.UserName}, Tenant: {u.tenant_id if hasattr(u, "tenant_id") else "N/A"}')

print('\n--- Approved/Active Frameworks ---')
for f in Framework.objects.filter(Status="Approved", ActiveInactive="Active")[:10]:
    print(f'ID: {f.FrameworkId}, Name: {f.FrameworkName}, Tenant: {f.tenant_id}')
