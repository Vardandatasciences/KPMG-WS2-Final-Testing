"""
Script to encrypt all existing plaintext data in the database.

This script:
1. Reads GRC_ENCRYPTION_KEY from environment
2. Finds all models with encrypted fields
3. Encrypts any plaintext data in those fields
4. Saves encrypted data back to database

IMPORTANT: 
- Backup your database before running this!
- This script only encrypts data that is NOT already encrypted
- Run this ONCE to migrate existing plaintext data to encrypted format
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings
from grc.utils.data_encryption import encrypt_data, is_encrypted_data, get_encryption_service
from grc.utils.encryption_config import ENCRYPTED_FIELDS_CONFIG
# Import all models that might have encrypted fields
from grc.models import (
    Users, Framework, Policy, SubPolicy, Compliance, Risk, RiskInstance,
    Incident, Event, Audit, AuditFinding, AuditReport, BusinessUnit,
    Category, Department, Entity, Location, Kpi, PolicyCategory,
    ExternalApplication, ExternalApplicationConnection, AuditDocument, S3File
)

# Try to import additional models if they exist
try:
    from grc.models import (
        AWSCredentials, MfaEmailChallenge, DataSubjectRequest,
        OrganizationalControl, OrganizationalControlDocument, FileOperations,
        IntegrationDataList, OAuthState, PolicyAcknowledgementRequest,
        PolicyAcknowledgementUser, ConsentConfiguration, ConsentAcceptance,
        ConsentWithdrawal, CookiePreferences, RetentionTimeline,
        DataLifecycleAuditLog, UsersProjectList, Notification, RBAC,
        ExportTask, GRCLog, PasswordLog, AccessRequest, ComplianceBaseline,
        LastChecklistItemVerified, Workflow
    )
except ImportError:
    # Some models might not exist, that's okay
    pass

# Map model names to actual model classes
# This dynamically builds the map from available models
MODEL_MAP = {
    'Users': Users,
    'Framework': Framework,
    'Policy': Policy,
    'SubPolicy': SubPolicy,
    'Compliance': Compliance,
    'Risk': Risk,
    'RiskInstance': RiskInstance,
    'Incident': Incident,
    'Event': Event,
    'Audit': Audit,
    'AuditFinding': AuditFinding,
    'AuditReport': AuditReport,
    'BusinessUnit': BusinessUnit,
    'Category': Category,
    'Department': Department,
    'Entity': Entity,
    'Location': Location,
    'Kpi': Kpi,
    'PolicyCategory': PolicyCategory,
    'ExternalApplication': ExternalApplication,
    'ExternalApplicationConnection': ExternalApplicationConnection,
    'AuditDocument': AuditDocument,
    'S3File': S3File,
}

# Add additional models if they exist
try:
    MODEL_MAP.update({
        'AWSCredentials': AWSCredentials,
        'MfaEmailChallenge': MfaEmailChallenge,
        'DataSubjectRequest': DataSubjectRequest,
        'OrganizationalControl': OrganizationalControl,
        'OrganizationalControlDocument': OrganizationalControlDocument,
        'FileOperations': FileOperations,
        'IntegrationDataList': IntegrationDataList,
        'OAuthState': OAuthState,
        'PolicyAcknowledgementRequest': PolicyAcknowledgementRequest,
        'PolicyAcknowledgementUser': PolicyAcknowledgementUser,
        'ConsentConfiguration': ConsentConfiguration,
        'ConsentAcceptance': ConsentAcceptance,
        'ConsentWithdrawal': ConsentWithdrawal,
        'CookiePreferences': CookiePreferences,
        'RetentionTimeline': RetentionTimeline,
        'DataLifecycleAuditLog': DataLifecycleAuditLog,
        'UsersProjectList': UsersProjectList,
        'Notification': Notification,
        'RBAC': RBAC,
        'ExportTask': ExportTask,
        'GRCLog': GRCLog,
        'PasswordLog': PasswordLog,
        'AccessRequest': AccessRequest,
        'ComplianceBaseline': ComplianceBaseline,
        'LastChecklistItemVerified': LastChecklistItemVerified,
        'Workflow': Workflow,
    })
except NameError:
    # Some models don't exist, that's okay - they'll be skipped
    pass

def check_encryption_key():
    """Verify that GRC_ENCRYPTION_KEY is set"""
    env_key = os.environ.get('GRC_ENCRYPTION_KEY', None)
    settings_key = getattr(settings, 'GRC_ENCRYPTION_KEY', None)
    
    if not env_key and not settings_key:
        print("=" * 80)
        print("ERROR: GRC_ENCRYPTION_KEY is not set!")
        print("=" * 80)
        print("Please set GRC_ENCRYPTION_KEY in your environment or Django settings.")
        print("This script requires a valid encryption key to proceed.")
        sys.exit(1)
    
    # Test encryption service
    try:
        service = get_encryption_service()
        test_text = "test"
        encrypted = service.encrypt(test_text)
        decrypted = service.decrypt(encrypted)
        if decrypted != test_text:
            print("ERROR: Encryption service test failed!")
            sys.exit(1)
        print("✅ Encryption key verified and working")
        return True
    except Exception as e:
        print(f"ERROR: Encryption service failed: {e}")
        sys.exit(1)

def encrypt_model_field(model_class, field_name, dry_run=True):
    """
    Encrypt a specific field for all records in a model.
    
    Args:
        model_class: Django model class
        field_name: Name of the field to encrypt
        dry_run: If True, only show what would be encrypted without saving
    
    Returns:
        Tuple of (total_records, encrypted_count, skipped_count, error_count)
    """
    try:
        # Get all records
        records = model_class.objects.all()
        total_records = records.count()
        
        if total_records == 0:
            return (0, 0, 0, 0)
        
        encrypted_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"  Processing {total_records} records...")
        
        for record in records:
            try:
                # Get current field value
                field_value = getattr(record, field_name, None)
                
                # Skip if field is None or empty
                if not field_value:
                    skipped_count += 1
                    continue
                
                # Convert to string if needed
                if not isinstance(field_value, str):
                    field_value = str(field_value)
                
                # Check if already encrypted
                if is_encrypted_data(field_value):
                    skipped_count += 1
                    continue
                
                # Encrypt the value
                encrypted_value = encrypt_data(field_value)
                
                if not dry_run:
                    # Use direct database update() to avoid triggering save() methods/signals
                    # This prevents creating related records like RetentionTimeline
                    try:
                        # Direct SQL update - bypasses model save() and all signals
                        model_class.objects.filter(pk=record.pk).update(**{field_name: encrypted_value})
                        encrypted_count += 1
                    except Exception as update_error:
                        # If update fails, log error but don't use save() (it might create unwanted records)
                        error_count += 1
                        record_id = getattr(record, 'pk', 'unknown')
                        print(f"    ⚠️  Error updating {model_class.__name__}.{field_name} (ID: {record_id}): {update_error}")
                else:
                    # Dry run - just count
                    encrypted_count += 1
                    
            except Exception as e:
                error_count += 1
                record_id = getattr(record, 'pk', 'unknown')
                print(f"    ⚠️  Error encrypting {model_class.__name__}.{field_name} (ID: {record_id}): {e}")
        
        return (total_records, encrypted_count, skipped_count, error_count)
        
    except Exception as e:
        print(f"  ❌ Error processing model {model_class.__name__}: {e}")
        return (0, 0, 0, 1)

def encrypt_all_data(dry_run=True):
    """
    Encrypt all plaintext data in the database.
    
    Args:
        dry_run: If True, only show what would be encrypted without saving
    """
    print("=" * 80)
    print("DATABASE ENCRYPTION SCRIPT")
    print("=" * 80)
    print()
    
    if dry_run:
        print("🔍 DRY RUN MODE - No data will be modified")
    else:
        print("⚠️  LIVE MODE - Data will be encrypted and saved!")
    print()
    
    # Check encryption key
    check_encryption_key()
    print()
    
    # Statistics
    total_models = 0
    total_records = 0
    total_encrypted = 0
    total_skipped = 0
    total_errors = 0
    
    # Process each model
    for model_name, encrypted_fields in ENCRYPTED_FIELDS_CONFIG.items():
        if model_name not in MODEL_MAP:
            print(f"⚠️  Model '{model_name}' not found in MODEL_MAP, skipping...")
            continue
        
        model_class = MODEL_MAP[model_name]
        print(f"\n📦 Processing model: {model_name}")
        
        model_encrypted = 0
        model_skipped = 0
        model_errors = 0
        
        # Process each encrypted field
        for field_name in encrypted_fields:
            # Skip Password field - should be hashed, not encrypted
            if field_name == 'Password':
                print(f"  ⏭️  Skipping {field_name} (should be hashed, not encrypted)")
                continue
            
            # Check if field exists in model
            if not hasattr(model_class, field_name):
                print(f"  ⚠️  Field '{field_name}' not found in {model_name}, skipping...")
                continue
            
            print(f"  🔐 Encrypting field: {field_name}")
            
            records, encrypted, skipped, errors = encrypt_model_field(
                model_class, field_name, dry_run=dry_run
            )
            
            model_encrypted += encrypted
            model_skipped += skipped
            model_errors += errors
            
            if encrypted > 0:
                print(f"    ✅ Encrypted: {encrypted} records")
            if skipped > 0:
                print(f"    ⏭️  Skipped (already encrypted/empty): {skipped} records")
            if errors > 0:
                print(f"    ❌ Errors: {errors} records")
        
        if model_encrypted > 0 or model_skipped > 0:
            total_models += 1
            total_encrypted += model_encrypted
            total_skipped += model_skipped
            total_errors += model_errors
    
    # Summary
    print()
    print("=" * 80)
    print("ENCRYPTION SUMMARY")
    print("=" * 80)
    print(f"Models processed: {total_models}")
    print(f"Records encrypted: {total_encrypted}")
    print(f"Records skipped (already encrypted/empty): {total_skipped}")
    print(f"Errors: {total_errors}")
    print()
    
    if dry_run:
        print("🔍 This was a DRY RUN - no data was modified")
        print("To actually encrypt the data, run:")
        print("  python encrypt_all_data.py --live")
    else:
        print("✅ Encryption complete!")
    print("=" * 80)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Encrypt all plaintext data in the database')
    parser.add_argument('--live', action='store_true', 
                       help='Actually encrypt and save data (default is dry-run)')
    args = parser.parse_args()
    
    # Run encryption
    encrypt_all_data(dry_run=not args.live)

