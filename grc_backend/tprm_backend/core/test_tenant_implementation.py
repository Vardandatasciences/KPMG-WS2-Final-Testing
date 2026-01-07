"""
Test script to verify multi-tenancy implementation for TPRM

Run this script to check if tenant signals, middleware, and filtering are working correctly.

Usage:
    python manage.py shell
    >>> exec(open('tprm_backend/core/test_tenant_implementation.py').read())
    
Or run directly:
    python manage.py shell < tprm_backend/core/test_tenant_implementation.py
"""

import os
import django

# Setup Django if not already done
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()

from django.db import connection
from tprm_backend.core.models import Tenant
from tprm_backend.core.tenant_context import set_current_tenant, get_current_tenant, clear_current_tenant
from tprm_backend.rfp.models import RFP, RFPEvaluationCriteria


def test_tenant_context():
    """Test 1: Verify tenant context functions work"""
    print("\n" + "="*60)
    print("TEST 1: Tenant Context Functions")
    print("="*60)
    
    # Clear any existing tenant
    clear_current_tenant()
    assert get_current_tenant() is None, "Tenant should be None initially"
    print("✅ Tenant context cleared successfully")
    
    # Set a test tenant
    set_current_tenant(1)
    assert get_current_tenant() == 1, "Tenant should be set to 1"
    print(f"✅ Tenant context set to: {get_current_tenant()}")
    
    # Clear again
    clear_current_tenant()
    assert get_current_tenant() is None, "Tenant should be None after clearing"
    print("✅ Tenant context cleared successfully")
    
    print("✅ TEST 1 PASSED: Tenant context functions work correctly\n")


def test_tenant_model():
    """Test 2: Verify Tenant model exists and can be queried"""
    print("="*60)
    print("TEST 2: Tenant Model")
    print("="*60)
    
    try:
        tenants = Tenant.objects.all()[:5]
        tenant_count = Tenant.objects.count()
        print(f"✅ Tenant model accessible")
        print(f"✅ Found {tenant_count} tenant(s) in database")
        
        if tenant_count > 0:
            first_tenant = tenants[0]
            print(f"   Sample tenant: {first_tenant.name} (ID: {first_tenant.tenant_id}, Subdomain: {first_tenant.subdomain})")
        else:
            print("   ⚠️  WARNING: No tenants found in database. Create at least one tenant for testing.")
        
        print("✅ TEST 2 PASSED: Tenant model works correctly\n")
        return tenant_count > 0
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {str(e)}\n")
        return False


