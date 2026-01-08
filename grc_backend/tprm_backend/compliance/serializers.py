from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import Framework, ComplianceMapping

class FrameworkSerializer(AutoDecryptingModelSerializer):
    class Meta:
        model = Framework
        fields = '__all__'

class ComplianceMappingSerializer(AutoDecryptingModelSerializer):
    framework_name = serializers.CharField(source='framework.FrameworkName', read_only=True)
    framework_category = serializers.CharField(source='framework.Category', read_only=True)
    framework_version = serializers.FloatField(source='framework.CurrentVersion', read_only=True)
    sla_name = serializers.SerializerMethodField()
    vendor_name = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceMapping
        fields = [
            'mapping_id', 'sla_id', 'framework_id', 'compliance_status', 
            'compliance_score', 'last_audited', 'next_audit_due', 
            'assigned_auditor', 'audit_frequency', 'compliance_version', 
            'compliance_description', 'framework_name', 'framework_category', 
            'framework_version', 'sla_name', 'vendor_name'
        ]

    def get_sla_name(self, obj):
        # This would need to be populated from the SLA data
        # For now, return a placeholder
        return f"SLA-{obj.sla_id}"

    def get_vendor_name(self, obj):
        # This would need to be populated from the vendor data
        # For now, return a placeholder
        return "Unknown Vendor"

class ComplianceMappingDetailSerializer(AutoDecryptingModelSerializer):
    framework = FrameworkSerializer(read_only=True)
    sla_name = serializers.SerializerMethodField()
    vendor_name = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceMapping
        fields = [
            'mapping_id', 'sla_id', 'framework_id', 'compliance_status', 
            'compliance_score', 'last_audited', 'next_audit_due', 
            'assigned_auditor', 'audit_frequency', 'compliance_version', 
            'compliance_description', 'framework', 'sla_name', 'vendor_name'
        ]

    def get_sla_name(self, obj):
        # This would need to be populated from the SLA data
        return f"SLA-{obj.sla_id}"

    def get_vendor_name(self, obj):
        # This would need to be populated from the vendor data
        return "Unknown Vendor"