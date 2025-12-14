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
from ...models import (
    RetentionModulePageConfig,
    Users, Framework, RBAC
)
from django.db.models import Q
from datetime import timedelta
import logging
import json

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
# RETENTION POLICY VIEWS
# =====================================================

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_retention_policies(request):
    """List all retention policies"""
    try:
        framework_id = request.GET.get('framework_id')
        status_filter = request.GET.get('status')
        retention_type = request.GET.get('retention_type')
        
        policies = RetentionPolicy.objects.all()
        
        if framework_id:
            policies = policies.filter(FrameworkId=framework_id)
        if status_filter:
            policies = policies.filter(Status=status_filter)
        if retention_type:
            policies = policies.filter(RetentionType=retention_type)
        
        policies_list = []
        for policy in policies:
            policies_list.append({
                'retention_policy_id': policy.RetentionPolicyId,
                'policy_name': policy.PolicyName,
                'policy_description': policy.PolicyDescription,
                'retention_type': policy.RetentionType,
                'retention_period_years': policy.RetentionPeriodYears,
                'retention_period_months': policy.RetentionPeriodMonths,
                'retention_period_days': policy.RetentionPeriodDays,
                'total_retention_days': policy.total_retention_days,
                'status': policy.Status,
                'framework_id': policy.FrameworkId.FrameworkId,
                'framework_name': policy.FrameworkId.FrameworkName,
                'applicable_to': policy.ApplicableTo,
                'legal_basis': policy.LegalBasis,
                'regulatory_requirements': policy.RegulatoryRequirements,
                'disposal_method': policy.DisposalMethod,
                'review_frequency': policy.ReviewFrequency,
                'last_reviewed_date': policy.LastReviewedDate.isoformat() if policy.LastReviewedDate else None,
                'next_review_date': policy.NextReviewDate.isoformat() if policy.NextReviewDate else None,
                'created_by': policy.CreatedBy.UserName if policy.CreatedBy else None,
                'created_at': policy.CreatedAt.isoformat(),
                'updated_at': policy.UpdatedAt.isoformat(),
            })
        
        return Response({
            'status': 'success',
            'data': policies_list,
            'count': len(policies_list)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing retention policies: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_retention_policy(request, policy_id):
    """Get a specific retention policy"""
    try:
        policy = get_object_or_404(RetentionPolicy, RetentionPolicyId=policy_id)
        
        data = {
            'retention_policy_id': policy.RetentionPolicyId,
            'policy_name': policy.PolicyName,
            'policy_description': policy.PolicyDescription,
            'retention_type': policy.RetentionType,
            'retention_period_years': policy.RetentionPeriodYears,
            'retention_period_months': policy.RetentionPeriodMonths,
            'retention_period_days': policy.RetentionPeriodDays,
            'total_retention_days': policy.total_retention_days,
            'status': policy.Status,
            'framework_id': policy.FrameworkId.FrameworkId,
            'framework_name': policy.FrameworkId.FrameworkName,
            'applicable_to': policy.ApplicableTo,
            'legal_basis': policy.LegalBasis,
            'regulatory_requirements': policy.RegulatoryRequirements,
            'disposal_method': policy.DisposalMethod,
            'review_frequency': policy.ReviewFrequency,
            'last_reviewed_date': policy.LastReviewedDate.isoformat() if policy.LastReviewedDate else None,
            'next_review_date': policy.NextReviewDate.isoformat() if policy.NextReviewDate else None,
            'created_by': policy.CreatedBy.UserName if policy.CreatedBy else None,
            'created_at': policy.CreatedAt.isoformat(),
            'updated_at': policy.UpdatedAt.isoformat(),
        }
        
        return Response({
            'status': 'success',
            'data': data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting retention policy: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_retention_policy(request):
    """Create a new retention policy"""
    try:
        user_id = request.user.UserId if hasattr(request.user, 'UserId') else None
        if not user_id:
            user_id = request.session.get('user_id') or request.data.get('user_id')
        
        data = request.data

        # Helper to safely parse date strings (YYYY-MM-DD) or return None
        def parse_date(value):
            from datetime import datetime
            if not value:
                return None
            if isinstance(value, str):
                try:
                    return datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError:
                    return None
            return value

        with transaction.atomic():
            policy = RetentionPolicy.objects.create(
                PolicyName=data.get('policy_name'),
                PolicyDescription=data.get('policy_description'),
                RetentionType=data.get('retention_type', 'Other'),
                RetentionPeriodYears=data.get('retention_period_years'),
                RetentionPeriodMonths=data.get('retention_period_months'),
                RetentionPeriodDays=data.get('retention_period_days'),
                Status=data.get('status', 'Draft'),
                FrameworkId_id=data.get('framework_id'),
                ApplicableTo=data.get('applicable_to', []),
                LegalBasis=data.get('legal_basis'),
                RegulatoryRequirements=data.get('regulatory_requirements'),
                DisposalMethod=data.get('disposal_method'),
                ReviewFrequency=data.get('review_frequency'),
                LastReviewedDate=parse_date(data.get('last_reviewed_date')),
                NextReviewDate=parse_date(data.get('next_review_date')),
                CreatedBy_id=user_id,
            )
            
            return Response({
                'status': 'success',
                'message': 'Retention policy created successfully',
                'data': {
                    'retention_policy_id': policy.RetentionPolicyId,
                    'policy_name': policy.PolicyName,
                }
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error creating retention policy: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_retention_policy(request, policy_id):
    """Update a retention policy"""
    try:
        user_id = request.user.UserId if hasattr(request.user, 'UserId') else None
        if not user_id:
            user_id = request.session.get('user_id') or request.data.get('user_id')
        
        policy = get_object_or_404(RetentionPolicy, RetentionPolicyId=policy_id)
        data = request.data
        
        with transaction.atomic():
            if 'policy_name' in data:
                policy.PolicyName = data['policy_name']
            if 'policy_description' in data:
                policy.PolicyDescription = data.get('policy_description')
            if 'retention_type' in data:
                policy.RetentionType = data['retention_type']
            if 'retention_period_years' in data:
                policy.RetentionPeriodYears = data.get('retention_period_years')
            if 'retention_period_months' in data:
                policy.RetentionPeriodMonths = data.get('retention_period_months')
            if 'retention_period_days' in data:
                policy.RetentionPeriodDays = data.get('retention_period_days')
            if 'status' in data:
                policy.Status = data['status']
            if 'applicable_to' in data:
                policy.ApplicableTo = data['applicable_to']
            if 'legal_basis' in data:
                policy.LegalBasis = data.get('legal_basis')
            if 'regulatory_requirements' in data:
                policy.RegulatoryRequirements = data.get('regulatory_requirements')
            if 'disposal_method' in data:
                policy.DisposalMethod = data.get('disposal_method')
            if 'review_frequency' in data:
                policy.ReviewFrequency = data.get('review_frequency')
            if 'last_reviewed_date' in data:
                policy.LastReviewedDate = data.get('last_reviewed_date')
            if 'next_review_date' in data:
                policy.NextReviewDate = data.get('next_review_date')
            
            policy.UpdatedBy_id = user_id
            policy.save()
            
            return Response({
                'status': 'success',
                'message': 'Retention policy updated successfully',
                'data': {
                    'retention_policy_id': policy.RetentionPolicyId,
                    'policy_name': policy.PolicyName,
                }
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error updating retention policy: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_retention_policy(request, policy_id):
    """Delete a retention policy"""
    try:
        policy = get_object_or_404(RetentionPolicy, RetentionPolicyId=policy_id)
        policy_name = policy.PolicyName
        
        with transaction.atomic():
            policy.delete()
            
            return Response({
                'status': 'success',
                'message': f'Retention policy "{policy_name}" deleted successfully'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error deleting retention policy: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================================
# RETENTION TIMELINE VIEWS
# =====================================================

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_retention_timelines(request):
    """List all retention timelines"""
    try:
        framework_id = request.GET.get('framework_id')
        status_filter = request.GET.get('status')
        record_type = request.GET.get('record_type')
        record_id = request.GET.get('record_id')
        policy_id = request.GET.get('retention_policy_id')
        expired_only = request.GET.get('expired_only', 'false').lower() == 'true'
        
        timelines = RetentionTimeline.objects.all()
        
        if framework_id:
            timelines = timelines.filter(FrameworkId=framework_id)
        if status_filter:
            timelines = timelines.filter(Status=status_filter)
        if record_type:
            timelines = timelines.filter(RecordType=record_type)
        if record_id:
            timelines = timelines.filter(RecordId=record_id)
        if policy_id:
            timelines = timelines.filter(RetentionPolicy_id=policy_id)
        if expired_only:
            today = timezone.now().date()
            timelines = timelines.filter(RetentionEndDate__lt=today, Status='Active')
        
        timelines_list = []
        for timeline in timelines:
            timelines_list.append({
                'retention_timeline_id': timeline.RetentionTimelineId,
                'retention_policy_id': timeline.RetentionPolicy.RetentionPolicyId,
                'retention_policy_name': timeline.RetentionPolicy.PolicyName,
                'record_type': timeline.RecordType,
                'record_id': timeline.RecordId,
                'record_name': timeline.RecordName,
                'created_date': timeline.CreatedDate.isoformat(),
                'retention_start_date': timeline.RetentionStartDate.isoformat(),
                'retention_end_date': timeline.RetentionEndDate.isoformat(),
                'status': timeline.Status,
                'is_expired': timeline.is_expired,
                'days_until_expiry': timeline.days_until_expiry,
                'disposal_date': timeline.DisposalDate.isoformat() if timeline.DisposalDate else None,
                'disposal_method': timeline.DisposalMethod,
                'disposal_confirmation': timeline.DisposalConfirmation,
                'extension_reason': timeline.ExtensionReason,
                'extended_until': timeline.ExtendedUntil.isoformat() if timeline.ExtendedUntil else None,
                'framework_id': timeline.FrameworkId.FrameworkId,
                'framework_name': timeline.FrameworkId.FrameworkName,
                'created_by': timeline.CreatedBy.UserName if timeline.CreatedBy else None,
                'created_at': timeline.CreatedAt.isoformat(),
                'updated_at': timeline.UpdatedAt.isoformat(),
            })
        
        return Response({
            'status': 'success',
            'data': timelines_list,
            'count': len(timelines_list)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing retention timelines: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_retention_timeline(request):
    """Create a new retention timeline"""
    try:
        user_id = request.user.UserId if hasattr(request.user, 'UserId') else None
        if not user_id:
            user_id = request.session.get('user_id') or request.data.get('user_id')
        
        data = request.data
        
        # Get the retention policy to calculate end date
        policy = get_object_or_404(RetentionPolicy, RetentionPolicyId=data.get('retention_policy_id'))
        
        # Calculate retention end date
        start_date = data.get('retention_start_date') or data.get('created_date')
        if isinstance(start_date, str):
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        end_date = start_date
        if policy.RetentionPeriodYears:
            end_date += timedelta(days=policy.RetentionPeriodYears * 365)
        if policy.RetentionPeriodMonths:
            end_date += timedelta(days=policy.RetentionPeriodMonths * 30)
        if policy.RetentionPeriodDays:
            end_date += timedelta(days=policy.RetentionPeriodDays)
        
        with transaction.atomic():
            timeline = RetentionTimeline.objects.create(
                RetentionPolicy_id=data.get('retention_policy_id'),
                RecordType=data.get('record_type'),
                RecordId=data.get('record_id'),
                RecordName=data.get('record_name'),
                CreatedDate=data.get('created_date'),
                RetentionStartDate=start_date,
                RetentionEndDate=end_date,
                Status='Active',
                FrameworkId_id=data.get('framework_id'),
                CreatedBy_id=user_id,
            )
            
            return Response({
                'status': 'success',
                'message': 'Retention timeline created successfully',
                'data': {
                    'retention_timeline_id': timeline.RetentionTimelineId,
                    'retention_end_date': timeline.RetentionEndDate.isoformat(),
                }
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error creating retention timeline: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_retention_timeline(request, timeline_id):
    """Update a retention timeline"""
    try:
        user_id = request.user.UserId if hasattr(request.user, 'UserId') else None
        if not user_id:
            user_id = request.session.get('user_id') or request.data.get('user_id')
        
        timeline = get_object_or_404(RetentionTimeline, RetentionTimelineId=timeline_id)
        data = request.data
        
        with transaction.atomic():
            if 'status' in data:
                timeline.Status = data['status']
            if 'disposal_date' in data:
                timeline.DisposalDate = data.get('disposal_date')
            if 'disposal_method' in data:
                timeline.DisposalMethod = data.get('disposal_method')
            if 'disposal_confirmation' in data:
                timeline.DisposalConfirmation = data.get('disposal_confirmation')
            if 'extension_reason' in data:
                timeline.ExtensionReason = data.get('extension_reason')
            if 'extended_until' in data:
                timeline.ExtendedUntil = data.get('extended_until')
                if data.get('extended_until'):
                    timeline.Status = 'Extended'
            
            timeline.UpdatedBy_id = user_id
            timeline.save()
            
            return Response({
                'status': 'success',
                'message': 'Retention timeline updated successfully'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error updating retention timeline: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================================
# DATA PROCESSING AGREEMENT VIEWS
# =====================================================

@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_data_processing_agreements(request):
    """List all data processing agreements"""
    try:
        framework_id = request.GET.get('framework_id')
        status_filter = request.GET.get('status')
        expired_only = request.GET.get('expired_only', 'false').lower() == 'true'
        
        agreements = DataProcessingAgreement.objects.all()
        
        if framework_id:
            agreements = agreements.filter(FrameworkId=framework_id)
        if status_filter:
            agreements = agreements.filter(Status=status_filter)
        if expired_only:
            today = timezone.now().date()
            agreements = agreements.filter(ExpiryDate__lt=today, Status='Active')
        
        agreements_list = []
        for agreement in agreements:
            agreements_list.append({
                'dpa_id': agreement.DPAId,
                'agreement_name': agreement.AgreementName,
                'agreement_number': agreement.AgreementNumber,
                'description': agreement.Description,
                'data_controller': agreement.DataController,
                'data_processor': agreement.DataProcessor,
                'processor_contact': agreement.ProcessorContact,
                'processor_email': agreement.ProcessorEmail,
                'effective_date': agreement.EffectiveDate.isoformat(),
                'expiry_date': agreement.ExpiryDate.isoformat() if agreement.ExpiryDate else None,
                'status': agreement.Status,
                'is_expired': agreement.is_expired,
                'days_until_expiry': agreement.days_until_expiry,
                'framework_id': agreement.FrameworkId.FrameworkId,
                'framework_name': agreement.FrameworkId.FrameworkName,
                'purpose_of_processing': agreement.PurposeOfProcessing,
                'types_of_data': agreement.TypesOfData,
                'data_subjects': agreement.DataSubjects,
                'security_measures': agreement.SecurityMeasures,
                'data_retention': agreement.DataRetention,
                'data_transfer': agreement.DataTransfer,
                'sub_processors': agreement.SubProcessors,
                'breach_notification': agreement.BreachNotification,
                'audit_rights': agreement.AuditRights,
                'document_url': agreement.DocumentURL,
                'review_frequency': agreement.ReviewFrequency,
                'last_reviewed_date': agreement.LastReviewedDate.isoformat() if agreement.LastReviewedDate else None,
                'next_review_date': agreement.NextReviewDate.isoformat() if agreement.NextReviewDate else None,
                'created_by': agreement.CreatedBy.UserName if agreement.CreatedBy else None,
                'created_at': agreement.CreatedAt.isoformat(),
                'updated_at': agreement.UpdatedAt.isoformat(),
            })
        
        return Response({
            'status': 'success',
            'data': agreements_list,
            'count': len(agreements_list)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing data processing agreements: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_data_processing_agreement(request, dpa_id):
    """Get a specific data processing agreement"""
    try:
        agreement = get_object_or_404(DataProcessingAgreement, DPAId=dpa_id)
        
        data = {
            'dpa_id': agreement.DPAId,
            'agreement_name': agreement.AgreementName,
            'agreement_number': agreement.AgreementNumber,
            'description': agreement.Description,
            'data_controller': agreement.DataController,
            'data_processor': agreement.DataProcessor,
            'processor_contact': agreement.ProcessorContact,
            'processor_email': agreement.ProcessorEmail,
            'effective_date': agreement.EffectiveDate.isoformat(),
            'expiry_date': agreement.ExpiryDate.isoformat() if agreement.ExpiryDate else None,
            'status': agreement.Status,
            'is_expired': agreement.is_expired,
            'days_until_expiry': agreement.days_until_expiry,
            'framework_id': agreement.FrameworkId.FrameworkId,
            'framework_name': agreement.FrameworkId.FrameworkName,
            'purpose_of_processing': agreement.PurposeOfProcessing,
            'types_of_data': agreement.TypesOfData,
            'data_subjects': agreement.DataSubjects,
            'security_measures': agreement.SecurityMeasures,
            'data_retention': agreement.DataRetention,
            'data_transfer': agreement.DataTransfer,
            'sub_processors': agreement.SubProcessors,
            'breach_notification': agreement.BreachNotification,
            'audit_rights': agreement.AuditRights,
            'document_url': agreement.DocumentURL,
            'review_frequency': agreement.ReviewFrequency,
            'last_reviewed_date': agreement.LastReviewedDate.isoformat() if agreement.LastReviewedDate else None,
            'next_review_date': agreement.NextReviewDate.isoformat() if agreement.NextReviewDate else None,
            'created_by': agreement.CreatedBy.UserName if agreement.CreatedBy else None,
            'created_at': agreement.CreatedAt.isoformat(),
            'updated_at': agreement.UpdatedAt.isoformat(),
        }
        
        return Response({
            'status': 'success',
            'data': data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting data processing agreement: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_data_processing_agreement(request):
    """Create a new data processing agreement"""
    try:
        user_id = request.user.UserId if hasattr(request.user, 'UserId') else None
        if not user_id:
            user_id = request.session.get('user_id') or request.data.get('user_id')
        
        data = request.data
        
        with transaction.atomic():
            agreement = DataProcessingAgreement.objects.create(
                AgreementName=data.get('agreement_name'),
                AgreementNumber=data.get('agreement_number'),
                Description=data.get('description'),
                DataController=data.get('data_controller'),
                DataProcessor=data.get('data_processor'),
                ProcessorContact=data.get('processor_contact'),
                ProcessorEmail=data.get('processor_email'),
                EffectiveDate=data.get('effective_date'),
                ExpiryDate=data.get('expiry_date'),
                Status=data.get('status', 'Draft'),
                FrameworkId_id=data.get('framework_id'),
                PurposeOfProcessing=data.get('purpose_of_processing'),
                TypesOfData=data.get('types_of_data'),
                DataSubjects=data.get('data_subjects'),
                SecurityMeasures=data.get('security_measures'),
                DataRetention=data.get('data_retention'),
                DataTransfer=data.get('data_transfer'),
                SubProcessors=data.get('sub_processors', []),
                BreachNotification=data.get('breach_notification'),
                AuditRights=data.get('audit_rights'),
                DocumentURL=data.get('document_url'),
                ReviewFrequency=data.get('review_frequency'),
                LastReviewedDate=data.get('last_reviewed_date'),
                NextReviewDate=data.get('next_review_date'),
                CreatedBy_id=user_id,
            )
            
            return Response({
                'status': 'success',
                'message': 'Data processing agreement created successfully',
                'data': {
                    'dpa_id': agreement.DPAId,
                    'agreement_name': agreement.AgreementName,
                }
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error creating data processing agreement: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_data_processing_agreement(request, dpa_id):
    """Update a data processing agreement"""
    try:
        user_id = request.user.UserId if hasattr(request.user, 'UserId') else None
        if not user_id:
            user_id = request.session.get('user_id') or request.data.get('user_id')
        
        agreement = get_object_or_404(DataProcessingAgreement, DPAId=dpa_id)
        data = request.data
        
        with transaction.atomic():
            field_mapping = {
                'agreement_name': 'AgreementName',
                'agreement_number': 'AgreementNumber',
                'description': 'Description',
                'data_controller': 'DataController',
                'data_processor': 'DataProcessor',
                'processor_contact': 'ProcessorContact',
                'processor_email': 'ProcessorEmail',
                'effective_date': 'EffectiveDate',
                'expiry_date': 'ExpiryDate',
                'status': 'Status',
                'purpose_of_processing': 'PurposeOfProcessing',
                'types_of_data': 'TypesOfData',
                'data_subjects': 'DataSubjects',
                'security_measures': 'SecurityMeasures',
                'data_retention': 'DataRetention',
                'data_transfer': 'DataTransfer',
                'sub_processors': 'SubProcessors',
                'breach_notification': 'BreachNotification',
                'audit_rights': 'AuditRights',
                'document_url': 'DocumentURL',
                'review_frequency': 'ReviewFrequency',
                'last_reviewed_date': 'LastReviewedDate',
                'next_review_date': 'NextReviewDate'
            }
            
            for field, model_field in field_mapping.items():
                if field in data:
                    setattr(agreement, model_field, data[field])
            
            agreement.UpdatedBy_id = user_id
            agreement.save()
            
            return Response({
                'status': 'success',
                'message': 'Data processing agreement updated successfully'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error updating data processing agreement: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_data_processing_agreement(request, dpa_id):
    """Delete a data processing agreement"""
    try:
        agreement = get_object_or_404(DataProcessingAgreement, DPAId=dpa_id)
        agreement_name = agreement.AgreementName
        
        with transaction.atomic():
            agreement.delete()
            
            return Response({
                'status': 'success',
                'message': f'Data processing agreement "{agreement_name}" deleted successfully'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error deleting data processing agreement: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
}


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
            if not module_key or module_key not in MODULE_PAGES:
                continue
            if not page_key or page_key not in MODULE_PAGES[module_key]:
                continue
            enabled = bool(cfg.get('enabled', False))
            retention_days = int(cfg.get('retention_days', DEFAULT_RETENTION_DAYS) or DEFAULT_RETENTION_DAYS)
            ensure_defaults_for_module(module_key)
            obj, _ = RetentionModulePageConfig.objects.get_or_create(
                module=module_key,
                sub_page=page_key,
                defaults={'checklist_status': enabled, 'retention_days': retention_days}
            )
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
