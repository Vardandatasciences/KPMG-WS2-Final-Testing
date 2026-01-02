"""
Management command to add sample data for dashboard testing
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from datetime import timedelta
import uuid
import json


class Command(BaseCommand):
    help = 'Add sample data for dashboard testing'

    def handle(self, *args, **options):
        self.stdout.write('Adding sample dashboard data...')
        
        try:
            with connection.cursor() as cursor:
                # Temporarily disable foreign key checks
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                
                # 1. Create sample workflows
                workflows_data = [
                    {
                        'workflow_id': 'WF001',
                        'workflow_name': 'Vendor Onboarding',
                        'workflow_type': 'MULTI_LEVEL',
                        'description': 'Standard vendor onboarding process',
                        'business_object_type': 'Vendor'
                    },
                    {
                        'workflow_id': 'WF002', 
                        'workflow_name': 'Contract Approval',
                        'workflow_type': 'MULTI_PERSON',
                        'description': 'Contract review and approval process',
                        'business_object_type': 'Contract'
                    },
                    {
                        'workflow_id': 'WF003',
                        'workflow_name': 'Risk Assessment',
                        'workflow_type': 'MULTI_LEVEL',
                        'description': 'Vendor risk assessment workflow',
                        'business_object_type': 'Risk'
                    }
                ]
                
                for workflow in workflows_data:
                    cursor.execute("""
                        INSERT IGNORE INTO approval_workflows 
                        (workflow_id, workflow_name, workflow_type, description, business_object_type, 
                         is_active, created_by, created_at, updated_at) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        workflow['workflow_id'],
                        workflow['workflow_name'],
                        workflow['workflow_type'],
                        workflow['description'],
                        workflow['business_object_type'],
                        True,
                        'admin',
                        timezone.now(),
                        timezone.now()
                    ])
                
                # 2. Create sample approval requests
                requests_data = [
                    {
                        'approval_id': 'REQ001',
                        'workflow_id': 'WF001',
                        'request_title': 'New Vendor Registration - ABC Corp',
                        'request_description': 'Onboarding new vendor ABC Corporation for IT services',
                        'requester_id': 'admin',
                        'requester_department': 'Procurement',
                        'priority': 'HIGH',
                        'overall_status': 'PENDING',
                        'created_at': timezone.now() - timedelta(days=1)
                    },
                    {
                        'approval_id': 'REQ002',
                        'workflow_id': 'WF002',
                        'request_title': 'Contract Renewal - XYZ Ltd',
                        'request_description': 'Annual contract renewal for XYZ Limited',
                        'requester_id': 'admin',
                        'requester_department': 'Legal',
                        'priority': 'MEDIUM',
                        'overall_status': 'IN_PROGRESS',
                        'created_at': timezone.now() - timedelta(days=2)
                    },
                    {
                        'approval_id': 'REQ003',
                        'workflow_id': 'WF001',
                        'request_title': 'Vendor Assessment - DEF Inc',
                        'request_description': 'Security assessment for DEF Incorporated',
                        'requester_id': 'admin',
                        'requester_department': 'Security',
                        'priority': 'URGENT',
                        'overall_status': 'APPROVED',
                        'created_at': timezone.now() - timedelta(days=3)
                    },
                    {
                        'approval_id': 'REQ004',
                        'workflow_id': 'WF003',
                        'request_title': 'Risk Review - GHI Corp',
                        'request_description': 'Quarterly risk review for GHI Corporation',
                        'requester_id': 'admin',
                        'requester_department': 'Risk Management',
                        'priority': 'LOW',
                        'overall_status': 'REJECTED',
                        'created_at': timezone.now() - timedelta(days=4)
                    },
                    {
                        'approval_id': 'REQ005',
                        'workflow_id': 'WF002',
                        'request_title': 'New Contract - JKL Ltd',
                        'request_description': 'New service contract with JKL Limited',
                        'requester_id': 'admin',
                        'requester_department': 'Procurement',
                        'priority': 'MEDIUM',
                        'overall_status': 'PENDING',
                        'created_at': timezone.now() - timedelta(hours=6)
                    }
                ]
                
                for request in requests_data:
                    cursor.execute("""
                        INSERT IGNORE INTO approval_requests 
                        (approval_id, workflow_id, request_title, request_description, requester_id, 
                         requester_department, priority, request_data, overall_status, 
                         submission_date, created_at, updated_at) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        request['approval_id'],
                        request['workflow_id'],
                        request['request_title'],
                        request['request_description'],
                        request['requester_id'],
                        request['requester_department'],
                        request['priority'],
                        json.dumps({'sample': True}),
                        request['overall_status'],
                        request['created_at'],
                        request['created_at'],
                        timezone.now()
                    ])
                
                # 3. Create sample approval stages
                stages_data = [
                    {
                        'stage_id': 'STG001',
                        'approval_id': 'REQ001',
                        'stage_order': 1,
                        'stage_name': 'Initial Review',
                        'stage_description': 'Initial vendor documentation review',
                        'assigned_user_id': 'admin',
                        'assigned_user_name': 'Admin User',
                        'assigned_user_role': 'Manager',
                        'department': 'Procurement',
                        'stage_type': 'REVIEW',
                        'stage_status': 'PENDING',
                        'deadline_date': timezone.now() + timedelta(days=2),
                        'created_at': timezone.now() - timedelta(days=1)
                    },
                    {
                        'stage_id': 'STG002',
                        'approval_id': 'REQ002',
                        'stage_order': 1,
                        'stage_name': 'Legal Review',
                        'stage_description': 'Legal team contract review',
                        'assigned_user_id': 'admin',
                        'assigned_user_name': 'Admin User',
                        'assigned_user_role': 'Manager',
                        'department': 'Legal',
                        'stage_type': 'REVIEW',
                        'stage_status': 'IN_PROGRESS',
                        'deadline_date': timezone.now() + timedelta(days=1),
                        'created_at': timezone.now() - timedelta(days=2)
                    },
                    {
                        'stage_id': 'STG003',
                        'approval_id': 'REQ005',
                        'stage_order': 1,
                        'stage_name': 'Contract Analysis',
                        'stage_description': 'Analyze contract terms and conditions',
                        'assigned_user_id': 'admin',
                        'assigned_user_name': 'Admin User',
                        'assigned_user_role': 'Manager',
                        'department': 'Procurement',
                        'stage_type': 'REVIEW',
                        'stage_status': 'PENDING',
                        'deadline_date': timezone.now() + timedelta(hours=12),
                        'created_at': timezone.now() - timedelta(hours=6)
                    }
                ]
                
                for stage in stages_data:
                    cursor.execute("""
                        INSERT IGNORE INTO approval_stages 
                        (stage_id, approval_id, stage_order, stage_name, stage_description,
                         assigned_user_id, assigned_user_name, assigned_user_role, department,
                         stage_type, stage_status, deadline_date, created_at, updated_at) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        stage['stage_id'],
                        stage['approval_id'],
                        stage['stage_order'],
                        stage['stage_name'],
                        stage['stage_description'],
                        stage['assigned_user_id'],
                        stage['assigned_user_name'],
                        stage['assigned_user_role'],
                        stage['department'],
                        stage['stage_type'],
                        stage['stage_status'],
                        stage['deadline_date'],
                        stage['created_at'],
                        timezone.now()
                    ])
                
                # Re-enable foreign key checks
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                
                self.stdout.write(
                    self.style.SUCCESS('Successfully added sample dashboard data!')
                )
                self.stdout.write('Created:')
                self.stdout.write('- 3 sample workflows')
                self.stdout.write('- 5 sample approval requests')
                self.stdout.write('- 3 sample approval stages')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error adding sample data: {str(e)}')
            )

