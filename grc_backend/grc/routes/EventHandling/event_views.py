from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.db import models
from django.db import close_old_connections
import logging
import threading
from django.utils import timezone
from datetime import date, datetime as dt_datetime, timedelta
import json

def _format_datetime_ist(dt):
    """
    Format datetime for display - time is already in IST, just format it
    """
    if not dt:
        return ''
    try:
        # Time is already in IST, just format it
        return dt.strftime('%Y-%m-%d %H:%M IST')
    except Exception:
        # Fallback to original format if conversion fails
        try:
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return str(dt) if dt else ''

# RBAC imports
from ...rbac.permissions import (
    EventViewAllPermission, EventViewModulePermission, EventCreatePermission,
    EventEditPermission, EventApprovePermission, EventRejectPermission,
    EventArchivePermission, EventAnalyticsPermission, EventDashboardPermission,
    EventQueuePermission, EventCalendarPermission, EventExportPermission
)
from ...rbac.utils import RBACUtils
from ...routes.Consent import require_consent

# DRF Session auth variant that skips CSRF enforcement for API clients
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

from ...models import (
    Event, Framework, Policy, Compliance, Audit, Risk, Incident, 
    SubPolicy, Users, EventType, Module, FileOperations
)
from ...routes.Global.s3_fucntions import create_direct_mysql_client, export_data as s3_export_data
from ...utils.file_compression import decompress_if_needed

from ...debug_utils import debug_print
from ...utils.log_sanitize import sanitize_for_log
from ...utils.csv_security import sanitize_export_filename
from ...routes.Global.validation import SecureValidator, ValidationError as TrustedUrlValidationError
# MULTI-TENANCY: Import tenant utilities for data isolation
from ...tenant_utils import (
    require_tenant, tenant_filter, get_tenant_id_from_request,
    validate_tenant_access, get_tenant_aware_queryset
)
from ..Incident.system_risk_service import trigger_single_source_risk_scan
logger = logging.getLogger(__name__)

# SECURITY: S3 download / Content-Disposition hardening (header injection, CRLF, reflection).
_MAX_S3_DOWNLOAD_KEY_LEN = 2048
_MAX_S3_DOWNLOAD_FILENAME_LEN = 255


def _sanitize_s3_download_param(value, *, for_filename=False):
    """
    Normalize URL-decoded s3_key or file_name before headers, JSON, or backend calls.
    Strips control/non-printable characters, CRLF, limits length, and for filenames
    keeps basename only and removes characters that break Content-Disposition.
    """
    s = str(value or '')
    s = ''.join(ch for ch in s if ord(ch) >= 32 and ord(ch) != 127)
    if for_filename:
        s = s.replace('\\', '/').split('/')[-1]
        for bad in ('"', ';'):
            s = s.replace(bad, '')
        s = s.strip(' .')
        s = s[:_MAX_S3_DOWNLOAD_FILENAME_LEN]
    else:
        s = s[:_MAX_S3_DOWNLOAD_KEY_LEN]
    return s


def _sanitize_reflected_error_detail(value, max_len=500):
    """Single-line, bounded string safe for JSON bodies (reduces XSS/reflection and log forging)."""
    s = str(value or '')
    s = ''.join(ch for ch in s if ord(ch) >= 32 and ord(ch) != 127)
    if len(s) > max_len:
        s = s[:max_len] + '…'
    return s


def _log_exception(exc, *, context: str, max_len: int = 800) -> None:
    """Operator logging without full tracebacks (reduces secret/internal leakage via logs)."""
    safe_msg = sanitize_for_log(exc, max_len=max_len)
    # Always emit to backend logs so production/dev can diagnose 500s.
    logger.error("[EventHandling:%s] %s", context, safe_msg)
    debug_print(f"DEBUG: [{context}] {safe_msg}")


def _validate_event_evidence_s3_url(url, *, field_label='evidence.s3_url'):
    """
    Allow-list evidence URLs before persisting (mitigates SSRF / malicious links in UI).
    Uses the same TRUSTED_EVIDENCE_* settings as Risk/Incident modules.
    """
    if url is None or url == '':
        return None
    if not isinstance(url, str):
        raise ValueError('Evidence URL must be a string.')
    try:
        validated = SecureValidator.validate_trusted_url(
            url.strip(),
            field_label,
            allowed_hosts=getattr(settings, 'TRUSTED_EVIDENCE_URL_HOSTS', None) or [],
            allowed_host_suffixes=getattr(settings, 'TRUSTED_EVIDENCE_URL_HOST_SUFFIXES', None) or [],
            allow_http_hosts=getattr(settings, 'TRUSTED_EVIDENCE_URL_ALLOW_HTTP_HOSTS', None) or [],
        )
    except TrustedUrlValidationError as e:
        raise ValueError(getattr(e, 'message', None) or str(e) or 'Evidence URL is not allowed.') from e
    if not validated:
        raise ValueError('Evidence URL is not allowed.')
    return validated


# Shared with upload_event_evidence / attach_evidence (type + size guards)
_EVENT_EVIDENCE_ALLOWED_CONTENT_TYPES = frozenset({
    'application/pdf',
    'text/csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
})
_EVENT_EVIDENCE_MAX_BYTES = 10 * 1024 * 1024

_EVENT_ALLOWED_PRIORITIES = frozenset({'Critical', 'High', 'Medium', 'Low'})
_EVENT_ALLOWED_RECURRENCE = frozenset({'Non-Recurring', 'Recurring'})
_EVENT_LINKED_RECORD_TYPES = frozenset({
    'policy', 'compliance', 'audit', 'risk', 'incident', 'subpolicy', 'Jira Issue',
})
_EVENT_MAX_TITLE_LEN = 2155
_EVENT_MAX_MODULE_LEN = 255
_EVENT_MAX_FRAMEWORK_NAME_LEN = 255
_EVENT_MAX_LINKED_RECORD_NAME_LEN = 1000
_EVENT_MAX_CATEGORY_LEN = 100
_EVENT_SCHEMA_PRECHECK_DONE = False


def _event_schema_maintenance_allowed():
    """Schema DDL helpers only in DEBUG or when ALLOW_EVENT_SCHEMA_MAINTENANCE is set."""
    if getattr(settings, 'DEBUG', False):
        return True
    return getattr(settings, 'ALLOW_EVENT_SCHEMA_MAINTENANCE', False)


def _ensure_event_runtime_columns():
    """
    Best-effort compatibility for environments with partial migrations.
    Adds newer Event columns if missing so create_event won't 500 on unknown columns.
    """
    global _EVENT_SCHEMA_PRECHECK_DONE
    if _EVENT_SCHEMA_PRECHECK_DONE:
        return
    try:
        from django.db import connection
        ddl = (
            "ALTER TABLE events ADD COLUMN EventTypeId INT NULL",
            "ALTER TABLE events ADD COLUMN SubEventType VARCHAR(100) NULL",
            "ALTER TABLE events ADD COLUMN DynamicFieldsData JSON NULL",
            "ALTER TABLE events ADD COLUMN data_inventory JSON NULL",
        )
        with connection.cursor() as cursor:
            for stmt in ddl:
                try:
                    cursor.execute(stmt)
                except Exception:
                    # Column may already exist or DB may enforce strict JSON version rules.
                    # Keep best-effort behavior; create path still has explicit error handling.
                    pass
    except Exception:
        pass
    finally:
        _EVENT_SCHEMA_PRECHECK_DONE = True


def _normalize_event_priority(value):
    if value is None or value == '':
        return 'Medium'
    s = str(value).strip()
    if s not in _EVENT_ALLOWED_PRIORITIES:
        allowed = ', '.join(sorted(_EVENT_ALLOWED_PRIORITIES))
        raise ValueError(f'Priority must be one of: {allowed}.')
    return s


def _normalize_event_recurrence_type(value):
    if value is None or value == '':
        return 'Non-Recurring'
    s = str(value).strip()
    if s not in _EVENT_ALLOWED_RECURRENCE:
        allowed = ', '.join(sorted(_EVENT_ALLOWED_RECURRENCE))
        raise ValueError(f'Recurrence type must be one of: {allowed}.')
    return s


def _sanitize_optional_str_field(value, max_len, field_label):
    if value is None or value == '':
        return None
    s = str(value).strip()
    if len(s) > max_len:
        raise ValueError(f'{field_label} must be at most {max_len} characters.')
    return s


def _normalize_linked_record_type(value):
    if value is None or value == '':
        return None
    s = str(value).strip()
    if s in _EVENT_LINKED_RECORD_TYPES:
        return s
    normalized = s.lower().replace('_', ' ')
    head = normalized.split()[0] if normalized.split() else ''
    head_map = {
        'policy': 'policy',
        'compliance': 'compliance',
        'audit': 'audit',
        'risk': 'risk',
        'incident': 'incident',
        'subpolicy': 'subpolicy',
        'jira': 'Jira Issue',
    }
    if head in head_map:
        return head_map[head]
    allowed = ', '.join(sorted(_EVENT_LINKED_RECORD_TYPES))
    raise ValueError(f'linked_record_type must be one of: {allowed}.')


def _get_server_user_id(request):
    """
    Resolve the authenticated user identity from server-side auth context only.
    Client-supplied user_id values in query/body are intentionally ignored.
    """
    user_id = RBACUtils.get_user_id_from_request(request)
    return str(user_id) if user_id else None


def _parse_server_user_id_int(request):
    """Authenticated user id as int, or None if missing/invalid."""
    raw = _get_server_user_id(request)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _event_access_context(request):
    """
    Tenant + RBAC context for object-level event checks.
    Returns (tenant_id, user_id_int, permissions_dict, accessible_modules).
    """
    tenant_id = get_tenant_id_from_request(request)
    user_id_int = _parse_server_user_id_int(request)
    perms = RBACUtils.get_user_event_permissions(user_id_int) if user_id_int else {}
    modules = RBACUtils.get_user_accessible_modules(user_id_int) if user_id_int else []
    return tenant_id, user_id_int, perms, modules


def _user_can_view_event_object(user_id_int, perms, accessible_modules, event):
    """Whether the user may see or act on this event row (after tenant match)."""
    if not user_id_int or not perms:
        return False
    if perms.get('is_admin') or perms.get('view_all_event'):
        return True
    if perms.get('view_module_event'):
        mod = (event.Module or '').strip()
        if not mod or not accessible_modules:
            return False
        return mod in accessible_modules
    return False


def _guard_event_object_access(request, event):
    """
    Enforce tenant isolation + RBAC module scope on a single Event instance.
    Returns None if allowed, or (payload_dict, http_status) for the error response.
    """
    tenant_id, user_id_int, perms, modules = _event_access_context(request)
    if not user_id_int:
        return {'success': False, 'message': 'Authentication required'}, 401
    if tenant_id is None:
        return {'success': False, 'message': 'Event not found'}, 404
    if getattr(event, 'tenant_id', None) != tenant_id:
        return {'success': False, 'message': 'Event not found'}, 404
    if not _user_can_view_event_object(user_id_int, perms, modules, event):
        return {'success': False, 'message': 'Event not found'}, 404
    return None


def _apply_event_list_scope(qs, user_id_int):
    """
    Apply the same module-level visibility as list endpoints.
    Fail closed: users without view_all and without usable view_module see nothing.
    """
    if not user_id_int:
        return qs.none()
    perms = RBACUtils.get_user_event_permissions(user_id_int)
    modules = RBACUtils.get_user_accessible_modules(user_id_int)
    if perms.get('is_admin') or perms.get('view_all_event'):
        return qs
    if perms.get('view_module_event') and modules:
        return qs.filter(Module__in=modules)
    return qs.none()


def _get_event_for_tenant(tenant_id, event_id_raw, *, select_related=None, allow_generated_slug=True):
    """
    Load a single event by numeric EventId, or by EventId_Generated when allow_generated_slug=True.
    Raises Event.DoesNotExist when not found or tenant_id is None.
    """
    if tenant_id is None:
        raise Event.DoesNotExist
    rel = select_related or (
        'Owner', 'Reviewer', 'CreatedBy', 'FrameworkId', 'EventType'
    )
    if allow_generated_slug:
        try:
            eid = int(event_id_raw)
            return Event.objects.select_related(*rel).get(EventId=eid, tenant_id=tenant_id)
        except (ValueError, TypeError):
            return Event.objects.select_related(*rel).get(
                EventId_Generated=str(event_id_raw), tenant_id=tenant_id
            )
    try:
        eid = int(event_id_raw)
    except (ValueError, TypeError):
        raise Event.DoesNotExist
    return Event.objects.select_related(*rel).get(EventId=eid, tenant_id=tenant_id)


def _export_row_event_identifier(row):
    """Extract event id or generated code from a client export row (dict)."""
    if not isinstance(row, dict):
        return None
    for key in ('id', 'EventId', 'event_id', 'Event ID'):
        val = row.get(key)
        if val is None or val == '' or val == 'N/A':
            continue
        return val
    return None


def _event_to_export_row_dict(event):
    """Build export row dict aligned with frontend EventsList / EventsDashboard export keys."""
    owner_disp = event.owner_name if hasattr(event, 'owner_name') else ''
    rev_disp = event.reviewer_name if hasattr(event, 'reviewer_name') else ''
    created = event.CreatedAt.strftime('%Y-%m-%d %H:%M') if event.CreatedAt else 'N/A'
    updated = event.UpdatedAt.strftime('%Y-%m-%d %H:%M') if event.UpdatedAt else 'N/A'
    return {
        'Event ID': event.EventId,
        'Event Title': event.EventTitle or 'N/A',
        'Framework': event.FrameworkName or 'N/A',
        'Module': event.Module or 'N/A',
        'Category': event.Category or 'General',
        'Owner': owner_disp or 'Not Assigned',
        'Reviewer': rev_disp or 'Not Assigned',
        'Status': event.Status or 'Pending Review',
        'Priority': event.Priority or 'Medium',
        'Created Date': created,
        'Updated Date': updated,
        'Description': (event.Description or 'No description')[:10000],
    }


# Event schedule / due-date rules (aligned with audit-style due date bounds)
_EVENT_DATE_MAX_YEARS_AHEAD = 10


def _parse_event_date_value(value, field_label):
    """
    Normalize API input to a datetime.date. None or blank -> None.
    Accepts date, datetime, ISO / common locale strings.
    """
    if value is None or value == '':
        return None
    if isinstance(value, dt_datetime):
        if timezone.is_aware(value):
            return timezone.localtime(value).date()
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%m-%d-%Y'):
            try:
                return dt_datetime.strptime(v, fmt).date()
            except ValueError:
                continue
        raise ValueError(f'{field_label} must be a valid date (e.g. YYYY-MM-DD).')
    raise ValueError(f'{field_label} has an invalid type.')


def _creation_ref_date(created_at):
    """Calendar date an event was created (for comparing start/end to record creation)."""
    def _current_date_safe():
        now_dt = timezone.now()
        return timezone.localtime(now_dt).date() if timezone.is_aware(now_dt) else now_dt.date()

    if not created_at:
        return _current_date_safe()
    if timezone.is_aware(created_at):
        return timezone.localtime(created_at).date()
    if hasattr(created_at, 'date'):
        return created_at.date()
    return _current_date_safe()


def _validate_event_start_end_dates(start_d, end_d, *, mode, created_at=None, is_template=False):
    """
    Validate start/end (due) dates: realistic upper bound, ordering, and not before creation day.
    mode: 'create' uses today as creation reference; 'update' uses created_at.
    Templates skip creation-day rules but keep ordering and max-future cap.
    """
    now_dt = timezone.now()
    today = timezone.localtime(now_dt).date() if timezone.is_aware(now_dt) else now_dt.date()
    max_d = today.replace(year=today.year + _EVENT_DATE_MAX_YEARS_AHEAD)

    if is_template:
        if start_d is not None and start_d > max_d:
            return f'Start date cannot be more than {_EVENT_DATE_MAX_YEARS_AHEAD} years in the future.'
        if end_d is not None and end_d > max_d:
            return f'End date cannot be more than {_EVENT_DATE_MAX_YEARS_AHEAD} years in the future.'
        if start_d is not None and end_d is not None and end_d < start_d:
            return 'End date must be on or after start date.'
        return None

    ref = today if mode == 'create' else _creation_ref_date(created_at)

    if start_d is not None:
        if start_d > max_d:
            return f'Start date cannot be more than {_EVENT_DATE_MAX_YEARS_AHEAD} years in the future.'
        if start_d < ref:
            return f'Start date cannot be before the event creation date ({ref.isoformat()}).'
    if end_d is not None:
        if end_d > max_d:
            return f'End date (due date) cannot be more than {_EVENT_DATE_MAX_YEARS_AHEAD} years in the future.'
        if end_d < ref:
            return f'End date (due date) cannot be before the event creation date ({ref.isoformat()}).'
    if start_d is not None and end_d is not None and end_d < start_d:
        return 'End date must be on or after start date.'
    return None


# FK / record identifiers — reject negative, zero, non-integer, bool, and overflow-style values
_EVENT_MAX_ID_VALUE = 2_147_483_647
_MAX_SUBEVENT_TYPE_INDEX = 10_000
_MAX_ADDITIONAL_EVENT_RECORDS = 100


def _parse_optional_positive_int(value, field_label, *, max_value=_EVENT_MAX_ID_VALUE):
    """
    None or '' -> None. Otherwise integer >= 1 and <= max_value.
    Rejects bool (subclass of int) and non-numeric strings.
    """
    if value is None or value == '':
        return None
    if isinstance(value, bool):
        raise ValueError(f'{field_label} must be a valid positive integer.')
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_label} must be a valid positive integer.')
    if v < 1:
        raise ValueError(f'{field_label} must be a positive integer.')
    if v > max_value:
        raise ValueError(f'{field_label} is out of allowed range.')
    return v


def _parse_required_positive_int(value, field_label, *, max_value=_EVENT_MAX_ID_VALUE):
    if value is None or value == '':
        raise ValueError(f'{field_label} is required.')
    return _parse_optional_positive_int(value, field_label, max_value=max_value)


def _parse_non_negative_int(value, field_label, *, max_value=_MAX_SUBEVENT_TYPE_INDEX):
    """For sub-event type indices: 0 allowed, capped at max_value."""
    if value is None or value == '':
        return None
    if isinstance(value, bool):
        raise ValueError(f'{field_label} must be a valid integer.')
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_label} must be a valid integer.')
    if v < 0:
        raise ValueError(f'{field_label} cannot be negative.')
    if v > max_value:
        raise ValueError(f'{field_label} is out of allowed range.')
    return v


def _get_framework_for_tenant(fid, tenant_id):
    """
    Resolve Framework for event flows. Prefer strict tenant match; fall back to
    legacy rows with TenantId NULL (common in DBs migrated before multi-tenancy).
    """
    if fid is None:
        return None
    try:
        return Framework.objects.get(FrameworkId=fid, tenant_id=tenant_id)
    except Framework.DoesNotExist:
        pass
    try:
        return Framework.objects.get(FrameworkId=fid, tenant_id__isnull=True)
    except Framework.DoesNotExist:
        return None


