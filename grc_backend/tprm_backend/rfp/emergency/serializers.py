from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import EmergencyProcurement, EmergencyEvaluationCriteria


class EmergencyEvaluationCriteriaSerializer(AutoDecryptingModelSerializer):
    """Serializer for Emergency Procurement Evaluation Criteria"""
    emergency_id = serializers.IntegerField(write_only=True, required=False)
    emergency = serializers.PrimaryKeyRelatedField(queryset=EmergencyProcurement.objects.all(), required=False, allow_null=True)
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    created_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = EmergencyEvaluationCriteria
        fields = [
            'criteria_id', 'emergency_id', 'emergency', 'criteria_name', 'criteria_description', 
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
    
    def get_emergency_id(self, obj):
        try:
            if hasattr(obj, 'emergency_id'):
                return obj.emergency_id
            elif hasattr(obj, 'emergency') and obj.emergency:
                return obj.emergency.emergency_id
        except Exception:
            pass
        return None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['emergency_id'] = self.get_emergency_id(instance)
        return representation
    
    def validate(self, data):
        """Validate evaluation criteria data and convert emergency_id to emergency"""
        # Convert emergency_id to emergency if emergency_id is provided but emergency is not
        emergency_id = data.pop('emergency_id', None)
        if emergency_id is not None:
            try:
                from .models import EmergencyProcurement
                emergency_obj = EmergencyProcurement.objects.get(emergency_id=emergency_id)
                data['emergency'] = emergency_obj
            except EmergencyProcurement.DoesNotExist:
                raise serializers.ValidationError({'emergency_id': f'Emergency Procurement with ID {emergency_id} does not exist'})
            except Exception as e:
                raise serializers.ValidationError({'emergency_id': f'Error fetching Emergency Procurement: {str(e)}'})
        elif 'emergency' not in data or data.get('emergency') is None:
            # If neither emergency_id nor emergency is provided, make it optional for now
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


class EmergencyProcurementSerializer(AutoDecryptingModelSerializer):
    """Serializer for Emergency Procurement model"""
    evaluation_criteria = EmergencyEvaluationCriteriaSerializer(many=True, required=False)
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = EmergencyProcurement
        fields = [
            'emergency_id', 'emergency_number', 'emergency_title', 'description', 'emergency_type',
            'category', 'estimated_value', 'currency', 'issue_date',
            'submission_deadline', 'evaluation_period_end', 'award_date',
            'status', 'created_by', 'approved_by', 'primary_reviewer_id',
            'executive_reviewer_id', 'version_number', 'auto_approve',
            'allow_late_submissions', 'created_at', 'updated_at',
            'approval_workflow_id', 'evaluation_method', 'budget_range_min',
            'budget_range_max', 'criticality_level', 'geographical_scope',
            'compliance_requirements', 'custom_fields', 'final_evaluation_score',
            'award_decision_date', 'award_justification', 'documents', 'evaluation_criteria',
            'data_inventory', 'retentionExpiry', 'emergency_justification',
            'emergency_type_category', 'urgency_level', 'required_delivery_date', 'impact_description'
        ]
        read_only_fields = ['emergency_id', 'emergency_number', 'created_by', 'created_at', 'updated_at']
    
    def validate_data_inventory(self, value):
        if not isinstance(value, dict):
            return {}
        return value


class EmergencyProcurementCreateSerializer(AutoDecryptingModelSerializer):
    """Serializer for creating Emergency Procurement"""
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    created_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = EmergencyProcurement
        fields = [
            'emergency_id', 'emergency_number', 'emergency_title', 'description', 'emergency_type',
            'category', 'estimated_value', 'currency', 'issue_date',
            'submission_deadline', 'evaluation_period_end', 'award_date',
            'status', 'created_by', 'approved_by', 'primary_reviewer_id',
            'executive_reviewer_id', 'version_number', 'auto_approve',
            'allow_late_submissions', 'approval_workflow_id', 'evaluation_method',
            'budget_range_min', 'budget_range_max', 'criticality_level',
            'geographical_scope', 'compliance_requirements', 'custom_fields',
            'data_inventory', 'retentionExpiry', 'documents', 'emergency_justification',
            'emergency_type_category', 'urgency_level', 'required_delivery_date', 'impact_description'
        ]
        read_only_fields = ['emergency_id', 'emergency_number', 'created_by']


class EmergencyProcurementListSerializer(AutoDecryptingModelSerializer):
    """Simplified serializer for Emergency Procurement list view"""
    
    class Meta:
        model = EmergencyProcurement
        fields = [
            'emergency_id', 'emergency_number', 'emergency_title', 'description', 'emergency_type',
            'status', 'created_at', 'submission_deadline', 'criticality_level',
            'created_by', 'budget_range_min', 'budget_range_max', 'category', 'urgency_level'
        ]
