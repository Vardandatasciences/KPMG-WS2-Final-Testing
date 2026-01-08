from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.models import User
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import RFP, RFPEvaluationCriteria, CustomUser, RFPTypeCustomFields
from .validators import validate_rfp_data


class UserSerializer(AutoDecryptingModelSerializer):
    """Serializer for User model (for reviewer information)"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = fields


class CustomUserSerializer(AutoDecryptingModelSerializer):
    """Serializer for CustomUser model"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 'is_active', 
                 'department_id', 'full_name']
        read_only_fields = ['user_id', 'password', 'created_at', 'updated_at', 
                           'session_token', 'consent_accepted', 'license_key']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class RFPEvaluationCriteriaSerializer(AutoDecryptingModelSerializer):
    """Serializer for RFP Evaluation Criteria"""
    rfp_id = serializers.SerializerMethodField()
    
    class Meta:
        model = RFPEvaluationCriteria
        fields = [
            'criteria_id', 'rfp_id', 'rfp', 'criteria_name', 'criteria_description', 
            'weight_percentage', 'evaluation_type', 'min_score', 
            'max_score', 'median_score', 'is_mandatory', 
            'veto_enabled', 'veto_threshold', 'min_word_count',
            'expected_boolean_answer', 'display_order', 'created_by'
        ]
        read_only_fields = ['criteria_id', 'rfp_id', 'created_by']  # created_by is set by perform_create
    
    def get_rfp_id(self, obj):
        """Get rfp_id from ForeignKey relationship or directly from the object"""
        try:
            # First try: Django automatically provides rfp_id from ForeignKey
            if hasattr(obj, 'rfp_id'):
                return obj.rfp_id
            # Second try: Get from ForeignKey relationship
            elif hasattr(obj, 'rfp') and obj.rfp:
                return obj.rfp.rfp_id
            # Last resort: query database directly
            else:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT rfp_id FROM rfp_evaluation_criteria 
                        WHERE criteria_id = %s
                    """, [obj.criteria_id])
                    row = cursor.fetchone()
                    if row:
                        return row[0]
        except Exception as e:
            print(f"⚠️ Error getting rfp_id for criteria {obj.criteria_id}: {e}")
            import traceback
            print(traceback.format_exc())
        return None
    
    def validate(self, data):
        """Validate evaluation criteria data"""
        if 'weight_percentage' in data:
            weight = data['weight_percentage']
            if weight < 0 or weight > 100:
                raise serializers.ValidationError(
                    {"weight_percentage": "Weight must be between 0 and 100"}
                )
        
        if 'min_score' in data and 'max_score' in data:
            min_score = data['min_score']
            max_score = data['max_score']
            if min_score is not None and max_score is not None and min_score > max_score:
                raise serializers.ValidationError(
                    {"min_score": "Minimum score cannot be greater than maximum score"}
                )
        
        return data




class RFPSerializer(AutoDecryptingModelSerializer):
    """Serializer for RFP model"""
    evaluation_criteria = RFPEvaluationCriteriaSerializer(many=True, required=False)
    created_by_details = serializers.SerializerMethodField()
    approved_by_details = serializers.SerializerMethodField()
    primary_reviewer_details = serializers.SerializerMethodField()
    executive_reviewer_details = serializers.SerializerMethodField()
    
    class Meta:
        model = RFP
        fields = [
            'rfp_id', 'rfp_number', 'rfp_title', 'description', 'rfp_type',
            'category', 'estimated_value', 'currency', 'issue_date',
            'submission_deadline', 'evaluation_period_end', 'award_date',
            'status', 'created_by', 'approved_by', 'primary_reviewer_id',
            'executive_reviewer_id', 'version_number', 'auto_approved',
            'allow_late_submissions', 'created_at', 'updated_at',
            'approval_workflow_id', 'evaluation_method', 'budget_range_min',
            'budget_range_max', 'criticality_level', 'geographical_scope',
            'compliance_requirements', 'custom_fields', 'final_evaluation_score',
            'award_decision_date', 'award_justification', 'documents', 'evaluation_criteria',
            'created_by_details', 'approved_by_details', 'primary_reviewer_details',
            'executive_reviewer_details'
        ]
        read_only_fields = [
            'rfp_id', 'rfp_number', 'created_at', 'updated_at', 
            'created_by_details', 'approved_by_details', 'primary_reviewer_details',
            'executive_reviewer_details'
        ]
    
    def get_created_by_details(self, obj):
        if obj.created_by:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=obj.created_by)
                return UserSerializer(user).data
            except User.DoesNotExist:
                return None
        return None
    
    def get_approved_by_details(self, obj):
        if obj.approved_by:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=obj.approved_by)
                return UserSerializer(user).data
            except User.DoesNotExist:
                return None
        return None
    
    def get_primary_reviewer_details(self, obj):
        if obj.primary_reviewer_id:
            try:
                user = CustomUser.objects.get(user_id=obj.primary_reviewer_id)
                return CustomUserSerializer(user).data
            except CustomUser.DoesNotExist:
                return None
        return None
    
    def get_executive_reviewer_details(self, obj):
        if obj.executive_reviewer_id:
            try:
                user = CustomUser.objects.get(user_id=obj.executive_reviewer_id)
                return CustomUserSerializer(user).data
            except CustomUser.DoesNotExist:
                return None
        return None
    
    def validate(self, data):
        """
        Validate the RFP data using the validators and convert decimal fields
        """
        from decimal import Decimal
        
        # Convert decimal fields to proper Decimal type
        decimal_fields = ['estimated_value', 'budget_range_min', 'budget_range_max']
        for field in decimal_fields:
            if field in data:
                if data[field] == '' or data[field] is None:
                    data[field] = None
                else:
                    try:
                        data[field] = Decimal(str(data[field]))
                    except (TypeError, ValueError, Exception):
                        data[field] = None
        
        # Combine initial data and validated data for complete validation
        validation_data = {**self.initial_data} if hasattr(self, 'initial_data') else {}
        
        # Add any nested evaluation criteria
        if validation_data and 'evaluation_criteria' in self.initial_data:
            validation_data['evaluation_criteria'] = self.initial_data['evaluation_criteria']
        
        # Run validation (skip if no initial_data for partial updates)
        if validation_data:
            errors = validate_rfp_data(validation_data)
            
            if errors:
                raise serializers.ValidationError(errors)
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Create RFP with nested evaluation criteria and approval workflow
        """
        evaluation_criteria_data = validated_data.pop('evaluation_criteria', [])
        primary_reviewer_id = validated_data.get('primary_reviewer_id')
        executive_reviewer_id = validated_data.get('executive_reviewer_id')
        
        # Store created_by before creating RFP
        created_by = validated_data.get('created_by')
        
        # Create the RFP
        rfp = RFP.objects.create(**validated_data)
        
        # Create evaluation criteria
        for i, criterion_data in enumerate(evaluation_criteria_data):
            criterion_data = criterion_data.copy()  # Make a copy to avoid modifying the original
            criterion_data['display_order'] = i
            criterion_data['created_by'] = created_by
            RFPEvaluationCriteria.objects.create(rfp=rfp, **criterion_data)
        
        
        return rfp
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update RFP with nested evaluation criteria and approval workflow
        """
        evaluation_criteria_data = validated_data.pop('evaluation_criteria', None)
        primary_reviewer_id = validated_data.get('primary_reviewer_id', instance.primary_reviewer_id)
        executive_reviewer_id = validated_data.get('executive_reviewer_id', instance.executive_reviewer_id)
        
        # Update RFP fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update evaluation criteria if provided
        if evaluation_criteria_data is not None:
            # Delete existing criteria
            instance.evaluation_criteria.all().delete()
            
            # Create new criteria
            for i, criterion_data in enumerate(evaluation_criteria_data):
                criterion_data['display_order'] = i
                criterion_data['created_by'] = instance.created_by
                RFPEvaluationCriteria.objects.create(rfp=instance, **criterion_data)
        
        
        return instance


class RFPCreateSerializer(RFPSerializer):
    """Serializer specifically for RFP creation with validation"""
    
    def validate(self, data):
        """Additional validation for RFP creation"""
        # Print data for debugging
        print("RFPCreateSerializer validate data:", data)
        
        # Call parent validation first (which handles decimal conversion)
        data = super().validate(data)
        
        # Required fields for creation
        required_fields = ['rfp_title', 'description', 'rfp_type']
        for field in required_fields:
            if field not in data or not data.get(field):
                raise serializers.ValidationError({field: f"{field} is required"})
        
        # Convert reviewer IDs to integers
        if 'primary_reviewer_id' in data:
            if data['primary_reviewer_id'] == '' or data['primary_reviewer_id'] is None:
                data['primary_reviewer_id'] = None
            else:
                try:
                    data['primary_reviewer_id'] = int(data['primary_reviewer_id'])
                except (TypeError, ValueError):
                    data['primary_reviewer_id'] = None
            
        if 'executive_reviewer_id' in data:
            if data['executive_reviewer_id'] == '' or data['executive_reviewer_id'] is None:
                data['executive_reviewer_id'] = None
            else:
                try:
                    data['executive_reviewer_id'] = int(data['executive_reviewer_id'])
                except (TypeError, ValueError):
                    data['executive_reviewer_id'] = None
        
        return data


class RFPTypeCustomFieldsSerializer(AutoDecryptingModelSerializer):
    """Serializer for RFP Type Custom Fields"""
    class Meta:
        model = RFPTypeCustomFields
        fields = ['rfp_type_id', 'rfp_type', 'custom_fields']
        read_only_fields = ['rfp_type_id']


class RFPListSerializer(AutoDecryptingModelSerializer):
    """Simplified serializer for listing RFPs"""
    created_by_name = serializers.SerializerMethodField()
    criteria_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RFP
        fields = [
            'rfp_id', 'rfp_number', 'rfp_title', 'rfp_type', 'status', 
            'created_at', 'submission_deadline', 'created_by_name',
            'criteria_count', 'budget_range_min', 'budget_range_max',
            'estimated_value', 'created_by'
        ]
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=obj.created_by)
                return f"{user.first_name} {user.last_name}".strip() or user.username
            except Exception:
                return str(obj.created_by)
        return None
    
    def get_criteria_count(self, obj):
        try:
            return obj.evaluation_criteria.count()
        except Exception:
            return 0