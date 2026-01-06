"""
Views for RFP Evaluation Scores Management
Saves evaluation scores to the rfp_evaluation_scores table
"""

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json
from .models import RFPEvaluationScore, RFPResponse
from tprm_backend.rfp_approval.models import ApprovalRequestVersions
from .rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission
from tprm_backend.rbac.tprm_decorators import rbac_rfp_required


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('evaluate_rfp')
def save_committee_evaluation(request, rfp_id):
    """
    Save committee rankings for an RFP.
    Payload shape expected from frontend:
    {
      "rfp_id": 55,
      "evaluator_id": 28,
      "rankings": [
        { "response_id": 123, "ranking_position": 1, "ranking_score": 95, "evaluation_comments": "..." },
        ...
      ]
    }
    This endpoint updates each `RFPResponse` with the provided ranking score
    using the `weighted_final_score` field and stores comments in
    `evaluation_comments`. It does not depend on migrations and only uses
    existing columns.
    """
    try:
        data = request.data or {}
        evaluator_id = data.get('evaluator_id')
        rankings = data.get('rankings', [])

        if not isinstance(rankings, list) or len(rankings) == 0:
            return Response({
                'error': 'rankings array is required'
            }, status=status.HTTP_400_BAD_REQUEST)
          # Get RFP and update status to EVALUATION if needed
        from .models import RFP
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id)
            if rfp.status in ['SUBMISSION_OPEN', 'PUBLISHED']:
                rfp.status = 'EVALUATION'
                rfp.save()
                print(f"[STATUS UPDATE] RFP {rfp_id} status changed to EVALUATION")
        except RFP.DoesNotExist:
            pass

        updated = 0
        with transaction.atomic():
            for item in rankings:
                try:
                    response_id = int(item.get('response_id'))
                except (TypeError, ValueError):
                    continue

                ranking_score = item.get('ranking_score')
                ranking_comments = item.get('evaluation_comments', '')

                try:
                    resp = RFPResponse.objects.get(response_id=response_id, rfp_id=rfp_id)
                except RFPResponse.DoesNotExist:
                    continue

                # Persist ranking score and comments using existing fields
                try:
                    if ranking_score is not None:
                        resp.weighted_final_score = ranking_score
                    if ranking_comments:
                        resp.evaluation_comments = ranking_comments
                    # Mark as under committee evaluation
                    if not resp.evaluation_status:
                        resp.evaluation_status = 'UNDER_EVALUATION'
                    resp.last_saved_at = timezone.now()
                    resp.save()
                    updated += 1
                except Exception:
                    # Continue with remaining items
                    continue

        return Response({
            'success': True,
            'message': 'Committee rankings saved',
            'rfp_id': rfp_id,
            'updated_count': updated
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to save committee rankings: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('evaluate_rfp')
def save_evaluation_scores(request, response_id):
    """
    Save evaluation scores for an RFP response to rfp_evaluation_scores table
    Handles both draft saves and final submissions
    
    Each criterion score is saved as a separate record in the table
    """
    try:
        print(f"Saving evaluation scores for response_id: {response_id}")
        print(f"Request data: {request.data}")
        
        # Get the RFP response to validate it exists
        try:
            rfp_response = RFPResponse.objects.get(response_id=response_id)
        except RFPResponse.DoesNotExist:
            return Response({
                'error': f'RFP Response with ID {response_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
         # Update RFP status to EVALUATION if needed
        from .models import RFP
        try:
            rfp = RFP.objects.get(rfp_id=rfp_response.rfp_id)
            if rfp.status in ['SUBMISSION_OPEN', 'PUBLISHED'] and not is_draft:
                rfp.status = 'EVALUATION'
                rfp.save()
                print(f"[STATUS UPDATE] RFP {rfp.rfp_id} status changed to EVALUATION (evaluation scores saved)")
        except RFP.DoesNotExist:
            pass
        
        # Extract data from request
        evaluation_scores = request.data.get('evaluation_scores', {})
        comments = request.data.get('comments', {})
        overall_comments = request.data.get('overall_comments', '')
        evaluator_id = request.data.get('evaluator_id')
        stage_id = request.data.get('stage_id')
        approval_id = request.data.get('approval_id')
        is_draft = request.data.get('is_draft', False)
        clear_existing = request.data.get('clear_existing', False)
        
        if not evaluator_id:
            return Response({
                'error': 'evaluator_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"Evaluation scores: {evaluation_scores}")
        print(f"Comments: {comments}")
        print(f"Evaluator ID: {evaluator_id}")
        print(f"Is draft: {is_draft}")
        
        # Determine evaluation status based on draft flag
        eval_status = 'pending' if is_draft else 'completed'
        
        # Variables to track scores for summary
        technical_scores = []
        commercial_scores = []
        saved_scores = []
        updated_scores = []
        
        with transaction.atomic():
            # If clear_existing is True, delete existing scores for this evaluator
            if clear_existing:
                deleted_count = RFPEvaluationScore.objects.filter(
                    response_id=response_id,
                    evaluator_id=evaluator_id
                ).delete()[0]
                print(f"Cleared {deleted_count} existing scores for evaluator {evaluator_id}")
            
            # Process each criterion score
            for criterion_key, score_data in evaluation_scores.items():
                # Extract criterion ID from the key (might be string like "criterion_1" or just "1")
                try:
                    if isinstance(criterion_key, str) and criterion_key.startswith('criterion_'):
                        criteria_id = int(criterion_key.replace('criterion_', ''))
                    else:
                        criteria_id = int(criterion_key)
                except (ValueError, AttributeError):
                    print(f"Warning: Could not parse criteria_id from '{criterion_key}', skipping")
                    continue
                
                # Extract score data
                score_value = score_data.get('score')
                weight = score_data.get('weight', 0)
                category = score_data.get('category', 'technical')
                criterion_comment = comments.get(criterion_key, '')
                
                # Convert score to Decimal
                if score_value is not None:
                    try:
                        score_value = Decimal(str(score_value))
                    except:
                        score_value = None
                
                # Convert weight to float/int
                try:
                    weight = float(weight) if weight is not None else 0
                except (ValueError, TypeError):
                    weight = 0
                
                print(f"Processing criterion {criteria_id}: score={score_value}, weight={weight}, category={category}")
                
                # Calculate weighted score for summary
                if score_value is not None and weight > 0:
                    weighted_score = float(score_value) * float(weight) / 100
                    if category.lower() == 'technical':
                        technical_scores.append(weighted_score)
                    elif category.lower() == 'commercial':
                        commercial_scores.append(weighted_score)
                    else:
                        technical_scores.append(weighted_score)
                
                # Create or update evaluation score record
                score_obj, created = RFPEvaluationScore.objects.update_or_create(
                    response_id=response_id,
                    criteria_id=criteria_id,
                    evaluator_id=evaluator_id,
                    defaults={
                        'score_value': score_value,
                        'comments': criterion_comment,
                        'evaluation_status': eval_status,
                        'auto_calculated': False,
                        'raw_response': json.dumps(score_data) if score_data else None
                    }
                )
                
                if created:
                    saved_scores.append(criteria_id)
                    print(f"Created new score record for criterion {criteria_id}")
                else:
                    updated_scores.append(criteria_id)
                    print(f"Updated existing score record for criterion {criteria_id}")
            
            # Calculate total scores
            technical_score = sum(technical_scores) if technical_scores else None
            commercial_score = sum(commercial_scores) if commercial_scores else None
            overall_score = (technical_score or 0) + (commercial_score or 0) if (technical_score or commercial_score) else None
            
            print(f"Calculated scores - Technical: {technical_score}, Commercial: {commercial_score}, Overall: {overall_score}")
            
            # Update the RFP response with aggregate scores if not a draft
            if not is_draft:
                if technical_score is not None:
                    rfp_response.technical_score = Decimal(str(technical_score))
                if commercial_score is not None:
                    rfp_response.commercial_score = Decimal(str(commercial_score))
                if overall_score is not None:
                    rfp_response.overall_score = Decimal(str(overall_score))
                
                # Update evaluation status
                if rfp_response.evaluation_status == 'SUBMITTED':
                    rfp_response.evaluation_status = 'UNDER_EVALUATION'
                
                rfp_response.evaluated_by = evaluator_id
                rfp_response.evaluation_date = timezone.now()
                
                # Store overall comments in evaluation_comments field
                if overall_comments:
                    rfp_response.evaluation_comments = overall_comments
                
                rfp_response.save()
                print(f"Updated RFP Response with aggregate scores")
        
        return Response({
            'success': True,
            'message': 'Evaluation scores saved successfully' if not is_draft else 'Draft saved successfully',
            'response_id': response_id,
            'evaluator_id': evaluator_id,
            'technical_score': float(technical_score) if technical_score else None,
            'commercial_score': float(commercial_score) if commercial_score else None,
            'overall_score': float(overall_score) if overall_score else None,
            'is_draft': is_draft,
            'scores_created': len(saved_scores),
            'scores_updated': len(updated_scores),
            'total_criteria_scored': len(saved_scores) + len(updated_scores),
            'criteria_ids_saved': saved_scores,
            'criteria_ids_updated': updated_scores
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error saving evaluation scores: {str(e)}")
        print(f"Full traceback: {error_traceback}")
        return Response({
            'error': 'Failed to save evaluation scores',
            'details': str(e),
            'traceback': error_traceback
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_evaluation_scores(request, response_id):
    """
    Get evaluation scores for an RFP response from rfp_evaluation_scores table
    """
    try:
        # Get the RFP response to validate it exists
        try:
            rfp_response = RFPResponse.objects.get(response_id=response_id)
        except RFPResponse.DoesNotExist:
            return Response({
                'error': f'RFP Response with ID {response_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get query parameters for filtering
        evaluator_id = request.query_params.get('evaluator_id')
        stage_id = request.query_params.get('stage_id')
        criteria_id = request.query_params.get('criteria_id')
        
        # Query evaluation scores
        scores_query = RFPEvaluationScore.objects.filter(response_id=response_id)
        
        if evaluator_id:
            scores_query = scores_query.filter(evaluator_id=evaluator_id)
        if criteria_id:
            scores_query = scores_query.filter(criteria_id=criteria_id)
        
        # Get all matching scores
        scores = scores_query.order_by('criteria_id')
        
        # Format scores for response
        scores_data = []
        for score in scores:
            score_dict = {
                'score_id': score.score_id,
                'response_id': score.response_id,
                'criteria_id': score.criteria_id,
                'evaluator_id': score.evaluator_id,
                'score_value': float(score.score_value) if score.score_value else None,
                'comments': score.comments,
                'evaluation_status': score.evaluation_status,
                'auto_calculated': score.auto_calculated,
                'evaluation_date': score.evaluation_date.isoformat() if score.evaluation_date else None,
                'raw_response': score.raw_response
            }
            scores_data.append(score_dict)
        
        # Group scores by evaluator
        evaluators = {}
        for score_dict in scores_data:
            eval_id = score_dict['evaluator_id']
            if eval_id not in evaluators:
                evaluators[eval_id] = {
                    'evaluator_id': eval_id,
                    'scores': []
                }
            evaluators[eval_id]['scores'].append(score_dict)
        
        return Response({
            'success': True,
            'response_id': response_id,
            'rfp_id': rfp_response.rfp_id,
            'vendor_name': rfp_response.vendor_name,
            'technical_score': float(rfp_response.technical_score) if rfp_response.technical_score else None,
            'commercial_score': float(rfp_response.commercial_score) if rfp_response.commercial_score else None,
            'overall_score': float(rfp_response.overall_score) if rfp_response.overall_score else None,
            'evaluation_status': rfp_response.evaluation_status,
            'evaluation_comments': rfp_response.evaluation_comments,
            'scores_count': len(scores_data),
            'scores': scores_data,
            'evaluators': list(evaluators.values())
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error getting evaluation scores: {str(e)}")
        print(f"Full traceback: {error_traceback}")
        return Response({
            'error': 'Failed to get evaluation scores',
            'details': str(e),
            'traceback': error_traceback
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_evaluation_scores_bulk(request):
    """
    Get evaluation scores for multiple RFP responses from rfp_evaluation_scores table
    Accepts comma-separated response_ids as query parameter
    Returns scores grouped by response_id for mean calculation
    """
    try:
        # Get response_ids from query parameters
        response_ids_param = request.query_params.get('response_ids', '')
       
        if not response_ids_param:
            return Response({
                'success': False,
                'error': 'response_ids parameter is required (comma-separated)'
            }, status=status.HTTP_400_BAD_REQUEST)
       
        # Parse response_ids
        try:
            response_ids = [int(rid.strip()) for rid in response_ids_param.split(',') if rid.strip()]
        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid response_ids format. Expected comma-separated integers.'
            }, status=status.HTTP_400_BAD_REQUEST)
       
        if not response_ids:
            return Response({
                'success': False,
                'error': 'No valid response_ids provided'
            }, status=status.HTTP_400_BAD_REQUEST)
       
        # Query evaluation scores for all response_ids
        scores_query = RFPEvaluationScore.objects.filter(
            response_id__in=response_ids,
            evaluation_status='completed'  # Only get completed evaluations
        ).order_by('response_id', 'criteria_id', 'evaluator_id')
       
        # Get all matching scores
        scores = scores_query
       
        # Format scores for response
        scores_data = []
        for score in scores:
            score_dict = {
                'score_id': score.score_id,
                'response_id': score.response_id,
                'criteria_id': score.criteria_id,
                'evaluator_id': score.evaluator_id,
                'score_value': float(score.score_value) if score.score_value else None,
                'comments': score.comments,
                'evaluation_status': score.evaluation_status,
                'auto_calculated': score.auto_calculated,
                'evaluation_date': score.evaluation_date.isoformat() if score.evaluation_date else None,
                'raw_response': score.raw_response
            }
            scores_data.append(score_dict)
       
        # Group scores by response_id for easier processing on frontend
        scores_by_response = {}
        for score_dict in scores_data:
            resp_id = score_dict['response_id']
            if resp_id not in scores_by_response:
                scores_by_response[resp_id] = []
            scores_by_response[resp_id].append(score_dict)
       
        return Response({
            'success': True,
            'response_ids': response_ids,
            'total_scores': len(scores_data),
            'scores_by_response': scores_by_response,
            'scores': scores_data  # Flat list for backward compatibility
        }, status=status.HTTP_200_OK)
       
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error getting bulk evaluation scores: {str(e)}")
        print(f"Full traceback: {error_traceback}")
        return Response({
            'success': False,
            'error': 'Failed to get evaluation scores',
            'details': str(e),
            'traceback': error_traceback
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 