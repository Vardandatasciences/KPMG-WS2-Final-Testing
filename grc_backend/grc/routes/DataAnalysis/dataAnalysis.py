from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from grc.models import Policy, Compliance, Audit, Incident, Risk, RiskInstance, Event
import json


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_data_analysis(request):
    """
    Get data inventory analysis for all modules.
    Returns percentage breakdown of personal, regular, and confidential data for each module.
    """
    try:
        framework_id = request.query_params.get('framework_id', None)
        
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
                                    personal_columns.add(key)
                                elif value_lower == 'regular':
                                    regular_count += 1
                                    regular_columns.add(key)
                                elif value_lower == 'confidential':
                                    confidential_count += 1
                                    confidential_columns.add(key)
            
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
        policy_queryset = Policy.objects.filter(filter_query)
        results['policy'] = analyze_data_inventory(policy_queryset)
        
        # Compliance Module
        compliance_queryset = Compliance.objects.filter(filter_query)
        results['compliance'] = analyze_data_inventory(compliance_queryset)
        
        # Audit Module
        audit_queryset = Audit.objects.filter(filter_query)
        results['audit'] = analyze_data_inventory(audit_queryset)
        
        # Incident Module
        incident_queryset = Incident.objects.filter(filter_query)
        results['incident'] = analyze_data_inventory(incident_queryset)
        
        # Risk Module - Combine Risk and RiskInstance
        risk_queryset = Risk.objects.filter(filter_query)
        risk_instance_queryset = RiskInstance.objects.filter(filter_query)
        
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
                                risk_personal_columns.add(key)
                            elif value_lower == 'regular':
                                risk_regular += 1
                                risk_regular_columns.add(key)
                            elif value_lower == 'confidential':
                                risk_confidential += 1
                                risk_confidential_columns.add(key)
        
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
                                risk_personal_columns.add(key)
                            elif value_lower == 'regular':
                                risk_regular += 1
                                risk_regular_columns.add(key)
                            elif value_lower == 'confidential':
                                risk_confidential += 1
                                risk_confidential_columns.add(key)
        
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
        event_queryset = Event.objects.filter(filter_query)
        results['event'] = analyze_data_inventory(event_queryset)
        
        return Response({
            'status': 'success',
            'data': results
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

