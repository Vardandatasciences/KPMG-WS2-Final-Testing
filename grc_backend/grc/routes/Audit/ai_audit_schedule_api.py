"""
AI Audit Schedule API - Create, list, update, delete scheduled AI audits
"""
import logging
import re
from datetime import timedelta, datetime

from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response

from ...rbac.utils import RBACUtils
from ...tenant_utils import tenant_filter, get_tenant_id_from_request
from ...models import AIAuditSchedule, AIAuditScheduleRun, Audit, CompanyFolder, CompanySubfolder, FileOperations

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
                candidate = now.replace(day=dom, hour=hour, minute=minute, second=0, microsecond=0)
                if candidate <= now:
                    if candidate.month == 12:
                        candidate = candidate.replace(year=candidate.year + 1, month=1)
                    else:
                        candidate = candidate.replace(month=candidate.month + 1)
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
    return None


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
    try:
        d['document_ids'] = _get_document_ids_for_schedule(s)
    except Exception as e:
        logger.warning("Could not get document_ids for schedule %s: %s", s.id, e)
        d['document_ids'] = []
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
    with connection.cursor() as cursor:
        for q, params in [
            ("SELECT TenantId FROM audit WHERE AuditId = %s LIMIT 1", [audit_id]),
            ("SELECT tenant_id FROM audit WHERE audit_id = %s LIMIT 1", [audit_id]),
        ]:
            try:
                cursor.execute(q, params)
                row = cursor.fetchone()
                if row:
                    audit_tenant_id = row[0]
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
    if schedule_type not in ('one_week', 'one_minute', 'exact_date', 'recurring', 'daily', 'monthly', 'every_minute', 'cron'):
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
            return Response({'success': False, 'error': f'Invalid cron expression: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    start_date = None
    if data.get('start_date'):
        start_date = _parse_datetime(data.get('start_date'))
        if start_date and start_date.tzinfo is None and getattr(settings, 'USE_TZ', True):
            start_date = timezone.make_aware(start_date)

    recurring_types = ('recurring', 'daily', 'monthly', 'every_minute', 'cron')
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

    # Ensure cron_expression is always stored for recurring types (so DB column is populated)
    if schedule_type in ('every_minute', 'daily', 'monthly', 'recurring', 'cron') and cron_expression is None:
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
