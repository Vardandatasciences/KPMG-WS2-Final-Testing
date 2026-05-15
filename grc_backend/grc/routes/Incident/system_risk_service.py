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


def _get_tenant_frameworks_context(tenant_id):
    """
    Fetch frameworks for the tenant and return a formatted string for injection into AI prompts.
    Falls back to empty string if no frameworks found.
    """
    try:
        from ...models import Framework
        frameworks = Framework.objects.filter(tenant_id=tenant_id).values(
            'FrameworkId', 'FrameworkName'
        ).order_by('FrameworkName')[:20]
        if not frameworks:
            return ""
        names = [fw.get('FrameworkName') or '' for fw in frameworks if fw.get('FrameworkName')]
        if not names:
            return ""
        names_list = "\n".join(f"  - {n}" for n in names)
        return (
            f"The following are the ONLY frameworks used by this organisation.\n"
            f"{names_list}\n"
            f"You MUST pick 'framework_reference' ONLY from this list. "
            f"Do NOT use NIST, ISO, GDPR, or any other framework not listed above."
        )
    except Exception:
        return ""


def _clamp_int(value, low=0, high=100, default=60):
    try:
        return max(low, min(high, int(value)))
    except Exception:
        return default


def ensure_department_exists(department_name, tenant_id):
    """
    Check if a department exists for a tenant, if not create it with defaults.
    Ensures data integrity for functional_area categorization.
    """
    if not department_name or not tenant_id:
        return department_name
        
    from ...models import Department, Framework, Entity
    from django.utils import timezone
    
    # Standardize name
    name = str(department_name).strip()
    if not name:
        return name
        
    # Check existing
    existing = Department.objects.filter(
        DepartmentName__iexact=name,
        tenant_id=tenant_id
    ).first()
    
    if existing:
        return existing.DepartmentName
        
    # Auto-provision if missing
    try:
        # Get defaults
        default_fw = Framework.objects.filter(tenant_id=tenant_id).first() or Framework.objects.first()
        default_entity = Entity.objects.filter(tenant_id=tenant_id).first() or Entity.objects.first()
        
        Department.objects.create(
            tenant_id=tenant_id,
            DepartmentName=name,
            EntityId=default_entity.Id if default_entity else 1,
            DepartmentHead=1, # Default to system/admin user ID 1
            IsActive=True,
            CreatedDate=timezone.now(),
            BusinessUnitId=1,
            FrameworkId=default_fw
        )
        print(f"[SYSTEM-RISK] Auto-provisioned department: {name} for tenant {tenant_id}")
        return name
    except Exception as e:
        print(f"[SYSTEM-RISK] Failed to auto-provision department '{name}': {e}")
        return name # Return name anyway to store in risk record


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

def _validate_framework_reference(tenant_id, framework_ref):
    """Return framework_ref only if it matches a tenant framework name, else return empty string."""
    if not framework_ref:
        return ''
    try:
        from ...models import Framework
        names = list(Framework.objects.filter(tenant_id=tenant_id).values_list('FrameworkName', flat=True))
        ref_lower = framework_ref.strip().lower()
        for name in names:
            if name and (name.lower() in ref_lower or ref_lower in name.lower()):
                return name
        return ''
    except Exception:
        return framework_ref


def _save_risk_candidate(tenant_id, source_module, source_record_id, source_ref, risk_data):
    """Internal helper to save a single risk candidate to the queue."""
    try:
        # Resolve confidence and metadata
        confidence_score, ai_metadata = _resolve_confidence_from_risk(risk_data)
        
        # Merge extra source metadata if present in risk_data
        if 'source_url' in risk_data:
            ai_metadata['source_url'] = risk_data['source_url']
        if 'source_title' in risk_data:
            ai_metadata['source_title'] = risk_data['source_title']
        if 'source_text' in risk_data:
            ai_metadata['source_text'] = risk_data['source_text']
            
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
            framework_reference=_validate_framework_reference(tenant_id, risk_data.get('framework_reference') or ai_metadata.get('framework_reference') or ''),
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
            elif source_type == SystemIdentifiedRiskQueue.SOURCE_EVENT: # Used for Events
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
                "data_summary": data_summary,
                "frameworks_context": _get_tenant_frameworks_context(tenant_id),
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
    frameworks_context = _get_tenant_frameworks_context(tenant_id)
    
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
                    "data_summary": json.dumps(incident_data, indent=2),
                    "frameworks_context": frameworks_context,
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
                    
                    # Prepare more descriptive source ref
                    source_ref = f"Incident: {incident.IncidentTitle[:100]} (#{incident.IncidentId})"
                    
                    # Add source metadata for the drawer
                    risk_data['source_title'] = incident.IncidentTitle
                    risk_data['source_text'] = incident.Description
                    
                    candidate = _save_risk_candidate(
                        tenant_id, 
                        SystemIdentifiedRiskQueue.SOURCE_INCIDENT, 
                        incident.IncidentId, 
                        source_ref, 
                        risk_data
                    )
                    
                    results["created"] += 1
                    print(f"[SYSTEM-RISK] Created queue entry {queue_entry.id}: {risk_title[:60]}...")
                    
        except Exception as e:
            error_msg = f"Incident {incident.IncidentId}: {str(e)}"
            results["errors"].append(error_msg)
            print(f"[SYSTEM-RISK] Error processing incident {incident.IncidentId}: {e}")
    
    print(f"[SYSTEM-RISK] Scan complete: created={results['created']}, skipped={results['skipped']}, errors={len(results['errors'])}")
    return results

