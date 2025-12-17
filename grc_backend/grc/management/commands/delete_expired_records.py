import logging
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from grc.models import RetentionTimeline

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Scheduled job to delete or dispose records whose retention period has expired.
    This performs a soft-delete on the retention timeline (Status -> Disposed),
    and attempts to delete the actual record if a model mapping is known.
    """

    help = "Delete/Dispose records whose retention has expired (auto-delete enabled, not paused, not archived)."

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
                try:
                    deleted_record, error_msg = timeline.dispose_and_delete_record(auto_delete=True)
                except Exception:
                    # dispose_and_delete_record already logs its own errors;
                    # we just keep statistics here.
                    logger.exception("Error disposing timeline %s", timeline.RetentionTimelineId)
                    errors += 1
                    continue

                if deleted_record and not error_msg:
                    deleted_count += 1
                else:
                    disposed_only += 1

        self.stdout.write(self.style.SUCCESS(
            f"Processed {total} expired timelines; deleted={deleted_count}, disposed_only={disposed_only}, errors={errors}"
        ))


