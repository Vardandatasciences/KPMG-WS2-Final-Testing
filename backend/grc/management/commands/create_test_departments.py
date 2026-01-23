from django.core.management.base import BaseCommand
from django.utils import timezone
from grc.models import Department
from datetime import datetime

class Command(BaseCommand):
    help = 'Create test departments for the GRC system'

    def handle(self, *args, **options):
        # Sample departments data
        departments_data = [
            {
                'EntityId': 1,
                'DepartmentName': 'Information Technology',
                'DepartmentHead': 1,
                'BusinessUnitId': 1,
                'CreatedDate': timezone.now()
            },
            {
                'EntityId': 1,
                'DepartmentName': 'Human Resources',
                'DepartmentHead': 2,
                'BusinessUnitId': 1,
                'CreatedDate': timezone.now()
            },
            {
                'EntityId': 1,
                'DepartmentName': 'Finance',
                'DepartmentHead': 3,
                'BusinessUnitId': 1,
                'CreatedDate': timezone.now()
            },
            {
                'EntityId': 1,
                'DepartmentName': 'Legal',
                'DepartmentHead': 4,
                'BusinessUnitId': 1,
                'CreatedDate': timezone.now()
            },
            {
                'EntityId': 1,
                'DepartmentName': 'Operations',
                'DepartmentHead': 5,
                'BusinessUnitId': 1,
                'CreatedDate': timezone.now()
            },
            {
                'EntityId': 1,
                'DepartmentName': 'Marketing',
                'DepartmentHead': 6,
                'BusinessUnitId': 1,
                'CreatedDate': timezone.now()
            },
            {
                'EntityId': 1,
                'DepartmentName': 'Sales',
                'DepartmentHead': 7,
                'BusinessUnitId': 1,
                'CreatedDate': timezone.now()
            },
            {
                'EntityId': 1,
                'DepartmentName': 'Research & Development',
                'DepartmentHead': 8,
                'BusinessUnitId': 1,
                'CreatedDate': timezone.now()
            },
            {
                'EntityId': 1,
                'DepartmentName': 'Customer Support',
                'DepartmentHead': 9,
                'BusinessUnitId': 1,
                'CreatedDate': timezone.now()
            },
            {
                'EntityId': 1,
                'DepartmentName': 'Quality Assurance',
                'DepartmentHead': 10,
                'BusinessUnitId': 1,
                'CreatedDate': timezone.now()
            }
        ]

        created_count = 0
        for dept_data in departments_data:
            # Check if department already exists
            existing_dept = Department.objects.filter(
                DepartmentName=dept_data['DepartmentName'],
                EntityId=dept_data['EntityId']
            ).first()
            
            if not existing_dept:
                Department.objects.create(**dept_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created department: {dept_data["DepartmentName"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Department already exists: {dept_data["DepartmentName"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new departments')
        ) 