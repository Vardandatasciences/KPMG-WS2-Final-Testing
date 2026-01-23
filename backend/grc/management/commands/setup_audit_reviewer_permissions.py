from django.core.management.base import BaseCommand
from grc.models import RBAC, Users
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Setup permissions for Audit Reviewer role to access compliance endpoints'

    def handle(self, *args, **options):
        try:
            # Find all users with Audit Reviewer role
            audit_reviewers = RBAC.objects.filter(role='Audit Reviewer', is_active='Y')
            
            if not audit_reviewers.exists():
                self.stdout.write(
                    self.style.WARNING('No Audit Reviewer users found in the system.')
                )
                return
            
            updated_count = 0
            
            for rbac_record in audit_reviewers:
                # Get the user details
                user = rbac_record.user
                
                self.stdout.write(f'Processing Audit Reviewer: {user.FirstName} {user.LastName} (ID: {user.UserId})')
                
                # Set compliance permissions that Audit Reviewers should have
                # They need view permissions to access compliance data for audit purposes
                rbac_record.view_all_compliance = True
                rbac_record.compliance_performance_analytics = True
                
                # They should also have view permissions for policies since they need to review compliance
                rbac_record.view_all_policy = True
                rbac_record.policy_performance_analytics = True
                
                # Save the changes
                rbac_record.save()
                updated_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Updated permissions for {user.FirstName} {user.LastName}'
                    )
                )
                
                # Log the changes
                logger.info(f'[RBAC SETUP] Updated Audit Reviewer permissions for user {user.UserId}: '
                          f'view_all_compliance=True, compliance_performance_analytics=True, '
                          f'view_all_policy=True, policy_performance_analytics=True')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated permissions for {updated_count} Audit Reviewer(s)'
                )
            )
            
            # Also create a general Audit Reviewer template if it doesn't exist
            self.create_audit_reviewer_template()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up Audit Reviewer permissions: {str(e)}')
            )
            logger.error(f'[RBAC SETUP] Error setting up Audit Reviewer permissions: {str(e)}')

    def create_audit_reviewer_template(self):
        """Create a template RBAC record for Audit Reviewer role with proper permissions"""
        try:
            # Check if we have any users to create a template from
            users = Users.objects.filter(is_active='Y').first()
            if not users:
                self.stdout.write(
                    self.style.WARNING('No active users found to create template.')
                )
                return
            
            # Create a template RBAC record for Audit Reviewer role
            template_rbac, created = RBAC.objects.get_or_create(
                role='Audit Reviewer',
                defaults={
                    'user': users,  # Use first user as placeholder
                    'username': 'audit_reviewer_template',
                    'is_active': 'N',  # Mark as inactive since it's just a template
                    
                    # Audit permissions (they should already have these)
                    'assign_audit': True,
                    'conduct_audit': False,  # Reviewers typically don't conduct audits
                    'review_audit': True,
                    'view_audit_reports': True,
                    'audit_performance_analytics': True,
                    
                    # Compliance permissions (needed for audit review)
                    'create_compliance': False,
                    'edit_compliance': False,
                    'approve_compliance': False,
                    'view_all_compliance': True,  # Need to view compliance for audit review
                    'compliance_performance_analytics': True,
                    
                    # Policy permissions (needed to understand what they're auditing)
                    'create_policy': False,
                    'edit_policy': False,
                    'approve_policy': False,
                    'create_framework': False,
                    'approve_framework': False,
                    'view_all_policy': True,  # Need to view policies for audit review
                    'policy_performance_analytics': True,
                    
                    # Risk permissions (minimal for audit review)
                    'create_risk': False,
                    'edit_risk': False,
                    'approve_risk': False,
                    'assign_risk': False,
                    'evaluate_assigned_risk': False,
                    'view_all_risk': True,  # May need to view risks during audit
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Created Audit Reviewer permission template')
                )
                logger.info('[RBAC SETUP] Created Audit Reviewer permission template')
            else:
                self.stdout.write(
                    self.style.SUCCESS('Audit Reviewer permission template already exists')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating Audit Reviewer template: {str(e)}')
            )
            logger.error(f'[RBAC SETUP] Error creating Audit Reviewer template: {str(e)}')
