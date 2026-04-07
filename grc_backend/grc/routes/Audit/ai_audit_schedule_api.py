"""
AI Audit Schedule API - Create, list, update, delete scheduled AI audits
"""
import logging
import re
from datetime import timedelta, datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect as csrf_exempt
from django.db import connection
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response

from ...rbac.utils import RBACUtils
from ...tenant_utils import tenant_filter, get_tenant_id_from_request
from ...models import (
    AIAuditSchedule,
    AIAuditScheduleRun,
    Audit,
    CompanyFolder,
    CompanySubfolder,
    Compliance,
    FileOperations,
)

logger = logging.getLogger(__name__)


def _get_document_ids_for_schedule(schedule):
    """Return document_ids for a schedule. For company_folder: docs from DH; else: all audit docs."""
    audit_id = schedule.audit_id
    company_folder_id = getattr(schedule, 'company_folder_id', None)
    if not company_folder_id:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT document_id FROM ai_audit_data WHERE audit_id = %s AND document_id IS NOT NULL AND document_id > 0 ORDER BY document_id",
                [int(audit_id)]
            )
            return [r[0] for r in cur.fetchall()]
    try:
        company_folder = CompanyFolder.objects.get(folder_id=company_folder_id, is_active=True)
    except CompanyFolder.DoesNotExist:
        return []
    with connection.cursor() as cur:
        cur.execute("SELECT FrameworkId FROM audit WHERE AuditId = %s LIMIT 1", [int(audit_id)])
        row = cur.fetchone()
        if not row or not row[0]:
            return []
        framework_id = row[0]
    code = (company_folder.code or '').strip().lower()
    code_safe = re.sub(r'[^a-z0-9]+', '_', code).strip('_') or 'na'
    subfolder_prefix = None
    company_subfolder_id = getattr(schedule, 'company_subfolder_id', None)
    if company_subfolder_id:
        try:
            subfolder = CompanySubfolder.objects.get(
                subfolder_id=company_subfolder_id,
                company_folder_id=company_folder_id,
                is_active=True
            )
            sub_code = (subfolder.code or '').strip().lower()
            sub_safe = re.sub(r'[^a-z0-9]+', '_', sub_code).strip('_') or 'na'
            subfolder_prefix = f"{code_safe}_{sub_safe}_"
        except CompanySubfolder.DoesNotExist:
            pass
    company_filter = (
        Q(file_name__istartswith=f"{code_safe}_") |
        Q(file_name__icontains=code_safe) |
        Q(stored_name__icontains=code_safe) |
        Q(s3_key__icontains=code_safe)
    )
    if subfolder_prefix:
        company_filter = company_filter & (
            Q(file_name__istartswith=subfolder_prefix) |
            Q(stored_name__icontains=subfolder_prefix) |
            Q(s3_key__icontains=subfolder_prefix)
        )
    file_ops = list(
        FileOperations.objects.filter(
            operation_type='upload', FrameworkId=framework_id, status='completed'
        ).filter(company_filter).exclude(user_id='export_user').values_list('id', flat=True)[:500]
    )
    if not file_ops:
        file_ops = list(
            FileOperations.objects.filter(
                operation_type='upload', status='completed'
            ).filter(company_filter).exclude(user_id='export_user').values_list('id', flat=True)[:500]
        )
    if not file_ops:
        return []
    ext_ids = [str(x) for x in file_ops]
    placeholders = ','.join(['%s'] * len(ext_ids))
    with connection.cursor() as cur:
        cur.execute(
            f"SELECT DISTINCT id FROM ai_audit_data WHERE audit_id = %s AND external_source = 'evidence_attachment' AND external_id IN ({placeholders}) AND document_id IS NOT NULL ORDER BY id",
            [int(audit_id)] + ext_ids
        )
        return [r[0] for r in cur.fetchall()]


