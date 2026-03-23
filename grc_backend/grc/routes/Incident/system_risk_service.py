"""
System Identified Risk Queue Service
Handles AI-powered risk identification from incidents and queue management.
"""

from django.db import transaction
from django.utils import timezone
from django.conf import settings
from ...models import Incident, SystemIdentifiedRiskQueue
from ...ai.service import get_ai_service
from ...tenant_utils import get_tenant_id_from_request
import hashlib
import json
import time
import os

ai_service = get_ai_service()

def generate_risk_candidates_from_incidents(tenant_id, limit=50):
    """
    Scan recent incidents and generate risk candidates.
    
    Args:
        tenant_id: Tenant ID for data isolation
        limit: Maximum number of incidents to process
    
    Returns:
        dict: {"created": int, "skipped": int, "errors": []}
    """
    results = {"created": 0, "skipped": 0, "errors": []}
    
    print(f"[SYSTEM-RISK] Starting incident scan for tenant {tenant_id}, limit={limit}")
    
    # Get recent incidents that haven't been processed yet
    recent_incidents = Incident.objects.filter(
        tenant_id=tenant_id,
        Date__gte=timezone.now().date() - timezone.timedelta(days=90)  # Last 90 days
    ).exclude(
        IncidentId__in=SystemIdentifiedRiskQueue.objects.filter(
            tenant_id=tenant_id,
            source_module=SystemIdentifiedRiskQueue.SOURCE_INCIDENT
        ).values_list('source_record_id', flat=True)
    ).order_by('-Date')[:limit]
    
    total_unprocessed = recent_incidents.count()
    print(f"[SYSTEM-RISK] Found {total_unprocessed} unprocessed incidents from last 90 days")

    start_ts = time.time()

    for idx, incident in enumerate(recent_incidents, start=1):
        try:
            elapsed_s = time.time() - start_ts
            remaining = max(total_unprocessed - idx, 0)
            avg_s_per_incident = elapsed_s / idx if idx else 0
            eta_s = avg_s_per_incident * remaining
            print(
                f"[SYSTEM-RISK] Progress {idx}/{total_unprocessed} "
                f"(remaining={remaining}, elapsed={elapsed_s/60:.1f}m, ETA~{eta_s/60:.1f}m)"
            )

            print(f"[SYSTEM-RISK] Processing incident {incident.IncidentId}: {incident.IncidentTitle[:60]}...")
            
            # Prepare incident data for AI analysis
            incident_data = {
                'IncidentTitle': incident.IncidentTitle or '',
                'Description': incident.Description or '',
                'IncidentCategory': incident.IncidentCategory or '',
                'RiskCategory': incident.RiskCategory or '',
                'Criticality': incident.Criticality or '',
                'PossibleDamage': incident.PossibleDamage or '',
                'ControlFailures': incident.ControlFailures or '',
                'LessonsLearned': incident.LessonsLearned or '',
                'AffectedBusinessUnit': incident.AffectedBusinessUnit or '',
                'SystemsAssetsInvolved': incident.SystemsAssetsInvolved or '',
            }
            
            # Call AI service to identify risks
            risk_candidates = ai_service.run_task(
                "incident.identify_risks",
                payload={
                    "incident_data": incident_data,
                    "incident_id": incident.IncidentId
                }
            )
            
            print(f"[SYSTEM-RISK] AI generated {len(risk_candidates)} risk candidates for incident {incident.IncidentId}")
            
            # Create queue entries for each risk candidate
            for risk_data in risk_candidates:
                with transaction.atomic():
                    # Check for duplicates using title similarity
                    risk_title = risk_data.get('risk_title', '')
                    if not risk_title:
                        print(f"[SYSTEM-RISK] Skipping risk with empty title")
                        results["skipped"] += 1
                        continue
                    
                    # Check for existing similar risks from this incident
                    existing = SystemIdentifiedRiskQueue.objects.filter(
                        tenant_id=tenant_id,
                        source_module=SystemIdentifiedRiskQueue.SOURCE_INCIDENT,
                        source_record_id=incident.IncidentId,
                        risk_title__icontains=risk_title[:50]  # Fuzzy match on first 50 chars
                    ).exists()
                    
                    if existing:
                        print(f"[SYSTEM-RISK] Skipping duplicate risk: {risk_title[:50]}...")
                        results["skipped"] += 1
                        continue
                    
                    # Create queue entry
                    queue_entry = SystemIdentifiedRiskQueue.objects.create(
                        tenant_id=tenant_id,
                        source_module=SystemIdentifiedRiskQueue.SOURCE_INCIDENT,
                        source_record_id=incident.IncidentId,
                        source_ref=f"Incident #{incident.IncidentId}: {incident.IncidentTitle[:100]}",
                        risk_title=risk_data.get('risk_title', ''),
                        risk_type=risk_data.get('risk_type', 'Current'),
                        category=risk_data.get('category', ''),
                        criticality=risk_data.get('criticality', 'Medium'),
                        risk_description=risk_data.get('risk_description', ''),
                        possible_damage=risk_data.get('possible_damage', ''),
                        business_impact=risk_data.get('business_impact', []),
                        likelihood=risk_data.get('likelihood'),
                        impact=risk_data.get('impact'),
                        priority=risk_data.get('priority', 'Medium'),
                        mitigation_steps=risk_data.get('mitigation_steps', []),
                        ai_reasoning=risk_data.get('ai_reasoning', ''),
                        confidence_score=risk_data.get('_meta', {}).get('confidence_score', 75),
                        ai_metadata=risk_data.get('_meta', {}),
                        status=SystemIdentifiedRiskQueue.STATUS_PENDING_REVIEW
                    )
                    
                    results["created"] += 1
                    print(f"[SYSTEM-RISK] Created queue entry {queue_entry.id}: {risk_title[:60]}...")
                    
        except Exception as e:
            error_msg = f"Incident {incident.IncidentId}: {str(e)}"
            results["errors"].append(error_msg)
            print(f"[SYSTEM-RISK] Error processing incident {incident.IncidentId}: {e}")
    
    print(f"[SYSTEM-RISK] Scan complete: created={results['created']}, skipped={results['skipped']}, errors={len(results['errors'])}")
    return results


