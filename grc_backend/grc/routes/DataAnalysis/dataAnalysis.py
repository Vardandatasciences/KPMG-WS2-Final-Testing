from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from grc.models import Policy, Compliance, Audit, Incident, Risk, RiskInstance, Event, Users
from grc.rbac.utils import RBACUtils
import json
import logging


logger = logging.getLogger(__name__)


def _sanitize_text_output(value, max_len=256):
    if value is None:
        return ''
    text = str(value)
    text = ''.join(ch for ch in text if ch == '\t' or ch == '\n' or ord(ch) >= 32).strip()
    if len(text) > max_len:
        text = text[:max_len]
    if text.startswith(('=', '+', '-', '@')):
        text = "'" + text
    return text


def _get_authenticated_user(request):
    raw_request = getattr(request, '_request', request)
    grc_user = getattr(raw_request, '_grc_user', None)
    if grc_user and hasattr(grc_user, 'UserId'):
        try:
            return Users.objects.filter(UserId=int(grc_user.UserId)).first()
        except Exception:
            return None
    resolved_user_id = RBACUtils.get_user_id_from_request(request)
    if not resolved_user_id:
        return None
    try:
        return Users.objects.filter(UserId=int(resolved_user_id)).first()
    except Exception:
        return None


def _is_system_admin(user):
    try:
        return bool(user and RBACUtils.is_system_admin(int(user.UserId)))
    except Exception:
        return False


