from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.models import User
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import RFI, RFIEvaluationCriteria


class RFIEvaluationCriteriaSerializer(AutoDecryptingModelSerializer):
    """Serializer for RFI Evaluation Criteria"""
    rfi_id = serializers.IntegerField(write_only=True, required=False)
    rfi = serializers.PrimaryKeyRelatedField(queryset=RFI.objects.all(), required=False, allow_null=True)
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    created_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = RFIEvaluationCriteria
        fields = [
            'criteria_id', 'rfi_id', 'rfi', 'criteria_name', 'criteria_description', 
            'weight_percentage', 'evaluation_type', 'min_score', 
            'max_score', 'median_score', 'is_mandatory', 
            'veto_enabled', 'veto_threshold', 'min_word_count',
            'expected_boolean_answer', 'display_order', 'created_by', 'data_inventory'
        ]
        read_only_fields = ['criteria_id', 'created_by']
    
    def get_rfi_id(self, obj):
        """Get rfi_id from ForeignKey relationship"""
        try:
            if hasattr(obj, 'rfi_id'):
                return obj.rfi_id
            elif hasattr(obj, 'rfi') and obj.rfi:
                return obj.rfi.rfi_id
        except Exception:
            pass
        return None
    
    def to_representation(self, instance):
        """Override to include rfi_id in response"""
        representation = super().to_representation(instance)
        representation['rfi_id'] = self.get_rfi_id(instance)
        return representation
    
    def validate(self, data):
        """Validate evaluation criteria data and convert rfi_id to rfi"""
        # Convert rfi_id to rfi if rfi_id is provided but rfi is not
        rfi_id = data.pop('rfi_id', None)
        if rfi_id is not None:
            try:
                rfi_obj = RFI.objects.get(rfi_id=rfi_id)
                data['rfi'] = rfi_obj
            except RFI.DoesNotExist:
                raise serializers.ValidationError({'rfi_id': f'RFI with ID {rfi_id} does not exist'})
            except Exception as e:
                raise serializers.ValidationError({'rfi_id': f'Error fetching RFI: {str(e)}'})
        elif 'rfi' not in data or data.get('rfi') is None:
            # If neither rfi_id nor rfi is provided, make it optional for now
            # The model will enforce the constraint if needed
            pass
        
        # Validate weight_percentage if provided
        if 'weight_percentage' in data:
            weight = data['weight_percentage']
            if weight is not None and (weight < 0 or weight > 100):
                raise serializers.ValidationError(
                    {"weight_percentage": "Weight must be between 0 and 100"}
                )
        return data
    
    def validate_data_inventory(self, value):
        """Ensure data_inventory is always a dictionary"""
        if not isinstance(value, dict):
            return {}
        return value


class RFISerializer(AutoDecryptingModelSerializer):
    """Serializer for RFI model"""
    evaluation_criteria = RFIEvaluationCriteriaSerializer(many=True, required=False)
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = RFI
        fields = [
            'rfi_id', 'rfi_number', 'rfi_title', 'description', 'rfi_type',
            'category', 'estimated_value', 'currency', 'issue_date',
            'submission_deadline', 'evaluation_period_end', 'award_date',
            'status', 'created_by', 'approved_by', 'primary_reviewer_id',
            'executive_reviewer_id', 'version_number', 'auto_approve',
            'allow_late_submissions', 'created_at', 'updated_at',
            'approval_workflow_id', 'evaluation_method', 'budget_range_min',
            'budget_range_max', 'criticality_level', 'geographical_scope',
            'compliance_requirements', 'custom_fields', 'final_evaluation_score',
            'award_decision_date', 'award_justification', 'documents', 'evaluation_criteria',
            'data_inventory', 'retentionExpiry'
        ]
        read_only_fields = [
            'rfi_id', 'rfi_number', 'created_at', 'updated_at'
        ]
    
    def validate_data_inventory(self, value):
        """Ensure data_inventory is always a dictionary"""
        if not isinstance(value, dict):
            return {}
        return value


class RFICreateSerializer(AutoDecryptingModelSerializer):
    """Serializer for creating RFI (simplified)"""
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    documents = serializers.JSONField(required=False, allow_null=True)
    created_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = RFI
        fields = [
            'rfi_id', 'rfi_number', 'rfi_title', 'description', 'rfi_type',
            'category', 'estimated_value', 'currency', 'issue_date',
            'submission_deadline', 'evaluation_period_end', 'award_date',
            'status', 'created_by', 'approved_by', 'primary_reviewer_id',
            'executive_reviewer_id', 'version_number', 'auto_approve',
            'allow_late_submissions', 'approval_workflow_id', 'evaluation_method',
            'budget_range_min', 'budget_range_max', 'criticality_level',
            'geographical_scope', 'compliance_requirements', 'custom_fields',
            'data_inventory', 'retentionExpiry', 'documents'
        ]
        read_only_fields = ['rfi_id', 'rfi_number', 'created_by']
    
    def validate_documents(self, value):
        """Ensure documents is always a list/array when provided"""
        if value is not None and not isinstance(value, list):
            return []
        return value
    
    def validate_data_inventory(self, value):
        """Ensure data_inventory is always a dictionary"""
        if not isinstance(value, dict):
            return {}
        return value


class RFIListSerializer(AutoDecryptingModelSerializer):
    """Simplified serializer for RFI list view"""
    
    class Meta:
        model = RFI
        fields = [
            'rfi_id', 'rfi_number', 'rfi_title', 'description', 'rfi_type',
            'status', 'created_at', 'submission_deadline', 'criticality_level',
            'created_by', 'budget_range_min', 'budget_range_max', 'category'
        ]
