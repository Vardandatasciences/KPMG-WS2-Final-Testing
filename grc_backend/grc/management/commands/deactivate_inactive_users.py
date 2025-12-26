"""
Management command to automatically deactivate users who haven't logged in for a specified number of days.

This command can be scheduled to run periodically (e.g., via cron or Windows Task Scheduler)
to automatically mark inactive users as inactive in the system.

Usage:
    python manage.py deactivate_inactive_users
    python manage.py deactivate_inactive_users --days 90
    python manage.py deactivate_inactive_users --days 60 --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from grc.models import Users, GRCLog, Framework
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Deactivate users who have not logged in for a specified number of days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=getattr(settings, 'USER_INACTIVITY_DAYS', 90),
            help='Number of days of inactivity before deactivating a user (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually deactivating users'
        )
        parser.add_argument(
            '--exclude-never-logged-in',
            action='store_true',
            help='Exclude users who have never logged in from deactivation'
        )

    def handle(self, *args, **options):
        inactivity_days = options['days']
        dry_run = options['dry_run']
        exclude_never_logged_in = options['exclude_never_logged_in']
        
        self.stdout.write(self.style.SUCCESS(
            f'Starting inactive user deactivation process...'
        ))
        self.stdout.write(f'Inactivity threshold: {inactivity_days} days')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Calculate the cutoff date
        cutoff_date = timezone.now() - timedelta(days=inactivity_days)
        self.stdout.write(f'Cutoff date: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Find inactive users
        # Users are considered inactive if:
        # 1. They are currently active (IsActive='Y')
        # 2. Their last_login is before the cutoff date OR they have never logged in (unless excluded)
        
        active_users = Users.objects.filter(IsActive='Y')
        
        users_to_deactivate = []
        for user in active_users:
            should_deactivate = False
            reason = ""
            
            if user.last_login is None:
                if not exclude_never_logged_in:
                    should_deactivate = True
                    reason = "Never logged in"
            elif user.last_login < cutoff_date:
                should_deactivate = True
                days_since_login = (timezone.now() - user.last_login).days
                reason = f"Last login: {user.last_login.strftime('%Y-%m-%d')} ({days_since_login} days ago)"
            
            if should_deactivate:
                users_to_deactivate.append({
                    'user': user,
                    'reason': reason
                })
        
        if not users_to_deactivate:
            self.stdout.write(self.style.SUCCESS(
                f'No users found with inactivity >= {inactivity_days} days'
            ))
            return
        
        self.stdout.write(self.style.WARNING(
            f'\nFound {len(users_to_deactivate)} user(s) to deactivate:'
        ))
        self.stdout.write('-' * 80)
        
        deactivated_count = 0
        
        for item in users_to_deactivate:
            user = item['user']
            reason = item['reason']
            
            self.stdout.write(
                f'User ID: {user.UserId}, Username: {user.UserName}, '
                f'Email: {user.Email}, {reason}'
            )
            
            if not dry_run:
                try:
                    # Deactivate the user
                    user.IsActive = 'N'
                    user.save(update_fields=['IsActive'])
                    deactivated_count += 1
                    
                    # Log the deactivation
                    self._log_deactivation(user, reason, inactivity_days)
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ Deactivated user {user.UserName} (ID: {user.UserId})'
                    ))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'  ✗ Error deactivating user {user.UserName} (ID: {user.UserId}): {str(e)}'
                    ))
                    logger.error(f'Error deactivating user {user.UserId}: {str(e)}')
        
        self.stdout.write('-' * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\nDRY RUN: Would have deactivated {len(users_to_deactivate)} user(s)'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\nSuccessfully deactivated {deactivated_count} user(s)'
            ))
            
            if deactivated_count < len(users_to_deactivate):
                self.stdout.write(self.style.WARNING(
                    f'Failed to deactivate {len(users_to_deactivate) - deactivated_count} user(s)'
                ))

    def _log_deactivation(self, user, reason, inactivity_days):
        """Log the user deactivation to GRCLog"""
        try:
            # Get a default framework for logging
            framework = Framework.objects.filter(ActiveInactive='Active').first()
            if not framework:
                framework = Framework.objects.first()
            
            if framework:
                log_entry = GRCLog(
                    Module='User Management',
                    ActionType='USER_DEACTIVATED',
                    Description=f'User {user.UserName} (ID: {user.UserId}) automatically deactivated due to inactivity',
                    UserId=str(user.UserId),
                    UserName=user.UserName,
                    LogLevel='INFO',
                    IPAddress='system',
                    FrameworkId=framework,
                    AdditionalInfo={
                        'reason': reason,
                        'inactivity_days_threshold': inactivity_days,
                        'deactivation_type': 'automatic',
                        'last_login': user.last_login.isoformat() if user.last_login else None,
                        'email': user.Email
                    }
                )
                log_entry.save()
                logger.info(f'Logged deactivation for user {user.UserId} to grc_logs')
        except Exception as log_error:
            logger.error(f'Error logging deactivation for user {user.UserId}: {str(log_error)}')

