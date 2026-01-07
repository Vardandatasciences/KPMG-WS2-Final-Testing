"""
Serializers for the SLAs app matching MySQL schema.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import (
    Vendor, Contract, VendorSLA, SLAMetric, SLADocument,
    SLACompliance, SLAViolation, SLAReview
)

User = get_user_model()


class VendorSerializer(AutoDecryptingModelSerializer):
    """Serializer for Vendor model."""
    
    class Meta:
        model = Vendor
        fields = [
            'vendor_id', 'vendor_code', 'company_name', 'legal_name', 'status'
        ]
        read_only_fields = ['vendor_id']


class ContractSerializer(AutoDecryptingModelSerializer):
    """Serializer for Contract model."""
    
    class Meta:
        model = Contract
        fields = [
            'contract_id', 'contract_name'
        ]
        read_only_fields = ['contract_id']


class SLAMetricSerializer(AutoDecryptingModelSerializer):
    """Serializer for SLAMetric model."""
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = SLAMetric
        fields = [
            'metric_id', 'sla', 'metric_name', 'threshold', 'measurement_unit', 'frequency',
            'penalty', 'measurement_methodology', 'data_inventory'
        ]
        read_only_fields = ['metric_id']


class VendorSLASerializer(AutoDecryptingModelSerializer):
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
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = VendorSLA
        fields = [
            'sla_id', 'vendor', 'vendor_id', 'contract', 'contract_id',
            'sla_name', 'sla_type', 'effective_date', 'expiry_date', 'status', 
            'business_service_impacted', 'reporting_frequency', 'baseline_period', 
            'improvement_targets', 'penalty_threshold', 'credit_threshold', 
            'measurement_methodology', 'exclusions', 'force_majeure_clauses', 
            'compliance_framework', 'audit_requirements', 'document_versioning', 
            'priority', 'approval_status', 'compliance_score', 'data_inventory', 'metrics'
        ]
        read_only_fields = ['sla_id']


class SLADocumentSerializer(AutoDecryptingModelSerializer):
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


class SLAComplianceSerializer(AutoDecryptingModelSerializer):
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


class SLAViolationSerializer(AutoDecryptingModelSerializer):
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


class SLAReviewSerializer(AutoDecryptingModelSerializer):
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


class VendorSLADetailSerializer(AutoDecryptingModelSerializer):
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
            'priority', 'approval_status', 'data_inventory', 'metrics',
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


class SLAMetricCreateSerializer(AutoDecryptingModelSerializer):
    """Serializer for creating SLA metrics without requiring sla field."""
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = SLAMetric
        fields = [
            'metric_name', 'threshold', 'measurement_unit', 'frequency',
            'penalty', 'measurement_methodology', 'data_inventory'
        ]
    
    def validate_data_inventory(self, value):
        """Ensure data_inventory is always a dict (even if empty)."""
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        # If it's not a dict, return empty dict
        return {}
    
    def to_internal_value(self, data):
        """Override to ensure data_inventory is always included in validated data."""
        validated_data = super().to_internal_value(data)
        # Ensure data_inventory is always present (even if None or empty)
        if 'data_inventory' not in validated_data:
            validated_data['data_inventory'] = {}
        elif validated_data.get('data_inventory') is None:
            validated_data['data_inventory'] = {}
        return validated_data


class VendorSLASubmissionSerializer(AutoDecryptingModelSerializer):
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
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = VendorSLA
        fields = [
            'sla_id', 'vendor_id', 'contract_id', 'sla_name', 'sla_type',
            'effective_date', 'expiry_date', 'status', 'business_service_impacted',
            'reporting_frequency', 'baseline_period', 'improvement_targets',
            'penalty_threshold', 'credit_threshold', 'measurement_methodology',
            'exclusions', 'force_majeure_clauses', 'compliance_framework',
            'audit_requirements', 'document_versioning', 'compliance_score',
            'priority', 'approval_status', 'data_inventory', 'metrics'
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
        
        # Log data_inventory if present for main SLA
        if 'data_inventory' in validated_data:
            print(f"📊 [SLA CREATE] Data inventory for vendor_slas: {validated_data.get('data_inventory')}")
        else:
            print("⚠️ [SLA CREATE] No data_inventory found in validated_data for vendor_slas")
            
        sla = VendorSLA.objects.create(**validated_data)
        
        # Create metrics with their individual data_inventory
        print(f"📊 [SLA CREATE] Processing {len(metrics_data)} metrics")
        for idx, metric_data in enumerate(metrics_data):
            # Log all metric data keys for debugging
            print(f"📊 [SLA CREATE] Metric {idx + 1} data keys: {list(metric_data.keys())}")
            print(f"📊 [SLA CREATE] Metric {idx + 1} full data: {metric_data}")
            
            # Explicitly ensure data_inventory is included and is a dict (not None)
            metric_to_create = metric_data.copy()
            
            # Get data_inventory value
            data_inv_value = metric_to_create.get('data_inventory')
            
            # Normalize data_inventory: ensure it's always a dict (never None)
            if data_inv_value is None:
                metric_to_create['data_inventory'] = {}
                print(f"⚠️ [SLA CREATE] data_inventory was None, setting to empty dict for metric '{metric_data.get('metric_name')}'")
            elif not isinstance(data_inv_value, dict):
                # If it's not a dict, convert to empty dict
                metric_to_create['data_inventory'] = {}
                print(f"⚠️ [SLA CREATE] data_inventory was not a dict ({type(data_inv_value)}), converting to empty dict for metric '{metric_data.get('metric_name')}'")
            elif len(data_inv_value) == 0:
                # Empty dict is fine, but log it
                print(f"📊 [SLA CREATE] data_inventory is empty dict for metric '{metric_data.get('metric_name')}' - this is OK")
            else:
                # Has data, log it
                print(f"📊 [SLA CREATE] data_inventory for metric '{metric_data.get('metric_name')}': {data_inv_value}")
                print(f"📊 [SLA CREATE] data_inventory type: {type(data_inv_value)}, keys: {list(data_inv_value.keys())}")
            
            # Ensure data_inventory is explicitly set (even if empty dict)
            # This prevents Django from treating it as "not provided" and setting to None
            if 'data_inventory' not in metric_to_create:
                metric_to_create['data_inventory'] = {}
            
            # Create the metric with all data including data_inventory
            print(f"📊 [SLA CREATE] Creating metric '{metric_data.get('metric_name')}' with data_inventory: {metric_to_create.get('data_inventory')}")
            
            # Use create with explicit data_inventory to ensure it's saved
            created_metric = SLAMetric.objects.create(
                sla=sla,
                metric_name=metric_to_create.get('metric_name'),
                threshold=metric_to_create.get('threshold'),
                measurement_unit=metric_to_create.get('measurement_unit', ''),
                frequency=metric_to_create.get('frequency'),
                penalty=metric_to_create.get('penalty', ''),
                measurement_methodology=metric_to_create.get('measurement_methodology', ''),
                data_inventory=metric_to_create.get('data_inventory', {})  # Explicitly set, default to {}
            )
            
            print(f"✅ [SLA CREATE] Created metric {created_metric.metric_id} - '{created_metric.metric_name}'")
            print(f"✅ [SLA CREATE] Saved data_inventory value: {created_metric.data_inventory}")
            print(f"✅ [SLA CREATE] Saved data_inventory type: {type(created_metric.data_inventory)}")
            print(f"✅ [SLA CREATE] Saved data_inventory is None: {created_metric.data_inventory is None}")
            print(f"✅ [SLA CREATE] Saved data_inventory == {{}}: {created_metric.data_inventory == {}}")
        
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