import json
import os
import time
from datetime import date
from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect as csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from ...ai.service import get_ai_service
from ...debug_utils import debug_print
from ...models import (
    Compliance,
    Framework,
    FrameworkApproval,
    FrameworkVersion,
    Policy,
    PolicyApproval,
    PolicyVersion,
    SubPolicy,
    Users,
)
from ...rbac.permissions import PolicyCreatePermission, PolicyEditPermission, PolicyViewPermission
from ...tenant_utils import get_tenant_id_from_request, require_tenant, tenant_filter


policy_ai_jobs = None


def _get_job_service():
    global policy_ai_jobs
    if policy_ai_jobs is None:
        from ...ai.runtime.jobs import AIJobService

        policy_ai_jobs = AIJobService("policy_import")
    return policy_ai_jobs


def _parse_request_json(request) -> dict[str, Any]:
    if hasattr(request, "data") and request.data:
        return dict(request.data)
    if not getattr(request, "body", b""):
        return {}
    return json.loads(request.body)


def _resolve_user_id(data: dict[str, Any], request=None) -> str:
    user_id = data.get("user_id") or data.get("userid")
    if user_id:
        return str(user_id)
    if request is not None:
        if hasattr(request.user, "UserId") and getattr(request.user, "UserId", None):
            return str(request.user.UserId)
        if hasattr(request.user, "id") and getattr(request.user, "id", None):
            return str(request.user.id)
    return "1"


def _resolve_actor_id(request=None, data: dict[str, Any] | None = None) -> int:
    if data:
        explicit = data.get("reviewer_id") or data.get("user_id")
        if explicit is not None:
            try:
                return int(explicit)
            except (TypeError, ValueError):
                pass
    if request is not None:
        for attr in ("UserId", "id"):
            value = getattr(request.user, attr, None)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
    return 0


def _resolve_created_by_name(request, framework_data: dict[str, Any], user_id: str) -> str:
    created_by_name = framework_data.get("CreatedByName", "")
    if created_by_name:
        return created_by_name
    try:
        user_obj = Users.objects.filter(UserId=user_id).first()
        if user_obj:
            return getattr(user_obj, "UserName_plain", None) or getattr(user_obj, "UserName", None) or str(user_obj.UserName)
    except Exception:
        pass
    return getattr(getattr(request, "user", None), "username", None) or getattr(request, "session", {}).get("grc_username", "Admin")


def _user_folder(user_id: str) -> Path:
    folder = Path(settings.MEDIA_ROOT) / f"upload_{user_id}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _checked_section_path(user_id: str) -> Path:
    return _user_folder(user_id) / "checked_section.json"


def _framework_data_path(user_id: str) -> Path:
    return _user_folder(user_id) / "framework_data.json"


