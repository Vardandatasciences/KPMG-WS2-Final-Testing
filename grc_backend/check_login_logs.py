"""
Script to check if login logs are being saved to grc_logs table
Run this script to verify login logging is working
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import GRCLog
from datetime import datetime, timedelta

def check_login_logs():
    """Check recent login logs in grc_logs table"""
    
    print("=" * 80)
    print("CHECKING LOGIN LOGS IN grc_logs TABLE")
    print("=" * 80)
    
    # Get logs from last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    
    # Check all-time logs first
    all_time_logs = GRCLog.objects.filter(
        Module='Authentication',
        ActionType__in=['LOGIN_SUCCESS', 'LOGIN_FAILED']
    ).count()
    
    # Get recent login-related logs (last 24 hours)
    login_logs = GRCLog.objects.filter(
        Module='Authentication',
        ActionType__in=['LOGIN_SUCCESS', 'LOGIN_FAILED'],
        Timestamp__gte=yesterday
    ).order_by('-Timestamp')[:20]
    
    print(f"\n📊 Total login logs (all time): {all_time_logs}")
    print(f"📅 Login logs in last 24 hours: {login_logs.count()}\n")
    
    # Check for successful vs failed
    all_success = GRCLog.objects.filter(
        Module='Authentication',
        ActionType='LOGIN_SUCCESS'
    ).count()
    
    all_failed = GRCLog.objects.filter(
        Module='Authentication',
        ActionType='LOGIN_FAILED'
    ).count()
    
    print(f"✅ Successful logins (all time): {all_success}")
    print(f"❌ Failed logins (all time): {all_failed}\n")
    
    if login_logs.count() == 0 and all_time_logs == 0:
        print("⚠️  NO LOGIN LOGS FOUND!")
        print("\nThis could mean:")
        print("1. No one has logged in yet")
        print("2. Login logging is not working (check for errors)")
        print("3. FrameworkId is missing (required field)")
        return
    elif all_success == 0 and all_failed > 0:
        print("⚠️  WARNING: Only failed login logs found, no successful logins!")
        print("   This could mean:")
        print("   1. Users haven't successfully logged in yet")
        print("   2. Successful login logging might have an issue")
        print("   3. Check if login endpoint is being called correctly\n")
    
    # If no recent logs but there are all-time logs, show those instead
    if login_logs.count() == 0 and all_time_logs > 0:
        print("📋 Showing all-time login logs (no recent logs found):\n")
        login_logs = GRCLog.objects.filter(
            Module='Authentication',
            ActionType__in=['LOGIN_SUCCESS', 'LOGIN_FAILED']
        ).order_by('-Timestamp')[:20]
    
    print(f"{'Timestamp':<20} {'Action':<15} {'User':<20} {'IP Address':<15} {'Description'}")
    print("-" * 100)
    
    for log in login_logs:
        timestamp = log.Timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.Timestamp else 'N/A'
        action = log.ActionType or 'N/A'
        username = log.UserName or 'N/A'
        ip = log.IPAddress or 'N/A'
        description = (log.Description or 'N/A')[:50]
        
        print(f"{timestamp:<20} {action:<15} {username:<20} {ip:<15} {description}")
    
    # Summary statistics (last 24 hours)
    success_count_24h = GRCLog.objects.filter(
        Module='Authentication',
        ActionType='LOGIN_SUCCESS',
        Timestamp__gte=yesterday
    ).count()
    
    failed_count_24h = GRCLog.objects.filter(
        Module='Authentication',
        ActionType='LOGIN_FAILED',
        Timestamp__gte=yesterday
    ).count()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("Last 24 hours:")
    print(f"  ✅ Successful Logins: {success_count_24h}")
    print(f"  ❌ Failed Logins: {failed_count_24h}")
    print(f"  📊 Total: {success_count_24h + failed_count_24h}")
    print("\nAll time:")
    print(f"  ✅ Successful Logins: {all_success}")
    print(f"  ❌ Failed Logins: {all_failed}")
    print(f"  📊 Total: {all_time_logs}")
    print("=" * 80)
    
    # Check for any logging errors
    error_logs = GRCLog.objects.filter(
        Module='Authentication',
        ActionType='LOG_ERROR',
        Timestamp__gte=yesterday
    ).count()
    
    if error_logs > 0:
        print(f"\n⚠️  WARNING: Found {error_logs} logging errors!")
        print("   Check the Description field for details.")

if __name__ == '__main__':
    try:
        check_login_logs()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

