from grc.models import Framework
qs = Framework.objects.filter(Status="Approved", ActiveInactive="Active")
print(f"Total Approved/Active: {qs.count()}")
for f in qs:
    try:
        print(f"ID: {f.FrameworkId}, Status: {f.Status}, Active: {f.ActiveInactive}, Tenant: {f.tenant_id}")
    except Exception as e:
        print(f"Error printing framework {f.FrameworkId}: {e}")