def _get_document_details_for_schedule(schedule):
    """Return list of {document_id, document_name, document_type} for this schedule so the UI can show which documents are used (even when main document list is empty). For company folder with no runs yet, preview from file_operations."""
    audit_id = schedule.audit_id
    company_folder_id = getattr(schedule, 'company_folder_id', None)
    document_ids = _get_document_ids_for_schedule(schedule)
    if document_ids:
        with connection.cursor() as cur:
            placeholders = ','.join(['%s'] * len(document_ids))
            id_list = [int(x) for x in document_ids]
            if company_folder_id:
                cur.execute(
                    f"SELECT id, document_id, document_name, document_type FROM ai_audit_data WHERE audit_id = %s AND id IN ({placeholders}) ORDER BY document_name",
                    [int(audit_id)] + id_list,
                )
            else:
                cur.execute(
                    f"SELECT id, document_id, document_name, document_type FROM ai_audit_data WHERE audit_id = %s AND document_id IN ({placeholders}) ORDER BY document_name",
                    [int(audit_id)] + id_list,
                )
            return [
                {'document_id': r[1] or r[0], 'document_name': (r[2] or 'document')[:255], 'document_type': (r[3] or 'file')[:50]}
                for r in cur.fetchall()
            ]
    # Company folder but no ai_audit_data rows yet (no run): preview from file_operations
    company_folder_id = getattr(schedule, 'company_folder_id', None)
    if not company_folder_id:
        return []
    try:
        company_folder = CompanyFolder.objects.get(folder_id=company_folder_id, is_active=True)
    except CompanyFolder.DoesNotExist:
        return []
    with connection.cursor() as cur:
        cur.execute("SELECT FrameworkId FROM audit WHERE AuditId = %s LIMIT 1", [int(audit_id)])
        row = cur.fetchone()
        if not row or not row[0]:
            return []
        framework_id = row[0]
    code = (company_folder.code or '').strip().lower()
    code_safe = re.sub(r'[^a-z0-9]+', '_', code).strip('_') or 'na'
    company_filter = (
        Q(file_name__istartswith=f"{code_safe}_") |
        Q(file_name__icontains=code_safe) |
        Q(stored_name__icontains=code_safe) |
        Q(s3_key__icontains=code_safe)
    )
    if getattr(schedule, 'company_subfolder_id', None):
        try:
            subfolder = CompanySubfolder.objects.get(
                subfolder_id=schedule.company_subfolder_id,
                company_folder_id=company_folder_id,
                is_active=True,
            )
            sub_code = (subfolder.code or '').strip().lower()
            sub_safe = re.sub(r'[^a-z0-9]+', '_', sub_code).strip('_') or 'na'
            sub_prefix = f"{code_safe}_{sub_safe}_"
            company_filter = company_filter & (
                Q(file_name__istartswith=sub_prefix) |
                Q(stored_name__icontains=sub_prefix) |
                Q(s3_key__icontains=sub_prefix)
            )
        except CompanySubfolder.DoesNotExist:
            pass
    file_ops = list(
        FileOperations.objects.filter(
            operation_type='upload', FrameworkId=framework_id, status='completed',
        ).filter(company_filter).exclude(user_id='export_user').values_list('id', 'file_name', 'file_type', 'original_name')[:100]
    )
    if not file_ops:
        file_ops = list(
            FileOperations.objects.filter(
                operation_type='upload', status='completed',
            ).filter(company_filter).exclude(user_id='export_user').values_list('id', 'file_name', 'file_type', 'original_name')[:100]
        )
    return [
        {'document_id': fo[0], 'document_name': (fo[1] or fo[3] or 'document')[:255], 'document_type': (fo[2] or 'file')[:50]}
        for fo in file_ops
    ]


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        pass


