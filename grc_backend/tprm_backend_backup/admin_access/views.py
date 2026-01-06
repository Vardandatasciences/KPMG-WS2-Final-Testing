"""
Views for Admin Access Control
No RBAC or MFA dependency - accessible by default for admin configuration
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.db import transaction
import logging

from .models import User, RBACTPRM
from .serializers import (
    UserSerializer, 
    RBACTPRMSerializer, 
    PermissionUpdateSerializer,
    PermissionFieldSerializer
)

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_users(request):
    """
    Get list of all active users with their permission count
    No RBAC check - accessible for admin configuration
    """
    try:
        # Filter parameters
        search = request.GET.get('search', '')
        department_id = request.GET.get('department_id')
        
        # Base query
        queryset = User.objects.filter(isactive='Y')
        
        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(firstname__icontains=search) |
                Q(lastname__icontains=search) |
                Q(email__icontains=search)
            )
        
        if department_id:
            queryset = queryset.filter(departmentid=department_id)
        
        # Order by name
        queryset = queryset.order_by('firstname', 'lastname')
        
        # Paginate
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = UserSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return Response(
            {'error': f'Failed to fetch users: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_permissions(request, user_id):
    """
    Get permissions for a specific user
    No RBAC check - accessible for admin configuration
    """
    try:
        # Check if user exists
        user = User.objects.filter(userid=user_id, isactive='Y').first()
        if not user:
            return Response(
                {'error': 'User not found or inactive'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get RBAC record
        rbac = RBACTPRM.objects.filter(user_id=user_id, is_active='Y').first()
        
        if not rbac:
            # Return user info with empty permissions
            return Response({
                'userId': user.userid,
                'userName': user.username,
                'fullName': f"{user.firstname} {user.lastname}" if user.firstname else user.username,
                'email': user.email,
                'departmentId': user.departmentid,
                'role': None,
                'permissions': {}
            }, status=status.HTTP_200_OK)
        
        serializer = RBACTPRMSerializer(rbac)
        response_data = serializer.data
        
        # Add user info
        response_data['fullName'] = f"{user.firstname} {user.lastname}" if user.firstname else user.username
        response_data['email'] = user.email
        response_data['departmentId'] = user.departmentid
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching user permissions: {str(e)}")
        return Response(
            {'error': f'Failed to fetch permissions: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST', 'PUT'])
@permission_classes([AllowAny])
def update_user_permissions(request):
    """
    Update permissions for a user
    No RBAC check - accessible for admin configuration
    """
    try:
        serializer = PermissionUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = serializer.validated_data['user_id']
        permissions = serializer.validated_data['permissions']
        role = serializer.validated_data.get('role', 'User')
        
        # Get user
        user = User.objects.get(userid=user_id, isactive='Y')
        
        with transaction.atomic():
            # Get or create RBAC record
            rbac, created = RBACTPRM.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'username': user.username,
                    'role': role,
                    'is_active': 'Y'
                }
            )
            
            # Update role if provided
            if role:
                rbac.role = role
            
            # Update permissions
            for permission_name, permission_value in permissions.items():
                if hasattr(rbac, permission_name):
                    setattr(rbac, permission_name, permission_value)
            
            rbac.save()
        
        logger.info(f"Updated permissions for user {user_id} ({user.username})")
        
        return Response({
            'message': 'Permissions updated successfully',
            'userId': user_id,
            'userName': user.username
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error updating permissions: {str(e)}")
        return Response(
            {'error': f'Failed to update permissions: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_permission_fields(request):
    """
    Get metadata about all available permission fields
    No RBAC check - accessible for admin configuration
    """
    try:
        # Define permission field metadata organized by module
        # Using the same module names as tprm_utils.py for consistency
        permission_metadata = {
            'rfp': {
                'name': 'RFP Management',
                'permissions': [
                    {'field': 'create_rfp', 'display': 'Create RFP', 'description': 'Create new RFPs'},
                    {'field': 'edit_rfp', 'display': 'Edit RFP', 'description': 'Edit existing RFPs'},
                    {'field': 'view_rfp', 'display': 'View RFP', 'description': 'View RFP details'},
                    {'field': 'delete_rfp', 'display': 'Delete RFP', 'description': 'Delete RFPs'},
                    {'field': 'clone_rfp', 'display': 'Clone RFP', 'description': 'Clone existing RFPs'},
                    {'field': 'submit_rfp_for_review', 'display': 'Submit for Review', 'description': 'Submit RFPs for approval'},
                    {'field': 'approve_rfp', 'display': 'Approve RFP', 'description': 'Approve RFPs'},
                    {'field': 'reject_rfp', 'display': 'Reject RFP', 'description': 'Reject RFPs'},
                    {'field': 'assign_rfp_reviewers', 'display': 'Assign Reviewers', 'description': 'Assign reviewers to RFPs'},
                    {'field': 'view_rfp_approval_status', 'display': 'View Approval Status', 'description': 'View RFP approval status'},
                    {'field': 'view_rfp_versions', 'display': 'View Versions', 'description': 'View RFP versions'},
                    {'field': 'create_rfp_version', 'display': 'Create Version', 'description': 'Create RFP versions'},
                    {'field': 'edit_rfp_version', 'display': 'Edit Version', 'description': 'Edit RFP versions'},
                    {'field': 'view_rfp_version', 'display': 'View Version', 'description': 'View specific RFP version'},
                    {'field': 'create_evaluation_criteria', 'display': 'Create Criteria', 'description': 'Create evaluation criteria'},
                    {'field': 'edit_evaluation_criteria', 'display': 'Edit Criteria', 'description': 'Edit evaluation criteria'},
                    {'field': 'delete_evaluation_criteria', 'display': 'Delete Criteria', 'description': 'Delete evaluation criteria'},
                    {'field': 'select_vendors_for_rfp', 'display': 'Select Vendors', 'description': 'Select vendors for RFP'},
                    {'field': 'invite_vendors_for_rfp', 'display': 'Invite Vendors', 'description': 'Invite vendors to participate'},
                    {'field': 'track_rfp_invitations', 'display': 'Track Invitations', 'description': 'Track RFP invitations'},
                    {'field': 'upload_documents_for_rfp', 'display': 'Upload Documents', 'description': 'Upload RFP documents'},
                    {'field': 'download_rfp_documents', 'display': 'Download Documents', 'description': 'Download RFP documents'},
                    {'field': 'preview_rfp_documents', 'display': 'Preview Documents', 'description': 'Preview RFP documents'},
                    {'field': 'validate_rfp_documents', 'display': 'Validate Documents', 'description': 'Validate RFP documents'},
                    {'field': 'scan_rfp_files_for_virus', 'display': 'Virus Scan', 'description': 'Scan RFP files for viruses'},
                    {'field': 'view_rfp_responses', 'display': 'View Responses', 'description': 'View vendor responses'},
                    {'field': 'submit_rfp_response', 'display': 'Submit Response', 'description': 'Submit RFP response'},
                    {'field': 'withdraw_rfp_response', 'display': 'Withdraw Response', 'description': 'Withdraw RFP response'},
                    {'field': 'auto_screen_rfp', 'display': 'Auto Screen', 'description': 'Automatically screen RFPs'},
                    {'field': 'assign_rfp_evaluators', 'display': 'Assign Evaluators', 'description': 'Assign evaluators to RFPs'},
                    {'field': 'score_rfp_response', 'display': 'Score Responses', 'description': 'Score vendor responses'},
                    {'field': 'view_rfp_response_scores', 'display': 'View Scores', 'description': 'View response scores'},
                    {'field': 'rank_vendors_for_rfp', 'display': 'Rank Vendors', 'description': 'Rank vendors for RFP'},
                    {'field': 'finalize_rfp_evaluation', 'display': 'Finalize Evaluation', 'description': 'Finalize RFP evaluation'},
                    {'field': 'send_rfp_award_notification', 'display': 'Send Award Notification', 'description': 'Send award notifications'},
                    {'field': 'view_rfp_analytics', 'display': 'View Analytics', 'description': 'View RFP analytics'},
                    {'field': 'generate_rfp_reports', 'display': 'Generate Reports', 'description': 'Generate RFP reports'},
                    {'field': 'download_rfp_report', 'display': 'Download Report', 'description': 'Download RFP report'},
                    {'field': 'manage_rfp_lifecycle', 'display': 'Manage Lifecycle', 'description': 'Manage RFP lifecycle'},
                    {'field': 'trigger_rfp_workflow', 'display': 'Trigger Workflow', 'description': 'Trigger RFP workflow'},
                    {'field': 'escalate_rfp_workflow', 'display': 'Escalate Workflow', 'description': 'Escalate RFP workflow'},
                    {'field': 'generate_rfp_tokens', 'display': 'Generate Tokens', 'description': 'Generate RFP access tokens'},
                    {'field': 'validate_rfp_access', 'display': 'Validate Access', 'description': 'Validate RFP access'},
                    {'field': 'view_rfp_audit_trail', 'display': 'View Audit Trail', 'description': 'View RFP audit trail'},
                    {'field': 'send_rfp_notifications', 'display': 'Send Notifications', 'description': 'Send RFP notifications'},
                    {'field': 'broadcast_rfp_communications', 'display': 'Broadcast Communications', 'description': 'Broadcast RFP communications'},
                    {'field': 'clarify_rfp_communications', 'display': 'Clarify Communications', 'description': 'Clarify RFP communications'},
                    {'field': 'amend_rfp_communications', 'display': 'Amend Communications', 'description': 'Amend RFP communications'},
                    {'field': 'create_rfp_vendor_from_rfp', 'display': 'Create Vendor from RFP', 'description': 'Create vendor from RFP'},
                    {'field': 'match_rfp_vendor', 'display': 'Match Vendor', 'description': 'Match RFP vendor'},
                    {'field': 'perform_rfp_health_check', 'display': 'Health Check', 'description': 'Perform RFP health check'},
                    {'field': 'validate_rfp_data', 'display': 'Validate Data', 'description': 'Validate RFP data'},
                    {'field': 'track_rfp_activity_log', 'display': 'Track Activity Log', 'description': 'Track RFP activity log'},
                ]
            },
            'contract': {
                'name': 'Contract Management',
                'permissions': [
                    {'field': 'list_contracts', 'display': 'View Contracts', 'description': 'View contract list'},
                    {'field': 'create_contract', 'display': 'Create Contract', 'description': 'Create new contracts'},
                    {'field': 'update_contract', 'display': 'Update Contract', 'description': 'Update existing contracts'},
                    {'field': 'delete_contract', 'display': 'Delete Contract', 'description': 'Delete contracts'},
                    {'field': 'approve_contract', 'display': 'Approve Contract', 'description': 'Approve contracts'},
                    {'field': 'reject_contract', 'display': 'Reject Contract', 'description': 'Reject contracts'},
                    {'field': 'create_contract_term', 'display': 'Create Terms', 'description': 'Create contract terms'},
                    {'field': 'list_contract_terms', 'display': 'List Terms', 'description': 'List contract terms'},
                    {'field': 'update_contract_term', 'display': 'Update Terms', 'description': 'Update contract terms'},
                    {'field': 'delete_contract_term', 'display': 'Delete Terms', 'description': 'Delete contract terms'},
                    {'field': 'list_contract_renewals', 'display': 'List Renewals', 'description': 'List contract renewals'},
                    {'field': 'create_contract_renewal', 'display': 'Create Renewal', 'description': 'Create contract renewals'},
                    {'field': 'approve_contract_renewal', 'display': 'Approve Renewal', 'description': 'Approve contract renewals'},
                    {'field': 'reject_contract_renewal', 'display': 'Reject Renewal', 'description': 'Reject contract renewals'},
                    {'field': 'create_contract_audit', 'display': 'Create Audit', 'description': 'Create contract audits'},
                    {'field': 'trigger_ocr', 'display': 'Trigger OCR', 'description': 'Trigger OCR extraction'},
                    {'field': 'get_nlp_clauses', 'display': 'Get NLP Clauses', 'description': 'Get NLP extracted clauses'},
                    {'field': 'contract_search', 'display': 'Search Contracts', 'description': 'Search contracts'},
                    {'field': 'get_contract_history', 'display': 'Get History', 'description': 'Get contract history'},
                    {'field': 'compare_contract_version', 'display': 'Compare Versions', 'description': 'Compare contract versions'},
                    {'field': 'download_contract_document', 'display': 'Download Document', 'description': 'Download contract document'},
                    {'field': 'contract_dashboard', 'display': 'View Dashboard', 'description': 'View contract dashboard'},
                    {'field': 'validate_contract_data', 'display': 'Validate Data', 'description': 'Validate contract data'},
                ]
            },
            'vendor': {
                'name': 'Vendor Management',
                'permissions': [
                    {'field': 'view_vendors', 'display': 'View Vendors', 'description': 'View vendor list'},
                    {'field': 'create_vendor', 'display': 'Create Vendor', 'description': 'Create new vendors'},
                    {'field': 'update_vendor', 'display': 'Update Vendor', 'description': 'Update vendor information'},
                    {'field': 'delete_vendor', 'display': 'Delete Vendor', 'description': 'Delete vendors'},
                    {'field': 'submit_vendor_for_approval', 'display': 'Submit for Approval', 'description': 'Submit vendors for approval'},
                    {'field': 'approve_reject_vendor', 'display': 'Approve/Reject Vendor', 'description': 'Approve or reject vendors'},
                    {'field': 'view_contacts_documents', 'display': 'View Contacts/Documents', 'description': 'View vendor contacts and documents'},
                    {'field': 'add_update_contacts_documents', 'display': 'Manage Contacts/Documents', 'description': 'Add/update vendor contacts and documents'},
                    {'field': 'approve_documents', 'display': 'Approve Documents', 'description': 'Approve vendor documents'},
                    {'field': 'view_risk_profile', 'display': 'View Risk Profile', 'description': 'View vendor risk profile'},
                    {'field': 'view_lifecycle_history', 'display': 'View Lifecycle', 'description': 'View vendor lifecycle history'},
                    {'field': 'assess_vendor_risk', 'display': 'Assess Risk', 'description': 'Assess vendor risk'},
                    {'field': 'view_vendor_risk_scores', 'display': 'View Risk Scores', 'description': 'View vendor risk scores'},
                    {'field': 'view_available_vendors', 'display': 'View Available Vendors', 'description': 'View available vendors'},
                    {'field': 'add_vendor_to_bcp_drp_strategy', 'display': 'Add to BCP/DRP', 'description': 'Add vendor to BCP/DRP strategy'},
                    {'field': 'view_vendor_contracts', 'display': 'View Contracts', 'description': 'View vendor contracts'},
                    {'field': 'create_modify_contracts', 'display': 'Create/Modify Contracts', 'description': 'Create or modify vendor contracts'},
                    {'field': 'initiate_screening', 'display': 'Initiate Screening', 'description': 'Initiate vendor screening'},
                    {'field': 'resolve_screening_matches', 'display': 'Resolve Screening', 'description': 'Resolve screening matches'},
                    {'field': 'view_screening_results', 'display': 'View Screening Results', 'description': 'View vendor screening results'},
                    {'field': 'access_integration_mappings', 'display': 'Integration Mappings', 'description': 'Access integration mappings'},
                    {'field': 'initiate_sync_with_finacle', 'display': 'Sync with Finacle', 'description': 'Initiate sync with Finacle'},
                ]
            },
            'risk': {
                'name': 'Risk Management',
                'permissions': [
                    {'field': 'view_risk_assessments', 'display': 'View Assessments', 'description': 'View risk assessments'},
                    {'field': 'create_risk_assessments', 'display': 'Create Assessments', 'description': 'Create risk assessments'},
                    {'field': 'recalculate_risk_scores', 'display': 'Recalculate Scores', 'description': 'Recalculate risk scores'},
                    {'field': 'identify_risks_in_plans', 'display': 'Identify Risks', 'description': 'Identify risks in plans'},
                    {'field': 'view_identified_risks', 'display': 'View Identified Risks', 'description': 'View identified risks'},
                    {'field': 'manage_risk_mitigation_plans', 'display': 'Manage Mitigation', 'description': 'Manage risk mitigation plans'},
                    {'field': 'view_risk_mitigation_status', 'display': 'View Mitigation Status', 'description': 'View risk mitigation status'},
                ]
            },
            'bcp_drp': {
                'name': 'BCP/DRP Management',
                'permissions': [
                    {'field': 'create_bcp_drp_strategy_and_plans', 'display': 'Create Strategy/Plans', 'description': 'Create BCP/DRP strategies and plans'},
                    {'field': 'view_plans_and_documents', 'display': 'View Plans', 'description': 'View BCP/DRP plans and documents'},
                    {'field': 'assign_plans_for_evaluation', 'display': 'Assign for Evaluation', 'description': 'Assign plans for evaluation'},
                    {'field': 'approve_or_reject_plan_evaluations', 'display': 'Approve/Reject Evaluation', 'description': 'Approve or reject plan evaluations'},
                    {'field': 'ocr_extraction_and_review', 'display': 'OCR Extraction', 'description': 'Perform OCR extraction and review'},
                    {'field': 'view_bcp_drp_plan_status', 'display': 'View Plan Status', 'description': 'View BCP/DRP plan status'},
                    {'field': 'view_document_status_history', 'display': 'View Document History', 'description': 'View document status history'},
                    {'field': 'request_document_revisions_from_vendor', 'display': 'Request Revisions', 'description': 'Request document revisions from vendor'},
                    {'field': 'view_vendor_submitted_documents', 'display': 'View Vendor Documents', 'description': 'View vendor submitted documents'},
                    {'field': 'coordinate_vendor_feedback', 'display': 'Coordinate Feedback', 'description': 'Coordinate vendor feedback'},
                    {'field': 'evaluate_plan_based_on_criteria', 'display': 'Evaluate Plan', 'description': 'Evaluate plan based on criteria'},
                    {'field': 'submit_evaluation_feedback', 'display': 'Submit Feedback', 'description': 'Submit evaluation feedback'},
                    {'field': 'manage_server_resources_for_bcp_drp', 'display': 'Manage Server Resources', 'description': 'Manage server resources for BCP/DRP'},
                    {'field': 'view_incident_response_plans', 'display': 'View Incident Plans', 'description': 'View incident response plans'},
                    {'field': 'create_incident_response_plans', 'display': 'Create Incident Plans', 'description': 'Create incident response plans'},
                    {'field': 'update_incident_response_plans', 'display': 'Update Incident Plans', 'description': 'Update incident response plans'},
                    {'field': 'integrate_bcp_drp_with_external_systems', 'display': 'External Integration', 'description': 'Integrate BCP/DRP with external systems'},
                    {'field': 'manage_integration_settings', 'display': 'Manage Integration', 'description': 'Manage integration settings'},
                ]
            },
            'questionnaire': {
                'name': 'Questionnaire Management',
                'permissions': [
                    {'field': 'create_questionnaire', 'display': 'Create Questionnaire', 'description': 'Create questionnaires'},
                    {'field': 'view_questionnaires', 'display': 'View Questionnaires', 'description': 'View questionnaires'},
                    {'field': 'manage_questionnaires', 'display': 'Manage Questionnaires', 'description': 'Manage questionnaires'},
                    {'field': 'view_all_questionnaires', 'display': 'View All Questionnaires', 'description': 'View all questionnaires'},
                    {'field': 'assign_questionnaires', 'display': 'Assign Questionnaires', 'description': 'Assign questionnaires to vendors'},
                    {'field': 'assign_questionnaires_for_review', 'display': 'Assign for Review', 'description': 'Assign questionnaires for review'},
                    {'field': 'submit_questionnaire_responses', 'display': 'Submit Responses', 'description': 'Submit questionnaire responses'},
                    {'field': 'review_approve_responses', 'display': 'Review/Approve Responses', 'description': 'Review and approve responses'},
                    {'field': 'create_questionnaire_for_testing', 'display': 'Create for Testing', 'description': 'Create questionnaire for testing'},
                    {'field': 'review_questionnaire_answers', 'display': 'Review Answers', 'description': 'Review questionnaire answers'},
                    {'field': 'final_approval_of_plan', 'display': 'Final Approval', 'description': 'Final approval of plan'},
                    {'field': 'configure_questionnaire_settings', 'display': 'Configure Settings', 'description': 'Configure questionnaire settings'},
                ]
            },
            'sla': {
                'name': 'SLA Management',
                'permissions': [
                    {'field': 'view_sla', 'display': 'View SLA', 'description': 'View SLAs'},
                    {'field': 'create_sla', 'display': 'Create SLA', 'description': 'Create new SLAs'},
                    {'field': 'update_sla', 'display': 'Update SLA', 'description': 'Update existing SLAs'},
                    {'field': 'delete_sla', 'display': 'Delete SLA', 'description': 'Delete SLAs'},
                    {'field': 'activate_deactivate_sla', 'display': 'Activate/Deactivate SLA', 'description': 'Activate or deactivate SLAs'},
                    {'field': 'view_performance', 'display': 'View Performance', 'description': 'View SLA performance metrics'},
                    {'field': 'create_performance', 'display': 'Create Performance', 'description': 'Create performance records'},
                    {'field': 'view_alerts', 'display': 'View Alerts', 'description': 'View SLA alerts'},
                    {'field': 'acknowledge_resolve_alerts', 'display': 'Manage Alerts', 'description': 'Acknowledge and resolve alerts'},
                    {'field': 'view_dashboard_trend', 'display': 'View Dashboard Trend', 'description': 'View dashboard trends'},
                ]
            },
            'compliance': {
                'name': 'Compliance & Audit',
                'permissions': [
                    {'field': 'generate_compliance_audit_reports', 'display': 'Generate Audit Reports', 'description': 'Generate compliance audit reports'},
                    {'field': 'review_regulatory_compliance', 'display': 'Review Compliance', 'description': 'Review regulatory compliance'},
                    {'field': 'audit_compliance_against_regulations', 'display': 'Audit Against Regulations', 'description': 'Audit compliance against regulations'},
                    {'field': 'view_compliance_status_of_plans', 'display': 'View Compliance Status', 'description': 'View compliance status of plans'},
                    {'field': 'audit_compliance_of_documents', 'display': 'Audit Documents', 'description': 'Audit compliance of documents'},
                    {'field': 'audit_compliance_of_plans', 'display': 'Audit Plans', 'description': 'Audit compliance of plans'},
                    {'field': 'view_compliance_audit_results', 'display': 'View Audit Results', 'description': 'View compliance audit results'},
                    {'field': 'generate_compliance_reports', 'display': 'Generate Reports', 'description': 'Generate compliance reports'},
                    {'field': 'configure_document_security_settings', 'display': 'Configure Security', 'description': 'Configure document security settings'},
                    {'field': 'view_document_access_logs', 'display': 'View Access Logs', 'description': 'View document access logs'},
                    {'field': 'review_and_approve_legal_aspects_of_plans', 'display': 'Review Legal Aspects', 'description': 'Review and approve legal aspects of plans'},
                    {'field': 'generate_legal_compliance_reports', 'display': 'Legal Reports', 'description': 'Generate legal compliance reports'},
                    {'field': 'view_contractual_obligations', 'display': 'View Obligations', 'description': 'View contractual obligations'},
                    {'field': 'audit_plan_documentation', 'display': 'Audit Documentation', 'description': 'Audit plan documentation'},
                    {'field': 'view_audit_logs', 'display': 'View Audit Logs', 'description': 'View system audit logs'},
                    {'field': 'generate_internal_audit_reports', 'display': 'Internal Audit Reports', 'description': 'Generate internal audit reports'},
                    {'field': 'conduct_external_compliance_audit', 'display': 'External Audit', 'description': 'Conduct external compliance audit'},
                    {'field': 'generate_external_audit_reports', 'display': 'External Reports', 'description': 'Generate external audit reports'},
                    {'field': 'review_external_auditor_comments', 'display': 'Review Auditor Comments', 'description': 'Review external auditor comments'},
                ]
            },
            'system': {
                'name': 'System Administration',
                'permissions': [
                    {'field': 'configure_system_settings', 'display': 'Configure System', 'description': 'Configure system settings'},
                    {'field': 'create_update_user_roles', 'display': 'Manage User Roles', 'description': 'Create and update user roles'},
                    {'field': 'manage_document_access_controls', 'display': 'Manage Access Controls', 'description': 'Manage document access controls'},
                    {'field': 'perform_health_check', 'display': 'Health Check', 'description': 'Perform system health checks'},
                    {'field': 'test_external_connections', 'display': 'Test Connections', 'description': 'Test external connections'},
                    {'field': 'monitor_system_health', 'display': 'Monitor Health', 'description': 'Monitor system health'},
                    {'field': 'backup_system_configuration', 'display': 'Backup Configuration', 'description': 'Backup system configuration'},
                    {'field': 'bulk_upload', 'display': 'Bulk Upload', 'description': 'Perform bulk data uploads'},
                ]
            }
        }
        
        return Response(permission_metadata, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching permission fields: {str(e)}")
        return Response(
            {'error': f'Failed to fetch permission fields: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def bulk_update_permissions(request):
    """
    Bulk update permissions for multiple users or apply a permission template
    No RBAC check - accessible for admin configuration
    """
    try:
        user_ids = request.data.get('user_ids', [])
        permissions = request.data.get('permissions', {})
        role = request.data.get('role')
        
        if not user_ids or not permissions:
            return Response(
                {'error': 'user_ids and permissions are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_users = []
        failed_users = []
        
        with transaction.atomic():
            for user_id in user_ids:
                try:
                    user = User.objects.get(userid=user_id, isactive='Y')
                    
                    rbac, created = RBACTPRM.objects.get_or_create(
                        user_id=user_id,
                        defaults={
                            'username': user.username,
                            'role': role or 'User',
                            'is_active': 'Y'
                        }
                    )
                    
                    if role:
                        rbac.role = role
                    
                    for permission_name, permission_value in permissions.items():
                        if hasattr(rbac, permission_name):
                            setattr(rbac, permission_name, permission_value)
                    
                    rbac.save()
                    updated_users.append({'userId': user_id, 'userName': user.username})
                    
                except User.DoesNotExist:
                    failed_users.append({'userId': user_id, 'error': 'User not found'})
                except Exception as e:
                    failed_users.append({'userId': user_id, 'error': str(e)})
        
        return Response({
            'message': f'Updated {len(updated_users)} users successfully',
            'updated': updated_users,
            'failed': failed_users
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        return Response(
            {'error': f'Bulk update failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

