"""
RBAC Models for TPRM System

This module defines the RBAC model for the rbac_tprm table.
"""

from django.db import models
from django.utils import timezone


class RBACTPRM(models.Model):
    """
    RBAC model for TPRM (Third Party Risk Management) system
    Maps to the rbac_tprm table
    """
    
    # Primary Key
    rbac_id = models.AutoField(db_column='RBACId', primary_key=True)
    
    # MULTI-TENANCY: Link RBAC to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rbac_tprm_records', null=True, blank=True,
                               help_text="Tenant this RBAC record belongs to")
    
    # User Information
    user_id = models.IntegerField(db_column='UserId')
    username = models.CharField(db_column='UserName', max_length=255)
    role = models.CharField(db_column='Role', max_length=100)
    
    # RFP (Request for Proposal) Permissions
    create_rfp = models.BooleanField(db_column='CreateRFP', default=False)
    edit_rfp = models.BooleanField(db_column='EditRFP', default=False)
    view_rfp = models.BooleanField(db_column='ViewRFP', default=False)
    delete_rfp = models.BooleanField(db_column='DeleteRFP', default=False)
    clone_rfp = models.BooleanField(db_column='CloneRFP', default=False)
    submit_rfp_for_review = models.BooleanField(db_column='SubmitRFPForReview', default=False)
    approve_rfp = models.BooleanField(db_column='ApproveRFP', default=False)
    reject_rfp = models.BooleanField(db_column='RejectRFP', default=False)
    assign_rfp_reviewers = models.BooleanField(db_column='AssignRFPReviewers', default=False)
    view_rfp_approval_status = models.BooleanField(db_column='ViewRFPApprovalStatus', default=False)
    view_rfp_versions = models.BooleanField(db_column='ViewRFPVersions', default=False)
    create_rfp_version = models.BooleanField(db_column='CreateRFPVersion', default=False)
    edit_rfp_version = models.BooleanField(db_column='EditRFPVersion', default=False)
    view_rfp_version = models.BooleanField(db_column='ViewRFPVersion', default=False)
    
    # Evaluation Criteria Permissions
    create_evaluation_criteria = models.BooleanField(db_column='CreateEvaluationCriteria', default=False)
    edit_evaluation_criteria = models.BooleanField(db_column='EditEvaluationCriteria', default=False)
    delete_evaluation_criteria = models.BooleanField(db_column='DeleteEvaluationCriteria', default=False)
    
    # Vendor Management Permissions
    select_vendors_for_rfp = models.BooleanField(db_column='SelectVendorsForRFP', default=False)
    invite_vendors_for_rfp = models.BooleanField(db_column='InviteVendorsForRFP', default=False)
    track_rfp_invitations = models.BooleanField(db_column='TrackRFPInvitations', default=False)
    
    # Document Management Permissions
    upload_documents_for_rfp = models.BooleanField(db_column='UploadDocumentsForRFP', default=False)
    download_rfp_documents = models.BooleanField(db_column='DownloadRFPDocuments', default=False)
    preview_rfp_documents = models.BooleanField(db_column='PreviewRFPDocuments', default=False)
    validate_rfp_documents = models.BooleanField(db_column='ValidateRFPDocuments', default=False)
    scan_rfp_files_for_virus = models.BooleanField(db_column='ScanRFPFilesForVirus', default=False)
    
    # RFP Response Permissions
    view_rfp_responses = models.BooleanField(db_column='ViewRFPResponses', default=False)
    submit_rfp_response = models.BooleanField(db_column='SubmitRFPResponse', default=False)
    withdraw_rfp_response = models.BooleanField(db_column='WithdrawRFPResponse', default=False)
    
    # RFP Evaluation Permissions
    auto_screen_rfp = models.BooleanField(db_column='AutoScreenRFP', default=False)
    assign_rfp_evaluators = models.BooleanField(db_column='AssignRFPEvaluators', default=False)
    score_rfp_response = models.BooleanField(db_column='ScoreRFPResponse', default=False)
    view_rfp_response_scores = models.BooleanField(db_column='ViewRFPResponseScores', default=False)
    rank_vendors_for_rfp = models.BooleanField(db_column='RankVendorsForRFP', default=False)
    finalize_rfp_evaluation = models.BooleanField(db_column='FinalizeRFPEvaluation', default=False)
    send_rfp_award_notification = models.BooleanField(db_column='SendRFPAwardNotification', default=False)
    
    # Analytics and Reporting Permissions
    view_rfp_analytics = models.BooleanField(db_column='ViewRFPAnalytics', default=False)
    generate_rfp_reports = models.BooleanField(db_column='GenerateRFPReports', default=False)
    download_rfp_report = models.BooleanField(db_column='DownloadRFPReport', default=False)
    
    # Workflow and Lifecycle Permissions
    manage_rfp_lifecycle = models.BooleanField(db_column='ManageRFPLifecycle', default=False)
    trigger_rfp_workflow = models.BooleanField(db_column='TriggerRFPWorkflow', default=False)
    escalate_rfp_workflow = models.BooleanField(db_column='EscalateRFPWorkflow', default=False)
    generate_rfp_tokens = models.BooleanField(db_column='GenerateRFPTokens', default=False)
    validate_rfp_access = models.BooleanField(db_column='ValidateRFPAccess', default=False)
    view_rfp_audit_trail = models.BooleanField(db_column='ViewRFPAuditTrail', default=False)
    
    # Communication Permissions
    send_rfp_notifications = models.BooleanField(db_column='SendRFPNotifications', default=False)
    broadcast_rfp_communications = models.BooleanField(db_column='BroadcastRFPCommunications', default=False)
    clarify_rfp_communications = models.BooleanField(db_column='ClarifyRFPCommunications', default=False)
    amend_rfp_communications = models.BooleanField(db_column='AmendRFPCommunications', default=False)
    
    # Vendor Management from RFP
    create_rfp_vendor_from_rfp = models.BooleanField(db_column='CreateRFPVendorFromRFP', default=False)
    match_rfp_vendor = models.BooleanField(db_column='MatchRFPVendor', default=False)
    
    # System Health and Validation
    perform_rfp_health_check = models.BooleanField(db_column='PerformRFPHealthCheck', default=False)
    validate_rfp_data = models.BooleanField(db_column='ValidateRFPData', default=False)
    track_rfp_activity_log = models.BooleanField(db_column='TrackRFPActivityLog', default=False)
    
    # Contract Management Permissions
    list_contracts = models.BooleanField(db_column='ListContracts', default=False)
    create_contract = models.BooleanField(db_column='CreateContract', default=False)
    update_contract = models.BooleanField(db_column='UpdateContract', default=False)
    delete_contract = models.BooleanField(db_column='DeleteContract', default=False)
    approve_contract = models.BooleanField(db_column='ApproveContract', default=False)
    reject_contract = models.BooleanField(db_column='RejectContract', default=False)
    
    # Contract Terms Permissions
    create_contract_term = models.BooleanField(db_column='CreateContractTerm', default=False)
    list_contract_terms = models.BooleanField(db_column='ListContractTerms', default=False)
    update_contract_term = models.BooleanField(db_column='UpdateContractTerm', default=False)
    delete_contract_term = models.BooleanField(db_column='DeleteContractTerm', default=False)
    
    # Contract Renewal Permissions
    list_contract_renewals = models.BooleanField(db_column='ListContractRenewals', default=False)
    create_contract_renewal = models.BooleanField(db_column='CreateContractRenewal', default=False)
    approve_contract_renewal = models.BooleanField(db_column='ApproveContractRenewal', default=False)
    reject_contract_renewal = models.BooleanField(db_column='RejectContractRenewal', default=False)
    
    # Contract Analysis Permissions
    create_contract_audit = models.BooleanField(db_column='CreateContractAudit', default=False)
    perform_contract_audit = models.BooleanField(db_column='PerformContractAudit', default=False)
    trigger_ocr = models.BooleanField(db_column='TriggerOCR', default=False)
    get_nlp_clauses = models.BooleanField(db_column='GetNLPClauses', default=False)
    contract_search = models.BooleanField(db_column='ContractSearch', default=False)
    get_contract_history = models.BooleanField(db_column='GetContractHistory', default=False)
    compare_contract_version = models.BooleanField(db_column='CompareContractVersion', default=False)
    download_contract_document = models.BooleanField(db_column='DownloadContractDocument', default=False)
    contract_dashboard = models.BooleanField(db_column='ContractDashboard', default=False)
    validate_contract_data = models.BooleanField(db_column='ValidateContractData', default=False)
    
    # BCP/DRP Strategy Permissions
    create_bcp_drp_strategy_and_plans = models.BooleanField(db_column='CreateBCPDRPStrategyAndPlans', default=False)
    view_plans_and_documents = models.BooleanField(db_column='ViewPlansAndDocuments', default=False)
    assign_plans_for_evaluation = models.BooleanField(db_column='AssignPlansForEvaluation', default=False)
    approve_or_reject_plan_evaluations = models.BooleanField(db_column='ApproveOrRejectPlanEvaluations', default=False)
    ocr_extraction_and_review = models.BooleanField(db_column='OCRExtractionAndReview', default=False)
    
    # Questionnaire Permissions
    create_questionnaire_for_testing = models.BooleanField(db_column='CreateQuestionnaireForTesting', default=False)
    review_questionnaire_answers = models.BooleanField(db_column='ReviewQuestionnaireAnswers', default=False)
    final_approval_of_plan = models.BooleanField(db_column='FinalApprovalOfPlan', default=False)
    create_questionnaire = models.BooleanField(db_column='CreateQuestionnaire', default=False)
    assign_questionnaires_for_review = models.BooleanField(db_column='AssignQuestionnairesForReview', default=False)
    view_all_questionnaires = models.BooleanField(db_column='ViewAllQuestionnaires', default=False)
    
    # System Configuration Permissions
    configure_system_settings = models.BooleanField(db_column='ConfigureSystemSettings', default=False)
    configure_questionnaire_settings = models.BooleanField(db_column='ConfigureQuestionnaireSettings', default=False)
    create_update_user_roles = models.BooleanField(db_column='CreateUpdateUserRoles', default=False)
    manage_document_access_controls = models.BooleanField(db_column='ManageDocumentAccessControls', default=False)
    
    # Compliance and Audit Permissions
    generate_compliance_audit_reports = models.BooleanField(db_column='GenerateComplianceAuditReports', default=False)
    view_document_status_history = models.BooleanField(db_column='ViewDocumentStatusHistory', default=False)
    request_document_revisions_from_vendor = models.BooleanField(db_column='RequestDocumentRevisionsFromVendor', default=False)
    view_vendor_submitted_documents = models.BooleanField(db_column='ViewVendorSubmittedDocuments', default=False)
    view_bcp_drp_plan_status = models.BooleanField(db_column='ViewBCPDRPPlanStatus', default=False)
    
    # Vendor Coordination and Evaluation
    coordinate_vendor_feedback = models.BooleanField(db_column='CoordinateVendorFeedback', default=False)
    evaluate_plan_based_on_criteria = models.BooleanField(db_column='EvaluatePlanBasedOnCriteria', default=False)
    submit_evaluation_feedback = models.BooleanField(db_column='SubmitEvaluationFeedback', default=False)
    view_vendor_contracts = models.BooleanField(db_column='ViewVendorContracts', default=False)
    create_modify_contracts = models.BooleanField(db_column='CreateModifyContracts', default=False)
    
    # Vendor Management Permissions
    view_available_vendors = models.BooleanField(db_column='ViewAvailableVendors', default=False)
    add_vendor_to_bcp_drp_strategy = models.BooleanField(db_column='AddVendorToBCPDRPStrategy', default=False)
    assess_vendor_risk = models.BooleanField(db_column='AssessVendorRisk', default=False)
    view_vendor_risk_scores = models.BooleanField(db_column='ViewVendorRiskScores', default=False)
    
    # Risk Management Permissions
    identify_risks_in_plans = models.BooleanField(db_column='IdentifyRisksInPlans', default=False)
    view_identified_risks = models.BooleanField(db_column='ViewIdentifiedRisks', default=False)
    manage_risk_mitigation_plans = models.BooleanField(db_column='ManageRiskMitigationPlans', default=False)
    view_risk_mitigation_status = models.BooleanField(db_column='ViewRiskMitigationStatus', default=False)
    
    # Compliance and Regulatory Permissions
    view_compliance_status_of_plans = models.BooleanField(db_column='ViewComplianceStatusOfPlans', default=False)
    audit_compliance_of_documents = models.BooleanField(db_column='AuditComplianceOfDocuments', default=False)
    configure_document_security_settings = models.BooleanField(db_column='ConfigureDocumentSecuritySettings', default=False)
    view_document_access_logs = models.BooleanField(db_column='ViewDocumentAccessLogs', default=False)
    review_regulatory_compliance = models.BooleanField(db_column='ReviewRegulatoryCompliance', default=False)
    audit_compliance_against_regulations = models.BooleanField(db_column='AuditComplianceAgainstRegulations', default=False)
    
    # Legal and Contractual Permissions
    review_and_approve_legal_aspects_of_plans = models.BooleanField(db_column='ReviewAndApproveLegalAspectsOfPlans', default=False)
    generate_legal_compliance_reports = models.BooleanField(db_column='GenerateLegalComplianceReports', default=False)
    view_contractual_obligations = models.BooleanField(db_column='ViewContractualObligations', default=False)
    
    # Audit and Documentation Permissions
    audit_plan_documentation = models.BooleanField(db_column='AuditPlanDocumentation', default=False)
    view_audit_logs = models.BooleanField(db_column='ViewAuditLogs', default=False)
    generate_internal_audit_reports = models.BooleanField(db_column='GenerateInternalAuditReports', default=False)
    conduct_external_compliance_audit = models.BooleanField(db_column='ConductExternalComplianceAudit', default=False)
    generate_external_audit_reports = models.BooleanField(db_column='GenerateExternalAuditReports', default=False)
    review_external_auditor_comments = models.BooleanField(db_column='ReviewExternalAuditorComments', default=False)
    audit_compliance_of_plans = models.BooleanField(db_column='AuditComplianceOfPlans', default=False)
    view_compliance_audit_results = models.BooleanField(db_column='ViewComplianceAuditResults', default=False)
    generate_compliance_reports = models.BooleanField(db_column='GenerateComplianceReports', default=False)
    
    # System Management Permissions
    manage_server_resources_for_bcp_drp = models.BooleanField(db_column='ManageServerResourcesForBCPDRP', default=False)
    monitor_system_health = models.BooleanField(db_column='MonitorSystemHealth', default=False)
    backup_system_configuration = models.BooleanField(db_column='BackupSystemConfiguration', default=False)
    
    # Incident Response Permissions
    view_incident_response_plans = models.BooleanField(db_column='ViewIncidentResponsePlans', default=False)
    create_incident_response_plans = models.BooleanField(db_column='CreateIncidentResponsePlans', default=False)
    update_incident_response_plans = models.BooleanField(db_column='UpdateIncidentResponsePlans', default=False)
    
    # Integration Permissions
    integrate_bcp_drp_with_external_systems = models.BooleanField(db_column='IntegrateBCPDRPWithExternalSystems', default=False)
    manage_integration_settings = models.BooleanField(db_column='ManageIntegrationSettings', default=False)
    
    # Vendor Management (General)
    view_vendors = models.BooleanField(db_column='ViewVendors', default=False)
    create_vendor = models.BooleanField(db_column='CreateVendor', default=False)
    update_vendor = models.BooleanField(db_column='UpdateVendor', default=False)
    delete_vendor = models.BooleanField(db_column='DeleteVendor', default=False)
    submit_vendor_for_approval = models.BooleanField(db_column='SubmitVendorForApproval', default=False)
    approve_reject_vendor = models.BooleanField(db_column='ApproveRejectVendor', default=False)
    
    # Document and Contact Management
    view_contacts_documents = models.BooleanField(db_column='ViewContactsDocuments', default=False)
    add_update_contacts_documents = models.BooleanField(db_column='AddUpdateContactsDocuments', default=False)
    approve_documents = models.BooleanField(db_column='ApproveDocuments', default=False)
    
    # Risk Assessment and Screening
    view_risk_profile = models.BooleanField(db_column='ViewRiskProfile', default=False)
    view_lifecycle_history = models.BooleanField(db_column='ViewLifecycleHistory', default=False)
    manage_questionnaires = models.BooleanField(db_column='ManageQuestionnaires', default=False)
    view_questionnaires = models.BooleanField(db_column='ViewQuestionnaires', default=False)
    assign_questionnaires = models.BooleanField(db_column='AssignQuestionnaires', default=False)
    submit_questionnaire_responses = models.BooleanField(db_column='SubmitQuestionnaireResponses', default=False)
    review_approve_responses = models.BooleanField(db_column='ReviewApproveResponses', default=False)
    view_risk_assessments = models.BooleanField(db_column='ViewRiskAssessments', default=False)
    create_risk_assessments = models.BooleanField(db_column='CreateRiskAssessments', default=False)
    recalculate_risk_scores = models.BooleanField(db_column='RecalculateRiskScores', default=False)
    
    # Screening and Integration
    initiate_screening = models.BooleanField(db_column='InitiateScreening', default=False)
    resolve_screening_matches = models.BooleanField(db_column='ResolveScreeningMatches', default=False)
    view_screening_results = models.BooleanField(db_column='ViewScreeningResults', default=False)
    access_integration_mappings = models.BooleanField(db_column='AccessIntegrationMappings', default=False)
    initiate_sync_with_finacle = models.BooleanField(db_column='InitiateSyncWithFinacle', default=False)
    
    # System Health and Performance
    perform_health_check = models.BooleanField(db_column='PerformHealthCheck', default=False)
    test_external_connections = models.BooleanField(db_column='TestExternalConnections', default=False)
    
    # SLA Management
    view_sla = models.BooleanField(db_column='ViewSLA', default=False)
    create_sla = models.BooleanField(db_column='CreateSLA', default=False)
    update_sla = models.BooleanField(db_column='UpdateSLA', default=False)
    delete_sla = models.BooleanField(db_column='DeleteSLA', default=False)
    view_performance = models.BooleanField(db_column='ViewPerformance', default=False)
    create_performance = models.BooleanField(db_column='CreatePerformance', default=False)
    
    # Bulk Operations and Alerts
    bulk_upload = models.BooleanField(db_column='BulkUpload', default=False)
    view_alerts = models.BooleanField(db_column='ViewAlerts', default=False)
    acknowledge_resolve_alerts = models.BooleanField(db_column='AcknowledgeResolveAlerts', default=False)
    view_dashboard_trend = models.BooleanField(db_column='ViewDashboardTrend', default=False)
    activate_deactivate_sla = models.BooleanField(db_column='ActivateDeactivateSLA', default=False)
    
    # Timestamps
    created_at = models.DateTimeField(db_column='CreatedAt', default=timezone.now)
    updated_at = models.DateTimeField(db_column='UpdatedAt', auto_now=True)
    is_active = models.CharField(db_column='IsActive', max_length=1, default='Y')
    
    class Meta:
        db_table = 'rbac_tprm'
        managed = False  # Table already exists in database
        verbose_name = 'RBAC TPRM Permission'
        verbose_name_plural = 'RBAC TPRM Permissions'
    
    def __str__(self):
        return f"{self.username} - {self.role}"
    
    @property
    def has_admin_access(self):
        """Check if user has admin-level access"""
        return self.role in ['Administrator', 'System Admin', 'Super User']
    
    @property
    def has_rfp_access(self):
        """Check if user has any RFP-related permissions"""
        return any([
            self.create_rfp, self.edit_rfp, self.view_rfp, self.delete_rfp,
            self.clone_rfp, self.submit_rfp_for_review, self.approve_rfp,
            self.reject_rfp, self.assign_rfp_reviewers
        ])
    
    @property
    def has_contract_access(self):
        """Check if user has any contract-related permissions"""
        return any([
            self.list_contracts, self.create_contract, self.update_contract,
            self.delete_contract, self.approve_contract, self.reject_contract
        ])
    
    @property
    def has_vendor_access(self):
        """Check if user has any vendor-related permissions"""
        return any([
            self.view_vendors, self.create_vendor, self.update_vendor,
            self.delete_vendor, self.submit_vendor_for_approval,
            self.approve_reject_vendor
        ])
    
    @property
    def has_risk_access(self):
        """Check if user has any risk-related permissions"""
        return any([
            self.assess_vendor_risk, self.view_vendor_risk_scores,
            self.identify_risks_in_plans, self.view_identified_risks,
            self.manage_risk_mitigation_plans
        ])
    
    @property
    def has_compliance_access(self):
        """Check if user has any compliance-related permissions"""
        return any([
            self.generate_compliance_audit_reports, self.review_regulatory_compliance,
            self.audit_compliance_against_regulations, self.generate_legal_compliance_reports
        ])


