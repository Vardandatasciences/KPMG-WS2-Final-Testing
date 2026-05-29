"""
Recurring audit scheduling, due-date calculation, and overdue escalation helpers.
"""
from __future__ import annotations

import datetime
import json
from typing import Iterable, Optional

from django.db import connection
from django.utils import timezone

from ..models import Audit, AuditFinding, Compliance, Framework, RBAC, Users
from ..utils.auto_decrypt_helper import display_audit_title

# Label -> interval days (matches Assign Audit / compliance frequency options)
FREQUENCY_LABEL_TO_DAYS = {
    'only once': 0,
    'daily': 1,
    'monthly': 30,
    'every 2 months': 60,
    'every 4 months': 120,
    'half yearly': 182,
    'yearly': 365,
}

FREQUENCY_VALUE_TO_DAYS = {
    '0': 0,
    '1': 1,
    '30': 30,
    '60': 60,
    '120': 120,
    '182': 182,
    '365': 365,
}

FREQUENCY_DAYS_TO_LABEL = {v: k.title() for k, v in FREQUENCY_LABEL_TO_DAYS.items() if v > 0}
FREQUENCY_DAYS_TO_LABEL[0] = 'Only Once'


def parse_frequency_to_days(value) -> int:
    """Convert frequency int/string/label to interval days."""
    if value is None or value == '':
        return 0
    s = str(value).strip().lower()
    if s.endswith('a'):
        s = s[:-1]
    if s in FREQUENCY_VALUE_TO_DAYS:
        return int(FREQUENCY_VALUE_TO_DAYS[s])
    try:
        return int(s)
    except (TypeError, ValueError):
        pass
    return int(FREQUENCY_LABEL_TO_DAYS.get(s, 0))


def audit_frequency_label_to_days(label: Optional[str]) -> int:
    if not label:
        return 0
    normalized = str(label).strip().lower()
    if normalized in FREQUENCY_LABEL_TO_DAYS:
        return FREQUENCY_LABEL_TO_DAYS[normalized]
    return parse_frequency_to_days(label)


def compute_due_date(start_date: datetime.date, completion_days: Optional[int]) -> datetime.date:
    if not start_date:
        start_date = timezone.now().date()
    days = int(completion_days) if completion_days else 30
    return start_date + datetime.timedelta(days=max(1, days))


def resolve_audit_start_date(
    assign_scope: str,
    assign_date: datetime.date,
    compliance_starts: Iterable[Optional[datetime.date]],
) -> datetime.date:
    """Sub-policy: assign day. Compliance: max(assign day, each compliance start)."""
    assign_date = assign_date or timezone.now().date()
    if assign_scope != 'compliance':
        return assign_date
    starts = [d for d in compliance_starts if d]
    if not starts:
        return assign_date
    anchor = max(starts)
    return max(assign_date, anchor)


def resolve_frequency_for_assignment(
    assign_scope: str,
    subpolicy_frequency,
    compliance_ids: list,
    tenant_id: int,
) -> int:
    if assign_scope == 'compliance' and compliance_ids:
        qs = Compliance.objects.filter(
            ComplianceId__in=compliance_ids, tenant_id=tenant_id
        ).only('AuditFrequency')
        days = [audit_frequency_label_to_days(c.AuditFrequency) for c in qs]
        days = [d for d in days if d is not None]
        if not days:
            return parse_frequency_to_days(subpolicy_frequency)
        return min(days) if days else 0
    return parse_frequency_to_days(subpolicy_frequency)


def get_compliance_manager_user_ids(tenant_id: int) -> list:
    rows = RBAC.objects.filter(
        role='Compliance Manager',
        is_active='Y',
        user__tenant_id=tenant_id,
    ).values_list('user_id', flat=True)
    return list(dict.fromkeys(rows))


def store_in_app_audit_notification(
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    framework_id: Optional[int],
    metadata: dict,
):
    """Persist in-app notification (read by get_notifications)."""
    try:
        # Must match get_notifications(), which looks up users.Email via get_user_email_from_id.
        from ..routes.Global.notifications import get_user_email_from_id

        recipient = (get_user_email_from_id(int(user_id)) or "").strip() or f"user_{user_id}"
        metadata = dict(metadata or {})
        metadata['message'] = message
        metadata['title'] = title
        payload = json.dumps(metadata)[:2000]
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO notifications
                (recipient, type, channel, success, error, created_at, FrameworkId)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    recipient,
                    notification_type,
                    'in_app',
                    1,
                    payload,
                    timezone.now(),
                    framework_id,
                ),
            )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception(
            "Failed to store audit notification type=%s user_id=%s: %s",
            notification_type,
            user_id,
            exc,
        )


