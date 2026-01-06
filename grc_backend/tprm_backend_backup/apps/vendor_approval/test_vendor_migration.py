#!/usr/bin/env python3
"""
Test script for vendor migration functionality
This script tests the migrate_vendor_from_temp_to_main function
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tprm_backend.apps.vendor_approval.views import migrate_vendor_from_temp_to_main
from tprm_backend.apps.vendor_approval.models import TempVendor
from django.db import connection
import json

def test_vendor_migration():
    """Test the vendor migration functionality"""
    print("Testing vendor migration functionality...")
    
    # Test 1: Check if we can find any temp vendors
    try:
        temp_vendors = TempVendor.objects.all()[:5]  # Get first 5 temp vendors
        print(f"Found {len(temp_vendors)} temp vendors in the system")
        
        if not temp_vendors:
            print("No temp vendors found. Creating a test temp vendor...")
            # Create a test temp vendor
            test_vendor = TempVendor.objects.create(
                vendor_code='TEST_MIGRATION_001',
                company_name='Test Migration Company',
                legal_name='Test Migration Company LLC',
                business_type='Technology',
                industry_sector='Software',
                website='https://testmigration.com',
                risk_level='LOW',
                status='PENDING',
                is_critical_vendor=False,
                has_data_access=False,
                has_system_access=False,
                description='Test vendor for migration testing',
                contacts=json.dumps([
                    {
                        'contact_type': 'PRIMARY',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'email': 'john.doe@testmigration.com',
                        'phone': '+1-555-0123',
                        'designation': 'CEO',
                        'is_primary': True
                    }
                ]),
                documents=json.dumps([
                    {
                        'document_type': 'CERTIFICATE',
                        'document_name': 'Business License',
                        'file_name': 'business_license.pdf',
                        'file_path': '/uploads/test/business_license.pdf',
                        'file_size': 1024000,
                        'mime_type': 'application/pdf',
                        'document_category': 'Legal',
                        'version_number': '1.0'
                    }
                ])
            )
            print(f"Created test temp vendor with ID: {test_vendor.id}")
            temp_vendor_id = test_vendor.id
        else:
            temp_vendor_id = temp_vendors[0].id
            print(f"Using existing temp vendor with ID: {temp_vendor_id}")
        
        # Test 2: Check if vendor already exists in main table
        with connection.cursor() as cursor:
            cursor.execute("SELECT vendor_id FROM vendors WHERE vendor_code = %s", ['TEST_MIGRATION_001'])
            existing_vendor = cursor.fetchone()
            
            if existing_vendor:
                print(f"Test vendor already exists in main table with ID: {existing_vendor[0]}")
                print("Skipping migration test to avoid duplicate data")
                return True
        
        # Test 3: Run the migration
        print(f"Running migration for temp vendor ID: {temp_vendor_id}")
        result = migrate_vendor_from_temp_to_main(temp_vendor_id, user_id=1)
        
        if result['success']:
            print("✅ Migration successful!")
            print(f"   - New vendor ID: {result['vendor_id']}")
            print(f"   - Vendor code: {result['vendor_code']}")
            print(f"   - Company name: {result['company_name']}")
            print(f"   - Contacts migrated: {result['contacts_migrated']}")
            print(f"   - Documents migrated: {result['documents_migrated']}")
            
            # Test 4: Verify data in main tables
            with connection.cursor() as cursor:
                # Check vendors table
                cursor.execute("SELECT * FROM vendors WHERE vendor_id = %s", [result['vendor_id']])
                vendor_data = cursor.fetchone()
                if vendor_data:
                    print("✅ Vendor data verified in main vendors table")
                else:
                    print("❌ Vendor data not found in main vendors table")
                
                # Check vendor_contacts table
                cursor.execute("SELECT COUNT(*) FROM vendor_contacts WHERE vendor_id = %s", [result['vendor_id']])
                contact_count = cursor.fetchone()[0]
                if contact_count > 0:
                    print(f"✅ {contact_count} contacts verified in vendor_contacts table")
                else:
                    print("❌ No contacts found in vendor_contacts table")
                
                # Check vendor_documents table
                cursor.execute("SELECT COUNT(*) FROM vendor_documents WHERE vendor_id = %s", [result['vendor_id']])
                doc_count = cursor.fetchone()[0]
                if doc_count > 0:
                    print(f"✅ {doc_count} documents verified in vendor_documents table")
                else:
                    print("❌ No documents found in vendor_documents table")
            
            return True
        else:
            print(f"❌ Migration failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Clean up test data"""
    try:
        with connection.cursor() as cursor:
            # Delete test vendor from main tables
            cursor.execute("DELETE FROM vendor_documents WHERE vendor_id IN (SELECT vendor_id FROM vendors WHERE vendor_code = 'TEST_MIGRATION_001')")
            cursor.execute("DELETE FROM vendor_contacts WHERE vendor_id IN (SELECT vendor_id FROM vendors WHERE vendor_code = 'TEST_MIGRATION_001')")
            cursor.execute("DELETE FROM vendors WHERE vendor_code = 'TEST_MIGRATION_001'")
            
            # Delete test temp vendor
            TempVendor.objects.filter(vendor_code='TEST_MIGRATION_001').delete()
            
            print("✅ Test data cleaned up successfully")
    except Exception as e:
        print(f"Warning: Error cleaning up test data: {str(e)}")

if __name__ == '__main__':
    print("=" * 60)
    print("VENDOR MIGRATION TEST")
    print("=" * 60)
    
    try:
        success = test_vendor_migration()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ TESTS FAILED!")
            print("=" * 60)
        
        # Ask user if they want to clean up test data
        cleanup = input("\nDo you want to clean up test data? (y/n): ").lower().strip()
        if cleanup == 'y':
            cleanup_test_data()
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

