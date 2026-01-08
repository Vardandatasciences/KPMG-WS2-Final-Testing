import logging
from django.core.management.base import BaseCommand
from django.db import transaction

from grc.models import (
    Policy, Compliance, Audit, Incident, Risk, RiskInstance,
    upsert_retention_timeline,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Backfill/repair RetentionTimeline entries from records that already have retentionExpiry set.
    Run this if timelines are missing for existing data.
    """

    help = "Sync RetentionTimeline from existing records with retentionExpiry"

    def handle(self, *args, **options):
        total = 0
        with transaction.atomic():
            total += self._sync_model(Policy, 'policy', 'PolicyName', 'CreatedByDate', 'FrameworkId')
            total += self._sync_model(Compliance, 'compliance', 'ComplianceTitle', 'CreatedByDate', 'FrameworkId')
            total += self._sync_model(Audit, 'audit', 'Title', 'AssignedDate', 'FrameworkId')
            total += self._sync_model(Incident, 'incident', 'IncidentTitle', 'CreatedAt', 'FrameworkId')
            total += self._sync_model(Risk, 'risk', 'RiskTitle', 'CreatedAt', 'FrameworkId')
            total += self._sync_model(RiskInstance, 'risk_instance', 'RiskTitle', 'CreatedAt', 'FrameworkId')

        self.stdout.write(self.style.SUCCESS(f"Synced timelines: {total}"))

    def _sync_model(self, model_cls, record_type, name_field, created_field, framework_field):
        count = 0
        qs = model_cls.objects.exclude(retentionExpiry__isnull=True)
        for obj in qs:
            try:
                record_name = getattr(obj, name_field, None)
                created_date = getattr(obj, created_field, None)
                framework_obj = getattr(obj, framework_field, None)
                upsert_retention_timeline(
                    obj,
                    record_type,
                    record_name=record_name,
                    created_date=created_date,
                    framework_id=framework_obj
                )
                count += 1
            except Exception as exc:
                logger.warning("Failed to upsert timeline for %s#%s: %s", record_type, getattr(obj, 'pk', None), exc)
        return count

