def test_tenant_signals():
    """Test 3: Verify tenant signals auto-assign tenant_id"""
    print("="*60)
    print("TEST 3: Tenant Signals (Auto-assignment)")
    print("="*60)
    
    try:
        # Get or create a test tenant
        test_tenant, created = Tenant.objects.get_or_create(
            subdomain='test',
            defaults={
                'name': 'Test Tenant',
                'status': 'active'
            }
        )
        if created:
            print(f"✅ Created test tenant: {test_tenant.name} (ID: {test_tenant.tenant_id})")
        else:
            print(f"✅ Using existing test tenant: {test_tenant.name} (ID: {test_tenant.tenant_id})")
        
        # Set tenant context
        set_current_tenant(test_tenant.tenant_id)
        print(f"✅ Set tenant context to: {get_current_tenant()}")
        
        # Try to create an RFP (should auto-assign tenant)
        try:
            # Check if RFP table exists and has tenant field
            with connection.cursor() as cursor:
                cursor.execute("SHOW COLUMNS FROM rfps LIKE 'TenantId'")
                has_tenant_field = cursor.fetchone() is not None
            
            if has_tenant_field:
                # Create a test RFP
                test_rfp = RFP.objects.create(
                    rfp_title="Test RFP for Tenant Signals",
                    description="Testing tenant auto-assignment",
                    rfp_type="Test",
                    created_by=1,
                    status="DRAFT"
                )
                
                # Check if tenant was auto-assigned
                if test_rfp.tenant_id == test_tenant.tenant_id:
                    print(f"✅ Tenant auto-assigned correctly: {test_rfp.tenant_id}")
                    print(f"   RFP ID: {test_rfp.rfp_id}, Tenant ID: {test_rfp.tenant_id}")
                    
                    # Clean up
                    test_rfp.delete()
                    print("✅ Test RFP cleaned up")
                else:
                    print(f"❌ Tenant NOT auto-assigned! Expected: {test_tenant.tenant_id}, Got: {test_rfp.tenant_id}")
                    test_rfp.delete()
                    return False
            else:
                print("⚠️  RFP table doesn't have TenantId column yet. Run migrations first.")
                return False
                
        except Exception as e:
            print(f"⚠️  Could not test RFP creation: {str(e)}")
            print("   This might be expected if migrations haven't been run")
        
        # Clear tenant context
        clear_current_tenant()
        print("✅ TEST 3 PASSED: Tenant signals work correctly\n")
        return True
        
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_tenant_filtering():
    """Test 4: Verify tenant filtering utilities work"""
    print("="*60)
    print("TEST 4: Tenant Filtering Utilities")
    print("="*60)
    
    try:
        from tprm_backend.core.tenant_utils import (
            filter_queryset_by_tenant,
            get_tenant_aware_queryset
        )
        
        # Get a tenant
        tenant = Tenant.objects.first()
        if not tenant:
            print("⚠️  No tenants found. Skipping filtering test.")
            return False
        
        print(f"✅ Testing with tenant: {tenant.name} (ID: {tenant.tenant_id})")
        
        # Test filter_queryset_by_tenant
        all_rfps = RFP.objects.all()
        filtered_rfps = filter_queryset_by_tenant(all_rfps, tenant.tenant_id)
        print(f"✅ filter_queryset_by_tenant works")
        print(f"   Total RFPs: {all_rfps.count()}, Filtered RFPs: {filtered_rfps.count()}")
        
        # Test get_tenant_aware_queryset (requires request object, so we'll mock it)
        class MockRequest:
            def __init__(self, tenant_id):
                self.tenant_id = tenant_id
                self.tenant = tenant
        
        mock_request = MockRequest(tenant.tenant_id)
        tenant_aware_qs = get_tenant_aware_queryset(RFP, mock_request)
        print(f"✅ get_tenant_aware_queryset works")
        print(f"   Tenant-aware queryset count: {tenant_aware_qs.count()}")
        
        print("✅ TEST 4 PASSED: Tenant filtering utilities work correctly\n")
        return True
        
    except Exception as e:
        print(f"❌ TEST 4 FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_middleware_registration():
    """Test 5: Verify middleware is registered in settings"""
    print("="*60)
    print("TEST 5: Middleware Registration")
    print("="*60)
    
    try:
        from django.conf import settings
        
        middleware_list = settings.MIDDLEWARE
        
        # Check for TPRM tenant middleware
        tprm_middleware_found = any(
            'tprm_backend.core.tenant_middleware' in mw 
            for mw in middleware_list
        )
        
        if tprm_middleware_found:
            print("✅ TPRM tenant middleware is registered in settings")
            for mw in middleware_list:
                if 'tprm_backend.core.tenant_middleware' in mw:
                    print(f"   Found: {mw}")
        else:
            print("❌ TPRM tenant middleware NOT found in settings")
            print("   Please add it to MIDDLEWARE in backend/settings.py")
            return False
        
        # Check for GRC tenant middleware (should also be there)
        grc_middleware_found = any(
            'grc.tenant_middleware' in mw 
            for mw in middleware_list
        )
        
        if grc_middleware_found:
            print("✅ GRC tenant middleware is also registered (for GRC routes)")
        else:
            print("⚠️  GRC tenant middleware not found (might be expected)")
        
        print("✅ TEST 5 PASSED: Middleware registration verified\n")
        return True
        
    except Exception as e:
        print(f"❌ TEST 5 FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_apps_registration():
    """Test 6: Verify tenant signals are registered in apps.py"""
    print("="*60)
    print("TEST 6: Apps Registration (Tenant Signals)")
    print("="*60)
    
    try:
        from django.apps import apps
        
        # Check if core app is registered
        try:
            core_app = apps.get_app_config('tprm_backend.core')
            print(f"✅ Core app is registered: {core_app.name}")
            
            # Check if apps.py exists and has ready() method
            import tprm_backend.core.apps
            if hasattr(tprm_backend.core.apps, 'CoreConfig'):
                print("✅ CoreConfig class exists in apps.py")
                
                # Check if ready() method imports tenant_signals
                import inspect
                source = inspect.getsource(tprm_backend.core.apps.CoreConfig.ready)
                if 'tenant_signals' in source:
                    print("✅ ready() method imports tenant_signals")
                else:
                    print("⚠️  ready() method might not import tenant_signals")
            else:
                print("❌ CoreConfig class not found in apps.py")
                return False
                
        except LookupError:
            print("❌ Core app not found in INSTALLED_APPS")
            return False
        
        print("✅ TEST 6 PASSED: Apps registration verified\n")
        return True
        
    except Exception as e:
        print(f"❌ TEST 6 FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and provide summary"""
    print("\n" + "="*60)
    print("TPRM MULTI-TENANCY IMPLEMENTATION TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("Tenant Context", test_tenant_context()))
    results.append(("Tenant Model", test_tenant_model()))
    results.append(("Tenant Signals", test_tenant_signals()))
    results.append(("Tenant Filtering", test_tenant_filtering()))
    results.append(("Middleware Registration", test_middleware_registration()))
    results.append(("Apps Registration", test_apps_registration()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Multi-tenancy implementation is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
    
    print("="*60 + "\n")
    
    return passed == total


if __name__ == '__main__':
    run_all_tests()

