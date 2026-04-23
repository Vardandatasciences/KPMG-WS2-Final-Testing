"""
System Identified Risk Queue Service
Handles AI-powered risk identification from incidents and queue management.
"""

from django.db import transaction, connection
from django.utils import timezone
from django.conf import settings
from ...models import (
    Incident, SystemIdentifiedRiskQueue, FileOperations, 
    CompanySubfolderDocument, CompanySubfolder, Compliance, Audit, Event
)
import threading
from ...ai.service import get_ai_service
from ...tenant_utils import get_tenant_id_from_request
from ..Global.s3_fucntions import create_direct_mysql_client
from grc.utils.auto_decrypt_helper import decrypt_any_encrypted_value
from grc.utils.data_encryption import encrypt_data, decrypt_data
from ...ai.processing.document_extractor import DocumentExtractor
import hashlib
import json
import time
import os
import tempfile
import logging
import requests

logger = logging.getLogger(__name__)

ai_service = get_ai_service()
document_extractor = DocumentExtractor()


def _clamp_int(value, low=0, high=100, default=60):
    try:
        return max(low, min(high, int(value)))
    except Exception:
        return default


def _resolve_confidence_from_risk(risk_data: dict) -> tuple[int, dict]:
    """Resolve confidence score/metadata from AI output with safe fallback."""
    meta = (risk_data or {}).get("_meta") or {}
    
    # Capture new fields in meta for persistence
    meta["control_effectiveness"] = (risk_data or {}).get("control_effectiveness")
    meta["framework_reference"] = (risk_data or {}).get("framework_reference")
    meta["per_field_rationale"] = (risk_data or {}).get("per_field_rationale") or {}
    
    score = meta.get("confidence_score")
    if score is None:
        likelihood = _clamp_int((risk_data or {}).get("likelihood"), 1, 10, 5)
        impact = _clamp_int((risk_data or {}).get("impact"), 1, 10, 5)
        reasoning = str((risk_data or {}).get("ai_reasoning") or "")
        mitigation_steps = (risk_data or {}).get("mitigation_steps") or []
        if isinstance(mitigation_steps, str):
            mitigation_steps = [mitigation_steps] if mitigation_steps.strip() else []
        base = 35 + (likelihood * impact * 0.35) + min(len(reasoning), 300) * 0.05 + min(len(mitigation_steps), 5) * 4
        score = _clamp_int(round(base), 35, 97, 60)
        if "confidence_justification" not in meta:
            meta["confidence_justification"] = (
                f"Confidence {score}% from likelihood={likelihood}, impact={impact}, "
                f"reasoning detail, and mitigation completeness."
            )
    meta["confidence_score"] = _clamp_int(score, 0, 100, 60)
    return meta["confidence_score"], meta

def _save_risk_candidate(tenant_id, source_module, source_record_id, source_ref, risk_data):
    """Internal helper to save a single risk candidate to the queue."""
    try:
        # Resolve confidence and metadata
        confidence_score, ai_metadata = _resolve_confidence_from_risk(risk_data)
        
        # Calculate exposure rating
        likelihood = _clamp_int(risk_data.get('likelihood'), 1, 10, 5)
        impact = _clamp_int(risk_data.get('impact'), 1, 10, 5)
        exposure = float(likelihood * impact)

        # Create the queue entry
        candidate = SystemIdentifiedRiskQueue.objects.create(
            tenant_id=tenant_id,
            source_module=source_module,
            source_record_id=source_record_id,
            source_ref=source_ref,
            risk_title=risk_data.get('risk_title', 'Identified Risk'),
            risk_description=risk_data.get('risk_description'),
            category=risk_data.get('category', 'Operational'),
            risk_type=risk_data.get('risk_type', 'Current'),
            criticality=risk_data.get('criticality', 'Medium'),
            likelihood=likelihood,
            impact=impact,
            exposure_rating=exposure,
            priority=risk_data.get('criticality', 'Medium'),
            ai_reasoning=risk_data.get('ai_reasoning'),
            confidence_score=confidence_score,
            velocity_score=_clamp_int(risk_data.get('velocity_score'), 1, 10, 5),
            functional_area=risk_data.get('functional_area', 'IT'),
            mitigation_steps=risk_data.get('mitigation_steps', []),
            ai_metadata=ai_metadata,
            status=SystemIdentifiedRiskQueue.STATUS_PENDING_REVIEW
        )
        return candidate
    except Exception as e:
        logger.error(f"[SYSTEM-RISK] Error saving risk candidate: {e}")
        return None

