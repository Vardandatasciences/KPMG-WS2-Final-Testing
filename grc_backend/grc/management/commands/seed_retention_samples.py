import logging
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from grc.models import (
    Users,
    Framework,
    RetentionTimeline,
    DataLifecycleAuditLog,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Seed sample retention timelines for dashboard testing.

    Creates:
    - Active expiring soon
    - Archived
    - Paused
    - Disposed (expired)
    - Extended
    """

    help = "Seed sample retention timelines for retention dashboard testing."

    def handle(self, *args, **options):
        with transaction.atomic():
            user = self._get_or_create_user()
            framework = self._get_or_create_framework()

            samples = [
                {
                    'RecordType': 'policy',
                    'RecordId': 10001,
                    'RecordName': 'Policy Expiring Soon',
                    'RetentionStartDate': date.today() - timedelta(days=300),
                    'RetentionEndDate': date.today() + timedelta(days=5),
                    'Status': 'Active',
                    'auto_delete_enabled': True,
                    'deletion_paused': False,
                    'is_archived': False,
                },
                {
                    'RecordType': 'compliance',
                    'RecordId': 10002,
                    'RecordName': 'Compliance Archived',
                    'RetentionStartDate': date.today() - timedelta(days=800),
                    'RetentionEndDate': date.today() + timedelta(days=30),
                    'Status': 'Archived',
                    'is_archived': True,
                    'archived_date': date.today() - timedelta(days=1),
                    'archive_location': 's3://retention-tests/archive/compliance-10002',
                    'deletion_paused': True,
                },
                {
                    'RecordType': 'risk',
                    'RecordId': 10003,
                    'RecordName': 'Risk Paused',
                    'RetentionStartDate': date.today() - timedelta(days=200),
                    'RetentionEndDate': date.today() + timedelta(days=60),
                    'Status': 'Paused',
                    'deletion_paused': True,
                    'pause_reason': 'Legal hold for investigation',
                    'pause_until': date.today() + timedelta(days=20),
                },
                {
                    'RecordType': 'audit',
                    'RecordId': 10004,
                    'RecordName': 'Audit Disposed',
                    'RetentionStartDate': date.today() - timedelta(days=900),
                    'RetentionEndDate': date.today() - timedelta(days=10),
                    'Status': 'Disposed',
                    'auto_delete_enabled': False,
                },
                {
                    'RecordType': 'incident',
                    'RecordId': 10005,
                    'RecordName': 'Incident Extended',
                    'RetentionStartDate': date.today() - timedelta(days=100),
                    'RetentionEndDate': date.today() + timedelta(days=400),
                    'Status': 'Extended',
                    'auto_delete_enabled': True,
                },
            ]

            created = 0
            for sample in samples:
                rt = sample['RecordType']
                rid = sample['RecordId']
                if RetentionTimeline.objects.filter(RecordType=rt, RecordId=rid).exists():
                    continue

                timeline = RetentionTimeline.objects.create(
                    RecordType=rt,
                    RecordId=rid,
                    RecordName=sample.get('RecordName'),
                    CreatedDate=sample.get('RetentionStartDate'),
                    RetentionStartDate=sample.get('RetentionStartDate'),
                    RetentionEndDate=sample.get('RetentionEndDate'),
                    Status=sample.get('Status', 'Active'),
                    is_archived=sample.get('is_archived', False),
                    archived_date=sample.get('archived_date'),
                    archive_location=sample.get('archive_location'),
                    deletion_paused=sample.get('deletion_paused', False),
                    pause_reason=sample.get('pause_reason'),
                    pause_until=sample.get('pause_until'),
                    auto_delete_enabled=sample.get('auto_delete_enabled', True),
                    backup_created=False,
                    FrameworkId=framework,
                    CreatedBy=user,
                    UpdatedBy=user,
                )

                DataLifecycleAuditLog.log_action(
                    action_type='CREATE',
                    record_type=rt,
                    record_id=rid,
                    record_name=sample.get('RecordName'),
                    timeline=timeline,
                    performed_by=user,
                    after_status=timeline.Status,
                    details={'seeded': True}
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} retention timeline samples."))

    def _get_or_create_user(self):
        user, _ = Users.objects.get_or_create(
            UserName='retention.tester',
            defaults={
                'Password': 'dummy',
                'Email': 'retention.tester@example.com',
                'FirstName': 'Retention',
                'LastName': 'Tester',
                'IsActive': 'Y',
                # Some deployments use integer DepartmentId; store a numeric-safe value.
                'DepartmentId': '0',
            }
        )
        return user

    def _get_or_create_framework(self):
        fw, _ = Framework.objects.get_or_create(
            FrameworkName='Retention Test Framework',
            defaults={
                'FrameworkDescription': 'Test framework for retention seeding',
                'CreatedByName': 'system',
                'CreatedByDate': date.today(),
                'Reviewer': 'system',
                'CurrentVersion': 1.0,
            }
        )
        return fw

