"""
Views for RFP Committee Management and Final Evaluation
"""

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json
from .models import RFP, RFPCommittee, RFPFinalEvaluation, RFPResponse
from .rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission
from tprm_backend.rbac.tprm_decorators import rbac_rfp_required

# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    require_tenant,
    tenant_filter
)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def create_committee(request, rfp_id):
    """
    Create committee assignments for an RFP
    Payload:
    {
        "rfp_id": 55,
        "committee_members": [
            {
                "member_id": 28,
                "member_role": "Technical Lead",
                "is_chair": true
            },
            ...
        ],
        "response_ids": [123, 456, 789],
        "added_by": 1
    }
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        data = request.data or {}
        committee_members = data.get('committee_members', [])
        response_ids = data.get('response_ids', [])
        added_by = data.get('added_by')

        if not committee_members or not added_by:
            return Response({
                'error': 'committee_members and added_by are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # If no response_ids provided, use empty array (committee can be assigned responses later)
        if not response_ids:
            response_ids = []

        # Verify RFP exists
        # MULTI-TENANCY: Filter by tenant
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=tenant_id)
        except RFP.DoesNotExist:
            return Response({
                'error': f'RFP with ID {rfp_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        created_committees = []
        with transaction.atomic():
            # Clear existing committee for this RFP
            # MULTI-TENANCY: Filter by tenant
            RFPCommittee.objects.filter(rfp_id=rfp_id, tenant_id=tenant_id).delete()
            
            for member_data in committee_members:
                # MULTI-TENANCY: Set tenant_id on creation
                committee = RFPCommittee.objects.create(
                    rfp_id=rfp_id,
                    response_id=response_ids,
                    response_ids=response_ids,
                    member_id=member_data.get('member_id'),
                    member_role=member_data.get('member_role', 'Committee Member'),
                    is_chair=member_data.get('is_chair', False),
                    added_by=added_by,
                    tenant_id=tenant_id  # MULTI-TENANCY: Set tenant_id
                )
                created_committees.append({
                    'committee_id': committee.committee_id,
                    'member_id': committee.member_id,
                    'member_role': committee.member_role,
                    'is_chair': committee.is_chair
                })

        return Response({
            'success': True,
            'message': 'Committee created successfully',
            'rfp_id': rfp_id,
            'committee_members': created_committees,
            'response_ids': response_ids
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': f'Failed to create committee: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_committee(request, rfp_id):
    """
    Get committee members for an RFP
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # MULTI-TENANCY: Verify RFP belongs to tenant
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=tenant_id)
        except RFP.DoesNotExist:
            return Response({
                'error': f'RFP with ID {rfp_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # MULTI-TENANCY: Filter by tenant
        committees = RFPCommittee.objects.filter(rfp_id=rfp_id, tenant_id=tenant_id).order_by('-is_chair', 'member_role')
        
        committee_data = []
        for committee in committees:
            committee_data.append({
                'committee_id': committee.committee_id,
                'member_id': committee.member_id,
                'member_role': committee.member_role,
                'is_chair': committee.is_chair,
                'added_date': committee.added_date,
                'response_ids': committee.response_ids or committee.response_id
            })

        return Response({
            'success': True,
            'rfp_id': rfp_id,
            'committee_members': committee_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get committee: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('evaluate_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def save_final_evaluation(request, rfp_id):
    """
    Save final evaluation rankings for an RFP
    Payload:
    {
        "rfp_id": 55,
        "evaluator_id": 28,
        "rankings": [
            {
                "response_id": 123,
                "ranking_position": 1,
                "ranking_score": 95.5,
                "evaluation_comments": "Excellent proposal"
            },
            ...
        ]
    }
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        data = request.data or {}
        evaluator_id = data.get('evaluator_id')
        rankings = data.get('rankings', [])

        if not evaluator_id or not rankings:
            return Response({
                'error': 'evaluator_id and rankings are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify evaluator is part of committee
        # MULTI-TENANCY: Filter by tenant
        committee_member = RFPCommittee.objects.filter(
            rfp_id=rfp_id, 
            member_id=evaluator_id,
            tenant_id=tenant_id
        ).first()
        
        if not committee_member:
            return Response({
                'error': 'Evaluator is not part of the committee for this RFP'
            }, status=status.HTTP_403_FORBIDDEN)

        saved_evaluations = []
        with transaction.atomic():
            # Clear existing evaluations for this evaluator and RFP
            # MULTI-TENANCY: Filter by tenant
            RFPFinalEvaluation.objects.filter(
                rfp_id=rfp_id, 
                evaluator_id=evaluator_id,
                tenant_id=tenant_id
            ).delete()
            
            for ranking in rankings:
                try:
                    response_id = int(ranking.get('response_id'))
                    ranking_position = int(ranking.get('ranking_position'))
                    ranking_score = Decimal(str(ranking.get('ranking_score', 0)))
                    evaluation_comments = ranking.get('evaluation_comments', '')
                    
                    # Verify response exists
                    # MULTI-TENANCY: Filter by tenant
                    try:
                        response = RFPResponse.objects.get(response_id=response_id, rfp_id=rfp_id, tenant_id=tenant_id)
                    except RFPResponse.DoesNotExist:
                        continue
                    
                    # MULTI-TENANCY: Set tenant_id on creation
                    evaluation = RFPFinalEvaluation.objects.create(
                        rfp_id=rfp_id,
                        response_id=response_id,
                        evaluator_id=evaluator_id,
                        ranking_position=ranking_position,
                        ranking_score=ranking_score,
                        evaluation_comments=evaluation_comments,
                        tenant_id=tenant_id  # MULTI-TENANCY: Set tenant_id
                    )
                    
                    saved_evaluations.append({
                        'final_eval_id': evaluation.final_eval_id,
                        'response_id': evaluation.response_id,
                        'ranking_position': evaluation.ranking_position,
                        'ranking_score': float(evaluation.ranking_score)
                    })
                    
                except (ValueError, TypeError) as e:
                    continue

        return Response({
            'success': True,
            'message': 'Final evaluation saved successfully',
            'rfp_id': rfp_id,
            'evaluator_id': evaluator_id,
            'evaluations': saved_evaluations
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': f'Failed to save final evaluation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_final_evaluations(request, rfp_id):
    """
    Get all final evaluations for an RFP
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # MULTI-TENANCY: Verify RFP belongs to tenant
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=tenant_id)
        except RFP.DoesNotExist:
            return Response({
                'error': f'RFP with ID {rfp_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # MULTI-TENANCY: Filter by tenant
        evaluations = RFPFinalEvaluation.objects.filter(rfp_id=rfp_id, tenant_id=tenant_id).order_by('evaluator_id', 'ranking_position')
        
        # Group by evaluator
        evaluator_evaluations = {}
        for evaluation in evaluations:
            evaluator_id = evaluation.evaluator_id
            if evaluator_id not in evaluator_evaluations:
                evaluator_evaluations[evaluator_id] = []
            
            evaluator_evaluations[evaluator_id].append({
                'final_eval_id': evaluation.final_eval_id,
                'response_id': evaluation.response_id,
                'ranking_position': evaluation.ranking_position,
                'ranking_score': float(evaluation.ranking_score),
                'evaluation_comments': evaluation.evaluation_comments,
                'evaluation_date': evaluation.evaluation_date
            })

        return Response({
            'success': True,
            'rfp_id': rfp_id,
            'evaluations': evaluator_evaluations
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to get final evaluations: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_consensus_ranking(request, rfp_id):
    """
    Calculate consensus ranking based on all committee evaluations
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # MULTI-TENANCY: Verify RFP belongs to tenant
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=tenant_id)
        except RFP.DoesNotExist:
            return Response({
                'error': f'RFP with ID {rfp_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # MULTI-TENANCY: Filter by tenant
        evaluations = RFPFinalEvaluation.objects.filter(rfp_id=rfp_id, tenant_id=tenant_id)
        
        if not evaluations.exists():
            return Response({
                'success': True,
                'rfp_id': rfp_id,
                'consensus_ranking': [],
                'message': 'No evaluations found'
            }, status=status.HTTP_200_OK)

        # Calculate consensus scores
        response_scores = {}
        evaluator_count = {}
        
        for evaluation in evaluations:
            response_id = evaluation.response_id
            ranking_score = float(evaluation.ranking_score)
            
            if response_id not in response_scores:
                response_scores[response_id] = 0
                evaluator_count[response_id] = 0
            
            response_scores[response_id] += ranking_score
            evaluator_count[response_id] += 1

        # Calculate average scores and create consensus ranking
        consensus_ranking = []
        for response_id, total_score in response_scores.items():
            avg_score = total_score / evaluator_count[response_id]
            
            # Get response details
            # MULTI-TENANCY: Filter by tenant
            try:
                response = RFPResponse.objects.get(response_id=response_id, tenant_id=tenant_id)
                consensus_ranking.append({
                    'response_id': response_id,
                    'vendor_name': getattr(response, 'vendor_name', 'Unknown Vendor'),
                    'org': getattr(response, 'org', 'Unknown Organization'),
                    'proposed_value': float(response.proposed_value) if response.proposed_value else 0,
                    'consensus_score': round(avg_score, 2),
                    'evaluator_count': evaluator_count[response_id]
                })
            except RFPResponse.DoesNotExist:
                continue

        # Sort by consensus score (descending)
        consensus_ranking.sort(key=lambda x: x['consensus_score'], reverse=True)
        
        # Add ranking position
        for i, item in enumerate(consensus_ranking):
            item['consensus_rank'] = i + 1

        return Response({
            'success': True,
            'rfp_id': rfp_id,
            'consensus_ranking': consensus_ranking,
            'total_evaluators': len(set(evaluations.values_list('evaluator_id', flat=True)))
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to calculate consensus ranking: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('approve_rfp')
def declare_award(request, rfp_id):
    """
    Declare award winner based on consensus ranking
    Payload:
    {
        "winning_response_id": 123,
        "award_justification": "Selected based on committee consensus",
        "awarded_by": 1
    }
    """
    try:
        data = request.data or {}
        winning_response_id = data.get('winning_response_id')
        award_justification = data.get('award_justification', '')
        awarded_by = data.get('awarded_by')

        if not winning_response_id or not awarded_by:
            return Response({
                'error': 'winning_response_id and awarded_by are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify response exists
        # MULTI-TENANCY: Filter by tenant
        try:
            response = RFPResponse.objects.get(response_id=winning_response_id, rfp_id=rfp_id, tenant_id=tenant_id)
        except RFPResponse.DoesNotExist:
            return Response({
                'error': f'Response with ID {winning_response_id} not found for RFP {rfp_id}'
            }, status=status.HTTP_404_NOT_FOUND)

        # Update RFP with award information
        # MULTI-TENANCY: Filter by tenant
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=tenant_id)
            rfp.status = 'AWARDED'
            rfp.award_decision_date = timezone.now()
            rfp.award_justification = award_justification
            rfp.save()
        except RFP.DoesNotExist:
            return Response({
                'error': f'RFP with ID {rfp_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Update response status
        response.evaluation_status = 'AWARDED'
        response.save()

        return Response({
            'success': True,
            'message': 'Award declared successfully',
            'rfp_id': rfp_id,
            'winning_response_id': winning_response_id,
            'award_justification': award_justification,
            'award_date': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to declare award: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
