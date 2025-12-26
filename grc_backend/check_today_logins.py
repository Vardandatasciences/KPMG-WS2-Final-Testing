"""
Check today's login logs specifically
"""

import os
import sys
import django
from datetime import datetime, timedelta, date

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import GRCLog, Framework
from django.utils import timezone

def check_today_logins():
    """Check login logs for today"""
    
    print("=" * 80)
    print("CHECKING TODAY'S LOGIN LOGS")
    print("=" * 80)
    
    # Get current date/time
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"\nCurrent server time: {now}")
    print(f"Today start: {today_start}\n")
    
    # Check all authentication logs from today
    today_logs = GRCLog.objects.filter(
        Module='Authentication',
        Timestamp__gte=today_start
    ).order_by('-Timestamp')
    
    print(f"📊 Total authentication logs today: {today_logs.count()}\n")
    
    # Filter by action type
    success_today = today_logs.filter(ActionType='LOGIN_SUCCESS').count()
    failed_today = today_logs.filter(ActionType='LOGIN_FAILED').count()
    error_today = today_logs.filter(ActionType='LOG_ERROR').count()
    
    print(f"✅ Successful logins today: {success_today}")
    print(f"❌ Failed logins today: {failed_today}")
    print(f"⚠️  Logging errors today: {error_today}\n")
    
    if today_logs.count() > 0:
        print("Today's authentication logs:")
        print("-" * 80)
        print(f"{'Timestamp':<25} {'Action':<20} {'User':<20} {'IP':<15}")
        print("-" * 80)
        for log in today_logs[:20]:
            timestamp = log.Timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.Timestamp else 'N/A'
            action = log.ActionType or 'N/A'
            username = log.UserName or 'N/A'
            ip = log.IPAddress or 'N/A'
            print(f"{timestamp:<25} {action:<20} {username:<20} {ip:<15}")
    else:
        print("⚠️  NO LOGS FOUND FOR TODAY!")
    
    # Check last 10 logs regardless of date
    print("\n" + "=" * 80)
    print("LAST 10 AUTHENTICATION LOGS (ANY DATE)")
    print("=" * 80)
    recent_logs = GRCLog.objects.filter(
        Module='Authentication'
    ).order_by('-Timestamp')[:10]
    
    if recent_logs.count() > 0:
        print(f"\n{'Timestamp':<25} {'Action':<20} {'User':<20} {'IP':<15}")
        print("-" * 80)
        for log in recent_logs:
            timestamp = log.Timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.Timestamp else 'N/A'
            action = log.ActionType or 'N/A'
            username = log.UserName or 'N/A'
            ip = log.IPAddress or 'N/A'
            print(f"{timestamp:<25} {action:<20} {username:<20} {ip:<15}")
    else:
        print("No authentication logs found")
    
    # Check for any LOG_ERROR entries that might indicate logging failures
    print("\n" + "=" * 80)
    print("CHECKING FOR LOGGING ERRORS")
    print("=" * 80)
    error_logs = GRCLog.objects.filter(
        Module='Authentication',
        ActionType='LOG_ERROR'
    ).order_by('-Timestamp')[:5]
    
    if error_logs.count() > 0:
        print(f"\n⚠️  Found {error_logs.count()} logging errors:")
        for log in error_logs:
            timestamp = log.Timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.Timestamp else 'N/A'
            print(f"\n  {timestamp}:")
            print(f"  Description: {log.Description}")
    else:
        print("✅ No logging errors found")
    
    # Check framework availability
    print("\n" + "=" * 80)
    print("FRAMEWORK CHECK")
    print("=" * 80)
    frameworks = Framework.objects.all()
    active_frameworks = Framework.objects.filter(ActiveInactive='Active', Status='Approved')
    
    print(f"Total frameworks: {frameworks.count()}")
    print(f"Active & Approved frameworks: {active_frameworks.count()}")
    
    if active_frameworks.count() > 0:
        first_fw = active_frameworks.first()
        print(f"✅ Framework available: ID={first_fw.FrameworkId}, Name={first_fw.FrameworkName}")
    else:
        print("⚠️  No active & approved frameworks found")
        if frameworks.count() > 0:
            first_fw = frameworks.first()
            print(f"   Using fallback: ID={first_fw.FrameworkId}, Name={first_fw.FrameworkName}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if today_logs.count() == 0:
        print("❌ No logs found for today. Possible issues:")
        print("   1. Login logging code is not being executed")
        print("   2. Errors are being silently caught")
        print("   3. FrameworkId is missing (required field)")
        print("   4. Database connection issue")
        print("\n   ACTION: Check Django server logs for:")
        print("   - '🔍 Attempting to log successful login'")
        print("   - '✅ Successfully saved log entry'")
        print("   - '❌ Error logging successful JWT login'")
    else:
        if success_today == 0 and failed_today > 0:
            print("⚠️  Only failed logins found today - successful logins not being logged")
        elif success_today > 0:
            print("✅ Login logging is working!")
    
    print("=" * 80)

if __name__ == '__main__':
    try:
        check_today_logins()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


