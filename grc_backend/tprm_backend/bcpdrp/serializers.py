"""
Django REST Framework serializers for BCP/DRP API
"""
from rest_framework import serializers
from .models import Plan, Questionnaire, Question, Users


# =============================================================================
# PLAN SERIALIZERS
# =============================================================================

class PlanListSerializer(serializers.ModelSerializer):
    """Serializer for listing plans with basic information"""
    vendor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = [
            'plan_id', 'vendor_id', 'strategy_id', 'strategy_name', 
            'plan_type', 'plan_name', 'vendor_name', 'status', 
            'criticality', 'plan_scope', 'submitted_at'
        ]
    
    def get_vendor_name(self, obj):
        return f"Vendor {obj.vendor_id}"


class PlanCreateSerializer(serializers.Serializer):
    """Serializer for creating a new plan"""
    
    vendor_id = serializers.IntegerField(required=True)
    strategy_id = serializers.IntegerField(required=False, allow_null=True)
    strategy_name = serializers.CharField(max_length=255, required=True)
    plan_type = serializers.CharField(max_length=45, required=True)  # Validated against dropdown values in view
    plan_name = serializers.CharField(max_length=255, required=True)
    version = serializers.CharField(max_length=32, required=False, default='1.0')
    document_date = serializers.DateField(required=False, allow_null=True)
    file_uri = serializers.CharField(max_length=1024, required=True)
    mime_type = serializers.CharField(max_length=128, required=False, allow_null=True)
    sha256_checksum = serializers.CharField(max_length=64, required=False, allow_null=True)
    size_bytes = serializers.IntegerField(required=False, allow_null=True)
    plan_scope = serializers.ChoiceField(
        choices=['cloud', 'physical_server', 'physical_device', 'application', 'network', 'other'],
        required=True
    )
    criticality = serializers.ChoiceField(
        choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        required=False,
        default='MEDIUM'
    )


class PlanUpdateSerializer(serializers.Serializer):
    """Serializer for updating a plan"""
    
    plan_name = serializers.CharField(max_length=255, required=False)
    version = serializers.CharField(max_length=32, required=False)
    document_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=[
            'SUBMITTED', 'OCR_IN_PROGRESS', 'OCR_COMPLETED', 'ASSIGNED_FOR_EVALUATION',
            'UNDER_EVALUATION', 'APPROVED', 'REJECTED', 'REVISION_REQUESTED'
        ],
        required=False
    )
    criticality = serializers.ChoiceField(
        choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        required=False
    )
    rejection_reason = serializers.CharField(required=False, allow_null=True)


# =============================================================================
# BCP/DRP DETAILS SERIALIZERS
# =============================================================================

class BcpDetailsSerializer(serializers.Serializer):
    """Serializer for BCP extracted details"""
    
    purpose_scope = serializers.CharField(required=False, allow_null=True)
    regulatory_references = serializers.JSONField(required=False, allow_null=True)
    critical_services = serializers.JSONField(required=False, allow_null=True)
    dependencies_internal = serializers.JSONField(required=False, allow_null=True)
    dependencies_external = serializers.JSONField(required=False, allow_null=True)
    risk_assessment_summary = serializers.CharField(required=False, allow_null=True)
    bia_summary = serializers.CharField(required=False, allow_null=True)
    rto_targets = serializers.JSONField(required=False, allow_null=True)
    rpo_targets = serializers.JSONField(required=False, allow_null=True)
    incident_types = serializers.JSONField(required=False, allow_null=True)
    alternate_work_locations = serializers.JSONField(required=False, allow_null=True)
    communication_plan_internal = serializers.CharField(required=False, allow_null=True)
    communication_plan_bank = serializers.CharField(required=False, allow_null=True)
    roles_responsibilities = serializers.JSONField(required=False, allow_null=True)
    training_testing_schedule = serializers.CharField(required=False, allow_null=True)
    maintenance_review_cycle = serializers.CharField(required=False, allow_null=True)
    extractor_version = serializers.CharField(max_length=32, required=False, allow_null=True)


class DrpDetailsSerializer(serializers.Serializer):
    """Serializer for DRP extracted details"""
    
    purpose_scope = serializers.CharField(required=False, allow_null=True)
    regulatory_references = serializers.JSONField(required=False, allow_null=True)
    critical_systems = serializers.JSONField(required=False, allow_null=True)
    critical_applications = serializers.JSONField(required=False, allow_null=True)
    databases_list = serializers.JSONField(required=False, allow_null=True)
    supporting_infrastructure = serializers.JSONField(required=False, allow_null=True)
    third_party_services = serializers.JSONField(required=False, allow_null=True)
    rto_targets = serializers.JSONField(required=False, allow_null=True)
    rpo_targets = serializers.JSONField(required=False, allow_null=True)
    disaster_scenarios = serializers.JSONField(required=False, allow_null=True)
    disaster_declaration_process = serializers.CharField(required=False, allow_null=True)
    data_backup_strategy = serializers.CharField(required=False, allow_null=True)
    recovery_site_details = serializers.CharField(required=False, allow_null=True)
    failover_procedures = serializers.CharField(required=False, allow_null=True)
    failback_procedures = serializers.CharField(required=False, allow_null=True)
    network_recovery_steps = serializers.CharField(required=False, allow_null=True)
    application_restoration_order = serializers.JSONField(required=False, allow_null=True)
    testing_validation_schedule = serializers.CharField(required=False, allow_null=True)
    maintenance_review_cycle = serializers.CharField(required=False, allow_null=True)
    extractor_version = serializers.CharField(max_length=32, required=False, allow_null=True)


