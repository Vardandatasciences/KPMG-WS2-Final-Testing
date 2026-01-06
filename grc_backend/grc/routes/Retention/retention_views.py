"""
Retention Policy Management Views
Handles retention policies, timelines, and data processing agreements
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.apps import apps
from datetime import timedelta
import logging
import json

from ...models import (
    RetentionModulePageConfig,
    RetentionTimeline,
    DataLifecycleAuditLog,
    Users, Framework, RBAC
)

logger = logging.getLogger(__name__)

# DRF Session auth variant that skips CSRF enforcement for API clients (SPA)
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


def is_user_administrator(user_id):
    """Check if user has administrator privileges"""
    try:
        user = Users.objects.get(UserId=user_id)
        try:
            rbac_entry = RBAC.objects.get(user_id=user_id)
            user_role = rbac_entry.role or ''
            is_admin = (
                rbac_entry.role == 'GRC Administrator' or
                'GRC Administrator' in user_role or
                'Administrator' in user_role
            )
            return is_admin
        except RBAC.DoesNotExist:
            return False
    except Users.DoesNotExist:
        return False


# =====================================================
# DATA RETENTION MODULE & PAGE CONFIGURATION VIEWS
# =====================================================

DEFAULT_RETENTION_DAYS = 210

# Map modules to their pages (must align with frontend)
MODULE_PAGES = {
    'policy': [
        'policy_create', 'policy_update', 'policy_version_create', 'policy_approval',
        'policy_acknowledgement', 'policy_templating', 'policy_subpolicy_add',
        'framework_create', 'framework_update', 'framework_version_create',
        'framework_approval', 'save_policy_details', 'save_framework_to_db',
        'save_edited_framework_to_db', 'save_policies_bulk', 'save_single_policy',
        'save_checked_sections_json'
    ],
    'compliance': [
        'compliance_create', 'compliance_edit', 'add_category_value', 'add_category_business_unit'
    ],
    'audit': [
        'create_audit', 'save_audit_json_version', 'save_audit_version',
        'update_audit_finding', 'add_compliance_to_audit', 'save_review_progress'
    ],
    'incident': [
        'create_incident', 'update_incident', 'create_workflow',
        'create_incident_from_audit_finding', 'add_category', 'add_business_unit'
    ],
    # Align risk keys with frontend and signals
    'risk': [
        'risk_create', 'risk_update',
        'risk_instance_create', 'risk_instance_update',
        'risk_status_update', 'risk_mitigation_update',
        'risk_category_add', 'add_business_impact', 'add_risk_category'
    ],
    'document_handling': [
        'document_upload'
    ],
    'change_management': [
        'start_amendment_analysis', 'match_amendments_compliances', 'add_compliance_from_amendment'
    ],
    'event_handling': [
        'create_module', 'create_event_type', 'create_event',
        'update_event', 'attach_evidence', 'upload_event_evidence'
    ],
    # TPRM Modules
    'vendor': [
        'vendor_create', 'vendor_update', 'vendor_category_create',
        'vendor_contact_create', 'vendor_document_upload', 'vendor_submit_registration'
    ],
    'vendor_contract': [
        'contract_create', 'contract_update', 'contract_archive', 'contract_restore',
        'contract_version_create', 'contract_amendment_create', 'contract_subcontract_create'
    ],
    'contract_term': [
        'contract_term_create', 'contract_term_update', 'contract_term_delete'
    ],
    'contract_clause': [
        'contract_clause_create', 'contract_clause_update', 'contract_clause_delete'
    ],
    'vendor_sla': [
        'sla_create', 'sla_update', 'sla_submit', 'sla_approve'
    ],
    'sla_metric': [
        'sla_metric_create', 'sla_metric_update', 'sla_metric_delete'
    ],
    'rfp': [
        'rfp_create', 'rfp_update', 'rfp_submit_for_review', 'rfp_publish',
        'rfp_award', 'rfp_document_upload', 'rfp_version_create'
    ],
    'rfp_evaluation_criteria': [
        'rfp_evaluation_criteria_create', 'rfp_evaluation_criteria_update',
        'rfp_evaluation_criteria_delete'
    ],
    'rfp_type_custom_fields': [
        'rfp_type_custom_fields_create', 'rfp_type_custom_fields_update'
    ],
    'bcp_drp_plan': [
        'bcp_drp_plan_create', 'bcp_drp_plan_update', 'bcp_drp_plan_upload',
        'bcp_drp_plan_ocr_extract', 'bcp_drp_plan_approve', 'bcp_drp_plan_reject'
    ],
    'bcp_drp_evaluation': [
        'bcp_drp_evaluation_create', 'bcp_drp_evaluation_update', 'bcp_drp_evaluation_save'
    ],
}

# Map RecordType (from RetentionTimeline) to Django app/model for updating retentionExpiry
RECORD_MODEL_MAP = {
    'policy': ('grc', 'Policy'),
    'compliance': ('grc', 'Compliance'),
    'audit': ('grc', 'Audit'),
    'incident': ('grc', 'Incident'),
    'risk': ('grc', 'Risk'),
    'risk_instance': ('grc', 'RiskInstance'),
    'event': ('grc', 'Event'),
    'audit_document': ('grc', 'AuditDocument'),
    's3_file': ('grc', 'S3File'),
    'file_operations': ('grc', 'FileOperations'),
    # TPRM Models
    'vendor': ('tprm_backend.apps.vendor_core', 'Vendors'),
    'vendor_contract': ('contracts', 'VendorContract'),
    'contract_term': ('contracts', 'ContractTerm'),
    'contract_clause': ('contracts', 'ContractClause'),
    'vendor_sla': ('slas', 'VendorSLA'),
    'sla_metric': ('slas', 'SLAMetric'),
    'rfp': ('rfp', 'RFP'),
    'rfp_evaluation_criteria': ('rfp', 'RFPEvaluationCriteria'),
    'rfp_type_custom_fields': ('rfp', 'RFPTypeCustomFields'),
    'bcp_drp_plan': ('bcpdrp', 'Plan'),
    'bcp_drp_evaluation': ('bcpdrp', 'Evaluation'),
}


def _update_record_retention_expiry_from_timeline(timeline: RetentionTimeline):
    """Update the underlying record's retentionExpiry to match the timeline."""
    try:
        key = (timeline.RecordType or '').lower()
        if key not in RECORD_MODEL_MAP:
            return
        app_label, model_name = RECORD_MODEL_MAP[key]
        model_cls = apps.get_model(app_label, model_name)
        if not model_cls:
            return
        model_cls.objects.filter(pk=timeline.RecordId).update(retentionExpiry=timeline.RetentionEndDate)
    except Exception as exc:
        logger.error(
            "Error updating retentionExpiry for %s#%s: %s",
            timeline.RecordType, timeline.RecordId, str(exc)
        )


