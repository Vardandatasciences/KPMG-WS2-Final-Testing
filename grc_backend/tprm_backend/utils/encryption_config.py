"""
TPRM Encryption Configuration
Defines which fields should be encrypted for each TPRM model.

Based on GRC encryption patterns, this configuration specifies sensitive fields
that contain personally identifiable information (PII), financial data, or other
confidential information that should be encrypted at rest.
"""

# Configuration: Map model name to list of field names that should be encrypted
TPRM_ENCRYPTED_FIELDS_CONFIG = {
    # ========== User Models ==========
    'User': [
        'email',
        'phone',
        'first_name',
        'last_name',
        'department',
        'position',
    ],
    
    'UserProfile': [
        'bio',
    ],
    
    'UserSession': [
        'session_key',
        'ip_address',
        'user_agent',
    ],
    
    # ========== Vendor Models ==========
    'Vendor': [
        'company_name',
        'legal_name',
        'tax_id',
        'duns_number',
        'website',
        'headquarters_address',
        'description',
    ],
    
    'VendorCategory': [
        'name',
        'description',
    ],
    
    'VendorRiskAssessment': [
        'assessment_factors',  # JSON field with sensitive assessment data
        'mitigation_actions',  # JSON field with mitigation details
    ],
    
    'VendorDocument': [
        'title',
        'description',
    ],
    
    'VendorContact': [
        'name',
        'title',
        'email',
        'phone',
        'mobile',
    ],
    
    'VendorFinancial': [
        'credit_rating',
    ],
    
    'VendorPerformance': [
        'performance_data',  # JSON field
    ],
    
    'VendorIncident': [
        'title',
        'description',
        'impact_assessment',
        'root_cause',
        'resolution_steps',
        'lessons_learned',
    ],
    
    # ========== Contract Models ==========
    'Contract': [
        'contract_name',
        'contract_number',
        'description',
        'vendor_legal_name',
        'signatory_name',
        'signatory_title',
        'signatory_email',
        'terms_and_conditions',
        'special_clauses',
        'payment_terms',
        'delivery_terms',
        'confidentiality_clause',
        'data_protection_clause',
        'intellectual_property_clause',
        'dispute_resolution_clause',
        'force_majeure_clause',
        'renewal_notice_period',
        'exit_strategy',
        'performance_guarantees',
    ],
    
    'ContractAmendment': [
        'amendment_title',
        'amendment_description',
        'changes_summary',
        'justification',
    ],
    
    'ContractDocument': [
        'document_name',
        'document_description',
    ],
    
    'ContractReview': [
        'review_comments',
        'risk_findings',
        'recommendations',
    ],
    
    'ContractApproval': [
        'comments',
        'rejection_reason',
    ],
    
    # ========== SLA Models ==========
    'VendorSLA': [
        'sla_name',
        'business_service_impacted',
        'measurement_methodology',
        'exclusions',
        'force_majeure_clauses',
        'audit_requirements',
    ],
    
    'SLAMetric': [
        'metric_name',
        'description',
        'calculation_method',
    ],
    
    'SLAPerformance': [
        'comments',
        'incident_details',
        'resolution_details',
    ],
    
    'SLAViolation': [
        'violation_description',
        'impact_description',
        'root_cause_analysis',
        'corrective_actions',
    ],
    
    'SLAReview': [
        'review_summary',
        'findings',
        'recommendations',
        'action_items',
    ],
    
    # ========== RFP Models ==========
    'RFP': [
        'rfp_title',
        'description',
        'rfp_number',
        'geographical_scope',
        'award_justification',
    ],
    
    'RFPSection': [
        'section_title',
        'section_content',
        'evaluation_criteria',
    ],
    
    'RFPQuestion': [
        'question_text',
        'help_text',
    ],
    
    'RFPResponse': [
        'response_text',
        'notes',
    ],
    
    'RFPSubmission': [
        'proposal_summary',
        'technical_approach',
        'pricing_details',
        'team_composition',
        'references',
    ],
    
    'RFPEvaluation': [
        'evaluator_comments',
        'strengths',
        'weaknesses',
        'recommendations',
    ],
    
    'RFPAward': [
        'justification',
        'decision_notes',
    ],
    
    # ========== Audit Models ==========
    'AuditLog': [
        'entity_name',
        'ip_address',
        'user_agent',
    ],
    
    'ContractAudit': [
        'audit_title',
        'audit_scope',
        'findings',
        'recommendations',
        'action_plan',
    ],
    
    'ContractAuditFinding': [
        'finding_description',
        'evidence',
        'recommendation',
        'management_response',
    ],
    
    # ========== Core Models ==========
    'NotificationTemplate': [
        'subject',
        'body',
    ],
    
    'FileUpload': [
        'original_filename',
    ],
    
    'Dashboard': [
        'name',
        'description',
    ],
    
    'Report': [
        'name',
        'description',
    ],
    
    'ReportExecution': [
        'error_message',
    ],
    
    'Integration': [
        'name',
        'configuration',  # JSON field - may contain API keys/tokens
    ],
    
    # ========== Risk Analysis Models ==========
    'VendorRisk': [
        'risk_title',
        'risk_description',
        'impact_description',
        'mitigation_plan',
        'contingency_plan',
    ],
    
    'RiskAssessment': [
        'assessment_title',
        'assessment_summary',
        'findings',
        'recommendations',
    ],
    
    'RiskMitigation': [
        'mitigation_description',
        'implementation_plan',
        'success_criteria',
    ],
    
    # ========== Compliance Models ==========
    'ComplianceRequirement': [
        'requirement_title',
        'requirement_description',
        'compliance_evidence',
    ],
    
    'ComplianceCheck': [
        'check_description',
        'findings',
        'recommendations',
    ],
    
    # ========== Performance Models ==========
    'PerformanceMetric': [
        'metric_name',
        'description',
        'calculation_formula',
    ],
    
    'PerformanceReport': [
        'report_title',
        'executive_summary',
        'detailed_findings',
        'recommendations',
    ],
    
    # ========== Notification Models ==========
    'Notification': [
        'subject',
        'message',
        'recipient_email',
    ],
    
    'NotificationLog': [
        'recipient',
        'content',
        'error_message',
    ],
    
    # ========== BCP/DRP Models ==========
    'Plan': [
        'strategy_name',
        'plan_name',
        'plan_scope',
        'rejection_reason',
        'file_uri',
    ],
    
    'BcpDetails': [
        'purpose_scope',
        'risk_assessment_summary',
        'bia_summary',
        'communication_plan_internal',
        'communication_plan_bank',
        'training_testing_schedule',
        'maintenance_review_cycle',
    ],
    
    'DrpDetails': [
        'purpose_scope',
        'disaster_declaration_process',
        'data_backup_strategy',
        'recovery_site_details',
        'failover_procedures',
        'failback_procedures',
        'network_recovery_steps',
        'testing_validation_schedule',
        'maintenance_review_cycle',
    ],
    
    'Evaluation': [
        'evaluator_comments',
    ],
    
    'Questionnaire': [
        'title',
        'description',
        'reviewer_comment',
    ],
    
    'Question': [
        'question_text',
    ],
    
    'TestAssignmentsResponses': [
        'owner_comment',
        'answer_text',
        'reason_comment',
        'evidence_uri',
    ],
    
    'BcpDrpApprovals': [
        'workflow_name',
        'assigner_name',
        'assignee_name',
        'comment_text',
    ],
    
    'Users': [
        'user_name',
        'email',
        'first_name',
        'last_name',
        'session_token',
        'license_key',
    ],
    
    'QuestionnaireTemplate': [
        'template_name',
        'template_description',
    ],
    
    'BusinessContinuityPlan': [
        'plan_title',
        'plan_description',
        'recovery_procedures',
        'contact_information',
    ],
    
    'DisasterRecoveryPlan': [
        'plan_title',
        'plan_description',
        'recovery_steps',
        'contact_list',
    ],
    
    # ========== RBAC Models ==========
    'Role': [
        'role_name',
        'description',
    ],
    
    'Permission': [
        'permission_name',
        'description',
    ],
    
    # ========== Analytics Models ==========
    'AnalyticsReport': [
        'report_title',
        'report_summary',
        'insights',
    ],
    
    # ========== Quick Access Models ==========
    'QuickLink': [
        'link_name',
        'link_url',
        'description',
    ],
    
    # ========== Admin Access Models ==========
    'AdminAction': [
        'action_description',
        'ip_address',
        'user_agent',
    ],
    
    # ========== MFA Models ==========
    'MFAToken': [
        'token',
        'backup_codes',
    ],
    
    'MFALog': [
        'ip_address',
        'user_agent',
    ],
    
    # ========== MFA Auth Models (CRITICAL) ==========
    'MfaEmailChallenge': [
        'ip_address',
        'user_agent',
    ],
    
    'MfaAuditLog': [
        'ip_address',
        'user_agent',
    ],
    
    # ========== Vendor Core Models ==========
    'Vendors': [
        'company_name',
        'legal_name',
        'tax_id',
        'duns_number',
        'website',
        'headquarters_address',
        'description',
    ],
    
    'VendorContacts': [
        'first_name',
        'last_name',
        'email',
        'phone',
        'mobile',
        'designation',
    ],
    
    'VendorDocuments': [
        'document_name',
        'file_path',
    ],
    
    'TempVendor': [
        'company_name',
        'legal_name',
        'tax_id',
        'headquarters_address',
    ],
    
    'ExternalScreeningResult': [
        'review_comments',
    ],
    
    'ScreeningMatch': [
        'resolution_notes',
    ],
    
    # ========== Audit Models ==========
    'Audit': [
        'title',
        'scope',
        'review_comments',
        'evidence_comments',
        'responsibility',
    ],
    
    'StaticQuestionnaire': [
        'question_text',
    ],
    
    'AuditVersion': [
        'extended_information',
    ],
    
    'AuditFinding': [
        'evidence',
        'how_to_verify',
        'impact_recommendations',
        'details_of_finding',
        'comment',
    ],
    
    # ========== Contract Audit Models ==========
    'ContractAudit': [
        'title',
        'scope',
        'review_comments',
        'evidence_comments',
        'responsibility',
    ],
    
    'ContractStaticQuestionnaire': [
        'question_text',
    ],
    
    'ContractAuditVersion': [
        'extended_information',
    ],
    
    'ContractAuditFinding': [
        'evidence',
        'how_to_verify',
        'impact_recommendations',
        'details_of_finding',
        'comment',
    ],
    
    # ========== OCR Models ==========
    'Document': [
        'Title',
        'Description',
        'OriginalFilename',
        'DocumentLink',
    ],
    
    'OcrResult': [
        'OcrText',
    ],
    
    'ExtractedData': [
        'sla_name',
        'business_service_impacted',
        'measurement_methodology',
        'exclusions',
        'force_majeure_clauses',
        'compliance_framework',
        'audit_requirements',
    ],
    
    # ========== Notification Models ==========
    'Notification': [
        'title',
        'message',
    ],
    
    # ========== Risk Analysis Models ==========
    'Risk': [
        'title',
        'description',
        'ai_explanation',
    ],
    
    # ========== RFP Approval Models ==========
    'ApprovalWorkflows': [
        'workflow_name',
        'description',
    ],
    
    'ApprovalRequests': [
        'request_title',
        'request_description',
    ],
    
    'ApprovalStages': [
        'stage_name',
        'stage_description',
        'assigned_user_name',
        'rejection_reason',
    ],
    
    'ApprovalComments': [
        'comment_text',
        'commented_by_name',
    ],
    
    'ApprovalRequestVersions': [
        'changes_summary',
        'created_by_name',
    ],
    
    # ========== SLA Approval Models ==========
    'SLAApproval': [
        'workflow_name',
        'assigner_name',
        'assignee_name',
        'comment_text',
    ],
    
    # ========== Compliance Models ==========
    'Framework': [
        'FrameworkDescription',
        'DocURL',
    ],
    
    'ComplianceMapping': [
        'compliance_description',
    ],
}


def get_encrypted_fields_for_model(model_name):
    """
    Get list of field names that should be encrypted for a given TPRM model.
    
    Args:
        model_name: String name of the model class
        
    Returns:
        List of field names to encrypt, or empty list if none
    """
    return TPRM_ENCRYPTED_FIELDS_CONFIG.get(model_name, [])


def should_encrypt_field(model_name, field_name):
    """
    Check if a specific field should be encrypted.
    
    Args:
        model_name: String name of the model class
        field_name: String name of the field
        
    Returns:
        True if field should be encrypted, False otherwise
    """
    encrypted_fields = get_encrypted_fields_for_model(model_name)
    return field_name in encrypted_fields


def get_all_configured_models():
    """
    Get list of all models that have encryption configured.
    
    Returns:
        List of model names with encryption configuration
    """
    return list(TPRM_ENCRYPTED_FIELDS_CONFIG.keys())


def get_all_encrypted_fields():
    """
    Get dictionary of all models and their encrypted fields.
    
    Returns:
        Dictionary mapping model names to lists of encrypted field names
    """
    return TPRM_ENCRYPTED_FIELDS_CONFIG.copy()