def _compute_next_run(schedule_type, scheduled_at=None, cron_expression=None, base_time=None):
    """Compute next_run_at from schedule_type and params. base_time: use this instead of now (e.g. start_date)."""
    now = base_time if base_time else timezone.now()

    # Custom cron expression (5 fields: minute hour day month day_of_week)
    if schedule_type == 'cron' and cron_expression and cron_expression.strip():
        try:
            from croniter import croniter
            cron_expression = cron_expression.strip()
            parts = cron_expression.split()
            if len(parts) == 5:
                it = croniter(cron_expression, now)
                next_dt = it.get_next(datetime)
                if timezone.is_naive(next_dt) and getattr(settings, 'USE_TZ', True):
                    next_dt = timezone.make_aware(next_dt)
                return next_dt
            return None
        except Exception:
            return None

    if schedule_type == 'one_week':
        if scheduled_at:
            return scheduled_at
        return now + timedelta(days=7)
    if schedule_type == 'one_minute':
        return now + timedelta(minutes=1)
    if schedule_type == 'exact_date':
        return scheduled_at
    if schedule_type == 'every_minute' and cron_expression:
        # cron_expression is "minute" only; run every minute
        return now + timedelta(minutes=1)
    if schedule_type == 'daily' and cron_expression:
        parts = cron_expression.strip().split()
        if len(parts) >= 2:
            try:
                minute, hour = int(parts[0]), int(parts[1])
                candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if candidate <= now:
                    candidate += timedelta(days=1)
                return candidate
            except (ValueError, IndexError):
                pass
        return None
    if schedule_type == 'monthly' and cron_expression:
        parts = cron_expression.strip().split()
        if len(parts) >= 3:
            try:
                minute, hour, dom = int(parts[0]), int(parts[1]), int(parts[2])
                dom = max(1, min(28, dom))  # 1-28 to avoid month-end issues
                # Run 5 days before the selected day of month (so audit is done before the target day)
                target = now.replace(day=dom, hour=hour, minute=minute, second=0, microsecond=0)
                candidate = target - timedelta(days=5)
                if candidate <= now:
                    if target.month == 12:
                        target = target.replace(year=target.year + 1, month=1)
                    else:
                        target = target.replace(month=target.month + 1)
                    candidate = target - timedelta(days=5)
                return candidate
            except (ValueError, IndexError, TypeError):
                pass
        return None
    if schedule_type == 'recurring' and cron_expression:
        parts = cron_expression.strip().split()
        if len(parts) >= 5:
            try:
                minute, hour = int(parts[0]), int(parts[1])
                dow = int(parts[4])
                cron_to_weekday = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
                target_weekday = cron_to_weekday.get(dow, dow)
                days_ahead = (target_weekday - now.weekday() + 7) % 7
                candidate = (now + timedelta(days=days_ahead)).replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                if candidate <= now:
                    candidate += timedelta(days=7)
                return candidate
            except (ValueError, IndexError):
                pass
    # Quarterly from start_date: every 3 months from start_date at same day-of-month and time
    if schedule_type == 'quarterly':
        # At create, caller passes start_date as base_time; we use it as series start
        return _compute_next_run_quarterly(
            start_date=now,
            cron_expression=cron_expression,
            base_time=now,
        )
    # Yearly: run 30 days before target date (start_date's month/day) each year
    if schedule_type == 'yearly':
        return _compute_next_run_yearly(
            start_date=now,  # at create, base_time is start_date (target date)
            cron_expression=cron_expression,
            base_time=now,
        )
    return None


def _compute_next_run_quarterly(start_date, cron_expression, base_time):
    """Next run = first (start_date + 3*k months) at hour:minute >= base_time. cron_expression is 'minute hour'."""
    if not start_date:
        return None
    if timezone.is_naive(start_date) and getattr(settings, 'USE_TZ', True):
        start_date = timezone.make_aware(start_date)
    minute, hour = 0, 9
    if cron_expression and cron_expression.strip():
        parts = cron_expression.strip().split()
        if len(parts) >= 2:
            try:
                minute, hour = int(parts[0]), int(parts[1])
            except (ValueError, TypeError):
                pass
    # First occurrence at start_date's calendar day and time
    candidate = start_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate < base_time:
        # Advance by 3 months until >= base_time
        k = 0
        while candidate < base_time:
            k += 1
            candidate = start_date + relativedelta(months=3 * k)
            candidate = candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if timezone.is_naive(candidate) and getattr(settings, 'USE_TZ', True):
                candidate = timezone.make_aware(candidate)
    return candidate


