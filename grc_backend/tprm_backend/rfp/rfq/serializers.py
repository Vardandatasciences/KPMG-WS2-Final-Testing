from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import RFQ, RFQEvaluationCriteria


class RFQEvaluationCriteriaSerializer(AutoDecryptingModelSerializer):
    """Serializer for RFQ Evaluation Criteria"""
    rfq_id = serializers.IntegerField(write_only=True, required=False)
    rfq = serializers.PrimaryKeyRelatedField(queryset=RFQ.objects.all(), required=False, allow_null=True)
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    created_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = RFQEvaluationCriteria
        fields = [
            'criteria_id', 'rfq_id', 'rfq', 'criteria_name', 'criteria_description', 
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
    
    def get_rfq_id(self, obj):
        try:
            if hasattr(obj, 'rfq_id'):
                return obj.rfq_id
            elif hasattr(obj, 'rfq') and obj.rfq:
                return obj.rfq.rfq_id
        except Exception:
            pass
        return None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['rfq_id'] = self.get_rfq_id(instance)
        return representation
    
    def validate(self, data):
        """Validate evaluation criteria data and convert rfq_id to rfq"""
        # Convert rfq_id to rfq if rfq_id is provided but rfq is not
        rfq_id = data.pop('rfq_id', None)
        if rfq_id is not None:
            try:
                from .models import RFQ
                rfq_obj = RFQ.objects.get(rfq_id=rfq_id)
                data['rfq'] = rfq_obj
            except RFQ.DoesNotExist:
                raise serializers.ValidationError({'rfq_id': f'RFQ with ID {rfq_id} does not exist'})
            except Exception as e:
                raise serializers.ValidationError({'rfq_id': f'Error fetching RFQ: {str(e)}'})
        elif 'rfq' not in data or data.get('rfq') is None:
            # If neither rfq_id nor rfq is provided, make it optional for now
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


class RFQSerializer(AutoDecryptingModelSerializer):
    """Serializer for RFQ model"""
    evaluation_criteria = RFQEvaluationCriteriaSerializer(many=True, required=False)
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = RFQ
        fields = [
            'rfq_id', 'rfq_number', 'rfq_title', 'description', 'rfq_type',
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
        read_only_fields = ['rfq_id', 'rfq_number', 'created_at', 'updated_at']
    
    def validate_data_inventory(self, value):
        if not isinstance(value, dict):
            return {}
        return value


class RFQCreateSerializer(AutoDecryptingModelSerializer):
    """Serializer for creating RFQ"""
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    created_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = RFQ
        fields = [
            'rfq_id', 'rfq_number', 'rfq_title', 'description', 'rfq_type',
            'category', 'estimated_value', 'currency', 'issue_date',
            'submission_deadline', 'evaluation_period_end', 'award_date',
            'status', 'created_by', 'approved_by', 'primary_reviewer_id',
            'executive_reviewer_id', 'version_number', 'auto_approve',
            'allow_late_submissions', 'approval_workflow_id', 'evaluation_method',
            'budget_range_min', 'budget_range_max', 'criticality_level',
            'geographical_scope', 'compliance_requirements', 'custom_fields',
            'data_inventory', 'retentionExpiry', 'documents'
        ]
        read_only_fields = ['rfq_id', 'rfq_number', 'created_by']


class RFQListSerializer(AutoDecryptingModelSerializer):
    """Simplified serializer for RFQ list view"""
    
    class Meta:
        model = RFQ
        fields = [
            'rfq_id', 'rfq_number', 'rfq_title', 'status', 'created_at',
            'submission_deadline', 'criticality_level', 'created_by'
        ]
