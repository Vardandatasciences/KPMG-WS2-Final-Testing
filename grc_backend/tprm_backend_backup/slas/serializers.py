"""
Serializers for the SLAs app matching MySQL schema.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Vendor, Contract, VendorSLA, SLAMetric, SLADocument,
    SLACompliance, SLAViolation, SLAReview
)

User = get_user_model()


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for Vendor model."""
    
    class Meta:
        model = Vendor
        fields = [
            'vendor_id', 'vendor_code', 'company_name', 'legal_name', 'status'
        ]
        read_only_fields = ['vendor_id']


class ContractSerializer(serializers.ModelSerializer):
    """Serializer for Contract model."""
    
    class Meta:
        model = Contract
        fields = [
            'contract_id', 'contract_name'
        ]
        read_only_fields = ['contract_id']


class SLAMetricSerializer(serializers.ModelSerializer):
    """Serializer for SLAMetric model."""
    
    class Meta:
        model = SLAMetric
        fields = [
            'metric_id', 'sla', 'metric_name', 'threshold', 'measurement_unit', 'frequency',
            'penalty', 'measurement_methodology'
        ]
        read_only_fields = ['metric_id']


class VendorSLASerializer(serializers.ModelSerializer):
    """Serializer for VendorSLA model."""
    vendor = VendorSerializer(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        source='vendor',
        write_only=True
    )
    contract = ContractSerializer(read_only=True)
    contract_id = serializers.PrimaryKeyRelatedField(
        queryset=Contract.objects.all(),
        source='contract',
        write_only=True
    )
    metrics = SLAMetricSerializer(many=True, read_only=True)
    
    class Meta:
        model = VendorSLA
        fields = [
            'sla_id', 'vendor', 'vendor_id', 'contract', 'contract_id',
            'sla_name', 'sla_type', 'effective_date', 'expiry_date', 'status', 
            'business_service_impacted', 'reporting_frequency', 'baseline_period', 
            'improvement_targets', 'penalty_threshold', 'credit_threshold', 
            'measurement_methodology', 'exclusions', 'force_majeure_clauses', 
            'compliance_framework', 'audit_requirements', 'document_versioning', 
            'priority', 'approval_status', 'compliance_score', 'metrics'
        ]
        read_only_fields = ['sla_id']


class SLADocumentSerializer(serializers.ModelSerializer):
    """Serializer for SLADocument model."""
    vendor = VendorSerializer(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        source='vendor',
        write_only=True
    )
    contract = ContractSerializer(read_only=True)
    contract_id = serializers.PrimaryKeyRelatedField(
        queryset=Contract.objects.all(),
        source='contract',
        write_only=True
    )
    uploaded_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False
    )
    
    class Meta:
        model = SLADocument
        fields = [
            'document_id', 'vendor', 'vendor_id', 'contract', 'contract_id',
            'sla_name', 'document_file', 'file_type', 'extracted_data',
            'uploaded_by', 'upload_date', 'processed_status',
        ]
        read_only_fields = ['document_id', 'upload_date']


