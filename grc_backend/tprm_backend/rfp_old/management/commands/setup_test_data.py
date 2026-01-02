"""
Django management command to set up test data for RFP approval system
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from rfp.models import CustomUser
from rfp_approval.models import ApprovalWorkflows, ApprovalStages, ApprovalRequests
import uuid


class Command(BaseCommand):
    help = 'Set up test data for RFP approval system'

    def handle(self, *args, **options):
        try:
            # Create test users
            self.create_test_users()
            
            # Create test approval workflow
            self.create_test_workflow()
            
            self.stdout.write(self.style.SUCCESS('✅ Test data created successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating test data: {e}'))
            raise

    def create_test_users(self):
        """Create test users"""
        users_data = [
            {
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'email': 'admin@company.com',
                'is_active': 'Y',
                'department_id': 1
            },
            {
                'username': 'manager',
                'first_name': 'Manager',
                'last_name': 'User',
                'email': 'manager@company.com',
                'is_active': 'Y',
                'department_id': 2
            },
            {
                'username': 'reviewer',
                'first_name': 'Reviewer',
                'last_name': 'User',
                'email': 'reviewer@company.com',
                'is_active': 'Y',
                'department_id': 3
            }
        ]
        
        for user_data in users_data:
            user, created = CustomUser.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                self.stdout.write(f"✅ Created user: {user.username}")
            else:
                self.stdout.write(f"⚠️  User already exists: {user.username}")

    def create_test_workflow(self):
        """Create test approval workflow with stages"""
        # Create workflow
        workflow_id = f"WF_{uuid.uuid4().hex[:8].upper()}"
        workflow, created = ApprovalWorkflows.objects.get_or_create(
            workflow_id=workflow_id,
            defaults={
                'workflow_name': 'Test RFP Approval Workflow',
                'workflow_type': 'MULTI_LEVEL',
                'description': 'Test workflow for RFP approval process',
                'business_object_type': 'RFP',
                'is_active': True,
                'created_by': 1
            }
        )
        
        if created:
            self.stdout.write(f"✅ Created workflow: {workflow_id}")
            
            # Create approval request
            approval_id = f"AR_{uuid.uuid4().hex[:8].upper()}"
            approval_request = ApprovalRequests.objects.create(
                approval_id=approval_id,
                workflow_id=workflow_id,
                request_title='Test RFP Approval Request',
                request_description='This is a test approval request for the RFP system',
                requester_id=1,
                requester_department='IT',
                priority='HIGH',
                overall_status='PENDING',
                submission_date=timezone.now()
            )
            self.stdout.write(f"✅ Created approval request: {approval_id}")
            
            # Create stages
            stages_data = [
                {
                    'stage_order': 1,
                    'stage_name': 'Initial Review',
                    'stage_description': 'Initial review of the RFP request',
                    'assigned_user_id': 1,
                    'assigned_user_name': 'Admin User',
                    'assigned_user_role': 'Administrator',
                    'department': 'IT',
                    'stage_type': 'SEQUENTIAL',
                    'stage_status': 'PENDING'
                },
                {
                    'stage_order': 2,
                    'stage_name': 'Manager Approval',
                    'stage_description': 'Manager approval for the RFP request',
                    'assigned_user_id': 2,
                    'assigned_user_name': 'Manager User',
                    'assigned_user_role': 'Manager',
                    'department': 'Operations',
                    'stage_type': 'SEQUENTIAL',
                    'stage_status': 'PENDING'
                },
                {
                    'stage_order': 3,
                    'stage_name': 'Final Review',
                    'stage_description': 'Final review and approval',
                    'assigned_user_id': 3,
                    'assigned_user_name': 'Reviewer User',
                    'assigned_user_role': 'Reviewer',
                    'department': 'Finance',
                    'stage_type': 'SEQUENTIAL',
                    'stage_status': 'PENDING'
                }
            ]
            
            for stage_data in stages_data:
                stage_id = f"ST_{uuid.uuid4().hex[:8].upper()}"
                stage = ApprovalStages.objects.create(
                    stage_id=stage_id,
                    approval_id=workflow_id,
                    **stage_data
                )
                self.stdout.write(f"✅ Created stage: {stage.stage_name}")
        else:
            self.stdout.write(f"⚠️  Workflow already exists: {workflow_id}")