def _get_framework_name_by_id(tenant_id, framework_id):
    """Return the FrameworkName for a given FrameworkId scoped to the tenant, or None."""
    if not framework_id:
        return None
    try:
        from ...models import Framework
        fw = Framework.objects.filter(tenant_id=tenant_id, FrameworkId=framework_id).values('FrameworkName').first()
        return fw['FrameworkName'] if fw else None
    except Exception:
        return None


def generate_risk_candidates_from_multiple_sources(tenant_id, source_types=None, limit=5, subfolder_ids=None, document_ids=None, run_checklist=False, external_urls=None, framework_id=None):
    """
    Scan recent records from multiple modules and generate risk candidates.
    Supported sources: INCIDENT, COMPLIANCE, AUDIT, MANUAL(Events), DOCUMENT, EXTERNAL_SOURCES
    If framework_id is provided, GRC module records are filtered to that framework and
    the framework name is stored as framework_reference on all generated risks.
    """
    results = {"created": 0, "skipped": 0, "errors": []}
    if source_types is None:
        source_types = []

    selected_framework_name = _get_framework_name_by_id(tenant_id, framework_id) if framework_id else None
    if framework_id and not selected_framework_name:
        print(f"[SYSTEM-RISK] WARNING: framework_id={framework_id} not found for tenant {tenant_id}. Ignoring.")
        framework_id = None

    print(f"[SYSTEM-RISK] Executing generate_risk_candidates_from_multiple_sources")
    print(f"[SYSTEM-RISK] Starting multi-source scan. Sources={source_types}, FrameworkId={framework_id}, FrameworkName={selected_framework_name}, Tenant {tenant_id}")

    # Process each standard source module
    for source_type in source_types:
        records = []
        if source_type == SystemIdentifiedRiskQueue.SOURCE_INCIDENT:
            qs = Incident.objects.filter(tenant_id=tenant_id)
            if framework_id:
                qs = qs.filter(FrameworkId=framework_id)
            records = list(qs.order_by('-Date')[:limit])
        elif source_type == SystemIdentifiedRiskQueue.SOURCE_COMPLIANCE:
            qs = Compliance.objects.filter(tenant_id=tenant_id)
            if framework_id:
                qs = qs.filter(FrameworkId=framework_id)
            records = list(qs.order_by('-CreatedByDate')[:limit])
        elif source_type == SystemIdentifiedRiskQueue.SOURCE_AUDIT:
            qs = Audit.objects.filter(tenant_id=tenant_id)
            if framework_id:
                qs = qs.filter(FrameworkId=framework_id)
            records = list(qs.order_by('-AssignedDate')[:limit])
        elif source_type == SystemIdentifiedRiskQueue.SOURCE_EVENT:
            qs = Event.objects.filter(tenant_id=tenant_id)
            if framework_id:
                qs = qs.filter(FrameworkId=framework_id)
            records = list(qs.order_by('-CreatedAt')[:limit])

        if not records and framework_id:
            msg = f"No {source_type} records found for the selected framework (id={framework_id})."
            print(f"[SYSTEM-RISK] {msg}")
            results["errors"].append(msg)
            continue

        if records:
            print(f"[SYSTEM-RISK] Processing {len(records)} records for source {source_type}")
            for record in records:
                res = _process_single_source_record(tenant_id, source_type, record, forced_framework_name=selected_framework_name)
                results["created"] += res.get("created", 0)
                results["skipped"] += res.get("skipped", 0)
                if res.get("error"):
                    results["errors"].append(res["error"])

    
    # Process External Sources
    # Check for various possible identifiers for external sources
    is_external = 'EXTERNAL' in source_types or 'EXTERNAL_SOURCES' in source_types
    print(f"[SYSTEM-RISK] External source check: {is_external} (source_types={source_types})")
    
    if is_external or external_urls:
        print(f"[SYSTEM-RISK] Processing external sources for tenant {tenant_id}")
        ext_res = generate_risk_candidates_from_external_sources(tenant_id, limit=limit, urls=external_urls)
        results["created"] += ext_res.get("created", 0)
        results["skipped"] += ext_res.get("skipped", 0)
        if ext_res.get("errors"):
            results["errors"].extend(ext_res["errors"])
                
    # Process Specific Documents or Subfolders
    if document_ids or subfolder_ids:
        from grc.models import CompanySubfolderDocument, FileOperations
        def _safe_int_list(values):
            out = []
            for value in values or []:
                try:
                    out.append(int(value))
                except Exception:
                    continue
            return out

        allowed_subfolder_ids = _safe_int_list(subfolder_ids)
        allowed_file_ids = set()
        if allowed_subfolder_ids:
            allowed_file_ids = set(
                CompanySubfolderDocument.objects.filter(
                    company_subfolder_id__in=allowed_subfolder_ids,
                    company_subfolder__tenant_id=tenant_id,
                ).values_list("file_operation_id", flat=True)
            )
        
        if document_ids:
            print(f"[SYSTEM-RISK] Processing {len(document_ids)} specific documents")
            requested_doc_ids = _safe_int_list(document_ids)
            docs_qs = FileOperations.objects.filter(id__in=requested_doc_ids, tenant_id=tenant_id)
            if allowed_file_ids:
                docs_qs = docs_qs.filter(id__in=allowed_file_ids)
            docs = list(docs_qs)
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
                    company_subfolder_id=subfolder_id,
                    company_subfolder__tenant_id=tenant_id,
                ).select_related('file_operation')
                
                for link in links:
                    if link.file_operation and getattr(link.file_operation, "tenant_id", None) == tenant_id:
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
            res = _process_single_source_record(tenant_id, SystemIdentifiedRiskQueue.SOURCE_COMPLIANCE, item, forced_framework_name=selected_framework_name)
            results["created"] += res.get("created", 0)
            results["skipped"] += res.get("skipped", 0)
            if res.get("error"):
                results["errors"].append(res["error"])

    return results