class SLAComplianceSerializer(serializers.ModelSerializer):
    """Serializer for SLACompliance model."""
    sla = VendorSLASerializer(read_only=True)
    metric = SLAMetricSerializer(read_only=True)
    
    class Meta:
        model = SLACompliance
        fields = [
            'id', 'sla', 'metric', 'period_start', 'period_end',
            'actual_value', 'target_value', 'compliance_percentage',
            'is_compliant', 'breach_duration', 'penalty_applied',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id']


class SLAViolationSerializer(serializers.ModelSerializer):
    """Serializer for SLAViolation model."""
    sla = VendorSLASerializer(read_only=True)
    metric = SLAMetricSerializer(read_only=True)
    
    class Meta:
        model = SLAViolation
        fields = [
            'id', 'sla', 'metric', 'violation_date', 'violation_type',
            'actual_value', 'expected_value', 'duration',
            'impact_assessment', 'mitigation_actions', 'penalty_amount',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id']


class SLAReviewSerializer(serializers.ModelSerializer):
    """Serializer for SLAReview model."""
    sla = VendorSLASerializer(read_only=True)
    reviewer = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False
    )
    
    class Meta:
        model = SLAReview
        fields = [
            'id', 'sla', 'review_date', 'reviewer', 'review_type',
            'overall_score', 'strengths', 'weaknesses',
            'recommendations', 'action_items', 'next_review_date',
        ]
        read_only_fields = ['id']


class VendorSLADetailSerializer(serializers.ModelSerializer):
    """Detailed VendorSLA serializer with all related data."""
    vendor = VendorSerializer(read_only=True)
    contract = ContractSerializer(read_only=True)
    metrics = serializers.SerializerMethodField()
    compliance_records = serializers.SerializerMethodField()
    violations = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorSLA
        fields = [
            'sla_id', 'vendor', 'contract', 'sla_name', 'sla_type',
            'effective_date', 'expiry_date', 'status', 'business_service_impacted',
            'reporting_frequency', 'baseline_period', 'improvement_targets',
            'penalty_threshold', 'credit_threshold', 'measurement_methodology',
            'exclusions', 'force_majeure_clauses', 'compliance_framework',
            'audit_requirements', 'document_versioning', 'compliance_score',
            'priority', 'approval_status', 'metrics',
            'compliance_records', 'violations', 'reviews',
        ]
        read_only_fields = ['sla_id']
    
    def get_metrics(self, obj):
        """Safely get metrics."""
        try:
            print(f"Getting metrics for SLA {obj.sla_id}")
            metrics = obj.sla_metrics.all()
            print(f"Found {metrics.count()} metrics")
            return SLAMetricSerializer(metrics, many=True).data
        except Exception as e:
            print(f"Error getting metrics: {e}")
            return []
    
    def get_compliance_records(self, obj):
        """Safely get compliance records."""
        try:
            return SLAComplianceSerializer(obj.compliance_records.all(), many=True).data
        except Exception:
            return []
    
    def get_violations(self, obj):
        """Safely get violations."""
        try:
            return SLAViolationSerializer(obj.violations.all(), many=True).data
        except Exception:
            return []
    
    def get_reviews(self, obj):
        """Safely get reviews."""
        try:
            return SLAReviewSerializer(obj.reviews.all(), many=True).data
        except Exception:
            return []


class SLAMetricCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating SLA metrics without requiring sla field."""
    
    class Meta:
        model = SLAMetric
        fields = [
            'metric_name', 'threshold', 'measurement_unit', 'frequency',
            'penalty', 'measurement_methodology'
        ]


class VendorSLASubmissionSerializer(serializers.ModelSerializer):
    """Serializer for VendorSLA submission."""
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        source='vendor',
        write_only=True
    )
    contract_id = serializers.PrimaryKeyRelatedField(
        queryset=Contract.objects.all(),
        source='contract',
        write_only=True
    )
    metrics = SLAMetricCreateSerializer(many=True, source='sla_metrics')
    
    class Meta:
        model = VendorSLA
        fields = [
            'sla_id', 'vendor_id', 'contract_id', 'sla_name', 'sla_type',
            'effective_date', 'expiry_date', 'status', 'business_service_impacted',
            'reporting_frequency', 'baseline_period', 'improvement_targets',
            'penalty_threshold', 'credit_threshold', 'measurement_methodology',
            'exclusions', 'force_majeure_clauses', 'compliance_framework',
            'audit_requirements', 'document_versioning', 'compliance_score',
            'priority', 'approval_status', 'metrics'
        ]
    
    def validate_compliance_score(self, value):
        """Ensure compliance_score is not null."""
        if value is None:
            return 0.0
        return value
    
    def create(self, validated_data):
        metrics_data = validated_data.pop('sla_metrics', [])
        
        # Ensure compliance_score has a default value
        if 'compliance_score' not in validated_data or validated_data['compliance_score'] is None:
            validated_data['compliance_score'] = 0.0
            
        sla = VendorSLA.objects.create(**validated_data)
        
        for metric_data in metrics_data:
            SLAMetric.objects.create(sla=sla, **metric_data)
        
        return sla


class SLAComplianceSummarySerializer(serializers.Serializer):
    """Serializer for SLA compliance summary."""
    sla_id = serializers.IntegerField()
    sla_name = serializers.CharField()
    vendor_name = serializers.CharField()
    overall_compliance = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_metrics = serializers.IntegerField()
    compliant_metrics = serializers.IntegerField()
    violations_count = serializers.IntegerField()
    last_review_date = serializers.DateField(allow_null=True)
    next_review_date = serializers.DateField(allow_null=True)


class VendorSummarySerializer(serializers.Serializer):
    """Serializer for vendor summary."""
    vendor_id = serializers.IntegerField()
    vendor_name = serializers.CharField()
    total_contracts = serializers.IntegerField()
    active_slas = serializers.IntegerField()
    overall_compliance = serializers.DecimalField(max_digits=5, decimal_places=2)
    violations_count = serializers.IntegerField()
    risk_level = serializers.CharField()
    contract_value = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)