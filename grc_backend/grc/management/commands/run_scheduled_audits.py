"""Run recurring audit generation, due reminders, and overdue escalations."""
from django.core.management.base import BaseCommand

from grc.services.audit_recurrence_service import process_audit_recurrence_and_escalations


class Command(BaseCommand):
    help = "Process audit due reminders, overdue escalations, and recurring audit occurrences."

    def add_arguments(self, parser):
        parser.add_argument('--tenant-id', type=int, default=None)

    def handle(self, *args, **options):
        stats = process_audit_recurrence_and_escalations(tenant_id=options.get('tenant_id'))
        self.stdout.write(self.style.SUCCESS(str(stats)))