def _process_single_source_record(tenant_id, source_type, record, forced_framework_name=None):
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
        elif source_type == SystemIdentifiedRiskQueue.SOURCE_EVENT:
            source_id = record.EventId
            data_summary = (
                f"Event Title: {record.EventTitle}\n"
                f"Module: {record.Module}\n"
                f"Category: {record.Category}\n"
                f"Description: {record.Description}"
            )
            source_ref = f"Event #{source_id}"
            
        # Skip if we already ran it — but allow re-scan when a specific framework is forced
        if not forced_framework_name:
            if SystemIdentifiedRiskQueue.objects.filter(
                tenant_id=tenant_id,
                source_module=source_type,
                source_record_id=source_id
            ).exists():
                return {"skipped": 1}
        else:
            # With a framework filter: skip only if a risk with the SAME framework already exists
            if SystemIdentifiedRiskQueue.objects.filter(
                tenant_id=tenant_id,
                source_module=source_type,
                source_record_id=source_id,
                framework_reference=forced_framework_name
            ).exists():
                return {"skipped": 1}

        # Call AI Service
        risk_candidates = ai_service.run_task("risk.identify_risks", {
            "source_type": source_type,
            "data_summary": data_summary,
            "frameworks_context": _get_tenant_frameworks_context(tenant_id),
        })
        
        if not isinstance(risk_candidates, list):
            risk_candidates = []
            
        created_count = 0
        with transaction.atomic():
            for risk_data in risk_candidates:
                risk_title = risk_data.get('risk_title', '')
                if not risk_title:
                    continue
                    
                if forced_framework_name:
                    risk_data['framework_reference'] = forced_framework_name
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
        SystemIdentifiedRiskQueue.SOURCE_EVENT,
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

    # Resolve functional area and auto-provision if needed
    raw_dept = _coalesce(review_data.get("functional_area"), queue_entry.functional_area)
    final_dept = ensure_department_exists(raw_dept, queue_entry.tenant_id)

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
                "framework_reference": _coalesce(review_data.get("framework_reference"), queue_entry.framework_reference, ""),
                "risk_owner": _coalesce(review_data.get("risk_owner"), ""),
                "reviewer": _coalesce(review_data.get("reviewer"), ""),
                "notes": _coalesce(review_data.get("notes"), ""),
                "residual_risk_score": _parse_float(review_data.get("residual_risk_score"), 0.0),
                "functional_area": _coalesce(review_data.get("functional_area"), queue_entry.functional_area),
                "justifications": review_data.get("justifications", (queue_entry.ai_metadata or {}).get("review_overrides", {}).get("justifications", {}))
            },
            functional_area=final_dept,
            Origin='SYSTEM-AI',
            CreatedAt=timezone.now().date()
        )
        
        # Update queue entry
        queue_entry.status = SystemIdentifiedRiskQueue.STATUS_APPROVED_ADDED
        queue_entry.created_risk = risk
        queue_entry.approved_by_id = user_id
        queue_entry.approved_at = timezone.now()
        if review_data.get('framework_reference'):
            queue_entry.framework_reference = review_data.get('framework_reference')
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
    if review_data.get('framework_reference') is not None:
        queue_entry.framework_reference = review_data.get('framework_reference')

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

    # Resolve functional area and auto-provision if needed
    raw_dept = _coalesce(review_data.get("functional_area"), queue_entry.functional_area)
    final_dept = ensure_department_exists(raw_dept, queue_entry.tenant_id)

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
        functional_area=final_dept,
        RiskMitigation=[x for x in final_mitigation.split("\n") if x.strip()] if isinstance(final_mitigation, str) else final_mitigation,
        RiskStatus='Pending Approval',  # Set to pending approval for workflow
        UserId=_parse_int(user_id, None),
        ReportedBy=_parse_int(user_id, None),
        tenant_id=queue_entry.tenant_id,
        ComplianceId=_parse_int(review_data.get("compliance_id"), None),
        Origin='SYSTEM-AI',
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