def trigger_single_source_risk_scan(source_type, source_id, tenant_id):
    """
    Triggers an asynchronous AI risk scan for a single record.
    Called automatically after record creation in views.
    """
    def _run_bg():
        try:
            # MULTI-TENANCY: Reset connection for background thread
            connection.close()
            print(f"[SYSTEM-RISK] Background scan started for {source_type} ID {source_id}")
            
            data_summary = ""
            source_ref = f"{source_type} #{source_id}"
            
            # 1. Fetch record and build summary
            if source_type == SystemIdentifiedRiskQueue.SOURCE_INCIDENT:
                record = Incident.objects.get(IncidentId=source_id, tenant_id=tenant_id)
                data_summary = (
                    f"Incident Title: {record.IncidentTitle}\n"
                    f"Description: {record.Description}\n"
                    f"Control Failures: {getattr(record, 'ControlFailures', 'N/A')}\n"
                    f"Impact: {getattr(record, 'InitialImpactAssessment', 'N/A')}\n"
                    f"Severity: {getattr(record, 'Criticality', 'N/A')}"
                )
                source_ref = record.IncidentTitle
            elif source_type == SystemIdentifiedRiskQueue.SOURCE_COMPLIANCE:
                record = Compliance.objects.get(ComplianceId=source_id, tenant_id=tenant_id)
                data_summary = (
                    f"Compliance Title: {record.ComplianceTitle}\n"
                    f"Description: {record.ComplianceItemDescription}\n"
                    f"Scope: {record.Scope}\n"
                    f"Objective: {record.Objective}\n"
                    f"Criticality: {record.Criticality}"
                )
                source_ref = record.ComplianceTitle
            elif source_type == SystemIdentifiedRiskQueue.SOURCE_AUDIT:
                record = Audit.objects.get(AuditId=source_id, tenant_id=tenant_id)
                data_summary = (
                    f"Audit Title: {record.Title}\n"
                    f"Scope: {record.Scope}\n"
                    f"Objective: {getattr(record, 'Objective', 'N/A')}\n"
                    f"Comments: {getattr(record, 'Comments', 'N/A')}"
                )
                source_ref = record.Title
            elif source_type == SystemIdentifiedRiskQueue.SOURCE_MANUAL: # Used for Events
                record = Event.objects.get(EventId=source_id, tenant_id=tenant_id)
                data_summary = (
                    f"Event Title: {record.EventTitle}\n"
                    f"Module: {record.Module}\n"
                    f"Category: {record.Category}\n"
                    f"Description: {record.Description or ''}"
                )
                source_ref = record.EventTitle or f"Event {source_id}"
            
            if not data_summary:
                print(f"[SYSTEM-RISK] No data summary generated for {source_type} {source_id}")
                return

            # 2. Run AI Task
            risks = ai_service.run_task("risk.identify_risks", {
                "source_type": source_type,
                "data_summary": data_summary
            })
            
            # 3. Save candidates
            count = 0
            if isinstance(risks, list):
                for r_data in risks:
                    if _save_risk_candidate(tenant_id, source_type, source_id, source_ref, r_data):
                        count += 1
            
            print(f"[SYSTEM-RISK] Background scan COMPLETED for {source_type} {source_id}. Created {count} risks.")
            
        except Exception as e:
            logger.error(f"[SYSTEM-RISK] Background single-source scan failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

    # Run in daemon thread to avoid blocking request but ensure execution
    threading.Thread(target=_run_bg, daemon=True).start()

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
            
            # Call AI service to identify risks using the new centralized task
            risk_candidates = ai_service.run_task(
                "risk.identify_risks",
                payload={
                    "source_type": "INCIDENT",
                    "data_summary": json.dumps(incident_data, indent=2)
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
                    confidence_score, confidence_meta = _resolve_confidence_from_risk(risk_data)
                    queue_entry = SystemIdentifiedRiskQueue.objects.create(
                        tenant_id=tenant_id,
                        source_module=SystemIdentifiedRiskQueue.SOURCE_INCIDENT,
                        source_record_id=incident.IncidentId,
                        source_ref=f"Incident #{incident.IncidentId}: {incident.IncidentTitle[:100]}",
                        risk_title=risk_data.get('risk_title') or risk_data.get('RiskTitle', ''),
                        risk_type=risk_data.get('risk_type') or risk_data.get('RiskType', 'Current'),
                        category=risk_data.get('category') or risk_data.get('Category', ''),
                        criticality=risk_data.get('criticality') or risk_data.get('Criticality', 'Medium'),
                        risk_description=risk_data.get('risk_description') or risk_data.get('RiskDescription', ''),
                        possible_damage=risk_data.get('possible_damage') or risk_data.get('PossibleDamage', ''),
                        business_impact=risk_data.get('business_impact') or risk_data.get('BusinessImpact', []),
                        likelihood=risk_data.get('likelihood') or risk_data.get('RiskLikelihood'),
                        impact=risk_data.get('impact') or risk_data.get('RiskImpact'),
                        priority=risk_data.get('priority') or risk_data.get('RiskPriority', 'Medium'),
                        mitigation_steps=risk_data.get('mitigation_steps') or risk_data.get('RiskMitigation', []),
                        ai_reasoning=risk_data.get('ai_reasoning', ''),
                        confidence_score=confidence_score,
                        ai_metadata=confidence_meta,
                        status=SystemIdentifiedRiskQueue.STATUS_PENDING_REVIEW,
                        velocity_score=risk_data.get('velocity_score', 50),
                        functional_area=risk_data.get('functional_area', 'General')
                    )
                    
                    results["created"] += 1
                    print(f"[SYSTEM-RISK] Created queue entry {queue_entry.id}: {risk_title[:60]}...")
                    
        except Exception as e:
            error_msg = f"Incident {incident.IncidentId}: {str(e)}"
            results["errors"].append(error_msg)
            print(f"[SYSTEM-RISK] Error processing incident {incident.IncidentId}: {e}")
    
    print(f"[SYSTEM-RISK] Scan complete: created={results['created']}, skipped={results['skipped']}, errors={len(results['errors'])}")
    return results

def generate_risk_candidates_from_multiple_sources(tenant_id, source_types=None, limit=5, subfolder_ids=None, document_ids=None, run_checklist=False):
    """
    Scan recent records from multiple modules and generate risk candidates.
    Supported sources: INCIDENT, COMPLIANCE, AUDIT, MANUAL(Events), DOCUMENT
    """
    # Triggering auto-reloader with this comment
    results = {"created": 0, "skipped": 0, "errors": []}
    if source_types is None:
        source_types = []
        
    print(f"[SYSTEM-RISK] Executing generate_risk_candidates_from_multiple_sources")
    print(f"[SYSTEM-RISK] Starting multi-source scan. Sources={source_types}, Folders={subfolder_ids}, Docs={document_ids}, Checklist={run_checklist}, Tenant {tenant_id}")
    
    # Process each standard source module
    for source_type in source_types:
        records = []
        if source_type == SystemIdentifiedRiskQueue.SOURCE_INCIDENT:
            records = list(Incident.objects.filter(tenant_id=tenant_id).order_by('-Date')[:limit])
        elif source_type == SystemIdentifiedRiskQueue.SOURCE_COMPLIANCE:
            records = list(Compliance.objects.filter(tenant_id=tenant_id).order_by('-CreatedByDate')[:limit])
        elif source_type == SystemIdentifiedRiskQueue.SOURCE_AUDIT:
            records = list(Audit.objects.filter(tenant_id=tenant_id).order_by('-AssignedDate')[:limit])
        elif source_type == SystemIdentifiedRiskQueue.SOURCE_MANUAL: # Events
            records = list(Event.objects.filter(tenant_id=tenant_id).order_by('-CreatedAt')[:limit])
        
        if records:
            print(f"[SYSTEM-RISK] Processing {len(records)} records for source {source_type}")
            for record in records:
                res = _process_single_source_record(tenant_id, source_type, record)
                results["created"] += res.get("created", 0)
                results["skipped"] += res.get("skipped", 0)
                if res.get("error"):
                    results["errors"].append(res["error"])
                
    # Process Specific Documents or Subfolders
    if document_ids or subfolder_ids:
        from grc.models import CompanySubfolderDocument, FileOperations
        
        if document_ids:
            print(f"[SYSTEM-RISK] Processing {len(document_ids)} specific documents")
            docs = FileOperations.objects.filter(id__in=document_ids)
            for doc in docs:
                doc_res = generate_risk_candidates_from_document(tenant_id, doc)
                results["created"] += doc_res.get("created", 0)
                results["skipped"] += doc_res.get("skipped", 0)
                if doc_res.get("errors"):
                    results["errors"].extend(doc_res["errors"])
        else:
            print(f"[SYSTEM-RISK] Processing all documents in {len(subfolder_ids)} subfolders")
            for subfolder_id in subfolder_ids:
                # Find documents in this subfolder
                links = CompanySubfolderDocument.objects.filter(
                    company_subfolder_id=subfolder_id
                ).select_related('file_operation')
                
                for link in links:
                    if link.file_operation:
                        doc_res = generate_risk_candidates_from_document(tenant_id, link.file_operation)
                        results["created"] += doc_res.get("created", 0)
                        results["skipped"] += doc_res.get("skipped", 0)
                        if doc_res.get("errors"):
                            results["errors"].extend(doc_res["errors"])

    # Process Checklist if requested
    if run_checklist:
        # Fetch checklisted items
        checklist_items = Compliance.objects.filter(tenant_id=tenant_id, status='CHECKLIST')
        for item in checklist_items:
            res = _process_single_source_record(tenant_id, SystemIdentifiedRiskQueue.SOURCE_COMPLIANCE, item)
            results["created"] += res.get("created", 0)
            results["skipped"] += res.get("skipped", 0)
            if res.get("error"):
                results["errors"].append(res["error"])

    return results

def _process_single_source_record(tenant_id, source_type, record):
    """Analyze a single record from any source and save risk candidates."""
    try:
        data_summary = ""
        source_id = None
        source_ref = ""
        
        if source_type == SystemIdentifiedRiskQueue.SOURCE_INCIDENT:
            source_id = record.IncidentId
            data_summary = (
                f"Incident Title: {record.IncidentTitle}\n"
                f"Description: {record.Description}\n"
                f"Category: {getattr(record, 'IncidentCategory', 'N/A')}\n"
                f"Impact: {getattr(record, 'InitialImpactAssessment', 'N/A')}"
            )
            source_ref = f"Incident #{source_id}"
        elif source_type == SystemIdentifiedRiskQueue.SOURCE_COMPLIANCE:
            source_id = record.ComplianceId
            data_summary = (
                f"Compliance Title: {record.ComplianceTitle}\n"
                f"Description: {record.ComplianceItemDescription}\n"
                f"Scope: {record.Scope}\n"
                f"Objective: {record.Objective}"
            )
            source_ref = f"Compliance #{source_id}"
        elif source_type == SystemIdentifiedRiskQueue.SOURCE_AUDIT:
            source_id = record.AuditId
            data_summary = (
                f"Audit Title: {record.Title}\n"
                f"Scope: {record.Scope}\n"
                f"Comments: {getattr(record, 'Comments', 'N/A')}"
            )
            source_ref = f"Audit #{source_id}"
        elif source_type == SystemIdentifiedRiskQueue.SOURCE_MANUAL:
            source_id = record.EventId
            data_summary = (
                f"Event Title: {record.EventTitle}\n"
                f"Module: {record.Module}\n"
                f"Category: {record.Category}\n"
                f"Description: {record.Description}"
            )
            source_ref = f"Event #{source_id}"
            
        # Skip if we already ran it
        if SystemIdentifiedRiskQueue.objects.filter(
            tenant_id=tenant_id,
            source_module=source_type,
            source_record_id=source_id
        ).exists():
            return {"skipped": 1}

        # Call AI Service
        risk_candidates = ai_service.run_task("risk.identify_risks", {
            "source_type": source_type,
            "data_summary": data_summary
        })
        
        if not isinstance(risk_candidates, list):
            risk_candidates = []
            
        created_count = 0
        with transaction.atomic():
            for risk_data in risk_candidates:
                risk_title = risk_data.get('risk_title', '')
                if not risk_title:
                    continue
                    
                candidate = _save_risk_candidate(tenant_id, source_type, source_id, source_ref, risk_data)
                if candidate:
                    created_count += 1
        
        return {"created": created_count}
    except Exception as e:
        print(f"[SYSTEM-RISK] Error processing record: {e}")
        return {"error": str(e)}


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
                "risk.identify_risks",
                payload={
                    "source_type": source_module,
                    "data_summary": json.dumps(record, indent=2)
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
                    confidence_score, confidence_meta = _resolve_confidence_from_risk(risk_data)
                    SystemIdentifiedRiskQueue.objects.create(
                        tenant_id=tenant_id,
                        source_module=source_module,
                        source_record_id=source_record_id,
                        source_ref=source_ref,
                        risk_title=risk_title,
                        risk_type=risk_data.get("risk_type") or risk_data.get("RiskType", "Current"),
                        category=risk_data.get("category") or risk_data.get("Category", "") or "Operational",
                        criticality=risk_data.get("criticality") or risk_data.get("Criticality", "Medium"),
                        risk_description=risk_data.get("risk_description") or risk_data.get("RiskDescription", ""),
                        possible_damage=risk_data.get("possible_damage") or risk_data.get("PossibleDamage", ""),
                        business_impact=risk_data.get("business_impact") or risk_data.get("BusinessImpact", []),
                        likelihood=risk_data.get("likelihood") or risk_data.get("RiskLikelihood"),
                        impact=risk_data.get("impact") or risk_data.get("RiskImpact"),
                        priority=risk_data.get("priority") or risk_data.get("RiskPriority", "Medium"),
                        mitigation_steps=risk_data.get("mitigation_steps") or risk_data.get("RiskMitigation", []),
                        ai_reasoning=risk_data.get("ai_reasoning", ""),
                        confidence_score=confidence_score,
                        ai_metadata={
                            **confidence_meta,
                            "synthetic_source_record_id": record_id,
                            "synthetic_expected_risk_signal": record.get("expected_risk_signal"),
                        },
                        status=SystemIdentifiedRiskQueue.STATUS_PENDING_REVIEW,
                        velocity_score=risk_data.get('velocity_score', 50),
                        functional_area=risk_data.get('functional_area', 'General')
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

def create_risk_from_queue_entry(queue_entry, user_id, review_data=None):
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
    
    review_data = review_data or {}

    def _coalesce(*values):
        for v in values:
            if v is not None and v != "":
                return v
        return None

    def _parse_int(v, default=None):
        try:
            return int(v)
        except Exception:
            return default

    def _parse_float(v, default=None):
        try:
            return float(v)
        except Exception:
            return default

    final_business_impact = _coalesce(review_data.get("business_impact"), queue_entry.business_impact)
    if isinstance(final_business_impact, list):
        final_business_impact = ", ".join([str(x) for x in final_business_impact if str(x).strip()])
    elif final_business_impact is None:
        final_business_impact = ""
    else:
        final_business_impact = str(final_business_impact)

    final_mitigation = _coalesce(review_data.get("mitigation_steps"), queue_entry.mitigation_steps)
    if isinstance(final_mitigation, list):
        final_mitigation = "\n".join([str(x) for x in final_mitigation if str(x).strip()])
    elif final_mitigation is None:
        final_mitigation = ""
    else:
        final_mitigation = str(final_mitigation)

    with transaction.atomic():
        # Create risk record
        risk = Risk.objects.create(
            tenant=queue_entry.tenant,
            ComplianceId=_parse_int(review_data.get("compliance_id"), None),
            RiskTitle=_coalesce(review_data.get("risk_title"), queue_entry.risk_title),
            RiskDescription=_coalesce(review_data.get("risk_description"), queue_entry.risk_description),
            Criticality=_coalesce(review_data.get("criticality"), queue_entry.criticality),
            Category=_coalesce(review_data.get("category"), queue_entry.category),
            RiskType=_coalesce(review_data.get("risk_type"), queue_entry.risk_type),
            PossibleDamage=_coalesce(review_data.get("possible_damage"), queue_entry.possible_damage),
            BusinessImpact=final_business_impact,
            RiskLikelihood=_parse_int(_coalesce(review_data.get("likelihood"), queue_entry.likelihood), 5),
            RiskImpact=_parse_int(_coalesce(review_data.get("impact"), queue_entry.impact), 5),
            RiskExposureRating=_parse_float(_coalesce(review_data.get("exposure_rating"), queue_entry.exposure_rating), 25.0),
            RiskPriority=_coalesce(review_data.get("priority"), queue_entry.priority),
            RiskMitigation=final_mitigation,
            # Handle new AI fields in Risk table if columns exist, else in a metadata blob
            # Assuming current schema might not have all cols, we'll put them in RiskFormDetails
            RiskFormDetails={
                "source_queue_id": queue_entry.id,
                "velocity_score": _parse_int(_coalesce(review_data.get("velocity_score"), queue_entry.velocity_score), 5),
                "control_effectiveness": _coalesce(review_data.get("control_effectiveness"), "Low"),
                "framework_reference": _coalesce(review_data.get("framework_reference"), ""),
                "risk_owner": _coalesce(review_data.get("risk_owner"), ""),
                "reviewer": _coalesce(review_data.get("reviewer"), ""),
                "notes": _coalesce(review_data.get("notes"), ""),
                "residual_risk_score": _parse_float(review_data.get("residual_risk_score"), 0.0),
                "functional_area": _coalesce(review_data.get("functional_area"), queue_entry.functional_area),
                "justifications": review_data.get("justifications", (queue_entry.ai_metadata or {}).get("review_overrides", {}).get("justifications", {}))
            },
            Origin='SYSTEM-AI',
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
        pending_approval_count=Count('id', filter=Q(status=SystemIdentifiedRiskQueue.STATUS_ACCEPTED_PENDING_APPROVAL)),
        accepted_count=Count('id', filter=Q(status=SystemIdentifiedRiskQueue.STATUS_APPROVED_ADDED)),
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
        'pending_approval_count': stats['pending_approval_count'] or 0,
        'accepted_count': stats['accepted_count'] or 0,
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
    queue_entry.velocity_score = _parse_int(review_data.get('velocity_score'), queue_entry.velocity_score)
    queue_entry.functional_area = review_data.get('functional_area', queue_entry.functional_area)
    queue_entry.review_notes = review_data.get('notes', queue_entry.review_notes)  # Map from 'notes' in frontend to 'review_notes'

    # Keep additional Create Risk-aligned fields in metadata so review modal can restore them.
    meta = queue_entry.ai_metadata if isinstance(queue_entry.ai_metadata, dict) else {}
    review_overrides = meta.get("review_overrides", {})
    review_overrides.update({
        "compliance_id": review_data.get("compliance_id", review_overrides.get("compliance_id")),
        "control_effectiveness": review_data.get("control_effectiveness", review_overrides.get("control_effectiveness")),
        "framework_reference": review_data.get("framework_reference", review_overrides.get("framework_reference")),
        "risk_owner": review_data.get("risk_owner", review_overrides.get("risk_owner")),
        "reviewer": review_data.get("reviewer", review_overrides.get("reviewer")),
        "residual_risk_score": review_data.get("residual_risk_score", review_overrides.get("residual_risk_score")),
        "justifications": review_data.get("justifications", review_overrides.get("justifications", {}))
    })
    meta["review_overrides"] = review_overrides
    queue_entry.ai_metadata = meta
    
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


def create_risk_from_queue_entry_for_workflow(queue_entry, user_id, review_data=None):
    """
    Convert an accepted queue entry to a Risk Instance for workflow (not Risk Register yet).
    This creates a RiskInstance that goes through approval workflow before becoming a Risk.

    Args:
        queue_entry: SystemIdentifiedRiskQueue instance
        user_id: ID of the user creating the risk
        review_data: Optional review data overrides

    Returns:
        RiskInstance: Created risk instance
    """
    from ...models import RiskInstance, Framework
    from django.utils import timezone

    print(f"[SYSTEM-RISK] Creating RiskInstance for workflow from queue entry {queue_entry.id}: {queue_entry.risk_title[:60]}...")

    review_data = review_data or {}

    def _coalesce(*values):
        for v in values:
            if v is not None and v != "":
                return v
        return None

    def _parse_int(v, default=None):
        try:
            return int(v)
        except Exception:
            return default

    def _parse_float(v, default=None):
        try:
            return float(v)
        except Exception:
            return default

    final_business_impact = _coalesce(review_data.get("business_impact"), queue_entry.business_impact)
    if isinstance(final_business_impact, list):
        final_business_impact = ", ".join([str(x) for x in final_business_impact if str(x).strip()])
    elif final_business_impact is None:
        final_business_impact = ""
    else:
        final_business_impact = str(final_business_impact)

    final_mitigation = _coalesce(review_data.get("mitigation_steps"), queue_entry.mitigation_steps)
    if isinstance(final_mitigation, list):
        final_mitigation = "\n".join([str(x) for x in final_mitigation if str(x).strip()])
    elif final_mitigation is None:
        final_mitigation = ""
    else:
        final_mitigation = str(final_mitigation)

    # Framework is mandatory in existing RiskInstance schema.
    # Resolve a safe framework id automatically so frontend does not need to send one.
    framework_id = _parse_int(review_data.get("framework_id"), None)
    if framework_id is None:
        default_fw = Framework.objects.order_by("FrameworkId").first()
        framework_id = default_fw.FrameworkId if default_fw else None
    if framework_id is None:
        raise ValueError("No framework record available to create risk workflow instance.")

    # Create RiskInstance (not Risk - this goes through workflow first)
    # IMPORTANT: use RiskInstance's actual column names.
    risk_instance = RiskInstance.objects.create(
        RiskTitle=_coalesce(review_data.get("risk_title"), queue_entry.risk_title) or "Untitled Risk",
        RiskDescription=_coalesce(review_data.get("risk_description"), queue_entry.risk_description) or "",
        RiskType=_coalesce(review_data.get("risk_type"), queue_entry.risk_type) or "Current",
        Category=_coalesce(review_data.get("category"), queue_entry.category) or "Operational",
        Criticality=_coalesce(review_data.get("criticality"), queue_entry.criticality) or "Medium",
        PossibleDamage=_coalesce(review_data.get("possible_damage"), queue_entry.possible_damage) or "",
        BusinessImpact=final_business_impact,
        RiskLikelihood=_parse_int(_coalesce(review_data.get("likelihood"), queue_entry.likelihood), 5),
        RiskImpact=_parse_int(_coalesce(review_data.get("impact"), queue_entry.impact), 5),
        RiskExposureRating=_parse_int(_coalesce(review_data.get("exposure_rating"), queue_entry.exposure_rating), 25),
        RiskPriority=_coalesce(review_data.get("priority"), queue_entry.priority) or "Medium",
        RiskMitigation=[x for x in final_mitigation.split("\n") if x.strip()] if isinstance(final_mitigation, str) else final_mitigation,
        RiskStatus='Pending Approval',  # Set to pending approval for workflow
        UserId=_parse_int(user_id, None),
        ReportedBy=_parse_int(user_id, None),
        tenant_id=queue_entry.tenant_id,
        ComplianceId=_parse_int(review_data.get("compliance_id"), None),
        Origin="SystemIdentifiedRiskQueue",
        RiskFormDetails={
            "source_queue_id": queue_entry.id,
            "source_ref": queue_entry.source_ref,
            "workflow_type": "system_risk",
            "velocity_score": _parse_int(_coalesce(review_data.get("velocity_score"), queue_entry.velocity_score), 5),
            "control_effectiveness": _coalesce(review_data.get("control_effectiveness"), "Low"),
            "framework_reference": _coalesce(review_data.get("framework_reference"), ""),
            "risk_owner": _coalesce(review_data.get("risk_owner"), ""),
            "reviewer": _coalesce(review_data.get("reviewer"), ""),
            "notes": _coalesce(review_data.get("notes"), ""),
            "residual_risk_score": _parse_float(review_data.get("residual_risk_score"), 0.0),
            "functional_area": _coalesce(review_data.get("functional_area"), queue_entry.functional_area),
            "justifications": review_data.get("justifications", (queue_entry.ai_metadata or {}).get("review_overrides", {}).get("justifications", {}))
        },
        FrameworkId_id=framework_id,
    )

    print(f"[SYSTEM-RISK] Created RiskInstance {risk_instance.RiskInstanceId}: {risk_instance.RiskTitle[:60]}...")
    return risk_instance


def find_latest_risk_document(tenant_id):
    """
    Locates the most recent file in the 'RISK_DOCUMENTS' subfolder for this tenant.
    Returns (file_operation, link) tuple or (None, None).
    """
    # 1. Find the subfolder
    subfolder = CompanySubfolder.objects.filter(
        code__iexact='RISK_DOCUMENTS',
        company_folder__code__iexact='AI_RISK',
        tenant_id=tenant_id
    ).first()
    
    if not subfolder:
        subfolder = CompanySubfolder.objects.filter(
            code__iexact='RISK_DOCUMENTS',
            tenant_id=tenant_id
        ).first()
        
    if not subfolder:
        print(f"[SYSTEM-RISK] No subfolder with code 'RISK_DOCUMENTS' found for tenant {tenant_id}.")
        return None, None
        
    # 2. Get the latest linked document in that subfolder
    latest_link = CompanySubfolderDocument.objects.filter(
        company_subfolder=subfolder
    ).select_related('file_operation').order_by('-file_operation__created_at').first()
    
    if not latest_link:
        print(f"[SYSTEM-RISK] No documents found in 'RISK_DOCUMENTS' for tenant {tenant_id}")
        return None, None
        
    return latest_link.file_operation, latest_link


def generate_risk_candidates_from_document(
    tenant_id, 
    file_op, 
    link=None,
    progress_callback=None, 
    should_abort=None
):
    """
    Extracts risks from a specific document using AI and creates queue entries.
    """
    results = {"processed": 1, "created": 0, "skipped": 0, "errors": []}
    
    if not file_op:
        return results
        
    print(f"[SYSTEM-RISK][DOC] Starting analysis for file: {file_op.original_name} (ID: {file_op.id})")
    
    if progress_callback:
        progress_callback(processed=0, total=1, phase="extracting", last_record=file_op.original_name)

    try:
        # 1. Try candidates for S3 download (matching document.py logic)
        s3_client = create_direct_mysql_client()
        with tempfile.TemporaryDirectory() as temp_dir:
            # Decrypt filename for local storage
            raw_file_name = file_op.original_name or file_op.file_name or "risk_doc"
            file_name_decrypted = decrypt_any_encrypted_value(raw_file_name)
            if not os.path.splitext(file_name_decrypted)[1] and file_op.file_type:
                file_name_decrypted += f".{file_op.file_type}"
            
            # Build candidate S3 keys
            candidates = []
            
            # Candidate 1: Link key
            if link and link.s3_key:
                val = link.s3_key
                candidates.append(val)
                candidates.append(decrypt_any_encrypted_value(val))
                candidates.append(encrypt_data(val))
            
            # Candidate 2: FileOp key
            if file_op.s3_key:
                val = file_op.s3_key
                candidates.append(val)
                candidates.append(decrypt_any_encrypted_value(val))
                candidates.append(encrypt_data(val))
            
            # Candidate 3: stored_name
            if hasattr(file_op, 'stored_name') and file_op.stored_name:
                val = file_op.stored_name
                candidates.append(val)
                candidates.append(decrypt_any_encrypted_value(val))
                candidates.append(encrypt_data(val))
                
            # Deduplicate while preserving order
            unique_candidates = []
            for c in candidates:
                if c and c not in unique_candidates:
                    unique_candidates.append(c)
            
            download_success = False
            last_error = "No candidates found"
            
            # Local filename logic (as requested: encrypt the filename for storage if needed, 
            # but we need it decrypted to match analysis expectations or at least consistent)
            local_save_name = file_name_decrypted
            local_file_path = os.path.join(temp_dir, local_save_name)
            
            user_id_decrypted = decrypt_any_encrypted_value(file_op.user_id) if file_op.user_id else "system"
            
            # Strategy A: Try candidates via RenderS3Client (microservice)
            for s3_key in unique_candidates:
                print(f"[SYSTEM-RISK][DOC] Attempting download with key: {s3_key}")
                try:
                    download_result = s3_client.download(
                        s3_key=s3_key,
                        file_name=local_save_name,
                        destination_path=temp_dir,
                        user_id=str(user_id_decrypted)
                    )
                    
                    if download_result and download_result.get('success'):
                        # Verify file exists on disk
                        if os.path.exists(local_file_path):
                            download_success = True
                            break
                        # Check if it was saved with a different name
                        existing_files = os.listdir(temp_dir)
                        if existing_files:
                            local_file_path = os.path.join(temp_dir, existing_files[0])
                            download_success = True
                            break
                    
                    last_error = download_result.get('error', 'Unknown S3 error') if download_result else 'No response'
                    print(f"[SYSTEM-RISK][DOC] Candidate {s3_key} failed: {last_error}")
                except Exception as e:
                    last_error = str(e)
                    print(f"[SYSTEM-RISK][DOC] Candidate {s3_key} crashed: {e}")
            
            # Strategy B: Fallback to direct s3_url download if Strategy A failed
            if not download_success and file_op.s3_url:
                print(f"[SYSTEM-RISK][DOC] Falling back to direct URL download: {file_op.s3_url}")
                try:
                    resp = requests.get(file_op.s3_url, stream=True, timeout=60)
                    if resp.status_code == 200:
                        os.makedirs(temp_dir, exist_ok=True)
                        with open(local_file_path, 'wb') as f:
                            for chunk in resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                        download_success = True
                        print(f"[SYSTEM-RISK][DOC] Direct URL download successful.")
                    else:
                        last_error = f"Direct download failed: HTTP {resp.status_code}"
                except Exception as e:
                    last_error = f"Direct download error: {e}"
                    print(f"[SYSTEM-RISK][DOC] Direct download error: {e}")
            
            if not download_success:
                print(f"[SYSTEM-RISK][DOC] S3 Download failed for all methods. Last error: {last_error}")
                raise FileNotFoundError(f"Failed to download file {file_op.id} from S3. Error: {last_error}")
            
            print(f"[SYSTEM-RISK][DOC] Successful download. File located at: {local_file_path}")
            
            # 2. Extract text and preprocess
            document_text = document_extractor.extract_and_preprocess(local_file_path)
            
            if not document_text or len(document_text.strip()) < 50:
                raise ValueError("Document text is too short or could not be extracted.")
                
            print(f"[SYSTEM-RISK][DOC] Extracted {len(document_text)} characters of text")
            
            if progress_callback:
                progress_callback(processed=0, total=1, phase="analyzing", last_record=file_op.original_name)
                
            # Call the new centralized identify_risks task for document extraction
            risk_candidates = ai_service.run_task(
                "risk.identify_risks",
                payload={
                    "source_type": "DOCUMENT",
                    "data_summary": f"File Name: {file_op.original_name}\n\nDocument Content:\n{document_text[:5000]}"
                }
            )
        
        if not risk_candidates:
            print("[SYSTEM-RISK][DOC] AI identified no risks in the document.")
            results["skipped"] = 1
            if progress_callback:
                progress_callback(processed=1, total=1, phase="completed", last_record=None)
            return results
            
        print(f"[SYSTEM-RISK][DOC] AI generated {len(risk_candidates)} risk candidates")
        
        # 4. Create queue entries
        for risk_data in risk_candidates:
            if should_abort and should_abort():
                break
                
            raw_title = risk_data.get('risk_title') or risk_data.get('RiskTitle', '')
            risk_title = raw_title.strip() if raw_title else ''
            if not risk_title:
                continue
                
            # Check for existing risks from this same document
            source_ref = f"Doc: {file_op.original_name}"
            existing = SystemIdentifiedRiskQueue.objects.filter(
                tenant_id=tenant_id,
                source_record_id=file_op.id,
                source_ref=source_ref,
                risk_title__icontains=risk_title[:50]
            ).exists()
            
            if existing:
                results["skipped"] += 1
                continue
                
            with transaction.atomic():
                confidence_score, confidence_meta = _resolve_confidence_from_risk(risk_data)
                
                SystemIdentifiedRiskQueue.objects.create(
                    tenant_id=tenant_id,
                    source_module=SystemIdentifiedRiskQueue.SOURCE_INTEGRATION,
                    source_record_id=file_op.id,
                    source_ref=source_ref,
                    risk_title=risk_title,
                    risk_type=risk_data.get('risk_type') or risk_data.get('RiskType', 'Current'),
                    category=risk_data.get('category') or risk_data.get('Category', 'Operational'),
                    criticality=risk_data.get('criticality') or risk_data.get('Criticality', 'Medium'),
                    risk_description=risk_data.get('risk_description') or risk_data.get('RiskDescription', ''),
                    possible_damage=risk_data.get('possible_damage') or risk_data.get('PossibleDamage', ''),
                    business_impact=risk_data.get('business_impact') or risk_data.get('BusinessImpact', []),
                    likelihood=risk_data.get('likelihood') or risk_data.get('RiskLikelihood'),
                    impact=risk_data.get('impact') or risk_data.get('RiskImpact'),
                    priority=risk_data.get('priority') or risk_data.get('RiskPriority', 'Medium'),
                    mitigation_steps=risk_data.get('mitigation_steps') or risk_data.get('RiskMitigation', []),
                    ai_reasoning=risk_data.get('ai_reasoning', 'Extracted from uploaded document.'),
                    confidence_score=confidence_score,
                    ai_metadata={
                        **confidence_meta,
                        "file_id": file_op.id,
                        "file_name": file_op.original_name
                    },
                    status=SystemIdentifiedRiskQueue.STATUS_PENDING_REVIEW,
                    velocity_score=risk_data.get('velocity_score', 3),
                    functional_area=risk_data.get('functional_area', 'Operations')
                )
                results["created"] += 1
                
        print(f"[SYSTEM-RISK][DOC] Created {results['created']} queue entries from document.")
        
    except Exception as e:
        error_msg = f"Document {file_op.id}: {str(e)}"
        results["errors"].append(error_msg)
        print(f"[SYSTEM-RISK][DOC] Error processing document: {e}")
        
    if progress_callback:
        progress_callback(processed=1, total=1, phase="completed", last_record=None)
        
    return results