# =============================================================================
# EVALUATION SERIALIZERS
# =============================================================================

class EvaluationCreateSerializer(serializers.Serializer):
    """Serializer for creating a new evaluation"""
    
    plan_id = serializers.IntegerField(required=True)
    assigned_to_user_id = serializers.IntegerField(required=True)
    assigned_by_user_id = serializers.IntegerField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)


class EvaluationUpdateSerializer(serializers.Serializer):
    """Serializer for updating an evaluation"""
    
    status = serializers.ChoiceField(
        choices=['ASSIGNED', 'IN_PROGRESS', 'SUBMITTED', 'REVIEWED', 'CLOSED'],
        required=False
    )
    started_at = serializers.DateTimeField(required=False, allow_null=True)
    submitted_at = serializers.DateTimeField(required=False, allow_null=True)
    reviewed_by_user_id = serializers.IntegerField(required=False, allow_null=True)
    reviewed_at = serializers.DateTimeField(required=False, allow_null=True)
    overall_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    quality_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    coverage_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    recovery_capability_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    compliance_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    weighted_score = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True)
    criteria_json = serializers.JSONField(required=False, allow_null=True)
    evaluator_comments = serializers.CharField(required=False, allow_null=True)


# =============================================================================
# VENDOR SERIALIZERS (if needed)
# =============================================================================

class VendorSerializer(serializers.Serializer):
    """Serializer for vendor data"""
    
    vendor_id = serializers.IntegerField(read_only=True)
    vendor_name = serializers.CharField(max_length=255)
    contact_email = serializers.EmailField(required=False, allow_null=True)
    contact_phone = serializers.CharField(max_length=20, required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


# =============================================================================
# QUESTIONNAIRE SERIALIZERS
# =============================================================================

class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for individual questions"""
    
    class Meta:
        model = Question
        fields = [
            'question_id', 'questionnaire_id', 'seq_no', 'question_text', 
            'answer_type', 'is_required', 'weight'
        ]


class QuestionnaireListSerializer(serializers.ModelSerializer):
    """Serializer for listing questionnaires with basic information"""
    question_count = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Questionnaire
        fields = [
            'questionnaire_id', 'version', 'title', 'description',
            'plan_type', 'plan_id', 'status', 'question_count', 'owner_name',
            'created_by_user_id', 'approved_at'
        ]
    
    def get_question_count(self, obj):
        """Get the count of questions for this questionnaire"""
        return Question.objects.filter(questionnaire_id=obj.questionnaire_id).count()
    
    def get_owner_name(self, obj):
        """Get owner name (placeholder - in real app would join with user table)"""
        return f"Owner {obj.created_by_user_id}"


class QuestionnaireDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed questionnaire information"""
    questions = QuestionSerializer(many=True, read_only=True)
    owner_name = serializers.SerializerMethodField()
    reviewer_name = serializers.SerializerMethodField()
    approver_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Questionnaire
        fields = [
            'questionnaire_id', 'version', 'previous_questionnaire_id',
            'title', 'description', 'plan_type', 'plan_id', 'status', 'created_by_user_id',
            'reviewer_user_id', 'reviewer_comment', 'approved_by_user_id', 'approved_at',
            'questions', 'owner_name', 'reviewer_name', 'approver_name'
        ]
    
    def get_owner_name(self, obj):
        """Get owner name (placeholder - in real app would join with user table)"""
        return f"Owner {obj.created_by_user_id}"
    
    def get_reviewer_name(self, obj):
        """Get reviewer name (placeholder - in real app would join with user table)"""
        return f"Reviewer {obj.reviewer_user_id}" if obj.reviewer_user_id else None
    
    def get_approver_name(self, obj):
        """Get approver name (placeholder - in real app would join with user table)"""
        return f"Approver {obj.approved_by_user_id}" if obj.approved_by_user_id else None


class QuestionnaireCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new questionnaire"""
    
    class Meta:
        model = Questionnaire
        fields = [
            'version', 'previous_questionnaire_id', 'title', 'description',
            'plan_type', 'created_by_user_id', 'status', 'reviewer_user_id'
        ]


class QuestionnaireUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a questionnaire"""
    
    class Meta:
        model = Questionnaire
        fields = [
            'title', 'description', 'status', 'reviewer_user_id', 'approved_by_user_id'
        ]


# =============================================================================
# AUTHENTICATION SERIALIZERS
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    
    class Meta:
        model = Users
        fields = [
            'user_id', 'user_name', 'email', 'first_name', 'last_name',
            'is_active', 'department_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'updated_at']