def _scope_queryset_for_user(queryset, user, is_admin=False):
    if user is None:
        return queryset.none()
    if hasattr(queryset.model, 'tenant_id') and getattr(user, 'tenant_id', None):
        queryset = queryset.filter(tenant_id=user.tenant_id)
    if is_admin:
        return queryset
    user_framework_id = getattr(user, 'FrameworkId_id', None)
    if user_framework_id and hasattr(queryset.model, 'FrameworkId_id'):
        queryset = queryset.filter(FrameworkId_id=user_framework_id)
    return queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_data_analysis(request):
    """
    Get data inventory analysis for all modules.
    Returns percentage breakdown of personal, regular, and confidential data for each module.
    """
    try:
        current_user = _get_authenticated_user(request)
        if not current_user:
            return Response({'status': 'error', 'message': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        is_admin = _is_system_admin(current_user)
        framework_id = request.query_params.get('framework_id', None)
        logger.info(
            "DataAnalysis summary requested: actor_user_id=%s framework_id=%s",
            getattr(current_user, 'UserId', None),
            framework_id,
        )
        
        # Build filter query
        filter_query = Q()
        if framework_id and framework_id != 'all' and framework_id != 'null':
            try:
                framework_id = int(framework_id)
                filter_query = Q(FrameworkId=framework_id)
            except (ValueError, TypeError):
                pass
        
        results = {}
        
        # Helper function to analyze data_inventory JSON
        def analyze_data_inventory(queryset):
            total_count = 0
            personal_count = 0
            regular_count = 0
            confidential_count = 0
            personal_columns = set()
            regular_columns = set()
            confidential_columns = set()
            
            for record in queryset:
                data_inventory = getattr(record, 'data_inventory', None)
                if data_inventory:
                    if isinstance(data_inventory, str):
                        try:
                            data_inventory = json.loads(data_inventory)
                        except json.JSONDecodeError:
                            continue
                    
                    if isinstance(data_inventory, dict):
                        total_count += len(data_inventory)
                        for key, value in data_inventory.items():
                            if isinstance(value, str):
                                value_lower = value.lower()
                                if value_lower == 'personal':
                                    personal_count += 1
                                    personal_columns.add(_sanitize_text_output(key, max_len=120))
                                elif value_lower == 'regular':
                                    regular_count += 1
                                    regular_columns.add(_sanitize_text_output(key, max_len=120))
                                elif value_lower == 'confidential':
                                    confidential_count += 1
                                    confidential_columns.add(_sanitize_text_output(key, max_len=120))
            
            total = personal_count + regular_count + confidential_count
            if total == 0:
                return {
                    'personal': 0,
                    'regular': 0,
                    'confidential': 0,
                    'total_fields': 0,
                    'total_records': queryset.count(),
                    'columns': {
                        'personal': [],
                        'regular': [],
                        'confidential': []
                    }
                }
            
            return {
                'personal': round((personal_count / total) * 100, 2),
                'regular': round((regular_count / total) * 100, 2),
                'confidential': round((confidential_count / total) * 100, 2),
                'total_fields': total,
                'total_records': queryset.count(),
                'counts': {
                    'personal': personal_count,
                    'regular': regular_count,
                    'confidential': confidential_count
                },
                'columns': {
                    'personal': sorted(list(personal_columns)),
                    'regular': sorted(list(regular_columns)),
                    'confidential': sorted(list(confidential_columns))
                }
            }
        
        # Policy Module
        policy_queryset = _scope_queryset_for_user(Policy.objects.filter(filter_query), current_user, is_admin=is_admin)
        results['policy'] = analyze_data_inventory(policy_queryset)
        
        # Compliance Module
        compliance_queryset = _scope_queryset_for_user(Compliance.objects.filter(filter_query), current_user, is_admin=is_admin)
        results['compliance'] = analyze_data_inventory(compliance_queryset)
        
        # Audit Module
        audit_queryset = _scope_queryset_for_user(Audit.objects.filter(filter_query), current_user, is_admin=is_admin)
        results['audit'] = analyze_data_inventory(audit_queryset)
        
        # Incident Module
        incident_queryset = _scope_queryset_for_user(Incident.objects.filter(filter_query), current_user, is_admin=is_admin)
        results['incident'] = analyze_data_inventory(incident_queryset)
        
        # Risk Module - Combine Risk and RiskInstance
        risk_queryset = _scope_queryset_for_user(Risk.objects.filter(filter_query), current_user, is_admin=is_admin)
        risk_instance_queryset = _scope_queryset_for_user(RiskInstance.objects.filter(filter_query), current_user, is_admin=is_admin)
        
        # Combine both risk tables
        risk_personal = 0
        risk_regular = 0
        risk_confidential = 0
        risk_total_fields = 0
        risk_total_records = 0
        risk_personal_columns = set()
        risk_regular_columns = set()
        risk_confidential_columns = set()
        
        for record in risk_queryset:
            data_inventory = getattr(record, 'data_inventory', None)
            if data_inventory:
                if isinstance(data_inventory, str):
                    try:
                        data_inventory = json.loads(data_inventory)
                    except json.JSONDecodeError:
                        continue
                if isinstance(data_inventory, dict):
                    risk_total_records += 1
                    risk_total_fields += len(data_inventory)
                    for key, value in data_inventory.items():
                        if isinstance(value, str):
                            value_lower = value.lower()
                            if value_lower == 'personal':
                                risk_personal += 1
                                risk_personal_columns.add(_sanitize_text_output(key, max_len=120))
                            elif value_lower == 'regular':
                                risk_regular += 1
                                risk_regular_columns.add(_sanitize_text_output(key, max_len=120))
                            elif value_lower == 'confidential':
                                risk_confidential += 1
                                risk_confidential_columns.add(_sanitize_text_output(key, max_len=120))
        
        for record in risk_instance_queryset:
            data_inventory = getattr(record, 'data_inventory', None)
            if data_inventory:
                if isinstance(data_inventory, str):
                    try:
                        data_inventory = json.loads(data_inventory)
                    except json.JSONDecodeError:
                        continue
                if isinstance(data_inventory, dict):
                    risk_total_records += 1
                    risk_total_fields += len(data_inventory)
                    for key, value in data_inventory.items():
                        if isinstance(value, str):
                            value_lower = value.lower()
                            if value_lower == 'personal':
                                risk_personal += 1
                                risk_personal_columns.add(_sanitize_text_output(key, max_len=120))
                            elif value_lower == 'regular':
                                risk_regular += 1
                                risk_regular_columns.add(_sanitize_text_output(key, max_len=120))
                            elif value_lower == 'confidential':
                                risk_confidential += 1
                                risk_confidential_columns.add(_sanitize_text_output(key, max_len=120))
        
        risk_total = risk_personal + risk_regular + risk_confidential
        if risk_total == 0:
            results['risk'] = {
                'personal': 0,
                'regular': 0,
                'confidential': 0,
                'total_fields': 0,
                'total_records': risk_total_records,
                'columns': {
                    'personal': [],
                    'regular': [],
                    'confidential': []
                }
            }
        else:
            results['risk'] = {
                'personal': round((risk_personal / risk_total) * 100, 2),
                'regular': round((risk_regular / risk_total) * 100, 2),
                'confidential': round((risk_confidential / risk_total) * 100, 2),
                'total_fields': risk_total,
                'total_records': risk_total_records,
                'counts': {
                    'personal': risk_personal,
                    'regular': risk_regular,
                    'confidential': risk_confidential
                },
                'columns': {
                    'personal': sorted(list(risk_personal_columns)),
                    'regular': sorted(list(risk_regular_columns)),
                    'confidential': sorted(list(risk_confidential_columns))
                }
            }
        
        # Event Module
        event_queryset = _scope_queryset_for_user(Event.objects.filter(filter_query), current_user, is_admin=is_admin)
        results['event'] = analyze_data_inventory(event_queryset)
        
        return Response({
            'status': 'success',
            'data': results
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error("Error in get_data_analysis: %s", e, exc_info=True)
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

