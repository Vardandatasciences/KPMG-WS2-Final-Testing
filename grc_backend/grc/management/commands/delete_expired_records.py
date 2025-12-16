import logging
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.apps import apps

from grc.models import (
    RetentionTimeline,
    DataLifecycleAuditLog,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Scheduled job to delete or dispose records whose retention period has expired.
    This performs a soft-delete on the retention timeline (Status -> Disposed),
    and attempts to delete the actual record if a model mapping is known.
    """

    help = "Delete/Dispose records whose retention has expired (auto-delete enabled, not paused, not archived)."

    # Map RecordType (case-insensitive) to app model label for deletion
    MODEL_MAP = {
        'policy': 'grc.Policy',
        'policyversion': 'grc.PolicyVersion',
        'policyapproval': 'grc.PolicyApproval',
        'subpolicy': 'grc.SubPolicy',
        'policyacknowledgementrequest': 'grc.PolicyAcknowledgementRequest',
        'framework': 'grc.Framework',
        'frameworkversion': 'grc.FrameworkVersion',
        'frameworkapproval': 'grc.FrameworkApproval',
        'compliance': 'grc.Compliance',
        'category': 'grc.Category',
        'categorybusinessunit': 'grc.CategoryBusinessUnit',
        'audit': 'grc.Audit',
        'auditversion': 'grc.AuditVersion',
        'auditfinding': 'grc.AuditFinding',
        'incident': 'grc.Incident',
        'workflow': 'grc.Workflow',
        'risk': 'grc.Risk',
        'riskinstance': 'grc.RiskInstance',
        'event': 'grc.Event',
        'auditdocument': 'grc.AuditDocument',
        's3file': 'grc.S3File',
        'fileoperations': 'grc.FileOperations',
    }

    def handle(self, *args, **options):
        today = timezone.now().date()
        qs = RetentionTimeline.objects.filter(
            RetentionEndDate__lte=today,
            Status='Active',
            deletion_paused=False,
            is_archived=False,
            auto_delete_enabled=True
        )

        total = qs.count()
        deleted_count = 0
        disposed_only = 0
        errors = 0

        for timeline in qs:
            with transaction.atomic():
                before_status = timeline.Status
                deleted_record = False
                error_msg = None

                model_label = self.MODEL_MAP.get(timeline.RecordType.lower())
                if model_label:
                    try:
                        model_cls = apps.get_model(model_label)
                        obj = model_cls.objects.filter(pk=timeline.RecordId).first()
                        if obj:
                            obj.delete()
                            deleted_record = True
                        else:
                            # Record already missing; proceed to dispose timeline
                            deleted_record = True
                    except Exception as exc:
                        error_msg = str(exc)
                        logger.exception("Error deleting record %s#%s", timeline.RecordType, timeline.RecordId)
                        errors += 1

                # Mark timeline as disposed
                timeline.Status = 'Disposed'
                timeline.save(update_fields=['Status', 'UpdatedAt'])

                # Audit log
                DataLifecycleAuditLog.log_action(
                    action_type='DELETE',
                    record_type=timeline.RecordType,
                    record_id=timeline.RecordId,
                    record_name=timeline.RecordName,
                    timeline=timeline,
                    before_status=before_status,
                    after_status='Disposed',
                    details={
                        'deleted_record': deleted_record,
                        'error': error_msg,
                        'auto_delete': True,
                        'retention_end_date': timeline.RetentionEndDate.isoformat(),
                    }
                )

                if deleted_record and not error_msg:
                    deleted_count += 1
                else:
                    disposed_only += 1

        self.stdout.write(self.style.SUCCESS(
            f"Processed {total} expired timelines; deleted={deleted_count}, disposed_only={disposed_only}, errors={errors}"
        ))