def _compute_next_run_yearly(start_date, cron_expression, base_time):
    """Next run = (target date - 1 month) at hour:minute. Target = start_date's month/day (this or next year)."""
    if not start_date:
        return None
    if timezone.is_naive(start_date) and getattr(settings, 'USE_TZ', True):
        start_date = timezone.make_aware(start_date)
    minute, hour = 0, 9
    if cron_expression and cron_expression.strip():
        parts = cron_expression.strip().split()
        if len(parts) >= 2:
            try:
                minute, hour = int(parts[0]), int(parts[1])
            except (ValueError, TypeError):
                pass
    # Target = start_date's month/day in base_time's year at hour:minute; run = target - 1 month
    target = base_time.replace(month=start_date.month, day=min(start_date.day, 28), hour=hour, minute=minute, second=0, microsecond=0)
    candidate = target - relativedelta(months=1)
    if timezone.is_naive(candidate) and getattr(settings, 'USE_TZ', True):
        candidate = timezone.make_aware(candidate)
    if candidate < base_time:
        target = target + relativedelta(years=1)
        candidate = target - relativedelta(months=1)
        if timezone.is_naive(candidate) and getattr(settings, 'USE_TZ', True):
            candidate = timezone.make_aware(candidate)
    return candidate


def _day_to_cron_dow(day_num):
    """Python weekday (Mon=0, Sun=6) to cron dow (Sun=0, Mon=1, ..., Sat=6)."""
    return {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}.get(day_num, 1)