def _to_source_record_id(record_id_value):
    if record_id_value is None:
        return None
    text = str(record_id_value).strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if digits:
        try:
            return int(digits)
        except Exception:
            pass
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:10], 16)


def _normalize_source_module(value):
    if not value:
        return None
    raw = str(value).strip().upper()
    allowed = {
        SystemIdentifiedRiskQueue.SOURCE_AUDIT,
        SystemIdentifiedRiskQueue.SOURCE_INCIDENT,
        SystemIdentifiedRiskQueue.SOURCE_COMPLIANCE,
        SystemIdentifiedRiskQueue.SOURCE_TPRM,
        SystemIdentifiedRiskQueue.SOURCE_INTEGRATION,
        SystemIdentifiedRiskQueue.SOURCE_MANUAL,
    }
    return raw if raw in allowed else None


def _criticality_from_signal(signal):
    mapping = {
        "LOW": "Low",
        "MEDIUM": "Medium",
        "HIGH": "High",
        "CRITICAL": "Critical",
    }
    return mapping.get((signal or "").strip().upper(), "Medium")


def generate_risk_candidates_from_synthetic_sources(
    tenant_id,
    limit=100,
    progress_callback=None,
    should_abort=None
):
    """
    Analyze synthetic multi-module source data with AI and create queue entries for detected risks.
    """
    results = {"processed": 0, "created": 0, "skipped": 0, "non_risk": 0, "errors": []}

    data_path = os.path.join(settings.BASE_DIR, "grc", "data", "system_risk_synthetic_source_data.json")
    print(f"[SYSTEM-RISK][SYN] Starting synthetic scan for tenant {tenant_id}, limit={limit}, file={data_path}")

    try:
        with open(data_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception as e:
        raise RuntimeError(f"Failed to read synthetic data JSON: {e}")

    records = payload.get("records", [])
    if not isinstance(records, list):
        raise RuntimeError("Invalid synthetic data format: records must be an array")

    if limit:
        try:
            records = records[:max(int(limit), 0)]
        except Exception:
            pass

    total = len(records)
    if progress_callback:
        progress_callback(processed=0, total=total, phase="started", last_record=None)
    print(f"[SYSTEM-RISK][SYN] Loaded {total} source records")

    for idx, record in enumerate(records, start=1):
        if should_abort and should_abort():
            print(f"[SYSTEM-RISK][SYN] Cancellation requested. Stopping at {idx - 1}/{total}")
            if progress_callback:
                progress_callback(
                    processed=results["processed"],
                    total=total,
                    phase="cancelled",
                    last_record=None
                )
            break
        results["processed"] += 1
        try:
            source_module = _normalize_source_module(record.get("source_module"))
            if not source_module:
                results["skipped"] += 1
                results["errors"].append(f"Record {record.get('record_id', idx)}: invalid source_module")
                continue

            record_id = record.get("record_id", f"SYN-{idx}")
            source_record_id = _to_source_record_id(record_id)
            source_ref = f"{record.get('source_label', source_module)} #{record_id}: {record.get('title', '')[:120]}"

            existing = SystemIdentifiedRiskQueue.objects.filter(
                tenant_id=tenant_id,
                source_module=source_module,
                source_record_id=source_record_id,
                source_ref=source_ref,
            ).exists()
            if existing:
                results["skipped"] += 1
                continue

            ai_risks = ai_service.run_task(
                "incident.identify_risks_from_source_record",
                payload={
                    "source_record": record,
                    "source_module": source_module,
                    "source_record_id": record_id
                }
            )

            if not ai_risks:
                results["non_risk"] += 1
                continue

            created_for_record = 0
            for risk_data in ai_risks:
                risk_title = (risk_data or {}).get("risk_title", "").strip()
                if not risk_title:
                    results["skipped"] += 1
                    continue

                duplicate_title = SystemIdentifiedRiskQueue.objects.filter(
                    tenant_id=tenant_id,
                    source_module=source_module,
                    source_record_id=source_record_id,
                    risk_title__icontains=risk_title[:60]
                ).exists()
                if duplicate_title:
                    results["skipped"] += 1
                    continue

                with transaction.atomic():
                    SystemIdentifiedRiskQueue.objects.create(
                        tenant_id=tenant_id,
                        source_module=source_module,
                        source_record_id=source_record_id,
                        source_ref=source_ref,
                        risk_title=risk_title,
                        risk_type=risk_data.get("risk_type", "Current"),
                        category=risk_data.get("category", "") or "Operational",
                        criticality=risk_data.get("criticality", "Medium"),
                        risk_description=risk_data.get("risk_description", ""),
                        possible_damage=risk_data.get("possible_damage", ""),
                        business_impact=risk_data.get("business_impact", []),
                        likelihood=risk_data.get("likelihood"),
                        impact=risk_data.get("impact"),
                        priority=risk_data.get("priority", "Medium"),
                        mitigation_steps=risk_data.get("mitigation_steps", []),
                        ai_reasoning=risk_data.get("ai_reasoning", ""),
                        confidence_score=(risk_data.get("_meta", {}) or {}).get("confidence_score", 75),
                        ai_metadata={
                            **(risk_data.get("_meta", {}) or {}),
                            "synthetic_source_record_id": record_id,
                            "synthetic_expected_risk_signal": record.get("expected_risk_signal"),
                        },
                        status=SystemIdentifiedRiskQueue.STATUS_PENDING_REVIEW
                    )

                created_for_record += 1
                results["created"] += 1

            if created_for_record == 0:
                results["non_risk"] += 1

            print(f"[SYSTEM-RISK][SYN] {idx}/{total}: created={created_for_record}, record={record_id}")
            if progress_callback:
                progress_callback(processed=results["processed"], total=total, phase="running", last_record=record_id)
        except Exception as e:
            msg = f"Record {record.get('record_id', idx)}: {str(e)}"
            results["errors"].append(msg)
            print(f"[SYSTEM-RISK][SYN] Error: {msg}")
            if progress_callback:
                progress_callback(processed=results["processed"], total=total, phase="running", last_record=record.get("record_id", idx))

    print(
        f"[SYSTEM-RISK][SYN] Complete: processed={results['processed']}, created={results['created']}, "
        f"non_risk={results['non_risk']}, skipped={results['skipped']}, errors={len(results['errors'])}"
    )
    if progress_callback:
        final_phase = "completed"
        if should_abort and should_abort():
            final_phase = "cancelled"
        progress_callback(processed=results["processed"], total=total, phase=final_phase, last_record=None)
    return results

def create_risk_from_queue_entry(queue_entry, user_id):
    """
    Convert an accepted queue entry to an official Risk Register entry.
    
    Args:
        queue_entry: SystemIdentifiedRiskQueue instance
        user_id: ID of the user creating the risk
    
    Returns:
        Risk: Created risk instance
    """
    from ...models import Risk
    
    print(f"[SYSTEM-RISK] Creating Risk from queue entry {queue_entry.id}: {queue_entry.risk_title[:60]}...")
    
    with transaction.atomic():
        # Create risk record
        risk = Risk.objects.create(
            tenant=queue_entry.tenant,
            RiskTitle=queue_entry.risk_title,
            Criticality=queue_entry.criticality,
            Category=queue_entry.category,
            RiskType=queue_entry.risk_type,
            RiskDescription=queue_entry.risk_description,
            PossibleDamage=queue_entry.possible_damage,
            BusinessImpact=json.dumps(queue_entry.business_impact) if queue_entry.business_impact else None,
            RiskLikelihood=queue_entry.likelihood,
            RiskImpact=queue_entry.impact,
            RiskExposureRating=queue_entry.exposure_rating,
            RiskPriority=queue_entry.priority,
            RiskMitigation=json.dumps(queue_entry.mitigation_steps) if queue_entry.mitigation_steps else None,
            # Mark as AI-generated origin
            CreatedAt=timezone.now().date()
        )
        
        # Update queue entry
        queue_entry.status = SystemIdentifiedRiskQueue.STATUS_APPROVED_ADDED
        queue_entry.created_risk = risk
        queue_entry.approved_by_id = user_id
        queue_entry.approved_at = timezone.now()
        queue_entry.save()
        
        print(f"[SYSTEM-RISK] Created Risk {risk.RiskId} from queue entry {queue_entry.id}")
        return risk

def get_queue_statistics(tenant_id):
    """
    Get statistics for the system risk queue.
    
    Args:
        tenant_id: Tenant ID for data isolation
    
    Returns:
        dict: Statistics about the queue
    """
    from django.db.models import Q, Count
    
    stats = SystemIdentifiedRiskQueue.objects.filter(tenant_id=tenant_id).aggregate(
        pending_count=Count('id', filter=Q(status=SystemIdentifiedRiskQueue.STATUS_PENDING_REVIEW)),
        draft_count=Count('id', filter=Q(status=SystemIdentifiedRiskQueue.STATUS_DRAFT)),
        accepted_today=Count('id', filter=Q(
            status=SystemIdentifiedRiskQueue.STATUS_APPROVED_ADDED,
            approved_at__date=timezone.now().date()
        )),
        rejected_count=Count('id', filter=Q(status=SystemIdentifiedRiskQueue.STATUS_REJECTED)),
        total_count=Count('id')
    )
    
    # Count active sources (modules with recent entries)
    active_sources = SystemIdentifiedRiskQueue.objects.filter(
        tenant_id=tenant_id,
        created_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).values('source_module').distinct().count()
    
    return {
        'pending_count': stats['pending_count'] or 0,
        'draft_count': stats['draft_count'] or 0,
        'accepted_today': stats['accepted_today'] or 0,
        'rejected_count': stats['rejected_count'] or 0,
        'total_count': stats['total_count'] or 0,
        'sources_active': active_sources
    }

def update_queue_entry_review(queue_entry, review_data, user_id):
    """
    Update a queue entry with review changes (save as draft).
    
    Args:
        queue_entry: SystemIdentifiedRiskQueue instance
        review_data: dict with updated field values
        user_id: ID of the reviewing user
    
    Returns:
        SystemIdentifiedRiskQueue: Updated queue entry
    """
    print(f"[SYSTEM-RISK] Updating queue entry {queue_entry.id} with review data")
    
    # Update fields from review data
    queue_entry.risk_title = review_data.get('risk_title', queue_entry.risk_title)
    queue_entry.risk_type = review_data.get('risk_type', queue_entry.risk_type)
    queue_entry.category = review_data.get('category', queue_entry.category)
    queue_entry.criticality = review_data.get('criticality', queue_entry.criticality)
    queue_entry.risk_description = review_data.get('risk_description', queue_entry.risk_description)
    queue_entry.possible_damage = review_data.get('possible_damage', queue_entry.possible_damage)
    queue_entry.business_impact = review_data.get('business_impact', queue_entry.business_impact)
    queue_entry.likelihood = review_data.get('likelihood', queue_entry.likelihood)
    queue_entry.impact = review_data.get('impact', queue_entry.impact)
    queue_entry.priority = review_data.get('priority', queue_entry.priority)
    queue_entry.mitigation_steps = review_data.get('mitigation_steps', queue_entry.mitigation_steps)
    queue_entry.review_notes = review_data.get('review_notes', queue_entry.review_notes)
    
    # Update status and tracking
    queue_entry.status = SystemIdentifiedRiskQueue.STATUS_DRAFT
    queue_entry.reviewed_by_id = user_id
    queue_entry.reviewed_at = timezone.now()
    
    queue_entry.save()
    
    print(f"[SYSTEM-RISK] Queue entry {queue_entry.id} updated and saved as draft")
    return queue_entry

def reject_queue_entry(queue_entry, rejection_reason, user_id):
    """
    Reject a queue entry with reason.
    
    Args:
        queue_entry: SystemIdentifiedRiskQueue instance
        rejection_reason: str explaining why it was rejected
        user_id: ID of the rejecting user
    
    Returns:
        SystemIdentifiedRiskQueue: Updated queue entry
    """
    print(f"[SYSTEM-RISK] Rejecting queue entry {queue_entry.id}: {rejection_reason[:60]}...")
    
    # Update risk status
    queue_entry.status = SystemIdentifiedRiskQueue.STATUS_REJECTED
    queue_entry.rejection_reason = rejection_reason
    queue_entry.reviewed_by_id = user_id
    queue_entry.reviewed_at = timezone.now()
    queue_entry.save()
    
    print(f"[SYSTEM-RISK] Queue entry {queue_entry.id} rejected successfully")
    return queue_entry