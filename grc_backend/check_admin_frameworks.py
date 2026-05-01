from grc.models import Users, Framework
u = Users.objects.filter(UserName_plain='Admin').first()
print(f'User: {u.UserName if u else "None"}, Tenant: {u.tenant_id if u else "None"}')

if u:
    tid = u.tenant_id
    qs = Framework.objects.filter(tenant_id=tid, Status='Approved', ActiveInactive='Active')
    print(f'Approved/Active Frameworks for Tenant {tid}: {qs.count()}')
    for f in qs:
        print(f' - ID: {f.FrameworkId}, Name: {f.FrameworkName}')
else:
    print('Admin user not found')