def ensure_defaults_for_module(module_key: str):
    """Ensure all pages for a module exist in DB with defaults."""
    if module_key not in MODULE_PAGES:
        return
    for page_key in MODULE_PAGES[module_key]:
        RetentionModulePageConfig.objects.get_or_create(
            module=module_key,
            sub_page=page_key,
            defaults={
                'checklist_status': True,
                'retention_days': DEFAULT_RETENTION_DAYS
            }
        )


def module_enabled_state(module_key: str) -> bool:
    """A module is enabled if any of its pages are enabled."""
    return RetentionModulePageConfig.objects.filter(
        module=module_key,
        checklist_status=True
    ).exists()


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_module_configs(request):
    """
    Get module enabled state (derived from page configs).
    framework_id is accepted for compatibility but ignored (per requirement: no framework storage).
    """
    try:
        module_key = request.GET.get('module_key')  # Optional filter

        # Ensure defaults exist
        for mk in MODULE_PAGES.keys():
            ensure_defaults_for_module(mk)

        def build_payload(mk: str):
            return {
                'enabled': module_enabled_state(mk),
                # Kept for compatibility; UI ignores these now
                'retention_years': 0,
                'retention_months': 0,
                'retention_days': 0,
                'auto_delete': False,
                'disposal_method': 'secure_delete'
            }

        if module_key:
            if module_key not in MODULE_PAGES:
                return Response({'status': 'error', 'message': 'invalid module_key'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'status': 'success', 'data': {module_key: build_payload(module_key)}},
                            status=status.HTTP_200_OK)

        data = {mk: build_payload(mk) for mk in MODULE_PAGES.keys()}
        return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting module configs: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def bulk_update_module_configs(request):
    """
    Bulk update module enabled state.
    Body: { "configs": [{module_key, enabled}], "updated_by": user_id }
    When a module is disabled, all its pages are unchecked.
    """
    try:
        data = request.data
        configs = data.get('configs', [])
        updated_by_id = data.get('updated_by')

        if not updated_by_id or not is_user_administrator(updated_by_id):
            return Response({
                'status': 'error',
                'message': 'Only administrators can update retention configurations'
            }, status=status.HTTP_403_FORBIDDEN)

        for cfg in configs:
            module_key = cfg.get('module_key')
            enabled = bool(cfg.get('enabled', False))
            if not module_key or module_key not in MODULE_PAGES:
                continue
            ensure_defaults_for_module(module_key)
            if not enabled:
                RetentionModulePageConfig.objects.filter(module=module_key).update(checklist_status=False)
            else:
                ensure_defaults_for_module(module_key)

        result = {mk: {'enabled': module_enabled_state(mk)} for mk in MODULE_PAGES.keys()}
        return Response({
            'status': 'success',
            'message': f'{len(configs)} module configurations updated successfully',
            'data': result
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error bulk updating module configs: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_page_configs(request):
    """
    Get retention configurations for pages within a module.
    Query params: module_key (optional), page_key (optional)
    framework_id is ignored (kept for compatibility).
    """
    try:
        module_key = request.GET.get('module_key')
        page_key = request.GET.get('page_key')

        if module_key:
            if module_key not in MODULE_PAGES:
                return Response({'status': 'error', 'message': 'invalid module_key'}, status=status.HTTP_400_BAD_REQUEST)
            ensure_defaults_for_module(module_key)
            qs = RetentionModulePageConfig.objects.filter(module=module_key)
        else:
            for mk in MODULE_PAGES.keys():
                ensure_defaults_for_module(mk)
            qs = RetentionModulePageConfig.objects.all()

        if page_key:
            qs = qs.filter(sub_page=page_key)

        data = {}
        for cfg in qs:
            data[cfg.sub_page] = {
                'enabled': cfg.checklist_status,
                'retention_years': 0,
                'retention_months': 0,
                'retention_days': cfg.retention_days,
                'override_module': False
            }

        return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting page configs: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def bulk_update_page_configs(request):
    """
    Bulk update page retention configurations
    Body: { "configs": [{page_key, module_key, enabled, retention_days}], "updated_by": user_id }
    """
    try:
        data = request.data
        configs = data.get('configs', [])
        updated_by_id = data.get('updated_by')

        if not updated_by_id or not is_user_administrator(updated_by_id):
            return Response({
                'status': 'error',
                'message': 'Only administrators can update retention configurations'
            }, status=status.HTTP_403_FORBIDDEN)

        for cfg in configs:
            page_key = cfg.get('page_key')
            module_key = cfg.get('module_key')
            # Require a valid module, but allow any page_key so frontend
            # can manage additional endpoints beyond the static MODULE_PAGES map.
            if not module_key or module_key not in MODULE_PAGES:
                continue
            if not page_key:
                continue
            enabled = bool(cfg.get('enabled', False))
            retention_days = int(cfg.get('retention_days', DEFAULT_RETENTION_DAYS) or DEFAULT_RETENTION_DAYS)
            ensure_defaults_for_module(module_key)
            obj, _ = RetentionModulePageConfig.objects.get_or_create(
                module=module_key,
                sub_page=page_key,
                defaults={'checklist_status': enabled, 'retention_days': retention_days}
            )
            # Safety: avoid ever persisting an explicit 0 for AutoField primary key
            if getattr(obj, 'id', None) == 0:
                obj.id = None
            obj.checklist_status = enabled
            obj.retention_days = retention_days
            obj.save()

        # Return latest data for all modules
        data_out = {}
        for mk in MODULE_PAGES.keys():
            ensure_defaults_for_module(mk)
            qs = RetentionModulePageConfig.objects.filter(module=mk)
            for cfg in qs:
                data_out[cfg.sub_page] = {
                    'enabled': cfg.checklist_status,
                    'retention_years': 0,
                    'retention_months': 0,
                    'retention_days': cfg.retention_days,
                    'override_module': False
                }

        return Response({
            'status': 'success',
            'message': f'{len(configs)} page configurations updated successfully',
            'data': data_out
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error bulk updating page configs: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================================
# ARCHIVE / UNARCHIVE RETENTION RECORDS
# =====================================================

def _get_user(user_id):
    try:
        return Users.objects.get(UserId=user_id)
    except Users.DoesNotExist:
        return None


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def archive_retention_record(request):
    """
    Archive a record's retention timeline.
    Body: { "retention_timeline_id": int, "archive_location": str, "archived_by": user_id }
    """
    try:
        data = request.data
        timeline_id = data.get('retention_timeline_id')
        archive_location = data.get('archive_location')
        archived_by_id = data.get('archived_by')

        if not timeline_id:
            return Response({'status': 'error', 'message': 'retention_timeline_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        timeline = get_object_or_404(RetentionTimeline, RetentionTimelineId=timeline_id)
        if timeline.is_archived:
            return Response({'status': 'error', 'message': 'Record already archived'}, status=status.HTTP_400_BAD_REQUEST)

        user_obj = _get_user(archived_by_id) if archived_by_id else None

        before_status = timeline.Status
        timeline.archive(user=user_obj, location=archive_location)

        DataLifecycleAuditLog.log_action(
            action_type='ARCHIVE',
            record_type=timeline.RecordType,
            record_id=timeline.RecordId,
            record_name=timeline.RecordName,
            timeline=timeline,
            performed_by=user_obj,
            before_status=before_status,
            after_status='Archived',
            details={'archive_location': archive_location}
        )

        return Response({'status': 'success', 'message': 'Record archived', 'data': {
            'retention_timeline_id': timeline.RetentionTimelineId,
            'status': timeline.Status,
            'is_archived': timeline.is_archived,
            'archived_date': timeline.archived_date,
            'archive_location': timeline.archive_location,
        }}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error archiving retention record: {str(e)}")
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def unarchive_retention_record(request):
    """
    Unarchive a record's retention timeline (resumes deletion if not paused).
    Body: { "retention_timeline_id": int, "performed_by": user_id }
    """
    try:
        data = request.data
        timeline_id = data.get('retention_timeline_id')
        performed_by_id = data.get('performed_by')

        if not timeline_id:
            return Response({'status': 'error', 'message': 'retention_timeline_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        timeline = get_object_or_404(RetentionTimeline, RetentionTimelineId=timeline_id)
        if not timeline.is_archived:
            return Response({'status': 'error', 'message': 'Record is not archived'}, status=status.HTTP_400_BAD_REQUEST)

        user_obj = _get_user(performed_by_id) if performed_by_id else None

        before_status = timeline.Status
        timeline.unarchive(user=user_obj)

        DataLifecycleAuditLog.log_action(
            action_type='UNARCHIVE',
            record_type=timeline.RecordType,
            record_id=timeline.RecordId,
            record_name=timeline.RecordName,
            timeline=timeline,
            performed_by=user_obj,
            before_status=before_status,
            after_status=timeline.Status
        )

        return Response({'status': 'success', 'message': 'Record unarchived', 'data': {
            'retention_timeline_id': timeline.RetentionTimelineId,
            'status': timeline.Status,
            'is_archived': timeline.is_archived,
            'archived_date': timeline.archived_date,
            'archive_location': timeline.archive_location,
        }}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error unarchiving retention record: {str(e)}")
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================================
# PAUSE / RESUME DELETION
# =====================================================

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def pause_deletion(request):
    """
    Pause automated deletion for a record.
    Body: { "retention_timeline_id": int, "reason": str, "pause_until": "YYYY-MM-DD", "performed_by": user_id }
    """
    try:
        data = request.data
        timeline_id = data.get('retention_timeline_id')
        reason = data.get('reason')
        pause_until = data.get('pause_until')
        performed_by_id = data.get('performed_by')

        if not timeline_id:
            return Response({'status': 'error', 'message': 'retention_timeline_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        timeline = get_object_or_404(RetentionTimeline, RetentionTimelineId=timeline_id)
        user_obj = _get_user(performed_by_id) if performed_by_id else None

        before_status = timeline.Status
        # parse pause_until if provided
        if pause_until:
            try:
                pause_until_date = timezone.datetime.fromisoformat(pause_until).date()
            except Exception:
                return Response({'status': 'error', 'message': 'Invalid pause_until date format, expected YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            pause_until_date = None

        timeline.pause_deletion(reason=reason, pause_until=pause_until_date)

        DataLifecycleAuditLog.log_action(
            action_type='PAUSE',
            record_type=timeline.RecordType,
            record_id=timeline.RecordId,
            record_name=timeline.RecordName,
            timeline=timeline,
            performed_by=user_obj,
            before_status=before_status,
            after_status='Paused',
            reason=reason,
            details={'pause_until': pause_until}
        )

        return Response({'status': 'success', 'message': 'Deletion paused', 'data': {
            'retention_timeline_id': timeline.RetentionTimelineId,
            'status': timeline.Status,
            'deletion_paused': timeline.deletion_paused,
            'pause_reason': timeline.pause_reason,
            'pause_until': timeline.pause_until,
        }}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error pausing deletion: {str(e)}")
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def resume_deletion(request):
    """
    Resume automated deletion for a record.
    Body: { "retention_timeline_id": int, "performed_by": user_id }
    """
    try:
        data = request.data
        timeline_id = data.get('retention_timeline_id')
        performed_by_id = data.get('performed_by')

        if not timeline_id:
            return Response({'status': 'error', 'message': 'retention_timeline_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        timeline = get_object_or_404(RetentionTimeline, RetentionTimelineId=timeline_id)
        user_obj = _get_user(performed_by_id) if performed_by_id else None

        before_status = timeline.Status
        timeline.resume_deletion()

        DataLifecycleAuditLog.log_action(
            action_type='RESUME',
            record_type=timeline.RecordType,
            record_id=timeline.RecordId,
            record_name=timeline.RecordName,
            timeline=timeline,
            performed_by=user_obj,
            before_status=before_status,
            after_status=timeline.Status
        )

        return Response({'status': 'success', 'message': 'Deletion resumed', 'data': {
            'retention_timeline_id': timeline.RetentionTimelineId,
            'status': timeline.Status,
            'deletion_paused': timeline.deletion_paused,
            'pause_reason': timeline.pause_reason,
            'pause_until': timeline.pause_until,
        }}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error resuming deletion: {str(e)}")
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================================
# EXTEND RETENTION
# =====================================================

@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def extend_retention(request):
    """
    Extend retention end date for a record.
    Body: { "retention_timeline_id": int, "extra_days": int, "reason": str, "performed_by": user_id }
    """
    try:
        data = request.data
        timeline_id = data.get('retention_timeline_id')
        extra_days = int(data.get('extra_days', 0) or 0)
        reason = data.get('reason')
        performed_by_id = data.get('performed_by')

        if not timeline_id:
            return Response({'status': 'error', 'message': 'retention_timeline_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if extra_days <= 0:
            return Response({'status': 'error', 'message': 'extra_days must be > 0'}, status=status.HTTP_400_BAD_REQUEST)

        timeline = get_object_or_404(RetentionTimeline, RetentionTimelineId=timeline_id)
        user_obj = _get_user(performed_by_id) if performed_by_id else None

        before_status = timeline.Status
        before_end_date = timeline.RetentionEndDate

        timeline.extend_retention(extra_days=extra_days)

        # Keep underlying record's retentionExpiry in sync
        _update_record_retentionExpiry_from_timeline = _update_record_retention_expiry_from_timeline  # alias for linting
        _update_record_retentionExpiry_from_timeline(timeline)

        DataLifecycleAuditLog.log_action(
            action_type='EXTEND',
            record_type=timeline.RecordType,
            record_id=timeline.RecordId,
            record_name=timeline.RecordName,
            timeline=timeline,
            performed_by=user_obj,
            before_status=before_status,
            after_status=timeline.Status,
            reason=reason,
            details={
                'previous_end_date': before_end_date.isoformat(),
                'new_end_date': timeline.RetentionEndDate.isoformat(),
                'extra_days': extra_days
            }
        )

        return Response({'status': 'success', 'message': 'Retention extended', 'data': {
            'retention_timeline_id': timeline.RetentionTimelineId,
            'status': timeline.Status,
            'retention_end_date': timeline.RetentionEndDate,
        }}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error extending retention: {str(e)}")
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================================
# DASHBOARD DATA ENDPOINTS
# =====================================================

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def retention_dashboard_overview(request):
    """
    Overview counts for retention dashboard.
    """
    today = timezone.now().date()
    active_qs = RetentionTimeline.objects.filter(Status='Active')
    archived_qs = RetentionTimeline.objects.filter(is_archived=True)
    paused_qs = RetentionTimeline.objects.filter(deletion_paused=True)
    disposed_qs = RetentionTimeline.objects.filter(Status='Disposed')

    expiring_days = int(request.GET.get('expiring_days', 30) or 30)
    expiring_qs = active_qs.filter(
        RetentionEndDate__gte=today,
        RetentionEndDate__lte=today + timedelta(days=expiring_days),
        is_archived=False,
        deletion_paused=False,
        auto_delete_enabled=True
    )

    return Response({
        'status': 'success',
        'data': {
            'active': active_qs.count(),
            'expiring': expiring_qs.count(),
            'archived': archived_qs.count(),
            'paused': paused_qs.count(),
            'disposed': disposed_qs.count(),
        }
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def retention_dashboard_expiring(request):
    """
    List expiring records within given days (default 30).
    Query params: days (int), limit (int)
    """
    today = timezone.now().date()
    days = int(request.GET.get('days', 30) or 30)
    limit = int(request.GET.get('limit', 100) or 100)

    qs = RetentionTimeline.objects.filter(
        Status='Active',
        RetentionEndDate__gte=today,
        RetentionEndDate__lte=today + timedelta(days=days),
        is_archived=False,
        deletion_paused=False,
        auto_delete_enabled=True
    ).order_by('RetentionEndDate')[:limit]

    data = [
        {
            'id': t.RetentionTimelineId,
            'record_type': t.RecordType,
            'record_id': t.RecordId,
            'record_name': t.RecordName,
            'status': t.Status,
            'retention_end_date': t.RetentionEndDate,
            'days_until_expiry': t.days_until_expiry,
        } for t in qs
    ]

    return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def retention_dashboard_archived(request):
    """
    List archived records.
    Query params: limit (int)
    """
    limit = int(request.GET.get('limit', 100) or 100)
    qs = RetentionTimeline.objects.filter(is_archived=True).order_by('-archived_date')[:limit]
    data = [
        {
            'id': t.RetentionTimelineId,
            'record_type': t.RecordType,
            'record_id': t.RecordId,
            'record_name': t.RecordName,
            'status': t.Status,
            'archived_date': t.archived_date,
            'archive_location': t.archive_location,
        } for t in qs
    ]
    return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def retention_dashboard_paused(request):
    """
    List records with deletion paused.
    Query params: limit (int)
    """
    limit = int(request.GET.get('limit', 100) or 100)
    qs = RetentionTimeline.objects.filter(deletion_paused=True).order_by('-UpdatedAt')[:limit]
    data = [
        {
            'id': t.RetentionTimelineId,
            'record_type': t.RecordType,
            'record_id': t.RecordId,
            'record_name': t.RecordName,
            'status': t.Status,
            'pause_reason': t.pause_reason,
            'pause_until': t.pause_until,
            'updated_at': t.UpdatedAt,
        } for t in qs
    ]
    return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def retention_dashboard_audit_trail(request):
    """
    Audit trail feed.
    Query params: record_type, record_id, limit
    """
    record_type = request.GET.get('record_type')
    record_id = request.GET.get('record_id')
    limit = int(request.GET.get('limit', 100) or 100)

    qs = DataLifecycleAuditLog.objects.all().order_by('-timestamp')
    if record_type:
        qs = qs.filter(record_type=record_type)
    if record_id:
        qs = qs.filter(record_id=record_id)

    qs = qs[:limit]
    data = [
        {
            'id': log.id,
            'action_type': log.action_type,
            'record_type': log.record_type,
            'record_id': log.record_id,
            'record_name': log.record_name,
            'before_status': log.before_status,
            'after_status': log.after_status,
            'reason': log.reason,
            'details': log.details,
            'notification_recipients': log.notification_recipients,
            'backup_id': log.backup_id,
            'performed_by': log.performed_by_id,
            'timestamp': log.timestamp,
        } for log in qs
    ]

    return Response({'status': 'success', 'data': data}, status=status.HTTP_200_OK)
