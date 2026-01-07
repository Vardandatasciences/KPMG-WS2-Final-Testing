"""
Vendor Questionnaire Serializers
"""

from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import Questionnaires, QuestionnaireQuestions, QuestionnaireAssignments, QuestionnaireResponseSubmissions
from tprm_backend.apps.vendor_core.models import TempVendor


class QuestionnaireQuestionSerializer(AutoDecryptingModelSerializer):
    """Serializer for individual questionnaire questions"""
    
    class Meta:
        model = QuestionnaireQuestions
        fields = [
            'question_id',
            'question_text',
            'question_type', 
            'question_category',
            'is_required',
            'display_order',
            'scoring_weight',
            'options',
            'conditional_logic',
            'help_text'
        ]
        read_only_fields = ['question_id']


class QuestionnaireSerializer(AutoDecryptingModelSerializer):
    """Serializer for questionnaires with nested questions"""
    
    questions = QuestionnaireQuestionSerializer(many=True, required=False)
    vendor_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Questionnaires
        fields = [
            'questionnaire_id',
            'questionnaire_name',
            'questionnaire_type',
            'description',
            'vendor_category_id',
            'vendor_id',
            'version',
            'status',
            'created_by',
            'created_at',
            'updated_at',
            'questions'
        ]
        read_only_fields = ['questionnaire_id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create questionnaire with nested questions"""
        questions_data = validated_data.pop('questions', [])
        # Keep vendor_id as it's now a field in the model
        print(f"DEBUG - QuestionnaireSerializer.create() validated_data: {validated_data}")
        questionnaire = Questionnaires.objects.create(**validated_data)
        
        for question_data in questions_data:
            QuestionnaireQuestions.objects.create(
                questionnaire=questionnaire,
                **question_data
            )
        
        return questionnaire
    
    def update(self, instance, validated_data):
        """Update questionnaire and its questions"""
        questions_data = validated_data.pop('questions', [])
        # Keep vendor_id as it's now a field in the model
        print(f"DEBUG - QuestionnaireSerializer.update() validated_data: {validated_data}")
        
        # Update questionnaire fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle questions update
        if questions_data:
            # Delete existing questions and create new ones
            # This is a simple approach - could be optimized for partial updates
            instance.questions.all().delete()
            
            for question_data in questions_data:
                QuestionnaireQuestions.objects.create(
                    questionnaire=instance,
                    **question_data
                )
        
        return instance


class QuestionnaireListSerializer(AutoDecryptingModelSerializer):
    """Simplified serializer for questionnaire list view"""
    
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Questionnaires
        fields = [
            'questionnaire_id',
            'questionnaire_name',
            'questionnaire_type',
            'description',
            'vendor_category_id',
            'version',
            'status',
            'created_at',
            'updated_at',
            'question_count'
        ]
    
    def get_question_count(self, obj):
        """Get the number of questions in this questionnaire"""
        return obj.questions.count()


class QuestionnaireCreateSerializer(AutoDecryptingModelSerializer):
    """Serializer for creating questionnaires (without questions initially)"""
    
    vendor_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Questionnaires
        fields = [
            'questionnaire_id',
            'questionnaire_name',
            'questionnaire_type',
            'description', 
            'vendor_category_id',
            'vendor_id',
            'version',
            'status',
            'created_by',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['questionnaire_id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create questionnaire with vendor_id"""
        # Keep vendor_id as it's now a field in the model
        print(f"DEBUG - QuestionnaireCreateSerializer.create() validated_data: {validated_data}")
        print(f"DEBUG - vendor_id in validated_data: {validated_data.get('vendor_id')}")
        print(f"DEBUG - vendor_id type: {type(validated_data.get('vendor_id'))}")
        
        # Create the questionnaire
        questionnaire = super().create(validated_data)
        
        print(f"DEBUG - Created questionnaire ID: {questionnaire.questionnaire_id}")
        print(f"DEBUG - Created questionnaire vendor_id: {questionnaire.vendor_id}")
        
        return questionnaire


class QuestionnaireAssignmentSerializer(AutoDecryptingModelSerializer):
    """Serializer for questionnaire assignments"""
    
    vendor_name = serializers.CharField(source='temp_vendor.company_name', read_only=True)
    questionnaire_name = serializers.CharField(source='questionnaire.questionnaire_name', read_only=True)
    
    class Meta:
        model = QuestionnaireAssignments
        fields = [
            'assignment_id',
            'temp_vendor',
            'questionnaire',
            'vendor_name',
            'questionnaire_name',
            'assigned_date',
            'due_date',
            'status',
            'submission_date',
            'completion_date',
            'overall_score',
            'assigned_by',
            'notes',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['assignment_id', 'assigned_date', 'created_at', 'updated_at']


class QuestionnaireResponseSerializer(AutoDecryptingModelSerializer):
    """Serializer for questionnaire responses"""
    
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)
    is_required = serializers.BooleanField(source='question.is_required', read_only=True)
    
    class Meta:
        model = QuestionnaireResponseSubmissions
        fields = [
            'response_id',
            'assignment',
            'question',
            'question_text',
            'question_type',
            'is_required',
            'vendor_response',
            'vendor_comment',
            'reviewer_comment',
            'is_completed',
            'score',
            'file_uploads',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['response_id', 'created_at', 'updated_at']