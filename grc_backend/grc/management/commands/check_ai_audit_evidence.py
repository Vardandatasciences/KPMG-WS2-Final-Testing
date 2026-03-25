from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from grc.models import Audit
from grc.debug_utils import debug_print
from grc.routes.Global.notifications import create_ai_audit_evidence_reminder_notification

# Fallback: when audit has no EvidenceReminderDays set, use this many days (e.g. legacy audits)
DEFAULT_DAYS_THRESHOLD = 15


class Command(BaseCommand):
    help = (
        "Check AI audits with no evidence: use each audit's EvidenceReminderDays (days after assign) to create alerts. "
        "If not set, fall back to due date within 15 days. Creates in-app alerts for the auditor.\n"
        "  python manage.py check_ai_audit_evidence\n"
        "  python manage.py check_ai_audit_evidence --verbose  # show why each audit was skipped or alert created"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print per-audit reason (skip vs alert created or error).',
        )

    def handle(self, *args, **options):
        now = timezone.now().date()
        due_cutoff = now + timedelta(days=DEFAULT_DAYS_THRESHOLD)

        self.stdout.write(
            "Checking AI audits with no evidence (using EvidenceReminderDays per audit, or due date within 15 days)..."
        )

        open_statuses = [
            "Yet to Start",  # newly assigned (from Assign Audit)
            "Open",
            "Pending",
            "In Progress",
            "Work In Progress",
            "Assigned",
        ]

        # Fetch all open AI audits; we decide per audit whether to alert (EvidenceReminderDays vs DueDate)
        audits = (
            Audit.objects.filter(
                AuditType="A",
                Status__in=open_statuses,
            )
            .select_related("Auditor")
        )

        if not audits:
            self.stdout.write("No AI audits eligible for evidence check.")
            return

        self.stdout.write(f"Found {audits.count()} AI audit(s) to check for evidence.")

        alerts_created = 0
        verbose = options.get('verbose', False) or options.get('verbosity', 0) >= 2

        for audit in audits:
            audit_id = audit.AuditId

            # Count evidences from ai_audit_data for this audit
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM ai_audit_data WHERE audit_id = %s",
                    [audit_id],
                )
                evidence_count = cursor.fetchone()[0] or 0

            if evidence_count > 0:
                if verbose:
                    self.stdout.write(f"  Audit {audit_id}: skip (has {evidence_count} evidence row(s))")
                continue

            auditor = getattr(audit, "Auditor", None)
            if not auditor or not getattr(auditor, "UserId", None):
                if verbose:
                    self.stdout.write(f"  Audit {audit_id}: skip (no auditor assigned)")
                continue

            # Use per-audit EvidenceReminderDays if set; else fall back to due-date within 15 days
            reminder_days = getattr(audit, "EvidenceReminderDays", None)
            if reminder_days is not None and reminder_days > 0:
                # Alert when (today - AssignedDate) >= EvidenceReminderDays (no evidence within X days)
                assigned = getattr(audit, "AssignedDate", None)
                if not assigned:
                    if verbose:
                        self.stdout.write(f"  Audit {audit_id}: skip (EvidenceReminderDays={reminder_days} but no AssignedDate)")
                    continue
                assigned_date = assigned.date() if hasattr(assigned, 'date') else assigned
                days_since_assign = (now - assigned_date).days
                if days_since_assign < reminder_days:
                    if verbose:
                        self.stdout.write(f"  Audit {audit_id}: skip (no evidence but only {days_since_assign} days since assign, need {reminder_days})")
                    continue
                days_used = reminder_days
            else:
                # Legacy: no EvidenceReminderDays — use due date within DEFAULT_DAYS_THRESHOLD
                if not getattr(audit, "DueDate", None):
                    if verbose:
                        self.stdout.write(f"  Audit {audit_id}: skip (no DueDate and no EvidenceReminderDays)")
                    continue
                if audit.DueDate > due_cutoff:
                    if verbose:
                        self.stdout.write(f"  Audit {audit_id}: skip (due date {audit.DueDate} after {due_cutoff})")
                    continue
                days_used = DEFAULT_DAYS_THRESHOLD

            user_id = auditor.UserId
            framework_id = getattr(audit, "FrameworkId_id", None)
            if verbose:
                self.stdout.write(f"  Audit {audit_id}: no evidence, threshold={days_used} days, creating notification...")

            try:
                if create_ai_audit_evidence_reminder_notification(
                    audit_id=audit_id,
                    user_id=user_id,
                    framework_id=framework_id,
                    due_days_threshold=days_used,
                ):
                    alerts_created += 1
                    self.stdout.write(f"  Audit {audit_id}: notification created for user_id={user_id}")
                else:
                    self.stdout.write(self.style.WARNING(f"  Audit {audit_id}: notification creation returned False/None"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Audit {audit_id}: notification failed: {e}"))

        self.stdout.write(f"Evidence alerts created: {alerts_created}")