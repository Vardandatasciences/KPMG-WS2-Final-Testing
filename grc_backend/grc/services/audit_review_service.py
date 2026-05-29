"""
Audit review notifications and Audit Manager escalation when review stalls.
"""
from __future__ import annotations

import datetime
import os
from typing import Optional

from django.db.models import Q
from django.utils import timezone

from ..models import Audit, RBAC
from ..utils.auto_decrypt_helper import display_audit_title
from .audit_recurrence_service import store_in_app_audit_notification

AUDIT_REVIEW_ESCALATION_DAYS_DEFAULT = 5


def _review_escalation_days() -> int:
    try:
        return max(1, int(os.environ.get('AUDIT_REVIEW_ESCALATION_DAYS', AUDIT_REVIEW_ESCALATION_DAYS_DEFAULT)))
    except (TypeError, ValueError):
        return AUDIT_REVIEW_ESCALATION_DAYS_DEFAULT


def _under_review_filter():
    return Q(Status__iexact='under review') | Q(Status__iexact='Under Review')


def get_audit_manager_user_ids(tenant_id: int) -> list:
    rows = RBAC.objects.filter(
        role='Audit Manager',
        is_active='Y',
        user__tenant_id=tenant_id,
    ).values_list('user_id', flat=True)
    return list(dict.fromkeys(rows))


def handle_audit_sent_for_review(audit_id: int, tenant_id: int) -> bool:
    """
    After audit moves to Under review: set ReviewStartDate and notify assigned Reviewer.
    """
    try:
        audit = Audit.objects.select_related('Reviewer', 'FrameworkId').get(
            AuditId=audit_id,
            tenant_id=tenant_id,
        )
    except Audit.DoesNotExist:
        return False

    now = timezone.now()
    update_fields = ['Status']
    audit.Status = 'Under review'
    if not audit.ReviewStartDate:
        audit.ReviewStartDate = now
        update_fields.append('ReviewStartDate')
    if audit.ReviewEscalatedAt:
        audit.ReviewEscalatedAt = None
        update_fields.append('ReviewEscalatedAt')
    audit.save(update_fields=update_fields)

    reviewer = audit.Reviewer
    if not reviewer or not reviewer.UserId:
        return True

    label = display_audit_title(audit.Title)
    store_in_app_audit_notification(
        reviewer.UserId,
        'audit_ready_for_review',
        'Audit ready for your review',
        (
            f'Audit "{label}" (ID {audit.AuditId}) was submitted for review. '
            f'Please complete your review in the Reviewer workspace.'
        ),
        audit.FrameworkId_id,
        {
            'audit_id': audit.AuditId,
            'action_url': '/auditor/reviews',
        },
    )
    return True


def process_audit_review_escalations(tenant_id: Optional[int] = None) -> dict:
    """
    Escalate audits stuck in Under review past AUDIT_REVIEW_ESCALATION_DAYS to Audit Managers.
    """
    stats = {'review_escalations': 0}
    days = _review_escalation_days()
    cutoff = timezone.now() - datetime.timedelta(days=days)

    qs = Audit.objects.exclude(AuditType='A').filter(_under_review_filter())
    qs = qs.filter(ReviewStartDate__isnull=False, ReviewStartDate__lte=cutoff)
    qs = qs.filter(ReviewEscalatedAt__isnull=True)
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)

    for audit in qs.select_related('Reviewer', 'FrameworkId')[:500]:
        fw_id = audit.FrameworkId_id if audit.FrameworkId_id else None
        label = display_audit_title(audit.Title)
        reviewer_name = ''
        if audit.Reviewer:
            reviewer_name = (audit.Reviewer.UserName or '').strip()

        for mgr_id in get_audit_manager_user_ids(audit.tenant_id):
            store_in_app_audit_notification(
                mgr_id,
                'audit_review_manager_escalation',
                'Audit review overdue – assign reviewer',
                (
                    f'Audit "{label}" (ID {audit.AuditId}) has been under review'
                    f'{f" with {reviewer_name}" if reviewer_name else ""} '
                    f'since {audit.ReviewStartDate.date() if audit.ReviewStartDate else "?"}. '
                    f'Assign or reassign a reviewer on the Audit Dashboard.'
                ),
                fw_id,
                {
                    'audit_id': audit.AuditId,
                    'reviewer_id': audit.Reviewer_id,
                    'manager_user_id': mgr_id,
                    'action_url': '/auditor/dashboard?reviewEscalations=1',
                },
            )
        Audit.objects.filter(pk=audit.pk).update(ReviewEscalatedAt=timezone.now())
        stats['review_escalations'] += 1

    return stats


def list_stalled_reviews_for_managers(tenant_id: int, include_not_yet_escalated: bool = True):
    """Audits under review past escalation threshold (for Audit Manager dashboard)."""
    days = _review_escalation_days()
    cutoff = timezone.now() - datetime.timedelta(days=days)

    qs = (
        Audit.objects.filter(tenant_id=tenant_id)
        .exclude(AuditType='A')
        .filter(_under_review_filter())
        .filter(ReviewStartDate__isnull=False, ReviewStartDate__lte=cutoff)
        .select_related('Reviewer', 'FrameworkId', 'Auditor')
        .order_by('ReviewStartDate', 'AuditId')
    )
    if not include_not_yet_escalated:
        qs = qs.filter(ReviewEscalatedAt__isnull=False)

    items = []
    for audit in qs[:200]:
        reviewer = audit.Reviewer
        auditor = audit.Auditor
        fw = audit.FrameworkId
        items.append(
            {
                'audit_id': audit.AuditId,
                'title': display_audit_title(audit.Title),
                'review_start_date': (
                    audit.ReviewStartDate.date().isoformat() if audit.ReviewStartDate else None
                ),
                'review_escalated_at': (
                    audit.ReviewEscalatedAt.isoformat() if audit.ReviewEscalatedAt else None
                ),
                'status': audit.Status,
                'reviewer_id': reviewer.UserId if reviewer else None,
                'reviewer_name': reviewer.UserName if reviewer else None,
                'auditor_id': auditor.UserId if auditor else None,
                'auditor_name': auditor.UserName if auditor else None,
                'framework_id': fw.FrameworkId if fw else None,
                'framework_name': getattr(fw, 'FrameworkName', None) if fw else None,
            }
        )
    return items