def clone_audit_for_next_occurrence(root_audit: Audit, next_start: datetime.date) -> Optional[Audit]:
    """Create the next recurring audit occurrence from a completed root audit."""
    interval = int(root_audit.Frequency or 0)
    if interval <= 0:
        return None
    if root_audit.EndDate and next_start > root_audit.EndDate:
        return None

    completion_days = root_audit.CompletionDays or 30
    due = compute_due_date(next_start, completion_days)

    if root_audit.EndDate and due > root_audit.EndDate:
        return None

    child_fields = {
        'Title': root_audit.Title,
        'Scope': root_audit.Scope,
        'Objective': root_audit.Objective,
        'BusinessUnit': root_audit.BusinessUnit,
        'Role': root_audit.Role,
        'Responsibility': root_audit.Responsibility,
        'Assignee': root_audit.Assignee,
        'Auditor': root_audit.Auditor,
        'Reviewer': root_audit.Reviewer,
        'FrameworkId': root_audit.FrameworkId,
        'PolicyId': root_audit.PolicyId,
        'SubPolicyId': root_audit.SubPolicyId,
        'DueDate': due,
        'Frequency': root_audit.Frequency,
        'Status': 'Yet to Start',
        'AuditType': root_audit.AuditType,
        'AssignedDate': timezone.now(),
        'StartDate': next_start,
        'EndDate': root_audit.EndDate,
        'AssignScope': root_audit.AssignScope,
        'CompletionDays': root_audit.CompletionDays,
        'ParentAudit': root_audit,
        'IsRecurrenceRoot': False,
        'tenant_id': root_audit.tenant_id,
        'data_inventory': root_audit.data_inventory,
    }
    child = Audit.objects.create(**child_fields)

    parent_id = root_audit.AuditId
    findings = AuditFinding.objects.filter(AuditId_id=parent_id)
    for f in findings:
        AuditFinding.objects.create(
            tenant_id=f.tenant_id,
            AuditId=child,
            ComplianceId=f.ComplianceId,
            UserId=f.UserId,
            Evidence='',
            Check='0',
            AssignedDate=timezone.now(),
            FrameworkId=f.FrameworkId,
        )
    return child


