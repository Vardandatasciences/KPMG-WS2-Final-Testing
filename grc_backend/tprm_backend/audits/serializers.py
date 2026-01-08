"""
Serializers for the Audits app.
"""
from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import Audit, StaticQuestionnaire, AuditVersion, AuditFinding, AuditReport
from tprm_backend.slas.models import VendorSLA
from tprm_backend.slas.serializers import VendorSLASerializer, SLAMetricSerializer


class StaticQuestionnaireSerializer(AutoDecryptingModelSerializer):
    """Serializer for StaticQuestionnaire model."""
    
    class Meta:
        model = StaticQuestionnaire
        fields = [
            'question_id', 'metric_name', 'question_text', 'question_type',
            'is_required', 'scoring_weightings', 'created_at'
        ]
        read_only_fields = ['question_id', 'created_at']


class AuditVersionSerializer(AutoDecryptingModelSerializer):
    """Serializer for AuditVersion model."""
    
    class Meta:
        model = AuditVersion
        fields = [
            'version_id', 'audit_id', 'version_type', 'version_number',
            'extended_information', 'user_id', 'approval_status', 'date_created',
            'is_active', 'created_at'
        ]
        read_only_fields = ['version_id', 'date_created', 'created_at']


class AuditFindingSerializer(AutoDecryptingModelSerializer):
    """Serializer for AuditFinding model."""
    
    class Meta:
        model = AuditFinding
        fields = [
            'audit_finding_id', 'audit_id', 'metrics_id', 'evidence', 'user_id',
            'how_to_verify', 'impact_recommendations', 'details_of_finding',
            'comment', 'check_date', 'questionnaire_responses', 'created_at', 'updated_at'
        ]
        read_only_fields = ['audit_finding_id', 'created_at', 'updated_at']


class AuditReportSerializer(AutoDecryptingModelSerializer):
    """Serializer for AuditReport model."""
    
    class Meta:
        model = AuditReport
        fields = [
            'report_id', 'audit_id', 'report_link', 'sla_id', 'metrics_id', 'generated_at'
        ]
        read_only_fields = ['report_id', 'generated_at']


class AuditSerializer(AutoDecryptingModelSerializer):
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
                sla = VendorSLA.objects.get(sla_id=obj.sla_id)
                return sla.sla_name
            except VendorSLA.DoesNotExist:
                return "Unknown SLA"
            except Exception:
                return "Unknown SLA"
        return None


class AuditCreateSerializer(AutoDecryptingModelSerializer):
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
        # MULTI-TENANCY: Filter by tenant_id when validating SLA
        sla_obj = None
        try:
            from tprm_backend.core.tenant_utils import get_tenant_id_from_request
            
            # Get tenant_id from request context if available
            tenant_id = None
            if self.context and 'request' in self.context:
                tenant_id = get_tenant_id_from_request(self.context['request'])
            
            # Try to get the SLA, filtering by tenant_id if available
            sla_query = VendorSLA.objects.filter(sla_id=sla_id)
            if tenant_id:
                sla_query = sla_query.filter(tenant_id=tenant_id)
            
            sla_obj = sla_query.first()
            if not sla_obj:
                if tenant_id:
                    raise serializers.ValidationError(f"SLA with ID {sla_id} not found for tenant {tenant_id}")
                else:
                    raise serializers.ValidationError(f"SLA with ID {sla_id} does not exist")
        except serializers.ValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            # Log unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error validating sla_id {sla_id}: {str(e)}", exc_info=True)
            raise serializers.ValidationError(f"Error validating SLA ID {sla_id}: {str(e)}")
        
        # Create the audit object
        # Note: sla is a ForeignKey field, but we'll set it directly using the sla_id
        # Since it's a ForeignKey with db_column='sla_id', we can set it after creation
        audit = Audit.objects.create(**validated_data)
        
        # Set the sla_id directly on the model instance
        # Since sla is a ForeignKey with db_column='sla_id', we can set it directly
        # Use pk instead of audit_id to avoid column name issues
        # Try setting the ForeignKey object first, then fallback to direct update
        try:
            if sla_obj:
                audit.sla = sla_obj
                audit.save(update_fields=['sla'])
            else:
                # Fallback: use update() method
                Audit.objects.filter(pk=audit.pk).update(sla_id=sla_id)
        except Exception as e:
            # If setting ForeignKey fails, try direct update
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error setting sla ForeignKey, trying direct update: {str(e)}")
            Audit.objects.filter(pk=audit.pk).update(sla_id=sla_id)
        
        # Refresh the audit object to get the updated sla_id
        audit.refresh_from_db()
        
        return audit


class AuditListSerializer(AutoDecryptingModelSerializer):
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
                sla = VendorSLA.objects.get(sla_id=obj.sla_id)
                return sla.sla_name
            except VendorSLA.DoesNotExist:
                return "Unknown SLA"
            except Exception:
                return "Unknown SLA"
        return None
    
    def get_sla_type(self, obj):
        """Get SLA type from sla_id using cross-database lookup."""
        if obj.sla_id:
            try:
                sla = VendorSLA.objects.get(sla_id=obj.sla_id)
                return sla.sla_type
            except VendorSLA.DoesNotExist:
                return "Unknown Type"
            except Exception:
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
