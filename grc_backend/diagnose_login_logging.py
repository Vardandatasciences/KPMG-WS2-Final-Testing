"""
Comprehensive diagnostic script to check login logging functionality
This will help identify why login logs might not be saving
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import GRCLog, Framework, Users
from datetime import datetime, timedelta

def diagnose_login_logging():
    """Comprehensive diagnosis of login logging"""
    
    print("=" * 80)
    print("LOGIN LOGGING DIAGNOSTIC REPORT")
    print("=" * 80)
    
    # 1. Check if ANY login logs exist (all time)
    print("\n1. CHECKING ALL LOGIN LOGS (ALL TIME)")
    print("-" * 80)
    all_login_logs = GRCLog.objects.filter(
        Module='Authentication',
        ActionType__in=['LOGIN_SUCCESS', 'LOGIN_FAILED']
    ).count()
    
    print(f"   Total login logs in database: {all_login_logs}")
    
    if all_login_logs > 0:
        # Show most recent ones
        recent_logs = GRCLog.objects.filter(
            Module='Authentication',
            ActionType__in=['LOGIN_SUCCESS', 'LOGIN_FAILED']
        ).order_by('-Timestamp')[:5]
        
        print(f"\n   Most recent {len(recent_logs)} login logs:")
        for log in recent_logs:
            timestamp = log.Timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.Timestamp else 'N/A'
            print(f"   - {timestamp} | {log.ActionType} | {log.UserName} | {log.IPAddress}")
    else:
        print("   ⚠️  NO LOGIN LOGS FOUND IN DATABASE!")
    
    # 2. Check for logging errors
    print("\n2. CHECKING FOR LOGGING ERRORS")
    print("-" * 80)
    error_logs = GRCLog.objects.filter(
        Module='Authentication',
        ActionType='LOG_ERROR'
    ).order_by('-Timestamp')[:5]
    
    if error_logs.count() > 0:
        print(f"   ⚠️  Found {error_logs.count()} logging errors:")
        for log in error_logs:
            timestamp = log.Timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.Timestamp else 'N/A'
            print(f"   - {timestamp}: {log.Description}")
    else:
        print("   ✅ No logging errors found")
    
    # 3. Check Framework availability (CRITICAL - required for logging)
    print("\n3. CHECKING FRAMEWORK AVAILABILITY")
    print("-" * 80)
    frameworks = Framework.objects.all()
    active_frameworks = Framework.objects.filter(ActiveInactive='Active')
    approved_frameworks = Framework.objects.filter(Status='Approved', ActiveInactive='Active')
    
    print(f"   Total frameworks: {frameworks.count()}")
    print(f"   Active frameworks: {active_frameworks.count()}")
    print(f"   Approved & Active frameworks: {approved_frameworks.count()}")
    
    if frameworks.count() == 0:
        print("   ❌ CRITICAL: NO FRAMEWORKS IN DATABASE!")
        print("      Login logs CANNOT be saved without a FrameworkId")
        print("      This is likely why login logging is failing!")
    elif approved_frameworks.count() == 0:
        print("   ⚠️  WARNING: No approved & active frameworks")
        print("      The logging service will use any available framework as fallback")
        if frameworks.count() > 0:
            first_framework = frameworks.first()
            print(f"      Fallback framework: ID={first_framework.FrameworkId}, Name={first_framework.FrameworkName}")
    else:
        first_approved = approved_frameworks.first()
        print(f"   ✅ Framework available: ID={first_approved.FrameworkId}, Name={first_approved.FrameworkName}")
    
    # 4. Check recent authentication logs (any type)
    print("\n4. CHECKING ALL AUTHENTICATION MODULE LOGS")
    print("-" * 80)
    all_auth_logs = GRCLog.objects.filter(Module='Authentication').order_by('-Timestamp')[:10]
    
    if all_auth_logs.count() > 0:
        print(f"   Found {all_auth_logs.count()} recent authentication logs:")
        for log in all_auth_logs:
            timestamp = log.Timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.Timestamp else 'N/A'
            action = log.ActionType or 'N/A'
            print(f"   - {timestamp} | {action} | {log.UserName or 'N/A'}")
    else:
        print("   ⚠️  No authentication logs found at all")
    
    # 5. Check if users exist
    print("\n5. CHECKING USER DATABASE")
    print("-" * 80)
    total_users = Users.objects.count()
    active_users = Users.objects.filter(IsActive='Y').count()
    
    print(f"   Total users: {total_users}")
    print(f"   Active users: {active_users}")
    
    if total_users == 0:
        print("   ⚠️  No users in database")
    else:
        # Show a few sample users
        sample_users = Users.objects.all()[:3]
        print(f"\n   Sample users:")
        for user in sample_users:
            framework_info = f"Framework: {user.FrameworkId.FrameworkId}" if user.FrameworkId else "No Framework"
            print(f"   - User ID: {user.UserId}, Username: {user.UserName}, {framework_info}")
    
    # 6. Test logging functionality
    print("\n6. TESTING LOGGING FUNCTIONALITY")
    print("-" * 80)
    try:
        from grc.routes.Global.logging_service import send_log
        
        # Try to get a framework for testing
        test_framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
        if not test_framework:
            test_framework = Framework.objects.first()
        
        if test_framework:
            print(f"   Attempting to create a test log entry...")
            test_log_id = send_log(
                module='Authentication',
                actionType='LOGIN_TEST',
                description='Test login log entry to verify logging functionality',
                userId='TEST',
                userName='TEST_USER',
                logLevel='INFO',
                ipAddress='127.0.0.1',
                additionalInfo={'test': True},
                frameworkId=test_framework.FrameworkId
            )
            
            if test_log_id:
                print(f"   ✅ SUCCESS: Test log created with ID: {test_log_id}")
                # Clean up test log
                try:
                    GRCLog.objects.filter(LogId=test_log_id).delete()
                    print(f"   ✅ Test log cleaned up")
                except:
                    pass
            else:
                print(f"   ❌ FAILED: Could not create test log (returned None)")
        else:
            print(f"   ❌ SKIPPED: No framework available for testing")
    except Exception as e:
        print(f"   ❌ ERROR testing logging: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 7. Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if frameworks.count() == 0:
        print("❌ CRITICAL: Create at least one Framework in the database")
        print("   Login logs require a FrameworkId to be saved")
    elif all_login_logs == 0:
        print("⚠️  No login logs found. Possible reasons:")
        print("   1. No one has logged in yet")
        print("   2. Try logging in now and run this script again")
        print("   3. Check Django server logs for errors during login")
        print("   4. Verify the login endpoint is calling send_log()")
    else:
        print("✅ Login logging appears to be working!")
        print("   If you're not seeing recent logs, users may not have logged in recently")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        diagnose_login_logging()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