def process_audit_recurrence_and_escalations(tenant_id: Optional[int] = None) -> dict:
    """
    Daily job:
    - Remind auditors before due date
    - Escalate to Compliance Managers 1 day after due if not completed
    - Spawn next recurring audit when previous is completed
    """
    today = timezone.now().date()
    stats = {
        'reminders': 0,
        'escalations': 0,
        'recurrences_created': 0,
        'review_escalations': 0,
    }

    qs = Audit.objects.exclude(AuditType='A').filter(Frequency__gt=0)
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)

    # Cap per run so dev DBs with thousands of legacy audits do not block the server
    max_per_run = 200
    try:
        import os
        max_per_run = int(os.environ.get('SCHEDULED_AUDITS_MAX_PER_RUN', '200'))
    except (TypeError, ValueError):
        pass
    max_per_run = max(10, min(max_per_run, 2000))

    base_qs = qs.select_related('Auditor', 'FrameworkId')
    due_soon_cutoff = today + datetime.timedelta(days=3)
    priority_ids = list(
        base_qs.filter(
            DueDate__isnull=False,
            DueDate__gte=today,
            DueDate__lte=due_soon_cutoff,
        )
        .exclude(Status__iexact='completed')
        .values_list('AuditId', flat=True)[:max_per_run]
    )
    overdue_ids = list(
        base_qs.filter(
            DueDate__isnull=False,
            DueDate__lt=today,
            OverdueEscalatedAt__isnull=True,
        )
        .exclude(Status__iexact='completed')
        .values_list('AuditId', flat=True)[:max_per_run]
    )
    recurrence_ids = list(
        base_qs.filter(Status__iexact='completed', Frequency__gt=0)
        .values_list('AuditId', flat=True)[:max_per_run]
    )
    seen = set()
    ordered_ids = []
    for pk in priority_ids + overdue_ids + recurrence_ids:
        if pk not in seen:
            seen.add(pk)
            ordered_ids.append(pk)
    remaining_slots = max(0, max_per_run - len(ordered_ids))
    if remaining_slots:
        for pk in base_qs.order_by('AuditId').values_list('AuditId', flat=True):
            if pk in seen:
                continue
            seen.add(pk)
            ordered_ids.append(pk)
            if len(ordered_ids) >= max_per_run:
                break

    audits_to_process = list(base_qs.filter(AuditId__in=ordered_ids)) if ordered_ids else []

    for audit in audits_to_process:
        if not audit.DueDate:
            continue

        fw_id = audit.FrameworkId_id if audit.FrameworkId_id else None
        completed = (audit.Status or '').lower() == 'completed'

        audit_label = display_audit_title(audit.Title)

        # Due soon (3 days)
        if not completed and audit.DueDate and today <= audit.DueDate <= today + datetime.timedelta(days=3):
            store_in_app_audit_notification(
                audit.Auditor_id,
                'audit_due_reminder',
                'Audit due soon',
                f'Audit "{audit_label}" is due on {audit.DueDate}.',
                fw_id,
                {'audit_id': audit.AuditId, 'due_date': audit.DueDate.isoformat()},
            )
            stats['reminders'] += 1

        # Overdue escalation (+1 day)
        if (
            not completed
            and not audit.OverdueEscalatedAt
            and audit.DueDate
            and today > audit.DueDate
        ):
            for mgr_id in get_compliance_manager_user_ids(audit.tenant_id):
                store_in_app_audit_notification(
                    mgr_id,
                    'audit_overdue_manager_escalation',
                    'Audit overdue – action required',
                    (
                        f'Audit "{audit_label}" (ID {audit.AuditId}) was due {audit.DueDate} '
                        f'and is not complete. Reassign the auditor on the Compliance Dashboard.'
                    ),
                    fw_id,
                    {
                        'audit_id': audit.AuditId,
                        'auditor_id': audit.Auditor_id,
                        'manager_user_id': mgr_id,
                        'action_url': '/compliance/user-dashboard?auditOverdueEscalations=1',
                    },
                )
            # Use queryset.update to avoid post_save retention/event signal storm
            Audit.objects.filter(pk=audit.pk).update(OverdueEscalatedAt=timezone.now())
            audit.OverdueEscalatedAt = timezone.now()
            stats['escalations'] += 1

        # Recurrence after completion
        if completed and audit.Frequency and int(audit.Frequency) > 0:
            root = audit
            if audit.ParentAudit_id and not audit.IsRecurrenceRoot:
                root = audit.ParentAudit or audit
            if not root.IsRecurrenceRoot and not audit.ParentAudit_id:
                root = audit

            interval = int(audit.Frequency)
            next_start = (audit.CompletionDate.date() if audit.CompletionDate else audit.DueDate) + datetime.timedelta(
                days=interval
            )
            if audit.EndDate and next_start > audit.EndDate:
                continue

            # Avoid duplicate child for same period
            existing = Audit.objects.filter(
                ParentAudit_id=root.AuditId,
                StartDate=next_start,
            ).exists()
            if not existing:
                child = clone_audit_for_next_occurrence(root, next_start)
                if child:
                    store_in_app_audit_notification(
                        child.Auditor_id,
                        'audit_recurrence_assigned',
                        'Recurring audit assigned',
                        f'A new audit round for "{display_audit_title(child.Title)}" is due {child.DueDate}.',
                        fw_id,
                        {'audit_id': child.AuditId},
                    )
                    stats['recurrences_created'] += 1

    try:
        from .audit_review_service import process_audit_review_escalations

        review_stats = process_audit_review_escalations(tenant_id=tenant_id)
        stats['review_escalations'] = review_stats.get('review_escalations', 0)
    except Exception:
        import logging

        logging.getLogger(__name__).exception('Audit review escalation pass failed')

    return stats


def resolve_framework_end_date(framework_obj: Optional[Framework]) -> Optional[datetime.date]:
    if not framework_obj:
        return None
    return framework_obj.EndDate
