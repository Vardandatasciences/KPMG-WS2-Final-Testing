from django.core.management.base import BaseCommand
from django.db import transaction
from grc.models import RBAC, Users
import logging
from django.db import models

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Set up RBAC permissions for users based on their roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Specific username to update permissions for'
        )
        parser.add_argument(
            '--role',
            type=str,
            help='Specific role to update permissions for'
        )
        parser.add_argument(
            '--grant-approve-policy',
            action='store_true',
            help='Grant approve_policy permission to users with appropriate roles'
        )

    def handle(self, *args, **options):
        try:
            if options['grant_approve_policy']:
                self.grant_approve_policy_permissions(
                    username=options.get('username'),
                    role=options.get('role')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'No action specified. Use --grant-approve-policy to grant approve_policy permissions.'
                    )
                )
        except Exception as e:
            logger.error(f"Error in setup_rbac_permissions: {e}")
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )

    def grant_approve_policy_permissions(self, username=None, role=None):
        """Grant approve_policy permission to users with appropriate roles"""
        
        # Define which roles should have approve_policy permission
        APPROVE_POLICY_ROLES = [
            'GRC Administrator',
            'Policy Manager',
            'Policy Approver',
            'Compliance Manager',
            'Compliance Approver',
            'Executive/Senior Management'
        ]
        
        # Build the query
        query = RBAC.objects.filter(is_active='Y')
        
        if username:
            query = query.filter(username=username)
        elif role:
            query = query.filter(role=role)
        else:
            # If no specific user/role, apply to all users with appropriate roles
            query = query.filter(role__in=APPROVE_POLICY_ROLES)
        
        # Get users who need approve_policy permission
        users_to_update = query.filter(approve_policy=False)
        
        if not users_to_update.exists():
            self.stdout.write(
                self.style.SUCCESS('No users found that need approve_policy permission.')
            )
            return
        
        self.stdout.write(f"Found {users_to_update.count()} users to update...")
        
        updated_count = 0
        with transaction.atomic():
            for rbac_record in users_to_update:
                old_permission = rbac_record.approve_policy
                rbac_record.approve_policy = True
                rbac_record.save()
                
                self.stdout.write(
                    f"Updated {rbac_record.username} ({rbac_record.role}): "
                    f"approve_policy {old_permission} -> {rbac_record.approve_policy}"
                )
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} users with approve_policy permission.'
            )
        )
        
        # Show summary of current permissions
        self.show_permission_summary()

    def show_permission_summary(self):
        """Show a summary of current RBAC permissions"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("RBAC PERMISSIONS SUMMARY")
        self.stdout.write("="*60)
        
        # Count users by role with approve_policy permission
        role_counts = RBAC.objects.filter(
            is_active='Y',
            approve_policy=True
        ).values('role').annotate(
            count=models.Count('rbac_id')
        ).order_by('role')
        
        for role_count in role_counts:
            self.stdout.write(
                f"{role_count['role']}: {role_count['count']} users with approve_policy"
            )
        
        # Show users without approve_policy permission
        users_without_approve = RBAC.objects.filter(
            is_active='Y',
            approve_policy=False
        ).values('username', 'role')
        
        if users_without_approve.exists():
            self.stdout.write("\nUsers WITHOUT approve_policy permission:")
            for user in users_without_approve:
                self.stdout.write(f"  - {user['username']} ({user['role']})")
        else:
            self.stdout.write("\nAll active users have approve_policy permission!")
        
        self.stdout.write("="*60)
