"""
Dynamic Script to Populate TenantId for Existing Records

This script:
1. Finds all tables with TenantId column
2. Distributes existing records between Tenant 1 and Tenant 2
3. Updates all NULL TenantId values

Usage:
    python manage.py shell
    >>> exec(open('tprm_backend/scripts/populate_tenantid_dynamic.py').read())
    
Or run directly:
    python manage.py shell < tprm_backend/scripts/populate_tenantid_dynamic.py
"""

import os
import django

# Setup Django if not already done
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()

from django.db import connection
from tprm_backend.core.models import Tenant


def get_tables_with_tenantid():
    """Get all tables that have TenantId column"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT TABLE_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND COLUMN_NAME = 'TenantId'
              AND TABLE_NAME != 'tenants'
            ORDER BY TABLE_NAME
        """)
        return [row[0] for row in cursor.fetchall()]


def get_primary_key_column(table_name):
    """Get the primary key column name for a table"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND CONSTRAINT_NAME = 'PRIMARY'
            LIMIT 1
        """, [table_name])
        result = cursor.fetchone()
        return result[0] if result else None


def populate_tenantid_for_table(table_name, tenant1_id, tenant2_id):
    """Populate TenantId for a specific table, distributing between two tenants"""
    pk_column = get_primary_key_column(table_name)
    
    if not pk_column:
        print(f"⚠️  {table_name}: No primary key found, skipping")
        return False
    
    try:
        with connection.cursor() as cursor:
            # Count records with NULL TenantId
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` WHERE TenantId IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count == 0:
                print(f"✅ {table_name}: All records already have TenantId")
                return True
            
            # Distribute records: even PK -> tenant 1, odd PK -> tenant 2
            # Handle different PK types (INT, BIGINT, VARCHAR, etc.)
            cursor.execute(f"""
                UPDATE `{table_name}` 
                SET TenantId = CASE 
                    WHEN (CAST({pk_column} AS UNSIGNED) % 2) = 0 THEN %s
                    ELSE %s
                END
                WHERE TenantId IS NULL
            """, [tenant1_id, tenant2_id])
            
            updated_count = cursor.rowcount
            
            # Verify distribution
            cursor.execute(f"""
                SELECT 
                    TenantId,
                    COUNT(*) as count
                FROM `{table_name}`
                WHERE TenantId IN (%s, %s)
                GROUP BY TenantId
            """, [tenant1_id, tenant2_id])
            
            distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            print(f"✅ {table_name}: Updated {updated_count} records")
            print(f"   Distribution: Tenant {tenant1_id}: {distribution.get(tenant1_id, 0)}, "
                  f"Tenant {tenant2_id}: {distribution.get(tenant2_id, 0)}")
            
            return True
            
    except Exception as e:
        print(f"❌ {table_name}: Error - {str(e)}")
        return False


def main():
    """Main function to populate TenantId for all tables"""
    print("\n" + "="*70)
    print("POPULATE TENANTID FOR EXISTING RECORDS")
    print("="*70)
    
    # Verify tenants exist
    try:
        tenant1 = Tenant.objects.get(tenant_id=1)
        tenant2 = Tenant.objects.get(tenant_id=2)
        print(f"\n✅ Found Tenant 1: {tenant1.name} (Subdomain: {tenant1.subdomain})")
        print(f"✅ Found Tenant 2: {tenant2.name} (Subdomain: {tenant2.subdomain})")
    except Tenant.DoesNotExist as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("   Please ensure Tenant 1 and Tenant 2 exist in the database")
        return False
    
    # Get all tables with TenantId column
    tables = get_tables_with_tenantid()
    
    if not tables:
        print("\n⚠️  No tables with TenantId column found")
        return False
    
    print(f"\n📋 Found {len(tables)} table(s) with TenantId column:")
    for table in tables:
        print(f"   - {table}")
    
    # Confirm before proceeding
    print("\n" + "="*70)
    print("This will distribute existing records between Tenant 1 and Tenant 2")
    print("Records will be distributed based on primary key MOD 2:")
    print("  - Even PK values -> Tenant 1")
    print("  - Odd PK values -> Tenant 2")
    print("="*70)
    
    response = input("\nProceed? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Cancelled by user")
        return False
    
    # Process each table
    print("\n" + "="*70)
    print("PROCESSING TABLES...")
    print("="*70)
    
    success_count = 0
    fail_count = 0
    
    for table in tables:
        if populate_tenantid_for_table(table, 1, 2):
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✅ Successfully processed: {success_count} table(s)")
    if fail_count > 0:
        print(f"❌ Failed: {fail_count} table(s)")
    
    # Verification query
    print("\n" + "="*70)
    print("VERIFICATION - Sample Distribution")
    print("="*70)
    
    # Check a few key tables
    sample_tables = ['rfps', 'vendors', 'vendor_contracts', 'rfp_evaluation_criteria']
    for table in sample_tables:
        if table in tables:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT 
                            TenantId,
                            COUNT(*) as count
                        FROM `{table}`
                        WHERE TenantId IN (1, 2)
                        GROUP BY TenantId
                        ORDER BY TenantId
                    """)
                    results = cursor.fetchall()
                    if results:
                        print(f"\n{table}:")
                        for tenant_id, count in results:
                            print(f"   Tenant {tenant_id}: {count} records")
            except Exception as e:
                print(f"⚠️  Could not verify {table}: {str(e)}")
    
    print("\n" + "="*70)
    print("✅ COMPLETE!")
    print("="*70 + "\n")
    
    return fail_count == 0


if __name__ == '__main__':
    main()

