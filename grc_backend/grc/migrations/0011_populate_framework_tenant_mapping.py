"""
Data migration: populate framework_tenant_mapping from existing data.

Rules:
  1. Frameworks with a non-NULL tenant_id  → one mapping row for their own tenant.
  2. Frameworks with tenant_id = NULL (shared/platform-level like HIPAA, NIST, SOC2)
     → one mapping row for EVERY active tenant in the system.
"""
from django.db import migrations


def populate_mappings(apps, schema_editor):
    Framework = apps.get_model('grc', 'Framework')
    Tenant = apps.get_model('grc', 'Tenant')
    FrameworkTenantMapping = apps.get_model('grc', 'FrameworkTenantMapping')

    all_tenants = list(Tenant.objects.filter(status='active'))

    for framework in Framework.objects.all():
        if framework.tenant_id:
            # Tenant-owned framework — map only to its own tenant
            FrameworkTenantMapping.objects.get_or_create(
                framework=framework,
                tenant_id=framework.tenant_id,
                defaults={'is_active': True},
            )
        else:
            # Shared platform framework — map to every active tenant
            for tenant in all_tenants:
                FrameworkTenantMapping.objects.get_or_create(
                    framework=framework,
                    tenant=tenant,
                    defaults={'is_active': True},
                )


def reverse_mappings(apps, schema_editor):
    FrameworkTenantMapping = apps.get_model('grc', 'FrameworkTenantMapping')
    FrameworkTenantMapping.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0010_framework_tenant_mapping'),
    ]

    operations = [
        migrations.RunPython(populate_mappings, reverse_code=reverse_mappings),
    ]
