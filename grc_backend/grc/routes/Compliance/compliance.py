from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import datetime
import traceback

from ...serializers import ComplianceSerializer, ComplianceApprovalSerializer
from ...models import SubPolicy, ComplianceApproval, Compliance, Framework, Policy, Users
from ...rbac.permissions import (
    ComplianceViewPermission, ComplianceCreatePermission, ComplianceEditPermission,
    ComplianceApprovePermission
)
from ...rbac.decorators import (
    compliance_view_required, compliance_create_required, compliance_edit_required,
    compliance_approve_required
)
from ...debug_utils import debug_print
# MULTI-TENANCY: Import tenant utilities for data isolation
from ...tenant_utils import (
    require_tenant, tenant_filter, get_tenant_id_from_request,
    validate_tenant_access, get_tenant_aware_queryset
)
from ...rbac.utils import RBACUtils

@api_view(['POST'])
@permission_classes([ComplianceCreatePermission])
@compliance_create_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def add_compliance(request, subpolicy_id):
    """
    Add a new compliance item to a subpolicy
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        with transaction.atomic():
            # Get the subpolicy
            subpolicy = get_object_or_404(SubPolicy, SubPolicyId=subpolicy_id, tenant_id=tenant_id)
            
            # Copy request data and add subpolicy_id
            data = request.data.copy()
            data['SubPolicyId'] = subpolicy_id
            
            # Set default values if not provided
            data.setdefault('Status', 'Under Review')
            data.setdefault('ActiveInactive', 'Active')
            data.setdefault('CreatedByDate', datetime.date.today())
            data.setdefault('ComplianceVersion', '1.0')
            
            # Duplicate name check: prevent two compliances with the same title in the same framework
            compliance_title = data.get('ComplianceTitle', '').strip()
            framework_id_for_check = subpolicy.PolicyId.FrameworkId_id
            if compliance_title and Compliance.objects.filter(
                FrameworkId_id=framework_id_for_check,
                ComplianceTitle__iexact=compliance_title,
                tenant_id=tenant_id
            ).exists():
                return Response(
                    {'error': f'A compliance with the title "{compliance_title}" already exists in this framework. '
                              'Each compliance name must be unique within a framework.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the compliance item
            compliance_serializer = ComplianceSerializer(data=data)
            if not compliance_serializer.is_valid():
                return Response(compliance_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            compliance = compliance_serializer.save()
            
            # Create extracted data for ComplianceApproval
            extracted_data = {
                'type': 'compliance',
                'ComplianceItemDescription': compliance.ComplianceItemDescription,
                'Criticality': compliance.Criticality,
                'Impact': compliance.Impact,
                'Probability': compliance.Probability,
                'mitigation': compliance.mitigation,
                'PossibleDamage': compliance.PossibleDamage,
                'IsRisk': compliance.IsRisk,
                'MandatoryOptional': compliance.MandatoryOptional,
                'ManualAutomatic': compliance.ManualAutomatic,
                'CreatedByName': compliance.CreatedByName,
                'CreatedByDate': compliance.CreatedByDate.isoformat() if compliance.CreatedByDate else None,
                'Status': compliance.Status,
                'ComplianceId': compliance.ComplianceId,
                'ComplianceVersion': compliance.ComplianceVersion,
                'SubPolicyId': subpolicy_id
            }
            
            # Get FrameworkId from the subpolicy's policy
            framework_id = subpolicy.PolicyId.FrameworkId
            debug_print(f"DEBUG: Using FrameworkId: {framework_id} for compliance addition")
            
            # Resolve creator from authenticated context (do not trust request body UserId)
            creator_user_id = RBACUtils.get_user_id_from_request(request) or getattr(request.user, 'id', None)
            reviewer_id = data.get('ReviewerId')
            if not creator_user_id:
                return Response(
                    {'error': 'User authentication required. Please log in and try again.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            if not reviewer_id:
                return Response(
                    {'error': 'Reviewer assignment required. Please select a reviewer and try again.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                creator_user_id = int(creator_user_id)
                reviewer_id = int(reviewer_id)
            except (TypeError, ValueError):
                return Response(
                    {'error': 'Invalid user or reviewer id. Please contact an administrator.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if creator_user_id == reviewer_id:
                return Response(
                    {'error': 'Self-approval is not allowed. Please select a different reviewer.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            reviewer_exists = Users.objects.filter(tenant_id=tenant_id, UserId=reviewer_id).exists()
            if not reviewer_exists:
                return Response(
                    {'error': 'Selected reviewer not found for your organization.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create the ComplianceApproval entry with version u1
            compliance_approval = ComplianceApproval(
                PolicyId=subpolicy.PolicyId,  # Associate with the parent policy
                ExtractedData=extracted_data,
                UserId=creator_user_id,
                ReviewerId=reviewer_id,
                Version='u1',
                ApprovedNot=None,  # Not yet approved
                FrameworkId=framework_id  # Add FrameworkId to compliance approval
            )
            compliance_approval.save()
            
            return Response({
                'message': 'Compliance added to subpolicy successfully',
                'ComplianceId': compliance.ComplianceId,
                'ComplianceVersion': compliance.ComplianceVersion,
                'ApprovalVersion': 'u1'
            }, status=status.HTTP_201_CREATED)
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return Response({'error': 'Error adding compliance to subpolicy', 'details': error_info}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_compliance_version(request, compliance_id):
    """
    Get the latest version of a compliance item from the policy approvals table
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        compliance = get_object_or_404(Compliance, ComplianceId=compliance_id, tenant_id=tenant_id)
        
        # Find the latest approval version from the database
        latest_approval = ComplianceApproval.objects.filter(
            ExtractedData__ComplianceId=compliance_id
        ).order_by('-Version').first()
        
        # Extract the latest version from policy approvals
        if latest_approval and latest_approval.Version:
            # If version starts with 'u', return it
            if latest_approval.Version.startswith('u'):
                version = latest_approval.Version
            else:
                # Check if there are any user versions (u1, u2, etc.)
                user_approvals = ComplianceApproval.objects.filter(
                    ExtractedData__ComplianceId=compliance_id,
                    Version__startswith='u'
                ).order_by('-Version')
                
                if user_approvals.exists():
                    version = user_approvals.first().Version
                else:
                    version = 'u1'  # Default if no user versions found
        else:
            # If no approvals found, default to u1
            version = 'u1'
        
        return Response({
            'compliance_id': compliance_id,
            'version': version
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_latest_reviewer_version(request, compliance_id):
    """
    Get the latest reviewer version (R1, R2, etc.) for a compliance item
    and return the complete policy approval data for that version
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        latest_r_version = 'R1'  # Default if no reviewer versions found
        approval_data = None
        
        # Find the latest R version for a compliance
        compliance = get_object_or_404(Compliance, ComplianceId=compliance_id, tenant_id=tenant_id)
        
        # Use Python filtering to find R versions
        r_approvals = []
        all_approvals = ComplianceApproval.objects.filter(
            ExtractedData__ComplianceId=compliance_id
        ).order_by('-Version')
        
        for approval in all_approvals:
            if approval.Version and approval.Version.startswith('R'):
                r_approvals.append(approval)
        
        if r_approvals:
            # Get the latest policy approval with R version
            latest_approval = r_approvals[0]
            latest_r_version = latest_approval.Version
            
            # Serialize the compliance approval data
            serializer = ComplianceApprovalSerializer(latest_approval)
            approval_data = serializer.data
        
        # Return the version and approval data
        return Response({
            'compliance_id': compliance_id,
            'version': latest_r_version,
            'approval_data': approval_data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_pending_compliance_approvals(request):
    """
    Get all compliance items with 'Under Review' status from both ComplianceApproval and Compliance tables
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        # Get all compliance records directly from Compliance table with Under Review status
        under_review_compliances = Compliance.objects.filter(tenant_id=tenant_id, Status__icontains='review')
        
        # Also find all compliance approvals with compliance type and Under Review status
        pending_approvals = ComplianceApproval.objects.filter(
            ExtractedData__type='compliance'
        ).order_by('-Version')
        
        # Use a set to track which compliance items we've already included
        processed_compliance_ids = set()
        filtered_approvals = []
        
        # First, process direct compliance items
        for compliance in under_review_compliances:
            if compliance.ComplianceId not in processed_compliance_ids:
                processed_compliance_ids.add(compliance.ComplianceId)
                
                # Find or create a ComplianceApproval for this compliance
                approval = ComplianceApproval.objects.filter(
                    ExtractedData__ComplianceId=compliance.ComplianceId
                ).first()
                
                if approval:
                    # Use existing approval
                    filtered_approvals.append(approval)
                else:
                    # Create a temporary ComplianceApproval object to represent this compliance
                    # This will have a real database ApprovalId that can be used for PUT requests
                    extracted_data = {
                        'type': 'compliance',
                        'ComplianceItemDescription': compliance.ComplianceItemDescription,
                        'ComplianceId': compliance.ComplianceId,
                        'Criticality': compliance.Criticality,
                        'Impact': compliance.Impact,
                        'Probability': compliance.Probability,
                        'mitigation': compliance.mitigation,
                        'PossibleDamage': compliance.PossibleDamage,
                        'Status': compliance.Status,
                        'CreatedByName': compliance.CreatedByName,
                        'CreatedByDate': compliance.CreatedByDate.isoformat() if compliance.CreatedByDate else None,
                        'Identifier': compliance.Identifier
                    }
                    
                    # Create a real ComplianceApproval record that can be referenced later
                    # Find the parent policy through the subpolicy
                    subpolicy = SubPolicy.objects.get(SubPolicyId=compliance.SubPolicyId.SubPolicyId, tenant_id=tenant_id)
                    
                    # Get user and reviewer IDs from request
                    user_id = request.user.id if hasattr(request.user, 'id') else None
                    if not user_id:
                        user_id = request.session.get('user_id')
                    if not user_id:
                        return Response({'error': 'No user ID found'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    reviewer_id = request.session.get('reviewer_id')
                    if not reviewer_id:
                        reviewer_id = request.session.get('user_id')  # Use user ID as reviewer ID if no reviewer ID found
                    if not reviewer_id:
                        return Response({'error': 'No reviewer ID found'}, status=status.HTTP_400_BAD_REQUEST)

                    # Enforce maker–checker: creator cannot be their own reviewer
                    try:
                        creator_id_int = int(user_id)
                        reviewer_id_int = int(reviewer_id)
                    except (TypeError, ValueError):
                        logger.warning("Invalid creator/reviewer id while creating ComplianceApproval in compliance.py (pending_compliances loop)")
                        return Response(
                            {'error': 'Invalid user or reviewer id. Please contact an administrator.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    if creator_id_int == reviewer_id_int:
                        logger.warning(f"Self-approval attempt detected for compliance on PolicyId {subpolicy.PolicyId_id} by user {creator_id_int}")
                        return Response(
                            {'error': 'Self-approval is not allowed. Please select a different reviewer.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    new_approval = ComplianceApproval.objects.create(
                        PolicyId=subpolicy.PolicyId,
                        ExtractedData=extracted_data,
                        UserId=creator_id_int,
                        ReviewerId=reviewer_id_int,
                        Version='u1',
                        ApprovedNot=None
                    )
                    filtered_approvals.append(new_approval)
        
        # Then process policy approvals
        for approval in pending_approvals:
            if not approval.ExtractedData:
                continue
                
            # Extract the compliance ID
            compliance_id = None
            if 'ComplianceId' in approval.ExtractedData:
                compliance_id = approval.ExtractedData['ComplianceId']
            elif 'compliance_id' in approval.ExtractedData:
                compliance_id = approval.ExtractedData['compliance_id']
            elif 'Identifier' in approval.ExtractedData:
                compliance_id = approval.ExtractedData['Identifier']
            
            # Check status - case insensitive matching for "under review"
            status_value = approval.ExtractedData.get('Status', '')
            is_under_review = False
            
            if status_value:
                is_under_review = 'review' in status_value.lower()
            
            # If we haven't seen this compliance item before and it's under review, add it to our results
            if compliance_id and compliance_id not in processed_compliance_ids and (is_under_review or approval.ApprovedNot is None):
                processed_compliance_ids.add(compliance_id)
                # Make sure Status is set properly for frontend
                if 'Status' not in approval.ExtractedData or not approval.ExtractedData['Status']:
                    approval.ExtractedData['Status'] = 'Under Review'
                filtered_approvals.append(approval)
        
        # For compliance approval objects, serialize them properly
        serialized_approvals = []
        for approval in filtered_approvals:
            # It's a ComplianceApproval object
            serializer = ComplianceApprovalSerializer(approval)
            serialized_approvals.append(serializer.data)
        
        return Response(serialized_approvals, status=status.HTTP_200_OK)
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return Response({'error': 'Error retrieving pending compliance approvals', 'details': error_info}, 
                      status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([ComplianceApprovePermission])
@compliance_approve_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def submit_compliance_review(request, approval_id):
    """
    Submit a review for a compliance item
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        # Get the compliance approval
        approval = get_object_or_404(ComplianceApproval, pk=approval_id)
        
        # Update the approval data
        if 'ExtractedData' in request.data:
            approval.ExtractedData = request.data['ExtractedData']
        
        if 'ApprovedNot' in request.data:
            approval.ApprovedNot = request.data['ApprovedNot']
            
            # Update version based on whether it's a reviewer or user
            current_version = approval.Version or ''
            
            # If this is a reviewer submitting a review
            if approval.ReviewerId and str(approval.ReviewerId) == str(request.data.get('reviewer_id')):
                # If current version is a reviewer version, increment it
                if current_version.startswith('r'):
                    try:
                        version_num = int(current_version[1:])
                        approval.Version = f'r{version_num + 1}'
                    except ValueError:
                        approval.Version = 'r1'
                else:
                    # Start with r1 if no reviewer version exists
                    approval.Version = 'r1'
            else:
                # This is a user resubmitting
                if current_version.startswith('u'):
                    try:
                        version_num = int(current_version[1:])
                        approval.Version = f'u{version_num + 1}'
                    except ValueError:
                        approval.Version = 'u1'
                else:
                    # Start with u1 if no user version exists
                    approval.Version = 'u1'
        
        # Save the updated approval
        approval.save()
        
        # Also update the corresponding compliance record if it exists
        compliance_id = None
        if 'ComplianceId' in approval.ExtractedData:
            compliance_id = approval.ExtractedData['ComplianceId']
        elif 'compliance_id' in approval.ExtractedData:
            compliance_id = approval.ExtractedData['compliance_id']
        
        if compliance_id:
            try:
                compliance = Compliance.objects.get(ComplianceId=compliance_id, tenant_id=tenant_id)
                # Update compliance status to match approval
                if approval.ApprovedNot is True:
                    compliance.Status = 'Approved'
                elif approval.ApprovedNot is False:
                    compliance.Status = 'Rejected'
                compliance.save()
            except Compliance.DoesNotExist:
                # Compliance record doesn't exist or ID is invalid, just continue
                pass
        
        return Response({
            'message': 'Compliance review submitted successfully',
            'ApprovalId': approval_id,
            'Version': approval.Version
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Error submitting compliance review: An internal server error occurred',
            'traceback': traceback.format_exc()
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([ComplianceApprovePermission])
@compliance_approve_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def resubmit_compliance_approval(request, approval_id):
    """
    Resubmit a rejected compliance for review
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        # Get the compliance approval
        approval = get_object_or_404(ComplianceApproval, pk=approval_id)
        
        # Update the extracted data
        if 'ExtractedData' in request.data:
            approval.ExtractedData = request.data['ExtractedData']
        
        # Reset approval status
        approval.ApprovedNot = None
        
        # Update status in extracted data
        if approval.ExtractedData and 'Status' in approval.ExtractedData:
            approval.ExtractedData['Status'] = 'Under Review'
        
        # Handle versioning for resubmission (always a user version since it's a resubmission)
        current_version = approval.Version or ''
        if current_version.startswith('u'):
            try:
                version_num = int(current_version[1:])
                approval.Version = f'u{version_num + 1}'
            except ValueError:
                approval.Version = 'u1'
        else:
            # If coming from a reviewer version or no version, start a new user version
            approval.Version = 'u1'
        
        # Save the updated approval
        approval.save()
        
        # Also update the compliance if it exists
        compliance_id = None
        if 'ComplianceId' in approval.ExtractedData:
            compliance_id = approval.ExtractedData['ComplianceId']
        elif 'compliance_id' in approval.ExtractedData:
            compliance_id = approval.ExtractedData['compliance_id']
        
        if compliance_id:
            try:
                compliance = Compliance.objects.get(ComplianceId=compliance_id, tenant_id=tenant_id)
                # Update compliance data from ExtractedData
                compliance.ComplianceItemDescription = approval.ExtractedData.get('ComplianceItemDescription', compliance.ComplianceItemDescription)
                compliance.Criticality = approval.ExtractedData.get('Criticality', compliance.Criticality)
                compliance.Impact = approval.ExtractedData.get('Impact', compliance.Impact)
                compliance.Probability = approval.ExtractedData.get('Probability', compliance.Probability)
                compliance.mitigation = approval.ExtractedData.get('mitigation', compliance.mitigation)
                compliance.Status = 'Under Review'
                compliance.save()
            except Compliance.DoesNotExist:
                # Compliance doesn't exist, just continue
                pass
        
        return Response({
            'message': 'Compliance resubmitted successfully',
            'ApprovalId': approval_id,
            'Version': approval.Version
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Error resubmitting compliance: An internal server error occurred',
            'traceback': traceback.format_exc()
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_compliance_status(request, compliance_id):
    """
    Get the status of a compliance item directly from the Compliance table
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        compliance = get_object_or_404(Compliance, ComplianceId=compliance_id, tenant_id=tenant_id)
        
        return Response({
            'compliance_id': compliance_id,
            'status': compliance.Status
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_compliances_by_type(request, type, id):
    """
    Get all compliances based on framework, policy, or subpolicy ID
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        compliances = []
        
        if type == 'framework':
            # Get all compliances under the framework through policy and subpolicy relationships
            compliances = Compliance.objects.select_related(
                'SubPolicy__PolicyId__FrameworkId'
            ).filter(
                SubPolicy__PolicyId__FrameworkId__FrameworkId=id
            ).order_by('ComplianceId')
        elif type == 'policy':
            # Get all compliances under the policy through subpolicy relationship
            compliances = Compliance.objects.select_related(
                'SubPolicy__PolicyId'
            ).filter(
                SubPolicy__PolicyId__PolicyId=id
            ).order_by('ComplianceId')
        elif type == 'subpolicy':
            # Get all compliances directly under the subpolicy
            compliances = Compliance.objects.select_related(
                'SubPolicy', 'SubPolicy__PolicyId', 'SubPolicy__PolicyId__FrameworkId'
            ).filter(
 
                SubPolicy__SubPolicyId=id
            ).order_by('ComplianceId')
        else:
            return Response({
                'success': False,
                'message': 'Invalid type specified'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Serialize the compliances with additional hierarchy information
        serialized_compliances = []
        for compliance in compliances:
            compliance_data = {
                'ComplianceId': compliance.ComplianceId,
                'ComplianceTitle': compliance.ComplianceTitle,
                'ComplianceItemDescription': compliance.ComplianceItemDescription,
                'ComplianceType': compliance.ComplianceType,
                'Scope': compliance.Scope,
                'Objective': compliance.Objective,
                'IsRisk': compliance.IsRisk,
                'PossibleDamage': compliance.PossibleDamage,
                'mitigation': compliance.mitigation,
                'Criticality': compliance.Criticality,
                'MandatoryOptional': compliance.MandatoryOptional,
                'ManualAutomatic': compliance.ManualAutomatic,
                'Impact': compliance.Impact,
                'Probability': compliance.Probability,
                'MaturityLevel': compliance.MaturityLevel,
                'Status': compliance.Status,
                'ComplianceVersion': compliance.ComplianceVersion,
                'CreatedByName': compliance.CreatedByName,
                'CreatedByDate': compliance.CreatedByDate,
                'Identifier': compliance.Identifier,
                'Annex': compliance.SubPolicy.Identifier if compliance.SubPolicy and compliance.SubPolicy.Identifier else None,  # Add SubPolicy Identifier as Annex
                'RiskType': compliance.RiskType,
                'RiskCategory': compliance.RiskCategory,
                'RiskBusinessImpact': compliance.RiskBusinessImpact,
                # Add hierarchy information
                'SubPolicyName': compliance.SubPolicy.SubPolicyName,
                'PolicyName': compliance.SubPolicy.PolicyId.PolicyName,
                'FrameworkName': compliance.SubPolicy.PolicyId.FrameworkId.FrameworkName
            }
            serialized_compliances.append(compliance_data)

        return Response({
            'success': True,
            'compliances': serialized_compliances
        }, status=status.HTTP_200_OK)

    except Exception as e:
        debug_print(f"Error in get_compliances_by_type: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching compliances: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_frameworks(request):
    """
    Get all frameworks
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        frameworks = Framework.objects.filter(tenant_id=tenant_id).order_by('FrameworkId')
        frameworks_data = []
        
        for framework in frameworks:
            framework_data = {
                'id': framework.FrameworkId,
                'name': framework.FrameworkName,
                'description': framework.FrameworkDescription,
                'category': framework.Category,
                'status': framework.Status,
                'version': str(framework.CurrentVersion),
                'createdBy': framework.CreatedByName,
                'createdDate': framework.CreatedByDate,
                'effectiveDate': framework.EffectiveDate,
                'identifier': framework.Identifier
            }
            frameworks_data.append(framework_data)
            
        return Response({
            'success': True,
            'frameworks': frameworks_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        debug_print(f"Error in get_frameworks: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching frameworks: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_policies(request, framework_id):
    """
    Get all policies for a framework
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        policies = Policy.objects.filter(tenant_id=tenant_id, 
            FrameworkId=framework_id
        ).order_by('PolicyId')
        
        policies_data = []
        for policy in policies:
            policy_data = {
                'id': policy.PolicyId,
                'name': policy.PolicyName,
                'description': policy.PolicyDescription,
                'status': policy.Status,
                'version': policy.CurrentVersion,
                'createdBy': policy.CreatedByName,
                'createdDate': policy.CreatedByDate,
                'startDate': policy.StartDate,
                'endDate': policy.EndDate,
                'department': policy.Department,
                'scope': policy.Scope,
                'objective': policy.Objective,
                'identifier': policy.Identifier
            }
            policies_data.append(policy_data)
            
        return Response({
            'success': True,
            'policies': policies_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        debug_print(f"Error in get_policies: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching policies: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_subpolicies(request, policy_id):
    """
    Get all subpolicies for a policy
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        subpolicies = SubPolicy.objects.filter(tenant_id=tenant_id, 
            PolicyId=policy_id
        ).order_by('SubPolicyId')
        
        subpolicies_data = []
        for subpolicy in subpolicies:
            subpolicy_data = {
                'id': subpolicy.SubPolicyId,
                'name': subpolicy.SubPolicyName,
                'description': subpolicy.Description,
                'status': subpolicy.Status,
                'createdBy': subpolicy.CreatedByName,
                'createdDate': subpolicy.CreatedByDate,
                'identifier': subpolicy.Identifier,
                'control': subpolicy.Control,
                'permanentTemporary': subpolicy.PermanentTemporary
            }
            subpolicies_data.append(subpolicy_data)
            
        return Response({
            'success': True,
            'subpolicies': subpolicies_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        debug_print(f"Error in get_subpolicies: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error fetching subpolicies: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_compliance_dashboard_with_filters(request):
    """
    Get compliance dashboard data with framework and other filters
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        # Get filter parameters from request
        framework_id = request.query_params.get('framework_id')
        time_range = request.query_params.get('timeRange')
        category = request.query_params.get('category')
        priority = request.query_params.get('priority')
        
        debug_print(f"Dashboard filters - Framework: {framework_id}, Time: {time_range}, Category: {category}, Priority: {priority}")
        
        # Start with base queryset
        queryset = Compliance.objects.select_related('SubPolicy__PolicyId__FrameworkId').all()
        
        # Apply framework filtering using the standard framework filter helper
        try:
            from ..Policy.framework_filter_helper import get_active_framework_filter
            
            # Get framework filter info for logging
            framework_filter_id = get_active_framework_filter(request)
            debug_print(f"🔍 DEBUG: Compliance Dashboard - Active framework filter: {framework_filter_id}")
            
            # Apply framework filter to compliance using direct FrameworkId relationship
            if framework_filter_id:
                queryset = queryset.filter(FrameworkId=framework_filter_id)
                debug_print(f"Applied session framework filter via FrameworkId: {framework_filter_id}")
            else:
                debug_print("No framework filter applied - showing all frameworks")
            
        except ImportError as e:
            debug_print(f"DEBUG: Could not import framework filter helper: {e}")
            # Fallback to manual framework filtering if helper is not available
            if framework_id and framework_id != '':
                queryset = queryset.filter(FrameworkId=framework_id)
                debug_print(f"Applied manual framework filter via FrameworkId: {framework_id}")
        except Exception as e:
            debug_print(f"DEBUG: Error applying framework filter: {e}")
            # Fallback to manual framework filtering on error
            if framework_id and framework_id != '':
                queryset = queryset.filter(FrameworkId=framework_id)
                debug_print(f"Applied manual framework filter via FrameworkId: {framework_id}")
        
        # Apply explicit framework filter if provided (for backward compatibility)
        if framework_id and framework_id != '':
            queryset = queryset.filter(FrameworkId=framework_id)
            debug_print(f"Applied explicit framework filter via FrameworkId: {framework_id}")
        
        # Apply time range filter if provided
        if time_range and time_range != 'Last 6 Months':
            from datetime import datetime, timedelta
            now = datetime.now()
            
            if time_range == 'Last 3 Months':
                start_date = now - timedelta(days=90)
            elif time_range == 'Last Month':
                start_date = now - timedelta(days=30)
            elif time_range == 'Last Week':
                start_date = now - timedelta(days=7)
            else:
                start_date = now - timedelta(days=180)  # Default to 6 months
            
            queryset = queryset.filter(CreatedByDate__gte=start_date.date())
            debug_print(f"Applied time filter: {time_range}")
        
        # Apply category filter if provided - now supports dynamic categories from DB
        if category and category != 'All Categories':
            queryset = queryset.filter(ComplianceType__icontains=category)
            debug_print(f"Applied category filter: {category}")
        
        # Apply priority filter if provided
        if priority and priority != 'All Priorities':
            queryset = queryset.filter(Criticality=priority)
            debug_print(f"Applied priority filter: {priority}")
        
        debug_print(f"Final query count: {queryset.count()}")
        
        # Calculate dashboard metrics
        total_count = queryset.count()
        
        # Status counts
        status_counts = {
            'approved': queryset.filter(Status='Approved').count(),
            'active': queryset.filter(Status='Active').count(),
            'scheduled': queryset.filter(Status='Schedule').count(),
            'rejected': queryset.filter(Status='Rejected').count(),
            'under_review': queryset.filter(Status='Under Review').count(),
            'active_compliance': queryset.filter(ActiveInactive='Active').count()
        }
        
        # Calculate approval rate
        approved_count = status_counts['approved']
        approval_rate = round((approved_count / total_count * 100) if total_count > 0 else 0, 1)
        
        # Calculate total findings (risks)
        total_findings = queryset.filter(IsRisk=True).count()
        
        return Response({
            'success': True,
            'data': {
                'summary': {
                    'status_counts': status_counts,
                    'total_count': total_count,
                    'total_findings': total_findings,
                    'approval_rate': approval_rate
                }
            }
        })
        
    except Exception as e:
        debug_print(f"Error in get_compliance_dashboard_with_filters: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error fetching dashboard data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

@api_view(['GET'])
@permission_classes([ComplianceViewPermission])
@compliance_view_required
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def test_framework_filter(request):
    """
    Test endpoint to debug framework filtering
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)

    try:
        framework_id = request.query_params.get('framework_id')
        
        debug_print(f"Testing framework filter with ID: {framework_id}")
        
        # Get all frameworks
        frameworks = Framework.objects.filter(tenant_id=tenant_id)
        frameworks_data = [{'id': f.FrameworkId, 'name': f.FrameworkName} for f in frameworks]
        
        # Get compliance count for the framework if provided
        compliance_count = 0
        if framework_id and framework_id != '':
            compliance_count = Compliance.objects.filter(tenant_id=tenant_id, 
                SubPolicy__PolicyId__FrameworkId=framework_id
            ).count()
        
        # Get total compliance count
        total_compliance_count = Compliance.objects.count()
        
        return Response({
            'success': True,
            'data': {
                'framework_id': framework_id,
                'available_frameworks': frameworks_data,
                'compliance_count_for_framework': compliance_count,
                'total_compliance_count': total_compliance_count,
                'message': f'Framework filter test completed. Found {compliance_count} compliances for framework {framework_id}' if framework_id else 'No framework filter applied'
            }
        })
        
    except Exception as e:
        debug_print(f"Error in test_framework_filter: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error testing framework filter: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 