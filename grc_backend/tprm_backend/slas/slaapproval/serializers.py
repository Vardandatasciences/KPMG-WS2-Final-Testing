from rest_framework import serializers
from django.utils import timezone
from .models import SLAApproval


class SLAApprovalAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for SLA approval assignment with enhanced SLA details"""
    
    sla_details = serializers.SerializerMethodField()
    assigner_details = serializers.SerializerMethodField()
    assignee_details = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    days_until_due = serializers.SerializerMethodField()
    
    class Meta:
        model = SLAApproval
        fields = [
            'approval_id', 'sla_id', 'workflow_id', 'workflow_name', 'assigner_id', 'assigner_name',
            'assignee_id', 'assignee_name', 'object_type', 'assigned_date', 'due_date', 'status',
            'priority', 'approval_status', 'comment_text', 'created_at', 'updated_at',
            'sla_details', 'assigner_details', 'assignee_details', 'is_overdue', 'days_until_due'
        ]
        read_only_fields = ['approval_id', 'created_at', 'updated_at']
    
    def get_sla_details(self, obj):
        """Get detailed SLA information"""
        sla = obj.get_sla()
        if sla:
            return {
                'sla_id': sla.sla_id,
                'sla_name': sla.sla_name,
                'sla_type': sla.sla_type,
                'vendor_id': sla.vendor_id,
                'contract_id': sla.contract_id,
                'effective_date': sla.effective_date,
                'expiry_date': sla.expiry_date,
                'status': sla.status,
                'priority': sla.priority,
                'compliance_score': sla.compliance_score,
                'business_service_impacted': sla.business_service_impacted,
                'compliance_framework': sla.compliance_framework,
                'penalty_threshold': sla.penalty_threshold,
                'credit_threshold': sla.credit_threshold,
                'reporting_frequency': sla.reporting_frequency,
                'baseline_period': sla.baseline_period,
                'measurement_methodology': sla.measurement_methodology,
                'exclusions': sla.exclusions,
                'force_majeure_clauses': sla.force_majeure_clauses,
                'audit_requirements': sla.audit_requirements,
                'document_versioning': sla.document_versioning,
                'improvement_targets': sla.improvement_targets,
                'approval_status': sla.approval_status
            }
        return None
    
    def get_assigner_details(self, obj):
        """Get assigner user details"""
        return {
            'userid': obj.assigner_id,
            'username': obj.assigner_name,
            'first_name': '',
            'last_name': '',
            'email': '',
            'full_name': obj.assigner_name
        }
    
    def get_assignee_details(self, obj):
        """Get assignee user details"""
        return {
            'userid': obj.assignee_id,
            'username': obj.assignee_name,
            'first_name': '',
            'last_name': '',
            'email': '',
            'full_name': obj.assignee_name
        }
    
    def get_is_overdue(self, obj):
        """Check if the approval is overdue"""
        return obj.is_overdue()
    
    def get_days_until_due(self, obj):
        """Calculate days until due date"""
        from django.utils import timezone
        if obj.due_date:
            delta = obj.due_date - timezone.now()
            return delta.days
        return None


class SLAApprovalCreateAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for creating SLA approval assignments"""
    
    class Meta:
        model = SLAApproval
        fields = [
            'sla_id', 'workflow_id', 'workflow_name', 'assigner_id', 'assigner_name',
            'assignee_id', 'assignee_name', 'object_type', 'assigned_date', 'due_date',
            'status', 'priority', 'approval_status', 'comment_text'
        ]
    
    def validate_sla_id(self, value):
        """Validate that the sla_id exists"""
        if value:
            try:
                from slas.models import VendorSLA
                VendorSLA.objects.get(sla_id=value)
            except:
                raise serializers.ValidationError(f"SLA with ID {value} not found")
        return value
    
    def validate_due_date(self, value):
        """Validate due date is not in the past"""
        from django.utils import timezone
        if value and value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value
    
    def validate(self, data):
        """Validate the entire approval data"""
        # Validate due_date is not before assigned_date
        if data.get('due_date') and data.get('assigned_date') and data['due_date'] < data['assigned_date']:
            raise serializers.ValidationError("Due date cannot be before assigned date")
        
        return data


class SLAApprovalBulkCreateSerializer(serializers.Serializer):
    """Serializer for creating multiple SLA approvals at once"""
    
    sla_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of SLA IDs to create approvals for"
    )
    workflow_id = serializers.IntegerField()
    workflow_name = serializers.CharField(max_length=255)
    assigner_id = serializers.IntegerField()
    assigner_name = serializers.CharField(max_length=255)
    assignee_id = serializers.IntegerField()
    assignee_name = serializers.CharField(max_length=255)
    object_type = serializers.ChoiceField(choices=SLAApproval.OBJECT_TYPE_CHOICES)
    due_date = serializers.DateTimeField()
    priority = serializers.ChoiceField(choices=SLAApproval.PRIORITY_CHOICES, default='MEDIUM')
    comment_text = serializers.CharField(required=False, allow_blank=True)
    
    def validate_sla_ids(self, value):
        """Validate that all SLA IDs exist"""
        if not value:
            raise serializers.ValidationError("At least one SLA ID is required")
        
        # Check if all SLAs exist
        for sla_id in value:
            try:
                from slas.models import VendorSLA
                VendorSLA.objects.get(sla_id=sla_id)
            except:
                raise serializers.ValidationError(f"SLA with ID {sla_id} not found")
        
        return value
    
    def create(self, validated_data):
        """Create multiple SLA approvals"""
        sla_ids = validated_data.pop('sla_ids')
        approvals = []
        
        for sla_id in sla_ids:
            approval_data = validated_data.copy()
            approval_data['sla_id'] = sla_id
            approval_data['assigned_date'] = timezone.now()
            approval_data['status'] = 'ASSIGNED'
            
            approval = SLAApproval.objects.create(**approval_data)
            approvals.append(approval)
        
        return approvals


class SLAApprovalStatsSerializer(serializers.Serializer):
    """Serializer for SLA approval statistics"""
    
    total_approvals = serializers.IntegerField()
    pending_approvals = serializers.IntegerField()
    overdue_approvals = serializers.IntegerField()
    completed_approvals = serializers.IntegerField()
    approvals_by_status = serializers.DictField()
    approvals_by_type = serializers.DictField()
    approvals_by_assignee = serializers.DictField()
    average_completion_time = serializers.FloatField()
    overdue_percentage = serializers.FloatField()