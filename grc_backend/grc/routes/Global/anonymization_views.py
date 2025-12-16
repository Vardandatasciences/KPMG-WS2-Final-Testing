"""
API endpoints for on-demand data anonymization and masking.
Provides endpoints to anonymize data in logs, exports, and analytics.
"""

import json
import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from ...models import GRCLog, Framework
from .data_masking import get_masking_service, mask_dict, mask_email, mask_phone, mask_address, mask_name, mask_user_id
from ...rbac.utils import RBACUtils

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def anonymize_logs(request):
    """
    Anonymize sensitive data in logs.
    POST /api/anonymize/logs/
    
    Body:
    {
        "log_ids": [1, 2, 3],  # Optional: specific log IDs to anonymize
        "fields": ["email", "phone", "address", "name"],  # Optional: fields to mask
        "date_from": "2024-01-01",  # Optional: start date
        "date_to": "2024-12-31"  # Optional: end date
    }
    """
    try:
        # Check if user is GRC Administrator
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not RBACUtils.is_system_admin(user_id):
            return Response({
                'success': False,
                'message': 'Only GRC Administrators can anonymize logs'
            }, status=status.HTTP_403_FORBIDDEN)
        
        data = request.data
        log_ids = data.get('log_ids', [])
        fields_to_mask = data.get('fields', ['email', 'phone', 'address', 'name', 'userId'])
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        masking_service = get_masking_service()
        
        # Build query
        logs_query = GRCLog.objects.all()
        
        if log_ids:
            logs_query = logs_query.filter(LogId__in=log_ids)
        
        if date_from:
            logs_query = logs_query.filter(Timestamp__gte=date_from)
        
        if date_to:
            logs_query = logs_query.filter(Timestamp__lte=date_to)
        
        # Anonymize logs
        anonymized_count = 0
        for log in logs_query:
            updated = False
            
            # Mask UserName
            if 'name' in fields_to_mask and log.UserName:
                log.UserName = masking_service.mask_name(log.UserName)
                updated = True
            
            # Mask UserId
            if 'userId' in fields_to_mask and log.UserId:
                log.UserId = masking_service.mask_user_id(log.UserId)
                updated = True
            
            # Mask Description
            if log.Description:
                desc = log.Description
                if 'email' in fields_to_mask:
                    desc = masking_service._mask_sensitive_in_text(desc)
                if 'phone' in fields_to_mask:
                    desc = masking_service._mask_sensitive_in_text(desc)
                if desc != log.Description:
                    log.Description = desc
                    updated = True
            
            # Mask AdditionalInfo
            if log.AdditionalInfo:
                if isinstance(log.AdditionalInfo, str):
                    try:
                        additional_info = json.loads(log.AdditionalInfo)
                        masked_info = masking_service.mask_dict(additional_info, fields_to_mask)
                        log.AdditionalInfo = masked_info
                        updated = True
                    except (json.JSONDecodeError, TypeError):
                        pass
                elif isinstance(log.AdditionalInfo, dict):
                    masked_info = masking_service.mask_dict(log.AdditionalInfo, fields_to_mask)
                    log.AdditionalInfo = masked_info
                    updated = True
            
            if updated:
                log.save()
                anonymized_count += 1
        
        # Log the anonymization activity
        try:
            framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
            if framework:
                audit_log = GRCLog(
                    UserId=str(user_id),
                    UserName=RBACUtils.get_user_rbac_record(user_id).username if RBACUtils.get_user_rbac_record(user_id) else 'System',
                    Module='Data Anonymization',
                    ActionType='ANONYMIZE_LOGS',
                    EntityType='Logs',
                    LogLevel='INFO',
                    Description=f'Anonymized {anonymized_count} log entries',
                    AdditionalInfo={
                        'fields_masked': fields_to_mask,
                        'log_ids': log_ids if log_ids else 'all',
                        'date_range': {'from': date_from, 'to': date_to} if date_from or date_to else None
                    },
                    FrameworkId=framework
                )
                audit_log.save()
        except Exception as audit_error:
            logger.error(f"Failed to log anonymization activity: {str(audit_error)}")
        
        return Response({
            'success': True,
            'message': f'Successfully anonymized {anonymized_count} log entries',
            'anonymized_count': anonymized_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error anonymizing logs: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': f'Failed to anonymize logs: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def anonymize_data(request):
    """
    Anonymize sensitive data in a provided dataset.
    POST /api/anonymize/data/
    
    Body:
    {
        "data": {
            "email": "john@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "name": "John Doe"
        },
        "fields": ["email", "phone", "address", "name"]  # Optional
    }
    """
    try:
        # Check if user is GRC Administrator
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not RBACUtils.is_system_admin(user_id):
            return Response({
                'success': False,
                'message': 'Only GRC Administrators can anonymize data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        data = request.data
        input_data = data.get('data', {})
        fields_to_mask = data.get('fields', ['email', 'phone', 'address', 'name', 'userId'])
        
        masking_service = get_masking_service()
        
        # Anonymize the data
        if isinstance(input_data, dict):
            anonymized_data = masking_service.mask_dict(input_data, fields_to_mask)
        elif isinstance(input_data, list):
            anonymized_data = [masking_service.mask_dict(item, fields_to_mask) if isinstance(item, dict) else item for item in input_data]
        else:
            anonymized_data = input_data
        
        # Log the anonymization activity
        try:
            framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
            if framework:
                audit_log = GRCLog(
                    UserId=str(user_id),
                    UserName=RBACUtils.get_user_rbac_record(user_id).username if RBACUtils.get_user_rbac_record(user_id) else 'System',
                    Module='Data Anonymization',
                    ActionType='ANONYMIZE_DATA',
                    EntityType='Data',
                    LogLevel='INFO',
                    Description='Data anonymized on-demand',
                    AdditionalInfo={
                        'fields_masked': fields_to_mask,
                        'data_type': type(input_data).__name__
                    },
                    FrameworkId=framework
                )
                audit_log.save()
        except Exception as audit_error:
            logger.error(f"Failed to log anonymization activity: {str(audit_error)}")
        
        return Response({
            'success': True,
            'message': 'Data anonymized successfully',
            'anonymized_data': anonymized_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error anonymizing data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': f'Failed to anonymize data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_anonymization_config(request):
    """
    Get anonymization configuration and available methods.
    GET /api/anonymize/config/
    """
    try:
        # Check if user is authenticated
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        config = {
            'available_methods': {
                'email': 'Email masking (e.g., jo******@ex*****.com)',
                'phone': 'Phone masking (e.g., 99405*****)',
                'address': 'Address masking (e.g., 123 M*** S******)',
                'name': 'Name masking (e.g., J***)',
                'userId': 'User ID pseudonymization (reversible with key)'
            },
            'masking_character': '*',
            'default_fields': ['email', 'phone', 'address', 'name', 'userId'],
            'reversible': {
                'userId': True,  # Pseudonymization is reversible with key
                'email': False,
                'phone': False,
                'address': False,
                'name': False
            }
        }
        
        return Response({
            'success': True,
            'config': config
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting anonymization config: {str(e)}")
        return Response({
            'success': False,
            'message': f'Failed to get config: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