class AccessRequestTPRM(models.Model):
    """
    Access Request model for TPRM system
    Tracks user requests for access permissions that require admin approval
    """
    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
   
    id = models.AutoField(primary_key=True)
    
    # MULTI-TENANCY: Link access request to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='access_requests_tprm', null=True, blank=True,
                               help_text="Tenant this access request belongs to")
    
    user_id = models.IntegerField(db_column='user_id')
    requested_url = models.CharField(max_length=500, db_column='requested_url', null=True, blank=True)
    requested_feature = models.CharField(max_length=255, db_column='requested_feature', null=True, blank=True)
    required_permission = models.CharField(max_length=255, db_column='required_permission', null=True, blank=True)
    requested_role = models.CharField(max_length=100, db_column='requested_role', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED', db_column='status')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    approved_by = models.IntegerField(null=True, blank=True, db_column='approved_by')
    audit_trail = models.JSONField(null=True, blank=True, db_column='audit_trail', default=dict)
    message = models.TextField(null=True, blank=True, db_column='message')
   
    class Meta:
        app_label = 'tprm_rbac'
        db_table = 'AccessRequestTPRM'
        ordering = ['-created_at']
        verbose_name = 'TPRM Access Request'
        verbose_name_plural = 'TPRM Access Requests'
        indexes = [
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['status']),
        ]
   
    def __str__(self):
        return f"TPRM Access Request {self.id} by User {self.user_id} - {self.status}"