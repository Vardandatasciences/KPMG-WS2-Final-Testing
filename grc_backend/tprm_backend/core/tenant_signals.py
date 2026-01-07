"""
Django Signals for Automatic Tenant ID Assignment

This module uses Django signals to automatically set tenant_id when creating
model instances, so you don't need to manually set it in every view.
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .tenant_context import get_current_tenant


# Import RFP models
try:
    from tprm_backend.rfp.models import (
        RFP, RFPEvaluationCriteria, FileStorage, S3Files,
        RFPEvaluationScore, RFPEvaluatorAssignment, RFPCommittee,
        RFPFinalEvaluation, RFPVersions, RFPChangeRequests,
        RFPVersionComparisons, RFPUnmatchedVendor, VendorInvitation,
        RFPVendorSelection, RFPResponse, RFPAwardNotification,
        RFPTypeCustomFields
    )
    RFP_MODELS = [
        RFP, RFPEvaluationCriteria, FileStorage, S3Files,
        RFPEvaluationScore, RFPEvaluatorAssignment, RFPCommittee,
        RFPFinalEvaluation, RFPVersions, RFPChangeRequests,
        RFPVersionComparisons, RFPUnmatchedVendor, VendorInvitation,
        RFPVendorSelection, RFPResponse, RFPAwardNotification,
        RFPTypeCustomFields
    ]
except ImportError:
    RFP_MODELS = []


# Import RFP Approval models
try:
    from tprm_backend.rfp_approval.models import (
        ApprovalWorkflows, ApprovalRequests, ApprovalStages,
        ApprovalComments, ApprovalRequestVersions
    )
    RFP_APPROVAL_MODELS = [
        ApprovalWorkflows, ApprovalRequests, ApprovalStages,
        ApprovalComments, ApprovalRequestVersions
    ]
except ImportError:
    RFP_APPROVAL_MODELS = []


# Import Contracts models
try:
    from tprm_backend.contracts.models import (
        Vendor, VendorContract, ContractTerm, ContractClause,
        VendorContact, ContractAmendment, ContractRenewal, ContractApproval
    )
    CONTRACTS_MODELS = [
        Vendor, VendorContract, ContractTerm, ContractClause,
        VendorContact, ContractAmendment, ContractRenewal, ContractApproval
    ]
except ImportError:
    CONTRACTS_MODELS = []


# Import BCP/DRP models
try:
    from tprm_backend.bcpdrp.models import (
        Dropdown, Plan, BcpDetails, DrpDetails, Evaluation,
        Questionnaire, TestQuestion, TestAssignmentResponse,
        Approval, QuestionnaireTemplate
    )
    BCPDRP_MODELS = [
        Dropdown, Plan, BcpDetails, DrpDetails, Evaluation,
        Questionnaire, TestQuestion, TestAssignmentResponse,
        Approval, QuestionnaireTemplate
    ]
except ImportError:
    BCPDRP_MODELS = []


# Import Audits models
try:
    from tprm_backend.audits.models import (
        Audit, StaticQuestionnaire, AuditVersion,
        AuditFinding, AuditReport
    )
    AUDITS_MODELS = [
        Audit, StaticQuestionnaire, AuditVersion,
        AuditFinding, AuditReport
    ]
except ImportError:
    AUDITS_MODELS = []


# Import Compliance models
try:
    from tprm_backend.compliance.models import ComplianceMapping
    COMPLIANCE_MODELS = [ComplianceMapping]
except ImportError:
    COMPLIANCE_MODELS = []


# Import Risk Analysis models
try:
    from tprm_backend.risk_analysis.models import Risk
    RISK_ANALYSIS_MODELS = [Risk]
except ImportError:
    RISK_ANALYSIS_MODELS = []


# Import SLAs models
try:
    from tprm_backend.slas.models import VendorSLA, SLAMetric, SLADocument
    SLAS_MODELS = [VendorSLA, SLAMetric, SLADocument]
except ImportError:
    SLAS_MODELS = []


# Combine all tenant-aware models
TENANT_AWARE_MODELS = (
    RFP_MODELS +
    RFP_APPROVAL_MODELS +
    CONTRACTS_MODELS +
    BCPDRP_MODELS +
    AUDITS_MODELS +
    COMPLIANCE_MODELS +
    RISK_ANALYSIS_MODELS +
    SLAS_MODELS
)


@receiver(pre_save)
def auto_set_tenant(sender, instance, **kwargs):
    """
    Automatically set tenant_id when creating new records
    
    This signal fires before any model is saved. It checks if:
    1. The model has a 'tenant' field
    2. The tenant is not already set
    3. This is a new record (pk is None)
    4. There's a current tenant in context
    
    If all conditions are met, it automatically sets the tenant.
    """
    # Only process models that have tenant field
    if not hasattr(instance, 'tenant'):
        return
    
    # Only set tenant if:
    # 1. tenant is not already set
    # 2. This is a new record (pk is None)
    if instance.tenant is None and instance.pk is None:
        tenant_id = get_current_tenant()
        
        if tenant_id:
            try:
                from .models import Tenant
                tenant = Tenant.objects.get(tenant_id=tenant_id)
                instance.tenant = tenant
            except Tenant.DoesNotExist:
                pass  # Tenant not found, skip auto-assignment
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"[Tenant Signals] Error auto-setting tenant for {sender.__name__}: {e}")

