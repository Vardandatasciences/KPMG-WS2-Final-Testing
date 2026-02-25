"""
Serializers for management views
"""

from rest_framework import serializers
from tprm_backend.apps.vendor_core.models import Vendors, TempVendor
from tprm_backend.apps.vendor_core.serializers import VendorsSerializer, TempVendorSerializer as BaseTempVendorSerializer


class AllVendorsListSerializer(serializers.ModelSerializer):
    """Serializer for vendor listing"""
    vendor_type = serializers.CharField(read_only=True)
    vendor_type_label = serializers.CharField(read_only=True)
    is_temporary = serializers.BooleanField(read_only=True)
    response_id = serializers.IntegerField(read_only=True, allow_null=True)
    
    class Meta:
        model = Vendors
        fields = [
            'vendor_id', 'vendor_code', 'company_name', 'legal_name',
            'business_type', 'industry_sector', 'risk_level', 'status',
            'lifecycle_stage', 'is_critical_vendor', 'has_data_access',
            'has_system_access', 'created_at', 'updated_at',
            'vendor_type', 'vendor_type_label', 'is_temporary', 'response_id'
        ]


class TempVendorSerializer(BaseTempVendorSerializer):
    """Extended serializer for temporary vendor with additional fields"""
    vendor_type = serializers.CharField(read_only=True)
    vendor_type_label = serializers.CharField(read_only=True)
    is_temporary = serializers.BooleanField(read_only=True)
    vendor_id = serializers.SerializerMethodField()
    
    class Meta(BaseTempVendorSerializer.Meta):
        fields = BaseTempVendorSerializer.Meta.fields + [
            'vendor_type', 'vendor_type_label', 'is_temporary', 'vendor_id'
        ]
    
    def get_vendor_id(self, obj):
        """Return id as vendor_id for consistency"""
        return obj.id
"""
Serializers for Management app
"""
 
from rest_framework import serializers
from tprm_backend.apps.vendor_core.models import TempVendor
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
 
 
class TempVendorManagementSerializer(AutoDecryptingModelSerializer):
    """Serializer for TempVendor in Management app"""
   
    class Meta:
        model = TempVendor
        fields = [
            'id', 'userid', 'vendor_code', 'company_name', 'legal_name',
            'lifecycle_stage', 'business_type', 'tax_id', 'duns_number',
            'incorporation_date', 'industry_sector', 'website',
            'annual_revenue', 'employee_count', 'headquarters_address',
            'vendor_category', 'risk_level', 'status', 'is_critical_vendor',
            'has_data_access', 'has_system_access', 'description',
            'contacts', 'documents', 'created_at', 'updated_at',
            'response_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
   
    def validate_company_name(self, value):
        """Validate company name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Company name must be at least 2 characters long")
        return value.strip()
   
    def validate_vendor_code(self, value):
        """Validate and truncate vendor_code to max 100 characters"""
        if value:
            value = str(value).strip()
            if len(value) > 100:
                import logging
                logger = logging.getLogger('management')
                logger.warning(f"Vendor Code truncated from {len(value)} to 100 characters: {value[:100]}")
                value = value[:100]
            if len(value) < 3:
                raise serializers.ValidationError("Vendor code must be at least 3 characters long")
            return value.upper()
        return value
   
    def validate_tax_id(self, value):
        """Validate and truncate tax_id to max 100 characters"""
        if value:
            value = str(value).strip()
            if len(value) > 100:
                import logging
                logger = logging.getLogger('management')
                logger.warning(f"Tax ID truncated from {len(value)} to 100 characters: {value[:100]}")
                value = value[:100]
        return value
   
    def validate_duns_number(self, value):
        """Validate and truncate duns_number to max 100 characters"""
        if value:
            value = str(value).strip()
            if len(value) > 100:
                import logging
                logger = logging.getLogger('management')
                logger.warning(f"DUNS Number truncated from {len(value)} to 100 characters: {value[:100]}")
                value = value[:100]
        return value
   
    def validate_annual_revenue(self, value):
        """Validate annual revenue"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Annual revenue cannot be negative")
        return value
   
    def validate_employee_count(self, value):
        """Validate employee count"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Employee count cannot be negative")
        return value
   
    def create(self, validated_data):
        """Create a new TempVendor instance using the correct database"""
        from django.db import connections
       
        # Use 'tprm' database connection which points to tprm_integrations schema
        if 'tprm' in connections.databases:
            instance = self.Meta.model.objects.using('tprm').create(**validated_data)
        else:
            instance = self.Meta.model.objects.create(**validated_data)
       
        return instance
   
    def update(self, instance, validated_data):
        """Update a TempVendor instance using the correct database"""
        from django.db import connections
       
        # Use 'tprm' database connection which points to tprm_integrations schema
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
       
        if 'tprm' in connections.databases:
            instance.save(using='tprm')
        else:
            instance.save()
       
        return instance
 
 
class VendorRiskSerializer(serializers.ModelSerializer):
    """Serializer for Vendor Risks from risk_tprm table"""
    tenant_id = serializers.SerializerMethodField()
    id = serializers.CharField(allow_null=True, allow_blank=True)  # String IDs like 'R-1755'
    title = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    description = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    likelihood = serializers.IntegerField(allow_null=True, required=False)
    impact = serializers.IntegerField(allow_null=True, required=False)
    score = serializers.FloatField(allow_null=True, required=False)
    priority = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    ai_explanation = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    suggested_mitigations = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    status = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    exposure_rating = serializers.IntegerField(allow_null=True, required=False)
    risk_type = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    entity = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    data = serializers.JSONField(allow_null=True, required=False)
    row = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    created_at = serializers.DateTimeField(allow_null=True, required=False)
    updated_at = serializers.DateTimeField(allow_null=True, required=False)
   
    class Meta:
        from tprm_backend.apps.vendor_risk.models import RiskTPRM
        model = RiskTPRM
        fields = [
            'id', 'title', 'description', 'likelihood', 'impact', 'score',
            'priority', 'ai_explanation', 'suggested_mitigations', 'status',
            'exposure_rating', 'risk_type', 'entity', 'data', 'row',
            'created_at', 'updated_at', 'tenant_id'
        ]
   
    def get_tenant_id(self, obj):
        """Get tenant_id from the ForeignKey"""
        return obj.tenant_id if hasattr(obj, 'tenant_id') else (obj.tenant.id if obj.tenant else None) 