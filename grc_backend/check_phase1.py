import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection
cursor = connection.cursor()

print("=== ENTITY TABLE COLUMNS ===")
cursor.execute("DESCRIBE entities")
cols = [r[0] for r in cursor.fetchall()]
print(f"  columns: {cols}")
print(f"  TenantId present: {'TenantId' in cols}")

print()
print("=== RBAC TABLE COLUMNS ===")
cursor.execute("DESCRIBE rbac")
cols = [r[0] for r in cursor.fetchall()]
print(f"  TenantId present: {'TenantId' in cols}")

print()
print("=== ALL PHASE 1 TABLES ===")
for tbl in ['tenant_audit_log', 'tenant_branding', 'tenant_modules',
            'tenant_security_settings', 'tenant_user_mapping',
            'business_units', 'user_entity_mapping', 'support_access_request']:
    cursor.execute("SHOW TABLES LIKE %s", [tbl])
    exists = bool(cursor.fetchone())
    print(f"  {tbl:35s} exists={exists}")

print()
print("=== DATA MIGRATION RESULTS ===")
cursor.execute("SELECT COUNT(*) FROM tenant_modules")
print(f"  TenantModule rows:          {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM tenant_security_settings")
print(f"  TenantSecuritySettings rows: {cursor.fetchone()[0]}")

print()
print("=== TENANT STATUS FIELD ===")
cursor.execute("SHOW COLUMNS FROM tenants LIKE 'Status'")
row = cursor.fetchone()
print(f"  {row}")
