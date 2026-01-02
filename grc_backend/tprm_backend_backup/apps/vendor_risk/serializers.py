"""
Vendor Risk Assessment Serializers
"""
from rest_framework import serializers
from .models import VendorRiskAssessments, VendorRiskFactors, VendorRiskThresholds, VendorLifecycleStages


class VendorRiskAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Vendor Risk Assessments"""
    
    class Meta:
        model = VendorRiskAssessments
        fields = '__all__'
        read_only_fields = ('assessment_id', 'created_at')


class VendorRiskFactorSerializer(serializers.ModelSerializer):
    """Serializer for Vendor Risk Factors"""
    
    class Meta:
        model = VendorRiskFactors
        fields = '__all__'
        read_only_fields = ('factor_id',)


class VendorRiskThresholdSerializer(serializers.ModelSerializer):
    """Serializer for Vendor Risk Thresholds"""
    
    class Meta:
        model = VendorRiskThresholds
        fields = '__all__'
        read_only_fields = ('threshold_id', 'created_at', 'updated_at')


class VendorLifecycleStageSerializer(serializers.ModelSerializer):
    """Serializer for Vendor Lifecycle Stages"""
    
    class Meta:
        model = VendorLifecycleStages
        fields = '__all__'
        read_only_fields = ('stage_id', 'created_at')
