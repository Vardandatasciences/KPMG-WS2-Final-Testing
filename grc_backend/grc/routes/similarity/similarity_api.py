"""
API endpoints for similarity detection (Step 1 of 9-step pipeline).

Endpoints:
- POST /api/similarity-check/ : Initiate similarity check (Step 1)
- GET  /api/similarity-check/<id>/ : Get check status
- POST /api/similarity-check/<id>/confirm/ : Submit user decision
- GET  /api/similarity-check/config/ : Get similarity configuration
"""

import json
import logging
from typing import Dict, Any, Optional

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from ...jwt_auth import UnifiedJWTAuthentication
from ...tenant_utils import require_tenant, get_tenant_id_from_request
from ...models import Framework, Policy, SubPolicy, Compliance, Users
from ...services.similarity_service import (
    SimilarityService,
    SimilarityCheckRequest,
    check_framework_similarity,
    check_policy_similarity,
    check_subpolicy_similarity,
    check_compliance_similarity,
)
from ...models_extensions.similarity_models import SimilarityCheckAudit
from ...rbac.decorators import rbac_required

logger = logging.getLogger(__name__)


# ============== STEP 1: INITIATE SIMILARITY CHECK ==============

@api_view(['POST'])
@authentication_classes([UnifiedJWTAuthentication])
@require_tenant
def similarity_check(request):
    """
    POST /api/similarity-check/
    
    Initiate Step 1 (Text Cleaning) and subsequent pipeline steps.
    
    Request body varies by item_type:
    
    For Framework:
    {
        "item_type": "Framework",
        "data": {
            "FrameworkName": "ISO 27001",
            "FrameworkDescription": "Information security framework",
            "Category": "Cybersecurity",
            "Domain": {"DomainName": "Information Technology"},
            "InternalExternal": "External",
            "Identifier": "ISO-27001:2022"
        }
    }
    
    For Policy:
    {
        "item_type": "Policy",
        "parent_framework_id": 123,
        "data": {
            "PolicyName": "Password Policy",
            "PolicyDescription": "Defines password requirements",
            "PolicyType": "Standard",
            "PolicyCategory": "Security",
            "PolicySubCategory": "Access Control",
            "Scope": "All employees",
            "Objective": "Ensure strong passwords"
        }
    }
    
    For SubPolicy:
    {
        "item_type": "SubPolicy",
        "parent_framework_id": 123,
        "parent_policy_id": 456,
        "data": {
            "SubPolicyName": "Password Length",
            "Description": "Minimum password length requirements",
            "Control": "Passwords must be 12+ characters",
            "Identifier": "SP-001"
        }
    }
    
    For Compliance:
    {
        "item_type": "Compliance",
        "parent_framework_id": 123,
        "parent_policy_id": 456,
        "parent_subpolicy_id": 789,
        "data": {
            "ComplianceTitle": "Quarterly Access Review",
            "ComplianceItemDescription": "Review user access rights quarterly",
            "ComplianceType": "Control",
            "Scope": "All privileged accounts",
            "Objective": "Prevent unauthorized access",
            "Criticality": "High",
            "RiskCategory": "Access Control",
            "Identifier": "COMP-045"
        }
    }
    
    Response:
    {
        "success": true,
        "check_id": 123,
        "status": "PENDING",
        "message": "Step 1 (Text Cleaning) completed. Cleaned text prepared for next steps.",
        "step1_result": {
            "cleaned_text": "ISO 27001 | Information security framework | Category: cybersecurity | Domain: Information Technology | Type: External | Identifier: ISO-27001:2022",
            "changes_made": ["Normalized FrameworkName", "Cleaned FrameworkDescription"],
            "entity_type": "Framework"
        }
    }
    """
    try:
        # Parse request body
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        
        item_type = data.get('item_type')
        item_data = data.get('data', {})
        
        if not item_type or not item_data:
            return JsonResponse({
                'success': False,
                'error': 'item_type and data are required'
            }, status=400)
        
        # Get tenant and user context
        tenant_id = get_tenant_id_from_request(request)
        user_id = getattr(request.user, 'UserId', None) or getattr(request.user, 'id', None)
        
        # Get parent IDs from request
        parent_framework_id = data.get('parent_framework_id')
        parent_policy_id = data.get('parent_policy_id')
        parent_subpolicy_id = data.get('parent_subpolicy_id')
        
        # Build request
        check_request = SimilarityCheckRequest(
            item_type=item_type,
            item_data=item_data,
            tenant_id=tenant_id,
            user_id=user_id,
            parent_framework_id=parent_framework_id,
            parent_policy_id=parent_policy_id,
            parent_subpolicy_id=parent_subpolicy_id,
        )
        
        # Execute Step 1 and initiate pipeline
        service = SimilarityService.get_service_for_tenant(tenant_id)
        
        # Step 1: Clean text
        cleaning_result, audit = service.step1_clean_text(check_request)
        
        # TODO: Steps 2-6 will be implemented here
        # For now, we return Step 1 result with pending status
        
        return JsonResponse({
            'success': True,
            'check_id': audit.id,
            'status': 'PENDING',
            'message': 'Step 1 (Text Cleaning) completed successfully. Hybrid format: Structured JSON + Embedding text prepared.',
            'step1_result': {
                'structured_json': cleaning_result.structured_json,  # For storage/querying
                'embedding_text': cleaning_result.embedding_text,  # For embedding similarity
                'changes_made': cleaning_result.changes_made,
                'entity_type': cleaning_result.entity_type,
                'timestamp': cleaning_result.timestamp,
            },
            'hybrid_approach': {
                'structured_json': 'Stored in MySQL for querying, debugging, future reuse',
                'embedding_text': 'Used for BGE-M3 embedding generation → Qdrant vector search',
            },
            'next_steps': [
                'Step 2: Domain Classification',
                'Step 3: Embedding Creation',
                'Step 4: Vector Search',
                'Step 5: Cross-Encoder Reranker',
                'Step 6: LLM Final Decision'
            ]
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.exception(f"Similarity check failed: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Similarity check failed: {str(e)}'
        }, status=500)


# ============== GET CHECK STATUS ==============

@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
@require_tenant
def get_similarity_check_status(request, check_id):
    """
    GET /api/similarity-check/<check_id>/
    
    Get status and results of a similarity check.
    """
    try:
        tenant_id = get_tenant_id_from_request(request)
        
        audit = SimilarityCheckAudit.objects.get(
            id=check_id,
            tenant_id=tenant_id
        )
        
        response = {
            'success': True,
            'check_id': audit.id,
            'status': audit.check_status,
            'item_type': audit.item_type,
            'proposed': {
                'name': audit.proposed_name,
                'description': audit.proposed_description,
                'structured_json': audit.proposed_structured_json,  # For storage/querying
                'embedding_text': audit.proposed_cleaned_text,  # For similarity search
            },
            'classification': {
                'domain': audit.classified_domain,
                'category': audit.classified_category,
                'confidence': audit.classification_confidence,
            },
            'llm_analysis': {
                'classification': audit.llm_classification,
                'confidence': audit.llm_confidence,
                'reasoning': audit.llm_reasoning,
                'suggested_action': audit.llm_suggested_action,
            } if audit.llm_classification else None,
            'candidates': audit.candidates_found,
            'user_decision': {
                'decision': audit.user_decision,
                'selected_existing_id': audit.selected_existing_id,
            } if audit.user_decision else None,
            'final_outcome': {
                'action': audit.final_action,
                'created_entity_id': audit.created_entity_id,
            } if audit.final_action else None,
            'timestamps': {
                'started': audit.started_at.isoformat() if audit.started_at else None,
                'completed': audit.completed_at.isoformat() if audit.completed_at else None,
            },
            'hybrid_approach': {
                'structured_json': 'Queryable, reusable, future-proof (MySQL storage)',
                'embedding_text': 'BGE-M3 → Qdrant vector search',
            },
            'error': audit.error_message,
        }
        
        return JsonResponse(response)
        
    except SimilarityCheckAudit.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Similarity check not found'
        }, status=404)
    except Exception as e:
        logger.exception(f"Failed to get check status: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============== SUBMIT USER DECISION ==============

@api_view(['POST'])
@authentication_classes([UnifiedJWTAuthentication])
@require_tenant
def confirm_similarity_decision(request, check_id):
    """
    POST /api/similarity-check/<check_id>/confirm/
    
    Step 8: User submits their decision.
    
    Request body:
    {
        "decision": "CREATE_NEW",  // or "USE_EXISTING", "MERGE"
        "selected_existing_id": null,  // required if USE_EXISTING or MERGE
        "selected_existing_type": null   // required if USE_EXISTING or MERGE
    }
    
    Response:
    {
        "success": true,
        "message": "Decision recorded. Proceeding with final action.",
        "action": "CREATE_NEW"
    }
    """
    try:
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        tenant_id = get_tenant_id_from_request(request)
        
        audit = SimilarityCheckAudit.objects.get(
            id=check_id,
            tenant_id=tenant_id
        )
        
        decision = data.get('decision')
        selected_id = data.get('selected_existing_id')
        selected_type = data.get('selected_existing_type')
        
        if decision not in ['USE_EXISTING', 'CREATE_NEW', 'MERGE']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid decision. Must be USE_EXISTING, CREATE_NEW, or MERGE'
            }, status=400)
        
        if decision in ['USE_EXISTING', 'MERGE'] and not selected_id:
            return JsonResponse({
                'success': False,
                'error': 'selected_existing_id required for USE_EXISTING or MERGE'
            }, status=400)
        
        # Record decision
        audit.user_decision = decision
        audit.selected_existing_id = selected_id
        audit.selected_existing_type = selected_type
        audit.save(update_fields=['user_decision', 'selected_existing_id', 'selected_existing_type'])
        
        # TODO: Step 9 - Save to DB, Qdrant, complete audit
        
        return JsonResponse({
            'success': True,
            'message': f'Decision recorded: {decision}',
            'action': decision,
            'check_id': audit.id,
            'next_step': 'Step 9: Final save to MySQL + Qdrant + Audit log'
        })
        
    except SimilarityCheckAudit.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Similarity check not found'
        }, status=404)
    except Exception as e:
        logger.exception(f"Failed to confirm decision: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============== UTILITY ENDPOINTS ==============

@api_view(['GET'])
@authentication_classes([UnifiedJWTAuthentication])
def get_similarity_config(request):
    """
    GET /api/similarity-check/config/
    
    Get similarity detection configuration.
    """
    from ...models_extensions.similarity_models import SimilarityConfiguration
    
    try:
        tenant_id = get_tenant_id_from_request(request)
        config = SimilarityConfiguration.get_for_tenant(tenant_id)
        
        return JsonResponse({
            'success': True,
            'config': {
                'embedding_model': config.embedding_model,
                'embedding_dimension': config.embedding_dimension,
                'reranker_model': config.reranker_model,
                'thresholds': {
                    'duplicate': config.threshold_duplicate,
                    'similar': config.threshold_similar,
                    'related': config.threshold_related,
                },
                'search_settings': {
                    'max_candidates': config.max_candidates,
                    'top_k_rerank': config.top_k_rerank,
                },
                'llm_settings': {
                    'model': config.llm_model,
                    'temperature': config.llm_temperature,
                },
                'enabled_steps': {
                    'step1_cleaning': config.enable_step1_cleaning,
                    'step2_classification': config.enable_step2_classification,
                    'step3_embedding': config.enable_step3_embedding,
                    'step4_vector_search': config.enable_step4_vector_search,
                    'step5_reranker': config.enable_step5_reranker,
                    'step6_llm': config.enable_step6_llm,
                }
            }
        })
    except Exception as e:
        logger.exception(f"Failed to get config: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
