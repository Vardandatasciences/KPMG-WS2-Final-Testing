from grc.models import Framework
print(f'Total: {Framework.objects.count()}')
print(f'Approved/Active: {Framework.objects.filter(Status="Approved", ActiveInactive="Active").count()}')
for f in Framework.objects.all():
    print(f'ID: {f.FrameworkId}, Name: {f.FrameworkName}, Status: {f.Status}, Active: {f.ActiveInactive}, Tenant: {f.tenant_id}')
