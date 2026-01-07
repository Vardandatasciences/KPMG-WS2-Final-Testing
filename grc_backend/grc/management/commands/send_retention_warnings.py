import logging
from datetime import date, timedelta

from django.apps import apps
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage, get_connection

from grc.models import (
    RetentionTimeline,
    DataLifecycleAuditLog,
    RBAC,
    Users,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Send notifications for records nearing retention expiry.
    Thresholds: 90, 30, 7 days.
    Skips archived or paused records.
    Logs each notification in DataLifecycleAuditLog to avoid duplicates per day/threshold.
    """

    help = "Send retention warning notifications for upcoming expiries (90/30/7 days)."

    THRESHOLDS = [90, 30, 7]

    def handle(self, *args, **options):
        today = timezone.now().date()

        qs = RetentionTimeline.objects.filter(
            Status='Active',
            deletion_paused=False,
            is_archived=False,
            auto_delete_enabled=True
        )

        total_checked = 0
        total_notified = 0
        errors = 0

        for timeline in qs:
            total_checked += 1
            days_left = (timeline.RetentionEndDate - today).days
            if days_left not in self.THRESHOLDS:
                continue

            # Avoid duplicate notifications for same threshold on same day
            already_sent = DataLifecycleAuditLog.objects.filter(
                action_type='WARNING_SENT',
                record_type=timeline.RecordType,
                record_id=timeline.RecordId,
                details__threshold=days_left,
                timestamp__date=today
            ).exists()

            if already_sent:
                continue

            recipients = self._get_admin_recipients()
            recipients_str = ";".join(recipients) if recipients else ""

            # Attempt email notification (best-effort)
            sent_ok = False
            if recipients:
                try:
                    subject = f"[Retention Warning] {timeline.RecordType} #{timeline.RecordId} expires in {days_left} days"
                    body = (
                        f"Record: {timeline.RecordType} #{timeline.RecordId}\n"
                        f"Name: {timeline.RecordName or '-'}\n"
                        f"Retention End Date: {timeline.RetentionEndDate}\n"
                        f"Days until expiry: {days_left}\n"
                        f"Status: {timeline.Status}\n"
                    )
                    send_mail(
                        subject=subject,
                        message=body,
                        from_email=None,  # use DEFAULT_FROM_EMAIL
                        recipient_list=recipients,
                        fail_silently=True
                    )
                    sent_ok = True
                except Exception as exc:
                    logger.warning("Email send failed for retention warning: %s", exc)

            # Log audit
            DataLifecycleAuditLog.log_action(
                action_type='WARNING_SENT',
                record_type=timeline.RecordType,
                record_id=timeline.RecordId,
                record_name=timeline.RecordName,
                timeline=timeline,
                before_status=timeline.Status,
                after_status=timeline.Status,
                details={
                    'threshold': days_left,
                    'retention_end_date': timeline.RetentionEndDate.isoformat(),
                    'email_sent': sent_ok,
                },
                notification_recipients=recipients_str
            )

            total_notified += 1

        self.stdout.write(self.style.SUCCESS(
            f"Retention warnings processed. checked={total_checked}, notified={total_notified}, errors={errors}"
        ))

    def _get_admin_recipients(self):
        """Return list of admin email addresses (GRC Administrator role)."""
        emails = []
        try:
            rbac_admins = RBAC.objects.filter(role='GRC Administrator', is_active='Y')
            user_ids = [r.user_id for r in rbac_admins]
            users = Users.objects.filter(UserId__in=user_ids).exclude(Email__isnull=True).exclude(Email='')
            emails = [u.Email for u in users if u.Email]
        except Exception as exc:
            logger.warning("Failed to load admin recipients: %s", exc)
        return emails

















