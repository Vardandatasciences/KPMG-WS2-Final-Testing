from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import Document, OcrResult, ExtractedData


class DocumentSerializer(AutoDecryptingModelSerializer):
    """Serializer for Document model"""
    
    class Meta:
        model = Document
        fields = [
            'DocumentId', 'ModuleId', 'Title', 'Description', 
            'OriginalFilename', 'DocumentLink', 'Category', 
            'Department', 'DocType', 'Status', 'CreatedBy', 
            'CreatedAt', 'UpdatedAt'
        ]
        read_only_fields = ['DocumentId', 'CreatedAt', 'UpdatedAt']


class OcrResultSerializer(AutoDecryptingModelSerializer):
    """Serializer for OcrResult model"""
    
    class Meta:
        model = OcrResult
        fields = [
            'OcrResultId', 'DocumentId', 'VersionId', 'OcrText',
            'OcrLanguage', 'OcrConfidence', 'OcrEngine', 'CreatedAt', 'ocr_data'
        ]
        read_only_fields = ['OcrResultId', 'CreatedAt']


class ExtractedDataSerializer(AutoDecryptingModelSerializer):
    """Serializer for ExtractedData model"""
    
    class Meta:
        model = ExtractedData
        fields = [
            'ExtractedDataId', 'DocumentId_id', 'OcrResultId_id',
            'sla_name', 'vendor_id', 'contract_id', 'sla_type',
            'effective_date', 'expiry_date', 'status',
            'business_service_impacted', 'reporting_frequency',
            'baseline_period', 'improvement_targets', 'penalty_threshold',
            'credit_threshold', 'measurement_methodology', 'exclusions',
            'force_majeure_clauses', 'compliance_framework', 'audit_requirements',
            'document_versioning', 'compliance_score', 'priority', 'approval_status',
            'metrics', 'raw_extracted_data', 'extraction_confidence',
            'extraction_method', 'CreatedAt', 'UpdatedAt'
        ]
        read_only_fields = ['ExtractedDataId', 'CreatedAt', 'UpdatedAt']


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload with metadata"""
    
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(max_length=100, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    doc_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    module_id = serializers.IntegerField(default=1)
    
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()


class DocumentProcessingSerializer(serializers.Serializer):
    """Serializer for document processing results"""
    
    document_id = serializers.IntegerField()
    upload_success = serializers.BooleanField()
    ocr_success = serializers.BooleanField()
    extraction_success = serializers.BooleanField()
    s3_url = serializers.URLField(required=False, allow_blank=True)
    ocr_text = serializers.CharField(required=False, allow_blank=True)
    extracted_data = serializers.JSONField(required=False)
    error_message = serializers.CharField(required=False, allow_blank=True)


class SLAExtractionPayloadSerializer(serializers.Serializer):
    """Serializer for SLA extraction payload structure"""
    
    sla_name = serializers.CharField(required=False, allow_blank=True)
    vendor_id = serializers.CharField(required=False, allow_blank=True)
    contract_id = serializers.CharField(required=False, allow_blank=True)
    sla_type = serializers.CharField(required=False, allow_blank=True)
    effective_date = serializers.CharField(required=False, allow_blank=True)
    expiry_date = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(default='PENDING')
    business_service_impacted = serializers.CharField(required=False, allow_blank=True)
    reporting_frequency = serializers.CharField(default='monthly')
    baseline_period = serializers.CharField(required=False, allow_blank=True)
    improvement_targets = serializers.JSONField(required=False, default=dict)
    penalty_threshold = serializers.CharField(required=False, allow_blank=True)
    credit_threshold = serializers.CharField(required=False, allow_blank=True)
    measurement_methodology = serializers.CharField(required=False, allow_blank=True)
    exclusions = serializers.CharField(required=False, allow_blank=True)
    force_majeure_clauses = serializers.CharField(required=False, allow_blank=True)
    compliance_framework = serializers.CharField(required=False, allow_blank=True)
    audit_requirements = serializers.CharField(required=False, allow_blank=True)
    document_versioning = serializers.CharField(required=False, allow_blank=True)
    compliance_score = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.CharField(required=False, allow_blank=True)
    approval_status = serializers.CharField(default='PENDING')
    metrics = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )




class BcpDrpOcrRunSerializer(serializers.Serializer):
    """Serializer for BCP/DRP OCR run request - accepts any plan type"""
    
    plan_id = serializers.IntegerField(required=True)
    plan_type = serializers.CharField(max_length=45, required=True)  # Accept any plan type
    file_uri = serializers.CharField(max_length=1024, required=False, allow_blank=True, allow_null=True)
    
    def validate_plan_id(self, value):
        if value <= 0:
            raise serializers.ValidationError("Plan ID must be a positive integer")
        return value


class BcpDrpExtractionPayloadSerializer(serializers.Serializer):
    """Serializer for BCP/DRP extraction payload structure"""
    
    # Common fields
    purpose_scope = serializers.CharField(required=False, allow_blank=True)
    regulatory_references = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    rto_targets = serializers.DictField(required=False, default=dict)
    rpo_targets = serializers.DictField(required=False, default=dict)
    
    # BCP-specific fields
    critical_services = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    dependencies_internal = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    dependencies_external = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    risk_assessment_summary = serializers.CharField(required=False, allow_blank=True)
    bia_summary = serializers.CharField(required=False, allow_blank=True)
    incident_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    alternate_work_locations = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    communication_plan_internal = serializers.CharField(required=False, allow_blank=True)
    communication_plan_bank = serializers.CharField(required=False, allow_blank=True)
    roles_responsibilities = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    training_testing_schedule = serializers.CharField(required=False, allow_blank=True)
    maintenance_review_cycle = serializers.CharField(required=False, allow_blank=True)
    
    # DRP-specific fields
    critical_systems = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    critical_applications = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    databases_list = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    supporting_infrastructure = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    third_party_services = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    disaster_scenarios = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    disaster_declaration_process = serializers.CharField(required=False, allow_blank=True)
    data_backup_strategy = serializers.CharField(required=False, allow_blank=True)
    recovery_site_details = serializers.CharField(required=False, allow_blank=True)
    failover_procedures = serializers.CharField(required=False, allow_blank=True)
    failback_procedures = serializers.CharField(required=False, allow_blank=True)
    network_recovery_steps = serializers.CharField(required=False, allow_blank=True)
    application_restoration_order = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    testing_validation_schedule = serializers.CharField(required=False, allow_blank=True)
