"""
Migration script to add retentionExpiry column (DATE type) to all tables in the database.

This script:
1. Connects to the MySQL database using Django settings
2. Adds 'retentionExpiry' DATE column to all tables
3. Handles errors gracefully if column already exists
"""

import os
import sys
import django
from django.conf import settings
from django.db import connection
from django.core.management import execute_from_command_line

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# List of all tables that need the retentionExpiry column
# Based on db_table values from models.py
TABLES = [
    'users',
    'categoryunit',
    'frameworks',
    'kpis',
    'frameworkversions',
    'policies',
    'policyversions',
    'policycategories',
    'subpolicies',
    'policyapproval',
    'complianceapproval',
    'frameworkapproval',
    'compliance',
    'exported_files',
    'audit',
    'audit_findings',
    'incidents',
    'incident_approval',
    'audit_report',
    'audit_documents',
    'audit_document_mappings',
    'workflow',
    'audit_version',
    'notifications',
    's3_files',
    'risk',
    'risk_instance',
    'risk_assignments',
    'grc.risk_approval',  # Note: This has a schema prefix
    'grc_logs',
    'entities',
    'lastchecklistitemverified',
    'rbac',
    'businessunits',
    'category',
    'department',
    'mainentities',
    'holidays',
    'locations',
    'applicability',
    'events',
    'eventtype',
    'modules',
    'aws_credentials',
    'file_operations',
    'external_applications',
    'external_application_connections',
    'external_application_sync_logs',
    'users_project_list',
    'integration_data_list',
    'oauth_states',
    'policy_acknowledgement_requests',
    'policy_acknowledgement_users',
    'consent_configuration',
    'consent_acceptance',
]


def add_retention_expiry_column():
    """
    Add retentionExpiry DATE column to all tables.
    """
    cursor = connection.cursor()
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    print("=" * 80)
    print("Adding 'retentionExpiry' column to all tables")
    print("=" * 80)
    print()
    
    for table in TABLES:
        try:
            # Handle schema-prefixed tables (e.g., 'grc.risk_approval')
            if '.' in table:
                schema, table_name = table.split('.', 1)
                alter_query = f"ALTER TABLE `{schema}`.`{table_name}` ADD COLUMN `retentionExpiry` DATE NULL"
                table_display = f"{schema}.{table_name}"
                # Check if column already exists (for schema-prefixed tables)
                check_query = f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = '{schema}' 
                    AND TABLE_NAME = '{table_name}' 
                    AND COLUMN_NAME = 'retentionExpiry'
                """
            else:
                alter_query = f"ALTER TABLE `{table}` ADD COLUMN `retentionExpiry` DATE NULL"
                table_display = table
                # Check if column already exists
                check_query = f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = '{table}' 
                    AND COLUMN_NAME = 'retentionExpiry'
                """
            
            cursor.execute(check_query)
            column_exists = cursor.fetchone()[0] > 0
            
            if column_exists:
                print(f"⏭️  SKIPPED: {table_display} - Column 'retentionExpiry' already exists")
                skipped_count += 1
            else:
                cursor.execute(alter_query)
                print(f"✅ SUCCESS: {table_display} - Added 'retentionExpiry' column")
                success_count += 1
                
        except Exception as e:
            error_msg = str(e)
            # Check if error is due to column already existing (different error message)
            if 'Duplicate column name' in error_msg or 'already exists' in error_msg.lower():
                print(f"⏭️  SKIPPED: {table_display} - Column already exists (different check)")
                skipped_count += 1
            else:
                print(f"❌ ERROR: {table_display} - {error_msg}")
                error_count += 1
    
    print()
    print("=" * 80)
    print("Migration Summary:")
    print(f"  ✅ Successfully added: {success_count} tables")
    print(f"  ⏭️  Skipped (already exists): {skipped_count} tables")
    print(f"  ❌ Errors: {error_count} tables")
    print("=" * 80)
    
    cursor.close()


if __name__ == '__main__':
    try:
        add_retention_expiry_column()
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