def _load_json(path: Path, default: Any):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _extract_nested_compliances(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compliances: list[dict[str, Any]] = []
    for section in sections:
        for policy in section.get("policies", []):
            for subpolicy in policy.get("subpolicies", []):
                for compliance in subpolicy.get("compliances", []):
                    enriched = dict(compliance)
                    enriched.setdefault("SubPolicyId", subpolicy.get("subpolicy_id", ""))
                    enriched.setdefault("SubPolicyTitle", subpolicy.get("subpolicy_title", ""))
                    enriched.setdefault("SectionTitle", section.get("section_title", ""))
                    enriched.setdefault("PolicyTitle", policy.get("policy_title", ""))
                    compliances.append(enriched)
    return compliances


def start_policy_import_job(task_id: str | None = None, message: str = "Queued") -> str:
    return _get_job_service().create_job(task_id=task_id, status="queued", message=message)


def get_policy_import_status(task_id: str):
    return _get_job_service().get_job_status(task_id)


def load_import_draft(user_id: str) -> dict[str, Any]:
    checked_data = _load_json(_checked_section_path(user_id), {"metadata": {}, "sections": []})
    framework_data = _load_json(_framework_data_path(user_id), {})
    framework_info = framework_data.get("framework_info", {})
    checked_data.setdefault("metadata", {})
    if framework_info:
        checked_data["metadata"]["framework_info"] = framework_info
    if "task_id" not in checked_data["metadata"]:
        checked_data["metadata"]["task_id"] = f"upload_{user_id}"
    checked_data["metadata"]["total_compliances"] = len(_extract_nested_compliances(checked_data.get("sections", [])))
    return checked_data


def save_selected_structure(data: dict[str, Any], request=None):
    selected_items = data.get("selected_items", [])
    if not selected_items:
        return JsonResponse({"error": "No items selected"}, status=400)

    user_id = _resolve_user_id(data, request)
    task_id = data.get("task_id") or f"upload_{user_id}"
    job_service = _get_job_service()
    job_service.update_job_status(
        task_id,
        status="draft_saved",
        progress=55,
        message="Policy draft structure saved",
        data={"user_id": user_id},
    )

    total_sections = len(selected_items)
    total_policies = sum(len(section.get("policies", [])) for section in selected_items)
    total_subpolicies = sum(
        len(policy.get("subpolicies", []))
        for section in selected_items
        for policy in section.get("policies", [])
    )

    checked_sections_data = {
        "metadata": {
            "task_id": task_id,
            "user_id": user_id,
            "creation_timestamp": int(time.time()),
            "creation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_sections": total_sections,
            "total_policies": total_policies,
            "total_subpolicies": total_subpolicies,
            "total_compliances": len(_extract_nested_compliances(selected_items)),
        },
        "sections": selected_items,
    }

    checked_section_file = _checked_section_path(user_id)
    _write_json(checked_section_file, checked_sections_data)
    return JsonResponse(
        {
            "message": "Selected sections saved successfully",
            "file_path": str(checked_section_file),
            "total_sections": total_sections,
            "total_policies": total_policies,
            "total_subpolicies": total_subpolicies,
            "status": "success",
        }
    )


def generate_selected_compliances(data: dict[str, Any], request=None):
    user_id = _resolve_user_id(data, request)
    checked_section_file = _checked_section_path(user_id)
    if not checked_section_file.exists():
        return JsonResponse({"error": "checked_section.json file not found"}, status=404)

    checked_data = _load_json(checked_section_file, {"sections": []})
    sections = checked_data.get("sections", [])
    if not sections:
        return JsonResponse({"error": "No sections found in checked_section.json"}, status=400)

    service = get_ai_service()
    print("[AI-POLICY] 🤖 Compliance generator: Using centralized AI service")
    task_id = checked_data.get("metadata", {}).get("task_id") or data.get("task_id") or f"upload_{user_id}"
    job_service = _get_job_service()
    job_service.update_job_status(task_id, status="processing", progress=75, message="Generating AI compliances", data={"user_id": user_id})

    compliance_records = []
    total_processed = 0
    total_sections = len(sections)
    total_policies = 0

    for section in sections:
        section_name = section.get("section_name", "")
        section_title = section.get("section_title", "")
        policies = section.get("policies", [])
        total_policies += len(policies)
        for policy in policies:
            policy_title = policy.get("policy_title", "")
            for subpolicy in policy.get("subpolicies", []):
                subpolicy_id = subpolicy.get("subpolicy_id", "")
                subpolicy_title = subpolicy.get("subpolicy_title", "")
                subpolicy_description = subpolicy.get("subpolicy_description", "")
                control = subpolicy.get("control", "")
                # Include if we have title, description, or control (don't skip content-rich rows)
                if not subpolicy_title and not subpolicy_description and not control:
                    continue
                if not subpolicy_title:
                    subpolicy_title = subpolicy_description[:80] if subpolicy_description else (control[:80] if control else f"Subpolicy {subpolicy_id}")

                try:
                    print(f"[AI-POLICY] 🤖 Generating compliance via centralized AI: {subpolicy_title[:60]}...")
                    ai_compliances = service.run_task(
                        "policy.generate_subpolicy_compliances",
                        {
                            "subpolicy_id": subpolicy_id,
                            "subpolicy_title": subpolicy_title,
                            "subpolicy_description": subpolicy_description,
                            "control": control,
                        },
                    )
                except Exception as exc:
                    debug_print(f"[WARN] AI compliance generation failed for {subpolicy_title}: {exc}")
                    ai_compliances = []

                if not ai_compliances:
                    ai_compliances = [
                        {
                            "ComplianceTitle": subpolicy_title,
                            "ComplianceItemDescription": f"Fallback compliance for {subpolicy_title}",
                            "PossibleDamage": "",
                            "Criticality": "Medium",
                            "ComplianceType": "Automated",
                            "Status": "Generated",
                        }
                    ]

                subpolicy["compliances"] = []
                for ai_compliance in ai_compliances:
                    compliance_record = {
                        "SubPolicyId": subpolicy_id,
                        "SubPolicyTitle": subpolicy_title,
                        "SectionName": section_name,
                        "SectionTitle": section_title,
                        "PolicyTitle": policy_title,
                        "Status": ai_compliance.get("Status", "Generated"),
                        "CreatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "ComplianceType": ai_compliance.get("ComplianceType", "Automated"),
                        "Description": ai_compliance.get("ComplianceItemDescription", ""),
                        "Evidence": ai_compliance.get("Evidence", []),
                        "Notes": ai_compliance.get("Notes", f"AI-generated from {section_title} - {policy_title}"),
                        "Identifier": ai_compliance.get("Identifier", ""),
                        "ComplianceTitle": ai_compliance.get("ComplianceTitle", ""),
                        "ComplianceItemDescription": ai_compliance.get("ComplianceItemDescription", ""),
                        "Scope": ai_compliance.get("Scope", ""),
                        "Objective": ai_compliance.get("Objective", ""),
                        "BusinessUnitsCovered": ai_compliance.get("BusinessUnitsCovered", ""),
                        "Criticality": ai_compliance.get("Criticality", "Medium"),
                        "MandatoryOptional": ai_compliance.get("MandatoryOptional", "Mandatory"),
                        "ManualAutomatic": ai_compliance.get("ManualAutomatic", "Manual"),
                        "Impact": ai_compliance.get("Impact", 5),
                        "Probability": ai_compliance.get("Probability", 5),
                        "MaturityLevel": ai_compliance.get("MaturityLevel", "Developing"),
                        "Applicability": ai_compliance.get("Applicability", "Global"),
                        "PotentialRiskScenarios": ai_compliance.get("PotentialRiskScenarios", ""),
                        "RiskType": ai_compliance.get("RiskType", "Current"),
                        "RiskCategory": ai_compliance.get("RiskCategory", "Operational"),
                        "RiskBusinessImpact": ai_compliance.get("RiskBusinessImpact", ""),
                        "PossibleDamage": ai_compliance.get("PossibleDamage", ""),
                        "risk_details": ai_compliance.get("risk_details", {}),
                    }
                    subpolicy["compliances"].append(compliance_record)
                    compliance_records.append(compliance_record)
                    total_processed += 1

    checked_data.setdefault("metadata", {})
    checked_data["metadata"]["task_id"] = task_id
    checked_data["metadata"]["compliance_generation_timestamp"] = int(time.time())
    checked_data["metadata"]["compliance_generation_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
    checked_data["metadata"]["total_compliances"] = len(compliance_records)
    checked_data["metadata"]["ai_generated"] = True
    checked_data["metadata"]["governance_ready"] = True
    checked_data["compliances"] = compliance_records

    _write_json(checked_section_file, checked_data)
    job_service.update_job_status(
        task_id,
        status="compliances_generated",
        progress=85,
        message="AI compliances generated",
        data={"user_id": user_id, "total_compliances": len(compliance_records)},
    )

    return JsonResponse(
        {
            "success": True,
            "message": "AI-powered compliance records generated and saved to checked_section.json",
            "file_path": str(checked_section_file),
            "total_compliance_records": len(compliance_records),
            "total_subpolicies": total_processed,
            "total_compliances": len(compliance_records),
            "total_sections": total_sections,
            "total_policies": total_policies,
            "ai_generated": True,
            "status": "success",
        }
    )


def _persist_policy_draft(data: dict[str, Any], request=None, tenant_id=None):
    framework_data = data.get("framework", {})
    sections_data = data.get("sections", [])
    user_id = _resolve_user_id(data, request)
    created_by_name = _resolve_created_by_name(request, framework_data, user_id)
    actor_id = _resolve_actor_id(request, data)
    reviewer_id = _resolve_actor_id(None, {"reviewer_id": data.get("reviewer_id")}) or actor_id

    checked_data = load_import_draft(user_id)
    nested_compliances = _extract_nested_compliances(sections_data) or _extract_nested_compliances(checked_data.get("sections", []))
    task_id = data.get("task_id") or checked_data.get("metadata", {}).get("task_id") or f"upload_{user_id}"
    job_service = _get_job_service()
    job_service.update_job_status(task_id, status="saving", progress=90, message="Persisting governed policy records", data={"user_id": user_id})

    with transaction.atomic():
        framework = Framework.objects.create(
            FrameworkName=framework_data.get("FrameworkName", "Untitled Framework"),
            CurrentVersion=float(framework_data.get("CurrentVersion", 1.0) or 1.0),
            FrameworkDescription=framework_data.get("FrameworkDescription", ""),
            EffectiveDate=framework_data.get("EffectiveDate") or date.today(),
            CreatedByName=created_by_name,
            CreatedByDate=date.today(),
            Category=framework_data.get("Category", ""),
            Identifier=framework_data.get("Identifier", ""),
            StartDate=framework_data.get("StartDate") or date.today(),
            EndDate=framework_data.get("EndDate"),
            Status=framework_data.get("Status", "Under Review"),
            ActiveInactive=framework_data.get("ActiveInactive", "Active"),
            Reviewer=framework_data.get("Reviewer", ""),
            InternalExternal=framework_data.get("InternalExternal", "Internal"),
            tenant_id=tenant_id,
        )

        FrameworkVersion.objects.create(
            FrameworkId=framework,
            Version=framework.CurrentVersion,
            FrameworkName=framework.FrameworkName,
            CreatedBy=created_by_name,
            CreatedDate=date.today(),
        )

        FrameworkApproval.objects.create(
            FrameworkId=framework,
            ExtractedData={"framework": framework_data, "sections": sections_data},
            UserId=actor_id,
            ReviewerId=reviewer_id,
            Version=str(framework.CurrentVersion),
            ApprovedNot=None,
        )

        subpolicy_mapping: dict[str, SubPolicy] = {}
        total_policies = 0
        total_subpolicies = 0
        total_compliances = 0
        policy_ids = []

        for section in sections_data:
            for policy_data in section.get("policies", []):
                policy = Policy.objects.create(
                    FrameworkId=framework,
                    CurrentVersion=str(policy_data.get("CurrentVersion", "1.0")),
                    Status=policy_data.get("Status", "Under Review"),
                    PolicyDescription=policy_data.get("policy_description", ""),
                    PolicyName=policy_data.get("policy_title", "Untitled Policy"),
                    StartDate=policy_data.get("StartDate") or date.today(),
                    Department=policy_data.get("Department", ""),
                    CreatedByName=policy_data.get("CreatedByName") or created_by_name,
                    CreatedByDate=date.today(),
                    Applicability=policy_data.get("Applicability", ""),
                    Scope=policy_data.get("scope", ""),
                    Objective=policy_data.get("objective", ""),
                    Identifier=policy_data.get("policy_id", ""),
                    PermanentTemporary=policy_data.get("PermanentTemporary", "Permanent"),
                    ActiveInactive=policy_data.get("ActiveInactive", "Active"),
                    Reviewer=policy_data.get("Reviewer", ""),
                    PolicyType=policy_data.get("policy_type", ""),
                    PolicyCategory=policy_data.get("policy_category", ""),
                    PolicySubCategory=policy_data.get("policy_subcategory", ""),
                    tenant_id=tenant_id,
                )
                policy_ids.append(policy.PolicyId)
                total_policies += 1

                PolicyVersion.objects.create(
                    PolicyId=policy,
                    Version=policy.CurrentVersion,
                    PolicyName=policy.PolicyName,
                    CreatedBy=policy.CreatedByName or created_by_name,
                    CreatedDate=date.today(),
                    FrameworkId=framework,
                )

                PolicyApproval.objects.create(
                    Identifier=policy.Identifier or f"POL-{policy.PolicyId}",
                    ExtractedData=policy_data,
                    UserId=actor_id,
                    ReviewerId=reviewer_id,
                    Version=policy.CurrentVersion,
                    ApprovedNot=None,
                    PolicyId=policy,
                    FrameworkId=framework,
                )

                for subpolicy_data in policy_data.get("subpolicies", []):
                    subpolicy = SubPolicy.objects.create(
                        PolicyId=policy,
                        SubPolicyName=subpolicy_data.get("subpolicy_title", "Untitled SubPolicy"),
                        CreatedByName=subpolicy_data.get("CreatedByName") or created_by_name,
                        CreatedByDate=date.today(),
                        Identifier=subpolicy_data.get("subpolicy_id", ""),
                        Description=subpolicy_data.get("subpolicy_description", ""),
                        Status=subpolicy_data.get("Status", "Under Review"),
                        PermanentTemporary=subpolicy_data.get("PermanentTemporary", "Permanent"),
                        Control=subpolicy_data.get("control", ""),
                        FrameworkId=framework,
                        tenant_id=tenant_id,
                    )
                    subpolicy_mapping[subpolicy.Identifier] = subpolicy
                    total_subpolicies += 1

        for compliance_data in nested_compliances:
            subpolicy = subpolicy_mapping.get(compliance_data.get("SubPolicyId", ""))
            if not subpolicy:
                continue

            mitigation_value = compliance_data.get("mitigation", {})
            if not isinstance(mitigation_value, (dict, str)):
                mitigation_value = {}

            Compliance.objects.create(
                SubPolicy=subpolicy,
                ComplianceTitle=(compliance_data.get("ComplianceTitle", "Untitled Compliance") or "Untitled Compliance")[:145],
                ComplianceItemDescription=compliance_data.get("ComplianceItemDescription", ""),
                ComplianceType=compliance_data.get("ComplianceType", "Regulatory"),
                Scope=compliance_data.get("Scope", ""),
                Objective=compliance_data.get("Objective", ""),
                BusinessUnitsCovered=(compliance_data.get("BusinessUnitsCovered", "") or "")[:225],
                IsRisk=bool(compliance_data.get("IsRisk", 1)),
                PossibleDamage=compliance_data.get("PossibleDamage", ""),
                mitigation=mitigation_value,
                Criticality=compliance_data.get("Criticality", "Medium"),
                MandatoryOptional=compliance_data.get("MandatoryOptional", "Mandatory"),
                ManualAutomatic=compliance_data.get("ManualAutomatic", "Manual"),
                Impact=str(compliance_data.get("Impact", "5")),
                Probability=str(compliance_data.get("Probability", "5")),
                MaturityLevel=compliance_data.get("MaturityLevel", "Initial"),
                ActiveInactive=compliance_data.get("ActiveInactive", "Active"),
                PermanentTemporary=compliance_data.get("PermanentTemporary", "Permanent"),
                CreatedByName=(compliance_data.get("CreatedByName") or created_by_name)[:250],
                CreatedByDate=date.today(),
                ComplianceVersion=compliance_data.get("ComplianceVersion", "1.0"),
                Status=compliance_data.get("Status", "Under Review"),
                Identifier=(compliance_data.get("Identifier", "") or "")[:45],
                Applicability=(compliance_data.get("Applicability", "") or "")[:450],
                PotentialRiskScenarios=compliance_data.get("PotentialRiskScenarios", ""),
                RiskType=compliance_data.get("RiskType", "Current"),
                RiskCategory=(compliance_data.get("RiskCategory", "") or "")[:45],
                RiskBusinessImpact=(compliance_data.get("RiskBusinessImpact", "") or "")[:45],
                FrameworkId=framework,
                tenant_id=tenant_id,
            )
            total_compliances += 1

    job_service.update_job_status(
        task_id,
        status="completed",
        progress=100,
        message="Governed policy records saved",
        data={"framework_id": framework.FrameworkId, "policy_ids": policy_ids},
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Successfully saved governed AI-generated policy content",
            "framework_id": framework.FrameworkId,
            "framework_name": framework.FrameworkName,
            "policy_ids": policy_ids,
            "total_policies": total_policies,
            "total_subpolicies": total_subpolicies,
            "total_compliances": total_compliances,
            "governance": {
                "framework_version_created": True,
                "policy_versions_created": total_policies,
                "approvals_created": total_policies + 1,
                "tenant_id": tenant_id,
            },
        }
    )


def create_policy_version_from_ai_draft(payload: dict[str, Any], request=None):
    service = get_ai_service()
    return service.run_task("policy.suggest_policy_version_delta", payload)


def submit_policy_for_approval(payload: dict[str, Any], request=None):
    actor_id = _resolve_actor_id(request, payload)
    reviewer_id = payload.get("reviewer_id", actor_id)
    return {
        "submitted": True,
        "submitted_by": actor_id,
        "reviewer_id": reviewer_id,
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def save_checked_sections_json(request):
    if request.method == "GET":
        return JsonResponse({"message": "save-checked-sections-json endpoint is working", "method": "GET", "status": "success"})
    return save_selected_structure(_parse_request_json(request), request=request)


@csrf_exempt
@require_http_methods(["POST"])
def generate_compliances_for_checked_sections(request):
    return generate_selected_compliances(_parse_request_json(request), request=request)


@csrf_exempt
@require_http_methods(["GET"])
def get_checked_sections_with_compliance(request):
    user_id = request.GET.get("user_id", "1")
    checked_data = load_import_draft(user_id)
    return JsonResponse({"success": True, "data": checked_data, "message": "Successfully loaded checked sections data"}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def save_edited_framework_to_database(request):
    data = _parse_request_json(request)
    tenant_id = None
    try:
        tenant_id = get_tenant_id_from_request(request)
    except Exception:
        tenant_id = None
    return _persist_policy_draft(data, request=request, tenant_id=tenant_id)


@api_view(["POST"])
@permission_classes([PolicyCreatePermission])
@require_tenant
@tenant_filter
def save_policy_draft_governed(request):
    tenant_id = get_tenant_id_from_request(request)
    return _persist_policy_draft(_parse_request_json(request), request=request, tenant_id=tenant_id)


@api_view(["POST"])
@permission_classes([PolicyCreatePermission])
@require_tenant
@tenant_filter
def draft_policy_from_control_view(request):
    """
    Draft a policy, subpolicies, and compliances in a single optimized flow.

    This endpoint now uses the centralized preprocessing + generation helper:
    - Preprocesses the raw input text (control chars, whitespace, lemmatization, truncation).
    - Attaches preprocessing metadata and document_hash for caching.
    - Calls `policy.generate_policy_with_compliances` via `AIService.generate_policy_bundle_from_text`.
    """
    service = get_ai_service()
    payload = _parse_request_json(request) or {}

    # Accept either a direct `document_text` or fall back to older fields like `framework_controls` / `source_text`
    document_text = (
        payload.get("document_text")
        or payload.get("framework_controls")
        or payload.get("source_text")
        or ""
    )

    # Remove the raw document text from extra payload to avoid duplication in the task payload
    extra_payload = {k: v for k, v in payload.items() if k not in {"document_text", "framework_controls", "source_text"}}

    result = service.generate_policy_bundle_from_text(
        document_text=document_text,
        extra_payload=extra_payload,
        extra_metadata={"source": "draft_policy_from_control_view"},
    )
    return Response({"success": True, "data": result})


@api_view(["POST"])
@permission_classes([PolicyViewPermission])
@require_tenant
@tenant_filter
def generate_policy_gap_analysis_view(request):
    service = get_ai_service()
    result = service.run_task("policy.generate_policy_gap_analysis", _parse_request_json(request))
    return Response({"success": True, "data": result})


@api_view(["POST"])
@permission_classes([PolicyEditPermission])
@require_tenant
@tenant_filter
def review_policy_quality_view(request):
    service = get_ai_service()
    result = service.run_task("policy.review_policy_quality", _parse_request_json(request))
    return Response({"success": True, "data": result})


@api_view(["POST"])
@permission_classes([PolicyViewPermission])
@require_tenant
@tenant_filter
def explain_generated_output_view(request):
    service = get_ai_service()
    result = service.run_task("policy.explain_generated_output_with_evidence", _parse_request_json(request))
    return Response({"success": True, "data": result})