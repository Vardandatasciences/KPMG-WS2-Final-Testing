# Phase 1 Data Migration
# Populates: TenantModule (all 7 modules for every tenant),
#            TenantSecuritySettings (defaults for every tenant),
#            Backfills Entity.tenant_id via Department relationships

from django.db import migrations


MODULES = ['framework', 'policy', 'compliance', 'audit', 'risk', 'incident', 'event']


def populate_tenant_modules(apps, schema_editor):
    Tenant = apps.get_model('grc', 'Tenant')
    TenantModule = apps.get_model('grc', 'TenantModule')
    for tenant in Tenant.objects.all():
        for module in MODULES:
            TenantModule.objects.get_or_create(
                tenant=tenant,
                module_code=module,
                defaults={'is_enabled': True, 'license_tier': 'enterprise'},
            )


def populate_security_settings(apps, schema_editor):
    Tenant = apps.get_model('grc', 'Tenant')
    TenantSecuritySettings = apps.get_model('grc', 'TenantSecuritySettings')
    for tenant in Tenant.objects.all():
        TenantSecuritySettings.objects.get_or_create(
            tenant=tenant,
            defaults={
                'mfa_required': False,
                'session_timeout_minutes': 30,
                'password_expiry_days': 90,
            },
        )


def backfill_entity_tenant(apps, schema_editor):
    Department = apps.get_model('grc', 'Department')
    Entity = apps.get_model('grc', 'Entity')
    for dept in Department.objects.filter(tenant__isnull=False).select_related('tenant'):
        Entity.objects.filter(Id=dept.EntityId, tenant__isnull=True).update(tenant=dept.tenant)


def reverse_populate_tenant_modules(apps, schema_editor):
    pass


def reverse_populate_security_settings(apps, schema_editor):
    pass


def reverse_backfill_entity_tenant(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0009_entity_add_tenant_fk'),
    ]

    operations = [
        migrations.RunPython(populate_tenant_modules, reverse_populate_tenant_modules),
        migrations.RunPython(populate_security_settings, reverse_populate_security_settings),
        migrations.RunPython(backfill_entity_tenant, reverse_backfill_entity_tenant),
    ]
