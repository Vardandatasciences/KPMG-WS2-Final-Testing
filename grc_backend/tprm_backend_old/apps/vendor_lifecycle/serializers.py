"""
Vendor Lifecycle Serializers
"""

from rest_framework import serializers
from .models import (
    VendorApprovals, 
    VendorStatusHistory, 
    VendorLifecycleStages,
    VendorContracts,
    VendorSlas
)
from tprm_backend.apps.vendor_core.models import Vendors, Users


class VendorLifecycleStageSerializer(serializers.ModelSerializer):
    """Serializer for vendor lifecycle stages"""
    
    class Meta:
        model = VendorLifecycleStages
        fields = [
            'stage_id', 'stage_name', 'stage_code', 'stage_order', 
            'description', 'is_active', 'approval_required', 'max_duration_days'
        ]


class VendorApprovalSerializer(serializers.ModelSerializer):
    """Serializer for vendor approvals"""
    
    vendor_name = serializers.CharField(source='vendor.company_name', read_only=True)
    stage_name = serializers.CharField(source='stage.stage_name', read_only=True)
    approver_name = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorApprovals
        fields = [
            'approval_id', 'vendor', 'stage', 'approver', 'approval_status',
            'comments', 'conditions', 'approval_date', 'due_date',
            'vendor_name', 'stage_name', 'approver_name', 'created_at'
        ]
    
    def get_approver_name(self, obj):
        if hasattr(obj.approver, 'first_name') and obj.approver.first_name:
            return f"{obj.approver.first_name} {obj.approver.last_name or ''}"
        return obj.approver.username


class VendorStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for vendor status history"""
    
    vendor_name = serializers.CharField(source='vendor.company_name', read_only=True)
    changed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorStatusHistory
        fields = [
            'history_id', 'vendor', 'old_status', 'new_status', 'old_stage', 'new_stage',
            'changed_by', 'change_reason', 'comments', 'change_date', 'vendor_name', 'changed_by_name'
        ]
    
    def get_changed_by_name(self, obj):
        if hasattr(obj.changed_by, 'first_name') and obj.changed_by.first_name:
            return f"{obj.changed_by.first_name} {obj.changed_by.last_name or ''}"
        return obj.changed_by.username


class TimelineEventSerializer(serializers.Serializer):
    """Serializer for timeline events"""
    
    id = serializers.CharField()
    date = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    status = serializers.CharField()
    user = serializers.CharField()


class StageAnalyticsSerializer(serializers.Serializer):
    """Serializer for stage analytics"""
    
    stage = serializers.CharField()
    vendors = serializers.IntegerField()
    percentage = serializers.FloatField()


class RecentChangeSerializer(serializers.Serializer):
    """Serializer for recent status changes"""
    
    vendor = serializers.CharField()
    from_stage = serializers.CharField(source='from')
    to_stage = serializers.CharField(source='to')
    date = serializers.CharField()


class VendorContractSerializer(serializers.ModelSerializer):
    """Serializer for vendor contracts"""
    
    vendor_name = serializers.CharField(source='vendor.company_name', read_only=True)
    contract_owner_name = serializers.SerializerMethodField()
    legal_reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorContracts
        fields = [
            'contract_id', 'vendor', 'contract_number', 'contract_title',
            'contract_type', 'contract_value', 'currency', 'start_date',
            'end_date', 'status', 'vendor_name', 'contract_owner_name', 'legal_reviewer_name'
        ]
    
    def get_contract_owner_name(self, obj):
        if obj.contract_owner and hasattr(obj.contract_owner, 'first_name'):
            return f"{obj.contract_owner.first_name} {obj.contract_owner.last_name or ''}"
        return None
    
    def get_legal_reviewer_name(self, obj):
        if obj.legal_reviewer and hasattr(obj.legal_reviewer, 'first_name'):
            return f"{obj.legal_reviewer.first_name} {obj.legal_reviewer.last_name or ''}"
        return None


class VendorSlaSerializer(serializers.ModelSerializer):
    """Serializer for vendor SLAs"""
    
    vendor_name = serializers.CharField(source='vendor.company_name', read_only=True)
    
    class Meta:
        model = VendorSlas
        fields = [
            'sla_id', 'vendor', 'sla_name', 'sla_type', 'metric_name',
            'target_value', 'measurement_unit', 'effective_date', 'expiry_date', 'status', 'vendor_name'
        ]
