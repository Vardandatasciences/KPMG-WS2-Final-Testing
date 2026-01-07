from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from tprm_backend.mfa_auth.models import User
from tprm_backend.contracts.models import ContractApproval, VendorContract, ContractAmendment, ContractRenewal


class ContractApprovalAssignmentSerializer(AutoDecryptingModelSerializer):
    """Serializer for contract approval assignment with enhanced contract details"""
    
    contract_details = serializers.SerializerMethodField()
    assigner_details = serializers.SerializerMethodField()
    assignee_details = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    days_until_due = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractApproval
        fields = [
            'approval_id', 'workflow_id', 'workflow_name', 'assigner_id', 'assigner_name',
            'assignee_id', 'assignee_name', 'object_type', 'object_id', 'assigned_date',
            'due_date', 'status', 'comment_text', 'approved_date', 'created_at', 'updated_at',
            'contract_details', 'assigner_details', 'assignee_details', 'is_overdue', 'days_until_due'
        ]
        read_only_fields = ['approval_id', 'created_at', 'updated_at']
    
    def get_contract_details(self, obj):
        """Get detailed contract information"""
        contract = obj.get_contract()
        if contract:
            if hasattr(contract, 'contract_title'):
                # Main contract or subcontract
                return {
                    'id': getattr(contract, 'contract_id', None),
                    'title': getattr(contract, 'contract_title', 'N/A'),
                    'number': getattr(contract, 'contract_number', 'N/A'),
                    'type': getattr(contract, 'contract_type', 'N/A'),
                    'status': getattr(contract, 'status', 'N/A'),
                    'value': getattr(contract, 'contract_value', None),
                    'currency': getattr(contract, 'currency', 'USD'),
                    'start_date': getattr(contract, 'start_date', None),
                    'end_date': getattr(contract, 'end_date', None),
                    'vendor_name': getattr(contract.vendor, 'company_name', 'N/A') if hasattr(contract, 'vendor') and contract.vendor else 'N/A'
                }
            elif hasattr(contract, 'amendment_number'):
                # Contract amendment
                return {
                    'id': getattr(contract, 'amendment_id', None),
                    'title': f"Amendment {getattr(contract, 'amendment_number', 'N/A')}",
                    'number': getattr(contract, 'amendment_number', 'N/A'),
                    'type': 'Amendment',
                    'status': getattr(contract, 'workflow_status', 'N/A'),
                    'reason': getattr(contract, 'amendment_reason', 'N/A'),
                    'effective_date': getattr(contract, 'effective_date', None)
                }
            elif hasattr(contract, 'renewal_decision'):
                # Contract renewal
                return {
                    'id': getattr(contract, 'renewal_id', None),
                    'title': f"Renewal - {getattr(contract, 'renewal_decision', 'N/A')}",
                    'number': f"REN-{getattr(contract, 'renewal_id', 'N/A')}",
                    'type': 'Renewal',
                    'status': getattr(contract, 'status', 'N/A'),
                    'decision': getattr(contract, 'renewal_decision', 'N/A'),
                    'renewal_date': getattr(contract, 'renewal_date', None)
                }
        return None
    
    def get_assigner_details(self, obj):
        """Get assigner user details"""
        try:
            user = User.objects.get(userid=obj.assigner_id)
            return {
                'userid': user.userid,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username
            }
        except User.DoesNotExist:
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
        try:
            user = User.objects.get(userid=obj.assignee_id)
            return {
                'userid': user.userid,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username
            }
        except User.DoesNotExist:
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


class ContractApprovalCreateAssignmentSerializer(AutoDecryptingModelSerializer):
    """Serializer for creating contract approval assignments"""
    
    class Meta:
        model = ContractApproval
        fields = [
            'workflow_id', 'workflow_name', 'assigner_id', 'assigner_name',
            'assignee_id', 'assignee_name', 'object_type', 'object_id',
            'assigned_date', 'due_date', 'status', 'comment_text', 'approved_date'
        ]
    
    def validate_object_id(self, value):
        """Validate that the object_id exists for the given object_type"""
        object_type = self.initial_data.get('object_type')
        if object_type and value:
            approval = ContractApproval(
                object_type=object_type,
                object_id=value
            )
            contract = approval.get_contract()
            if not contract:
                raise serializers.ValidationError(f"Object with ID {value} not found for type {object_type}")
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


class ContractApprovalBulkCreateSerializer(serializers.Serializer):
    """Serializer for creating multiple contract approvals at once"""
    
    contract_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of contract IDs to create approvals for"
    )
    workflow_id = serializers.IntegerField()
    workflow_name = serializers.CharField(max_length=255)
    assigner_id = serializers.IntegerField()
    assigner_name = serializers.CharField(max_length=255)
    assignee_id = serializers.IntegerField()
    assignee_name = serializers.CharField(max_length=255)
    object_type = serializers.ChoiceField(choices=ContractApproval.OBJECT_TYPE_CHOICES)
    due_date = serializers.DateTimeField()
    comment_text = serializers.CharField(required=False, allow_blank=True)
    
    def validate_contract_ids(self, value):
        """Validate that all contract IDs exist"""
        if not value:
            raise serializers.ValidationError("At least one contract ID is required")
        
        # Check if all contracts exist
        object_type = self.initial_data.get('object_type')
        if object_type:
            for contract_id in value:
                approval = ContractApproval(
                    object_type=object_type,
                    object_id=contract_id
                )
                contract = approval.get_contract()
                if not contract:
                    raise serializers.ValidationError(f"Contract with ID {contract_id} not found for type {object_type}")
        
        return value
    
    def create(self, validated_data):
        """Create multiple contract approvals"""
        contract_ids = validated_data.pop('contract_ids')
        approvals = []
        
        for contract_id in contract_ids:
            approval_data = validated_data.copy()
            approval_data['object_id'] = contract_id
            approval_data['assigned_date'] = timezone.now()
            approval_data['status'] = 'ASSIGNED'
            
            approval = ContractApproval.objects.create(**approval_data)
            approvals.append(approval)
        
        return approvals


class ContractApprovalStatsSerializer(serializers.Serializer):
    """Serializer for contract approval statistics"""
    
    total_approvals = serializers.IntegerField()
    pending_approvals = serializers.IntegerField()
    overdue_approvals = serializers.IntegerField()
    completed_approvals = serializers.IntegerField()
    approvals_by_status = serializers.DictField()
    approvals_by_type = serializers.DictField()
    approvals_by_assignee = serializers.DictField()
    average_completion_time = serializers.FloatField()
    overdue_percentage = serializers.FloatField()
