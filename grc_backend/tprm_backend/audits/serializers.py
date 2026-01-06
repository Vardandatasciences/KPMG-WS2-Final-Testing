"""
Serializers for the Audits app.
"""
from rest_framework import serializers
from .models import Audit, StaticQuestionnaire, AuditVersion, AuditFinding, AuditReport
from tprm_backend.slas.models import VendorSLA
from tprm_backend.slas.serializers import VendorSLASerializer, SLAMetricSerializer


class StaticQuestionnaireSerializer(serializers.ModelSerializer):
    """Serializer for StaticQuestionnaire model."""
    
    class Meta:
        model = StaticQuestionnaire
        fields = [
            'question_id', 'metric_name', 'question_text', 'question_type',
            'is_required', 'scoring_weightings', 'created_at'
        ]
        read_only_fields = ['question_id', 'created_at']


class AuditVersionSerializer(serializers.ModelSerializer):
    """Serializer for AuditVersion model."""
    
    class Meta:
        model = AuditVersion
        fields = [
            'version_id', 'audit_id', 'version_type', 'version_number',
            'extended_information', 'user_id', 'approval_status', 'date_created',
            'is_active', 'created_at'
        ]
        read_only_fields = ['version_id', 'date_created', 'created_at']


class AuditFindingSerializer(serializers.ModelSerializer):
    """Serializer for AuditFinding model."""
    
    class Meta:
        model = AuditFinding
        fields = [
            'audit_finding_id', 'audit_id', 'metrics_id', 'evidence', 'user_id',
            'how_to_verify', 'impact_recommendations', 'details_of_finding',
            'comment', 'check_date', 'questionnaire_responses', 'created_at', 'updated_at'
        ]
        read_only_fields = ['audit_finding_id', 'created_at', 'updated_at']


class AuditReportSerializer(serializers.ModelSerializer):
    """Serializer for AuditReport model."""
    
    class Meta:
        model = AuditReport
        fields = [
            'report_id', 'audit_id', 'report_link', 'sla_id', 'metrics_id', 'generated_at'
        ]
        read_only_fields = ['report_id', 'generated_at']


class AuditSerializer(serializers.ModelSerializer):
    """Serializer for Audit model."""
    sla_id = serializers.IntegerField(read_only=True)
    sla_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Audit
        fields = [
            'audit_id', 'title', 'scope', 'assignee_id', 'auditor_id', 'assign_date',
            'due_date', 'frequency', 'status', 'completion_date', 'reviewer_id',
            'metric_id', 'sla_id', 'sla_name', 'review_status', 'review_comments',
            'audit_type', 'evidence_comments', 'review_start_date', 'review_date',
            'reports_objective', 'business_unit', 'role', 'responsibility',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['audit_id', 'created_at', 'updated_at']
    
    def get_sla_name(self, obj):
        """Get SLA name from sla_id using cross-database lookup."""
        if obj.sla_id:
            try:
                from slas.models import VendorSLA
                sla = VendorSLA.objects.get(sla_id=obj.sla_id)
                return sla.sla_name
            except:
                return "Unknown SLA"
        return None


class AuditCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating audits."""
    sla_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Audit
        fields = [
            'title', 'scope', 'assignee_id', 'auditor_id', 'reviewer_id', 'assign_date',
            'due_date', 'frequency', 'audit_type', 'status', 'review_status', 'sla_id'
        ]
    
    def create(self, validated_data):
        # Extract sla_id and store as integer (not ForeignKey due to cross-database routing)
        sla_id = validated_data.pop('sla_id')
        
        # Set assign_date to today if not provided
        from django.utils import timezone
        if 'assign_date' not in validated_data or not validated_data['assign_date']:
            validated_data['assign_date'] = timezone.now().date()
        
        # Set default status if not provided
        if 'status' not in validated_data:
            validated_data['status'] = 'created'
        
        # Set default review_status if not provided
        if 'review_status' not in validated_data:
            validated_data['review_status'] = 'pending'
        
        # Validate that the SLA exists (but don't create ForeignKey relationship)
        try:
            from slas.models import VendorSLA
            VendorSLA.objects.get(sla_id=sla_id)
        except VendorSLA.DoesNotExist:
            raise serializers.ValidationError(f"SLA with ID {sla_id} does not exist")
        
        # Store sla_id as integer in the database (bypassing ForeignKey due to cross-database routing)
        # We'll use raw SQL to insert the sla_id directly
        from django.db import connections
        
        # Create the audit object without the sla field using the correct database
        audit = Audit.objects.create(**validated_data)
        
        # Update the sla_id directly using raw SQL to bypass the ForeignKey constraint
        with connections['default'].cursor() as cursor:
            cursor.execute(
                "UPDATE audits SET sla_id = %s WHERE audit_id = %s",
                [sla_id, audit.audit_id]
            )
        
        # Refresh the audit object to get the updated sla_id
        audit.refresh_from_db()
        
        return audit


class AuditListSerializer(serializers.ModelSerializer):
    """Simplified serializer for audit lists."""
    sla_name = serializers.SerializerMethodField()
    sla_type = serializers.SerializerMethodField()
    auditor_name = serializers.SerializerMethodField()
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Audit
        fields = [
            'audit_id', 'title', 'scope', 'sla_id', 'sla_name', 'sla_type', 'status',
            'due_date', 'frequency', 'audit_type', 'auditor_id', 'reviewer_id',
            'auditor_name', 'reviewer_name', 'created_at', 'updated_at'
        ]
    
    def get_sla_name(self, obj):
        """Get SLA name from sla_id using cross-database lookup."""
        if obj.sla_id:
            try:
                from slas.models import VendorSLA
                sla = VendorSLA.objects.get(sla_id=obj.sla_id)
                return sla.sla_name
            except:
                return "Unknown SLA"
        return None
    
    def get_sla_type(self, obj):
        """Get SLA type from sla_id using cross-database lookup."""
        if obj.sla_id:
            try:
                from slas.models import VendorSLA
                sla = VendorSLA.objects.get(sla_id=obj.sla_id)
                return sla.sla_type
            except:
                return "Unknown Type"
        return None
    
    def get_auditor_name(self, obj):
        """Get auditor name from user ID."""
        if obj.auditor_id:
            try:
                # This would need to be connected to your user system
                # For now, return the ID as a string
                return f"User {obj.auditor_id}"
            except:
                return "Unknown"
        return None
    
    def get_reviewer_name(self, obj):
        """Get reviewer name from user ID."""
        if obj.reviewer_id:
            try:
                # This would need to be connected to your user system
                # For now, return the ID as a string
                return f"User {obj.reviewer_id}"
            except:
                return "Unknown"
        return None
