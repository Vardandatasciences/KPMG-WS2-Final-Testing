#!/usr/bin/env python
"""
Change Management System - Quick Test Script
Verifies that all components are properly configured and working
"""

import os
import sys
import json
from pathlib import Path

# Add Django project to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

# Now import Django models and services
from grc.models import Framework
from grc.changeManagement.changemanagement import (
    get_change_management_service,
    scan_and_process_changes
)


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def print_status(emoji, text):
    """Print status message"""
    print(f"{emoji} {text}")


def test_directory_structure():
    """Test 1: Verify directory structure"""
    print_header("TEST 1: Directory Structure")
    
    service = get_change_management_service()
    data_dir = service.data_dir
    
    # Check data directory exists
    if data_dir.exists():
        print_status("✅", f"Data directory exists: {data_dir}")
    else:
        print_status("❌", f"Data directory missing: {data_dir}")
        return False
    
    # Check state files
    state_file = data_dir / "state.json"
    if state_file.exists():
        print_status("✅", "state.json exists")
    else:
        print_status("⚠️", "state.json not found (created by Selenium)")
    
    processed_file = data_dir / "processed_files.json"
    if processed_file.exists():
        print_status("✅", "processed_files.json exists")
    else:
        print_status("❌", "processed_files.json missing")
        return False
    
    # Count PDF files
    pdf_files = list(data_dir.glob("*.pdf")) + list(data_dir.glob("*.PDF"))
    print_status("📄", f"Found {len(pdf_files)} PDF file(s) in directory")
    
    return True


def test_database_connection():
    """Test 2: Verify database connection and Framework model"""
    print_header("TEST 2: Database Connection")
    
    try:
        # Try to query frameworks
        frameworks = Framework.objects.all()
        count = frameworks.count()
        
        print_status("✅", f"Database connection successful")
        print_status("📊", f"Found {count} framework(s) in database")
        
        # List frameworks
        if count > 0:
            print("\nFrameworks:")
            for fw in frameworks[:5]:  # Show first 5
                print(f"  - ID {fw.FrameworkId}: {fw.FrameworkName}")
                
                # Check Amendment column
                if hasattr(fw, 'Amendment'):
                    if fw.Amendment:
                        print(f"    └─ Has {len(fw.Amendment)} amendment(s)")
                    else:
                        print(f"    └─ No amendments yet")
                else:
                    print_status("❌", "Amendment column not found!")
                    return False
        else:
            print_status("⚠️", "No frameworks in database - add some frameworks first")
        
        return True
        
    except Exception as e:
        print_status("❌", f"Database error: {str(e)}")
        return False


def test_s3_service():
    """Test 3: Verify S3 service connection"""
    print_header("TEST 3: S3 Service Connection")
    
    try:
        service = get_change_management_service()
        
        if service.s3_client:
            print_status("✅", "S3 client initialized")
            
            # Test connection
            result = service.s3_client.test_connection()
            
            if result.get('overall_success'):
                print_status("✅", "S3 service connection successful")
                print_status("🌐", f"Direct URL: {service.s3_client.api_base_url}")
                return True
            else:
                print_status("❌", "S3 service connection failed")
                print(f"Details: {result}")
                return False
        else:
            print_status("❌", "S3 client not initialized")
            return False
            
    except Exception as e:
        print_status("❌", f"S3 service error: {str(e)}")
        return False


def test_framework_detection():
    """Test 4: Test framework detection logic"""
    print_header("TEST 4: Framework Detection")
    
    service = get_change_management_service()
    
    # Test with sample filenames
    test_files = [
        ("SP800-53_20241112_112130.pdf", "NIST"),
        ("PCI_DSS_1.pdf", "PCI"),
        ("ISO27001_audit.pdf", "ISO"),
        ("unknown_framework.pdf", "Unknown")
    ]
    
    all_passed = True
    for filename, expected in test_files:
        # Create dummy file path
        file_path = Path(filename)
        framework = service.identify_framework(file_path)
        
        if framework:
            if expected == "Unknown":
                print_status("⚠️", f"{filename} → Detected: {framework.FrameworkName} (expected Unknown)")
            else:
                print_status("✅", f"{filename} → Detected: {framework.FrameworkName}")
        else:
            if expected == "Unknown":
                print_status("✅", f"{filename} → Not detected (as expected)")
            else:
                print_status("❌", f"{filename} → Detection failed (expected {expected})")
                all_passed = False
    
    return all_passed


def test_pdf_processing():
    """Test 5: Test PDF processing (if PDFs available)"""
    print_header("TEST 5: PDF Processing Test")
    
    service = get_change_management_service()
    pdf_files = list(service.data_dir.glob("*.pdf")) + list(service.data_dir.glob("*.PDF"))
    
    if not pdf_files:
        print_status("⚠️", "No PDF files to test - add a PDF to data/ directory")
        print_status("ℹ️", "You can run: python selimium.py to download a test PDF")
        return None  # Neither pass nor fail
    
    print_status("📄", f"Testing with {len(pdf_files)} PDF file(s)")
    
    try:
        # Run scan
        print_status("🔄", "Running scan...")
        result = scan_and_process_changes("test_system")
        
        print(f"\nResults:")
        print(f"  Files found: {result.get('files_found', 0)}")
        print(f"  Files processed: {result.get('files_processed', 0)}")
        print(f"  Files skipped: {result.get('files_skipped', 0)}")
        print(f"  Files failed: {result.get('files_failed', 0)}")
        
        if result.get('errors'):
            print(f"\nErrors:")
            for error in result['errors']:
                print(f"  - {error['file']}: {error['error']}")
        
        if result.get('files_processed', 0) > 0 or result.get('files_skipped', 0) > 0:
            print_status("✅", "PDF processing successful")
            return True
        elif result.get('files_failed', 0) > 0:
            print_status("❌", "PDF processing failed")
            return False
        else:
            print_status("⚠️", "No files were processed")
            return None
            
    except Exception as e:
        print_status("❌", f"Processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and show summary"""
    print("\n" + "🚀 " + "="*58)
    print("  CHANGE MANAGEMENT SYSTEM - TEST SUITE")
    print("="*60 + "\n")
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Database Connection", test_database_connection),
        ("S3 Service", test_s3_service),
        ("Framework Detection", test_framework_detection),
        ("PDF Processing", test_pdf_processing),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print_status("❌", f"Test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    total = len(results)
    
    for test_name, result in results.items():
        if result is True:
            print_status("✅", f"{test_name}: PASSED")
        elif result is False:
            print_status("❌", f"{test_name}: FAILED")
        else:
            print_status("⏭️", f"{test_name}: SKIPPED")
    
    print(f"\n{'='*60}")
    print(f"Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print(f"{'='*60}\n")
    
    if failed == 0 and passed > 0:
        print("🎉 All tests passed! System is ready to use.")
        return 0
    elif failed > 0:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1
    else:
        print("ℹ️ Tests completed with skipped items. Review results above.")
        return 0


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

