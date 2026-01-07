"""
Serializers for the Audits app.
"""
from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import ContractAudit, ContractStaticQuestionnaire, ContractAuditVersion, ContractAuditFinding, ContractAuditReport
from tprm_backend.contracts.models import VendorContract, ContractTerm
from django.contrib.auth.models import User


class ContractStaticQuestionnaireSerializer(AutoDecryptingModelSerializer):
    """Serializer for ContractStaticQuestionnaire model."""
    term_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractStaticQuestionnaire
        fields = [
            'question_id', 'term_id', 'term_name', 'question_text', 'question_type',
            'is_required', 'scoring_weightings', 'document_upload', 'multiple_choice', 'created_at'
        ]
        read_only_fields = ['question_id', 'created_at']
    
    def get_term_name(self, obj):
        """Get term name by looking up ContractTerm using term_id."""
        try:
            from contracts.models import ContractTerm
            # Try to find the term by term_id
            term = ContractTerm.objects.filter(term_id=obj.term_id).first()
            if term:
                return term.term_title or f'Term {term.term_id}'
        except Exception:
            pass
        return obj.term_id or 'Unknown Term'


class ContractAuditVersionSerializer(AutoDecryptingModelSerializer):
    """Serializer for ContractAuditVersion model."""
    
    class Meta:
        model = ContractAuditVersion
        fields = [
            'version_id', 'audit_id', 'version_type', 'version_number',
            'extended_information', 'user_id', 'approval_status', 'date_created',
            'is_active', 'created_at'
        ]
        read_only_fields = ['version_id', 'date_created', 'created_at']


