from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import DirectProcurement, DirectEvaluationCriteria


class DirectEvaluationCriteriaSerializer(AutoDecryptingModelSerializer):
    """Serializer for Direct Procurement Evaluation Criteria"""
    direct_id = serializers.IntegerField(write_only=True, required=False)
    direct = serializers.PrimaryKeyRelatedField(queryset=DirectProcurement.objects.all(), required=False, allow_null=True)
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    created_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = DirectEvaluationCriteria
        fields = [
            'criteria_id', 'direct_id', 'direct', 'criteria_name', 'criteria_description', 
            'weight_percentage', 'evaluation_type', 'min_score', 
            'max_score', 'median_score', 'is_mandatory', 
            'veto_enabled', 'veto_threshold', 'min_word_count',
            'expected_boolean_answer', 'display_order', 'created_by', 'data_inventory'
        ]
        read_only_fields = ['criteria_id', 'created_by']
    
    def validate_data_inventory(self, value):
        if not isinstance(value, dict):
            return {}
        return value
    
    def get_direct_id(self, obj):
        try:
            if hasattr(obj, 'direct_id'):
                return obj.direct_id
            elif hasattr(obj, 'direct') and obj.direct:
                return obj.direct.direct_id
        except Exception:
            pass
        return None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['direct_id'] = self.get_direct_id(instance)
        return representation
    
    def validate(self, data):
        """Validate evaluation criteria data and convert direct_id to direct"""
        # Convert direct_id to direct if direct_id is provided but direct is not
        direct_id = data.pop('direct_id', None)
        if direct_id is not None:
            try:
                from .models import DirectProcurement
                direct_obj = DirectProcurement.objects.get(direct_id=direct_id)
                data['direct'] = direct_obj
            except DirectProcurement.DoesNotExist:
                raise serializers.ValidationError({'direct_id': f'Direct Procurement with ID {direct_id} does not exist'})
            except Exception as e:
                raise serializers.ValidationError({'direct_id': f'Error fetching Direct Procurement: {str(e)}'})
        elif 'direct' not in data or data.get('direct') is None:
            # If neither direct_id nor direct is provided, make it optional for now
            # The view will handle setting it if needed
            pass
        
        # Validate weight_percentage
        if 'weight_percentage' in data:
            weight = data['weight_percentage']
            if weight < 0 or weight > 100:
                raise serializers.ValidationError(
                    {"weight_percentage": "Weight must be between 0 and 100"}
                )
        
        return data


class DirectProcurementSerializer(AutoDecryptingModelSerializer):
    """Serializer for Direct Procurement model"""
    evaluation_criteria = DirectEvaluationCriteriaSerializer(many=True, required=False)
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = DirectProcurement
        fields = [
            'direct_id', 'direct_number', 'direct_title', 'description', 'direct_type',
            'category', 'estimated_value', 'currency', 'issue_date',
            'submission_deadline', 'evaluation_period_end', 'award_date',
            'status', 'created_by', 'approved_by', 'primary_reviewer_id',
            'executive_reviewer_id', 'version_number', 'auto_approve',
            'allow_late_submissions', 'created_at', 'updated_at',
            'approval_workflow_id', 'evaluation_method', 'budget_range_min',
            'budget_range_max', 'criticality_level', 'geographical_scope',
            'compliance_requirements', 'custom_fields', 'final_evaluation_score',
            'award_decision_date', 'award_justification', 'documents', 'evaluation_criteria',
            'data_inventory', 'retentionExpiry', 'direct_justification', 'vendor_id'
        ]
        read_only_fields = ['direct_id', 'direct_number', 'created_by', 'created_at', 'updated_at']
    
    def validate_data_inventory(self, value):
        if not isinstance(value, dict):
            return {}
        return value


class DirectProcurementCreateSerializer(AutoDecryptingModelSerializer):
    """Serializer for creating Direct Procurement"""
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    created_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = DirectProcurement
        fields = [
            'direct_id', 'direct_number', 'direct_title', 'description', 'direct_type',
            'category', 'estimated_value', 'currency', 'issue_date',
            'submission_deadline', 'evaluation_period_end', 'award_date',
            'status', 'created_by', 'approved_by', 'primary_reviewer_id',
            'executive_reviewer_id', 'version_number', 'auto_approve',
            'allow_late_submissions', 'approval_workflow_id', 'evaluation_method',
            'budget_range_min', 'budget_range_max', 'criticality_level',
            'geographical_scope', 'compliance_requirements', 'custom_fields',
            'data_inventory', 'retentionExpiry', 'documents', 'direct_justification', 'vendor_id'
        ]
        read_only_fields = ['direct_id', 'direct_number', 'created_by']


class DirectProcurementListSerializer(AutoDecryptingModelSerializer):
    """Simplified serializer for Direct Procurement list view"""
    
    class Meta:
        model = DirectProcurement
        fields = [
            'direct_id', 'direct_number', 'direct_title', 'description', 'direct_type',
            'status', 'created_at', 'submission_deadline', 'criticality_level',
            'created_by', 'budget_range_min', 'budget_range_max', 'category'
        ]
