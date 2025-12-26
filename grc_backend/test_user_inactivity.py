"""
Test script for user inactivity auto-deactivation feature.

This script tests the implementation of automatic user deactivation
based on inactivity periods.

Usage:
    python test_user_inactivity.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from grc.models import Users, GRCLog


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def test_last_login_field():
    """Test that last_login field exists and is accessible"""
    print_header("Test 1: Verify last_login field exists")
    
    try:
        # Try to access the last_login field
        user = Users.objects.first()
        if user:
            print(f"✓ last_login field exists")
            print(f"  Sample user: {user.UserName} (ID: {user.UserId})")
            print(f"  Last login: {user.last_login if user.last_login else 'Never logged in'}")
            return True
        else:
            print("⚠ No users found in database")
            return False
    except AttributeError as e:
        print(f"✗ last_login field does not exist: {e}")
        print("  Please run: python manage.py migrate grc")
        return False
    except Exception as e:
        print(f"✗ Error accessing last_login field: {e}")
        return False


def test_user_statistics():
    """Display statistics about user login activity"""
    print_header("Test 2: User Login Statistics")
    
    try:
        total_users = Users.objects.count()
        active_users = Users.objects.filter(IsActive='Y').count()
        inactive_users = Users.objects.filter(IsActive='N').count()
        
        users_with_login = Users.objects.filter(last_login__isnull=False).count()
        users_without_login = Users.objects.filter(last_login__isnull=True).count()
        
        print(f"Total Users: {total_users}")
        print(f"  Active: {active_users}")
        print(f"  Inactive: {inactive_users}")
        print(f"\nLogin History:")
        print(f"  Users with login history: {users_with_login}")
        print(f"  Users who never logged in: {users_without_login}")
        
        # Calculate inactivity statistics
        cutoff_dates = [30, 60, 90, 180]
        print(f"\nInactivity Analysis (Active Users Only):")
        
        for days in cutoff_dates:
            cutoff = timezone.now() - timedelta(days=days)
            inactive_for_period = Users.objects.filter(
                IsActive='Y',
                last_login__lt=cutoff
            ).count()
            print(f"  Users inactive for {days}+ days: {inactive_for_period}")
        
        return True
    except Exception as e:
        print(f"✗ Error getting statistics: {e}")
        return False


def test_find_inactive_users(days=90):
    """Find users who would be deactivated"""
    print_header(f"Test 3: Find Users Inactive for {days}+ Days")
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Find active users with old last_login
        inactive_users = Users.objects.filter(
            IsActive='Y',
            last_login__lt=cutoff_date
        ).order_by('last_login')
        
        # Find active users who never logged in
        never_logged_in = Users.objects.filter(
            IsActive='Y',
            last_login__isnull=True
        )
        
        print(f"\nActive users with no activity for {days}+ days: {inactive_users.count()}")
        
        if inactive_users.exists():
            print("\nTop 10 inactive users:")
            print("-" * 80)
            for user in inactive_users[:10]:
                days_since_login = (timezone.now() - user.last_login).days
                print(f"  ID: {user.UserId:5} | {user.UserName:20} | "
                      f"Last: {user.last_login.strftime('%Y-%m-%d'):12} | "
                      f"{days_since_login:4} days ago")
        else:
            print("  No users found with this inactivity period.")
        
        print(f"\nActive users who never logged in: {never_logged_in.count()}")
        
        if never_logged_in.exists():
            print("\nFirst 10 users who never logged in:")
            print("-" * 80)
            for user in never_logged_in[:10]:
                print(f"  ID: {user.UserId:5} | {user.UserName:20} | Email: {user.Email}")
        
        return True
    except Exception as e:
        print(f"✗ Error finding inactive users: {e}")
        return False


def test_deactivation_logs():
    """Check if deactivation logs exist"""
    print_header("Test 4: Check Deactivation Logs")
    
    try:
        deactivation_logs = GRCLog.objects.filter(
            ActionType='USER_DEACTIVATED'
        ).order_by('-Timestamp')[:10]
        
        if deactivation_logs.exists():
            print(f"Found {deactivation_logs.count()} recent deactivation log(s):")
            print("-" * 80)
            for log in deactivation_logs:
                print(f"  {log.Timestamp.strftime('%Y-%m-%d %H:%M')} | "
                      f"{log.UserName:20} | {log.Description}")
        else:
            print("No deactivation logs found yet.")
            print("This is normal if you haven't run the deactivation command yet.")
        
        return True
    except Exception as e:
        print(f"✗ Error checking logs: {e}")
        return False


def test_recent_logins():
    """Show most recent logins"""
    print_header("Test 5: Recent Login Activity")
    
    try:
        recent_logins = Users.objects.filter(
            last_login__isnull=False
        ).order_by('-last_login')[:10]
        
        if recent_logins.exists():
            print("Top 10 most recent logins:")
            print("-" * 80)
            for user in recent_logins:
                time_ago = timezone.now() - user.last_login
                days_ago = time_ago.days
                hours_ago = time_ago.seconds // 3600
                
                if days_ago > 0:
                    ago_str = f"{days_ago} day(s) ago"
                elif hours_ago > 0:
                    ago_str = f"{hours_ago} hour(s) ago"
                else:
                    ago_str = "Less than 1 hour ago"
                
                status = "Active" if user.IsActive == 'Y' else "Inactive"
                print(f"  {user.UserName:20} | "
                      f"{user.last_login.strftime('%Y-%m-%d %H:%M'):17} | "
                      f"{ago_str:20} | {status}")
        else:
            print("No users with login history found.")
        
        return True
    except Exception as e:
        print(f"✗ Error checking recent logins: {e}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("+" + "=" * 78 + "+")
    print("|" + " " * 20 + "USER INACTIVITY TEST SUITE" + " " * 32 + "|")
    print("+" + "=" * 78 + "+")
    
    tests = [
        test_last_login_field,
        test_user_statistics,
        lambda: test_find_inactive_users(90),
        test_deactivation_logs,
        test_recent_logins,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print_header("Test Summary")
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        print("\nNext steps:")
        print("  1. Run migration: python manage.py migrate grc")
        print("  2. Test deactivation (dry-run): python manage.py deactivate_inactive_users --dry-run")
        print("  3. Check the USER_INACTIVITY_IMPLEMENTATION.md file for detailed usage instructions")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("  - Migration not applied: python manage.py migrate grc")
        print("  - Database connection issues")
        print("  - Model changes not reflected")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    main()