# Simple test endpoint
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def test_endpoint(request):
    """Simple test endpoint to verify URL routing"""
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    return Response({
        'success': True,
        'message': 'Event handling endpoints are working!',
        'path': request.path
    })


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_user_event_permissions(request):
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    Get user's event permissions for frontend RBAC
    """
    try:
        user_id = RBACUtils.get_user_id_from_request(request)
        debug_print(f"DEBUG: get_user_event_permissions called for user_id: {user_id}")
        
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get user's event permissions
        permissions = RBACUtils.get_user_event_permissions(user_id)
        accessible_modules = RBACUtils.get_user_accessible_modules(user_id)
        
        debug_print(f"DEBUG: User {user_id} permissions: {permissions}")
        debug_print(f"DEBUG: User {user_id} accessible modules: {accessible_modules}")
        
        return Response({
            'success': True,
            'permissions': permissions,
            'accessible_modules': accessible_modules
        })
        
    except Exception as e:
        _log_exception(e, context='get_user_event_permissions')
        return Response({
            'success': False,
            'message': 'Error fetching user permissions. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_frameworks_for_events(request):
    """
    Get all frameworks for event creation.
    Delegates to get_approved_active_frameworks (via FrameworkTenantMapping) so both
    endpoints stay in sync — no duplicate query logic.
    Response is normalised to { success, frameworks } to preserve the existing contract.
    """
    from ..Framework.frameworks import get_approved_active_frameworks
    inner = get_approved_active_frameworks(request)

    try:
        payload = inner.data if hasattr(inner, 'data') else {}
        rows = payload.get('data', [])
        frameworks_list = [
            {'FrameworkId': f.get('FrameworkId'), 'FrameworkName': f.get('FrameworkName', '')}
            for f in rows
        ]
        return Response({
            'success': True,
            'frameworks': frameworks_list
        }, status=inner.status_code if hasattr(inner, 'status_code') else 200)
    except Exception as e:
        _log_exception(e, context='get_frameworks_for_events')
        return Response({
            'success': False,
            'message': 'Error fetching frameworks. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_modules_for_events(request):
    """
    Get all modules for event creation (simplified like event types)
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    debug_print("DEBUG: get_modules_for_events called")
    debug_print(f"DEBUG: Request path: {request.path}")
    debug_print(f"DEBUG: Request method: {request.method}")
    
    try:
        from ...models import Module
        
        # Get all modules from database (simplified approach like event types)
        all_modules = Module.objects.all().values('moduleid', 'modulename')
        modules_list = list(all_modules)
        
        debug_print(f"DEBUG: Found {len(modules_list)} modules in database")
        for module in modules_list:
            debug_print(f"DEBUG: Module: {module}")
        
        # Sort modules by name
        modules_list.sort(key=lambda x: x['modulename'])
        
        return Response({
            'success': True,
            'modules': modules_list
        })
        
    except Exception as e:
        _log_exception(e, context='get_modules_for_events')
        return Response({
            'success': False,
            'message': 'Error fetching modules. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_event_types_by_framework(request):
    """
    Get event types based on framework selection.
    Prefer framework_id (authoritative FK) and fall back to framework_name matching.
    """
    tenant_id = get_tenant_id_from_request(request)

    debug_print("DEBUG: get_event_types_by_framework called")
    try:
        framework_name = (request.GET.get('framework_name') or '').strip()
        framework_id_raw = request.GET.get('framework_id')

        framework_id = None
        if framework_id_raw not in (None, ''):
            try:
                framework_id = _parse_required_positive_int(framework_id_raw, 'Framework ID')
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)

        base_qs = EventType.objects.filter(FrameworkId__tenant_id=tenant_id)
        event_types_list = []
        search_used = None

        # 1) Preferred path: exact FK match
        if framework_id:
            event_types_list = list(
                base_qs.filter(FrameworkId=framework_id).values('eventtype_id', 'eventtype', 'eventSubtype')
            )
            search_used = f'framework_id={framework_id}'

        # 2) Fallbacks for legacy/name-only clients
        if not event_types_list and framework_name:
            event_types_list = list(
                base_qs.filter(FrameworkName=framework_name).values('eventtype_id', 'eventtype', 'eventSubtype')
            )
            search_used = f'framework_name={framework_name}'

        if not event_types_list and framework_name:
            event_types_list = list(
                base_qs.filter(FrameworkName__iexact=framework_name).values('eventtype_id', 'eventtype', 'eventSubtype')
            )
            search_used = f'framework_name__iexact={framework_name}'

        if not event_types_list and framework_name:
            event_types_list = list(
                base_qs.filter(FrameworkName__icontains=framework_name).values('eventtype_id', 'eventtype', 'eventSubtype')
            )
            search_used = f'framework_name__icontains={framework_name}'

        if not event_types_list and framework_name:
            for part in framework_name.split():
                if len(part) > 3:
                    partial = list(
                        base_qs.filter(FrameworkName__icontains=part).values('eventtype_id', 'eventtype', 'eventSubtype')
                    )
                    if partial:
                        event_types_list = partial
                        search_used = f'framework_name__icontains(part)={part}'
                        break

        all_framework_names = list(base_qs.values_list('FrameworkName', flat=True).distinct())
        return Response({
            'success': True,
            'event_types': event_types_list,
            'framework_name': framework_name,
            'framework_id': framework_id,
            'debug_info': {
                'available_frameworks': all_framework_names,
                'search_used': search_used
            }
        })
        
    except Exception as e:
        _log_exception(e, context='get_event_types_by_framework')
        return Response({
            'success': False,
            'message': 'Error fetching event types. Please try again later.'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventEditPermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def create_event_type(request):
    """
    Create a new event type for a specific framework
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    debug_print("DEBUG: create_event_type called")
    try:
        # Use DRF-parsed payload to avoid reading the request stream twice.
        data = request.data if hasattr(request, 'data') else {}
        framework_name = data.get('framework_name')
        event_type_name = data.get('event_type_name')
        event_subtypes = data.get('event_subtypes', None)  # Optional sub-event types
        
        debug_print(f"DEBUG: framework_name={framework_name}, event_type_name={event_type_name}")
        debug_print(f"DEBUG: event_subtypes={event_subtypes}")
        
        if not framework_name or not event_type_name:
            return Response({
                'success': False,
                'message': 'Framework name and event type name are required'
            }, status=400)
        
        # Check if event type already exists for this framework
        existing_event_type = EventType.objects.filter(
            FrameworkName=framework_name,
            eventtype=event_type_name
        ).first()
        
        if existing_event_type:
            return Response({
                'success': False,
                'message': f'Event type "{event_type_name}" already exists for framework "{framework_name}"'
            }, status=400)
        
        # Create new event type with sub-event types if provided
        new_event_type = EventType.objects.create(
            FrameworkName=framework_name,
            eventtype=event_type_name,
            eventSubtype=event_subtypes
        )
        
        debug_print(f"DEBUG: Created new event type with ID: {new_event_type.eventtype_id}")
        
        return Response({
            'success': True,
            'message': 'Event type created successfully',
            'event_type': {
                'eventtype_id': new_event_type.eventtype_id,
                'eventtype': new_event_type.eventtype,
                'FrameworkName': new_event_type.FrameworkName,
                'eventSubtype': new_event_type.eventSubtype
            }
        })
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        _log_exception(e, context='create_event_type')
        return Response({
            'success': False,
            'message': 'Error creating event type. Please try again later.'
        }, status=500)


@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventEditPermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def update_event_type_subtypes(request, event_type_id):
    """
    Update sub-event types for an existing event type
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    debug_print("DEBUG: update_event_type_subtypes called")
    try:
        # Use DRF-parsed payload to avoid reading the request stream twice.
        data = request.data if hasattr(request, 'data') else {}
        event_subtypes = data.get('event_subtypes')
        
        debug_print(f"DEBUG: event_type_id={event_type_id}, event_subtypes={event_subtypes}")
        
        if event_subtypes is None:
            return Response({
                'success': False,
                'message': 'event_subtypes is required'
            }, status=400)
        
        # Find the event type
        try:
            event_type = EventType.objects.get(eventtype_id=event_type_id)
        except EventType.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Event type with ID {event_type_id} not found'
            }, status=404)
        
        # Update the sub-event types
        event_type.eventSubtype = event_subtypes
        event_type.save()
        
        debug_print(f"DEBUG: Updated event type {event_type_id} with sub-event types")
        
        return Response({
            'success': True,
            'message': 'Event type sub-types updated successfully',
            'event_type': {
                'eventtype_id': event_type.eventtype_id,
                'eventtype': event_type.eventtype,
                'FrameworkName': event_type.FrameworkName,
                'eventSubtype': event_type.eventSubtype
            }
        })
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        _log_exception(e, context='update_event_type_subtypes')
        return Response({
            'success': False,
            'message': 'Error updating event type sub-types. Please try again later.'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventEditPermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def create_module(request):
    """
    Create a new module
    """
    debug_print("DEBUG: create_module called")
    try:
        # Use DRF-parsed payload to avoid reading the request stream twice.
        data = request.data if hasattr(request, 'data') else {}
        module_name = data.get('module_name')
        
        debug_print(f"DEBUG: module_name={module_name}")
        
        if not module_name:
            return Response({
                'success': False,
                'message': 'Module name is required'
            }, status=400)
        
        # Check if module already exists
        existing_module = Module.objects.filter(
            modulename=module_name
        ).first()
        
        if existing_module:
            return Response({
                'success': False,
                'message': f'Module "{module_name}" already exists'
            }, status=400)
        
        # Create new module
        new_module = Module.objects.create(
            modulename=module_name
        )
        
        debug_print(f"DEBUG: Created new module with ID: {new_module.moduleid}")
        
        return Response({
            'success': True,
            'message': 'Module created successfully',
            'module': {
                'moduleid': new_module.moduleid,
                'modulename': new_module.modulename
            }
        })
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        _log_exception(e, context='create_module')
        return Response({
            'success': False,
            'message': 'Error creating module. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_records_by_module(request):
    """
    Get records based on framework and module selection
    """
    debug_print("DEBUG: get_records_by_module called")
    try:
        tenant_id = get_tenant_id_from_request(request)
        framework_id = request.GET.get('framework_id')
        module = request.GET.get('module')
        
        debug_print(f"DEBUG: framework_id={framework_id}, module={module}")
        
        if not framework_id:
            return Response({
                'success': False,
                'message': 'Framework ID is required'
            }, status=400)
        
        try:
            framework_id = _parse_required_positive_int(framework_id, 'Framework ID')
        except ValueError as ve:
            return Response({
                'success': False,
                'message': str(ve)
            }, status=400)
        
        records = []
        
        # Handle case where module might be empty or None
        if not module or module.strip() == '':
            # If no module is selected, return empty records list
            return Response({
                'success': True,
                'records': []
            })
        
        # Normalize module name to handle full module names from frontend
        module_lower = module.lower()
        
        if 'policy' in module_lower:
            # Fetch policies for the selected framework
            debug_print(f"DEBUG: Fetching policies for framework_id={framework_id}")
            try:
                policies = Policy.objects.filter(tenant_id=tenant_id, 
                    FrameworkId=framework_id,
                    ActiveInactive='Active'
                ).values(
                    'PolicyId', 'PolicyName', 'PolicyDescription', 
                    'Status', 'Department', 'Identifier'
                )
                debug_print(f"DEBUG: Found {policies.count()} policies")
                
                # Debug: Check if there are any policies at all
                all_policies = Policy.objects.filter(tenant_id=tenant_id).count()
                debug_print(f"DEBUG: Total policies in database: {all_policies}")
                
                # Debug: Check policies for this framework regardless of status
                framework_policies = Policy.objects.filter(tenant_id=tenant_id, FrameworkId=framework_id).count()
                debug_print(f"DEBUG: Total policies for framework {framework_id}: {framework_policies}")
                
                # If no active policies found, try to get any policies for this framework
                if policies.count() == 0:
                    debug_print(f"DEBUG: No active policies found, trying to get any policies for framework {framework_id}")
                    policies = Policy.objects.filter(tenant_id=tenant_id, 
                        FrameworkId=framework_id
                    ).values(
                        'PolicyId', 'PolicyName', 'PolicyDescription', 
                        'Status', 'Department', 'Identifier'
                    )
                    debug_print(f"DEBUG: Found {policies.count()} policies (including inactive)")
                
            except Exception as e:
                _log_exception(e, context='get_records_by_module.policies')
                policies = []
            
            records = [
                {
                    'id': p['PolicyId'],
                    'name': p['PolicyName'],
                    'description': p['PolicyDescription'],
                    'status': p['Status'],
                    'department': p['Department'],
                    'identifier': p['Identifier']
                }
                for p in policies
            ]
            
        elif 'compliance' in module_lower:
            # Fetch compliance records for the selected framework
            debug_print(f"DEBUG: Fetching compliance records for framework_id={framework_id}")
            compliances = Compliance.objects.filter(tenant_id=tenant_id, 
                SubPolicy__Policy__FrameworkId=framework_id,
                ActiveInactive='Active'
            ).select_related('SubPolicy__Policy').values(
                'ComplianceId', 'ComplianceTitle', 'ComplianceItemDescription',
                'Status', 'Identifier', 'SubPolicy__Policy__PolicyName'
            )
            debug_print(f"DEBUG: Found {compliances.count()} compliance records")
            records = [
                {
                    'id': c['ComplianceId'],
                    'name': c['ComplianceTitle'] or f"Compliance {c['ComplianceId']}",
                    'description': c['ComplianceItemDescription'],
                    'status': c['Status'],
                    'identifier': c['Identifier'],
                    'policy_name': c['SubPolicy__Policy__PolicyName']
                }
                for c in compliances
            ]
            
        elif 'audit' in module_lower:
            # Fetch audits for the selected framework
            debug_print(f"DEBUG: Fetching audits for framework_id={framework_id}")
            audits = Audit.objects.filter(tenant_id=tenant_id, 
                FrameworkId=framework_id
            ).values(
                'AuditId', 'Title', 'Scope', 'Status', 'AuditType'
            )
            debug_print(f"DEBUG: Found {audits.count()} audits")
            records = [
                {
                    'id': a['AuditId'],
                    'name': a['Title'],
                    'description': a['Scope'],
                    'status': a['Status'],
                    'type': a['AuditType']
                }
                for a in audits
            ]
            
        elif 'risk' in module_lower:
            # Fetch risks (these might not be directly linked to frameworks)
            debug_print(f"DEBUG: Fetching risks for framework_id={framework_id}")
            risks = Risk.objects.filter(tenant_id=tenant_id).values(
                'RiskId', 'RiskTitle', 'RiskDescription'
            )
            debug_print(f"DEBUG: Found {risks.count()} risks")
            records = [
                {
                    'id': r['RiskId'],
                    'name': r['RiskTitle'],
                    'description': r['RiskDescription'],
                    'status': 'Active'  # Default status since Risk model doesn't have RiskStatus field
                }
                for r in risks
            ]
            
        elif 'incident' in module_lower:
            # Fetch incidents
            debug_print(f"DEBUG: Fetching incidents for framework_id={framework_id}")
            incidents = Incident.objects.filter(tenant_id=tenant_id).values(
                'IncidentId', 'IncidentTitle', 'Description', 'Status'
            )
            debug_print(f"DEBUG: Found {incidents.count()} incidents")
            records = [
                {
                    'id': i['IncidentId'],
                    'name': i['IncidentTitle'],
                    'description': i['Description'],
                    'status': i['Status']
                }
                for i in incidents
            ]
            
        elif 'subpolicy' in module_lower:
            # Fetch subpolicies for the selected framework
            debug_print(f"DEBUG: Fetching subpolicies for framework_id={framework_id}")
            subpolicies = SubPolicy.objects.filter(tenant_id=tenant_id, 
                Policy__FrameworkId=framework_id
            ).select_related('Policy').values(
                'SubPolicyId', 'SubPolicyName', 'Description', 
                'Status', 'Identifier', 'Policy__PolicyName'
            )
            debug_print(f"DEBUG: Found {subpolicies.count()} subpolicies")
            records = [
                {
                    'id': sp['SubPolicyId'],
                    'name': sp['SubPolicyName'],
                    'description': sp['Description'],
                    'status': sp['Status'],
                    'identifier': sp['Identifier'],
                    'policy_name': sp['Policy__PolicyName']
                }
                for sp in subpolicies
            ]
        else:
            debug_print(f"DEBUG: Unknown module type: {module}")
            records = []
        
        debug_print(f"DEBUG: Returning {len(records)} records for module '{module}'")
        
        # If no records found, return empty list
        if len(records) == 0:
            debug_print(f"DEBUG: No records found for module '{module}' and framework_id '{framework_id}'")
        
        return Response({
            'success': True,
            'records': records,
            'count': len(records),
            'module': module,
            'framework_id': framework_id
        })
        
    except Exception as e:
        _log_exception(e, context='get_records_by_module')
        return Response({
            'success': False,
            'message': 'Error fetching records. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_event_templates(request):
    """
    Get event templates for the template section
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    debug_print("DEBUG: get_event_templates called")
    try:
        # Check if Event table exists, if not return empty templates
        try:
            templates = Event.objects.filter(tenant_id=tenant_id, 
                IsTemplate=True,
                Status='Approved'
            ).values(
                'EventId', 'EventTitle', 'EventId_Generated', 'FrameworkName',
                'Module', 'Category', 'Owner__FirstName', 'Owner__LastName',
                'Reviewer__FirstName', 'Reviewer__LastName', 'CreatedAt'
            )
            
            formatted_templates = []
            for template in templates:
                formatted_templates.append({
                    'id': template['EventId'],
                    'title': template['EventTitle'],
                    'event_id': template['EventId_Generated'],
                    'framework': template['FrameworkName'],
                    'module': template['Module'],
                    'category': template['Category'],
                    'owner': f"{template['Owner__FirstName']} {template['Owner__LastName']}" if template['Owner__FirstName'] else 'Not Assigned',
                    'reviewer': f"{template['Reviewer__FirstName']} {template['Reviewer__LastName']}" if template['Reviewer__FirstName'] else 'Not Assigned',
                    'date': template['CreatedAt'].strftime('%d/%m') if template['CreatedAt'] else ''
                })
        except Exception as table_error:
            debug_print(f"DEBUG: Event table doesn't exist yet: {table_error}")
            # Return empty templates if table doesn't exist
            formatted_templates = []
        
        debug_print(f"DEBUG: Returning {len(formatted_templates)} templates")
        
        return Response({
            'success': True,
            'templates': formatted_templates
        })
        
    except Exception as e:
        _log_exception(e, context='get_event_templates')
        return Response({
            'success': False,
            'message': 'Error fetching templates. Please try again later.'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventCreatePermission])
@csrf_exempt
@require_consent('create_event')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def create_event(request):
    """
    Create a new event
    """
    debug_print("DEBUG: create_event called")
    debug_print(f"DEBUG: Request method: {request.method}")

    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        # Parse request data - handle both DRF request.data and raw JSON
        data = request.data if hasattr(request, 'data') else {}
        if not data and request.body:
            try:
                data = json.loads(request.body)
            except (json.JSONDecodeError, TypeError):
                data = {}
        
        debug_print(f"DEBUG: Parsed data keys: {list(data.keys()) if isinstance(data, dict) else 'n/a'}")
        
        # Authenticated creator identity — never trust client-supplied user_id.
        user_id = _parse_server_user_id_int(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Support multiple field name variations for event title:
        # 'title', 'name', 'EventTitle' (database field name)
        # Support multiple field name variations for category:
        # 'category', 'type'
        title = data.get('EventTitle') or data.get('title') or data.get('name')
        category_raw = data.get('category') or data.get('type')
        
        debug_print(f"DEBUG: Resolved title: {title}, category: {category_raw}")
        debug_print(f"DEBUG: Raw data keys: {list(data.keys())}")
        debug_print(f"DEBUG: EventTitle from data: {data.get('EventTitle')}")
        debug_print(f"DEBUG: title from data: {data.get('title')}")
        debug_print(f"DEBUG: name from data: {data.get('name')}")
        
        # Validate required fields
        if not title:
            return Response({
                'success': False,
                'message': 'Event title is required. Please provide "EventTitle", "title", or "name" field.'
            }, status=400)
        title = str(title).strip()
        if len(title) > _EVENT_MAX_TITLE_LEN:
            return Response({
                'success': False,
                'message': f'Event title must be at most {_EVENT_MAX_TITLE_LEN} characters.'
            }, status=400)
        try:
            if category_raw not in (None, ''):
                category = _sanitize_optional_str_field(
                    category_raw, _EVENT_MAX_CATEGORY_LEN, 'Category'
                )
            else:
                category = None
        except ValueError as ve:
            return Response({
                'success': False,
                'message': str(ve)
            }, status=400)
        
        # Get framework object if framework_id is provided
        framework_id = data.get('framework_id')
        framework_obj = None
        if framework_id not in (None, ''):
            try:
                fid = _parse_required_positive_int(framework_id, 'Framework ID')
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
            framework_obj = _get_framework_for_tenant(fid, tenant_id)
            if framework_obj:
                debug_print(f"DEBUG: Found framework: {framework_obj.FrameworkName}")
            else:
                debug_print(f"DEBUG: Framework with ID {fid} not found for tenant")
                return Response({
                    'success': False,
                    'message': f'Framework with ID {fid} not found'
                }, status=400)
        
        # Get owner and reviewer user objects
        owner_obj = None
        reviewer_obj = None
        
        # If owner_id is provided, use it; otherwise default to the logged-in user
        owner_id = data.get('owner_id')
        if owner_id not in (None, ''):
            try:
                oid = _parse_required_positive_int(owner_id, 'Owner ID')
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
            try:
                owner_obj = Users.objects.get(UserId=oid, tenant_id=tenant_id)
                debug_print(f"DEBUG: Found owner: {owner_obj.FirstName} {owner_obj.LastName}")
            except Users.DoesNotExist:
                debug_print(f"DEBUG: Owner with ID {oid} not found")
                return Response({
                    'success': False,
                    'message': 'Owner not found for this tenant.'
                }, status=400)
        else:
            # Default to logged-in user if no owner is specified
            try:
                owner_obj = Users.objects.get(UserId=user_id, tenant_id=tenant_id)
                debug_print(f"DEBUG: Defaulting owner to logged-in user: {owner_obj.FirstName} {owner_obj.LastName}")
            except Users.DoesNotExist:
                debug_print(f"DEBUG: Logged-in user with ID {user_id} not found")
        
        if data.get('reviewer_id') not in (None, ''):
            try:
                rid = _parse_required_positive_int(data.get('reviewer_id'), 'Reviewer ID')
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
            try:
                reviewer_obj = Users.objects.get(UserId=rid, tenant_id=tenant_id)
                debug_print(f"DEBUG: Found reviewer: {reviewer_obj.FirstName} {reviewer_obj.LastName}")
            except Users.DoesNotExist:
                debug_print(f"DEBUG: Reviewer with ID {rid} not found")
                return Response({
                    'success': False,
                    'message': 'Reviewer not found for this tenant.'
                }, status=400)
        
        # Determine initial status - always start with 'Under Review' for all events
        initial_status = 'Under Review'
        
        # Linked record ID — optional FK-style integer, must be positive when provided
        linked_record_id = data.get('linked_record_id')
        if linked_record_id in ('', None):
            linked_record_id = None
        else:
            try:
                linked_record_id = _parse_required_positive_int(linked_record_id, 'Linked record ID')
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
        
        try:
            recurrence_type = _normalize_event_recurrence_type(data.get('recurrence_type'))
        except ValueError as ve:
            return Response({
                'success': False,
                'message': str(ve)
            }, status=400)
        
        # Handle frequency field for non-recurring events
        frequency = data.get('frequency')
        if recurrence_type == 'Non-Recurring':
            frequency = None
        elif frequency not in (None, ''):
            try:
                frequency = _sanitize_optional_str_field(frequency, 50, 'Frequency')
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
        
        # Handle template selection (before date validation — templates use relaxed rules)
        is_template = data.get('is_template', False)
        if isinstance(is_template, str):
            is_template = is_template.lower() in ['true', '1', 'yes']
        is_template_flag = bool(is_template)
        is_template = 1 if is_template_flag else 0
        
        # Handle date fields: parse, validate vs creation day and realistic range
        raw_start = data.get('start_date')
        raw_end = data.get('end_date')
        if raw_start == '' or raw_start is None:
            raw_start = None
        if raw_end == '' or raw_end is None:
            raw_end = None
        
        try:
            start_date = _parse_event_date_value(raw_start, 'Start date') if raw_start is not None else None
            end_date = _parse_event_date_value(raw_end, 'End date') if raw_end is not None else None
        except ValueError as ve:
            return Response({
                'success': False,
                'message': str(ve)
            }, status=400)
        
        date_err = _validate_event_start_end_dates(
            start_date, end_date,
            mode='create',
            is_template=is_template_flag,
        )
        if date_err:
            return Response({
                'success': False,
                'message': date_err
            }, status=400)
        
        # All events should start with 'Under Review' status, including templates
        debug_print(f"DEBUG: Creating event with status 'Under Review', is_template: {is_template}")
        
        # Handle evidence files if provided
        evidence_data = data.get('evidence', [])
        evidence_urls = []
        
        debug_print(f"DEBUG: Raw evidence data from request: {evidence_data}")
        debug_print(f"DEBUG: Evidence data type: {type(evidence_data)}")
        
        # Handle evidence data - could be JSON string or array
        evidence_files = []
        if isinstance(evidence_data, str):
            try:
                # Parse JSON string
                evidence_files = json.loads(evidence_data)
                debug_print(f"DEBUG: Parsed evidence JSON: {evidence_files}")
            except json.JSONDecodeError as e:
                debug_print(f"DEBUG: Failed to parse evidence JSON: {e}")
                evidence_files = []
        elif isinstance(evidence_data, list):
            # Already an array
            evidence_files = evidence_data
        
        # Process evidence files — validate each URL against TRUSTED_EVIDENCE_* allow-list
        if evidence_files:
            debug_print(f"DEBUG: Processing {len(evidence_files)} evidence files")
            for i, evidence_file in enumerate(evidence_files):
                if not isinstance(evidence_file, dict):
                    return Response({
                        'success': False,
                        'message': 'Each evidence entry must be an object.',
                    }, status=400)
                raw_url = evidence_file.get('s3_url')
                if not raw_url:
                    continue
                try:
                    safe_url = _validate_event_evidence_s3_url(
                        raw_url, field_label=f'evidence[{i}].s3_url'
                    )
                    if safe_url:
                        evidence_urls.append(safe_url)
                except ValueError as ve:
                    return Response({
                        'success': False,
                        'message': _sanitize_reflected_error_detail(str(ve)),
                    }, status=400)
        else:
            debug_print("DEBUG: No evidence files provided")
        
        # Create semicolon-separated string of URLs
        evidence_string = ";".join(evidence_urls) if evidence_urls else ""
        debug_print(f"DEBUG: Final evidence string to save: '{evidence_string}'")
        debug_print(f"DEBUG: Evidence string length: {len(evidence_string)}")
        
        # Get event type object if event_type_id is provided
        event_type_obj = None
        event_type_id = data.get('event_type_id')
        if event_type_id not in (None, ''):
            try:
                etid = _parse_required_positive_int(event_type_id, 'Event type ID')
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
            try:
                event_type_obj = EventType.objects.get(eventtype_id=etid)
                debug_print(f"DEBUG: Found event type: {event_type_obj.eventtype}")
            except EventType.DoesNotExist:
                debug_print(f"DEBUG: Event type with ID {etid} not found")
                return Response({
                    'success': False,
                    'message': f'Event type with ID {etid} not found'
                }, status=400)

        # Sub-event type index (0-based); requires valid event_type and in-range index
        sub_event_type_name = None
        sub_event_type_raw = data.get('sub_event_type_id')
        if sub_event_type_raw is not None and sub_event_type_raw != '':
            try:
                sub_idx = _parse_non_negative_int(sub_event_type_raw, 'Sub-event type index')
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
            if not event_type_obj:
                return Response({
                    'success': False,
                    'message': 'sub_event_type_id requires a valid event_type_id.'
                }, status=400)
            if not event_type_obj.eventSubtype:
                return Response({
                    'success': False,
                    'message': 'The selected event type has no sub-types configured.'
                }, status=400)
            resolved = False
            if isinstance(event_type_obj.eventSubtype, list):
                if sub_idx < len(event_type_obj.eventSubtype):
                    sub_event_type_name = event_type_obj.eventSubtype[sub_idx]
                    debug_print(f"DEBUG: Selected sub-event type (array): {sub_event_type_name}")
                    resolved = True
            elif isinstance(event_type_obj.eventSubtype, dict):
                sub_type_keys = list(event_type_obj.eventSubtype.keys())
                if sub_idx < len(sub_type_keys):
                    selected_key = sub_type_keys[sub_idx]
                    display_name_map = {
                        'risk_register_updates': 'Risk Register Updates',
                        'formal_risk_assessments': 'Formal Risk Assessments',
                        'documented_risk_treatment_plans': 'Documented Risk Treatment Plans',
                        'approval_records_of_risk_acceptance_or_residual_risk': 'Approval Records Of Risk Acceptance Or Residual Risk',
                        'isms_policy_review': 'ISMS Policy Review',
                        'management_review': 'Management Review Meeting',
                        'resource_allocation': 'Resource Allocation Review',
                        'performance_monitoring': 'Performance Monitoring',
                        'continuous_improvement': 'Continuous Improvement Initiative'
                    }
                    sub_event_type_name = display_name_map.get(selected_key, selected_key.replace('_', ' ').title())
                    debug_print(f"DEBUG: Selected sub-event type (object): {sub_event_type_name} (key: {selected_key})")
                    resolved = True
            if not resolved:
                return Response({
                    'success': False,
                    'message': 'Sub-event type index is out of range for the selected event type.'
                }, status=400)

        # Handle data_inventory - optional JSON field mapping field labels to data types
        data_inventory = None
        if 'data_inventory' in data and data.get('data_inventory'):
            data_inventory_raw = data.get('data_inventory')
            if data_inventory_raw is None or data_inventory_raw == '':
                data_inventory = None
            elif isinstance(data_inventory_raw, str):
                try:
                    data_inventory = json.loads(data_inventory_raw)
                except json.JSONDecodeError:
                    debug_print(f"Warning: Invalid JSON in data_inventory, setting to None: {data_inventory_raw}")
                    data_inventory = None
            elif isinstance(data_inventory_raw, dict):
                # Clean the data_inventory to ensure all values are valid
                cleaned_inventory = {}
                valid_types = ['personal', 'confidential', 'regular']
                for key, value in data_inventory_raw.items():
                    if value in valid_types:
                        cleaned_inventory[key] = value
                data_inventory = cleaned_inventory if cleaned_inventory else None
            else:
                debug_print(f"Warning: Invalid type for data_inventory, setting to None: {type(data_inventory_raw)}")
                data_inventory = None
        
        created_by_user = Users.objects.filter(UserId=user_id, tenant_id=tenant_id).first()
        if not created_by_user:
            return Response({
                'success': False,
                'message': 'Authenticated user profile was not found for this tenant.'
            }, status=401)

        try:
            priority_val = _normalize_event_priority(data.get('priority'))
            module_val = _sanitize_optional_str_field(
                data.get('module'), _EVENT_MAX_MODULE_LEN, 'Module'
            )
            framework_name_val = _sanitize_optional_str_field(
                data.get('framework_name'), _EVENT_MAX_FRAMEWORK_NAME_LEN, 'Framework name'
            )
            linked_rt_val = _normalize_linked_record_type(data.get('linked_record_type'))
            linked_rn_val = _sanitize_optional_str_field(
                data.get('linked_record_name'), _EVENT_MAX_LINKED_RECORD_NAME_LEN, 'Linked record name'
            )
        except ValueError as ve:
            return Response({
                'success': False,
                'message': str(ve)
            }, status=400)
        
        # Extract data from request - match Django Event model field names exactly
        event_data = {
            'EventTitle': title,  # Use the resolved title (from 'title' or 'name')
            'Description': data.get('description'),
            'FrameworkId': framework_obj,
            'FrameworkName': framework_name_val,
            'Module': module_val,
            'LinkedRecordType': linked_rt_val,
            'LinkedRecordId': linked_record_id,
            'LinkedRecordName': linked_rn_val,
            'Category': category,  # Use the resolved category (from 'category' or 'type')
            'EventType': event_type_obj,  # Save event type object in EventType field
            'SubEventType': sub_event_type_name,  # Save selected sub-event type name
            'RecurrenceType': recurrence_type,
            'Frequency': frequency,
            'StartDate': start_date,
            'EndDate': end_date,
            # Workflow status is server-controlled at creation (not client-supplied).
            'Status': initial_status,
            'Priority': priority_val,
            'CreatedBy': created_by_user,
            'Owner': owner_obj,
            'Reviewer': reviewer_obj,
            'IsTemplate': is_template,
            'Evidence': evidence_string,  # Store evidence URLs as semicolon-separated string
            'DynamicFieldsData': data.get('dynamic_fields', {}),  # Store user-entered dynamic fields data
            'data_inventory': data_inventory  # Store data inventory mapping
        }
        
        debug_print(f"DEBUG: Event data to create: {event_data}")
        debug_print(f"DEBUG: Evidence field in event_data: {event_data.get('Evidence')}")
        debug_print(f"DEBUG: Evidence field type: {type(event_data.get('Evidence'))}")
        
        # Runtime compatibility: ensure recently-added Event columns exist.
        _ensure_event_runtime_columns()
        
        # Check if events table exists
        try:
            # Create the primary event
            debug_print("DEBUG: Attempting to create event...")
            event = Event.objects.create(**event_data)
            debug_print(f"DEBUG: Primary event created successfully with ID: {event.EventId}")
            debug_print(f"DEBUG: Event Evidence after creation: {event.Evidence}")
            debug_print(f"DEBUG: Event Evidence type after creation: {type(event.Evidence)}")
            
            created_events = [{
                'EventId': event.EventId,
                'EventTitle': event.EventTitle,
                'Status': event.Status,
                'RecurrenceType': event.RecurrenceType,
                'StartDate': event.StartDate,
                'EndDate': event.EndDate,
                'LinkedRecordName': event.LinkedRecordName,
                'FrameworkName': event.FrameworkName,
                'Module': event.Module
            }]
            
            # Handle additional records if any
            additional_records = data.get('additional_records', [])
            if additional_records:
                if not isinstance(additional_records, list):
                    return Response({
                        'success': False,
                        'message': 'additional_records must be a list.'
                    }, status=400)
                if len(additional_records) > _MAX_ADDITIONAL_EVENT_RECORDS:
                    return Response({
                        'success': False,
                        'message': f'Cannot create more than {_MAX_ADDITIONAL_EVENT_RECORDS} additional records at once.'
                    }, status=400)
                debug_print(f"DEBUG: Creating {len(additional_records)} additional events")
                
                for i, additional_record in enumerate(additional_records):
                    if not isinstance(additional_record, dict):
                        return Response({
                            'success': False,
                            'message': 'Each additional record must be an object.'
                        }, status=400)
                    # Get framework object for additional record
                    additional_framework_obj = None
                    if additional_record.get('framework_id') not in (None, ''):
                        try:
                            afid = _parse_required_positive_int(
                                additional_record['framework_id'], 'Additional record framework ID'
                            )
                        except ValueError as ve:
                            return Response({
                                'success': False,
                                'message': str(ve)
                            }, status=400)
                        additional_framework_obj = _get_framework_for_tenant(afid, tenant_id)
                        if additional_framework_obj:
                            debug_print(f"DEBUG: Found additional framework: {additional_framework_obj.FrameworkName}")
                        else:
                            debug_print(f"DEBUG: Additional framework with ID {afid} not found")
                            return Response({
                                'success': False,
                                'message': f'Additional record framework with ID {afid} not found'
                            }, status=400)
                    
                    add_lrid = additional_record.get('linked_record_id')
                    if add_lrid in (None, ''):
                        add_lrid_parsed = None
                    else:
                        try:
                            add_lrid_parsed = _parse_required_positive_int(add_lrid, 'Linked record ID')
                        except ValueError as ve:
                            return Response({
                                'success': False,
                                'message': str(ve)
                            }, status=400)
                    
                    # Create event data for additional record
                    additional_record_name = additional_record.get('linked_record_name', f'Additional Record {i+1}')
                    try:
                        add_fw_name = _sanitize_optional_str_field(
                            additional_record.get('framework_name'),
                            _EVENT_MAX_FRAMEWORK_NAME_LEN,
                            'Additional record framework name',
                        )
                        add_mod = _sanitize_optional_str_field(
                            additional_record.get('module'),
                            _EVENT_MAX_MODULE_LEN,
                            'Additional record module',
                        )
                        add_lrt = _normalize_linked_record_type(
                            additional_record.get('linked_record_type')
                        )
                        add_lrn = _sanitize_optional_str_field(
                            additional_record.get('linked_record_name'),
                            _EVENT_MAX_LINKED_RECORD_NAME_LEN,
                            'Additional record linked record name',
                        )
                    except ValueError as ve:
                        return Response({
                            'success': False,
                            'message': str(ve)
                        }, status=400)
                    additional_event_data = {
                        'EventTitle': f"{title} - {additional_record_name}",
                        'Description': f"Additional record for event: {title} - {additional_record_name}",
                        'FrameworkId': additional_framework_obj,
                        'FrameworkName': add_fw_name,
                        'Module': add_mod,
                        'LinkedRecordType': add_lrt,
                        'LinkedRecordId': add_lrid_parsed,
                        'LinkedRecordName': add_lrn,
                        'Category': category,  # Use resolved category (from 'category' or 'type')
                        'EventType': event_type_obj,  # Save event type object in EventType field
                        'SubEventType': sub_event_type_name,  # Save selected sub-event type name
                        'RecurrenceType': recurrence_type,
                        'Frequency': frequency,
                        'StartDate': start_date,
                        'EndDate': end_date,
                        'Status': initial_status,
                        'Priority': priority_val,
                        'CreatedBy': created_by_user,
                        'Owner': owner_obj,
                        'Reviewer': reviewer_obj,
                        'IsTemplate': is_template,
                        'Evidence': evidence_string,  # Include evidence for additional records too
                        'data_inventory': data_inventory  # Include data inventory for additional records too
                    }
                    
                    # Create the additional event
                    additional_event = Event.objects.create(**additional_event_data)
                    debug_print(f"DEBUG: Additional event {i+1} created successfully with ID: {additional_event.EventId}")
                    
                    created_events.append({
                        'EventId': additional_event.EventId,
                        'EventTitle': additional_event.EventTitle,
                        'Status': additional_event.Status,
                        'RecurrenceType': additional_event.RecurrenceType,
                        'StartDate': additional_event.StartDate,
                        'EndDate': additional_event.EndDate,
                        'LinkedRecordName': additional_event.LinkedRecordName,
                        'FrameworkName': additional_event.FrameworkName,
                        'Module': additional_event.Module
                    })
            
            total_events = len(created_events)
            message = f'Event created successfully' if total_events == 1 else f'{total_events} events created successfully (1 primary + {total_events-1} additional records)'


             # Trigger automatic AI Risk Identification (Background) - using primary event
            try:
                from ...models import SystemIdentifiedRiskQueue
                trigger_single_source_risk_scan(
                    source_type=SystemIdentifiedRiskQueue.SOURCE_EVENT, 
                    source_id=event.EventId, 
                    tenant_id=tenant_id
                )
            except Exception as e:
                debug_print(f"Error triggering automatic risk scan: {str(e)}")
            
            
            # Send email notifications for event creation
            try:
                from ...routes.Global.notification_service import NotificationService
                from ...routes.Global.notifications import (
                    send_event_aware_multi_channel,
                    append_event_notification_in_app,
                )
                notification_service = NotificationService()
                import uuid
                from datetime import datetime as dt
                
                # Helper function to send event notifications
                def send_event_notifications(event_obj, is_assigned=False):
                    """Send email and in-app notifications for an event"""
                    recipients = []
                    
                    # Collect recipients (Owner, Reviewer, Creator)
                    if event_obj.Owner and hasattr(event_obj.Owner, 'Email') and event_obj.Owner.Email:
                        recipients.append({
                            'role': 'owner',
                            'email': event_obj.Owner.Email,
                            'name': event_obj.Owner.UserName or event_obj.Owner.Email.split('@')[0],
                            'user_id': event_obj.Owner.UserId
                        })
                    if event_obj.Reviewer and hasattr(event_obj.Reviewer, 'Email') and event_obj.Reviewer.Email:
                        recipients.append({
                            'role': 'reviewer',
                            'email': event_obj.Reviewer.Email,
                            'name': event_obj.Reviewer.UserName or event_obj.Reviewer.Email.split('@')[0],
                            'user_id': event_obj.Reviewer.UserId
                        })
                    if event_obj.CreatedBy and hasattr(event_obj.CreatedBy, 'Email') and event_obj.CreatedBy.Email:
                        recipients.append({
                            'role': 'creator',
                            'email': event_obj.CreatedBy.Email,
                            'name': event_obj.CreatedBy.UserName or event_obj.CreatedBy.Email.split('@')[0],
                            'user_id': event_obj.CreatedBy.UserId
                        })
                    
                    # Send email notifications
                    for recipient in recipients:
                        try:
                            if is_assigned and recipient['role'] in ['owner', 'reviewer']:
                                # Use eventAssigned template for assigned users
                                notification_type = 'eventAssigned'
                                due_date_str = event_obj.EndDate.strftime('%Y-%m-%d') if event_obj.EndDate else 'Not specified'
                                template_data = [
                                    recipient['name'],
                                    event_obj.EventTitle,
                                    event_obj.Description or 'No description provided',
                                    event_obj.CreatedBy.UserName if event_obj.CreatedBy else 'System',
                                    event_obj.Category or 'General',
                                    due_date_str
                                ]
                            else:
                                # Use eventCreated template
                                notification_type = 'eventCreated'
                                template_data = [
                                    recipient['name'],
                                    event_obj.EventTitle,
                                    event_obj.Description or 'No description provided',
                                    event_obj.CreatedBy.UserName if event_obj.CreatedBy else 'System',
                                    event_obj.Category or 'General'
                                ]
                            
                            notification_data = {
                                'notification_type': notification_type,
                                'email': recipient['email'],
                                'email_type': 'gmail',
                                'template_data': template_data
                            }
                            send_event_aware_multi_channel(
                                notification_service,
                                notification_data,
                                event_obj.EventId,
                                recipient_user_id=recipient['user_id'],
                                dedup_extra='',
                            )
                            
                            # Create in-app notification
                            notification = {
                                'id': str(uuid.uuid4()),
                                'title': 'Event Assigned' if is_assigned and recipient['role'] in ['owner', 'reviewer'] else 'New Event Created',
                                'message': f'Event "{event_obj.EventTitle}" has been {"assigned to you" if is_assigned and recipient["role"] in ["owner", "reviewer"] else "created"}.',
                                'category': 'event',
                                'priority': event_obj.Priority.lower() if event_obj.Priority else 'medium',
                                'createdAt': dt.now().isoformat(),
                                'status': {'isRead': False, 'readAt': None},
                                'user_id': str(recipient['user_id'])
                            }
                            append_event_notification_in_app(
                                notification, event_obj.EventId, notification_type, dedup_extra=''
                            )
                                
                        except Exception as notify_error:
                            _log_exception(notify_error, context='create_event.notify_recipient')
                
                # Send notifications for primary event
                send_event_notifications(event, is_assigned=(event.Owner is not None or event.Reviewer is not None))
                
                # Send notifications for additional events if any
                for additional_event_dict in created_events[1:]:
                    try:
                        additional_event = Event.objects.get(EventId=additional_event_dict['EventId'], tenant_id=tenant_id)
                        send_event_notifications(additional_event, is_assigned=(additional_event.Owner is not None or additional_event.Reviewer is not None))
                    except Event.DoesNotExist:
                        pass
                        
            except Exception as notify_ex:
                _log_exception(notify_ex, context='create_event.notify_batch')
                # Don't fail event creation if notifications fail
            
            return Response({
                'success': True,
                'message': message,
                'event_id': event.EventId,
                'event_id_generated': event.EventId_Generated,
                'total_events_created': total_events,
                'events': created_events
            })
        except Exception as db_error:
            debug_print(f"DEBUG: Database error: {sanitize_for_log(db_error, max_len=800)}")
            if "Unknown column" in str(db_error):
                return Response({
                    'success': False,
                    'message': 'Events table schema mismatch. Please contact your administrator.',
                }, status=500)
            else:
                raise db_error
        
    except Exception as e:
        _log_exception(e, context='create_event')
        return Response({
            'success': False,
            'message': 'Error creating event. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_events(request):
    """
    Get all events with optional filtering
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        # Get filter parameters
        event_type = request.GET.get('type', '')
        module = request.GET.get('module', '')
        status = request.GET.get('status', '')
        
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Start with base query — tenant isolation + object-level list scope
        events_query = Event.objects.select_related(
            'Owner', 'Reviewer', 'CreatedBy', 'FrameworkId', 'EventType'
        ).filter(tenant_id=tenant_id, IsTemplate=False)
        events_query = _apply_event_list_scope(events_query, user_id_int)
        
        # Apply filters
        if event_type:
            events_query = events_query.filter(EventType__eventtype__icontains=event_type)
        if module:
            events_query = events_query.filter(Module__icontains=module)
        if status:
            events_query = events_query.filter(Status__icontains=status)
        
        # Apply framework filtering
        from ..Policy.framework_filter_helper import apply_framework_filter, get_framework_filter_info
        filter_info = get_framework_filter_info(request)
        debug_print(f"🔍 DEBUG: Framework filter info for get_events: {filter_info}")
        events_query = apply_framework_filter(events_query, request, 'FrameworkId')
        
        events = events_query.values(
            'EventId', 'EventTitle', 'EventId_Generated', 'FrameworkName',
            'Module', 'Category', 'Status', 'Priority', 'CreatedAt',
            'Description', 'LinkedRecordName', 'LinkedRecordType', 'RecurrenceType', 'Frequency',
            'EventType__eventtype_id', 'EventType__eventtype', 'EventType__FrameworkName',
            'Owner__FirstName', 'Owner__LastName', 'Owner__UserId', 'Reviewer__FirstName', 
            'Reviewer__LastName', 'Reviewer__UserId', 'CreatedBy__FirstName', 'CreatedBy__LastName',
            'Evidence', 'DynamicFieldsData'
        )
        
        formatted_events = []
        for event in events:
            # Process evidence data
            evidence_string = event['Evidence'] if event['Evidence'] else ''
            evidence_count = len([url for url in evidence_string.split(';') if url.strip()]) if evidence_string else 0
            
            formatted_events.append({
                'id': event['EventId'],
                'title': event['EventTitle'],
                'event_id': event['EventId_Generated'],
                'framework': event['FrameworkName'],
                'module': event['Module'],
                'category': event['Category'],
                'event_type_id': event['EventType__eventtype_id'],
                'event_type': event['EventType__eventtype'],
                'event_type_framework': event['EventType__FrameworkName'],
                'status': event['Status'],
                'evidence_count': evidence_count,
                'priority': event['Priority'],
                'description': event['Description'],
                'linked_record_name': event['LinkedRecordName'],
                'linked_record_type': event['LinkedRecordType'],
                'recurrence_type': event['RecurrenceType'],
                'frequency': event['Frequency'],
                'owner': f"{event['Owner__FirstName']} {event['Owner__LastName']}" if event['Owner__FirstName'] else 'Not Assigned',
                'owner_id': event['Owner__UserId'],
                'reviewer': f"{event['Reviewer__FirstName']} {event['Reviewer__LastName']}" if event['Reviewer__FirstName'] else 'Not Assigned',
                'reviewer_id': event['Reviewer__UserId'],
                'created_by': f"{event['CreatedBy__FirstName']} {event['CreatedBy__LastName']}" if event['CreatedBy__FirstName'] else 'Unknown',
                'created_at': _format_datetime_ist(event['CreatedAt']) if event['CreatedAt'] else '',
                'dynamic_fields_data': event['DynamicFieldsData']
            })
        
        return Response({
            'success': True,
            'events': formatted_events
        })
        
    except Exception as e:
        _log_exception(e, context='get_events')
        return Response({
            'success': False,
            'message': 'Error fetching events. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_document_handling_events(request):
    """
    Get document handling events from file_operations table
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        debug_print("DEBUG: get_document_handling_events called")
        # Get user ID for RBAC filtering
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        debug_print(f"DEBUG: User ID: {user_id}")
        
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get query parameters
        try:
            limit = int(request.GET.get('limit', 50))
        except (TypeError, ValueError):
            limit = 50
        limit = max(1, min(limit, 500))
        operation_type = request.GET.get('operation_type', '')
        status = request.GET.get('status', '')
        
        # Tenant-scoped file operations (framework belongs to tenant)
        file_operations_query = FileOperations.objects.filter(FrameworkId__tenant_id=tenant_id)
        perms = RBACUtils.get_user_event_permissions(user_id_int)
        modlist = RBACUtils.get_user_accessible_modules(user_id_int)
        if not (perms.get('is_admin') or perms.get('view_all_event')):
            if perms.get('view_module_event') and modlist:
                file_operations_query = file_operations_query.filter(module__in=modlist)
            else:
                file_operations_query = file_operations_query.none()
        
        # Apply filters
        if operation_type:
            file_operations_query = file_operations_query.filter(operation_type=operation_type)
        if status:
            file_operations_query = file_operations_query.filter(status=status)
        
        # Apply limit
        file_operations_query = file_operations_query[:limit]
        
        debug_print(f"DEBUG: Found {file_operations_query.count()} file operations")
        
        formatted_events = []
        for file_op in file_operations_query:
            # Create event-like structure from file operations
            formatted_events.append({
                'id': f"file_op_{file_op.id}",
                'title': f"{file_op.operation_type.title()}: {file_op.display_name}",
                'event_id': f"FILE-{file_op.id}",
                'framework': 'Document Handling System',
                'module': file_op.module or 'Document Handling',
                'category': 'File Operation',
                'event_type_id': None,
                'event_type': file_op.operation_type.title(),
                'event_type_framework': 'Document Handling System',
                'status': file_op.status.title(),
                'evidence_count': 1 if file_op.s3_url else 0,
                'priority': 'Medium',
                'description': f"File {file_op.operation_type} operation: {file_op.display_name}",
                'linked_record_name': file_op.display_name,
                'linked_record_type': 'File Operation',
                'linked_record_id': file_op.id,
                'recurrence_type': 'Non-Recurring',
                'frequency': None,
                'owner': f"User {file_op.user_id}",
                'owner_id': file_op.user_id,
                'reviewer': 'System',
                'reviewer_id': None,
                'created_by': f"User {file_op.user_id}",
                'created_at': _format_datetime_ist(file_op.created_at) if file_op.created_at else '',
                'dynamic_fields_data': {
                    'file_name': file_op.file_name,
                    'original_name': file_op.original_name,
                    'stored_name': file_op.stored_name,
                    'file_type': file_op.file_type,
                    'file_size': file_op.file_size,
                    'content_type': file_op.content_type,
                    's3_url': file_op.s3_url,
                    's3_key': file_op.s3_key,
                    's3_bucket': file_op.s3_bucket,
                    'export_format': file_op.export_format,
                    'record_count': file_op.record_count,
                    'platform': file_op.platform,
                    'error': file_op.error,
                    'metadata': file_op.metadata
                },
                'evidence': [file_op.s3_url] if file_op.s3_url else [],
                'is_file_operation': True
            })
        
        return Response({
            'success': True,
            'events': formatted_events
        })
        
    except Exception as e:
        _log_exception(e, context='get_document_handling_events')
        return Response({
            'success': False,
            'message': 'Error fetching document handling events. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_events_list(request):
    """
    Get list of all events (including templates and RiskaVaire events)
    Shows comprehensive view of all events in the system
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        import random
        
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get available frameworks and modules from database
        available_frameworks = []
        available_modules = []
        
        try:
            from ...models import Framework, Module
            
            # Fetch all active frameworks
            frameworks = Framework.objects.filter(tenant_id=tenant_id, ActiveInactive='Active').values_list('FrameworkName', flat=True)
            available_frameworks = list(frameworks)
            
            # Fetch all modules (Module model doesn't have is_active field)
            modules = Module.objects.all().values_list('modulename', flat=True)
            available_modules = list(modules)
            
            debug_print(f"DEBUG: Fetched {len(available_frameworks)} frameworks from database: {list(available_frameworks)}")
            debug_print(f"DEBUG: Fetched {len(available_modules)} modules from database: {list(available_modules)}")
        except Exception as module_error:
            _log_exception(module_error, context='get_events_list.frameworks_modules')
        
        # Fallback lists if database is empty
        if not available_frameworks:
            available_frameworks = [
                'Basel III Framework',
                'NIST',
                'ISO 27001',
                'COBIT',
                'PCI DSS',
                'HIPAA',
                'SOX',
                'GDPR'
            ]
        
        if not available_modules:
            available_modules = [
                'Audit Management',
                'Compliance Management',
                'Incident Management',
                'Policy Management',
                'Risk Management'
            ]
        
        debug_print(f"Available Frameworks: {available_frameworks}")
        debug_print(f"Available Modules: {available_modules}")
        debug_print(f"DEBUG: Framework count: {len(available_frameworks)}")
        debug_print(f"DEBUG: Module count: {len(available_modules)}")
        
        # Check if events table exists and has data
        try:
            total_events = Event.objects.filter(tenant_id=tenant_id).count()
            debug_print(f"DEBUG: Total events in database: {total_events}")
            
            # If no events exist, create some sample events for testing
            if total_events == 0:
                debug_print("DEBUG: No events found, creating sample events...")
                from django.utils import timezone
                from datetime import datetime, timedelta
                
                # Get the current user for sample events
                try:
                    current_user = Users.objects.get(UserId=user_id_int, tenant_id=tenant_id)
                    debug_print(f"DEBUG: Using current user {user_id_int} for sample events")
                except Users.DoesNotExist:
                    debug_print(f"DEBUG: Current user {user_id_int} not found, using first available user")
                    current_user = Users.objects.first()
                    if not current_user:
                        debug_print("DEBUG: No users found in database")
                        return Response({
                            'success': True,
                            'events': [],
                            'message': 'No users found in database'
                        })
                except Exception as e:
                    debug_print(f"DEBUG: Error getting user: {e}")
                    return Response({
                        'success': True,
                        'events': [],
                        'message': 'Error accessing user data'
                    })
                
                # Create sample events
                sample_events = [
                    {
                        'EventTitle': 'Security Policy Review',
                        'EventId_Generated': 'EVT-2025-0001',
                        'Description': 'Quarterly review of security policies',
                        'FrameworkName': 'ISO 27001',
                        'Module': 'Policy Management',
                        'Category': 'Compliance',
                        'Status': 'Pending Review',
                        'Priority': 'High',
                        'CreatedBy': current_user,
                        'Owner': current_user,
                        'Reviewer': current_user,
                        'CreatedAt': timezone.now() - timedelta(days=2),
                        'IsTemplate': False,
                        'tenant_id': tenant_id,
                    },
                    {
                        'EventTitle': 'Risk Assessment Update',
                        'EventId_Generated': 'EVT-2025-0002',
                        'Description': 'Update risk assessment for Q4',
                        'FrameworkName': 'Basel III Framework',
                        'Module': 'Risk Management',
                        'Category': 'Risk',
                        'Status': 'Under Review',
                        'Priority': 'Medium',
                        'CreatedBy': current_user,
                        'Owner': current_user,
                        'Reviewer': current_user,
                        'CreatedAt': timezone.now() - timedelta(days=1),
                        'IsTemplate': False,
                        'tenant_id': tenant_id,
                    },
                    {
                        'EventTitle': 'Audit Finding Resolution',
                        'EventId_Generated': 'EVT-2025-0003',
                        'Description': 'Resolve audit findings from last quarter',
                        'FrameworkName': 'SOX Compliance',
                        'Module': 'Audit Management',
                        'Category': 'Audit',
                        'Status': 'Approved',
                        'Priority': 'Critical',
                        'CreatedBy': current_user,
                        'Owner': current_user,
                        'Reviewer': current_user,
                        'CreatedAt': timezone.now() - timedelta(hours=6),
                        'IsTemplate': False,
                        'tenant_id': tenant_id,
                    }
                ]
                
                for event_data in sample_events:
                    try:
                        Event.objects.create(**event_data)
                        debug_print(f"DEBUG: Created sample event: {event_data['EventTitle']}")
                    except Exception as e:
                        debug_print(f"DEBUG: Error creating sample event {event_data['EventTitle']}: {e}")
                
                debug_print(f"DEBUG: Created {len(sample_events)} sample events")
                
        except Exception as e:
            debug_print(f"DEBUG: Error checking/creating events: {e}")
            return Response({
                'success': False,
                'message': 'Error accessing events table. Please try again later.'
            }, status=500)
        
        # Start with base query (tenant isolation + RBAC list scope)
        events_query = Event.objects.select_related(
            'Owner', 'Reviewer', 'CreatedBy', 'FrameworkId', 'EventType'
        ).filter(tenant_id=tenant_id)
        events_query = _apply_event_list_scope(events_query, user_id_int)
        
        # Apply framework filtering from session (similar to Policy module)
        try:
            from ..Policy.framework_filter_helper import apply_framework_filter, get_framework_filter_info
            
            # Get framework filter info for logging
            filter_info = get_framework_filter_info(request)
            debug_print(f"DEBUG: Events list - Framework filter info: {filter_info}")
            
            # Apply framework filter to events
            events_query = apply_framework_filter(events_query, request, 'FrameworkId')
            
        except ImportError as e:
            debug_print(f"DEBUG: Could not import framework filter helper: {e}")
            # Continue without framework filtering if helper is not available
        except Exception as e:
            debug_print(f"DEBUG: Error applying framework filter: {e}")
            # Continue without framework filtering on error
        
        events = events_query.values(
            'EventId', 'EventTitle', 'EventId_Generated', 'FrameworkName',
            'Module', 'Category', 'Status', 'Priority', 'CreatedAt',
            'Description', 'LinkedRecordName', 'LinkedRecordType', 'RecurrenceType', 'Frequency',
            'IsTemplate', 'EventType__eventtype_id', 'EventType__eventtype', 'EventType__FrameworkName',
            'Owner__FirstName', 'Owner__LastName', 'Owner__UserId', 'Reviewer__FirstName', 
            'Reviewer__LastName', 'Reviewer__UserId', 'CreatedBy__FirstName', 'CreatedBy__LastName',
            'Evidence'  # Include Evidence field
        )
        
        formatted_events = []
        for event in events:
            # Process evidence data for list view
            evidence_string = event.get('Evidence', '') or ""
            evidence_count = len([url for url in evidence_string.split(';') if url.strip()]) if evidence_string else 0
            
            # Assign random framework if missing
            framework = event['FrameworkName']
            if not framework or framework == 'N/A' or framework is None or framework == '':
                framework = random.choice(available_frameworks)
            
            # Assign random module if missing
            module = event['Module']
            if not module or module == 'N/A' or module is None or module == '':
                module = random.choice(available_modules)
            
            formatted_events.append({
                'id': event['EventId'],
                'title': event['EventTitle'],
                'event_id': event['EventId_Generated'],
                'framework': framework,
                'module': module,
                'category': event['Category'],
                'event_type_id': event['EventType__eventtype_id'],
                'event_type': event['EventType__eventtype'],
                'event_type_framework': event['EventType__FrameworkName'],
                'status': event['Status'],
                'evidence_count': evidence_count,  # Add evidence count
                'priority': event['Priority'],
                'description': event['Description'],
                'linked_record_name': event['LinkedRecordName'],
                'linked_record_type': event['LinkedRecordType'],
                'recurrence_type': event['RecurrenceType'],
                'frequency': event['Frequency'],
                'is_template': event['IsTemplate'],
                'owner': f"{event['Owner__FirstName']} {event['Owner__LastName']}" if event['Owner__FirstName'] else 'Not Assigned',
                'owner_id': event['Owner__UserId'],
                'reviewer': f"{event['Reviewer__FirstName']} {event['Reviewer__LastName']}" if event['Reviewer__FirstName'] else 'Not Assigned',
                'reviewer_id': event['Reviewer__UserId'],
                'created_by': f"{event['CreatedBy__FirstName']} {event['CreatedBy__LastName']}" if event['CreatedBy__FirstName'] else 'Unknown',
                'created_at': _format_datetime_ist(event['CreatedAt']) if event['CreatedAt'] else ''
            })
        
        return Response({
            'success': True,
            'events': formatted_events
        })
        
    except Exception as e:
        _log_exception(e, context='get_events_list')
        return Response({
            'success': False,
            'message': 'Error fetching events. Please try again later.'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventExportPermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def export_events_to_s3(request):
    """
    Export events data to S3 and return file URL.
    """
    try:
        export_format = str(request.data.get('export_format', 'csv')).lower()
        events_data = request.data.get('events', [])
        user_id = _get_server_user_id(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        raw_file_name = request.data.get('file_name') or f"events_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        file_name = sanitize_export_filename(raw_file_name, default='events_export')

        format_map = {
            'excel': 'xlsx',
            'xlsx': 'xlsx',
            'csv': 'csv',
            'pdf': 'pdf',
            'json': 'json',
            'xml': 'xml',
            'txt': 'txt'
        }
        normalized_format = format_map.get(export_format)
        if not normalized_format:
            return Response({
                'success': False,
                'message': 'Unsupported export format. Use Excel, CSV, PDF, JSON, XML, or TXT.'
            }, status=400)

        if not isinstance(events_data, list) or len(events_data) == 0:
            return Response({
                'success': False,
                'message': 'No events available to export.'
            }, status=400)

        # Security: bounded payload to reduce abuse and memory pressure.
        max_export_rows = 5000
        if len(events_data) > max_export_rows:
            return Response({
                'success': False,
                'message': f'Export exceeds limit of {max_export_rows} rows.'
            }, status=400)

        # Security: accept only object rows; reject malformed payloads.
        if any(not isinstance(row, dict) for row in events_data):
            return Response({
                'success': False,
                'message': 'Invalid export payload format.'
            }, status=400)

        tenant_id = get_tenant_id_from_request(request)
        resolved_rows = []
        seen_ids = set()
        for row in events_data:
            key = _export_row_event_identifier(row)
            if key is None:
                return Response({
                    'success': False,
                    'message': 'Invalid export payload: each row must include an event identifier.'
                }, status=400)
            try:
                event = _get_event_for_tenant(tenant_id, key, allow_generated_slug=True)
            except Event.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Event not found'
                }, status=404)
            deny = _guard_event_object_access(request, event)
            if deny:
                payload, code = deny
                return Response(payload, status=code)
            if event.EventId in seen_ids:
                continue
            seen_ids.add(event.EventId)
            resolved_rows.append(_event_to_export_row_dict(event))

        if not resolved_rows:
            return Response({
                'success': False,
                'message': 'No events available to export.'
            }, status=400)

        export_result = s3_export_data(
            data=resolved_rows,
            file_format=normalized_format,
            user_id=str(user_id),
            options={
                'file_name': file_name,
                'module': 'events_list',
                'record_count': len(resolved_rows)
            }
        )

        if export_result.get('success'):
            return Response({
                'success': True,
                'file_url': export_result.get('file_url'),
                'file_name': export_result.get('file_name'),
                'metadata': export_result.get('metadata', {})
            })

        return Response({
            'success': False,
            'message': export_result.get('error', 'Export failed')
        }, status=500)
    except Exception as e:
        _log_exception(e, context='export_events_to_s3')
        return Response({
            'success': False,
            'message': 'Error exporting events. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_event_details(request, event_id):
    """
    Get detailed information about a specific event
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        debug_print(f"DEBUG: Fetching event details for ID: {event_id}")
        try:
            event = _get_event_for_tenant(tenant_id, event_id, allow_generated_slug=False)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return Response(payload, status=code)
        debug_print(f"DEBUG: Found event: {event.EventTitle}")
        
        # Process evidence data from semicolon-separated string to array
        _ev_raw = event.Evidence or ""
        evidence_string = _ev_raw if isinstance(_ev_raw, str) else ""
        evidence_urls = evidence_string.split(';') if evidence_string else []
        evidence_urls = [url.strip() for url in evidence_urls if url.strip()]
        
        # Convert evidence URLs to evidence objects for frontend
        evidence_objects = []
        for i, url in enumerate(evidence_urls):
            # Extract filename from URL
            filename = "Evidence File"
            if url:
                try:
                    # Extract filename from S3 URL
                    if 'amazonaws.com' in url:
                        # Extract from S3 URL like: https://bucket.s3.region.amazonaws.com/path/filename.ext
                        url_parts = url.split('/')
                        if len(url_parts) > 0:
                            filename = url_parts[-1]
                            # Decode URL encoding
                            filename = filename.replace('%20', ' ').replace('%2E', '.')
                    else:
                        # Extract from other URL formats
                        url_parts = url.split('/')
                        if len(url_parts) > 0:
                            filename = url_parts[-1]
                except:
                    filename = f"Evidence File {i + 1}"
            
            evidence_objects.append({
                'id': i + 1,
                'fileName': filename,
                'url': url,
                's3_url': url,
                'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                'uploadDate': event.CreatedAt.strftime('%Y-%m-%d') if event.CreatedAt else 'Unknown',
                'size': 'Unknown'  # Size would need to be stored separately or fetched from S3
            })
        
        try:
            debug_print(f"DEBUG: Building event data for event: {event.EventTitle}")
            event_data = {
                'id': event.EventId,
                'title': event.EventTitle,
                'event_id_generated': event.EventId_Generated,
                'description': event.Description,
                'framework_id': event.FrameworkId.FrameworkId if event.FrameworkId else None,
                'framework': event.FrameworkName or 'Not Assigned',  # Map to 'framework' for frontend
                'framework_name': event.FrameworkName,
                'module': event.Module or 'Not Assigned',
                'linked_record_type': event.LinkedRecordType,
                'linked_record_id': event.LinkedRecordId,
                'linked_record_name': event.LinkedRecordName,
                'category': event.Category or 'Not Assigned',
                'event_type_id': event.EventType.eventtype_id if event.EventType else None,
                'event_type': event.EventType.eventtype if event.EventType else None,
                'event_type_framework': event.EventType.FrameworkName if event.EventType else None,
                'sub_event_type': event.SubEventType,
                'recurrence_type': event.RecurrenceType,
                'frequency': event.Frequency,
                'start_date': event.StartDate,
                'end_date': event.EndDate,
                'status': event.Status or 'Not Assigned',
                'priority': event.Priority or 'Not Assigned',
                'comments': event.Comments,
                'evidence': evidence_objects,  # Include evidence data
                'evidence_string': evidence_string,  # Include raw evidence string
                'owner_id': event.Owner.UserId if event.Owner else None,
                'owner': event.owner_name,  # Use the model property
                'owner_name': event.owner_name,
                'reviewer_id': event.Reviewer.UserId if event.Reviewer else None,
                'reviewer': event.reviewer_name,  # Use the model property
                'reviewer_name': event.reviewer_name,
                'source_system': 'GRC System',  # Add source system field
                'created_by_id': event.CreatedBy.UserId if event.CreatedBy else None,
                'created_by_name': f"{event.CreatedBy.FirstName} {event.CreatedBy.LastName}" if event.CreatedBy else 'Unknown',
                'created_at': event.CreatedAt,
                'updated_at': event.UpdatedAt,
                'approved_at': event.ApprovedAt,
                'dynamic_fields_data': event.DynamicFieldsData
            }
            debug_print(f"DEBUG: Event data built successfully")
        except Exception as e:
            _log_exception(e, context='get_event_details.build_event_data')
            raise e
        
        return Response({
            'success': True,
            'event': event_data
        })
        
    except Event.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Event not found'
        }, status=404)
    except Exception as e:
        _log_exception(e, context='get_event_details')
        return Response({
            'success': False,
            'message': 'Error fetching event details. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_current_user(request):
    """
    Get current logged-in user information
    """
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        user = Users.objects.get(UserId=user_id_int, tenant_id=tenant_id)
        
        # Decrypt encrypted fields using _plain properties
        firstname_plain = getattr(user, 'FirstName_plain', None) or getattr(user, 'FirstName', None)
        lastname_plain = getattr(user, 'LastName_plain', None) or getattr(user, 'LastName', None)
        email_plain = getattr(user, 'email_plain', None) or getattr(user, 'Email', None)
        username_plain = getattr(user, 'UserName_plain', None) or getattr(user, 'UserName', None)
        
        user_data = {
            'id': user.UserId,
            'name': f"{firstname_plain or ''} {lastname_plain or ''}".strip() or username_plain or 'User',
            'first_name': firstname_plain,
            'last_name': lastname_plain,
            'email': email_plain,
            'username': username_plain
        }
        
        return Response({
            'success': True,
            'user': user_data
        })
        
    except Users.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        _log_exception(e, context='get_current_user')
        return Response({
            'success': False,
            'message': 'Error fetching user. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def test_dynamic_fields_endpoint(request):
    """
    Test endpoint to verify URL routing is working
    """
    debug_print("DEBUG: test_dynamic_fields_endpoint called")
    return Response({
        'success': True,
        'message': 'Dynamic fields endpoint is working',
        'path': request.path,
        'method': request.method
    })

@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_dynamic_fields_for_event(request):
    """
    Get dynamic fields configuration based on framework and event type selection
    """
    debug_print("DEBUG: get_dynamic_fields_for_event called")
    debug_print(f"DEBUG: Request path: {request.path}")
    debug_print(f"DEBUG: Request method: {request.method}")
    debug_print(f"DEBUG: Request GET params: {request.GET}")
    try:
        framework_name = request.GET.get('framework_name')
        event_type_id = request.GET.get('event_type_id')
        sub_event_type_id = request.GET.get('sub_event_type_id')
        
        debug_print(f"DEBUG: framework_name='{framework_name}', event_type_id='{event_type_id}', sub_event_type_id='{sub_event_type_id}'")
        
        if not framework_name or not event_type_id:
            return Response({
                'success': False,
                'message': 'Framework name and event type ID are required'
            }, status=400)
        
        # Get the event type object
        try:
            event_type = EventType.objects.get(
                eventtype_id=event_type_id,
                FrameworkName=framework_name.strip()
            )
        except EventType.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event type not found'
            }, status=404)
        
        # Default field configuration (excluding fields already in the main form)
        default_fields = {
            'priority': {
                'type': 'select',
                'label': 'Priority',
                'required': True,
                'options': [
                    {'value': 'Low', 'label': 'Low'},
                    {'value': 'Medium', 'label': 'Medium'},
                    {'value': 'High', 'label': 'High'},
                    {'value': 'Critical', 'label': 'Critical'}
                ],
                'default': 'Medium',
                'description': 'Event priority level'
            }
        }
        
        # Get dynamic fields from event type configuration
        dynamic_fields = {}
        
        # Parse the JSON data from eventSubtype field
        if event_type.eventSubtype:
            try:
                # eventSubtype is already a JSON field, so we can access it directly
                event_subtype_data = event_type.eventSubtype
                debug_print(f"DEBUG: Raw eventSubtype data: {event_subtype_data}")
                
                if isinstance(event_subtype_data, dict):
                    # Get the sub-event type name from the index
                    sub_event_type_name = None
                    if sub_event_type_id is not None:
                        try:
                            sub_event_type_index = int(sub_event_type_id)
                            sub_event_type_keys = list(event_subtype_data.keys())
                            if 0 <= sub_event_type_index < len(sub_event_type_keys):
                                sub_event_type_name = sub_event_type_keys[sub_event_type_index]
                                debug_print(f"DEBUG: Selected sub-event type: {sub_event_type_name}")
                                
                                # Get the configuration for this sub-event type
                                sub_event_config = event_subtype_data.get(sub_event_type_name, {})
                                debug_print(f"DEBUG: Sub-event config: {sub_event_config}")
                                
                                # Parse the configuration to create dynamic fields
                                dynamic_fields = parse_event_subtype_config(sub_event_config, sub_event_type_name)
                                
                        except (ValueError, IndexError, KeyError) as e:
                            _log_exception(e, context='get_dynamic_fields.sub_event_type')
                            # Continue with empty dynamic fields if there's an error
                            pass
                    else:
                        # If no sub-event type is selected, use the first available one
                        if event_subtype_data:
                            first_key = list(event_subtype_data.keys())[0]
                            sub_event_config = event_subtype_data.get(first_key, {})
                            dynamic_fields = parse_event_subtype_config(sub_event_config, first_key)
                            
            except Exception as e:
                _log_exception(e, context='get_dynamic_fields.eventSubtype_json')
                # Continue with empty dynamic fields if there's an error
                pass
        
        # Merge default fields with dynamic fields
        all_fields = {**default_fields, **dynamic_fields}
        
        debug_print(f"DEBUG: Returning {len(all_fields)} fields for event type '{event_type.eventtype}'")
        
        # Get the sub-event type name for the response
        sub_event_type_name = None
        if sub_event_type_id is not None and event_type.eventSubtype:
            try:
                sub_event_type_index = int(sub_event_type_id)
                if isinstance(event_type.eventSubtype, dict):
                    sub_event_type_keys = list(event_type.eventSubtype.keys())
                    if 0 <= sub_event_type_index < len(sub_event_type_keys):
                        sub_event_type_name = sub_event_type_keys[sub_event_type_index]
            except (ValueError, IndexError, KeyError):
                pass
        
        return Response({
            'success': True,
            'fields': all_fields,
            'event_type': event_type.eventtype,
            'framework_name': framework_name,
            'sub_event_type': sub_event_type_name
        })
        
    except Exception as e:
        _log_exception(e, context='get_dynamic_fields_for_event')
        return Response({
            'success': False,
            'message': 'Error fetching dynamic fields. Please try again later.'
        }, status=500)


def parse_event_subtype_config(sub_event_config, sub_event_type_name):
    """
    Parse the JSON configuration from eventSubtype and convert it to dynamic fields
    """
    dynamic_fields = {}
    
    try:
        debug_print(f"DEBUG: Parsing config for '{sub_event_type_name}': {sub_event_config}")
        
        # Recursively parse the configuration
        def parse_config_recursive(config, prefix=""):
            fields = {}
            
            for key, value in config.items():
                field_key = f"{prefix}_{key}".strip("_") if prefix else key
                field_key = field_key.lower().replace(" ", "_").replace("&", "and")
                
                if isinstance(value, dict):
                    # If it's a nested object, create a field for it
                    if any(isinstance(v, dict) for v in value.values()):
                        # It has nested objects, create a section header
                        fields[field_key] = {
                            'type': 'section',
                            'label': key.replace("_", " ").title(),
                            'description': f'Configuration for {key}',
                            'children': parse_config_recursive(value, field_key)
                        }
                    else:
                        # It's a simple key-value mapping, create a select field
                        if value:
                            options = []
                            for opt_key, opt_value in value.items():
                                if isinstance(opt_value, str) and opt_value.strip():
                                    options.append({'value': opt_key, 'label': f"{opt_key}: {opt_value}"})
                                else:
                                    options.append({'value': opt_key, 'label': opt_key})
                            
                            if options:
                                fields[field_key] = {
                                    'type': 'select',
                                    'label': key.replace("_", " ").title(),
                                    'required': False,
                                    'options': options,
                                    'description': f'Select {key.lower()}'
                                }
                        else:
                            # Empty dict, create a text field
                            fields[field_key] = {
                                'type': 'text',
                                'label': key.replace("_", " ").title(),
                                'required': False,
                                'placeholder': f'Enter {key.lower()}',
                                'description': f'Specify {key.lower()}'
                            }
                elif isinstance(value, str):
                    # String value, create a text field with the value as placeholder
                    fields[field_key] = {
                        'type': 'text',
                        'label': key.replace("_", " ").title(),
                        'required': False,
                        'placeholder': value if value.strip() else f'Enter {key.lower()}',
                        'description': f'Specify {key.lower()}'
                    }
                elif isinstance(value, list):
                    # List value, create a select field with list items as options
                    if value:
                        options = [{'value': item, 'label': str(item)} for item in value if str(item).strip()]
                        if options:
                            fields[field_key] = {
                                'type': 'select',
                                'label': key.replace("_", " ").title(),
                                'required': False,
                                'options': options,
                                'description': f'Select {key.lower()}'
                            }
                    else:
                        # Empty list, create a text field
                        fields[field_key] = {
                            'type': 'text',
                            'label': key.replace("_", " ").title(),
                            'required': False,
                            'placeholder': f'Enter {key.lower()}',
                            'description': f'Specify {key.lower()}'
                        }
                else:
                    # Other types, create a text field
                    fields[field_key] = {
                        'type': 'text',
                        'label': key.replace("_", " ").title(),
                        'required': False,
                        'placeholder': f'Enter {key.lower()}',
                        'description': f'Specify {key.lower()}'
                    }
            
            return fields
        
        # Parse the configuration
        parsed_fields = parse_config_recursive(sub_event_config)
        dynamic_fields.update(parsed_fields)
        
        debug_print(f"DEBUG: Generated {len(dynamic_fields)} dynamic fields")
        for field_key, field_config in dynamic_fields.items():
            debug_print(f"DEBUG: Field '{field_key}': {field_config.get('type', 'unknown')} - {field_config.get('label', 'No label')}")
        
    except Exception as e:
        _log_exception(e, context='parse_event_subtype_config')
    
    return dynamic_fields


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_users_for_reviewer(request):
    """
    Get all users except the current user for reviewer selection
    """
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        current_user_id = _get_server_user_id(request)
        if not current_user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get all users except the current user, filtered by tenant
        # Explicitly query default DB (grc2) to avoid cross-database routing ambiguity.
        users = Users.objects.using('default').filter(tenant_id=tenant_id).exclude(UserId=current_user_id).values(
            'UserId', 'FirstName', 'LastName', 'Email', 'UserName'
        )
        
        users_list = []
        for user in users:
            users_list.append({
                'id': user['UserId'],
                'name': f"{user['FirstName']} {user['LastName']}".strip(),
                'first_name': user['FirstName'],
                'last_name': user['LastName'],
                'email': user['Email'],
                'username': user['UserName']
            })
        
        return Response({
            'success': True,
            'users': users_list
        })
        
    except Exception as e:
        _log_exception(e, context='get_users_for_reviewer')
        return Response({
            'success': False,
            'message': 'Error fetching users. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_events_for_calendar(request):
    """
    Get events for calendar display (recurring events only, including all event types)
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get only recurring events for calendar - include ALL events
        events_query = Event.objects.filter(tenant_id=tenant_id, 
            RecurrenceType='Recurring',
            IsTemplate=False
        ).select_related(
            'Owner', 'Reviewer', 'FrameworkId'
        )
        events_query = _apply_event_list_scope(events_query, user_id_int)
        
        # Apply framework filtering
        from ..Policy.framework_filter_helper import apply_framework_filter, get_framework_filter_info
        filter_info = get_framework_filter_info(request)
        debug_print(f"🔍 DEBUG: Framework filter info for get_events_for_calendar: {filter_info}")
        events_query = apply_framework_filter(events_query, request, 'FrameworkId')
        
        events = events_query.values(
            'EventId', 'EventTitle', 'EventId_Generated', 'FrameworkName',
            'Module', 'Category', 'Status', 'Priority', 'Frequency',
            'StartDate', 'EndDate', 'CreatedAt', 'Description',
            'Owner__FirstName', 'Owner__LastName', 'Reviewer__FirstName', 
            'Reviewer__LastName'
        )
        
        formatted_events = []
        for event in events:
            formatted_events.append({
                'id': event['EventId'],
                'title': event['EventTitle'],
                'event_id': event['EventId_Generated'],
                'framework': event['FrameworkName'],
                'module': event['Module'],
                'category': event['Category'],
                'status': event['Status'],
                'priority': event['Priority'],
                'description': event.get('Description') or '',
                'frequency': event['Frequency'],
                'start_date': event['StartDate'].strftime('%Y-%m-%d') if event['StartDate'] else None,
                'end_date': event['EndDate'].strftime('%Y-%m-%d') if event['EndDate'] else None,
                'owner': f"{event['Owner__FirstName']} {event['Owner__LastName']}" if event['Owner__FirstName'] else 'Not Assigned',
                'reviewer': f"{event['Reviewer__FirstName']} {event['Reviewer__LastName']}" if event['Reviewer__FirstName'] else 'Not Assigned',
                'created_at': _format_datetime_ist(event['CreatedAt']) if event['CreatedAt'] else ''
            })
        
        return Response({
            'success': True,
            'events': formatted_events
        })
        
    except Exception as e:
        _log_exception(e, context='get_events_for_calendar')
        return Response({
            'success': False,
            'message': 'Error fetching calendar events. Please try again later.'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventEditPermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def create_events_table(request):
    """
    Create the events table if it doesn't exist
    """
    if not _event_schema_maintenance_allowed():
        return Response({'success': False, 'message': 'Not found.'}, status=404)
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # First, check if table exists and add missing columns
            try:
                cursor.execute("ALTER TABLE events ADD COLUMN SubEventType VARCHAR(100)")
                debug_print("Added SubEventType column")
            except Exception as e:
                debug_print(f"SubEventType column may already exist: {e}")
            
            try:
                cursor.execute("ALTER TABLE events ADD COLUMN DynamicFieldsData JSON")
                debug_print("Added DynamicFieldsData column")
            except Exception as e:
                debug_print(f"DynamicFieldsData column may already exist: {e}")
            
            # Create events table matching the exact database structure
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    EventId INT AUTO_INCREMENT PRIMARY KEY,
                    EventTitle VARCHAR(255) NOT NULL,
                    EventId_Generated VARCHAR(50) UNIQUE NOT NULL,
                    Description TEXT,
                    
                    -- Framework and Module Information
                    FrameworkId INT,
                    FrameworkName VARCHAR(255),
                    Module VARCHAR(255),
                    
                    -- Linked Records
                    LinkedRecordType VARCHAR(50),
                    LinkedRecordId INT,
                    LinkedRecordName VARCHAR(255),
                    
                    -- Event Details
                    Category VARCHAR(100),
                    OwnerId INT,
                    ReviewerId INT,
                    
                    -- Recurrence Information
                    RecurrenceType VARCHAR(20) DEFAULT 'Non-Recurring',
                    Frequency VARCHAR(50),
                    StartDate DATE,
                    EndDate DATE,
                    
                    -- Status and Dates
                    Status VARCHAR(50) DEFAULT 'Draft',
                    Priority VARCHAR(20) DEFAULT 'Medium',
                    
                    -- Evidence and Attachments
                    Evidence JSON,
                    CreatedById INT,
                    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    ApprovedAt TIMESTAMP NULL,
                    IsTemplate TINYINT(1) DEFAULT 0,
                    comments VARCHAR(255),
                    EventTypeId INT,
                    DynamicFieldsData JSON,
                    SubEventType VARCHAR(100),
                    
                    -- Foreign Key Constraints
                    FOREIGN KEY (FrameworkId) REFERENCES frameworks(FrameworkId) ON DELETE SET NULL,
                    FOREIGN KEY (EventTypeId) REFERENCES eventtype(eventtype_id) ON DELETE SET NULL,
                    FOREIGN KEY (OwnerId) REFERENCES users(UserId) ON DELETE SET NULL,
                    FOREIGN KEY (ReviewerId) REFERENCES users(UserId) ON DELETE SET NULL,
                    FOREIGN KEY (CreatedById) REFERENCES users(UserId) ON DELETE SET NULL
                )
            """)
            
            return Response({
                'success': True,
                'message': 'Events table created successfully'
            })
            
    except Exception as e:
        _log_exception(e, context='create_events_table')
        return Response({
            'success': False,
            'message': 'Error creating events table. Please try again later.'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventEditPermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def fix_events_table_schema(request):
    """
    Fix the events table schema by adding missing columns
    """
    if not _event_schema_maintenance_allowed():
        return Response({'success': False, 'message': 'Not found.'}, status=404)
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Check if EventTypeId column exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'events' 
                AND COLUMN_NAME = 'EventTypeId'
            """)
            event_type_exists = cursor.fetchone()[0] > 0
            
            # Check if SubEventType column exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'events' 
                AND COLUMN_NAME = 'SubEventType'
            """)
            sub_event_type_exists = cursor.fetchone()[0] > 0
            
            # Add missing columns
            if not event_type_exists:
                cursor.execute("ALTER TABLE events ADD COLUMN EventTypeId INT")
                debug_print("Added EventTypeId column to events table")
            
            if not sub_event_type_exists:
                cursor.execute("ALTER TABLE events ADD COLUMN SubEventType VARCHAR(100)")
                debug_print("Added SubEventType column to events table")
            
            # Add foreign key constraint for EventTypeId if it doesn't exist
            if not event_type_exists:
                try:
                    cursor.execute("""
                        ALTER TABLE events 
                        ADD CONSTRAINT fk_events_eventtype 
                        FOREIGN KEY (EventTypeId) REFERENCES eventtype(eventtype_id) ON DELETE SET NULL
                    """)
                    debug_print("Added foreign key constraint for EventTypeId")
                except Exception as e:
                    debug_print(f"Could not add foreign key constraint: {e}")
            
            return Response({
                'success': True,
                'message': 'Events table schema fixed successfully',
                'changes': {
                    'event_type_id_added': not event_type_exists,
                    'sub_event_type_added': not sub_event_type_exists
                }
            })
            
    except Exception as e:
        _log_exception(e, context='fix_events_table_schema')
        return Response({
            'success': False,
            'message': 'Error fixing events table schema. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventDashboardPermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_events_dashboard(request):
    """
    Get events dashboard analytics and KPIs with optional filters
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        # Get filter parameters from request
        framework_filter = request.GET.get('framework', '')
        module_filter = request.GET.get('module', '')
        category_filter = request.GET.get('category', '')
        owner_filter = request.GET.get('owner', '')
        
        debug_print(f"DEBUG: Dashboard filters - Framework: {framework_filter}, Module: {module_filter}, Category: {category_filter}, Owner: {owner_filter}")
        
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Build base query with filters - include ALL events (including RiskaVaire events)
        # Show all events in the dashboard for comprehensive view
        base_query = Event.objects.filter(tenant_id=tenant_id, IsTemplate=False)
        base_query = _apply_event_list_scope(base_query, user_id_int)
        
        # Apply framework filtering using the standard framework filter helper
        from ..Policy.framework_filter_helper import apply_framework_filter, get_framework_filter_info
        filter_info = get_framework_filter_info(request)
        debug_print(f"🔍 DEBUG: Framework filter info for get_events_dashboard: {filter_info}")
        base_query = apply_framework_filter(base_query, request, 'FrameworkId')
        
        # Apply additional framework filter if provided in request (for backward compatibility)
        if framework_filter:
            base_query = base_query.filter(FrameworkName__icontains=framework_filter)
        
        if module_filter:
            base_query = base_query.filter(Module__icontains=module_filter)
        
        if category_filter:
            base_query = base_query.filter(Category__icontains=category_filter)
        
        if owner_filter:
            base_query = base_query.filter(
                Q(Owner__FirstName__icontains=owner_filter) | 
                Q(Owner__LastName__icontains=owner_filter)
            )
        
        # Get current date and calculate date ranges
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        
        # Calculate KPIs using filtered query
        total_events = base_query.count()
        
        # Upcoming events (next 30 days)
        upcoming_events = base_query.filter(
            StartDate__gte=now.date(),
            StartDate__lte=(now + timedelta(days=30)).date()
        ).count()
        
        # Overdue events (past due date and not completed)
        overdue_events = base_query.filter(
            EndDate__lt=now.date(),
            Status__in=['Draft', 'Submitted', 'Under Review']
        ).count()
        
        # Pending approvals
        pending_approvals = base_query.filter(
            Status='Under Review'
        ).count()
        
        # Events by status
        events_by_status = base_query.values('Status').annotate(
            count=Count('EventId')
        ).order_by('Status')
        
        # Events by category
        events_by_category = base_query.values('Category').annotate(
            count=Count('EventId')
        ).order_by('Category')
        
        # Events by framework
        events_by_framework = base_query.values('FrameworkName').annotate(
            count=Count('EventId')
        ).order_by('FrameworkName')
        
        # Events by priority
        events_by_priority = base_query.values('Priority').annotate(
            count=Count('EventId')
        ).order_by('Priority')
        
        # Monthly event trends (last 6 months) using filtered query
        monthly_trends = []
        for i in range(6):
            month_start = now - timedelta(days=30 * (i + 1))
            month_end = now - timedelta(days=30 * i)
            
            month_events = base_query.filter(
                CreatedAt__gte=month_start,
                CreatedAt__lt=month_end
            ).count()
            
            month_name = month_start.strftime('%b')
            monthly_trends.append({
                'month': month_name,
                'count': month_events
            })
        
        # Reverse to show chronological order (oldest to newest)
        monthly_trends.reverse()
        
        # Recent events (last 7 days) - limit to 3 most recent using filtered query
        recent_events = base_query.filter(
            CreatedAt__gte=seven_days_ago
        ).select_related('Owner', 'Reviewer').values(
            'EventId', 'EventTitle', 'EventId_Generated', 'Status', 'Category',
            'Owner__FirstName', 'Owner__LastName', 'Reviewer__FirstName', 
            'Reviewer__LastName', 'CreatedAt'
        ).order_by('-CreatedAt')[:3]
        
        # Format recent events
        formatted_recent_events = []
        for event in recent_events:
            formatted_recent_events.append({
                'id': event['EventId'],
                'title': event['EventTitle'],
                'event_id': event['EventId_Generated'],
                'status': event['Status'],
                'category': event['Category'],
                'owner': f"{event['Owner__FirstName']} {event['Owner__LastName']}" if event['Owner__FirstName'] else 'Not Assigned',
                'reviewer': f"{event['Reviewer__FirstName']} {event['Reviewer__LastName']}" if event['Reviewer__FirstName'] else 'Not Assigned',
                'created_at': _format_datetime_ist(event['CreatedAt']) if event['CreatedAt'] else ''
            })
        
        # Calculate trends (comparing last 30 days with previous 30 days)
        previous_period_start = now - timedelta(days=60)
        previous_period_end = now - timedelta(days=30)
        
        current_period_events = base_query.filter(
            CreatedAt__gte=thirty_days_ago
        ).count()
        
        previous_period_events = base_query.filter(
            CreatedAt__gte=previous_period_start,
            CreatedAt__lt=previous_period_end
        ).count()
        
        # Calculate trend percentage
        if previous_period_events > 0:
            trend_percentage = ((current_period_events - previous_period_events) / previous_period_events) * 100
        else:
            trend_percentage = 100 if current_period_events > 0 else 0
        
        # Calculate completion rate trends (last 6 months)
        completion_trends = []
        for i in range(6):
            month_start = now - timedelta(days=30 * (i + 1))
            month_end = now - timedelta(days=30 * i)
            
            month_total = base_query.filter(
                CreatedAt__gte=month_start,
                CreatedAt__lt=month_end
            ).count()
            
            month_completed = base_query.filter(
                CreatedAt__gte=month_start,
                CreatedAt__lt=month_end,
                Status='Completed'
            ).count()
            
            completion_rate = (month_completed / month_total * 100) if month_total > 0 else 0
            
            month_name = month_start.strftime('%b')
            completion_trends.append({
                'month': month_name,
                'completion_rate': round(completion_rate, 1),
                'total_events': month_total,
                'completed_events': month_completed
            })
        
        # Reverse to show chronological order (oldest to newest)
        completion_trends.reverse()
        
        return Response({
            'success': True,
            'kpis': {
                'total_events': total_events,
                'upcoming_events': upcoming_events,
                'overdue_events': overdue_events,
                'pending_approvals': pending_approvals,
                'trend_percentage': round(trend_percentage, 1)
            },
            'charts': {
                'events_by_status': list(events_by_status),
                'events_by_category': list(events_by_category),
                'events_by_framework': list(events_by_framework),
                'events_by_priority': list(events_by_priority),
                'monthly_trends': monthly_trends,
                'completion_trends': completion_trends
            },
            'recent_events': formatted_recent_events
        })
        
    except Exception as e:
        _log_exception(e, context='get_events_dashboard')
        return Response({
            'success': False,
            'message': 'Error fetching dashboard data. Please try again later.'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventApprovePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approve_event(request, event_id):
    """
    Approve an event (reviewer action)
    """
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        data = request.data
        comments = data.get('comments', '')
        
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id, tenant_id=tenant_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return Response(payload, status=code)
        
        # Check if user is the reviewer
        if event.Reviewer and event.Reviewer.UserId != user_id_int:
            return Response({
                'success': False,
                'message': 'Only the assigned reviewer can approve this event'
            }, status=403)
        
        # Check if event is in a reviewable status
        reviewable_statuses = ['Pending Review', 'Under Review', 'Pending Approval']
        if event.Status not in reviewable_statuses:
            return Response({
                'success': False,
                'message': f'Event must be in a reviewable status to be approved. Current status: {event.Status}. Allowed statuses: {", ".join(reviewable_statuses)}'
            }, status=400)
        
        # Store old status for notification
        old_status = event.Status
        
        # Update event status
        event.Status = 'Approved'
        event.ApprovedAt = timezone.now()
        if comments:
            event.Comments = comments
        event.save()
        
        status_dedup = str(event.Status or '')
        
        # Send email notification for status change
        try:
            from ...routes.Global.notification_service import NotificationService
            from ...routes.Global.notifications import (
                send_event_aware_multi_channel,
                append_event_notification_in_app,
            )
            notification_service = NotificationService()
            import uuid
            from datetime import datetime as dt
            
            # Get actor name
            actor = Users.objects.filter(tenant_id=tenant_id, UserId=user_id_int).first()
            actor_name = actor.UserName if actor else 'System'
            
            # Collect recipients
            recipients = []
            if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                recipients.append({
                    'email': event.Owner.Email,
                    'name': event.Owner.UserName or event.Owner.Email.split('@')[0],
                    'user_id': event.Owner.UserId
                })
            if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                recipients.append({
                    'email': event.Reviewer.Email,
                    'name': event.Reviewer.UserName or event.Reviewer.Email.split('@')[0],
                    'user_id': event.Reviewer.UserId
                })
            if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                recipients.append({
                    'email': event.CreatedBy.Email,
                    'name': event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0],
                    'user_id': event.CreatedBy.UserId
                })
            
            # Send notifications
            for recipient in recipients:
                try:
                    notification_data = {
                        'notification_type': 'eventStatusChanged',
                        'email': recipient['email'],
                        'email_type': 'gmail',
                        'template_data': [
                            recipient['name'],
                            event.EventTitle,
                            old_status,
                            event.Status,
                            actor_name
                        ]
                    }
                    send_event_aware_multi_channel(
                        notification_service,
                        notification_data,
                        event.EventId,
                        recipient_user_id=recipient['user_id'],
                        dedup_extra=status_dedup,
                    )
                    
                    # In-app notification
                    notification = {
                        'id': str(uuid.uuid4()),
                        'title': 'Event Status Updated',
                        'message': f'Event "{event.EventTitle}" has been approved.',
                        'category': 'event',
                        'priority': 'medium',
                        'createdAt': dt.now().isoformat(),
                        'status': {'isRead': False, 'readAt': None},
                        'user_id': str(recipient['user_id'])
                    }
                    append_event_notification_in_app(
                        notification, event.EventId, 'eventStatusChanged', dedup_extra=status_dedup
                    )
                except Exception as notify_error:
                    _log_exception(notify_error, context='approve_event.notify')
        except Exception as notify_ex:
            _log_exception(notify_ex, context='approve_event.notify_service')
        
        return Response({
            'success': True,
            'message': 'Event approved successfully',
            'event_id': event.EventId,
            'status': event.Status
        })
        
    except Exception as e:
        _log_exception(e, context='approve_event')
        return Response({
            'success': False,
            'message': 'Error approving event. Please try again later.'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventRejectPermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def reject_event(request, event_id):
    """
    Reject an event (reviewer action)
    """
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        data = request.data
        comments = data.get('comments', '')
        
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id, tenant_id=tenant_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return Response(payload, status=code)
        
        # Check if user is the reviewer
        if event.Reviewer and event.Reviewer.UserId != user_id_int:
            return Response({
                'success': False,
                'message': 'Only the assigned reviewer can reject this event'
            }, status=403)
        
        # Check if event is in a reviewable status
        reviewable_statuses = ['Pending Review', 'Under Review', 'Pending Approval']
        if event.Status not in reviewable_statuses:
            return Response({
                'success': False,
                'message': f'Event must be in a reviewable status to be rejected. Current status: {event.Status}. Allowed statuses: {", ".join(reviewable_statuses)}'
            }, status=400)
        
        # Store old status for notification
        old_status = event.Status
        
        # Update event status
        event.Status = 'Rejected'
        event.UpdatedAt = timezone.now()
        if comments:
            event.Comments = comments
        event.save()
        
        status_dedup = str(event.Status or '')
        
        # Send email notification for status change
        try:
            from ...routes.Global.notification_service import NotificationService
            from ...routes.Global.notifications import (
                send_event_aware_multi_channel,
                append_event_notification_in_app,
            )
            notification_service = NotificationService()
            import uuid
            from datetime import datetime as dt
            
            # Get actor name
            actor = Users.objects.filter(tenant_id=tenant_id, UserId=user_id_int).first()
            actor_name = actor.UserName if actor else 'System'
            
            # Collect recipients
            recipients = []
            if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                recipients.append({
                    'email': event.Owner.Email,
                    'name': event.Owner.UserName or event.Owner.Email.split('@')[0],
                    'user_id': event.Owner.UserId
                })
            if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                recipients.append({
                    'email': event.Reviewer.Email,
                    'name': event.Reviewer.UserName or event.Reviewer.Email.split('@')[0],
                    'user_id': event.Reviewer.UserId
                })
            if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                recipients.append({
                    'email': event.CreatedBy.Email,
                    'name': event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0],
                    'user_id': event.CreatedBy.UserId
                })
            
            # Send notifications
            for recipient in recipients:
                try:
                    notification_data = {
                        'notification_type': 'eventStatusChanged',
                        'email': recipient['email'],
                        'email_type': 'gmail',
                        'template_data': [
                            recipient['name'],
                            event.EventTitle,
                            old_status,
                            event.Status,
                            actor_name
                        ]
                    }
                    send_event_aware_multi_channel(
                        notification_service,
                        notification_data,
                        event.EventId,
                        recipient_user_id=recipient['user_id'],
                        dedup_extra=status_dedup,
                    )
                    
                    # In-app notification
                    notification = {
                        'id': str(uuid.uuid4()),
                        'title': 'Event Status Updated',
                        'message': f'Event "{event.EventTitle}" has been rejected.',
                        'category': 'event',
                        'priority': 'high',
                        'createdAt': dt.now().isoformat(),
                        'status': {'isRead': False, 'readAt': None},
                        'user_id': str(recipient['user_id'])
                    }
                    append_event_notification_in_app(
                        notification, event.EventId, 'eventStatusChanged', dedup_extra=status_dedup
                    )
                except Exception as notify_error:
                    _log_exception(notify_error, context='reject_event.notify')
        except Exception as notify_ex:
            _log_exception(notify_ex, context='reject_event.notify_service')
        
        return Response({
            'success': True,
            'message': 'Event rejected successfully',
            'event_id': event.EventId,
            'status': event.Status
        })
        
    except Exception as e:
        _log_exception(e, context='reject_event')
        return Response({
            'success': False,
            'message': 'Error rejecting event. Please try again later.'
        }, status=500)


@api_view(['PUT'])
@permission_classes([EventEditPermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def update_event(request, event_id):
    """Update an event"""
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)

        # Parse request data - handle both DRF request.data and raw JSON
        data = request.data if hasattr(request, 'data') else {}
        if not data and request.body:
            try:
                data = json.loads(request.body)
            except (json.JSONDecodeError, TypeError):
                data = {}

        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id, tenant_id=tenant_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return Response(payload, status=code)
        
        debug_print(f"DEBUG: Event {event_id} - CreatedBy: {event.CreatedBy}, Reviewer: {event.Reviewer}, User: {user_id_int}")
        
        # Update event fields (validated lengths / allow-listed enums)
        if 'title' in data or 'EventTitle' in data or 'name' in data:
            new_title = data.get('title') or data.get('EventTitle') or data.get('name')
            new_title = str(new_title).strip() if new_title is not None else ''
            if not new_title:
                return Response({
                    'success': False,
                    'message': 'Event title cannot be empty.'
                }, status=400)
            if len(new_title) > _EVENT_MAX_TITLE_LEN:
                return Response({
                    'success': False,
                    'message': f'Event title must be at most {_EVENT_MAX_TITLE_LEN} characters.'
                }, status=400)
            event.EventTitle = new_title
        if 'description' in data:
            event.Description = data['description']
        if 'framework' in data or 'framework_name' in data:
            raw_fw = data['framework_name'] if 'framework_name' in data else data.get('framework')
            try:
                event.FrameworkName = _sanitize_optional_str_field(
                    raw_fw, _EVENT_MAX_FRAMEWORK_NAME_LEN, 'Framework name'
                )
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
        if 'module' in data:
            try:
                event.Module = _sanitize_optional_str_field(
                    data['module'], _EVENT_MAX_MODULE_LEN, 'Module'
                )
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
        if 'category' in data or 'type' in data:
            raw_cat = data['category'] if 'category' in data else data.get('type')
            try:
                event.Category = _sanitize_optional_str_field(
                    raw_cat, _EVENT_MAX_CATEGORY_LEN, 'Category'
                )
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
        if 'recurrence_type' in data:
            try:
                event.RecurrenceType = _normalize_event_recurrence_type(data['recurrence_type'])
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
        if 'frequency' in data:
            if event.RecurrenceType == 'Non-Recurring':
                event.Frequency = None
            else:
                fv = data['frequency']
                if fv in ('', None):
                    event.Frequency = None
                else:
                    try:
                        event.Frequency = _sanitize_optional_str_field(fv, 50, 'Frequency')
                    except ValueError as ve:
                        return Response({
                            'success': False,
                            'message': str(ve)
                        }, status=400)
        if 'priority' in data:
            try:
                event.Priority = _normalize_event_priority(data['priority'])
            except ValueError as ve:
                return Response({
                    'success': False,
                    'message': str(ve)
                }, status=400)
        
        # Status transitions must use approve/reject/archive (or other workflow) endpoints —
        # do not accept client-supplied status on generic update (prevents privilege escalation).
        
        # Handle evidence updates
        if 'evidence' in data:
            evidence_data = data.get('evidence', [])
            evidence_urls = []
            
            debug_print(f"DEBUG: Updating evidence for event {event_id}")
            debug_print(f"DEBUG: Raw evidence data from request: {evidence_data}")
            
            # Handle evidence data - could be JSON string or array
            evidence_files = []
            if isinstance(evidence_data, str):
                try:
                    # Parse JSON string
                    evidence_files = json.loads(evidence_data)
                    debug_print(f"DEBUG: Parsed evidence JSON: {evidence_files}")
                except json.JSONDecodeError as e:
                    debug_print(f"DEBUG: Failed to parse evidence JSON: {e}")
                    evidence_files = []
            elif isinstance(evidence_data, list):
                # Already an array
                evidence_files = evidence_data
            
            # Process evidence files and extract S3 URLs
            if evidence_files:
                debug_print(f"DEBUG: Processing {len(evidence_files)} evidence files")
                for i, evidence_file in enumerate(evidence_files):
                    if not isinstance(evidence_file, dict):
                        return Response({
                            'success': False,
                            'message': 'Each evidence entry must be an object.',
                        }, status=400)
                    raw_url = evidence_file.get('s3_url')
                    if not raw_url:
                        continue
                    try:
                        safe_url = _validate_event_evidence_s3_url(
                            raw_url, field_label=f'evidence[{i}].s3_url'
                        )
                        if safe_url:
                            evidence_urls.append(safe_url)
                    except ValueError as ve:
                        return Response({
                            'success': False,
                            'message': _sanitize_reflected_error_detail(str(ve)),
                        }, status=400)
            else:
                debug_print("DEBUG: No evidence files provided")
            
            # Create semicolon-separated string of URLs
            evidence_string = ";".join(evidence_urls) if evidence_urls else ""
            debug_print(f"DEBUG: Final evidence string to save: '{evidence_string}'")
            debug_print(f"DEBUG: Evidence string length: {len(evidence_string)}")
            
            # Update the event's evidence
            event.Evidence = evidence_string
        
        # Handle owner assignment - convert name to Users instance
        if 'owner' in data and data['owner']:
            try:
                # Try to find user by full name (FirstName + LastName)
                owner_name = data['owner'].strip()
                if ' ' in owner_name:
                    first_name, last_name = owner_name.split(' ', 1)
                    owner_user = Users.objects.filter(tenant_id=tenant_id, 
                        FirstName__iexact=first_name.strip(),
                        LastName__iexact=last_name.strip()
                    ).first()
                else:
                    # If no space, try to find by first name or last name
                    owner_user = Users.objects.filter(
                        models.Q(FirstName__iexact=owner_name) | 
                        models.Q(LastName__iexact=owner_name),
                        tenant_id=tenant_id
                    ).first()
                
                if owner_user:
                    event.Owner = owner_user
                else:
                    debug_print(f"DEBUG: Owner user not found for name: {owner_name}")
            except Exception as e:
                _log_exception(e, context='update_event.owner_lookup')
        
        # Handle reviewer assignment - convert name to Users instance
        if 'reviewer' in data and data['reviewer']:
            try:
                # Try to find user by full name (FirstName + LastName)
                reviewer_name = data['reviewer'].strip()
                if ' ' in reviewer_name:
                    first_name, last_name = reviewer_name.split(' ', 1)
                    reviewer_user = Users.objects.filter(tenant_id=tenant_id, 
                        FirstName__iexact=first_name.strip(),
                        LastName__iexact=last_name.strip()
                    ).first()
                else:
                    # If no space, try to find by first name or last name
                    reviewer_user = Users.objects.filter(
                        models.Q(FirstName__iexact=reviewer_name) | 
                        models.Q(LastName__iexact=reviewer_name),
                        tenant_id=tenant_id
                    ).first()
                
                if reviewer_user:
                    event.Reviewer = reviewer_user
                else:
                    debug_print(f"DEBUG: Reviewer user not found for name: {reviewer_name}")
            except Exception as e:
                _log_exception(e, context='update_event.reviewer_lookup')
        
        if any(k in data for k in ('start_date', 'StartDate', 'end_date', 'EndDate')):
            new_start = event.StartDate
            new_end = event.EndDate
            if 'start_date' in data or 'StartDate' in data:
                rs = data['start_date'] if 'start_date' in data else data['StartDate']
                if rs in ('', None):
                    new_start = None
                else:
                    try:
                        new_start = _parse_event_date_value(rs, 'Start date')
                    except ValueError as ve:
                        return Response({
                            'success': False,
                            'message': str(ve)
                        }, status=400)
            if 'end_date' in data or 'EndDate' in data:
                re_val = data['end_date'] if 'end_date' in data else data['EndDate']
                if re_val in ('', None):
                    new_end = None
                else:
                    try:
                        new_end = _parse_event_date_value(re_val, 'End date')
                    except ValueError as ve:
                        return Response({
                            'success': False,
                            'message': str(ve)
                        }, status=400)
            is_tpl = bool(getattr(event, 'IsTemplate', False))
            date_err = _validate_event_start_end_dates(
                new_start, new_end,
                mode='update',
                created_at=event.CreatedAt,
                is_template=is_tpl,
            )
            if date_err:
                return Response({
                    'success': False,
                    'message': date_err
                }, status=400)
            event.StartDate = new_start
            event.EndDate = new_end
        
        event.UpdatedAt = timezone.now()
        event.save()
        
        # Return the updated event data
        event_data = {
            'id': event.EventId,
            'title': event.EventTitle,
            'description': event.Description,
            'framework': event.FrameworkName,
            'module': event.Module,
            'category': event.Category,
            'recurrence_type': event.RecurrenceType,
            'frequency': event.Frequency,
            'owner': event.owner_name if hasattr(event, 'owner_name') else '',
            'reviewer': event.reviewer_name if hasattr(event, 'reviewer_name') else '',
            'status': event.Status,
            'priority': event.Priority,
            'start_date': event.StartDate.isoformat() if event.StartDate else None,
            'end_date': event.EndDate.isoformat() if event.EndDate else None,
            'updated_at': event.UpdatedAt
        }
        
        return Response({
            'success': True,
            'message': 'Event updated successfully',
            'event_id': event.EventId,
            'event': event_data
        })
        
    except Exception as e:
        _log_exception(e, context='update_event')
        return Response({
            'success': False,
            'message': 'Error updating event. Please try again later.'
        }, status=500)


def _run_event_archive_notifications_worker(tenant_id, event_pk, user_id_int, old_status):
    """
    Send archive notifications outside the request thread so POST /archive/ returns quickly.
    Multi-channel / email work was routinely adding many seconds to the HTTP response.
    """
    close_old_connections()
    try:
        try:
            event = Event.objects.select_related('Owner', 'Reviewer', 'CreatedBy').get(
                EventId=event_pk, tenant_id=tenant_id
            )
        except Event.DoesNotExist:
            return

        try:
            from ...routes.Global.notification_service import NotificationService
            from ...routes.Global.notifications import (
                send_event_aware_multi_channel,
                append_event_notification_in_app,
            )
            notification_service = NotificationService()
            import uuid
            from datetime import datetime as dt

            actor = Users.objects.filter(tenant_id=tenant_id, UserId=user_id_int).first()
            actor_name = actor.UserName if actor else 'System'
            status_dedup = str(event.Status or 'Archived')

            recipients = []
            if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                recipients.append({
                    'email': event.Owner.Email,
                    'name': event.Owner.UserName or event.Owner.Email.split('@')[0],
                    'user_id': event.Owner.UserId,
                })
            if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                recipients.append({
                    'email': event.Reviewer.Email,
                    'name': event.Reviewer.UserName or event.Reviewer.Email.split('@')[0],
                    'user_id': event.Reviewer.UserId,
                })
            if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                recipients.append({
                    'email': event.CreatedBy.Email,
                    'name': event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0],
                    'user_id': event.CreatedBy.UserId,
                })

            for recipient in recipients:
                try:
                    notification_data = {
                        'notification_type': 'eventStatusChanged',
                        'email': recipient['email'],
                        'email_type': 'gmail',
                        'template_data': [
                            recipient['name'],
                            event.EventTitle,
                            old_status,
                            event.Status,
                            actor_name,
                        ],
                    }
                    send_event_aware_multi_channel(
                        notification_service,
                        notification_data,
                        event.EventId,
                        recipient_user_id=recipient['user_id'],
                        dedup_extra=status_dedup,
                    )
                    notification = {
                        'id': str(uuid.uuid4()),
                        'title': 'Event Status Updated',
                        'message': f'Event "{event.EventTitle}" was archived (status: {old_status} → {event.Status}).',
                        'category': 'event',
                        'priority': 'medium',
                        'createdAt': dt.now().isoformat(),
                        'status': {'isRead': False, 'readAt': None},
                        'user_id': str(recipient['user_id']),
                    }
                    append_event_notification_in_app(
                        notification, event.EventId, 'eventStatusChanged', dedup_extra=status_dedup
                    )
                except Exception as notify_error:
                    _log_exception(notify_error, context='archive_event.notify')
        except Exception as notify_ex:
            _log_exception(notify_ex, context='archive_event.notify_service')
    finally:
        close_old_connections()


def _schedule_event_archive_notifications(tenant_id, event_pk, user_id_int, old_status):
    t = threading.Thread(
        target=_run_event_archive_notifications_worker,
        args=(tenant_id, event_pk, user_id_int, old_status),
        daemon=True,
        name=f'event-archive-notify-{event_pk}',
    )
    t.start()


@api_view(['POST'])
@permission_classes([EventArchivePermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def archive_event(request, event_id):
    """Archive an event - accepts either integer EventId or string EventId_Generated (e.g., EVT-2026-4226)"""
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        try:
            event = _get_event_for_tenant(tenant_id, event_id, allow_generated_slug=True)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return Response(payload, status=code)
        
        debug_print(f"DEBUG: Event {event_id} - CreatedBy: {event.CreatedBy}, Reviewer: {event.Reviewer}, User: {user_id_int}")
        
        old_status = event.Status
        # Archive the event
        event.Status = 'Archived'
        event.UpdatedAt = timezone.now()
        event.save()

        # Notifications (email / multi-channel) can take many seconds — do not block the HTTP response.
        _schedule_event_archive_notifications(tenant_id, event.EventId, user_id_int, old_status)

        return Response({
            'success': True,
            'message': 'Event archived successfully',
            'event_id': event.EventId,
            'new_status': event.Status,
        })
        
    except Exception as e:
        _log_exception(e, context='archive_event')
        return Response({
            'success': False,
            'message': 'Error archiving event. Please try again later.'
        }, status=500)


@api_view(['GET'])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_archived_events(request):
    """Get all archived events (excluding integration and Riskavaire events)"""
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get archived events that are NOT from integrations or Riskavaire
        archived_events_query = Event.objects.filter(tenant_id=tenant_id, 
            Status='Archived'
        ).exclude(
            models.Q(FrameworkName__icontains='Integration') | 
            models.Q(FrameworkName__icontains='Jira') |
            models.Q(FrameworkName__icontains='Riskavaire') |
            models.Q(LinkedRecordType__icontains='Jira') |
            models.Q(LinkedRecordType__icontains='Integration') |
            models.Q(LinkedRecordType__icontains='Riskavaire')
        )
        archived_events_query = _apply_event_list_scope(archived_events_query, user_id_int)
        
        # Apply framework filtering
        from ..Policy.framework_filter_helper import apply_framework_filter, get_framework_filter_info
        filter_info = get_framework_filter_info(request)
        debug_print(f"🔍 DEBUG: Framework filter info for get_archived_events: {filter_info}")
        archived_events_query = apply_framework_filter(archived_events_query, request, 'FrameworkId')
        
        archived_events = archived_events_query.order_by('-UpdatedAt')
        
        events_data = []
        for event in archived_events:
            # Get owner name
            owner_name = 'Unknown'
            if event.Owner:
                try:
                    owner_name = event.Owner.username or f"User {event.Owner.UserId}"
                except:
                    owner_name = f"User {event.Owner.UserId}"
            elif event.CreatedBy:
                try:
                    owner = Users.objects.get(UserId=event.CreatedBy.UserId, tenant_id=tenant_id)
                    owner_name = owner.username or f"User {event.CreatedBy.UserId}"
                except (Users.DoesNotExist, AttributeError):
                    owner_name = f"User {event.CreatedBy.UserId if hasattr(event.CreatedBy, 'UserId') else 'Unknown'}"
            
            # Get reviewer name
            reviewer_name = 'N/A'
            if event.Reviewer:
                try:
                    reviewer_name = event.Reviewer.username or f"User {event.Reviewer.UserId}"
                except:
                    reviewer_name = f"User {event.Reviewer.UserId}"
            
            events_data.append({
                'id': event.EventId,
                'title': event.EventTitle or 'Untitled Event',
                'description': event.Description or '',
                'framework': event.FrameworkName or 'N/A',
                'category': event.Category or 'N/A',
                'owner': owner_name,
                'reviewer': reviewer_name,
                'status': event.Status,
                'priority': event.Priority or 'Medium',
                'dateCreated': event.CreatedAt.strftime('%m/%d/%Y') if event.CreatedAt else 'N/A',
                'dateUpdated': event.UpdatedAt.strftime('%m/%d/%Y') if event.UpdatedAt else 'N/A',
                'linkedRecordType': event.LinkedRecordType or 'N/A',
                'linkedRecordId': event.LinkedRecordId or 'N/A',
                'linkedRecordName': event.LinkedRecordName or 'N/A'
            })
        
        return Response({
            'success': True,
            'events': events_data,
            'count': len(events_data)
        })
        
    except Exception as e:
        _log_exception(e, context='get_archived_events')
        return Response({
            'success': False,
            'message': 'Error fetching archived events. Please try again later.'
        }, status=500)


@api_view(['GET'])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_archived_queue_items(request):
    """Get archived queue items (integration and Riskavaire events)"""
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get archived events that are from integrations or Riskavaire
        archived_queue_items = Event.objects.filter(tenant_id=tenant_id, 
            Status='Archived'
        ).filter(
            models.Q(FrameworkName__icontains='Integration') | 
            models.Q(FrameworkName__icontains='Jira') |
            models.Q(FrameworkName__icontains='Riskavaire') |
            models.Q(LinkedRecordType__icontains='Jira') |
            models.Q(LinkedRecordType__icontains='Integration') |
            models.Q(LinkedRecordType__icontains='Riskavaire')
        )
        archived_queue_items = _apply_event_list_scope(archived_queue_items, user_id_int).order_by('-UpdatedAt')
        
        queue_items_data = []
        for event in archived_queue_items:
            # Determine source system
            source_system = 'Unknown'
            if event.FrameworkName and 'Jira' in event.FrameworkName:
                source_system = 'Jira Integration'
            elif event.FrameworkName and 'Riskavaire' in event.FrameworkName:
                source_system = 'Riskavaire'
            elif event.LinkedRecordType and 'Jira' in event.LinkedRecordType:
                source_system = 'Jira Integration'
            elif event.LinkedRecordType and 'Riskavaire' in event.LinkedRecordType:
                source_system = 'Riskavaire'
            elif event.FrameworkName and 'Integration' in event.FrameworkName:
                source_system = 'External Integration'
            
            # Determine suggested type based on category and content
            suggested_type = event.Category or 'General'
            if event.EventTitle:
                title_lower = event.EventTitle.lower()
                if any(keyword in title_lower for keyword in ['security', 'vulnerability', 'breach']):
                    suggested_type = 'Security Event'
                elif any(keyword in title_lower for keyword in ['compliance', 'audit', 'policy']):
                    suggested_type = 'Compliance Event'
                elif any(keyword in title_lower for keyword in ['risk', 'threat', 'exposure']):
                    suggested_type = 'Risk Event'
                elif any(keyword in title_lower for keyword in ['incident', 'bug', 'issue']):
                    suggested_type = 'Incident Event'
            
            queue_items_data.append({
                'id': event.EventId,
                'sourceSystem': source_system,
                'rawTitle': event.EventTitle or 'Untitled Event',
                'suggestedType': suggested_type,
                'timestamp': event.UpdatedAt.strftime('%m/%d/%Y %H:%M') if event.UpdatedAt else 'N/A',
                'linkedRecordId': event.LinkedRecordId or 'N/A',
                'linkedRecordName': event.LinkedRecordName or 'N/A',
                'framework': event.FrameworkName or 'N/A',
                'category': event.Category or 'N/A',
                'priority': event.Priority or 'Medium',
                'description': event.Description or '',
                'dateCreated': event.CreatedAt.strftime('%m/%d/%Y') if event.CreatedAt else 'N/A'
            })
        
        return Response({
            'success': True,
            'queueItems': queue_items_data,
            'count': len(queue_items_data)
        })
        
    except Exception as e:
        _log_exception(e, context='get_archived_queue_items')
        return Response({
            'success': False,
            'message': 'Error fetching archived queue items. Please try again later.'
        }, status=500)


@api_view(['POST'])
@permission_classes([EventArchivePermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def unarchive_event(request, event_id):
    """Unarchive an event (change status from Archived to Pending Review) - accepts either integer EventId or string EventId_Generated"""
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        try:
            event = _get_event_for_tenant(tenant_id, event_id, allow_generated_slug=True)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return Response(payload, status=code)
        
        # Check if event is archived
        if event.Status != 'Archived':
            return Response({
                'success': False,
                'message': 'Event is not archived'
            }, status=400)
        
        old_status = event.Status
        # Update event status to Pending Review
        event.Status = 'Pending Review'
        event.UpdatedAt = timezone.now()
        event.save()

        try:
            from ...routes.Global.notification_service import NotificationService
            from ...routes.Global.notifications import (
                send_event_aware_multi_channel,
                append_event_notification_in_app,
            )
            notification_service = NotificationService()
            import uuid
            from datetime import datetime as dt

            actor = Users.objects.filter(tenant_id=tenant_id, UserId=user_id_int).first()
            actor_name = actor.UserName if actor else 'System'
            status_dedup = str(event.Status or 'Pending Review')

            recipients = []
            if event.Owner and hasattr(event.Owner, 'Email') and event.Owner.Email:
                recipients.append({
                    'email': event.Owner.Email,
                    'name': event.Owner.UserName or event.Owner.Email.split('@')[0],
                    'user_id': event.Owner.UserId,
                })
            if event.Reviewer and hasattr(event.Reviewer, 'Email') and event.Reviewer.Email:
                recipients.append({
                    'email': event.Reviewer.Email,
                    'name': event.Reviewer.UserName or event.Reviewer.Email.split('@')[0],
                    'user_id': event.Reviewer.UserId,
                })
            if event.CreatedBy and hasattr(event.CreatedBy, 'Email') and event.CreatedBy.Email:
                recipients.append({
                    'email': event.CreatedBy.Email,
                    'name': event.CreatedBy.UserName or event.CreatedBy.Email.split('@')[0],
                    'user_id': event.CreatedBy.UserId,
                })

            for recipient in recipients:
                try:
                    notification_data = {
                        'notification_type': 'eventStatusChanged',
                        'email': recipient['email'],
                        'email_type': 'gmail',
                        'template_data': [
                            recipient['name'],
                            event.EventTitle,
                            old_status,
                            event.Status,
                            actor_name,
                        ],
                    }
                    send_event_aware_multi_channel(
                        notification_service,
                        notification_data,
                        event.EventId,
                        recipient_user_id=recipient['user_id'],
                        dedup_extra=status_dedup,
                    )
                    notification = {
                        'id': str(uuid.uuid4()),
                        'title': 'Event Status Updated',
                        'message': f'Event "{event.EventTitle}" was unarchived (status: {old_status} → {event.Status}).',
                        'category': 'event',
                        'priority': 'medium',
                        'createdAt': dt.now().isoformat(),
                        'status': {'isRead': False, 'readAt': None},
                        'user_id': str(recipient['user_id']),
                    }
                    append_event_notification_in_app(
                        notification, event.EventId, 'eventStatusChanged', dedup_extra=status_dedup
                    )
                except Exception as notify_error:
                    _log_exception(notify_error, context='unarchive_event.notify')
        except Exception as notify_ex:
            _log_exception(notify_ex, context='unarchive_event.notify_service')
        
        return Response({
            'success': True,
            'message': 'Event unarchived successfully',
            'event_id': event.EventId,
            'new_status': event.Status
        })
        
    except Exception as e:
        _log_exception(e, context='unarchive_event')
        return Response({
            'success': False,
            'message': 'Error unarchiving event. Please try again later.'
        }, status=500)


@api_view(['POST'])
@permission_classes([EventArchivePermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def delete_event_permanently(request, event_id):
    """Permanently delete an event from the database"""
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)

        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id, tenant_id=tenant_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return Response(payload, status=code)
        
        # Check if event is archived
        if event.Status != 'Archived':
            return Response({
                'success': False,
                'message': 'Only archived events can be permanently deleted'
            }, status=400)
        
        # Store event details for logging before deletion
        event_title = event.EventTitle
        event_id_generated = event.EventId_Generated
        
        # Delete the event
        event.delete()
        
        return Response({
            'success': True,
            'message': 'Event permanently deleted',
            'deleted_event_title': event_title,
            'deleted_event_id': event_id_generated
        })
        
    except Exception as e:
        _log_exception(e, context='delete_event_permanently')
        return Response({
            'success': False,
            'message': 'Error deleting event. Please try again later.'
        }, status=500)


@api_view(['POST'])
@permission_classes([EventEditPermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def attach_evidence(request, event_id):
    """Attach evidence to an event"""
    try:
        tenant_id = get_tenant_id_from_request(request)
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get the event
        try:
            event = Event.objects.get(EventId=event_id, tenant_id=tenant_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return Response(payload, status=code)
        
        debug_print(f"DEBUG: Event {event_id} - CreatedBy: {event.CreatedBy}, Reviewer: {event.Reviewer}, User: {user_id_int}")
        
        # Handle file upload (same size/type policy as upload_event_evidence)
        if 'file' in request.FILES:
            import os
            file = request.FILES['file']
            if file.size > _EVENT_EVIDENCE_MAX_BYTES:
                return Response({
                    'success': False,
                    'message': 'File size exceeds 10MB limit'
                }, status=400)
            ct = file.content_type or ''
            if ct not in _EVENT_EVIDENCE_ALLOWED_CONTENT_TYPES:
                return Response({
                    'success': False,
                    'message': 'File type not supported. Allowed types: PDF, CSV, XLSX, DOC, TXT'
                }, status=400)
            safe_name = os.path.basename((file.name or 'upload').replace('\\', '/'))
            safe_name = ''.join(c for c in safe_name if ord(c) >= 32 and ord(c) != 127)[:255] or 'upload'
            evidence_info = f"\n\nEvidence attached: {safe_name} (uploaded by user {user_id_int})"
            event.Description = (event.Description or '') + evidence_info
            event.UpdatedAt = timezone.now()
            event.save()
            
            return Response({
                'success': True,
                'message': 'Evidence attached successfully',
                'event_id': event.EventId,
                'filename': safe_name
            })
        else:
            return Response({
                'success': False,
                'message': 'No file provided'
            }, status=400)
        
    except Exception as e:
        _log_exception(e, context='attach_evidence')
        return Response({
            'success': False,
            'message': 'Error attaching evidence. Please try again later.'
        }, status=500)


@api_view(['GET'])
@permission_classes([EventEditPermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def test_integration_db_connection(request):
    """
    Test connection to the integration database and create it if it doesn't exist
    """
    if not _event_schema_maintenance_allowed():
        return Response({'success': False, 'message': 'Not found.'}, status=404)
    try:
        import mysql.connector
        from django.conf import settings
        
        # Use the same credentials as the main GRC database
        main_db_config = settings.DATABASES['default']
        
        # First, try to connect to MySQL server without specifying database
        server_config = {
            'host': main_db_config['HOST'],
            'user': main_db_config['USER'],
            'password': main_db_config['PASSWORD'],
            'port': int(main_db_config['PORT'])
        }
        
        # Connect to MySQL server
        connection = mysql.connector.connect(**server_config)
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS grc_integrations")
        cursor.execute("USE grc_integrations")
        
        # Create jira_issues table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jira_issues (
                id INT AUTO_INCREMENT PRIMARY KEY,
                issue_key VARCHAR(50) NOT NULL,
                summary TEXT,
                description TEXT,
                status VARCHAR(50),
                priority VARCHAR(50),
                assignee VARCHAR(100),
                reporter VARCHAR(100),
                issue_type VARCHAR(50),
                project_key VARCHAR(50),
                project_name VARCHAR(100),
                created_date TIMESTAMP NULL,
                updated_date TIMESTAMP NULL,
                resolution VARCHAR(100),
                labels TEXT,
                components TEXT,
                custom_fields JSON,
                raw_data JSON,
                is_archived BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        cursor.close()
        connection.close()
        
        return Response({
            'success': True,
            'message': 'Integration database and tables created successfully'
        })
        
    except Exception as e:
        _log_exception(e, context='test_integration_db_connection')
        return Response({
            'success': False,
            'message': 'Error setting up integration database. Please try again later.'
        }, status=500)


@api_view(['GET'])
@permission_classes([EventQueuePermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_integration_events(request):
    """
    Get events from external integrations using integration_data_list table
    """
    try:
        from ...models import IntegrationDataList
        from django.db import connection
        
        # Initialize integration_records
        integration_records = []
        
        # Fetch integration data from the grc.integration_data_list table
        # IMPORTANT: Use Django ORM to get automatic decryption of encrypted fields
        # IntegrationDataList uses EncryptedFieldsMixin, so fields like heading, source, 
        # username, data, and metadata are encrypted and need decryption
        try:
            # Use Django ORM - this automatically decrypts encrypted fields via EncryptedFieldsMixin
            integration_records = IntegrationDataList.objects.only(
                'id', 'heading', 'source', 'username', 'time', 'data', 'metadata', 'created_at', 'updated_at'
            ).order_by('-id')[:100]
            
            debug_print(f"DEBUG: Django ORM query succeeded, got {len(integration_records)} records (decrypted)")
            
            # Verify decryption is working
            if integration_records:
                first_record = integration_records[0]
                debug_print(f"DEBUG: Sample record ID {first_record.id}:")
                debug_print(f"  - Heading: {first_record.heading[:50] if first_record.heading else 'None'}...")
                debug_print(f"  - Source: {first_record.source}")
                debug_print(f"  - Data type: {type(first_record.data)}")
                debug_print(f"  - Is encrypted (heading): {isinstance(first_record.heading, str) and first_record.heading.startswith('gAAAAA') if first_record.heading else False}")
                    
        except Exception as query_error:
            _log_exception(query_error, context='get_integration_events.orm')
            
            # Fallback: retry with indexed ordering to avoid DB filesort pressure
            try:
                integration_records = IntegrationDataList.objects.only(
                    'id', 'heading', 'source', 'username', 'time', 'data', 'metadata', 'created_at', 'updated_at'
                ).order_by('-id')[:100]
                debug_print(f"DEBUG: Fallback query (id ordering) succeeded, got {len(integration_records)} records")
            except Exception as fallback_error:
                _log_exception(fallback_error, context='get_integration_events.fallback')
                return Response({
                    'success': False,
                    'message': 'Failed to fetch integration data. Please try again later.',
                    'events': []
                }, status=500)
        
        # Check if we have any records
        if not integration_records:
            debug_print("DEBUG: No integration records found")
            return Response({
                'success': True,
                'events': [],
                'count': 0,
                'message': 'No integration events found'
            })
        
        debug_print(f"DEBUG: Processing {len(integration_records)} integration records")
        
        # Debug: Print source values
        for i, record in enumerate(integration_records[:5]):  # Print first 5 records
            debug_print(f"DEBUG: Record {i+1} - Source: {getattr(record, 'source', 'N/A')}")
        
        # Debug: Count Microsoft Sentinel records
        sentinel_count = sum(1 for record in integration_records if getattr(record, 'source', '') == 'Microsoft Sentinel')
        debug_print(f"DEBUG: Microsoft Sentinel records found: {sentinel_count}")
        
        # Transform integration records to match the events queue format
        integration_events = []
        from grc.utils.data_encryption import decrypt_data, is_encrypted_data
        import json
        
        for record in integration_records:
            # CRITICAL: Manually decrypt ALL encrypted fields
            # EncryptedFieldsMixin doesn't automatically decrypt when using .only() or raw access
            # So we need to explicitly decrypt heading, source, username, data, and metadata
            
            # Decrypt heading
            heading = record.heading or ''
            if heading and isinstance(heading, str) and is_encrypted_data(heading):
                try:
                    heading = decrypt_data(heading)
                    debug_print(f"DEBUG: Decrypted heading for record {record.id}")
                except Exception as e:
                    _log_exception(e, context=f'get_integration_events.decrypt_heading.{record.id}')
            
            # Decrypt source
            source = record.source or ''
            if source and isinstance(source, str) and is_encrypted_data(source):
                try:
                    source = decrypt_data(source)
                    debug_print(f"DEBUG: Decrypted source for record {record.id}: {source}")
                except Exception as e:
                    _log_exception(e, context=f'get_integration_events.decrypt_source.{record.id}')
            
            # Decrypt username
            username = record.username or ''
            if username and isinstance(username, str) and is_encrypted_data(username):
                try:
                    username = decrypt_data(username)
                    debug_print(f"DEBUG: Decrypted username for record {record.id}")
                except Exception as e:
                    _log_exception(e, context=f'get_integration_events.decrypt_username.{record.id}')
            
            # Decrypt and parse data JSONField
            data = record.data or {}
            if isinstance(data, str):
                try:
                    # Check if encrypted
                    if is_encrypted_data(data):
                        decrypted_data_str = decrypt_data(data)
                        data = json.loads(decrypted_data_str) if isinstance(decrypted_data_str, str) else decrypted_data_str
                        debug_print(f"DEBUG: Decrypted and parsed data for record {record.id}")
                    else:
                        # Not encrypted, just parse JSON
                        data = json.loads(data)
                except (json.JSONDecodeError, Exception) as e:
                    _log_exception(e, context=f'get_integration_events.parse_data.{record.id}')
                    data = {}
            elif not isinstance(data, dict):
                # If it's not a dict or string, make it empty dict
                data = {}
            
            # Decrypt and parse metadata JSONField
            metadata = record.metadata or {}
            if isinstance(metadata, str):
                try:
                    # Check if encrypted
                    if is_encrypted_data(metadata):
                        decrypted_meta_str = decrypt_data(metadata)
                        metadata = json.loads(decrypted_meta_str) if isinstance(decrypted_meta_str, str) else decrypted_meta_str
                        debug_print(f"DEBUG: Decrypted and parsed metadata for record {record.id}")
                    else:
                        # Not encrypted, just parse JSON
                        metadata = json.loads(metadata)
                except (json.JSONDecodeError, Exception) as e:
                    _log_exception(e, context=f'get_integration_events.parse_metadata.{record.id}')
                    metadata = {}
            elif not isinstance(metadata, dict):
                # If it's not a dict or string, make it empty dict
                metadata = {}
            
            # Debug logging for integration records (use decrypted values)
            if record.id in [1, 2, 14, 52]:  # Added 52 for the encrypted record
                debug_print(f"DEBUG: Record ID {record.id} - Source (decrypted): {source}")
                debug_print(f"DEBUG: Record ID {record.id} - Heading (decrypted): {heading[:50] if heading else 'None'}...")
                debug_print(f"DEBUG: Record ID {record.id} - Username (decrypted): {username}")
                debug_print(f"DEBUG: Record ID {record.id} - Data keys: {list(data.keys()) if data else 'None'}")
                debug_print(f"DEBUG: Record ID {record.id} - Metadata: {metadata}")
                debug_print(f"DEBUG: Record ID {record.id} - Metadata type: {type(metadata)}")
                debug_print(f"DEBUG: Record ID {record.id} - Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
            
            # Determine event type based on content
            event_type = determine_event_type_from_integration_data(record, data, metadata)
            
            # Handle different data structures based on source
            # Use decrypted source value
            source = source or 'Integration'
            
            # Microsoft Sentinel has different data structure
            if source == 'Microsoft Sentinel':
                summary = data.get('title') or data.get('displayName') or heading
                description = data.get('description', '')
                status = data.get('status', 'New')
                priority = metadata.get('severity', 'Medium') if metadata else 'Medium'
                assignee = data.get('owner', 'Unassigned')
                reporter = username or 'Unknown'
                issue_type = 'Security Incident'
                project_key = data.get('incidentNumber') or data.get('id', '')
                project_name = 'Microsoft Sentinel'
                
                debug_print(f"[SENTINEL] Transforming Microsoft Sentinel record {record.id}")
                debug_print(f"[SENTINEL]   - Title: {summary}")
                debug_print(f"[SENTINEL]   - Status: {status}")
                debug_print(f"[SENTINEL]   - Priority: {priority}")
                debug_print(f"[SENTINEL]   - Project Key: {project_key}")
            else:
                # Default Jira/Gmail format
                summary = data.get('summary', heading)
                description = data.get('description', '')
                status = data.get('status', 'New')
                priority = data.get('priority', 'Medium')
                assignee = data.get('assignee', 'Unassigned')
                reporter = data.get('reporter', username or 'Unknown')
                issue_type = data.get('issue_type', 'Task')
                project_key = data.get('project_key', '')
                project_name = data.get('project_name', 'Integration Project')
            # Handle time fields safely
            try:
                created_date = data.get('created_date', record.time.isoformat() if hasattr(record, 'time') and record.time else '')
            except (AttributeError, TypeError):
                created_date = data.get('created_date', '')
                
            try:
                updated_date = data.get('updated_date', record.updated_at.isoformat() if hasattr(record, 'updated_at') and record.updated_at else '')
            except (AttributeError, TypeError):
                updated_date = data.get('updated_date', '')
            resolution = data.get('resolution', '')
            labels = data.get('labels', [])
            components = data.get('components', [])
            custom_fields = data.get('custom_fields', {})
            
            event_obj = {
                'id': f"integration_{record.id}",
                'title': summary,
                'framework': 'Integration',  # Default framework
                'module': determine_module_from_integration_data(record, data, metadata),
                'category': determine_category_from_integration_data(record, data, metadata),
                'source': source or 'Integration',
                'timestamp': record.time.strftime('%m/%d/%Y %H:%M') if hasattr(record, 'time') and record.time else 'N/A',
                'status': status,
                'linkedRecordType': 'Integration Event',
                'linkedRecordId': data.get('issue_key', f"INT-{record.id}"),
                'linkedRecordName': summary,
                'priority': priority,
                'description': description,
                'owner': assignee,
                'reviewer': 'Not Assigned',
                'evidence': [],
                'metadata': metadata,  # Include metadata field
                'rawData': {
                    'issue_key': data.get('issue_key', f"INT-{record.id}"),
                    'summary': summary,
                    'status': status,
                    'assignee': assignee,
                    'priority': priority,
                    'created': record.time.isoformat() if hasattr(record, 'time') and record.time else None,
                    'updated': record.updated_at.isoformat() if hasattr(record, 'updated_at') and record.updated_at else None,
                    'description': description,
                    'project': project_name,
                    'issue_type': issue_type,
                    'labels': labels,
                    'components': components,
                    'custom_fields': custom_fields,
                    'raw_data': data
                }
            }
            
            # Debug logging for specific events
            if record.id in [1, 2, 14]:  # Added 14 for Microsoft Sentinel record
                debug_print(f"DEBUG: Event object for record {record.id}:")
                debug_print(f"  - ID: {event_obj['id']}")
                debug_print(f"  - Title: {event_obj['title']}")
                debug_print(f"  - Source: {event_obj['source']}")
                debug_print(f"  - Priority: {event_obj['priority']}")
                debug_print(f"  - Status: {event_obj['status']}")
                debug_print(f"  - Metadata: {event_obj['metadata']}")
                debug_print(f"  - Metadata type: {type(event_obj['metadata'])}")
            
            integration_events.append(event_obj)
        
        # Debug: Count Microsoft Sentinel events in final response
        sentinel_events_count = sum(1 for event in integration_events if event.get('source') == 'Microsoft Sentinel')
        debug_print(f"DEBUG: Microsoft Sentinel events in final response: {sentinel_events_count}")
        
        # Log details of each Sentinel event
        for event in integration_events:
            if event.get('source') == 'Microsoft Sentinel':
                debug_print(f"[SENTINEL] Returning event: ID={event.get('id')}, Title={event.get('title')}, Source={event.get('source')}")
        
        debug_print(f"[FINAL] Returning {len(integration_events)} total integration events")
        
        return Response({
            'success': True,
            'events': integration_events,
            'count': len(integration_events)
        })
        
    except Exception as e:
        _log_exception(e, context='get_integration_events')
        return Response({
            'success': False,
            'message': 'Error fetching integration events. Please try again later.'
        }, status=500)


def determine_event_type_from_integration_data(record, data, metadata):
    """Determine the type of event based on integration data content"""
    summary = (data.get('summary', record.heading) or '').lower()
    description = (data.get('description', '') or '').lower()
    status = (data.get('status', '') or '').lower()
    issue_type = (data.get('issue_type', '') or '').lower()
    source = (record.source or '').lower()
    
    # Security-related issues
    if any(keyword in summary or keyword in description for keyword in 
           ['security', 'vulnerability', 'breach', 'incident', 'threat']):
        return 'Security Event'
    
    # Compliance-related issues
    if any(keyword in summary or keyword in description for keyword in 
           ['compliance', 'audit', 'policy', 'regulation', 'standard']):
        return 'Compliance Event'
    
    # Risk-related issues
    if any(keyword in summary or keyword in description for keyword in 
           ['risk', 'threat', 'exposure', 'mitigation']):
        return 'Risk Event'
    
    # Bug/Incident issues
    if issue_type in ['bug', 'incident'] or status in ['done', 'resolved']:
        return 'Incident Event'
    
    # Default to general event
    return 'General Event'


def determine_module_from_integration_data(record, data, metadata):
    """Determine the module based on integration data"""
    from ...models import Module
    
    summary = (data.get('summary', record.heading) or '').lower()
    description = (data.get('description', '') or '').lower()
    source = (record.source or '').lower()
    
    # Get all modules from database
    try:
        all_modules = Module.objects.all().values_list('modulename', flat=True)
        module_names = [name.lower() for name in all_modules]
    except Exception as e:
        _log_exception(e, context='get_users_for_reviewer.modules')
        # Fallback to hardcoded modules if database fails
        module_names = ['policy management', 'compliance management', 'audit management', 'incident management', 'risk management']

    from ...utils.bulk_limits import MAX_INTEGRATION_MODULE_NAMES_CHECK

    module_names = module_names[:MAX_INTEGRATION_MODULE_NAMES_CHECK]

    # Check content against database modules
    for module_name in module_names:
        module_keywords = module_name.split()
        if any(keyword in summary or keyword in description for keyword in module_keywords):
            # Find the exact module name from database
            try:
                exact_module = Module.objects.filter(modulename__icontains=module_name).first()
                if exact_module:
                    return exact_module.modulename
            except:
                pass
    
    # Default based on source
    if source == 'jira':
        return 'Integration Management'
    elif 'security' in summary:
        return 'Security Management'
    elif 'compliance' in summary:
        return 'Compliance Management'
    elif 'audit' in summary:
        return 'Audit Management'
    else:
        return 'General Integration'


def determine_category_from_integration_data(record, data, metadata):
    """Determine the category based on integration data"""
    summary = (data.get('summary', record.heading) or '').lower()
    description = (data.get('description', '') or '').lower()
    issue_type = (data.get('issue_type', '') or '').lower()
    priority = (data.get('priority', '') or '').lower()
    source = (record.source or '').lower()
    
    # High priority issues
    if priority in ['critical', 'high']:
        return 'Critical'
    
    # Bug/Incident issues
    if issue_type in ['bug', 'incident']:
        return 'Incident'
    
    # Security issues
    if any(keyword in summary or keyword in description for keyword in 
           ['security', 'vulnerability', 'breach']):
        return 'Security'
    
    # Compliance issues
    if any(keyword in summary or keyword in description for keyword in 
           ['compliance', 'audit', 'policy']):
        return 'Compliance'
    
    # Risk issues
    if any(keyword in summary or keyword in description for keyword in 
           ['risk', 'threat', 'exposure']):
        return 'Risk'
    
    # Default based on source
    if source.lower() == 'jira':
        return issue_type.title() if issue_type else 'Integration Item'
    else:
        return 'Integration Event'


@api_view(['POST'])
@permission_classes([EventCreatePermission])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def create_event_from_integration(request):
    """
    Create an event from an integration item (Jira issue, etc.)
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        data = request.data
        user_id = _parse_server_user_id_int(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        integration_item_id = data.get('integration_item_id')
        integration_type = data.get('integration_type', 'jira')
        
        if not integration_item_id:
            return Response({
                'success': False,
                'message': 'Integration item ID is required'
            }, status=400)
        
        # Get integration item details
        if integration_type == 'jira':
            import mysql.connector
            from django.conf import settings
            
            # Database configuration for GRC_INTEGRATIONS
            # Use the same credentials as the main GRC database
            main_db_config = settings.DATABASES['default']
            integration_db_config = {
                'host': main_db_config['HOST'],
                'user': main_db_config['USER'],
                'password': main_db_config['PASSWORD'],
                'database': 'grc_integrations',  # Different database name
                'port': int(main_db_config['PORT'])
            }
            
            # Connect to the integration database
            try:
                connection = mysql.connector.connect(**integration_db_config)
                cursor = connection.cursor(dictionary=True)
                
                # Fetch the specific Jira issue
                cursor.execute("""
                    SELECT * FROM jira_issues WHERE id = %s
                """, (integration_item_id,))
                
                jira_issue = cursor.fetchone()
                
                # Check if this is an archive action
                action = request.data.get('action', 'create')
                if action == 'archive':
                    # Mark the Jira issue as archived
                    cursor.execute("""
                        UPDATE jira_issues SET is_archived = TRUE WHERE id = %s
                    """, (integration_item_id,))
                    connection.commit()
                    
                    # Create an archived event record in the main events table
                    from grc.models import Event, Users
                    from django.utils import timezone
                    
                    try:
                        # Get the user
                        user = Users.objects.get(UserId=user_id, tenant_id=tenant_id)
                        
                        # Create event data from Jira issue
                        event_data = {
                            'EventTitle': jira_issue['summary'] or f"Jira Issue: {jira_issue['issue_key']}",
                            'Description': jira_issue['description'] or f"Archived from Jira issue {jira_issue['issue_key']}",
                            'FrameworkId': None,
                            'FrameworkName': 'Jira Integration',
                            'Module': determine_module(jira_issue),
                            'LinkedRecordType': 'Jira Issue',
                            'LinkedRecordId': jira_issue['id'],  # Use numeric ID from Jira issue
                            'LinkedRecordName': jira_issue['issue_key'],  # Store issue key as name
                            'Category': determine_category(jira_issue),
                            'RecurrenceType': 'Non-Recurring',
                            'Frequency': None,
                            'StartDate': None,
                            'EndDate': None,
                            'Status': 'Archived',  # Set status to Archived
                            'Priority': jira_issue['priority'] or 'Medium',
                            'CreatedBy': user,
                            'Owner': None,
                            'Reviewer': None,
                            'IsTemplate': False
                        }
                        if tenant_id is not None:
                            event_data['tenant_id'] = tenant_id
                        
                        # Create the archived event
                        archived_event = Event.objects.create(**event_data)
                        
                        return Response({
                            'success': True,
                            'message': 'Jira issue archived successfully and event created',
                            'action': 'archived',
                            'event_id': archived_event.EventId,
                            'event_id_generated': archived_event.EventId_Generated
                        })
                        
                    except Exception as event_error:
                        debug_print(f"DEBUG: Error creating archived event: {sanitize_for_log(event_error, max_len=800)}")
                        # Still return success for the Jira archive even if event creation fails
                        return Response({
                            'success': True,
                            'message': 'Jira issue archived successfully (event creation failed)',
                            'action': 'archived',
                            'warning': 'Event record could not be created. Please try again later.'
                        })
                
            except mysql.connector.Error as db_error:
                debug_print(f"DEBUG: Integration DB error: {sanitize_for_log(db_error, max_len=800)}")
                return Response({
                    'success': False,
                    'message': 'Failed to connect to integration database. Please try again later.'
                }, status=500)
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if 'connection' in locals():
                    connection.close()
            
            if not jira_issue:
                return Response({
                    'success': False,
                    'message': 'Jira issue not found'
                }, status=404)
            
            # Create event data from Jira issue
            event_data = {
                'EventTitle': jira_issue['summary'] or f"Jira Issue: {jira_issue['issue_key']}",
                'Description': jira_issue['description'] or f"Created from Jira issue {jira_issue['issue_key']}",
                'FrameworkId': None,  # Can be set later
                'FrameworkName': 'Jira Integration',
                'Module': determine_module(jira_issue),
                'LinkedRecordType': 'Jira Issue',
                'LinkedRecordId': jira_issue['issue_key'],
                'LinkedRecordName': jira_issue['issue_key'],
                'Category': determine_category(jira_issue),
                'RecurrenceType': 'Non-Recurring',
                'Frequency': None,
                'StartDate': None,
                'EndDate': None,
                'Status': 'Pending Review',
                'Priority': jira_issue['priority'] or 'Medium',
                'CreatedBy': Users.objects.get(UserId=user_id, tenant_id=tenant_id),
                'Owner': None,  # Can be set later
                'Reviewer': None,  # Can be set later
                'IsTemplate': False
            }
            if tenant_id is not None:
                event_data['tenant_id'] = tenant_id
            
            # Create the event
            event = Event.objects.create(**event_data)
            
            return Response({
                'success': True,
                'message': 'Event created successfully from Jira issue',
                'event_id': event.EventId,
                'event_id_generated': event.EventId_Generated,
                'event': {
                    'EventId': event.EventId,
                    'EventTitle': event.EventTitle,
                    'Status': event.Status,
                    'LinkedRecordId': event.LinkedRecordId,
                    'LinkedRecordName': event.LinkedRecordName
                }
            })
        
        else:
            return Response({
                'success': False,
                'message': f'Integration type {integration_type} not supported'
            }, status=400)
        
    except Exception as e:
        _log_exception(e, context='create_event_from_integration')
        return Response({
            'success': False,
            'message': 'Error creating event from integration. Please try again later.'
        }, status=500)


# S3 Upload Endpoints

@require_http_methods(["POST"])
@csrf_exempt
@require_tenant
@tenant_filter
def s3_upload_file(request):
    """Upload file to S3 via microservice"""
    try:
        debug_print(f"DEBUG: s3_upload_file called with method: {request.method}")
        debug_print(f"DEBUG: Content-Type: {request.content_type}")
        debug_print(f"DEBUG: FILES: {list(request.FILES.keys())}")
        debug_print(f"DEBUG: POST: {list(request.POST.keys())}")
        
        user_id = _get_server_user_id(request)
        debug_print(f"DEBUG: User ID (server): {sanitize_for_log(user_id, max_len=64)}")
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Check if file is provided
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file provided'
            }, status=400)
        
        file = request.FILES['file']
        debug_print(f"DEBUG: File received: {file.name}, size: {file.size}, type: {file.content_type}")
        
        # Get custom file name from multiple sources
        custom_file_name = None
        if hasattr(request, 'POST') and request.POST:
            custom_file_name = request.POST.get('custom_file_name')
        
        if file.size > _EVENT_EVIDENCE_MAX_BYTES:
            return JsonResponse({
                'success': False,
                'message': 'File size exceeds 10MB limit'
            }, status=400)
        
        if (file.content_type or '') not in _EVENT_EVIDENCE_ALLOWED_CONTENT_TYPES:
            return JsonResponse({
                'success': False,
                'message': f'File type {file.content_type} not supported. Allowed types: PDF, CSV, XLSX, DOC, TXT'
            }, status=400)
        
        # Create S3 client
        try:
            s3_client = create_direct_mysql_client()
            debug_print("DEBUG: S3 client created successfully")
        except Exception as e:
            _log_exception(e, context='s3_upload_file.s3_client')
            return JsonResponse({
                'success': False,
                'message': 'Error initializing S3 client. Please try again later.'
            }, status=500)
        
        # Save file temporarily
        import tempfile
        import os
        
        try:
            file_ext = os.path.splitext(file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            debug_print(f"DEBUG: Temporary file created: {temp_file_path}")
            
            # Decompress if needed (client-side compression)
            compression_metadata = None
            temp_file_path, was_compressed, compression_stats = decompress_if_needed(temp_file_path)
            if was_compressed:
                compression_metadata = compression_stats
                # Update file extension after decompression (remove .gz)
                file_ext = os.path.splitext(temp_file_path)[1]
                debug_print(f"📦 Decompressed file: {compression_stats['ratio']}% reduction, saved {compression_stats['bandwidth_saved_kb']} KB")
        except Exception as e:
            _log_exception(e, context='s3_upload_file.temp_file')
            return JsonResponse({
                'success': False,
                'message': 'Error saving file temporarily. Please try again later.'
            }, status=500)
        
        try:
            # Upload to S3
            debug_print(f"DEBUG: Starting S3 upload for user: {user_id}, file: {file.name}")
            result = s3_client.upload(
                file_path=temp_file_path,
                user_id=user_id,
                custom_file_name=custom_file_name or file.name,
                module='Event'
            )
            
            debug_print(f"DEBUG: S3 upload result: {result}")
            
            if result.get('success'):
                file_info = result.get('file_info', {})
                return JsonResponse({
                    'success': True,
                    'message': 'File uploaded successfully',
                    's3_key': file_info.get('s3Key'),
                    's3_url': file_info.get('url'),
                    'stored_name': file_info.get('storedName'),
                    'file_info': file_info
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': _sanitize_reflected_error_detail(
                        result.get('error', 'Upload failed')
                    ),
                }, status=500)
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        _log_exception(e, context='s3_upload_file')
        return JsonResponse({
            'success': False,
            'message': 'Error uploading file. Please try again later.'
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
@require_tenant
@tenant_filter
def s3_download_file(request, s3_key, file_name):
    """Download file from S3 via microservice"""
    try:
        user_id = _get_server_user_id(request)
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # URL decode the parameters
        from urllib.parse import unquote
        decoded_s3_key = unquote(s3_key)
        decoded_file_name = unquote(file_name)

        decoded_s3_key_safe = _sanitize_s3_download_param(decoded_s3_key)
        decoded_file_name_safe = _sanitize_s3_download_param(decoded_file_name, for_filename=True)

        if not decoded_s3_key_safe or not decoded_file_name_safe:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or empty file identifier after sanitization.',
            }, status=400)
        
        debug_print(
            f"DEBUG: Download request - s3_key(safe): {sanitize_for_log(decoded_s3_key_safe, max_len=300)}"
        )
        debug_print(
            f"DEBUG: Download request - file_name(safe): {sanitize_for_log(decoded_file_name_safe, max_len=300)}"
        )
        debug_print(f"DEBUG: Download request - User ID: {sanitize_for_log(user_id, max_len=64)}")
        
        # Create S3 client
        s3_client = create_direct_mysql_client()
        
        # Test connection first
        debug_print(f"DEBUG: Testing S3 connection before download...")
        connection_test = s3_client.test_connection()
        debug_print(f"DEBUG: Connection test result: {connection_test}")
        
        if not connection_test.get('overall_success', False):
            debug_print(
                f"DEBUG: [s3_download_file] S3 unavailable: "
                f"{sanitize_for_log(connection_test, max_len=400)}"
            )
            return JsonResponse({
                'success': False,
                'message': 'S3 service is currently unavailable. Please try again later.',
            }, status=503)
        
        # Download file
        debug_print(f"DEBUG: Starting download with s3_key: {decoded_s3_key_safe}, file_name: {decoded_file_name_safe}")
        result = s3_client.download(
            s3_key=decoded_s3_key_safe,
            file_name=decoded_file_name_safe,
            user_id=user_id
        )
        debug_print(f"DEBUG: Download result: {result}")
        
        if result.get('success'):
            # Return file content
            from django.http import HttpResponse
            response = HttpResponse(
                result.get('file_content'),
                content_type=result.get('content_type', 'application/octet-stream')
            )
            response['Content-Disposition'] = f'attachment; filename="{decoded_file_name_safe}"'
            return response
        else:
            error_message = result.get('error', 'Download failed')
            error_message_safe = _sanitize_reflected_error_detail(error_message)
            debug_print(f"DEBUG: Download failed with error: {sanitize_for_log(error_message_safe, max_len=500)}")
            
            if '404' in str(error_message_safe) or 'Not Found' in str(error_message_safe):
                return JsonResponse({
                    'success': False,
                    'message': 'File not found or no longer available.',
                }, status=404)
            return JsonResponse({
                'success': False,
                'message': 'Download failed. Please try again later.',
            }, status=500)
            
    except Exception as e:
        _log_exception(e, context='s3_download_file')
        return JsonResponse({
            'success': False,
            'message': 'Error downloading file. Please try again later.',
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
@require_tenant
@tenant_filter
def s3_test_connection(request):
    """Test S3 microservice connection"""
    try:
        if not _get_server_user_id(request):
            return JsonResponse({
                'success': False,
                'message': 'Authentication required',
            }, status=401)
        # Create S3 client
        s3_client = create_direct_mysql_client()
        
        # Test connection — do not expose internal diagnostics to the client
        result = s3_client.test_connection()
        ok = bool(isinstance(result, dict) and result.get('overall_success'))
        
        return JsonResponse({
            'success': True,
            'message': 'S3 connection test completed',
            's3_available': ok,
        })
    except Exception as e:
        _log_exception(e, context='s3_test_connection')
        return JsonResponse({
            'success': False,
            'message': 'Error testing S3 connection. Please try again later.'
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
@require_tenant
@tenant_filter
def s3_check_file_exists(request, s3_key, file_name):
    """Check if file exists in S3"""
    try:
        user_id = _get_server_user_id(request)
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # URL decode the parameters
        from urllib.parse import unquote
        decoded_s3_key = unquote(s3_key)
        decoded_file_name = unquote(file_name)

        decoded_s3_key_safe = _sanitize_s3_download_param(decoded_s3_key)
        decoded_file_name_safe = _sanitize_s3_download_param(decoded_file_name, for_filename=True)

        if not decoded_s3_key_safe or not decoded_file_name_safe:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or empty file identifier after sanitization.',
            }, status=400)
        
        debug_print(
            f"DEBUG: Check file exists - s3_key(safe): {sanitize_for_log(decoded_s3_key_safe, max_len=300)}, "
            f"file_name(safe): {sanitize_for_log(decoded_file_name_safe, max_len=300)}"
        )
        
        # Create S3 client
        s3_client = create_direct_mysql_client()
        
        # Test connection first
        connection_test = s3_client.test_connection()
        if not connection_test.get('overall_success', False):
            return JsonResponse({
                'success': False,
                'message': 'S3 service is currently unavailable. Please try again later.',
            }, status=503)
        
        # For now, we'll assume the file exists if the connection is successful
        # In a real implementation, you might want to make a HEAD request to S3
        return JsonResponse({
            'success': True,
            'message': 'File existence check completed',
            'file_exists': True,  # This is a placeholder - implement actual check
            's3_key': decoded_s3_key_safe,
            'file_name': decoded_file_name_safe
        })
        
    except Exception as e:
        _log_exception(e, context='s3_check_file_exists')
        return JsonResponse({
            'success': False,
            'message': 'Error checking file existence. Please try again later.',
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@require_consent('upload_event')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def upload_event_evidence(request, event_id):
    """Upload evidence file for a specific event"""
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        debug_print(f"DEBUG: upload_event_evidence called for event_id: {event_id}")
        debug_print(f"DEBUG: Request method: {request.method}")
        debug_print(f"DEBUG: Content-Type: {request.content_type}")
        debug_print(f"DEBUG: FILES: {list(request.FILES.keys())}")
        debug_print(f"DEBUG: POST: {list(request.POST.keys())}")

        # Resolve user identity from authenticated server context only.
        user_id = _get_server_user_id(request)
        
        debug_print(f"DEBUG: User ID: {user_id}")
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        if tenant_id is None:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        # Check if file is provided
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file provided'
            }, status=400)
        
        file = request.FILES['file']
        debug_print(f"DEBUG: File received: {file.name}, size: {file.size}, type: {file.content_type}")
        
        # Get custom file name from request
        custom_file_name = None
        if hasattr(request, 'POST') and request.POST:
            custom_file_name = request.POST.get('custom_file_name')
        
        if file.size > _EVENT_EVIDENCE_MAX_BYTES:
            return JsonResponse({
                'success': False,
                'message': 'File size exceeds 10MB limit'
            }, status=400)
        
        if (file.content_type or '') not in _EVENT_EVIDENCE_ALLOWED_CONTENT_TYPES:
            return JsonResponse({
                'success': False,
                'message': f'File type {file.content_type} not supported. Allowed types: PDF, CSV, XLSX, DOC, TXT'
            }, status=400)
        
        # Check if event exists (tenant-scoped)
        try:
            event = Event.objects.select_related(
                'Owner', 'Reviewer', 'CreatedBy', 'FrameworkId', 'EventType'
            ).get(EventId=event_id, tenant_id=tenant_id)
            debug_print(f"DEBUG: Found event: {event.EventTitle}")
        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return JsonResponse(payload, status=code)
        
        # Create S3 client
        try:
            s3_client = create_direct_mysql_client()
            debug_print("DEBUG: S3 client created successfully")
        except Exception as e:
            _log_exception(e, context='upload_event_evidence.s3_client')
            return JsonResponse({
                'success': False,
                'message': 'Error initializing S3 client. Please try again later.'
            }, status=500)
        
        # Save file temporarily
        import tempfile
        import os
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            debug_print(f"DEBUG: Temporary file created: {temp_file_path}")
        except Exception as e:
            _log_exception(e, context='upload_event_evidence.temp_file')
            return JsonResponse({
                'success': False,
                'message': 'Error saving file temporarily. Please try again later.'
            }, status=500)
        
        try:
            # Upload to S3
            debug_print(f"DEBUG: Starting S3 upload for user: {user_id}, file: {file.name}")
            result = s3_client.upload(
                file_path=temp_file_path,
                user_id=user_id,
                custom_file_name=custom_file_name or file.name,
                module='Event'
            )
            
            debug_print(f"DEBUG: S3 upload result: {result}")
            
            if result.get('success'):
                # Update event with new evidence file
                file_info = result.get('file_info', {})
                s3_url = file_info.get('url')
                s3_key = file_info.get('s3Key')
                stored_name = file_info.get('storedName')
                try:
                    s3_url = _validate_event_evidence_s3_url(s3_url, field_label='upload.result.url')
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'Uploaded file URL failed security validation.',
                    }, status=500)
                
                debug_print(f"DEBUG: S3 URL from result: {s3_url}")
                debug_print(f"DEBUG: S3 Key from result: {s3_key}")
                debug_print(f"DEBUG: Stored name from result: {stored_name}")
                
                evidence_data = {
                    'file_name': file.name,
                    's3_url': s3_url,
                    's3_key': s3_key,
                    'stored_name': stored_name,
                    'file_size': file.size,
                    'file_type': file.content_type,
                    'uploaded_at': timezone.now().isoformat(),
                    'uploaded_by': user_id
                }
                
                # Get current evidence string
                current_evidence = event.Evidence or ""
                debug_print(f"DEBUG: Current evidence before update: '{current_evidence}'")
                
                # Add new evidence URL to existing evidence string
                if current_evidence:
                    current_evidence += f";{s3_url}"
                else:
                    current_evidence = s3_url
                
                debug_print(f"DEBUG: Final evidence string to save: '{current_evidence}'")
                
                # Update event with evidence string in Evidence CharField
                event.Evidence = current_evidence
                event.UpdatedAt = timezone.now()
                event.save()
                
                debug_print(f"DEBUG: Event {event_id} updated with new evidence file")
                debug_print(f"DEBUG: Event Evidence after save: '{event.Evidence}'")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Evidence file uploaded successfully',
                    's3_key': s3_key,
                    's3_url': s3_url,
                    'stored_name': stored_name,
                    'file_info': evidence_data
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': _sanitize_reflected_error_detail(
                        result.get('error', 'Upload failed')
                    ),
                }, status=500)
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        _log_exception(e, context='upload_event_evidence')
        return JsonResponse({
            'success': False,
            'message': 'Error uploading evidence file. Please try again later.'
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_event_evidence(request, event_id):
    """Get evidence files for a specific event with detailed information"""
    try:
        tenant_id = get_tenant_id_from_request(request)
        if tenant_id is None:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        if not _parse_server_user_id_int(request):
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Check if event exists
        try:
            event = Event.objects.select_related(
                'Owner', 'Reviewer', 'CreatedBy', 'FrameworkId', 'EventType'
            ).get(EventId=event_id, tenant_id=tenant_id)
            debug_print(f"DEBUG: Found event: {event.EventTitle}")
        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return JsonResponse(payload, status=code)
        
        # Get evidence data from CharField
        raw_ev = event.Evidence or ""
        evidence_string = raw_ev if isinstance(raw_ev, str) else ""
        evidence_urls = evidence_string.split(';') if evidence_string else []
        
        # Process evidence URLs to extract filenames and create detailed evidence objects
        evidence_objects = []
        for i, url in enumerate(evidence_urls):
            if url and url.strip():
                # Extract filename from URL
                filename = "Evidence File"
                if url:
                    try:
                        # Extract filename from S3 URL
                        if 'amazonaws.com' in url:
                            # Extract from S3 URL like: https://bucket.s3.region.amazonaws.com/path/filename.ext
                            url_parts = url.split('/')
                            if len(url_parts) > 0:
                                filename = url_parts[-1]
                                # Decode URL encoding
                                filename = filename.replace('%20', ' ').replace('%2E', '.')
                        else:
                            # Extract from other URL formats
                            url_parts = url.split('/')
                            if len(url_parts) > 0:
                                filename = url_parts[-1]
                    except:
                        filename = f"Evidence File {i + 1}"
                
                evidence_objects.append({
                    'id': i + 1,
                    'fileName': filename,
                    'filename': filename,
                    'name': filename,
                    'url': url,
                    's3_url': url,
                    'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                    'uploadDate': event.CreatedAt.strftime('%Y-%m-%d') if event.CreatedAt else 'Unknown',
                    'size': 'Unknown'  # Size would need to be stored separately or fetched from S3
                })
        
        return JsonResponse({
            'success': True,
            'evidence': evidence_objects,
            'evidence_string': evidence_string,
            'count': len(evidence_objects)
        })
        
    except Exception as e:
        _log_exception(e, context='get_event_evidence')
        return JsonResponse({
            'success': False,
            'message': 'Error fetching event evidence. Please try again later.'
        }, status=500)

def resolve_file_operation_evidence(evidence_urls, event):
    """Resolve file operation identifiers to actual S3 URLs and details"""
    evidence_objects = []
    
    for i, url in enumerate(evidence_urls):
        if url and url.strip():
            # Check if this is a file operation identifier
            if url.startswith('#linked-event-file_op_'):
                try:
                    # Extract file operation ID from identifier
                    file_op_id = url.replace('#linked-event-file_op_', '')
                    debug_print(f"DEBUG: Resolving file operation ID: {file_op_id}")
                    
                    # Query file_operations table to get actual S3 URL and details
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT stored_name, s3_url, s3_key, s3_bucket, file_type, original_name, 
                                   content_type, export_format, file_size, created_at
                            FROM grc2.file_operations 
                            WHERE id = %s
                        """, [file_op_id])
                        
                        file_ops = cursor.fetchall()
                        if file_ops:
                            stored_name, s3_url, s3_key, s3_bucket, file_type, original_name, content_type, export_format, file_size, created_at = file_ops[0]
                            
                            debug_print(f"DEBUG: Found file operation - S3 URL: {s3_url}, Original name: {original_name}")
                            
                            # Use original name or stored name as filename
                            filename = original_name or stored_name or f"File Operation {file_op_id}"
                            
                            evidence_objects.append({
                                'id': i + 1,
                                'fileName': filename,
                                'filename': filename,
                                'name': filename,
                                'url': s3_url,
                                's3_url': s3_url,
                                's3_key': s3_key,
                                'file_type': file_type,
                                'file_size': file_size,
                                'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                                'uploadDate': created_at.strftime('%Y-%m-%d') if created_at else 'Unknown',
                                'is_file_operation': True,
                                'file_operation_id': file_op_id
                            })
                        else:
                            debug_print(f"DEBUG: No file operation found for ID: {file_op_id}")
                            # Fallback for missing file operation
                            evidence_objects.append({
                                'id': i + 1,
                                'fileName': f"File Operation {file_op_id}",
                                'filename': f"File Operation {file_op_id}",
                                'name': f"File Operation {file_op_id}",
                                'url': url,
                                's3_url': url,
                                'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                                'uploadDate': event.CreatedAt.strftime('%Y-%m-%d') if event.CreatedAt else 'Unknown',
                                'size': 'Unknown',
                                'is_file_operation': True,
                                'file_operation_id': file_op_id
                            })
                except Exception as e:
                    _log_exception(e, context='get_event_evidence.resolve_file_op')
                    # Fallback for error cases
                    evidence_objects.append({
                        'id': i + 1,
                        'fileName': url,
                        'filename': url,
                        'name': url,
                        'url': url,
                        's3_url': url,
                        'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                        'uploadDate': event.CreatedAt.strftime('%Y-%m-%d') if event.CreatedAt else 'Unknown',
                        'size': 'Unknown'
                    })
            else:
                # Handle direct S3 URLs or other URL formats
                filename = "Evidence File"
                if url:
                    try:
                        # Extract filename from S3 URL
                        if 'amazonaws.com' in url:
                            # Extract from S3 URL like: https://bucket.s3.region.amazonaws.com/path/filename.ext
                            url_parts = url.split('/')
                            if len(url_parts) > 0:
                                filename = url_parts[-1]
                                # Decode URL encoding
                                filename = filename.replace('%20', ' ').replace('%2E', '.')
                        else:
                            # Extract from other URL formats
                            url_parts = url.split('/')
                            if len(url_parts) > 0:
                                filename = url_parts[-1]
                    except:
                        filename = f"Evidence File {i + 1}"
                
                evidence_objects.append({
                    'id': i + 1,
                    'fileName': filename,
                    'filename': filename,
                    'name': filename,
                    'url': url,
                    's3_url': url,
                    'uploadedBy': event.CreatedBy.FirstName + ' ' + event.CreatedBy.LastName if event.CreatedBy else 'Unknown',
                    'uploadDate': event.CreatedAt.strftime('%Y-%m-%d') if event.CreatedAt else 'Unknown',
                    'size': 'Unknown'
                })
    
    return evidence_objects

@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_event_evidence_details(request, event_id):
    """Get detailed evidence information for a specific event - accepts either integer EventId or string EventId_Generated"""
    try:
        # MULTI-TENANCY: Extract tenant_id from request
        tenant_id = get_tenant_id_from_request(request)
        
        try:
            event = _get_event_for_tenant(tenant_id, event_id, allow_generated_slug=True)
            debug_print(f"DEBUG: Found event: {event.EventTitle}")
        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return JsonResponse(payload, status=code)
        
        # Get evidence data from CharField
        raw_ev = event.Evidence or ""
        evidence_string = raw_ev if isinstance(raw_ev, str) else ""
        evidence_urls = evidence_string.split(';') if evidence_string else []
        
        # Use the helper function to resolve file operation evidence
        evidence_objects = resolve_file_operation_evidence(evidence_urls, event)
        
        return JsonResponse({
            'success': True,
            'evidence': evidence_objects,
            'evidence_string': evidence_string,
            'count': len(evidence_objects)
        })
        
    except Exception as e:
        _log_exception(e, context='get_event_evidence_details')
        return JsonResponse({
            'success': False,
            'message': 'Error fetching event evidence details. Please try again later.'
        }, status=500)

@require_http_methods(["DELETE"])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def delete_event_evidence(request, event_id, evidence_id):
    """Delete evidence file from an event"""
    try:
        tenant_id = get_tenant_id_from_request(request)
        if tenant_id is None:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        if not _parse_server_user_id_int(request):
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Get the event
        try:
            event = Event.objects.select_related(
                'Owner', 'Reviewer', 'CreatedBy', 'FrameworkId', 'EventType'
            ).get(EventId=event_id, tenant_id=tenant_id)
        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return JsonResponse(payload, status=code)
        
        # Get current evidence string
        raw_ev = event.Evidence or ""
        evidence_string = raw_ev if isinstance(raw_ev, str) else ""
        evidence_urls = evidence_string.split(';') if evidence_string else []
        
        # Find and remove evidence URL
        evidence_found = False
        updated_urls = []
        
        for url in evidence_urls:
            if url.strip() and evidence_id not in url:
                updated_urls.append(url)
            elif evidence_id in url:
                evidence_found = True
        
        if not evidence_found:
            return JsonResponse({
                'success': False,
                'message': 'Evidence file not found'
            }, status=404)
        
        # Update the event with remaining URLs
        event.Evidence = ';'.join(updated_urls) if updated_urls else ""
        event.UpdatedAt = timezone.now()
        event.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Evidence file deleted successfully',
            'data': {
                'event_id': event_id,
                'evidence_id': evidence_id,
                'remaining_files': len(updated_urls)
            }
        })
        
    except Exception as e:
        _log_exception(e, context='delete_event_evidence')
        return JsonResponse({
            'success': False,
            'message': 'Error deleting evidence. Please try again later.'
        }, status=500)


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def link_evidence_to_incident(request):
    """
    Link multiple selected events as evidence to an incident
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        if tenant_id is None:
            return Response({
                'success': False,
                'message': 'Invalid tenant context'
            }, status=400)
        
        data = request.data
        incident_id = data.get('incident_id')
        linked_events = data.get('linked_events', [])
        
        debug_print(f"DEBUG: Linking evidence to incident {incident_id}")
        debug_print(f"DEBUG: User ID: {user_id_int}")
        debug_print(f"DEBUG: Linked events: {linked_events}")
        
        if not incident_id:
            return Response({
                'success': False,
                'message': 'Incident ID is required'
            }, status=400)
        
        try:
            incident_id = _parse_required_positive_int(incident_id, 'Incident ID')
        except ValueError as ve:
            return Response({
                'success': False,
                'message': str(ve)
            }, status=400)
            
        if not linked_events or len(linked_events) == 0:
            return Response({
                'success': False,
                'message': 'At least one event must be selected'
            }, status=400)
        
        # Import IncidentApproval model
        from ...models import IncidentApproval
        
        # Transform events data for storage
        evidence_data = []
        for event in linked_events:
            # Extract documents from different sources
            documents = []
            
            # 1. Check for Event evidence (S3 URLs from RiskaVaire/Event System)
            if event.get('source') in ['Riskavaire', 'RiskaVaire Module', 'Event System']:
                # Try to fetch the actual Event from database for more accurate data
                event_evidence_data = []
                
                # Try to get Event ID from the event data
                event_db_id = None
                if event.get('linkedRecordId') not in (None, ''):
                    try:
                        event_db_id = _parse_required_positive_int(
                            event.get('linkedRecordId'), 'Linked event record ID'
                        )
                    except ValueError as ve:
                        return Response({
                            'success': False,
                            'message': str(ve)
                        }, status=400)
                elif event.get('id') and str(event.get('id')).startswith('event_'):
                    try:
                        event_db_id = _parse_required_positive_int(
                            str(event.get('id')).replace('event_', ''), 'Event ID'
                        )
                    except ValueError:
                        event_db_id = None
                
                # If we have an Event ID, fetch from database
                if event_db_id:
                    try:
                        from ...models import Event
                        db_event = Event.objects.select_related(
                            'Owner', 'Reviewer', 'CreatedBy', 'FrameworkId', 'EventType'
                        ).get(EventId=event_db_id, tenant_id=tenant_id)
                        deny = _guard_event_object_access(request, db_event)
                        if deny:
                            payload, code = deny
                            return Response(payload, status=code)
                        if db_event.Evidence:
                            # Split semicolon-separated evidence URLs from database
                            ev_raw = db_event.Evidence
                            if isinstance(ev_raw, str):
                                event_evidence_data = [url.strip() for url in ev_raw.split(';') if url.strip()]
                            else:
                                event_evidence_data = []
                            debug_print(f"DEBUG: Found database evidence for Event {event_db_id}: {event_evidence_data}")
                    except Event.DoesNotExist:
                        debug_print(f"DEBUG: Event {event_db_id} not found in database")
                    except Exception as e:
                        _log_exception(e, context='link_evidence.fetch_event')
                
                # Fallback to event data from request
                if not event_evidence_data:
                    # Check for evidence array
                    if event.get('evidence') and isinstance(event.get('evidence'), list):
                        event_evidence_data = event.get('evidence', [])
                    # Check for rawData.evidence (for RiskaVaire events)
                    elif event.get('rawData') and event.get('rawData').get('evidence'):
                        evidence_str = event.get('rawData').get('evidence')
                        if evidence_str:
                            # Split semicolon-separated evidence URLs
                            event_evidence_data = [url.strip() for url in evidence_str.split(';') if url.strip()]
                    # Check for direct evidence string
                    elif event.get('evidence') and isinstance(event.get('evidence'), str):
                        evidence_str = event.get('evidence')
                        event_evidence_data = [url.strip() for url in evidence_str.split(';') if url.strip()]
                
                debug_print(f"DEBUG: Final evidence data for {event.get('source')}: {event_evidence_data}")
                
                for evidence_item in event_evidence_data:
                    if isinstance(evidence_item, str):
                        evidence_url = evidence_item
                    elif isinstance(evidence_item, dict) and evidence_item.get('url'):
                        evidence_url = evidence_item.get('url')
                    else:
                        continue
                    
                    if evidence_url and evidence_url.strip():
                        # Extract filename from URL
                        filename = "Document"
                        try:
                            if 'amazonaws.com' in evidence_url:
                                url_parts = evidence_url.split('/')
                                if len(url_parts) > 0:
                                    filename = url_parts[-1]
                                    filename = filename.replace('%20', ' ').replace('%2E', '.')
                            else:
                                url_parts = evidence_url.split('/')
                                if len(url_parts) > 0:
                                    filename = url_parts[-1]
                        except:
                            filename = "Event Document"
                        
                        documents.append({
                            'type': 'event_evidence',
                            'filename': filename,
                            'url': evidence_url,
                            's3_url': evidence_url,
                            'downloadable': True,
                            'source': 'Event Evidence'
                        })
            
            # 2. Check for Document Handling file operations
            if event.get('source') == 'Document Handling System':
                # Try to get file operation ID from the event data
                file_operation_id = None
                if event.get('linkedRecordId') not in (None, ''):
                    try:
                        file_operation_id = _parse_required_positive_int(
                            event.get('linkedRecordId'), 'File operation ID'
                        )
                    except ValueError as ve:
                        return Response({
                            'success': False,
                            'message': str(ve)
                        }, status=400)
                elif event.get('id') and str(event.get('id')).startswith('file_op_'):
                    try:
                        file_operation_id = _parse_required_positive_int(
                            str(event.get('id')).replace('file_op_', ''), 'File operation ID'
                        )
                    except ValueError:
                        pass
                
                debug_print(f"DEBUG: Document Handling - Looking for file operation ID: {file_operation_id}")
                
                # If we have a file operation ID, fetch from database
                if file_operation_id:
                    debug_print(f"DEBUG: Querying file_operations table for ID: {file_operation_id}")
                    try:
                        from django.db import connection
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT stored_name, s3_url, s3_key, s3_bucket, file_type, 
                                       original_name, content_type, export_format, file_size
                                FROM grc2.file_operations 
                                WHERE id = %s AND s3_url IS NOT NULL AND s3_url != ''
                            """, [file_operation_id])
                            
                            file_ops = cursor.fetchall()
                            debug_print(f"DEBUG: Found {len(file_ops)} file operations for ID {file_operation_id}")
                            
                            for file_op in file_ops:
                                stored_name, s3_url, s3_key, s3_bucket, file_type, original_name, content_type, export_format, file_size = file_op
                                
                                if s3_url and s3_url.strip():
                                    filename = original_name or stored_name or 'Document Handling File'
                                    
                                    documents.append({
                                        'type': 'file_operation',
                                        'filename': filename,
                                        'url': s3_url,
                                        's3_url': s3_url,
                                        's3_key': s3_key,
                                        's3_bucket': s3_bucket,
                                        'downloadable': True,
                                        'source': 'Document Handling',
                                        'file_type': file_type,
                                        'content_type': content_type,
                                        'export_format': export_format,
                                        'file_size': file_size
                                    })
                                    debug_print(f"DEBUG: Added Document Handling file: {filename} -> {s3_url}")
                    
                    except Exception as e:
                        _log_exception(e, context='link_evidence.file_operation')
                
                # Alternative: Try to find file operations by event title/description if no direct ID
                if not documents and event.get('title'):
                    try:
                        from django.db import connection
                        with connection.cursor() as cursor:
                            # Search for file operations that might be related to this event
                            event_title = event.get('title', '').lower()
                            cursor.execute("""
                                SELECT stored_name, s3_url, s3_key, s3_bucket, file_type, 
                                       original_name, content_type, export_format, file_size
                                FROM grc2.file_operations 
                                WHERE s3_url IS NOT NULL AND s3_url != ''
                                AND (LOWER(original_name) LIKE %s OR LOWER(stored_name) LIKE %s)
                                ORDER BY id DESC
                                LIMIT 5
                            """, [f'%{event_title}%', f'%{event_title}%'])
                            
                            file_ops = cursor.fetchall()
                            debug_print(f"DEBUG: Found {len(file_ops)} file operations by title search for: {event_title}")
                            
                            for file_op in file_ops:
                                stored_name, s3_url, s3_key, s3_bucket, file_type, original_name, content_type, export_format, file_size = file_op
                                
                                if s3_url and s3_url.strip():
                                    filename = original_name or stored_name or 'Document Handling File'
                                    
                                    documents.append({
                                        'type': 'file_operation',
                                        'filename': filename,
                                        'url': s3_url,
                                        's3_url': s3_url,
                                        's3_key': s3_key,
                                        's3_bucket': s3_bucket,
                                        'downloadable': True,
                                        'source': 'Document Handling',
                                        'file_type': file_type,
                                        'content_type': content_type,
                                        'export_format': export_format,
                                        'file_size': file_size
                                    })
                                    debug_print(f"DEBUG: Added Document Handling file by search: {filename} -> {s3_url}")
                    
                    except Exception as e:
                        _log_exception(e, context='link_evidence.file_op_search')
                
                # Last resort: Get recent Document Handling files if still no documents found
                if not documents:
                    try:
                        from django.db import connection
                        with connection.cursor() as cursor:
                            # Get recent file operations that have S3 URLs
                            cursor.execute("""
                                SELECT stored_name, s3_url, s3_key, s3_bucket, file_type, 
                                       original_name, content_type, export_format, file_size
                                FROM grc2.file_operations 
                                WHERE s3_url IS NOT NULL AND s3_url != ''
                                AND file_type IN ('pdf', 'xlsx', 'docx', 'csv', 'json')
                                ORDER BY id DESC
                                LIMIT 3
                            """)
                            
                            file_ops = cursor.fetchall()
                            debug_print(f"DEBUG: Found {len(file_ops)} recent file operations as fallback")
                            
                            for file_op in file_ops:
                                stored_name, s3_url, s3_key, s3_bucket, file_type, original_name, content_type, export_format, file_size = file_op
                                
                                if s3_url and s3_url.strip():
                                    filename = original_name or stored_name or 'Document Handling File'
                                    
                                    documents.append({
                                        'type': 'file_operation',
                                        'filename': f"{filename} (Recent)",
                                        'url': s3_url,
                                        's3_url': s3_url,
                                        's3_key': s3_key,
                                        's3_bucket': s3_bucket,
                                        'downloadable': True,
                                        'source': 'Document Handling',
                                        'file_type': file_type,
                                        'content_type': content_type,
                                        'export_format': export_format,
                                        'file_size': file_size
                                    })
                                    debug_print(f"DEBUG: Added recent Document Handling file: {filename} -> {s3_url}")
                    
                    except Exception as e:
                        _log_exception(e, context='link_evidence.recent_file_ops')
                
                # Fallback: Check for file_data in event
                if event.get('file_data'):
                    file_data = event.get('file_data', {})
                    if file_data.get('s3_url'):
                        documents.append({
                            'type': 'file_operation',
                            'filename': file_data.get('original_name') or file_data.get('file_name', 'Document'),
                            'url': file_data.get('s3_url'),
                            's3_url': file_data.get('s3_url'),
                            's3_key': file_data.get('s3_key'),
                            'file_size': file_data.get('file_size'),
                            'content_type': file_data.get('content_type'),
                            'downloadable': True,
                            'source': 'Document Handling'
                        })
            
            # 3. Check for Jira attachments (if any)
            if event.get('source') == 'Jira' and event.get('evidence'):
                for evidence_item in event.get('evidence', []):
                    if isinstance(evidence_item, dict) and evidence_item.get('url'):
                        documents.append({
                            'type': 'jira_attachment',
                            'filename': evidence_item.get('filename', 'Jira Attachment'),
                            'url': evidence_item.get('url'),
                            'downloadable': evidence_item.get('downloadable', False),
                            'source': 'Jira'
                        })
            
            evidence_item = {
                'id': event.get('id'),
                'title': event.get('title'),
                'source': event.get('source'),
                'framework': event.get('framework'),
                'module': event.get('module'),
                'category': event.get('category'),
                'status': event.get('status'),
                'priority': event.get('priority'),
                'description': event.get('description'),
                'timestamp': event.get('timestamp'),
                'linkedRecordType': event.get('linkedRecordType'),
                'linkedRecordId': event.get('linkedRecordId'),
                'linkedRecordName': event.get('linkedRecordName'),
                'owner': event.get('owner'),
                'reviewer': event.get('reviewer'),
                'evidence': event.get('evidence', []),
                'file_data': event.get('file_data', {}),
                'documents': documents,  # Add extracted documents
                'document_count': len(documents),
                'linked_at': timezone.now().isoformat(),
                'linked_by': user_id_int,
                'type': 'linked_evidence'
            }
            evidence_data.append(evidence_item)
        
        debug_print(f"DEBUG: Processed evidence data: {len(evidence_data)} items")
        
        # Check if incident approval record exists
        try:
            # Use filter().first() to handle multiple records gracefully
            incident_approval = IncidentApproval.objects.filter(IncidentId=incident_id).first()
            if not incident_approval:
                debug_print(f"DEBUG: IncidentApproval not found for incident {incident_id}, creating new one")
                incident_approval = IncidentApproval.objects.create(
                    IncidentId=incident_id,
                    ExtractedInfo={}
                )
            else:
                debug_print(f"DEBUG: Found existing incident approval record")
            
            # Get existing ExtractedInfo or create new
            existing_data = incident_approval.ExtractedInfo or {}
            
            # Add linked evidence to existing data
            if 'linked_evidence' not in existing_data:
                existing_data['linked_evidence'] = []
            
            existing_data['linked_evidence'].extend(evidence_data)
            
            # Update the record
            incident_approval.ExtractedInfo = existing_data
            incident_approval.save()
            
        except Exception as e:
            _log_exception(e, context='link_evidence.incident_approval')
            return Response({
                'success': False,
                'message': 'Error accessing incident approval. Please try again later.'
            }, status=500)
        
        debug_print(f"DEBUG: Successfully linked {len(evidence_data)} events to incident {incident_id}")
        
        return Response({
            'success': True,
            'message': f'Successfully linked {len(evidence_data)} event(s) as evidence',
            'incident_id': incident_id,
            'linked_count': len(evidence_data),
            'evidence_data': evidence_data
        })
        
    except Exception as e:
        _log_exception(e, context='link_evidence_to_incident')
        return Response({
            'success': False,
            'message': 'Error linking evidence. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_incident_linked_evidence(request, incident_id):
    """
    Get linked evidence for a specific incident
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if tenant_id is None:
            return Response({
                'success': False,
                'message': 'Invalid tenant context'
            }, status=400)
        if not _parse_server_user_id_int(request):
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=401)

        debug_print(f"DEBUG: Getting linked evidence for incident {incident_id}")
        
        # Import IncidentApproval model
        from ...models import IncidentApproval
        
        try:
            incident_approval = IncidentApproval.objects.filter(
                IncidentId=incident_id,
                FrameworkId__tenant_id=tenant_id,
            ).first()
            if not incident_approval:
                # No approval row yet is normal (e.g. new incident); return empty evidence — not HTTP 404
                # (404 makes browsers log failed requests and breaks clients that expect 200 + JSON).
                debug_print(f"DEBUG: No IncidentApproval found for incident {incident_id} — returning empty linked_evidence")
                return Response({
                    'success': True,
                    'incident_id': incident_id,
                    'linked_evidence': [],
                    'count': 0
                })
            
            extracted_info = incident_approval.ExtractedInfo or {}
            linked_evidence = extracted_info.get('linked_evidence', [])
            
            debug_print(f"DEBUG: Found {len(linked_evidence)} linked evidence items")
            
            # Re-extract documents for each linked evidence item to get fresh data
            enhanced_linked_evidence = []
            for evidence in linked_evidence:
                debug_print(f"DEBUG: Re-extracting documents for evidence: {evidence.get('id')} - {evidence.get('title')}")
                
                # Extract documents from different sources (same logic as in link_evidence_to_incident)
                documents = []
                
                # 1. Check for Event evidence (S3 URLs from RiskaVaire/Event System)
                if evidence.get('source') in ['Riskavaire', 'RiskaVaire Module', 'Event System']:
                    # Try to get Event ID from the evidence data
                    event_db_id = None
                    if evidence.get('linkedRecordId'):
                        event_db_id = evidence.get('linkedRecordId')
                    elif evidence.get('id') and evidence.get('id').startswith('event_'):
                        try:
                            event_db_id = int(evidence.get('id').replace('event_', ''))
                        except ValueError:
                            pass
                    
                    # If we have an Event ID, fetch from database
                    if event_db_id:
                        try:
                            from ...models import Event
                            db_event = Event.objects.get(EventId=event_db_id, tenant_id=tenant_id)
                            if db_event.Evidence:
                                # Split semicolon-separated evidence URLs from database
                                event_evidence_data = [url.strip() for url in db_event.Evidence.split(';') if url.strip()]
                                debug_print(f"DEBUG: Found database evidence for Event {event_db_id}: {event_evidence_data}")
                                
                                for evidence_url in event_evidence_data:
                                    if evidence_url and evidence_url.strip():
                                        # Extract filename from URL
                                        filename = "Document"
                                        try:
                                            if 'amazonaws.com' in evidence_url:
                                                url_parts = evidence_url.split('/')
                                                if len(url_parts) > 0:
                                                    filename = url_parts[-1]
                                                    filename = filename.replace('%20', ' ').replace('%2E', '.')
                                            else:
                                                url_parts = evidence_url.split('/')
                                                if len(url_parts) > 0:
                                                    filename = url_parts[-1]
                                        except:
                                            filename = "Event Document"
                                        
                                        documents.append({
                                            'type': 'event_evidence',
                                            'filename': filename,
                                            'url': evidence_url,
                                            's3_url': evidence_url,
                                            'downloadable': True,
                                            'source': 'Event Evidence'
                                        })
                        except Event.DoesNotExist:
                            debug_print(f"DEBUG: Event {event_db_id} not found in database")
                        except Exception as e:
                            _log_exception(e, context='get_incident_linked_evidence.fetch_event')
                
                # 2. Check for Document Handling file operations
                if evidence.get('source') == 'Document Handling System':
                    # Try to get file operation ID from the evidence data
                    file_operation_id = None
                    if evidence.get('linkedRecordId'):
                        file_operation_id = evidence.get('linkedRecordId')
                    elif evidence.get('id') and evidence.get('id').startswith('file_op_'):
                        try:
                            file_operation_id = int(evidence.get('id').replace('file_op_', ''))
                        except ValueError:
                            pass
                    
                    debug_print(f"DEBUG: Document Handling - Looking for file operation ID: {file_operation_id}")
                    
                    # If we have a file operation ID, fetch from database
                    if file_operation_id:
                        try:
                            fo = FileOperations.objects.filter(
                                id=file_operation_id,
                                FrameworkId__tenant_id=tenant_id,
                            ).exclude(s3_url__isnull=True).exclude(s3_url='').first()
                            if fo and (fo.s3_url or '').strip():
                                s3_url = fo.s3_url.strip()
                                filename = fo.original_name or fo.stored_name or 'Document Handling File'
                                documents.append({
                                    'type': 'file_operation',
                                    'filename': filename,
                                    'url': s3_url,
                                    's3_url': s3_url,
                                    's3_key': fo.s3_key,
                                    's3_bucket': fo.s3_bucket,
                                    'downloadable': True,
                                    'source': 'Document Handling',
                                    'file_type': fo.file_type,
                                    'content_type': fo.content_type,
                                    'export_format': fo.export_format,
                                    'file_size': fo.file_size,
                                })
                                debug_print(f"DEBUG: Added Document Handling file: {filename} -> {s3_url}")
                        except Exception as e:
                            _log_exception(e, context='get_incident_linked_evidence.file_operation')
                
                # Create enhanced evidence item with fresh documents
                enhanced_evidence = {
                    **evidence,  # Copy all original evidence data
                    'documents': documents,  # Add fresh documents
                    'document_count': len(documents)  # Update document count
                }
                enhanced_linked_evidence.append(enhanced_evidence)
                
                debug_print(f"DEBUG: Enhanced evidence {evidence.get('id')} now has {len(documents)} documents")
            
            return Response({
                'success': True,
                'incident_id': incident_id,
                'linked_evidence': enhanced_linked_evidence,
                'count': len(enhanced_linked_evidence)
            })
        
        except Exception as inner_exc:
            _log_exception(inner_exc, context='get_incident_linked_evidence.inner')
            return Response({
                'success': False,
                'message': 'Error loading linked evidence. Please try again later.'
            }, status=500)
        
    except Exception as e:
        _log_exception(e, context='get_incident_linked_evidence')
        return Response({
            'success': False,
            'message': 'Error fetching linked evidence. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def download_linked_evidence_document(request, incident_id, evidence_id, document_index):
    """
    Download a document from linked evidence
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not _parse_server_user_id_int(request):
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        debug_print(f"DEBUG: Download linked evidence document - incident: {incident_id}, evidence: {evidence_id}, document: {document_index}")
        
        # Import IncidentApproval model
        from ...models import IncidentApproval
        
        try:
            # Tenant-scoped incident approval (via framework)
            incident_approval = IncidentApproval.objects.filter(
                IncidentId=incident_id,
                FrameworkId__tenant_id=tenant_id,
            ).first()
            if not incident_approval:
                return JsonResponse({
                    'success': False,
                    'message': 'Incident approval record not found'
                }, status=404)
            
            extracted_info = incident_approval.ExtractedInfo or {}
            linked_evidence = extracted_info.get('linked_evidence', [])
            
            # Find the specific evidence item
            evidence_item = None
            for evidence in linked_evidence:
                if str(evidence.get('id')) == str(evidence_id):
                    evidence_item = evidence
                    break
            
            if not evidence_item:
                return JsonResponse({
                    'success': False,
                    'message': 'Linked evidence not found'
                }, status=404)
            
            # Get the documents from the evidence
            documents = evidence_item.get('documents', [])
            document_index = int(document_index)
            
            if document_index < 0 or document_index >= len(documents):
                return JsonResponse({
                    'success': False,
                    'message': 'Document not found'
                }, status=404)
            
            document = documents[document_index]
            
            if not document.get('downloadable'):
                return JsonResponse({
                    'success': False,
                    'message': 'Document is not downloadable'
                }, status=400)
            
            # Handle different document types
            if document.get('type') == 'event_evidence' and document.get('s3_url'):
                # Use existing S3 download functionality
                from urllib.parse import quote
                s3_url = document.get('s3_url')
                filename = document.get('filename', 'document')
                
                # Extract S3 key from URL
                s3_key = ""
                if 'amazonaws.com' in s3_url:
                    try:
                        # Extract S3 key from URL like: https://bucket.s3.region.amazonaws.com/key
                        url_parts = s3_url.split('amazonaws.com/')
                        if len(url_parts) > 1:
                            s3_key = url_parts[1]
                    except:
                        s3_key = filename
                
                # Redirect to S3 download — auth uses session in s3_download_file (no client user_id).
                download_url = f"/api/s3/download/{quote(s3_key, safe='')}/{quote(filename, safe='')}/"

                from django.http import HttpResponseRedirect
                from grc.utils.url_validator import assert_safe_relative_redirect, UnsafeRedirectError
                try:
                    safe_download_url = assert_safe_relative_redirect(
                        download_url,
                        allowed_path_prefixes=("/api/s3/download/",),
                    )
                except UnsafeRedirectError:
                    return JsonResponse(
                        {
                            'success': False,
                            'message': 'Invalid download redirect target',
                        },
                        status=400,
                    )
                return HttpResponseRedirect(safe_download_url)
                
            elif document.get('type') == 'file_operation' and document.get('s3_url'):
                # Handle Document Handling file downloads
                from urllib.parse import quote
                s3_url = document.get('s3_url')
                s3_key = document.get('s3_key', '')
                filename = document.get('filename', 'document')
                
                if not s3_key and 'amazonaws.com' in s3_url:
                    try:
                        url_parts = s3_url.split('amazonaws.com/')
                        if len(url_parts) > 1:
                            s3_key = url_parts[1]
                    except:
                        s3_key = filename
                
                download_url = f"/api/s3/download/{quote(s3_key, safe='')}/{quote(filename, safe='')}/"

                from django.http import HttpResponseRedirect
                from grc.utils.url_validator import assert_safe_relative_redirect, UnsafeRedirectError
                try:
                    safe_download_url = assert_safe_relative_redirect(
                        download_url,
                        allowed_path_prefixes=("/api/s3/download/",),
                    )
                except UnsafeRedirectError:
                    return JsonResponse(
                        {
                            'success': False,
                            'message': 'Invalid download redirect target',
                        },
                        status=400,
                    )
                return HttpResponseRedirect(safe_download_url)
                
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Document type not supported for download'
                }, status=400)
            
        except IncidentApproval.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Incident approval record not found'
            }, status=404)
        
    except Exception as e:
        _log_exception(e, context='download_linked_evidence_document')
        return JsonResponse({
            'success': False,
            'message': 'Error downloading document. Please try again later.'
        }, status=500)


@require_http_methods(["DELETE"])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def remove_event_evidence(request, event_id):
    """Remove evidence file from a specific event"""
    try:
        tenant_id = get_tenant_id_from_request(request)
        if not _parse_server_user_id_int(request):
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        data = request.data if hasattr(request, 'data') else {}
        file_index = data.get('file_index') or request.GET.get('file_index')
        
        if file_index is None:
            return JsonResponse({
                'success': False,
                'message': 'File index is required'
            }, status=400)
        
        try:
            file_index = int(file_index)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid file index'
            }, status=400)
        
        # Check if event exists
        try:
            event = Event.objects.select_related(
                'Owner', 'Reviewer', 'CreatedBy', 'FrameworkId', 'EventType'
            ).get(EventId=event_id, tenant_id=tenant_id)
            debug_print(f"DEBUG: Found event: {event.EventTitle}")
        except Event.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Event not found'
            }, status=404)
        
        deny = _guard_event_object_access(request, event)
        if deny:
            payload, code = deny
            return JsonResponse(payload, status=code)
        
        # Get current evidence lists
        current_evidence = event.Evidence or []
        current_s3_urls = getattr(event, 'S3EvidenceUrls', None) or []
        
        # Check if file index is valid
        if file_index < 0 or file_index >= len(current_evidence):
            return JsonResponse({
                'success': False,
                'message': 'Invalid file index'
            }, status=400)
        
        # Remove file from both lists
        removed_file = current_evidence.pop(file_index)
        if file_index < len(current_s3_urls):
            current_s3_urls.pop(file_index)
        
        # Update event
        event.Evidence = current_evidence
        event.S3EvidenceUrls = current_s3_urls
        event.UpdatedAt = timezone.now()
        event.save()
        
        debug_print(f"DEBUG: Removed evidence file from event {event_id}: {removed_file.get('file_name', 'Unknown')}")
        
        return JsonResponse({
            'success': True,
            'message': 'Evidence file removed successfully',
            'removed_file': removed_file,
            'remaining_count': len(current_evidence)
        })
        
    except Exception as e:
        _log_exception(e, context='remove_event_evidence')
        return JsonResponse({
            'success': False,
            'message': 'Error removing evidence file. Please try again later.'
        }, status=500)


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([EventViewAllPermission, EventViewModulePermission])
@csrf_exempt
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_file_operations(request):
    """
    Get file operations for Document Handling evidence
    Returns file operations from the file_operations table using Django ORM
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        if tenant_id is None:
            return JsonResponse({
                'success': False,
                'message': 'Tenant context required',
                'events': [],
            }, status=400)

        user_id_int = _parse_server_user_id_int(request)
        if not user_id_int:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required',
                'events': [],
            }, status=401)

        try:
            limit = int(request.GET.get('limit', 50))
        except (TypeError, ValueError):
            limit = 50
        limit = max(1, min(limit, 500))

        operation_type = request.GET.get('operation_type')
        status = request.GET.get('status')

        perms = RBACUtils.get_user_event_permissions(user_id_int)
        modlist = RBACUtils.get_user_accessible_modules(user_id_int)
        view_all = bool(perms.get('is_admin') or perms.get('view_all_event'))

        base = FileOperations.objects.filter(FrameworkId__tenant_id=tenant_id)
        total_records = base.count()
        query = base

        if not view_all:
            if perms.get('view_module_event') and modlist:
                query = query.filter(module__in=modlist)
            else:
                query = query.none()
            query = query.filter(user_id=str(user_id_int))
        if operation_type:
            query = query.filter(operation_type=operation_type)
        if status:
            query = query.filter(status=status)

        operations = list(query.order_by('-created_at')[:limit])
        debug_print(f"DEBUG: get_file_operations tenant={tenant_id} count={len(operations)} view_all={view_all}")

        # Transform operations to match event format for frontend
        transformed_operations = []
        for op in operations:
            # Format timestamp
            timestamp = op.created_at.strftime('%m/%d/%Y, %I:%M:%S %p') if op.created_at else 'N/A'
            
            # Format file size
            def format_file_size(size_bytes):
                if not size_bytes:
                    return "Unknown size"
                # Convert bytes to human readable format
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.1f} {unit}"
                    size_bytes /= 1024.0
                return f"{size_bytes:.1f} TB"
            
            file_size_display = format_file_size(op.file_size)
            display_name = op.original_name or op.file_name or "Unknown File"
            
            transformed_op = {
                'id': f"file_op_{op.id}",
                'title': f"{op.operation_type.title()} Operation: {display_name}",
                'framework': 'Document Handling',
                'module': getattr(op, 'module', None) or op.operation_type.title(),
                'category': 'File Operation',
                'source': 'Document Handling System',
                'timestamp': timestamp,
                'status': op.status.title(),
                'linkedRecordType': 'File Operation',
                'linkedRecordId': str(op.id),
                'linkedRecordName': display_name,
                'priority': 'High' if op.status == 'failed' else 'Medium',
                'description': f"File {op.operation_type}: {display_name} ({file_size_display})" + (f" - Error: {op.error}" if op.status == 'failed' and op.error else ''),
                'owner': op.user_id,
                'reviewer': 'System',
                'evidence': [],
                'file_data': {
                    'file_name': op.file_name,
                    'original_name': op.original_name,
                    'stored_name': op.stored_name,
                    's3_url': op.s3_url,
                    's3_key': op.s3_key,
                    's3_bucket': op.s3_bucket,
                    'file_type': op.file_type,
                    'file_size': op.file_size,
                    'content_type': op.content_type,
                    'export_format': op.export_format,
                    'record_count': op.record_count,
                    'operation_type': op.operation_type,
                    'platform': op.platform,
                    'completed_at': op.completed_at.strftime('%m/%d/%Y, %I:%M:%S %p') if op.completed_at else None,
                    'metadata': op.metadata
                }
            }
            transformed_operations.append(transformed_op)
        
        return JsonResponse({
            'success': True,
            'events': transformed_operations,
            'count': len(transformed_operations),
            'total_records': total_records,
            'message': f'Retrieved {len(transformed_operations)} file operations out of {total_records} total records'
        })
        
    except Exception as e:
        _log_exception(e, context='get_file_operations')
        return JsonResponse({
            'success': False,
            'message': 'Error retrieving file operations. Please try again later.',
            'events': []
        }, status=500)