class ContractAuditFindingSerializer(AutoDecryptingModelSerializer):
    """Serializer for ContractAuditFinding model."""
    
    # Add a computed field to show questionnaire responses with question text
    questionnaire_responses_with_questions = serializers.SerializerMethodField()
    term_title = serializers.SerializerMethodField()
    term_text = serializers.SerializerMethodField()
    term_category = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractAuditFinding
        fields = [
            'audit_finding_id', 'audit_id', 'term_id', 'term_title', 'term_text', 'term_category',
            'evidence', 'user_id', 'how_to_verify', 'impact_recommendations', 'details_of_finding',
            'comment', 'check_date', 'questionnaire_responses', 'questionnaire_responses_with_questions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['audit_finding_id', 'created_at', 'updated_at']

    def _get_term_cache(self):
        """Return a shared cache for term lookups scoped to this serializer instance."""
        if '_term_cache' not in self.context:
            self.context['_term_cache'] = {}
        return self.context['_term_cache']
    
    def _get_term_details(self, term_id):
        """Fetch term details from cache or database."""
        if not term_id:
            return None
        
        cache = self._get_term_cache()
        if term_id not in cache:
            cache[term_id] = ContractTerm.objects.filter(term_id=term_id).values(
                'term_title', 'term_text', 'term_category'
            ).first()
        return cache[term_id]
    
    def get_term_title(self, obj):
        term = self._get_term_details(obj.term_id)
        if term:
            return term.get('term_title') or f"Term {obj.term_id}"
        return None
    
    def get_term_text(self, obj):
        term = self._get_term_details(obj.term_id)
        if term:
            return term.get('term_text')
        return None
    
    def get_term_category(self, obj):
        term = self._get_term_details(obj.term_id)
        if term:
            return term.get('term_category')
        return None
    
    def validate_questionnaire_responses(self, value):
        """Ensure questionnaire_responses is valid JSON."""
        if value is None:
            return {}
        
        # If it's a string, try to parse it
        if isinstance(value, str):
            import json
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # If it's not valid JSON, wrap it in a dict
                return {'response': value}
        
        # If it's already a dict or list, return as is
        if isinstance(value, (dict, list)):
            return value
        
        # For any other type, convert to dict
        return {'value': str(value)}
    
    def get_questionnaire_responses_with_questions(self, obj):
        """Get questionnaire responses with question text for better readability."""
        if not obj.questionnaire_responses:
            return {}
        
        try:
            # Parse the responses
            responses = obj.questionnaire_responses
            if isinstance(responses, str):
                import json
                responses = json.loads(responses)
            
            # Get question texts from the database
            from .models import ContractStaticQuestionnaire
            
            enhanced_responses = {}
            for question_id, answer in responses.items():
                try:
                    question = ContractStaticQuestionnaire.objects.get(question_id=question_id)
                    enhanced_responses[question_id] = {
                        'question_text': question.question_text,
                        'answer': answer,
                        'question_type': question.question_type
                    }
                except ContractStaticQuestionnaire.DoesNotExist:
                    enhanced_responses[question_id] = {
                        'question_text': f'Question {question_id}',
                        'answer': answer,
                        'question_type': 'unknown'
                    }
            
            return enhanced_responses
            
        except Exception as e:
            print(f"Error enhancing questionnaire responses: {e}")
            return obj.questionnaire_responses
    
    def create(self, validated_data):
        """Create audit finding with better logging."""
        print(f"📝 Creating audit finding with validated data: {validated_data}")
        
        try:
            finding = ContractAuditFinding.objects.create(**validated_data)
            print(f"✅ Audit finding created: ID={finding.audit_finding_id}, Audit ID={finding.audit_id}, Term ID={finding.term_id}")
            return finding
        except Exception as e:
            print(f"❌ Error in ContractAuditFinding.objects.create: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            raise


class ContractAuditReportSerializer(AutoDecryptingModelSerializer):
    """Serializer for ContractAuditReport model."""
    
    class Meta:
        model = ContractAuditReport
        fields = [
            'report_id', 'audit_id', 'report_link', 'contract_id', 'term_id', 'generated_at'
        ]
        read_only_fields = ['report_id', 'generated_at']


class ContractAuditSerializer(AutoDecryptingModelSerializer):
    """Serializer for ContractAudit model."""
    contract_title = serializers.SerializerMethodField()
    contract_id = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractAudit
        fields = [
            'audit_id', 'title', 'scope', 'assignee_id', 'auditor_id', 'assign_date',
            'due_date', 'frequency', 'status', 'completion_date', 'reviewer_id',
            'term_id', 'contract', 'contract_id', 'contract_title', 'review_status', 'review_comments',
            'audit_type', 'evidence_comments', 'review_start_date', 'review_date',
            'reports_objective', 'business_unit', 'role', 'responsibility',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['audit_id', 'created_at', 'updated_at']
    
    def get_contract_title(self, obj):
        """Get contract title from related contract."""
        if obj.contract:
            return obj.contract.contract_title
        return None
    
    def get_contract_id(self, obj):
        """Get contract ID from related contract."""
        if obj.contract:
            return obj.contract.contract_id
        return None


class ContractAuditCreateSerializer(AutoDecryptingModelSerializer):
    """Serializer for creating contract audits."""
    
    class Meta:
        model = ContractAudit
        fields = [
            'title', 'scope', 'assignee_id', 'auditor_id', 'reviewer_id', 'due_date', 'frequency',
            'audit_type', 'contract', 'term_id', 'business_unit', 'role', 'responsibility', 'tenant_id'
        ]
    
    def create(self, validated_data):
        # Set assign_date to today if not provided
        from django.utils import timezone
        validated_data['assign_date'] = timezone.now().date()
        
        # Set review_status to 'pending' by default if not provided
        if 'review_status' not in validated_data:
            validated_data['review_status'] = 'pending'
        
        # Debug: Log the validated data to see what's being saved
        print(f"ContractAuditCreateSerializer - Creating audit with data: {validated_data}")
        print(f"Scope value: '{validated_data.get('scope', 'NOT_FOUND')}'")
        print(f"Assignee ID: {validated_data.get('assignee_id', 'NOT_FOUND')}")
        
        audit = ContractAudit.objects.create(**validated_data)
        
        # Debug: Verify the saved audit
        print(f"Created audit - ID: {audit.audit_id}, Scope: '{audit.scope}', Assignee ID: {audit.assignee_id}")
        
        return audit


class ContractAuditUpdateSerializer(AutoDecryptingModelSerializer):
    """Serializer for updating contract audits with partial updates."""
    
    class Meta:
        model = ContractAudit
        fields = [
            'title', 'scope', 'assignee_id', 'auditor_id', 'reviewer_id', 'due_date', 'frequency',
            'status', 'completion_date', 'review_status', 'review_comments', 'audit_type',
            'evidence_comments', 'review_start_date', 'review_date', 'reports_objective',
            'business_unit', 'role', 'responsibility', 'contract', 'term_id'
        ]
        # Make all fields optional for partial updates
        extra_kwargs = {
            'title': {'required': False},
            'due_date': {'required': False},
            'scope': {'required': False},
            'assignee_id': {'required': False},
            'auditor_id': {'required': False},
            'reviewer_id': {'required': False},
            'frequency': {'required': False},
            'audit_type': {'required': False},
            'business_unit': {'required': False},
            'role': {'required': False},
            'responsibility': {'required': False},
            'contract': {'required': False},
            'term_id': {'required': False},
            'status': {'required': False},
            'completion_date': {'required': False},
            'review_status': {'required': False, 'allow_null': True},
            'review_comments': {'required': False, 'allow_null': True},
            'evidence_comments': {'required': False},
            'review_start_date': {'required': False},
            'review_date': {'required': False},
            'reports_objective': {'required': False},
        }
    
    def validate_review_status(self, value):
        """Convert null values to 'pending' for review_status to prevent database errors."""
        if value is None:
            return 'pending'
        return value
    
    def validate_review_comments(self, value):
        """Allow null values for review_comments."""
        return value


class ContractAuditListSerializer(AutoDecryptingModelSerializer):
    """Simplified serializer for contract audit lists."""
    contract_title = serializers.SerializerMethodField()
    contract_id = serializers.SerializerMethodField()
    auditor_name = serializers.SerializerMethodField()
    reviewer_name = serializers.SerializerMethodField()
    assignee_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractAudit
        fields = [
            'audit_id', 'title', 'scope', 'contract_title', 'contract_id', 'status',
            'due_date', 'completion_date', 'frequency', 'audit_type', 'auditor_id', 'reviewer_id', 'assignee_id',
            'auditor_name', 'reviewer_name', 'assignee_name', 'business_unit', 'role',
            'review_status', 'review_comments', 'created_at', 'updated_at'
        ]
    
    def get_contract_title(self, obj):
        """Get contract title from related contract."""
        if obj.contract:
            return obj.contract.contract_title
        return None
    
    def get_contract_id(self, obj):
        """Get contract ID from related contract."""
        if obj.contract:
            return obj.contract.contract_id
        return None
    
    def get_auditor_name(self, obj):
        """Get auditor name from user ID."""
        if obj.auditor_id:
            try:
                from django.db import connections
                with connections['default'].cursor() as cursor:
                    cursor.execute("""
                        SELECT FirstName, LastName, UserName
                        FROM users 
                        WHERE UserId = %s AND (IsActive = 'Y' OR IsActive = '1' OR IsActive = 'true')
                    """, [obj.auditor_id])
                    row = cursor.fetchone()
                    if row:
                        first_name, last_name, username = row
                        full_name = f"{first_name or ''} {last_name or ''}".strip()
                        return full_name if full_name else username or f"User {obj.auditor_id}"
                    return f"User {obj.auditor_id}"
            except Exception:
                return f"User {obj.auditor_id}"
        return None
    
    def get_reviewer_name(self, obj):
        """Get reviewer name from user ID."""
        if obj.reviewer_id:
            try:
                from django.db import connections
                with connections['default'].cursor() as cursor:
                    cursor.execute("""
                        SELECT FirstName, LastName, UserName
                        FROM users 
                        WHERE UserId = %s AND (IsActive = 'Y' OR IsActive = '1' OR IsActive = 'true')
                    """, [obj.reviewer_id])
                    row = cursor.fetchone()
                    if row:
                        first_name, last_name, username = row
                        full_name = f"{first_name or ''} {last_name or ''}".strip()
                        return full_name if full_name else username or f"User {obj.reviewer_id}"
                    return f"User {obj.reviewer_id}"
            except Exception:
                return f"User {obj.reviewer_id}"
        return None
    
    def get_assignee_name(self, obj):
        """Get assignee name from user ID."""
        if obj.assignee_id:
            try:
                from django.db import connections
                with connections['default'].cursor() as cursor:
                    cursor.execute("""
                        SELECT FirstName, LastName, UserName
                        FROM users 
                        WHERE UserId = %s AND (IsActive = 'Y' OR IsActive = '1' OR IsActive = 'true')
                    """, [obj.assignee_id])
                    row = cursor.fetchone()
                    if row:
                        first_name, last_name, username = row
                        full_name = f"{first_name or ''} {last_name or ''}".strip()
                        return full_name if full_name else username or f"User {obj.assignee_id}"
                    return f"User {obj.assignee_id}"
            except Exception:
                return f"User {obj.assignee_id}"
        return None
