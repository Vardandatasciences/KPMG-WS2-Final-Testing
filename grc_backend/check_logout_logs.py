"""
Check logout logs in grc_logs table
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import GRCLog
from django.utils import timezone

def check_logout_logs():
    """Check logout logs in grc_logs table"""
    
    print("=" * 80)
    print("CHECKING LOGOUT LOGS IN grc_logs TABLE")
    print("=" * 80)
    
    # Get current date/time
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = now - timedelta(days=1)
    
    # Check all-time logs
    all_logout_logs = GRCLog.objects.filter(
        Module='Authentication',
        ActionType='LOGOUT'
    ).count()
    
    # Check today's logs
    today_logout_logs = GRCLog.objects.filter(
        Module='Authentication',
        ActionType='LOGOUT',
        Timestamp__gte=today_start
    ).order_by('-Timestamp')
    
    # Check last 24 hours
    recent_logout_logs = GRCLog.objects.filter(
        Module='Authentication',
        ActionType='LOGOUT',
        Timestamp__gte=yesterday
    ).count()
    
    print(f"\n📊 Total logout logs (all time): {all_logout_logs}")
    print(f"📅 Logout logs today: {today_logout_logs.count()}")
    print(f"⏰ Logout logs (last 24 hours): {recent_logout_logs}\n")
    
    if today_logout_logs.count() > 0:
        print("Today's logout logs:")
        print("-" * 80)
        print(f"{'Timestamp':<25} {'User':<20} {'IP Address':<15} {'Description'}")
        print("-" * 80)
        for log in today_logout_logs[:20]:
            timestamp = log.Timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.Timestamp else 'N/A'
            username = log.UserName or 'N/A'
            ip = log.IPAddress or 'N/A'
            description = (log.Description or 'N/A')[:40]
            print(f"{timestamp:<25} {username:<20} {ip:<15} {description}")
    else:
        print("⚠️  NO LOGOUT LOGS FOUND FOR TODAY!")
    
    # Show last 10 logout logs regardless of date
    print("\n" + "=" * 80)
    print("LAST 10 LOGOUT LOGS (ANY DATE)")
    print("=" * 80)
    recent_logs = GRCLog.objects.filter(
        Module='Authentication',
        ActionType='LOGOUT'
    ).order_by('-Timestamp')[:10]
    
    if recent_logs.count() > 0:
        print(f"\n{'Timestamp':<25} {'User':<20} {'IP Address':<15} {'Description'}")
        print("-" * 80)
        for log in recent_logs:
            timestamp = log.Timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.Timestamp else 'N/A'
            username = log.UserName or 'N/A'
            ip = log.IPAddress or 'N/A'
            description = (log.Description or 'N/A')[:40]
            print(f"{timestamp:<25} {username:<20} {ip:<15} {description}")
    else:
        print("No logout logs found")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Total logout logs: {all_logout_logs}")
    print(f"📅 Today: {today_logout_logs.count()}")
    print(f"⏰ Last 24 hours: {recent_logout_logs}")
    print("=" * 80)
    
    if today_logout_logs.count() == 0:
        print("\n⚠️  No logout logs found for today.")
        print("   Try logging out and run this script again to verify logging works.")

if __name__ == '__main__':
    try:
        check_logout_logs()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


