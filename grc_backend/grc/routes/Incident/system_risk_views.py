"""
System Identified Risk Queue API Views
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
import threading
import uuid
import time

from ...models import SystemIdentifiedRiskQueue, Department, Users
from ...jwt_auth import UnifiedJWTAuthentication
from ...tenant_utils import get_tenant_id_from_request, require_tenant
from .system_risk_service import (
    generate_risk_candidates_from_incidents,
    generate_risk_candidates_from_multiple_sources,
    generate_risk_candidates_from_synthetic_sources,
    generate_risk_candidates_from_document,
    find_latest_risk_document,
    create_risk_from_queue_entry,
    create_risk_from_queue_entry_for_workflow,
    get_queue_statistics,
    update_queue_entry_review,
    reject_queue_entry,
    get_external_portals_list,
)
import json

# In-memory job state for synthetic analysis progress (dev-safe, process-local).
_SYNTHETIC_ANALYSIS_JOBS = {}
_SYNTHETIC_ANALYSIS_LOCK = threading.Lock()


def _resolve_actor_user_id(user):
    """
    Resolve business user id consistently across auth backends.
    Prefer `userid` (used in this codebase), then fallback to Django `id`.
    """
    raw = getattr(user, 'userid', None)
    if raw is None:
        raw = getattr(user, 'id', None)
    try:
        return int(raw) if raw is not None else None
    except Exception:
        return raw


def _derive_confidence_for_response(item):
    """Provide confidence details even for older records missing factor metadata."""
    ai_meta = item.ai_metadata or {}
    factors = ai_meta.get("confidence_factors") if isinstance(ai_meta, dict) else None
    justification = ai_meta.get("confidence_justification") if isinstance(ai_meta, dict) else ""
    score = item.confidence_score

    if isinstance(factors, list) and factors:
        return score or 0, justification or "", factors

    def _clamp(v, lo, hi):
        return max(lo, min(hi, v))

    likelihood = _clamp(int(item.likelihood or 5), 1, 10)
    impact = _clamp(int(item.impact or 5), 1, 10)
    exposure = likelihood * impact
    text_len = len((item.risk_description or "")) + len((item.ai_reasoning or "")) + len((item.possible_damage or ""))
    mitigation_steps = item.mitigation_steps if isinstance(item.mitigation_steps, list) else []
    business_impact = item.business_impact if isinstance(item.business_impact, list) else []

    evidence = _clamp(round(min(text_len / 6, 100)), 20, 100)
    severity = _clamp(round((exposure / 100) * 100), 20, 100)
    mitigation_quality = _clamp(round((len(mitigation_steps) / 5) * 100), 20, 100)
    impact_coverage = _clamp(round((len(business_impact) / 5) * 100), 20, 100)
    consistency = _clamp(round(100 - abs(exposure - 56)), 20, 100)

    factors = [
        {"name": "Evidence quality", "score": evidence, "reason": f"AI description/reasoning depth ({text_len} chars)"},
        {"name": "Severity strength", "score": severity, "reason": f"likelihood={likelihood}, impact={impact}, exposure={exposure}"},
        {"name": "Mitigation quality", "score": mitigation_quality, "reason": f"{len(mitigation_steps)} mitigation steps"},
        {"name": "Business impact coverage", "score": impact_coverage, "reason": f"{len(business_impact)} impact dimensions"},
        {"name": "Scoring consistency", "score": consistency, "reason": "alignment across exposure, criticality, and priority"},
    ]

    weighted = (evidence * 0.27) + (severity * 0.18) + (consistency * 0.23) + (mitigation_quality * 0.17) + (impact_coverage * 0.15)
    final_score = int(round(_clamp(weighted, 35, 97)))
    justification = f"Confidence {final_score}% based on evidence quality and likelihood-impact alignment."
    return final_score, justification, factors


def _get_source_details(risk):
    """Enrich response with detailed source record information."""
    tenant_id = risk.tenant_id
    source_module = risk.source_module
    source_record_id = risk.source_record_id
    ai_meta = risk.ai_metadata or {}
    
    details = {
        'module': source_module,
        'record_id': source_record_id,
        'title': risk.source_ref,
        'description': '',
        'link': '',
        'extra_info': {}
    }
    
    try:
        from ...models import Incident, Compliance, FileOperations
        
        if source_module == SystemIdentifiedRiskQueue.SOURCE_INCIDENT:
            # Try to get descriptive metadata from ai_meta first (saved during scan)
            details['title'] = ai_meta.get('source_title', risk.source_ref)
            details['description'] = ai_meta.get('source_text', '')
            
            # Fallback to database if needed
            if not details['description']:
                incident = Incident.objects.filter(IncidentId=source_record_id, tenant_id=tenant_id).first()
                if incident:
                    details['title'] = incident.IncidentTitle
                    details['description'] = incident.Description
                    details['extra_info']['date'] = incident.Date.isoformat() if hasattr(incident, 'Date') and incident.Date else None
                    details['extra_info']['category'] = getattr(incident, 'IncidentCategory', '')
                    
        elif source_module == SystemIdentifiedRiskQueue.SOURCE_COMPLIANCE:
            comp = Compliance.objects.filter(ComplianceId=source_record_id, tenant_id=tenant_id).first()
            if comp:
                details['title'] = comp.ComplianceTitle
                details['description'] = comp.ComplianceItemDescription
                details['extra_info']['type'] = comp.ComplianceType
                
        elif source_module == SystemIdentifiedRiskQueue.SOURCE_EXTERNAL or (source_module == 'INTEGRATION' and risk.source_ref.startswith('External:')):
            details['title'] = ai_meta.get('source_title', risk.source_ref.replace('External:', '').strip())
            details['description'] = ai_meta.get('source_text', '')
            details['link'] = ai_meta.get('source_url', '')
            
        elif source_module == SystemIdentifiedRiskQueue.SOURCE_INTEGRATION:
            # Check if it's a document upload
            file_id = ai_meta.get('file_id')
            if file_id:
                file_op = FileOperations.objects.filter(id=file_id, tenant_id=tenant_id).first()
                if file_op:
                    details['title'] = file_op.original_name
                    details['link'] = file_op.s3_url
                    details['description'] = f"Extracted from document: {file_op.original_name}"

    except Exception as e:
        print(f"[SYSTEM-RISK] Error fetching source details: {e}")
        
    return details


# DRF Session auth variant that skips CSRF enforcement for API clients.
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_tenant
@csrf_exempt
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
def run_incident_risk_scan(request):
    """Run AI scan on incidents to generate risk candidates."""
    tenant_id = get_tenant_id_from_request(request)
    requested_limit = request.data.get('limit', 50)
    # Safety cap so we don't run huge scans while validating workflow.
    # Frontend may still send an older value during dev/HMR/build lag.
    try:
        requested_limit = int(requested_limit)
    except Exception:
        requested_limit = 50
    limit = min(requested_limit, 5)
    
    print(f"[API] run_incident_risk_scan: tenant={tenant_id}, requested_limit={requested_limit}, effective_limit={limit}")
    
    try:
        results = generate_risk_candidates_from_incidents(tenant_id, limit)
        return Response({
            'status': 'success',
            'message': f"Scan completed. Created {results['created']} new risk candidates.",
            'results': results
        })
    except Exception as e:
        print(f"[API] run_incident_risk_scan error: {e}")
        return Response({
            'status': 'error',
            'message': f'Scan failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@require_tenant
@csrf_exempt
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
def run_manual_risk_scan(request):
    """Run AI scan on multiple manually selected sources to generate risk candidates."""
    tenant_id = get_tenant_id_from_request(request)
    def _to_int_list(values):
        if not isinstance(values, list):
            return []
        out = []
        for value in values:
            try:
                out.append(int(value))
            except Exception:
                continue
        return list(dict.fromkeys(out))
    
    # New multi-source payload
    source_types = request.data.get('source_types', [])
    if not source_types and 'source_type' in request.data:
        source_types = [request.data.get('source_type')]
        
    subfolder_ids = _to_int_list(request.data.get('subfolder_ids', []))
    document_ids = _to_int_list(request.data.get('document_ids', []))
    run_checklist = request.data.get('run_checklist', False)
    external_urls = request.data.get('external_urls', [])
    requested_limit = request.data.get('limit', 5)
    
    try:
        requested_limit = int(requested_limit)
    except Exception:
        requested_limit = 5
    limit = min(requested_limit, 10) # Increased limit for multi-source
    
    print(f"[API] run_manual_risk_scan: tenant={tenant_id}, sources={source_types}, subfolders={subfolder_ids}, docs={document_ids}, external_urls={external_urls}, checklist={run_checklist}, limit={limit}")
    
    try:
        results = generate_risk_candidates_from_multiple_sources(
            tenant_id=tenant_id, 
            source_types=source_types, 
            limit=limit,
            subfolder_ids=subfolder_ids,
            document_ids=document_ids,
            run_checklist=run_checklist,
            external_urls=external_urls
        )
        return Response({
            'status': 'success',
            'message': f"Scan completed for {', '.join(source_types) if source_types else 'requested sources'}. Created {results['created']} new risk candidates.",
            'results': results
        })
    except Exception as e:
        print(f"[API] run_manual_risk_scan error: {e}")
        return Response({
            'status': 'error',
            'message': f'Scan failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_tenant
@csrf_exempt
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
def run_synthetic_risk_test_analysis(request):
    """Run AI risk test analysis on synthetic multi-module source data."""
    tenant_id = get_tenant_id_from_request(request)
    requested_limit = request.data.get('limit', 100)
    try:
        requested_limit = int(requested_limit)
    except Exception:
        requested_limit = 100
    limit = min(max(requested_limit, 1), 200)

    print(f"[API] run_synthetic_risk_test_analysis: tenant={tenant_id}, requested_limit={requested_limit}, effective_limit={limit}")

    job_id = str(uuid.uuid4())
    started_at = time.time()
    with _SYNTHETIC_ANALYSIS_LOCK:
        _SYNTHETIC_ANALYSIS_JOBS[job_id] = {
            "tenant_id": tenant_id,
            "status": "running",
            "cancel_requested": False,
            "processed": 0,
            "total": 0,
            "progress_pct": 0,
            "last_record": None,
            "results": None,
            "error": None,
            "started_at": started_at,
            "finished_at": None,
        }

    def _update_progress(*, processed, total, phase, last_record):
        pct = int((processed / total) * 100) if total else 0
        with _SYNTHETIC_ANALYSIS_LOCK:
            job = _SYNTHETIC_ANALYSIS_JOBS.get(job_id)
            if not job:
                return
            job["processed"] = processed
            job["total"] = total
            job["progress_pct"] = max(0, min(100, pct))
            job["last_record"] = last_record
            if phase == "completed":
                job["progress_pct"] = 100
            elif phase == "cancelled":
                job["status"] = "cancelled"

    def _run_job():
        def _should_abort():
            with _SYNTHETIC_ANALYSIS_LOCK:
                job = _SYNTHETIC_ANALYSIS_JOBS.get(job_id)
                return bool(job and job.get("cancel_requested"))

        try:
            # Smart Scan: Check for document first
            file_op, link = find_latest_risk_document(tenant_id)
            
            if file_op:
                print(f"[API] Smart Scan: Found document {file_op.original_name}. Using document-based analysis.")
                results = generate_risk_candidates_from_document(
                    tenant_id,
                    file_op,
                    link=link,
                    progress_callback=_update_progress,
                    should_abort=_should_abort
                )
            else:
                print("[API] Smart Scan: No document found. Falling back to synthetic sources.")
                results = generate_risk_candidates_from_synthetic_sources(
                    tenant_id,
                    limit,
                    progress_callback=_update_progress,
                    should_abort=_should_abort
                )
                
            with _SYNTHETIC_ANALYSIS_LOCK:
                job = _SYNTHETIC_ANALYSIS_JOBS.get(job_id)
                if job is not None:
                    if job.get("cancel_requested"):
                        job["status"] = "cancelled"
                    else:
                        job["status"] = "completed"
                    job["results"] = results
                    job["finished_at"] = time.time()
                    if job["status"] == "completed":
                        job["progress_pct"] = 100
        except Exception as e:
            print(f"[API] run_synthetic_risk_test_analysis background error: {e}")
            with _SYNTHETIC_ANALYSIS_LOCK:
                job = _SYNTHETIC_ANALYSIS_JOBS.get(job_id)
                if job is not None:
                    job["status"] = "failed"
                    job["error"] = str(e)
                    job["finished_at"] = time.time()

    threading.Thread(target=_run_job, daemon=True).start()

    return Response({
        "status": "accepted",
        "message": "Risk test analysis started.",
        "job_id": job_id
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_tenant
def get_synthetic_risk_test_analysis_status(request, job_id):
    """Get live status/progress for a synthetic risk test analysis job."""
    tenant_id = get_tenant_id_from_request(request)
    with _SYNTHETIC_ANALYSIS_LOCK:
        job = _SYNTHETIC_ANALYSIS_JOBS.get(job_id)
        if not job or job.get("tenant_id") != tenant_id:
            return Response({
                "status": "error",
                "message": "Job not found."
            }, status=status.HTTP_404_NOT_FOUND)

        payload = {
            "status": "success",
            "job": {
                "job_id": job_id,
                "state": job.get("status"),
                "processed": job.get("processed", 0),
                "total": job.get("total", 0),
                "progress_pct": job.get("progress_pct", 0),
                "last_record": job.get("last_record"),
                "started_at": job.get("started_at"),
                "finished_at": job.get("finished_at"),
                "error": job.get("error"),
                "results": job.get("results"),
            }
        }
    return Response(payload)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_tenant
@csrf_exempt
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
def cancel_synthetic_risk_test_analysis(request, job_id):
    """Request cancellation for a running synthetic risk test analysis job."""
    tenant_id = get_tenant_id_from_request(request)
    with _SYNTHETIC_ANALYSIS_LOCK:
        job = _SYNTHETIC_ANALYSIS_JOBS.get(job_id)
        if not job or job.get("tenant_id") != tenant_id:
            return Response({
                "status": "error",
                "message": "Job not found."
            }, status=status.HTTP_404_NOT_FOUND)

        if job.get("status") in ("completed", "failed", "cancelled"):
            return Response({
                "status": "success",
                "message": f"Job already {job.get('status')}.",
                "job_state": job.get("status")
            })

        job["cancel_requested"] = True
        job["status"] = "cancelling"

    return Response({
        "status": "success",
        "message": "Cancellation requested.",
        "job_state": "cancelling"
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_tenant
def list_system_risk_queue(request):
    """List system identified risks with filtering."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] list_system_risk_queue: tenant={tenant_id}")
    
    # Build query
    queryset = SystemIdentifiedRiskQueue.objects.filter(tenant_id=tenant_id)
    
    # Apply filters
    source_filter = request.GET.get('source')
    if source_filter:
        if source_filter == 'EXTERNAL_SOURCES':
            # Filter for INTEGRATION module but only those with External prefix
            queryset = queryset.filter(source_module='INTEGRATION', source_ref__startswith='External:')
        else:
            queryset = queryset.filter(source_module=source_filter)
        print(f"[API] Filtering by source: {source_filter}")
    
    status_filter = request.GET.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
        print(f"[API] Filtering by status: {status_filter}")
    
    category_filter = request.GET.get('category')
    if category_filter:
        queryset = queryset.filter(category__icontains=category_filter)
        print(f"[API] Filtering by category: {category_filter}")

    functional_area_filter = request.GET.get('functional_area')
    if functional_area_filter:
        queryset = queryset.filter(functional_area=functional_area_filter)
        print(f"[API] Filtering by functional_area: {functional_area_filter}")

    velocity_filter = request.GET.get('velocity_min')
    if velocity_filter:
        try:
            queryset = queryset.filter(velocity_score__gte=int(velocity_filter))
            print(f"[API] Filtering by velocity_min: {velocity_filter}")
        except Exception:
            pass
    
    # Order by creation date (newest first)
    queryset = queryset.order_by('-created_at')
    
    # Pagination
    def _safe_int(value, default: int) -> int:
        if value is None:
            return default
        if isinstance(value, str) and value.strip().lower() in ("", "undefined", "null"):
            return default
        try:
            return int(value)
        except Exception:
            return default

    page = _safe_int(request.GET.get('page', 1), 1)
    page_size = _safe_int(request.GET.get('page_size', 20), 20)
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = queryset.count()
    items = queryset[start:end]
    
    print(f"[API] Found {total_count} total items, returning page {page} ({len(items)} items)")
    
    # Serialize data
    data = []
    for item in items:
        final_score, confidence_justification, confidence_factors = _derive_confidence_for_response(item)
        
        # Get risk instance ID + assigned reviewer if this risk has been sent for approval
        risk_instance_id = None
        reviewer_id = None
        effective_status = item.status
        if item.status == 'ACCEPTED_PENDING_APPROVAL':
            from django.db import connection
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            ri.RiskInstanceId,
                            ra.ApproverId,
                            ri.RiskStatus
                        FROM grc2.risk_instance ri 
                        LEFT JOIN grc2.risk_approval ra
                          ON ra.RiskInstanceId = ri.RiskInstanceId
                         AND ra.version = (
                           SELECT MAX(ra2.version)
                           FROM grc2.risk_approval ra2
                           WHERE ra2.RiskInstanceId = ri.RiskInstanceId
                         )
                        WHERE JSON_UNQUOTE(JSON_EXTRACT(ri.RiskFormDetails, '$.source_queue_id')) = %s
                          AND ri.TenantId = %s
                        ORDER BY ri.RiskInstanceId DESC
                        LIMIT 1
                    """, [str(item.id), item.tenant_id])
                    result = cursor.fetchone()
                    if result:
                        risk_instance_id = result[0]
                        reviewer_id = result[1]
                        risk_instance_status = (result[2] or '').strip().lower()
                        # Backfill/reflect queue status from workflow result for old records.
                        if risk_instance_status == 'approved':
                            effective_status = 'APPROVED_ADDED'
                        elif risk_instance_status == 'rejected':
                            effective_status = 'REJECTED'
            except Exception as e:
                print(f"Error getting risk instance ID for queue item {item.id}: {e}")
        # If effective status differs, persist it so UI and metrics stay correct.
        if effective_status != item.status:
            item.status = effective_status
            if effective_status == 'APPROVED_ADDED':
                item.approved_at = item.approved_at or timezone.now()
            if effective_status in ('APPROVED_ADDED', 'REJECTED'):
                item.reviewed_at = item.reviewed_at or timezone.now()
            item.save(update_fields=['status', 'approved_at', 'reviewed_at'])
        
        data.append({
            'id': item.id,
            'source_module': item.source_module,
            'source_ref': item.source_ref,
            'source_title': _get_source_details(item).get('title', item.source_ref),
            'risk_title': item.risk_title,
            'risk_type': item.risk_type,
            'category': item.category,
            'criticality': item.criticality,
            'confidence_score': final_score,
            'velocity_score': item.velocity_score,
            'functional_area': item.functional_area,
            'likelihood': item.likelihood,
            'impact': item.impact,
            'exposure_rating': item.exposure_rating,
            'priority': item.priority,
            'ai_reasoning': item.ai_reasoning,
            'inherent_risk_score': item.inherent_risk_score,
            'residual_risk_score': item.residual_risk_score,
            'ai_metadata': item.ai_metadata,
            'confidence_justification': confidence_justification,
            'confidence_factors': confidence_factors,
            'status': effective_status,
            'risk_instance_id': risk_instance_id,  # Add risk instance ID for workflow
            'reviewer_id': reviewer_id,
            'created_at': item.created_at.isoformat(),
            'reviewed_at': item.reviewed_at.isoformat() if item.reviewed_at else None,
        })
    
    return Response({
        'status': 'success',
        'data': data,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': (total_count + page_size - 1) // page_size
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_tenant
def get_system_risk_detail(request, risk_id):
    """Get detailed information for a specific system risk."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] get_system_risk_detail: tenant={tenant_id}, risk_id={risk_id}")
    
    risk = get_object_or_404(SystemIdentifiedRiskQueue, 
                             id=risk_id, tenant_id=tenant_id)
    
    final_score, confidence_justification, confidence_factors = _derive_confidence_for_response(risk)
    data = {
        'id': risk.id,
        'source_module': risk.source_module,
        'source_record_id': risk.source_record_id,
        'source_ref': risk.source_ref,
        'risk_title': risk.risk_title,
        'risk_type': risk.risk_type,
        'category': risk.category,
        'criticality': risk.criticality,
        'risk_description': risk.risk_description,
        'possible_damage': risk.possible_damage,
        'business_impact': risk.business_impact,
        'likelihood': risk.likelihood,
        'impact': risk.impact,
        'inherent_risk_score': risk.inherent_risk_score,
        'residual_risk_score': risk.residual_risk_score,
        'exposure_rating': risk.exposure_rating,
        'priority': risk.priority,
        'mitigation_steps': risk.mitigation_steps,
        'ai_reasoning': risk.ai_reasoning,
        'confidence_score': final_score,
        'velocity_score': risk.velocity_score,
        'functional_area': risk.functional_area,
        'confidence_justification': confidence_justification,
        'confidence_factors': confidence_factors,
        'ai_metadata': risk.ai_metadata,
        'status': risk.status,
        'source_details': _get_source_details(risk),
        'review_notes': risk.review_notes,
        'rejection_reason': risk.rejection_reason,
        'created_at': risk.created_at.isoformat(),
        'updated_at': risk.updated_at.isoformat(),
        'reviewed_at': risk.reviewed_at.isoformat() if risk.reviewed_at else None,
    }
    
    return Response({'status': 'success', 'data': data})

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@require_tenant
@csrf_exempt
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
def update_system_risk_review(request, risk_id):
    """Update system risk with review changes (save as draft)."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] update_system_risk_review: tenant={tenant_id}, risk_id={risk_id}")
    
    risk = get_object_or_404(SystemIdentifiedRiskQueue, 
                             id=risk_id, tenant_id=tenant_id)
    
    try:
        # Update using service layer
        updated_risk = update_queue_entry_review(risk, request.data, request.user.id)
        
        return Response({
            'status': 'success',
            'message': 'Risk review saved as draft.'
        })
    except Exception as e:
        print(f"[API] update_system_risk_review error: {e}")
        return Response({
            'status': 'error',
            'message': f'Failed to update risk: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_tenant
@csrf_exempt
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
def accept_system_risk(request, risk_id):
    """Accept a system risk and create Risk Register entry."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] accept_system_risk: tenant={tenant_id}, risk_id={risk_id}")
    
    risk = get_object_or_404(SystemIdentifiedRiskQueue, 
                             id=risk_id, tenant_id=tenant_id)
    
    try:
        # Create official risk record (apply review overrides from request if present)
        created_risk = create_risk_from_queue_entry(risk, request.user.id, request.data)
        
        return Response({
            'status': 'success',
            'message': 'Risk accepted and added to Risk Register.',
            'risk_id': created_risk.RiskId
        })
    except Exception as e:
        print(f"[API] accept_system_risk error: {e}")
        return Response({
            'status': 'error',
            'message': f'Failed to create risk: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_tenant
@csrf_exempt
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
def reject_system_risk(request, risk_id):
    """Reject a system risk with reason."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] reject_system_risk: tenant={tenant_id}, risk_id={risk_id}")
    
    risk = get_object_or_404(SystemIdentifiedRiskQueue, 
                             id=risk_id, tenant_id=tenant_id)
    
    rejection_reason = request.data.get('reason', '')
    if not rejection_reason:
        return Response({
            'status': 'error',
            'message': 'Rejection reason is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Reject using service layer
        rejected_risk = reject_queue_entry(risk, rejection_reason, request.user.id)
        
        return Response({
            'status': 'success',
            'message': 'Risk rejected successfully.'
        })
    except Exception as e:
        print(f"[API] reject_system_risk error: {e}")
        return Response({
            'status': 'error',
            'message': f'Failed to reject risk: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_tenant
@csrf_exempt
@authentication_classes([UnifiedJWTAuthentication, CsrfExemptSessionAuthentication, BasicAuthentication])
def send_system_risk_for_approval(request, risk_id):
    """Send a system risk for approval workflow instead of direct acceptance."""
    tenant_id = get_tenant_id_from_request(request)

    print(f"[API] send_system_risk_for_approval: tenant={tenant_id}, risk_id={risk_id}")

    risk = get_object_or_404(SystemIdentifiedRiskQueue,
                             id=risk_id, tenant_id=tenant_id)

    try:
        user_id = request.data.get('user_id')
        reviewer_id = request.data.get('reviewer_id')
        risk_data = request.data.get('risk_data', {})

        if not user_id or not reviewer_id:
            return Response({
                'status': 'error',
                'message': 'User ID and Reviewer ID are required.'
            }, status=400)

        # Create risk instance first (similar to normal acceptance but with pending approval status)
        created_risk = create_risk_from_queue_entry_for_workflow(risk, request.user.id, risk_data)
        
        # Create workflow entry in risk_approval table
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Get framework_id (you might need to adjust this based on your logic)
            cursor.execute("SELECT FrameworkId FROM grc2.risk_instance WHERE RiskInstanceId = %s", [created_risk.RiskInstanceId])
            framework_row = cursor.fetchone()
            framework_id = framework_row[0] if framework_row else 1
            
            # Get next version for this risk
            cursor.execute("""
                SELECT COALESCE(MAX(version), 0) + 1 
                FROM grc2.risk_approval 
                WHERE RiskInstanceId = %s
            """, [created_risk.RiskInstanceId])
            version = cursor.fetchone()[0]
            
            # Insert workflow record
            cursor.execute("""
                INSERT INTO grc2.risk_approval 
                (RiskInstanceId, version, ExtractedInfo, UserId, ApproverId, ApprovedRejected, FrameworkId)
                VALUES (%s, %s, %s, %s, %s, NULL, %s)
            """, [
                created_risk.RiskInstanceId,
                version,
                json.dumps({
                    "workflow_type": "system_risk",
                    "source_queue_id": risk.id,
                    "submitted_at": timezone.now().isoformat()
                }),
                user_id,
                reviewer_id,
                framework_id
            ])

        # Update the risk status to indicate it's pending approval
        created_risk.RiskStatus = 'Pending Approval'
        created_risk.save()

        # Update queue entry status
        risk.status = 'ACCEPTED_PENDING_APPROVAL'
        risk.save()

        return Response({
            'status': 'success',
            'message': 'Risk sent for approval successfully.',
            'risk_instance_id': created_risk.RiskInstanceId,
            'workflow_version': version
        })
        
    except Exception as e:
        print(f"[API] send_system_risk_for_approval error: {e}")
        return Response({
            'status': 'error',
            'message': 'Failed to send risk for approval.'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_tenant
@csrf_exempt
@authentication_classes([UnifiedJWTAuthentication, CsrfExemptSessionAuthentication, BasicAuthentication])
def approve_system_risk_workflow(request, risk_instance_id):
    """Approve a system risk workflow and move it to Risk Register."""
    tenant_id = get_tenant_id_from_request(request)

    print(f"[API] approve_system_risk_workflow: tenant={tenant_id}, risk_instance_id={risk_instance_id}")

    try:
        from django.db import connection
        from ...models import RiskInstance, Risk
        
        # Get the risk instance
        risk_instance = RiskInstance.objects.get(
            RiskInstanceId=risk_instance_id,
            tenant_id=tenant_id
        )
        
        # Check if user has permission to approve (is the assigned reviewer)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ApproverId FROM grc2.risk_approval 
                WHERE RiskInstanceId = %s 
                ORDER BY version DESC LIMIT 1
            """, [risk_instance_id])
            
            approval_row = cursor.fetchone()
            actor_user_id = _resolve_actor_user_id(request.user)
            approver_id = int(approval_row[0]) if approval_row and approval_row[0] is not None else None
            if not approval_row or approver_id != actor_user_id:
                return Response({
                    'status': 'error',
                    'message': 'You are not authorized to approve this risk.'
                }, status=403)
            
            # Write a new approval version (matches existing risk workflow table shape)
            cursor.execute("""
                SELECT COALESCE(MAX(version), 0) + 1
                FROM grc2.risk_approval
                WHERE RiskInstanceId = %s
            """, [risk_instance_id])
            new_version = cursor.fetchone()[0]

            cursor.execute("SELECT FrameworkId FROM grc2.risk_instance WHERE RiskInstanceId = %s", [risk_instance_id])
            fw_row = cursor.fetchone()
            framework_id = fw_row[0] if fw_row else None

            cursor.execute("""
                INSERT INTO grc2.risk_approval
                (RiskInstanceId, version, ExtractedInfo, UserId, ApproverId, ApprovedRejected, FrameworkId)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [
                risk_instance_id,
                new_version,
                json.dumps({
                    "workflow_type": "system_risk",
                    "feedback": request.data.get('feedback', ''),
                    "action_at": timezone.now().isoformat()
                }),
                actor_user_id,
                actor_user_id,
                "Approved",
                framework_id
            ])
        
        # Create Risk Register entry from RiskInstance
        risk = Risk.objects.create(
            tenant=risk_instance.tenant,
            ComplianceId=risk_instance.ComplianceId,
            RiskTitle=risk_instance.RiskTitle,
            Criticality=risk_instance.Criticality,
            Category=risk_instance.Category,
            RiskType=risk_instance.RiskType,
            RiskDescription=risk_instance.RiskDescription,
            PossibleDamage=risk_instance.PossibleDamage,
            BusinessImpact=risk_instance.BusinessImpact,
            RiskLikelihood=risk_instance.RiskLikelihood,
            RiskImpact=risk_instance.RiskImpact,
            inherent_risk_score=risk_instance.inherent_risk_score,
            residual_risk_score=risk_instance.residual_risk_score,
            RiskExposureRating=risk_instance.RiskExposureRating,
            RiskMultiplierX=risk_instance.RiskMultiplierX,
            RiskMultiplierY=risk_instance.RiskMultiplierY,
            RiskPriority=risk_instance.RiskPriority,
            RiskMitigation=risk_instance.RiskMitigation,
            Origin='SYSTEM-AI',
            CreatedAt=timezone.now().date()
        )
        
        # Update risk instance status
        risk_instance.RiskStatus = 'Approved'
        risk_instance.save()
        
        # Update queue entry if it exists
        try:
            details = risk_instance.RiskFormDetails
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except Exception:
                    details = {}
            if not isinstance(details, dict):
                details = {}
            queue_id = details.get("source_queue_id")
            if queue_id:
                queue_entry = SystemIdentifiedRiskQueue.objects.get(id=queue_id, tenant_id=tenant_id)
                queue_entry.status = 'APPROVED_ADDED'
                queue_entry.approved_at = timezone.now()
                queue_entry.approved_by_id = actor_user_id
                queue_entry.reviewed_at = timezone.now()
                queue_entry.reviewed_by_id = actor_user_id
                queue_entry.save()
        except Exception as e:
            print(f"Warning: Could not update queue entry: {e}")
        
        return Response({
            'status': 'success',
            'message': 'Risk approved and added to Risk Register.',
            'risk_id': risk.RiskId
        })
        
    except RiskInstance.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Risk instance not found.'
        }, status=404)
    except Exception as e:
        print(f"[API] approve_system_risk_workflow error: {e}")
        return Response({
            'status': 'error',
            'message': 'Failed to approve risk.'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_tenant
@csrf_exempt
@authentication_classes([UnifiedJWTAuthentication, CsrfExemptSessionAuthentication, BasicAuthentication])
def reject_system_risk_workflow(request, risk_instance_id):
    """Reject a system risk workflow."""
    tenant_id = get_tenant_id_from_request(request)

    print(f"[API] reject_system_risk_workflow: tenant={tenant_id}, risk_instance_id={risk_instance_id}")

    try:
        from django.db import connection
        from ...models import RiskInstance
        
        # Get the risk instance
        risk_instance = RiskInstance.objects.get(
            RiskInstanceId=risk_instance_id,
            tenant_id=tenant_id
        )
        
        feedback = request.data.get('feedback', '')
        if not feedback:
            return Response({
                'status': 'error',
                'message': 'Rejection feedback is required.'
            }, status=400)
        
        # Check if user has permission to reject (is the assigned reviewer)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ApproverId FROM grc2.risk_approval 
                WHERE RiskInstanceId = %s 
                ORDER BY version DESC LIMIT 1
            """, [risk_instance_id])
            
            approval_row = cursor.fetchone()
            actor_user_id = _resolve_actor_user_id(request.user)
            approver_id = int(approval_row[0]) if approval_row and approval_row[0] is not None else None
            if not approval_row or approver_id != actor_user_id:
                return Response({
                    'status': 'error',
                    'message': 'You are not authorized to reject this risk.'
                }, status=403)
            
            # Write a new rejection version (matches existing risk workflow table shape)
            cursor.execute("""
                SELECT COALESCE(MAX(version), 0) + 1
                FROM grc2.risk_approval
                WHERE RiskInstanceId = %s
            """, [risk_instance_id])
            new_version = cursor.fetchone()[0]

            cursor.execute("SELECT FrameworkId FROM grc2.risk_instance WHERE RiskInstanceId = %s", [risk_instance_id])
            fw_row = cursor.fetchone()
            framework_id = fw_row[0] if fw_row else None

            cursor.execute("""
                INSERT INTO grc2.risk_approval
                (RiskInstanceId, version, ExtractedInfo, UserId, ApproverId, ApprovedRejected, FrameworkId)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [
                risk_instance_id,
                new_version,
                json.dumps({
                    "workflow_type": "system_risk",
                    "feedback": feedback,
                    "action_at": timezone.now().isoformat()
                }),
                actor_user_id,
                actor_user_id,
                "Rejected",
                framework_id
            ])
        
        # Update risk instance status
        risk_instance.RiskStatus = 'Rejected'
        risk_instance.save()
        
        # Update queue entry if it exists
        try:
            details = risk_instance.RiskFormDetails
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except Exception:
                    details = {}
            if not isinstance(details, dict):
                details = {}
            queue_id = details.get("source_queue_id")
            if queue_id:
                queue_entry = SystemIdentifiedRiskQueue.objects.get(id=queue_id, tenant_id=tenant_id)
                queue_entry.status = 'REJECTED'
                queue_entry.rejection_reason = feedback
                queue_entry.reviewed_at = timezone.now()
                queue_entry.reviewed_by_id = actor_user_id
                queue_entry.save()
        except Exception as e:
            print(f"Warning: Could not update queue entry: {e}")
        
        return Response({
            'status': 'success',
            'message': 'Risk rejected successfully.'
        })
        
    except RiskInstance.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Risk instance not found.'
        }, status=404)
    except Exception as e:
        print(f"[API] reject_system_risk_workflow error: {e}")
        return Response({
            'status': 'error',
            'message': 'Failed to reject risk.'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_tenant
def get_queue_stats(request):
    """Get statistics for the system risk queue."""
    tenant_id = get_tenant_id_from_request(request)
    
    print(f"[API] get_queue_stats: tenant={tenant_id}")
    
    try:
        stats = get_queue_statistics(tenant_id)
        
        return Response({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        print(f"[API] get_queue_stats error: {e}")
        return Response({
            'status': 'error',
            'message': f'Failed to get statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_tenant
def list_risks_exceeding_threshold(request):
    """
    List system identified risks that exceed their department's AI confidence threshold.
    """
    tenant_id = get_tenant_id_from_request(request)
    from grc.utils.auto_decrypt_helper import decrypt_any_encrypted_value
    
    print(f"[API] list_risks_exceeding_threshold: tenant={tenant_id}")
    
    # 1. Fetch all pending review risks for the tenant
    queryset = SystemIdentifiedRiskQueue.objects.filter(
        tenant_id=tenant_id, 
        status='PENDING_REVIEW'
    ).order_by('-created_at')
    
    # 2. Fetch all departments to get thresholds
    departments = Department.objects.filter(tenant_id=tenant_id)
    
    # Map department names (normalized) to their thresholds and original names
    threshold_map = {}
    for dept in departments:
        try:
            # Decrypt name for matching with functional_area
            dept_name = decrypt_any_encrypted_value(dept.DepartmentName)
            if dept_name:
                normalized_name = dept_name.strip().upper()
                threshold_map[normalized_name] = {
                    'threshold': dept.threshold_limit,
                    'original_name': dept_name.strip()
                }
        except Exception as e:
            print(f"[API] Error decrypting department name for threshold check: {e}")
            continue

    # 3. Filter risks based on thresholds
    data = []
    for item in queryset:
        # Decrypt functional_area for matching
        try:
            area_name = decrypt_any_encrypted_value(item.functional_area)
            area_name_upper = area_name.strip().upper() if area_name else None
        except Exception:
            area_name_upper = None

        # 4. Handle department matching with fallback to random as per user request
        import random
        all_dept_keys = list(threshold_map.keys())
        
        if not area_name_upper or area_name_upper not in threshold_map:
            if all_dept_keys:
                # If area is missing or not in DB, pick a random one from actual departments
                random_key = random.choice(all_dept_keys)
                area_name_upper = random_key
                area_name = threshold_map[random_key]['original_name']
            else:
                area_name_upper = "IT"
                area_name = "IT"
        else:
            # Use the original name from the threshold map for better casing
            area_name = threshold_map[area_name_upper]['original_name']

        # Get threshold
        dept_info = threshold_map.get(area_name_upper, {'threshold': 50})
        threshold = dept_info.get('threshold', 50)
        
        # Calculate Residual Risk Score
        # Priority: Persisted residual_risk_score > fallback calculation
        if item.residual_risk_score is not None:
            residual_score = item.residual_risk_score
        else:
            residual_score = int(item.exposure_rating or (item.likelihood or 5) * (item.impact or 5))
        
        # Apply threshold filter based on Residual Risk Score (0-100 scale)
        if residual_score >= threshold:
            # Get confidence details for secondary awareness
            final_score, confidence_justification, confidence_factors = _derive_confidence_for_response(item)
            
            data.append({
                'id': item.id,
                'source_module': item.source_module,
                'source_ref': item.source_ref,
                'source_title': _get_source_details(item).get('title', item.source_ref),
                'risk_title': item.risk_title,
                'risk_type': item.risk_type,
                'category': item.category,
                'criticality': item.criticality,
                'residual_score': residual_score, # Primary metric
                'confidence_score': final_score, # Secondary metric
                'threshold_limit': threshold, 
                'velocity_score': item.velocity_score,
                'functional_area': area_name if 'area_name' in locals() else item.functional_area,
                'likelihood': item.likelihood,
                'impact': item.impact,
                'inherent_risk_score': item.inherent_risk_score,
                'residual_risk_score': residual_score,
                'exposure_rating': item.exposure_rating,
                'priority': item.priority,
                'ai_reasoning': item.ai_reasoning,
                'ai_metadata': item.ai_metadata,
                'confidence_justification': confidence_justification,
                'confidence_factors': confidence_factors,
                'status': item.status,
                'created_at': item.created_at.isoformat(),
            })
    
    print(f"[API] Found {len(data)} risks exceeding department thresholds")
    
    return Response({
        'status': 'success',
        'count': len(data),
        'data': data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_tenant
def get_department_thresholds(request):
    """List all departments with their current AI confidence thresholds."""
    tenant_id = get_tenant_id_from_request(request)
    
    # Verify admin access
    from ...rbac.utils import RBACUtils
    user_id = RBACUtils.get_user_id_from_request(request)
    if not RBACUtils.is_system_admin(user_id):
        return Response({
            'status': 'error',
            'message': 'Only GRC Administrators can manage department thresholds.'
        }, status=403)

    # Fetch departments with threshold and head info
    # FIX: IsActive is a BooleanField, use True instead of 'Y'
    departments = Department.objects.filter(tenant_id=tenant_id, IsActive=True).values(
        'DepartmentId', 'DepartmentName', 'threshold_limit', 'DepartmentHead'
    )
    
    # Enrich with department head email (decrypted)
    data = list(departments)
    for dept in data:
        head_id = dept.get('DepartmentHead')
        if head_id:
            try:
                head_user = Users.objects.get(UserId=head_id)
                dept['DepartmentHeadEmail'] = head_user.Email_plain
                dept['DepartmentHeadName'] = f"{head_user.FirstName} {head_user.LastName}"
            except Users.DoesNotExist:
                dept['DepartmentHeadEmail'] = None
                dept['DepartmentHeadName'] = "Unknown"
        else:
            dept['DepartmentHeadEmail'] = None
            dept['DepartmentHeadName'] = "Not Assigned"
            
    return Response({
        'status': 'success',
        'data': data
    })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@require_tenant
def update_department_threshold(request):
    """Update AI confidence threshold for a specific department and notify head."""
    tenant_id = get_tenant_id_from_request(request)
    
    # Verify admin access
    from ...rbac.utils import RBACUtils
    user_id = RBACUtils.get_user_id_from_request(request)
    if not RBACUtils.is_system_admin(user_id):
        return Response({
            'status': 'error',
            'message': 'Only GRC Administrators can manage department thresholds.'
        }, status=403)

    dept_id = request.data.get('department_id')
    new_threshold = request.data.get('threshold_limit')
    
    if dept_id is None or new_threshold is None:
        return Response({
            'status': 'error',
            'message': 'Department ID and threshold limit are required.'
        }, status=400)
        
    try:
        new_threshold = int(new_threshold)
        if not (0 <= new_threshold <= 100):
            raise ValueError()
    except ValueError:
        return Response({
            'status': 'error',
            'message': 'Threshold limit must be an integer between 0 and 100.'
        }, status=400)

    try:
        dept = Department.objects.get(DepartmentId=dept_id, tenant_id=tenant_id)
        old_threshold = dept.threshold_limit
        dept.threshold_limit = new_threshold
        dept.save()
        
        # Send notification email to Department Head
        email_sent = False
        head_email = None
        if dept.DepartmentHead:
            try:
                head_user = Users.objects.get(UserId=dept.DepartmentHead)
                head_email = head_user.Email_plain
                
                if head_email:
                    from ..Global.notification_service import NotificationService
                    ns = NotificationService()
                    
                    subject = f"Security Update: Residual Risk Threshold Adjusted - {dept.DepartmentName}"
                    body = f"""
                    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <h2 style="color: #1a73e8;">Risk Threshold Update</h2>
                        <p>Hello <b>{head_user.FirstName} {head_user.LastName}</b>,</p>
                        <p>This is to inform you that the Residual Risk Score threshold for the <b>{dept.DepartmentName}</b> department has been updated.</p>
                        <table style="border-collapse: collapse; width: 100%; max-width: 400px; margin: 20px 0;">
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd; background-color: #f8f9fa;"><b>Previous Threshold:</b></td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{old_threshold}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd; background-color: #f8f9fa;"><b>New Threshold:</b></td>
                                <td style="padding: 10px; border: 1px solid #ddd; color: #d93025; font-weight: bold;">{new_threshold}</td>
                            </tr>
                        </table>
                        <p>Identified risks with a Residual Risk Score (Likelihood × Impact) below this threshold will no longer be automatically queued for your review.</p>
                        <p>Updated by: {request.user.username if hasattr(request.user, 'username') else 'Administrator'}</p>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                        <p style="font-size: 12px; color: #777;">This is an automated notification from the RiskAvaire GRC System.</p>
                    </div>
                    """
                    
                    # Using the direct graph sender for reliability in this specific trigger
                    ns.azure_email_sender.send_email_via_graph(
                        to_email=head_email,
                        subject=subject,
                        html_body=body
                    )
                    email_sent = True
            except Exception as e:
                print(f"[SYSTEM-RISK] Failed to send threshold update email to {head_email}: {e}")

        return Response({
            'status': 'success',
            'message': f'Threshold for {dept.DepartmentName} updated to {new_threshold}%.',
            'email_sent': email_sent
        })
        
    except Department.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Department not found.'
        }, status=404)
    except Exception as e:
        print(f"[SYSTEM-RISK] update_department_threshold error: {e}")
        return Response({
            'status': 'error',
            'message': 'An unexpected error occurred while updating the threshold.'
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_tenant
def list_external_sources(request):
    """List available external sources for risk scanning."""
    sources = get_external_portals_list()
    return Response({'status': 'success', 'data': sources})
