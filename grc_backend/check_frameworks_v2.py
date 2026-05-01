from grc.models import Framework
qs = Framework.objects.filter(Status="Approved", ActiveInactive="Active")
print(f"Total Approved/Active: {qs.count()}")
for f in qs:
    print(f"ID: {f.FrameworkId}, Name: {f.FrameworkName[:20]}, Status: {f.Status}, Active: {f.ActiveInactive}, Tenant: {f.tenant_id}")
