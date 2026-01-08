"""
Vendor Risk Assessment Serializers
"""
from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import VendorRiskAssessments, VendorRiskFactors, VendorRiskThresholds, VendorLifecycleStages


class VendorRiskAssessmentSerializer(AutoDecryptingModelSerializer):
    """Serializer for Vendor Risk Assessments"""
    
    class Meta:
        model = VendorRiskAssessments
        fields = '__all__'
        read_only_fields = ('assessment_id', 'created_at')


class VendorRiskFactorSerializer(AutoDecryptingModelSerializer):
    """Serializer for Vendor Risk Factors"""
    
    class Meta:
        model = VendorRiskFactors
        fields = '__all__'
        read_only_fields = ('factor_id',)


class VendorRiskThresholdSerializer(AutoDecryptingModelSerializer):
    """Serializer for Vendor Risk Thresholds"""
    
    class Meta:
        model = VendorRiskThresholds
        fields = '__all__'
        read_only_fields = ('threshold_id', 'created_at', 'updated_at')


class VendorLifecycleStageSerializer(AutoDecryptingModelSerializer):
    """Serializer for Vendor Lifecycle Stages"""
    
    class Meta:
        model = VendorLifecycleStages
        fields = '__all__'
        read_only_fields = ('stage_id', 'created_at')