def _schedule_to_dict(s):
    d = {
        'id': s.id,
        'audit_id': s.audit_id,
        'schedule_type': s.schedule_type,
        'scheduled_at': s.scheduled_at.isoformat() if s.scheduled_at else None,
        'cron_expression': s.cron_expression,
        'is_active': s.is_active,
        'last_run_at': s.last_run_at.isoformat() if s.last_run_at else None,
        'next_run_at': s.next_run_at.isoformat() if s.next_run_at else None,
        'start_date': (lambda d: d.isoformat() if d else None)(getattr(s, 'start_date', None)),
        'created_at': s.created_at.isoformat() if s.created_at else None,
    }
    if hasattr(s, 'company_folder_id') and s.company_folder_id:
        d['company_folder_id'] = s.company_folder_id
        if hasattr(s, 'company_folder') and s.company_folder:
            d['company_folder_name'] = getattr(s.company_folder, 'name', None) or getattr(s.company_folder, 'code', None)
        else:
            d['company_folder_name'] = None
    else:
        d['company_folder_id'] = None
        d['company_folder_name'] = None
    if hasattr(s, 'company_subfolder_id') and s.company_subfolder_id:
        d['company_subfolder_id'] = s.company_subfolder_id
        if hasattr(s, 'company_subfolder') and s.company_subfolder:
            d['company_subfolder_name'] = getattr(s.company_subfolder, 'name', None) or getattr(s.company_subfolder, 'code', None)
    else:
        d['company_subfolder_id'] = None
        d['company_subfolder_name'] = None
    d['selected_compliance_ids'] = getattr(s, 'selected_compliance_ids', None) or []
    # Mark schedule as running if there is an active run with status='running' and no finished_at
    try:
        running_exists = AIAuditScheduleRun.objects.filter(
            schedule_id=s.id,
            status='running',
            finished_at__isnull=True,
        ).exists()
        d['is_running'] = bool(running_exists)
    except Exception as e:
        logger.warning("Could not determine running status for schedule %s: %s", s.id, e)
        d['is_running'] = False
    try:
        d['document_ids'] = _get_document_ids_for_schedule(s)
    except Exception as e:
        logger.warning("Could not get document_ids for schedule %s: %s", s.id, e)
        d['document_ids'] = []
    try:
        d['document_details'] = _get_document_details_for_schedule(s)
    except Exception as e:
        logger.warning("Could not get document_details for schedule %s: %s", s.id, e)
        d['document_details'] = []
    return d


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@tenant_filter  # Optional: adds tenant if available, doesn't block
def create_ai_audit_schedule(request, audit_id):
    """Create a scheduled AI audit."""
    user_id = RBACUtils.get_user_id_from_request(request)
    if not user_id:
        return Response({'success': False, 'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    tenant_id = get_tenant_id_from_request(request)
    audit_id = int(audit_id) if str(audit_id).isdigit() else None
    if not audit_id:
        return Response({'success': False, 'error': 'Invalid audit ID'}, status=status.HTTP_400_BAD_REQUEST)

    # Lookup audit: try audit table first, then ai_audit_data (documents prove audit exists)
    audit_tenant_id = None
    framework_id = None
    with connection.cursor() as cursor:
        for q, params in [
            ("SELECT TenantId, FrameworkId FROM audit WHERE AuditId = %s LIMIT 1", [audit_id]),
            ("SELECT tenant_id, framework_id FROM audit WHERE audit_id = %s LIMIT 1", [audit_id]),
        ]:
            try:
                cursor.execute(q, params)
                row = cursor.fetchone()
                if row:
                    audit_tenant_id = row[0]
                    framework_id = row[1] if len(row) > 1 else None
                    break
            except Exception:
                pass

    if audit_tenant_id is None:
        # Fallback: if ai_audit_data has documents for this audit, treat it as valid
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    "SELECT 1 FROM ai_audit_data WHERE audit_id = %s LIMIT 1",
                    [audit_id]
                )
                row = cursor.fetchone()
            except Exception:
                row = None
        if not row:
            return Response({'success': False, 'error': 'Audit not found'}, status=status.HTTP_404_NOT_FOUND)
        audit_tenant_id = None  # Use request tenant or None for schedule
    # Do not block on tenant mismatch - user reached this page and has documents, so allow

    data = request.data
    schedule_type = data.get('schedule_type')
    if schedule_type not in ('one_week', 'one_minute', 'exact_date', 'recurring', 'daily', 'monthly', 'every_minute', 'cron', 'quarterly', 'yearly'):
        return Response({'success': False, 'error': 'Invalid schedule_type'}, status=status.HTTP_400_BAD_REQUEST)

    scheduled_at = None
    cron_expression = None

    def _parse_datetime(s):
        if not s:
            return None
        s = str(s).strip().replace('Z', '').replace('+00:00', '')
        # Strip milliseconds if present (e.g. .000)
        if '.' in s:
            s = s.split('.')[0]
        for fmt in (
            '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d',
            '%d-%m-%YT%H:%M:%S', '%d-%m-%YT%H:%M', '%d-%m-%Y %H:%M:%S', '%d-%m-%Y %H:%M', '%d-%m-%Y',
            '%d/%m/%YT%H:%M:%S', '%d/%m/%YT%H:%M', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y',
        ):
            try:
                dt = datetime.strptime(s, fmt)
                return timezone.make_aware(dt) if dt.tzinfo is None and getattr(settings, 'USE_TZ', True) else dt
            except (ValueError, TypeError):
                continue
        return None

    if schedule_type == 'one_week':
        scheduled_at = timezone.now() + timedelta(days=7)
        if data.get('scheduled_at'):
            parsed = _parse_datetime(data['scheduled_at'])
            if parsed:
                scheduled_at = parsed

    elif schedule_type == 'one_minute':
        scheduled_at = timezone.now() + timedelta(minutes=1)

    elif schedule_type == 'exact_date':
        sd = data.get('scheduled_at') or data.get('scheduledAt')
        if not sd:
            return Response({'success': False, 'error': 'scheduled_at required for exact_date'}, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(sd, (int, float)):
            try:
                ts = int(sd) / 1000.0 if int(sd) > 1e12 else int(sd)
                scheduled_at = datetime.fromtimestamp(ts)
                if getattr(settings, 'USE_TZ', True) and timezone.is_naive(scheduled_at):
                    scheduled_at = timezone.make_aware(scheduled_at)
            except (ValueError, OSError):
                scheduled_at = None
        else:
            scheduled_at = _parse_datetime(str(sd).strip())
        if not scheduled_at:
            logger.warning('Invalid scheduled_at format: %r', sd)
            return Response({'success': False, 'error': 'Invalid scheduled_at format. Use YYYY-MM-DDTHH:mm:ss or DD-MM-YYYYTHH:mm:ss'}, status=status.HTTP_400_BAD_REQUEST)

    elif schedule_type == 'every_minute':
        cron_expression = '* * * * *'  # every minute; stored so column is populated

    elif schedule_type == 'daily':
        hour = int(data.get('hour', 9))
        minute = int(data.get('minute', 0))
        cron_expression = f'{minute} {hour} * * *'

    elif schedule_type == 'monthly':
        day_of_month = int(data.get('day_of_month', 1))
        day_of_month = max(1, min(28, day_of_month))
        hour = int(data.get('hour', 9))
        minute = int(data.get('minute', 0))
        cron_expression = f'{minute} {hour} {day_of_month} * *'

    elif schedule_type == 'recurring':
        day_of_week = data.get('day_of_week', 1)  # 0=Mon, 6=Sun (Python weekday)
        hour = int(data.get('hour', 9))
        minute = int(data.get('minute', 0))
        cron_dow = _day_to_cron_dow(day_of_week)
        cron_expression = f'{minute} {hour} * * {cron_dow}'

    elif schedule_type == 'cron':
        cron_expression = (data.get('cron_expression') or data.get('cronExpression') or '').strip()
        if not cron_expression:
            return Response({'success': False, 'error': 'cron_expression required for cron schedule (5 fields: minute hour day month day_of_week)'}, status=status.HTTP_400_BAD_REQUEST)
        parts = cron_expression.split()
        if len(parts) != 5:
            return Response({'success': False, 'error': 'cron_expression must have 5 fields: minute hour day_of_month month day_of_week (e.g. "0 9 * * 1-5")'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from croniter import croniter
            croniter(cron_expression, timezone.now()).get_next(datetime)
        except ImportError as e:
            return Response({'success': False, 'error': 'Server missing croniter package. Install with: pip install croniter'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'success': False, 'error': f'Invalid cron expression: An internal server error occurred'}, status=status.HTTP_400_BAD_REQUEST)

    elif schedule_type == 'quarterly':
        # Quarterly from start_date: every 3 months from start_date at same day and time. start_date required.
        if not data.get('start_date'):
            return Response({'success': False, 'error': 'start_date is required for quarterly schedule'}, status=status.HTTP_400_BAD_REQUEST)
        hour = int(data.get('hour', 9))
        minute = int(data.get('minute', 0))
        cron_expression = f'{minute} {hour}'  # time of day; next_run uses start_date + 3*k months

    elif schedule_type == 'yearly':
        # Yearly: run 30 days before the target date each year. start_date = target date (month/day used).
        if not data.get('start_date'):
            return Response({'success': False, 'error': 'start_date (target date) is required for yearly schedule'}, status=status.HTTP_400_BAD_REQUEST)
        hour = int(data.get('hour', 9))
        minute = int(data.get('minute', 0))
        cron_expression = f'{minute} {hour}'  # time of day; next_run = (target date - 30 days)

    start_date = None
    if data.get('start_date'):
        start_date = _parse_datetime(data.get('start_date'))
        if start_date and start_date.tzinfo is None and getattr(settings, 'USE_TZ', True):
            start_date = timezone.make_aware(start_date)

    recurring_types = ('recurring', 'daily', 'monthly', 'every_minute', 'cron', 'quarterly', 'yearly')
    if start_date and schedule_type in recurring_types:
        next_run = _compute_next_run(schedule_type, scheduled_at, cron_expression, base_time=start_date)
    else:
        next_run = _compute_next_run(schedule_type, scheduled_at, cron_expression)
    if not next_run:
        return Response({'success': False, 'error': 'Could not compute next run time. Check cron expression or install croniter: pip install croniter'}, status=status.HTTP_400_BAD_REQUEST)
    if start_date and next_run < start_date:
        next_run = start_date

    schedule_tenant_id = tenant_id if tenant_id is not None else audit_tenant_id

    company_folder_id = data.get('company_folder_id')
    if company_folder_id is not None:
        company_folder_id = int(company_folder_id) if str(company_folder_id).isdigit() else None
    company_subfolder_id = data.get('company_subfolder_id')
    if company_subfolder_id is not None:
        company_subfolder_id = int(company_subfolder_id) if str(company_subfolder_id).isdigit() else None
    if company_subfolder_id and not company_folder_id:
        company_subfolder_id = None  # subfolder requires company folder
    if company_folder_id:
        try:
            CompanyFolder.objects.get(folder_id=company_folder_id, is_active=True)
        except CompanyFolder.DoesNotExist:
            return Response({'success': False, 'error': 'Company folder not found'}, status=status.HTTP_400_BAD_REQUEST)
    if company_subfolder_id and company_folder_id:
        try:
            CompanySubfolder.objects.get(subfolder_id=company_subfolder_id, company_folder_id=company_folder_id, is_active=True)
        except CompanySubfolder.DoesNotExist:
            return Response({'success': False, 'error': 'Subfolder not found or does not belong to selected company folder'}, status=status.HTTP_400_BAD_REQUEST)

    selected_compliance_ids = data.get('selected_compliance_ids')
    if selected_compliance_ids is not None:
        if isinstance(selected_compliance_ids, (list, tuple)):
            selected_compliance_ids = [int(x) for x in selected_compliance_ids if str(x).isdigit()]
        else:
            selected_compliance_ids = []
        if not selected_compliance_ids:
            selected_compliance_ids = None
    else:
        selected_compliance_ids = None

    # When scheduling a monthly AI audit, restrict scope to compliances
    # explicitly marked as Monthly in the compliance table.
    if schedule_type == 'monthly' and framework_id:
        try:
            monthly_qs = Compliance.objects.filter(
                FrameworkId_id=framework_id,
                AuditFrequency__iexact='monthly',
            )
            # If tenant scoping is available for schedule, respect it
            schedule_tenant_id = tenant_id if tenant_id is not None else audit_tenant_id
            if schedule_tenant_id is not None:
                monthly_qs = monthly_qs.filter(tenant_id=schedule_tenant_id)

            monthly_ids = list(
                monthly_qs.values_list('ComplianceId', flat=True)
            )
            monthly_ids = [int(cid) for cid in monthly_ids if cid is not None]
            selected_compliance_ids = monthly_ids or None
        except Exception as e:
            logger.warning("Could not restrict monthly schedule compliances: %s", e)

    # Ensure cron_expression is always stored for recurring types (so DB column is populated)
    if schedule_type in ('every_minute', 'daily', 'monthly', 'recurring', 'cron', 'quarterly', 'yearly') and cron_expression is None:
        cron_expression = ''
    try:
        schedule = AIAuditSchedule.objects.create(
            tenant_id=schedule_tenant_id,
            audit_id=audit_id,
            company_folder_id=company_folder_id,
            company_subfolder_id=company_subfolder_id,
            selected_compliance_ids=selected_compliance_ids,
            schedule_type=schedule_type,
            scheduled_at=scheduled_at,
            cron_expression=cron_expression or None,
            start_date=start_date,
            created_by_id=user_id,
            is_active=True,
            next_run_at=next_run,
        )
        if cron_expression:
            logger.info('AIAuditSchedule created id=%s schedule_type=%s cron_expression=%s', schedule.id, schedule_type, cron_expression)
    except Exception as e:
        logger.exception('Create AI audit schedule failed')
        from django.db import IntegrityError
        if isinstance(e, IntegrityError):
            return Response({'success': False, 'error': 'Invalid audit, company folder, or tenant. Check that the company folder exists and belongs to this context.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({'success': True, 'schedule': _schedule_to_dict(schedule)}, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@tenant_filter
def list_ai_audit_schedules(request, audit_id):
    """List all schedules for an audit."""
    tenant_id = get_tenant_id_from_request(request)
    audit_id = int(audit_id) if str(audit_id).isdigit() else None
    if not audit_id:
        return Response({'success': False, 'error': 'Invalid audit ID'}, status=status.HTTP_400_BAD_REQUEST)

    qs = AIAuditSchedule.objects.filter(audit_id=audit_id).select_related('company_folder', 'company_subfolder')
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    schedules = list(qs.order_by('-created_at'))
    return Response({
        'success': True,
        'schedules': [_schedule_to_dict(s) for s in schedules]
    })


@csrf_exempt
@api_view(['PATCH', 'DELETE'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@tenant_filter
def update_or_delete_ai_audit_schedule(request, schedule_id):
    """Update (toggle is_active) or delete a schedule."""
    tenant_id = get_tenant_id_from_request(request)
    schedule_id = int(schedule_id) if str(schedule_id).isdigit() else None
    if not schedule_id:
        return Response({'success': False, 'error': 'Invalid schedule ID'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        schedule = AIAuditSchedule.objects.get(id=schedule_id)
    except AIAuditSchedule.DoesNotExist:
        return Response({'success': False, 'error': 'Schedule not found'}, status=status.HTTP_404_NOT_FOUND)

    if tenant_id and schedule.tenant_id != tenant_id:
        return Response({'success': False, 'error': 'Schedule not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        schedule.delete()
        return Response({'success': True, 'message': 'Schedule deleted'})

    # PATCH - toggle is_active or update
    data = request.data
    if 'is_active' in data:
        schedule.is_active = bool(data['is_active'])
    schedule.save()
    return Response({'success': True, 'schedule': _schedule_to_dict(schedule)})


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@tenant_filter
def list_ai_audit_schedule_runs(request, schedule_id):
    """List run history for a schedule."""
    tenant_id = get_tenant_id_from_request(request)
    schedule_id = int(schedule_id) if str(schedule_id).isdigit() else None
    if not schedule_id:
        return Response({'success': False, 'error': 'Invalid schedule ID'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        schedule = AIAuditSchedule.objects.get(id=schedule_id)
    except AIAuditSchedule.DoesNotExist:
        return Response({'success': False, 'error': 'Schedule not found'}, status=status.HTTP_404_NOT_FOUND)

    if tenant_id and schedule.tenant_id != tenant_id:
        return Response({'success': False, 'error': 'Schedule not found'}, status=status.HTTP_404_NOT_FOUND)

    runs = AIAuditScheduleRun.objects.filter(schedule_id=schedule_id).order_by('-started_at')[:20]
    return Response({
        'success': True,
        'runs': [
            {
                'id': r.id,
                'started_at': r.started_at.isoformat() if r.started_at else None,
                'finished_at': r.finished_at.isoformat() if r.finished_at else None,
                'status': r.status,
                'result_summary': r.result_summary,
                'error_message': r.error_message,
            }
            for r in runs
        ]
    })


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@tenant_filter
def run_ai_audit_schedules_for_audit(request, audit_id):
    """
    Trigger all active AI audit schedules for a given audit once (manual run).
    Used by EventHandling calendar to run the AI audit cycle for an audit on demand.
    """
    from grc.routes.Audit.run_scheduled_ai_audits import _run_scheduled_audit, _compute_next_run  # type: ignore

    tenant_id = get_tenant_id_from_request(request)
    audit_id_int = int(audit_id) if str(audit_id).isdigit() else None
    if not audit_id_int:
        return Response({'success': False, 'error': 'Invalid audit ID'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        schedules_qs = AIAuditSchedule.objects.filter(audit_id=audit_id_int, is_active=True)
        if tenant_id:
            schedules_qs = schedules_qs.filter(tenant_id=tenant_id)
        schedules = list(schedules_qs)
        if not schedules:
            return Response(
                {'success': False, 'error': 'No active AI audit schedules found for this audit'},
                status=status.HTTP_404_NOT_FOUND,
            )

        results = []
        for schedule in schedules:
            run_record = AIAuditScheduleRun.objects.create(
                schedule=schedule,
                started_at=timezone.now(),
                status='running',
            )
            try:
                result = _run_scheduled_audit(schedule)
                run_record.finished_at = timezone.now()
                run_record.status = 'success' if result.get('success') else 'failed'
                run_record.result_summary = result
                if not result.get('success'):
                    run_record.error_message = result.get('error', 'Unknown error')
            except Exception as e:
                run_record.finished_at = timezone.now()
                run_record.status = 'failed'
                run_record.error_message = str(e)
                run_record.result_summary = {'success': False, 'error': str(e)}
                logger.exception("Manual run for scheduled audit %s failed: %s", schedule.id, e)
            run_record.save()

            # Update schedule next_run_at similar to management command
            schedule.last_run_at = run_record.started_at
            if schedule.schedule_type in ('recurring', 'daily', 'monthly', 'every_minute', 'cron', 'quarterly', 'yearly'):
                try:
                    schedule.next_run_at = _compute_next_run(schedule)
                except Exception:
                    schedule.next_run_at = None
            else:
                schedule.next_run_at = None
                schedule.is_active = False
            schedule.save()

            results.append(
                {
                    'schedule_id': schedule.id,
                    'status': run_record.status,
                    'result': run_record.result_summary,
                }
            )

        overall_success = any(r['status'] == 'success' for r in results)
        return Response({'success': overall_success, 'results': results})
    except Exception as e:
        logger.exception("Error running AI audit schedules for audit %s: %s", audit_id, e)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