def _selenium_fetch(url, wait_seconds=6):
    """
    Use headless Chrome via Selenium to fetch a fully JS-rendered page.
    Returns (title, html) or raises on failure.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
    except Exception:
        service = Service()  # rely on chromedriver already on PATH

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.set_page_load_timeout(30)
        driver.get(url)
        # Wait for body to have some text content (JS render)
        try:
            WebDriverWait(driver, wait_seconds).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
        except Exception:
            pass
        import time as _time
        _time.sleep(wait_seconds)  # extra wait for dynamic content
        title = driver.title or "External Source"
        html = driver.page_source
        return title, html
    finally:
        driver.quit()


def _extract_text_from_html(html):
    """
    Extract clean readable text from raw HTML.
    Works on both server-rendered and JS-rendered pages.
    """
    import re
    # Remove non-content blocks
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    html = re.sub(r'<noscript[^>]*>.*?</noscript>', '', html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.IGNORECASE | re.DOTALL)

    # Extract meaningful text nodes from semantic tags
    semantic = re.findall(
        r'<(?:p|h[1-6]|li|td|th|blockquote|article|section|div)[^>]*>(.*?)'
        r'</(?:p|h[1-6]|li|td|th|blockquote|article|section|div)>',
        html, re.IGNORECASE | re.DOTALL
    )
    texts = []
    for chunk in semantic:
        chunk = re.sub(r'<[^>]+>', ' ', chunk)
        chunk = re.sub(r'\s+', ' ', chunk).strip()
        if len(chunk) > 40:
            texts.append(chunk)

    # Fallback: strip all remaining tags
    if not texts:
        fallback = re.sub(r'<[^>]+>', ' ', html)
        fallback = re.sub(r'\s+', ' ', fallback).strip()
        texts = [fallback]

    return ' '.join(texts)


def fetch_external_source_content(url):
    """
    Fetch and extract text from any external website.
    Strategy:
      1. Try Selenium headless Chrome (handles JS/SPA sites fully).
      2. Fall back to plain requests + regex if Selenium is unavailable.
    """
    import re

    title = "External Source"
    html = ""

    # ── Strategy 1: Selenium (full JS render) ───────────────────────────────
    selenium_ok = False
    try:
        print(f"[SYSTEM-RISK] Fetching {url} via Selenium headless Chrome")
        title, html = _selenium_fetch(url, wait_seconds=6)
        selenium_ok = True
        print(f"[SYSTEM-RISK] Selenium fetched {len(html)} raw chars from {url}")
    except Exception as se:
        print(f"[SYSTEM-RISK] Selenium unavailable ({se}), falling back to requests")

    # ── Strategy 2: Plain requests fallback ─────────────────────────────────
    if not selenium_ok:
        try:
            HEADERS = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            resp = requests.get(url, timeout=20, headers=HEADERS)
            resp.raise_for_status()
            html = resp.text
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = re.sub(r'\s+', ' ', title_match.group(1)).strip()
            print(f"[SYSTEM-RISK] requests fetched {len(html)} raw chars from {url}")
        except Exception as re_err:
            logger.error(f"[SYSTEM-RISK] Both Selenium and requests failed for {url}: {re_err}")
            return None

    # ── Extract clean text ───────────────────────────────────────────────────
    content = _extract_text_from_html(html)
    content = re.sub(r'\s+', ' ', content).strip()

    print(f"[SYSTEM-RISK] Extracted {len(content)} chars of clean text from {url}")

    if not content:
        print(f"[SYSTEM-RISK] WARNING: No text extracted from {url}")
        return None

    return {
        "url": url,
        "title": title,
        "text": content[:12000]
    }

def generate_risk_candidates_from_external_sources(tenant_id, limit=5, urls=None):
    """
    Scan external news portals and generate risk candidates.
    """
    if not urls:
        urls = [
            "https://medwatch-india-news.lovable.app",
            "https://bankingwatch-news.lovable.app/",
            "https://datashield-insight.lovable.app/"
        ]
    
    results = {"created": 0, "skipped": 0, "errors": []}
    
    for url in urls:
        try:
            print(f"[SYSTEM-RISK] Fetching external content from {url}")
            source_data = fetch_external_source_content(url)
            
            # Generate a stable ID for this external source URL
            url_hash = hashlib.md5(url.encode()).hexdigest()
            source_record_id = int(url_hash[:7], 16) # integer ID for DB
            source_record_id_hex = url_hash[:8]      # short hex for ref
            
            if not source_data or not source_data.get("text"):
                print(f"[SYSTEM-RISK] No content extracted from {url}")
                continue
                
            # Prepare data for AI analysis
            risk_candidates = ai_service.run_task(
                "risk.identify_risks",
                payload={
                    "source_type": "EXTERNAL_SOURCES",
                    "data_summary": f"Source Title: {source_data['title']}\nURL: {url}\n\nContent:\n{source_data['text']}",
                    "frameworks_context": _get_tenant_frameworks_context(tenant_id),
                }
            )
            
            if not risk_candidates:
                print(f"[SYSTEM-RISK] AI identified no risks for external source: {url}")
                continue
                
            print(f"[SYSTEM-RISK] AI generated {len(risk_candidates)} risk candidates for {url}")
            
            for risk_data in risk_candidates:
                raw_title = risk_data.get('risk_title') or risk_data.get('RiskTitle', '')
                risk_title = raw_title.strip() if raw_title else ''
                if not risk_title:
                    continue
                    
                source_ref = f"External: {source_data['title'][:100]} (#{source_record_id_hex})"
                
                # Add source metadata for the drawer
                risk_data['source_url'] = url
                risk_data['source_title'] = source_data['title']
                risk_data['source_text'] = source_data['text'][:1000] # Snippet
                
                # Check for duplicates
                existing = SystemIdentifiedRiskQueue.objects.filter(
                    tenant_id=tenant_id,
                    source_module=SystemIdentifiedRiskQueue.SOURCE_EXTERNAL,
                    source_record_id=source_record_id,
                    risk_title__icontains=risk_title[:50]
                ).exists()
                
                if existing:
                    results["skipped"] += 1
                    continue
                candidate = _save_risk_candidate(
                    tenant_id, 
                    SystemIdentifiedRiskQueue.SOURCE_EXTERNAL, 
                    source_record_id, 
                    source_ref, 
                    risk_data
                )
                if candidate:
                    results["created"] += 1
                    
        except Exception as e:
            results["errors"].append(f"{url}: {str(e)}")
            print(f"[SYSTEM-RISK] Error processing external source {url}: {e}")
            
    return results


def get_external_portals_list():
    """
    Returns the curated list of simulated news sites available for risk analysis.
    This list is used both by the scanner and the frontend selection modal.
    """
    return [
        {
            "name": "MedWatch India (Healthcare)",
            "url": "https://medwatch-india-news.lovable.app",
            "category": "Healthcare"
        },
        {
            "name": "BankingWatch (Finance)",
            "url": "https://bankingwatch-news.lovable.app/",
            "category": "Finance"
        },
        {
            "name": "DataShield Insight (Technology)",
            "url": "https://datashield-insight.lovable.app/",
            "category": "Technology"
        }
    ]
