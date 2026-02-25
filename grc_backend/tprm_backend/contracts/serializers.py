from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from tprm_backend.mfa_auth.models import User
from .models import Vendor, VendorContract, ContractTerm, ContractClause, VendorContact, ContractAmendment, ContractRenewal, ContractApproval
from django.utils import timezone
from decimal import Decimal
import json
import time
import random
import string
from django.db import IntegrityError


class UserSerializer(AutoDecryptingModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['userid', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['userid']


class VendorSerializer(AutoDecryptingModelSerializer):
    """Serializer for Vendor model"""
    
    # Remove user-related fields since created_by/updated_by are now IntegerFields
    geographic_presence_display = serializers.SerializerMethodField()
    diversity_certifications_display = serializers.SerializerMethodField()
    primary_contact = serializers.SerializerMethodField()
    active_contacts = serializers.SerializerMethodField()
    contracts_count = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['vendor_id', 'created_at', 'updated_at']
    
    def validate_data_inventory(self, value):
        """Ensure data_inventory is always a dictionary"""
        if not isinstance(value, dict):
            return {}
        return value
    
    def get_geographic_presence_display(self, obj):
        return obj.get_geographic_presence_display()
    
    def get_diversity_certifications_display(self, obj):
        return obj.get_diversity_certifications_display()
    
    def get_primary_contact(self, obj):
        """Get primary contact for vendor"""
        contact = obj.get_primary_contact()
        if contact:
            return VendorContactSerializer(contact).data
        return None
    
    def get_active_contacts(self, obj):
        """Get all active contacts for vendor"""
        contacts = obj.get_active_contacts()
        return VendorContactSerializer(contacts, many=True).data
    
    def get_contracts_count(self, obj):
        """Get total contracts count for vendor - optimized to use annotation if available"""
        # Check if annotation exists (from optimized queryset)
        if hasattr(obj, 'contracts_count_annotated'):
            return obj.contracts_count_annotated
        # Fallback to query if annotation not available (for backward compatibility)
        from .models import VendorContract
        count = VendorContract.objects.filter(
            vendor_id=obj.vendor_id,
            is_archived=False
        ).count()
        return count
    
    def get_total_value(self, obj):
        """Get total contract value for vendor - optimized to use annotation if available"""
        # Check if annotation exists (from optimized queryset)
        if hasattr(obj, 'total_value_annotated'):
            return float(obj.total_value_annotated or 0)
        # Fallback to query if annotation not available (for backward compatibility)
        from .models import VendorContract
        from django.db.models import Sum
        total = VendorContract.objects.filter(
            vendor_id=obj.vendor_id,
            is_archived=False
        ).aggregate(total=Sum('contract_value'))['total']
        return float(total or 0)
    
    def get_last_activity(self, obj):
        """Get last activity date for vendor - optimized to use annotation if available"""
        # Check if annotation exists (from optimized queryset)
        if hasattr(obj, 'last_activity_annotated') and obj.last_activity_annotated:
            return obj.last_activity_annotated
        # Fallback to query if annotation not available (for backward compatibility)
        from .models import VendorContract
        from django.utils import timezone
        
        # Get the most recent contract for this vendor
        latest_contract = VendorContract.objects.filter(
            vendor_id=obj.vendor_id,
            is_archived=False
        ).order_by('-created_at').first()
        
        if latest_contract:
            return latest_contract.created_at
        return obj.updated_at
    
    def get_full_address(self, obj):
        """Get formatted full address"""
        address_parts = []
        if obj.headquarters_address:
            address_parts.append(obj.headquarters_address)
        if obj.headquarters_country:
            address_parts.append(obj.headquarters_country)
        
        return ', '.join(address_parts) if address_parts else 'Address not available'
    
    def validate_vendor_code(self, value):
        """Validate vendor code uniqueness"""
        if self.instance and self.instance.vendor_code == value:
            return value
        
        if Vendor.objects.filter(vendor_code=value).exists():
            raise serializers.ValidationError("Vendor code already exists")
        return value
    
    def validate_annual_revenue(self, value):
        """Validate annual revenue"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Annual revenue cannot be negative")
        return value
    
    def validate_employee_count(self, value):
        """Validate employee count"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Employee count cannot be negative")
        return value


class ContractTermSerializer(AutoDecryptingModelSerializer):
    """Serializer for ContractTerm model"""
    
    # Remove user-related fields since created_by/approved_by are now IntegerFields
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = ContractTerm
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']  # Removed term_id to allow frontend to provide it
    
    def validate_data_inventory(self, value):
        """Ensure data_inventory is always a dictionary"""
        if not isinstance(value, dict):
            return {}
        return value
    
    def create(self, validated_data):
        """Create contract term with term_id from frontend or auto-generated"""
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Store the original term_id from frontend (before any modifications)
        # This will be used to find and update questionnaires that were created with this term_id
        original_term_id = validated_data.get('term_id')
        
        # Check if term_id was provided in validated_data (now that it's not read-only)
        # If not provided, generate a new one
        term_id = validated_data.get('term_id')
        
        if not term_id:
            # Generate a new term_id
            term_id = f"term_{timezone.now().timestamp()}"
            validated_data['term_id'] = term_id
            original_term_id = term_id  # Original is the same as generated
            logger.info(f"Generated new term_id: {term_id}")
        else:
            # Check if the provided term_id already exists
            if ContractTerm.objects.filter(term_id=term_id).exists():
                logger.warning(f"⚠️ Term ID {term_id} already exists, generating a new unique one")
                # Generate a new unique term_id by appending timestamp and random suffix
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                term_id = f"{term_id}_{int(time.time() * 1000)}_{random_suffix}"
                validated_data['term_id'] = term_id
                logger.info(f"Generated new unique term_id: {term_id} (original was: {original_term_id})")
            else:
                logger.info(f"Using provided term_id: {term_id}")
        
        # Log the term_id being used for debugging
        logger.info(f"Creating contract term with term_id: {validated_data.get('term_id')} (original: {original_term_id})")
        
        # Try to create the term, and if there's still a duplicate error, generate a new ID
        max_retries = 5  # Increased retries to handle race conditions
        final_term_id = None
        for attempt in range(max_retries):
            try:
                # Double-check term_id doesn't exist right before creating (handles race conditions)
                current_term_id = validated_data.get('term_id')
                if current_term_id and ContractTerm.objects.filter(term_id=current_term_id).exists():
                    logger.warning(f"⚠️ Term ID {current_term_id} exists (race condition), generating new one")
                    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                    validated_data['term_id'] = f"term_{int(time.time() * 1000000)}_{random_suffix}"
                    if attempt < max_retries - 1:
                        time.sleep(0.1 * (attempt + 1))  # Small delay to reduce race conditions
                        continue
                
                term = super().create(validated_data)
                final_term_id = term.term_id
                
                # Store original_term_id in the term instance so the signal can access it
                # We'll use a custom attribute that won't be saved to the database
                if original_term_id and original_term_id != final_term_id:
                    term._original_term_id = original_term_id
                    logger.info(f"📋 Stored original_term_id {original_term_id} on term instance (saved as {final_term_id})")
                
                return term
            except IntegrityError as e:
                error_str = str(e)
                if ('term_id' in error_str or 'Duplicate entry' in error_str) and attempt < max_retries - 1:
                    # Generate a new unique term_id and retry
                    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                    validated_data['term_id'] = f"term_{int(time.time() * 1000000)}_{random_suffix}"
                    logger.warning(f"⚠️ Duplicate term_id detected (IntegrityError), retrying with new ID: {validated_data['term_id']} (attempt {attempt + 1}/{max_retries})")
                    time.sleep(0.1 * (attempt + 1))  # Small delay to reduce race conditions
                    continue
                else:
                    # Re-raise if it's not a duplicate error or we've exhausted retries
                    logger.error(f"❌ Failed to create term after {max_retries} attempts: {error_str}")
                    raise


class ContractClauseSerializer(AutoDecryptingModelSerializer):
    """Serializer for ContractClause model"""
    
    # Remove user-related fields since created_by is now IntegerField
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = ContractClause
        fields = '__all__'
        read_only_fields = ['clause_id', 'created_at', 'updated_at']
    
    def validate_data_inventory(self, value):
        """Ensure data_inventory is always a dictionary"""
        if not isinstance(value, dict):
            return {}
        return value
    
    def create(self, validated_data):
        """Create contract clause with auto-generated clause_id"""
        if not validated_data.get('clause_id'):
            validated_data['clause_id'] = f"clause_{timezone.now().timestamp()}"
        return super().create(validated_data)
    
    def validate_early_termination_fee(self, value):
        """Validate early termination fee"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Early termination fee cannot be negative")
        return value
    
    def validate_clause_name(self, value):
        """Validate clause name is not blank"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Clause name cannot be blank")
        return value
    
    def validate_clause_text(self, value):
        """Validate clause text is not blank"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Clause text cannot be blank")
        return value


class VendorContractSerializer(AutoDecryptingModelSerializer):
    """Serializer for VendorContract model"""
    
    # Related field serializers
    vendor = VendorSerializer(read_only=True)
    vendor_id = serializers.IntegerField(read_only=True)
    # Remove user-related fields since contract_owner/legal_reviewer/archived_by are now IntegerFields
    
    # Computed fields
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    insurance_requirements_display = serializers.SerializerMethodField()
    data_protection_clauses_display = serializers.SerializerMethodField()
    custom_fields_display = serializers.SerializerMethodField()
    contract_owner_username = serializers.SerializerMethodField()
    legal_reviewer_username = serializers.SerializerMethodField()
    
    # Nested serializers for terms and clauses
    terms = ContractTermSerializer(many=True, read_only=True)
    clauses = ContractClauseSerializer(many=True, read_only=True)
    
    class Meta:
        model = VendorContract
        fields = '__all__'
        read_only_fields = ['contract_id', 'created_at', 'updated_at']
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_days_until_expiry(self, obj):
        return obj.days_until_expiry()
    
    def get_insurance_requirements_display(self, obj):
        return obj.get_insurance_requirements_display()
    
    def get_data_protection_clauses_display(self, obj):
        return obj.get_data_protection_clauses_display()
    
    def get_custom_fields_display(self, obj):
        return obj.get_custom_fields_display()
    
    def get_contract_owner_username(self, obj):
        """Get full name for contract owner"""
        if obj.contract_owner:
            try:
                user = User.objects.get(userid=obj.contract_owner)
                
                # Check if first_name and last_name are populated
                first_name = user.first_name or ""
                last_name = user.last_name or ""
                full_name = f"{first_name} {last_name}".strip()
                
                # If no full name, return username
                if not full_name:
                    return user.username
                
                return full_name
            except User.DoesNotExist:
                return f"User {obj.contract_owner} (not found)"
        return None
    
    def get_legal_reviewer_username(self, obj):
        """Get full name for legal reviewer"""
        if obj.legal_reviewer:
            try:
                user = User.objects.get(userid=obj.legal_reviewer)
                
                # Check if first_name and last_name are populated
                first_name = user.first_name or ""
                last_name = user.last_name or ""
                full_name = f"{first_name} {last_name}".strip()
                
                # If no full name, return username
                if not full_name:
                    return user.username
                
                return full_name
            except User.DoesNotExist:
                return f"User {obj.legal_reviewer} (not found)"
        return None
    
    def validate_contract_number(self, value):
        """Validate contract number uniqueness"""
        if self.instance and self.instance.contract_number == value:
            return value
        
        if VendorContract.objects.filter(contract_number=value).exists():
            raise serializers.ValidationError("Contract number already exists")
        return value
    
    def validate_contract_value(self, value):
        """Validate contract value"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Contract value cannot be negative")
        return value
    
    def validate_liability_cap(self, value):
        """Validate liability cap"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Liability cap cannot be negative")
        return value
    
    def validate_contract_risk_score(self, value):
        """Validate contract risk score"""
        if value is not None and (value < 0 or value > 10):
            raise serializers.ValidationError("Contract risk score must be between 0 and 10")
        return value
    
    def validate_notice_period_days(self, value):
        """Validate notice period days"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Notice period days cannot be negative")
        return value
    
    def validate_vendor_id(self, value):
        """Validate vendor exists"""
        if not Vendor.objects.filter(vendor_id=value).exists():
            raise serializers.ValidationError("Vendor does not exist")
        return value
    
    def validate_dates(self, data):
        """Validate start and end dates"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError("End date must be after start date")
        
        return data
    
    def validate(self, data):
        """Validate the entire contract data"""
        # Validate dates
        data = self.validate_dates(data)
        
        # Handle JSON fields - convert plain text to JSON if needed
        if 'insurance_requirements' in data:
            if isinstance(data['insurance_requirements'], str):
                if data['insurance_requirements'].strip():
                    # Convert plain text to JSON format
                    data['insurance_requirements'] = {
                        'requirements': data['insurance_requirements'].strip(),
                        'type': 'text'
                    }
                else:
                    data['insurance_requirements'] = {}
            elif not isinstance(data['insurance_requirements'], dict):
                data['insurance_requirements'] = {}
        
        if 'data_protection_clauses' in data:
            if isinstance(data['data_protection_clauses'], str):
                if data['data_protection_clauses'].strip():
                    # Convert plain text to JSON format
                    data['data_protection_clauses'] = {
                        'clauses': data['data_protection_clauses'].strip(),
                        'type': 'text'
                    }
                else:
                    data['data_protection_clauses'] = {}
            elif not isinstance(data['data_protection_clauses'], dict):
                data['data_protection_clauses'] = {}
        
        if 'custom_fields' in data:
            if isinstance(data['custom_fields'], str):
                try:
                    # Try to parse as JSON first
                    data['custom_fields'] = json.loads(data['custom_fields'])
                except (json.JSONDecodeError, TypeError):
                    # If not valid JSON, convert to empty dict
                    data['custom_fields'] = {}
            elif not isinstance(data['custom_fields'], dict):
                data['custom_fields'] = {}
        
        return data


class VendorContractCreateSerializer(AutoDecryptingModelSerializer):
    """Simplified serializer for contract creation"""
    
    vendor_id = serializers.IntegerField()
    contract_owner = serializers.IntegerField(required=False, allow_null=True)
    legal_reviewer = serializers.IntegerField(required=False, allow_null=True)
    
    data_inventory = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = VendorContract
        fields = [
            'vendor_id', 'contract_number', 'contract_title', 'contract_type',
            'contract_kind', 'parent_contract_id', 'main_contract_id', 'permission_required',
            'version_number', 'previous_version_id', 'contract_value', 'currency', 
            'start_date', 'end_date', 'renewal_terms', 'auto_renewal', 'notice_period_days',
            'status', 'workflow_stage', 'priority', 'compliance_status',
            'contract_category', 'termination_clause_type', 'liability_cap',
            'insurance_requirements', 'data_protection_clauses',
            'dispute_resolution_method', 'governing_law', 'contract_risk_score',
            'assigned_to', 'custom_fields', 'compliance_framework',
            'contract_owner', 'legal_reviewer', 'file_path', 'data_inventory'
        ]
    
    def validate_contract_number(self, value):
        """Validate contract number uniqueness"""
        if value and VendorContract.objects.filter(contract_number=value).exists():
            raise serializers.ValidationError("Contract number already exists")
        return value
    
    def validate_vendor_id(self, value):
        """Validate vendor exists"""
        if not Vendor.objects.filter(vendor_id=value).exists():
            raise serializers.ValidationError("Vendor does not exist")
        return value
    
    def validate_version_number(self, value):
        """Validate version number is positive"""
        if value is not None and value < 1:
            raise serializers.ValidationError("Version number must be 1 or greater")
        return value
    
    def validate_previous_version_id(self, value):
        """Validate previous version contract exists"""
        if value is not None:
            if not VendorContract.objects.filter(contract_id=value).exists():
                raise serializers.ValidationError("Previous version contract does not exist")
        return value
    
    def validate_insurance_requirements(self, value):
        """Validate and convert insurance_requirements field"""
        if isinstance(value, str):
            if value.strip():
                return {
                    'requirements': value.strip(),
                    'type': 'text'
                }
            else:
                return {}
        elif not isinstance(value, dict):
            return {}
        return value
    
    def validate_data_protection_clauses(self, value):
        """Validate and convert data_protection_clauses field"""
        if isinstance(value, str):
            if value.strip():
                return {
                    'clauses': value.strip(),
                    'type': 'text'
                }
            else:
                return {}
        elif not isinstance(value, dict):
            return {}
        return value
    
    def validate_custom_fields(self, value):
        """Validate and convert custom_fields field"""
        if isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {}
        elif not isinstance(value, dict):
            return {}
        return value
    
    def validate_data_inventory(self, value):
        """Validate data_inventory field"""
        if value is None:
            return {}
        if isinstance(value, str):
            try:
                import json
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, TypeError):
                return {}
        if not isinstance(value, dict):
            return {}
        return value
    
    def validate(self, data):
        """Validate the entire contract data"""
        # Handle JSON fields - convert plain text to JSON if needed
        if 'insurance_requirements' in data:
            if isinstance(data['insurance_requirements'], str):
                if data['insurance_requirements'].strip():
                    # Convert plain text to JSON format
                    data['insurance_requirements'] = {
                        'requirements': data['insurance_requirements'].strip(),
                        'type': 'text'
                    }
                else:
                    data['insurance_requirements'] = {}
            elif not isinstance(data['insurance_requirements'], dict):
                data['insurance_requirements'] = {}
        
        if 'data_protection_clauses' in data:
            if isinstance(data['data_protection_clauses'], str):
                if data['data_protection_clauses'].strip():
                    # Convert plain text to JSON format
                    data['data_protection_clauses'] = {
                        'clauses': data['data_protection_clauses'].strip(),
                        'type': 'text'
                    }
                else:
                    data['data_protection_clauses'] = {}
            elif not isinstance(data['data_protection_clauses'], dict):
                data['data_protection_clauses'] = {}
        
        if 'custom_fields' in data:
            if isinstance(data['custom_fields'], str):
                try:
                    # Try to parse as JSON first
                    data['custom_fields'] = json.loads(data['custom_fields'])
                except (json.JSONDecodeError, TypeError):
                    # If not valid JSON, convert to empty dict
                    data['custom_fields'] = {}
            elif not isinstance(data['custom_fields'], dict):
                data['custom_fields'] = {}
        
        # Ensure data_inventory is always a dict
        if 'data_inventory' in data:
            if data['data_inventory'] is None:
                data['data_inventory'] = {}
            elif not isinstance(data['data_inventory'], dict):
                data['data_inventory'] = {}
        
        return data


class VendorContractUpdateSerializer(AutoDecryptingModelSerializer):
    """Serializer for contract updates"""
    
    contract_owner = serializers.IntegerField(required=False, allow_null=True)
    legal_reviewer = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = VendorContract
        fields = [
            'contract_title', 'contract_type', 'version_number', 'previous_version_id',
            'contract_value', 'currency', 'start_date', 'end_date', 'renewal_terms', 
            'auto_renewal', 'notice_period_days', 'status', 'workflow_stage', 'priority',
            'compliance_status', 'contract_category', 'termination_clause_type',
            'liability_cap', 'insurance_requirements', 'data_protection_clauses',
            'dispute_resolution_method', 'governing_law', 'contract_risk_score',
            'assigned_to', 'custom_fields', 'compliance_framework',
            'contract_owner', 'legal_reviewer', 'file_path', 'permission_required', 'data_inventory'
        ]
    
    def validate_contract_value(self, value):
        """Validate contract value"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Contract value cannot be negative")
        return value
    
    def validate_liability_cap(self, value):
        """Validate liability cap"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Liability cap cannot be negative")
        return value
    
    def validate_contract_risk_score(self, value):
        """Validate contract risk score"""
        if value is not None and (value < 0 or value > 10):
            raise serializers.ValidationError("Contract risk score must be between 0 and 10")
        return value
    
    def validate_version_number(self, value):
        """Validate version number is positive"""
        if value is not None and value < 1:
            raise serializers.ValidationError("Version number must be 1 or greater")
        return value
    
    def validate_previous_version_id(self, value):
        """Validate previous version contract exists"""
        if value is not None:
            if not VendorContract.objects.filter(contract_id=value).exists():
                raise serializers.ValidationError("Previous version contract does not exist")
        return value
    
    def validate_insurance_requirements(self, value):
        """Validate and convert insurance_requirements field"""
        if isinstance(value, str):
            if value.strip():
                return {
                    'requirements': value.strip(),
                    'type': 'text'
                }
            else:
                return {}
        elif not isinstance(value, dict):
            return {}
        return value
    
    def validate_data_protection_clauses(self, value):
        """Validate and convert data_protection_clauses field"""
        if isinstance(value, str):
            if value.strip():
                return {
                    'clauses': value.strip(),
                    'type': 'text'
                }
            else:
                return {}
        elif not isinstance(value, dict):
            return {}
        return value
    
    def validate_custom_fields(self, value):
        """Validate and convert custom_fields field"""
        if isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {}
        elif not isinstance(value, dict):
            return {}
        return value
    
    def validate_data_inventory(self, value):
        """Validate data_inventory field"""
        if value is None:
            return {}
        if isinstance(value, str):
            try:
                import json
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, TypeError):
                return {}
        if not isinstance(value, dict):
            return {}
        return value
    
    def validate(self, data):
        """Validate the entire contract data"""
        # Handle JSON fields - convert plain text to JSON if needed
        if 'insurance_requirements' in data:
            if isinstance(data['insurance_requirements'], str):
                if data['insurance_requirements'].strip():
                    # Convert plain text to JSON format
                    data['insurance_requirements'] = {
                        'requirements': data['insurance_requirements'].strip(),
                        'type': 'text'
                    }
                else:
                    data['insurance_requirements'] = {}
            elif not isinstance(data['insurance_requirements'], dict):
                data['insurance_requirements'] = {}
        
        if 'data_protection_clauses' in data:
            if isinstance(data['data_protection_clauses'], str):
                if data['data_protection_clauses'].strip():
                    # Convert plain text to JSON format
                    data['data_protection_clauses'] = {
                        'clauses': data['data_protection_clauses'].strip(),
                        'type': 'text'
                    }
                else:
                    data['data_protection_clauses'] = {}
            elif not isinstance(data['data_protection_clauses'], dict):
                data['data_protection_clauses'] = {}
        
        if 'custom_fields' in data:
            if isinstance(data['custom_fields'], str):
                try:
                    # Try to parse as JSON first
                    data['custom_fields'] = json.loads(data['custom_fields'])
                except (json.JSONDecodeError, TypeError):
                    # If not valid JSON, convert to empty dict
                    data['custom_fields'] = {}
            elif not isinstance(data['custom_fields'], dict):
                data['custom_fields'] = {}
        
        # Ensure data_inventory is always a dict
        if 'data_inventory' in data:
            if data['data_inventory'] is None:
                data['data_inventory'] = {}
            elif not isinstance(data['data_inventory'], dict):
                data['data_inventory'] = {}
        
        return data


class ContractArchiveSerializer(AutoDecryptingModelSerializer):
    """Serializer for contract archiving"""
    
    class Meta:
        model = VendorContract
        fields = ['archive_reason', 'archive_comments', 'can_be_restored']
    
    def validate_archive_reason(self, value):
        """Validate archive reason is provided"""
        if not value:
            raise serializers.ValidationError("Archive reason is required")
        return value


class ContractRestoreSerializer(serializers.Serializer):
    """Serializer for contract restoration"""
    
    restore_reason = serializers.CharField(max_length=500, required=True)
    
    def validate_restore_reason(self, value):
        """Validate restore reason"""
        if not value.strip():
            raise serializers.ValidationError("Restore reason cannot be empty")
        return value


class ContractSearchSerializer(serializers.Serializer):
    """Serializer for contract search parameters"""
    
    search = serializers.CharField(required=False, allow_blank=True)
    contract_type = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    workflow_stage = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.CharField(required=False, allow_blank=True)
    vendor_id = serializers.IntegerField(required=False)
    contract_owner = serializers.IntegerField(required=False)
    start_date_from = serializers.DateField(required=False)
    start_date_to = serializers.DateField(required=False)
    end_date_from = serializers.DateField(required=False)
    end_date_to = serializers.DateField(required=False)
    is_archived = serializers.BooleanField(required=False)
    ordering = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)


class ContractStatsSerializer(serializers.Serializer):
    """Serializer for contract statistics"""
    
    total_contracts = serializers.IntegerField()
    active_contracts = serializers.IntegerField()
    expired_contracts = serializers.IntegerField()
    draft_contracts = serializers.IntegerField()
    contracts_by_type = serializers.DictField()
    contracts_by_status = serializers.DictField()
    contracts_by_priority = serializers.DictField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_risk_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    expiring_soon = serializers.IntegerField()
    overdue_renewals = serializers.IntegerField()


class VendorContactSerializer(AutoDecryptingModelSerializer):
    """Serializer for VendorContact model"""
    
    # Computed fields
    full_name = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()
    primary_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorContact
        fields = '__all__'
        read_only_fields = ['contact_id', 'created_at', 'updated_at']
    
    def get_primary_phone(self, obj):
        """Get primary phone number (mobile preferred, then phone)"""
        return obj.get_primary_phone()
    
    def validate_email(self, value):
        """Validate email format and uniqueness per vendor"""
        if not value:
            raise serializers.ValidationError("Email is required")
        
        # Check if email already exists for this vendor
        vendor_id = self.initial_data.get('vendor_id')
        if vendor_id:
            existing = VendorContact.objects.filter(
                vendor_id=vendor_id,
                email=value
            )
            if self.instance:
                existing = existing.exclude(contact_id=self.instance.contact_id)
            
            if existing.exists():
                raise serializers.ValidationError("Email address already exists for this vendor")
        
        return value
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if value and len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value
    
    def validate_mobile(self, value):
        """Validate mobile number format"""
        if value and len(value) < 10:
            raise serializers.ValidationError("Mobile number must be at least 10 digits")
        return value
    
    def validate(self, data):
        """Validate contact data"""
        # Ensure at least one phone number is provided
        if not data.get('phone') and not data.get('mobile'):
            raise serializers.ValidationError("At least one phone number (phone or mobile) must be provided")
        
        # Ensure first_name and last_name are provided
        if not data.get('first_name') or not data.get('last_name'):
            raise serializers.ValidationError("Both first name and last name are required")
        
        return data


class VendorContactCreateSerializer(AutoDecryptingModelSerializer):
    """Simplified serializer for vendor contact creation"""
    
    vendor_id = serializers.IntegerField()
    
    class Meta:
        model = VendorContact
        fields = [
            'vendor_id', 'contact_type', 'first_name', 'last_name', 
            'email', 'phone', 'mobile', 'designation', 'department',
            'is_primary', 'is_active'
        ]
    
    def validate_vendor_id(self, value):
        """Validate vendor exists"""
        if not Vendor.objects.filter(vendor_id=value).exists():
            raise serializers.ValidationError("Vendor does not exist")
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness per vendor"""
        vendor_id = self.initial_data.get('vendor_id')
        if vendor_id and VendorContact.objects.filter(vendor_id=vendor_id, email=value).exists():
            raise serializers.ValidationError("Email address already exists for this vendor")
        return value
    
    def validate(self, data):
        """Validate contact data"""
        # Ensure at least one phone number is provided
        if not data.get('phone') and not data.get('mobile'):
            raise serializers.ValidationError("At least one phone number (phone or mobile) must be provided")
        
        return data


class VendorContactUpdateSerializer(AutoDecryptingModelSerializer):
    """Serializer for vendor contact updates"""
    
    class Meta:
        model = VendorContact
        fields = [
            'contact_type', 'first_name', 'last_name', 'email', 
            'phone', 'mobile', 'designation', 'department',
            'is_primary', 'is_active'
        ]
    
    def validate_email(self, value):
        """Validate email uniqueness per vendor"""
        if self.instance and self.instance.vendor_id:
            existing = VendorContact.objects.filter(
                vendor_id=self.instance.vendor_id,
                email=value
            ).exclude(contact_id=self.instance.contact_id)
            
            if existing.exists():
                raise serializers.ValidationError("Email address already exists for this vendor")
        
        return value
    
    def validate(self, data):
        """Validate contact data"""
        # Ensure at least one phone number is provided
        if not data.get('phone') and not data.get('mobile'):
            raise serializers.ValidationError("At least one phone number (phone or mobile) must be provided")
        
        return data


class ContractAmendmentSerializer(AutoDecryptingModelSerializer):
    """Serializer for ContractAmendment model"""
    
    # Computed fields
    approved_by_display = serializers.SerializerMethodField()
    initiated_by_display = serializers.SerializerMethodField()
    amended_clause_ids_list = serializers.SerializerMethodField()
    amended_term_ids_list = serializers.SerializerMethodField()
    supporting_documents_list = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractAmendment
        fields = '__all__'
        read_only_fields = ['amendment_id', 'created_at', 'updated_at']
    
    def get_approved_by_display(self, obj):
        """Get display name for approved_by user"""
        return obj.get_approved_by_display()
    
    def get_initiated_by_display(self, obj):
        """Get display name for initiated_by user"""
        return obj.get_initiated_by_display()
    
    def get_amended_clause_ids_list(self, obj):
        """Get amended clause IDs as a list"""
        return obj.get_amended_clause_ids_list()
    
    def get_amended_term_ids_list(self, obj):
        """Get amended term IDs as a list"""
        return obj.get_amended_term_ids_list()
    
    def get_supporting_documents_list(self, obj):
        """Get supporting documents as a list"""
        return obj.get_supporting_documents_list()
    
    def validate_amendment_number(self, value):
        """Validate amendment number is not blank"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Amendment number cannot be blank")
        return value.strip()
    
    def validate_amendment_reason(self, value):
        """Validate amendment reason is not blank"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Amendment reason cannot be blank")
        return value.strip()
    
    def validate_changes_summary(self, value):
        """Validate changes summary is not blank"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Changes summary cannot be blank")
        return value.strip()
    
    def validate_financial_impact(self, value):
        """Validate financial impact"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Financial impact cannot be negative")
        return value
    
    def validate_contract_id(self, value):
        """Validate contract exists"""
        if not VendorContract.objects.filter(contract_id=value).exists():
            raise serializers.ValidationError("Contract does not exist")
        return value
    
    def validate_approved_by(self, value):
        """Validate approved_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Approved by user does not exist")
        return value
    
    def validate_initiated_by(self, value):
        """Validate initiated_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Initiated by user does not exist")
        return value
    
    def validate_workflow_status(self, value):
        """Validate workflow status"""
        valid_statuses = ['pending', 'approved', 'rejected', 'under_review']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid workflow status. Must be one of: {', '.join(valid_statuses)}")
        return value
    
    def validate_affected_area(self, value):
        """Validate affected area"""
        valid_areas = ['terms', 'clauses', 'both']
        if value is not None and value not in valid_areas:
            raise serializers.ValidationError(f"Invalid affected area. Must be one of: {', '.join(valid_areas)}")
        return value
    
    def validate_amended_clause_ids(self, value):
        """Validate amended clause IDs format"""
        if value:
            # Check if it's a comma-separated list of integers
            try:
                ids = [int(id.strip()) for id in value.split(',') if id.strip()]
                return ','.join(map(str, ids))
            except ValueError:
                raise serializers.ValidationError("Amended clause IDs must be comma-separated integers")
        return value
    
    def validate_amended_term_ids(self, value):
        """Validate amended term IDs format"""
        if value:
            # Check if it's a comma-separated list of integers
            try:
                ids = [int(id.strip()) for id in value.split(',') if id.strip()]
                return ','.join(map(str, ids))
            except ValueError:
                raise serializers.ValidationError("Amended term IDs must be comma-separated integers")
        return value
    
    def validate_supporting_documents(self, value):
        """Validate supporting documents JSON format"""
        if value is not None:
            if isinstance(value, str):
                import json
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    raise serializers.ValidationError("Supporting documents must be valid JSON")
        return value
    
    def validate_dates(self, data):
        """Validate amendment and effective dates"""
        amendment_date = data.get('amendment_date')
        effective_date = data.get('effective_date')
        approval_date = data.get('approval_date')
        initiated_date = data.get('initiated_date')
        
        if amendment_date and effective_date and effective_date < amendment_date:
            raise serializers.ValidationError("Effective date cannot be before amendment date")
        
        if approval_date and amendment_date and approval_date < amendment_date:
            raise serializers.ValidationError("Approval date cannot be before amendment date")
        
        if initiated_date and amendment_date and initiated_date > amendment_date:
            raise serializers.ValidationError("Initiated date cannot be after amendment date")
        
        return data
    
    def validate_workflow_consistency(self, data):
        """Validate workflow status consistency"""
        workflow_status = data.get('workflow_status')
        approval_date = data.get('approval_date')
        
        if workflow_status == 'approved' and not approval_date:
            raise serializers.ValidationError("Approval date is required when workflow status is approved")
        
        return data
    
    def validate_affected_area_consistency(self, data):
        """Validate affected area consistency with amended IDs"""
        affected_area = data.get('affected_area')
        amended_clause_ids = data.get('amended_clause_ids')
        amended_term_ids = data.get('amended_term_ids')
        
        if affected_area == 'terms' and amended_clause_ids:
            raise serializers.ValidationError("Cannot have amended clause IDs when affected area is 'terms'")
        
        if affected_area == 'clauses' and amended_term_ids:
            raise serializers.ValidationError("Cannot have amended term IDs when affected area is 'clauses'")
        
        return data
    
    def validate(self, data):
        """Validate the entire amendment data"""
        # Validate dates
        data = self.validate_dates(data)
        
        # Validate workflow consistency
        data = self.validate_workflow_consistency(data)
        
        # Validate affected area consistency
        data = self.validate_affected_area_consistency(data)
        
        return data


class ContractAmendmentCreateSerializer(AutoDecryptingModelSerializer):
    """Simplified serializer for contract amendment creation"""
    
    contract_id = serializers.IntegerField()
    approved_by = serializers.IntegerField(required=False, allow_null=True)
    initiated_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = ContractAmendment
        fields = [
            'contract_id', 'amendment_number', 'amendment_date', 
            'amendment_reason', 'changes_summary', 'financial_impact',
            'approved_by', 'effective_date', 'attachment_path',
            'amended_clause_ids', 'amended_term_ids', 'affected_area',
            'workflow_status', 'approval_date', 'amendment_version',
            'justification', 'supporting_documents', 'initiated_by',
            'initiated_date', 'amendment_notes'
        ]
    
    def validate_contract_id(self, value):
        """Validate contract exists"""
        if not VendorContract.objects.filter(contract_id=value).exists():
            raise serializers.ValidationError("Contract does not exist")
        return value
    
    def validate_approved_by(self, value):
        """Validate approved_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Approved by user does not exist")
        return value
    
    def validate_initiated_by(self, value):
        """Validate initiated_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Initiated by user does not exist")
        return value
    
    def validate_workflow_status(self, value):
        """Validate workflow status"""
        valid_statuses = ['pending', 'approved', 'rejected', 'under_review']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid workflow status. Must be one of: {', '.join(valid_statuses)}")
        return value
    
    def validate_affected_area(self, value):
        """Validate affected area"""
        valid_areas = ['terms', 'clauses', 'both']
        if value is not None and value not in valid_areas:
            raise serializers.ValidationError(f"Invalid affected area. Must be one of: {', '.join(valid_areas)}")
        return value
    
    def validate_amendment_number(self, value):
        """Validate amendment number is not blank"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Amendment number cannot be blank")
        return value.strip()
    
    def validate_amendment_reason(self, value):
        """Validate amendment reason is not blank"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Amendment reason cannot be blank")
        return value.strip()
    
    def validate_changes_summary(self, value):
        """Validate changes summary is not blank"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Changes summary cannot be blank")
        return value.strip()
    
    def validate_financial_impact(self, value):
        """Validate financial impact"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Financial impact cannot be negative")
        return value
    
    def validate(self, data):
        """Validate the entire amendment data"""
        # Validate dates
        amendment_date = data.get('amendment_date')
        effective_date = data.get('effective_date')
        
        if amendment_date and effective_date and effective_date < amendment_date:
            raise serializers.ValidationError("Effective date cannot be before amendment date")
        
        return data


class ContractAmendmentUpdateSerializer(AutoDecryptingModelSerializer):
    """Serializer for contract amendment updates"""
    
    approved_by = serializers.IntegerField(required=False, allow_null=True)
    initiated_by = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = ContractAmendment
        fields = [
            'amendment_number', 'amendment_date', 'amendment_reason', 
            'changes_summary', 'financial_impact', 'approved_by', 
            'effective_date', 'attachment_path', 'amended_clause_ids',
            'amended_term_ids', 'affected_area', 'workflow_status',
            'approval_date', 'amendment_version', 'justification',
            'supporting_documents', 'initiated_by', 'initiated_date',
            'amendment_notes'
        ]
    
    def validate_approved_by(self, value):
        """Validate approved_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Approved by user does not exist")
        return value
    
    def validate_initiated_by(self, value):
        """Validate initiated_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Initiated by user does not exist")
        return value
    
    def validate_workflow_status(self, value):
        """Validate workflow status"""
        valid_statuses = ['pending', 'approved', 'rejected', 'under_review']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid workflow status. Must be one of: {', '.join(valid_statuses)}")
        return value
    
    def validate_affected_area(self, value):
        """Validate affected area"""
        valid_areas = ['terms', 'clauses', 'both']
        if value is not None and value not in valid_areas:
            raise serializers.ValidationError(f"Invalid affected area. Must be one of: {', '.join(valid_areas)}")
        return value
    
    def validate_amendment_number(self, value):
        """Validate amendment number is not blank"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Amendment number cannot be blank")
        return value.strip()
    
    def validate_amendment_reason(self, value):
        """Validate amendment reason is not blank"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Amendment reason cannot be blank")
        return value.strip()
    
    def validate_changes_summary(self, value):
        """Validate changes summary is not blank"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Changes summary cannot be blank")
        return value.strip()
    
    def validate_financial_impact(self, value):
        """Validate financial impact"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Financial impact cannot be negative")
        return value
    
    def validate(self, data):
        """Validate the entire amendment data"""
        # Validate dates
        amendment_date = data.get('amendment_date')
        effective_date = data.get('effective_date')
        
        if amendment_date and effective_date and effective_date < amendment_date:
            raise serializers.ValidationError("Effective date cannot be before amendment date")
        
        return data


class ContractAmendmentSearchSerializer(serializers.Serializer):
    """Serializer for contract amendment search parameters"""
    
    contract_id = serializers.IntegerField(required=False)
    amendment_number = serializers.CharField(required=False, allow_blank=True)
    amendment_reason = serializers.CharField(required=False, allow_blank=True)
    approved_by = serializers.IntegerField(required=False)
    amendment_date_from = serializers.DateTimeField(required=False)
    amendment_date_to = serializers.DateTimeField(required=False)
    effective_date_from = serializers.DateTimeField(required=False)
    effective_date_to = serializers.DateTimeField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)


class VendorContactSearchSerializer(serializers.Serializer):
    """Serializer for vendor contact search parameters"""
    
    vendor_id = serializers.IntegerField(required=False)
    contact_type = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    designation = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)
    is_primary = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)


class ContractRenewalSerializer(AutoDecryptingModelSerializer):
    """Serializer for ContractRenewal model"""
    
    # Computed fields
    initiated_by_display = serializers.SerializerMethodField()
    decided_by_display = serializers.SerializerMethodField()
    renewal_documents_list = serializers.SerializerMethodField()
    
    # Contract details
    contract_title = serializers.SerializerMethodField()
    contract_value = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    contract_risk_score = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractRenewal
        fields = '__all__'
        read_only_fields = ['renewal_id']
    
    def get_initiated_by_display(self, obj):
        """Get display name for initiated_by user"""
        return obj.get_initiated_by_display()
    
    def get_decided_by_display(self, obj):
        """Get display name for decided_by user"""
        return obj.get_decided_by_display()
    
    def get_renewal_documents_list(self, obj):
        """Get renewal documents as a list"""
        return obj.get_renewal_documents_list()
    
    def get_contract_title(self, obj):
        """Get contract title"""
        try:
            contract = VendorContract.objects.get(contract_id=obj.contract_id)
            return contract.contract_title
        except VendorContract.DoesNotExist:
            return None
    
    def get_contract_value(self, obj):
        """Get contract value"""
        try:
            contract = VendorContract.objects.get(contract_id=obj.contract_id)
            return contract.contract_value
        except VendorContract.DoesNotExist:
            return None
    
    def get_currency(self, obj):
        """Get contract currency"""
        try:
            contract = VendorContract.objects.get(contract_id=obj.contract_id)
            return contract.currency
        except VendorContract.DoesNotExist:
            return None
    
    def get_contract_risk_score(self, obj):
        """Get contract risk score"""
        try:
            contract = VendorContract.objects.get(contract_id=obj.contract_id)
            return contract.contract_risk_score
        except VendorContract.DoesNotExist:
            return None
    
    def get_vendor(self, obj):
        """Get vendor details"""
        try:
            contract = VendorContract.objects.get(contract_id=obj.contract_id)
            if contract.vendor:
                # Get primary contact email
                primary_contact = contract.vendor.get_primary_contact()
                contact_email = primary_contact.email if primary_contact else None
                
                return {
                    'vendor_id': contract.vendor.vendor_id,
                    'company_name': contract.vendor.company_name,
                    'contact_email': contact_email
                }
            return None
        except VendorContract.DoesNotExist:
            return None
    
    def validate_initiated_by(self, value):
        """Validate initiated_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Initiated by user does not exist")
        return value
    
    def validate_decided_by(self, value):
        """Validate decided_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Decided by user does not exist")
        return value
    
    def validate_renewal_decision(self, value):
        """Validate renewal decision"""
        valid_decisions = ['RENEW', 'RENEGOTIATE', 'TERMINATE', 'PENDING']
        if value not in valid_decisions:
            raise serializers.ValidationError(f"Invalid renewal decision. Must be one of: {', '.join(valid_decisions)}")
        return value
    
    def validate_status(self, value):
        """Validate status"""
        valid_statuses = ['initiated', 'under_review', 'decision_made']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value
    
    def validate_renewal_documents(self, value):
        """Validate renewal documents JSON format"""
        if value is not None:
            if isinstance(value, str):
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    raise serializers.ValidationError("Renewal documents must be valid JSON")
        return value
    
    def validate_dates(self, data):
        """Validate renewal dates"""
        renewal_date = data.get('renewal_date')
        decision_date = data.get('decision_date')
        decision_due_date = data.get('decision_due_date')
        notification_sent_date = data.get('notification_sent_date')
        
        # Date validation removed - allow any date combinations
        
        # Date validation removed - allow any date combinations
        
        # Date validation removed - allow any date combinations
        
        return data
    
    def validate_decision_consistency(self, data):
        """Validate decision consistency"""
        renewal_decision = data.get('renewal_decision')
        decision_date = data.get('decision_date')
        decided_by = data.get('decided_by')
        # new_contract_id removed as field is no longer used
        
        if renewal_decision != 'PENDING':
            if not decision_date:
                raise serializers.ValidationError("Decision date is required when renewal decision is not pending")
            if not decided_by:
                raise serializers.ValidationError("Decided by is required when renewal decision is not pending")
        
        # Note: new_contract_id validation removed as field is no longer used
        
        return data
    
    def validate(self, data):
        """Validate the entire renewal data"""
        # Validate dates
        data = self.validate_dates(data)
        
        # Validate decision consistency
        data = self.validate_decision_consistency(data)
        
        return data


class ContractRenewalCreateSerializer(AutoDecryptingModelSerializer):
    """Serializer for creating ContractRenewal instances"""
    
    class Meta:
        model = ContractRenewal
        fields = [
            'contract_id', 'renewal_date', 'notification_sent_date', 'decision_due_date',
            'renewal_decision', 'decided_by', 'decision_date',
            'comments', 'initiated_by', 'initiated_date', 'renewal_reason',
            'renewal_documents', 'status', 'renewed_contract_id'
        ]
    
    def validate(self, data):
        """Validate the entire renewal data"""
        # Debug: Log the data being validated
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"ContractRenewalCreateSerializer validation - Input data: {data}")
        
        # Validate dates
        data = self.validate_dates(data)
        
        # Validate decision consistency
        data = self.validate_decision_consistency(data)
        
        # Debug: Log the validated data
        logger.info(f"ContractRenewalCreateSerializer validation - Validated data: {data}")
        
        return data
    
    def create(self, validated_data):
        """Override create to add debugging"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"ContractRenewalCreateSerializer create - validated_data: {validated_data}")
        
        # Create the instance
        instance = super().create(validated_data)
        
        # Debug: Log the created instance
        logger.info(f"ContractRenewalCreateSerializer create - created instance ID: {instance.renewal_id}")
        logger.info(f"ContractRenewalCreateSerializer create - notification_sent_date: {instance.notification_sent_date}")
        logger.info(f"ContractRenewalCreateSerializer create - decision_due_date: {instance.decision_due_date}")
        logger.info(f"ContractRenewalCreateSerializer create - decision_date: {instance.decision_date}")
        logger.info(f"ContractRenewalCreateSerializer create - comments: {instance.comments}")
        logger.info(f"ContractRenewalCreateSerializer create - renewal_reason: {instance.renewal_reason}")
        
        return instance
    
    def validate_initiated_by(self, value):
        """Validate initiated_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Initiated by user does not exist")
        return value
    
    def validate_decided_by(self, value):
        """Validate decided_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Decided by user does not exist")
        return value
    
    def validate_renewal_decision(self, value):
        """Validate renewal decision"""
        valid_decisions = ['RENEW', 'RENEGOTIATE', 'TERMINATE', 'PENDING']
        if value not in valid_decisions:
            raise serializers.ValidationError(f"Invalid renewal decision. Must be one of: {', '.join(valid_decisions)}")
        return value
    
    def validate_status(self, value):
        """Validate status"""
        valid_statuses = ['initiated', 'under_review', 'decision_made']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value
    
    def validate_renewal_documents(self, value):
        """Validate renewal documents JSON format"""
        if value is not None:
            if isinstance(value, str):
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    raise serializers.ValidationError("Renewal documents must be valid JSON")
        return value
    
    def validate_dates(self, data):
        """Validate renewal dates"""
        renewal_date = data.get('renewal_date')
        decision_date = data.get('decision_date')
        decision_due_date = data.get('decision_due_date')
        notification_sent_date = data.get('notification_sent_date')
        
        # Date validation removed - allow any date combinations
        
        # Date validation removed - allow any date combinations
        
        # Date validation removed - allow any date combinations
        
        return data
    
    def validate_decision_consistency(self, data):
        """Validate decision consistency"""
        renewal_decision = data.get('renewal_decision')
        decision_date = data.get('decision_date')
        decided_by = data.get('decided_by')
        # new_contract_id removed as field is no longer used
        
        if renewal_decision != 'PENDING':
            if not decision_date:
                raise serializers.ValidationError("Decision date is required when renewal decision is not pending")
            if not decided_by:
                raise serializers.ValidationError("Decided by is required when renewal decision is not pending")
        
        # Note: new_contract_id validation removed as field is no longer used
        
        return data
    
    def validate(self, data):
        """Validate the entire renewal data"""
        # Validate dates
        data = self.validate_dates(data)
        
        # Validate decision consistency
        data = self.validate_decision_consistency(data)
        
        return data


class ContractRenewalUpdateSerializer(AutoDecryptingModelSerializer):
    """Serializer for updating ContractRenewal instances"""
    
    class Meta:
        model = ContractRenewal
        fields = [
            'contract_id', 'renewal_date', 'notification_sent_date', 'decision_due_date',
            'renewal_decision', 'decided_by', 'decision_date',
            'comments', 'initiated_by', 'initiated_date', 'renewal_reason',
            'renewal_documents', 'status', 'renewed_contract_id'
        ]
    
    def validate_initiated_by(self, value):
        """Validate initiated_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Initiated by user does not exist")
        return value
    
    def validate_decided_by(self, value):
        """Validate decided_by user exists"""
        if value is not None:
            try:
                User.objects.get(userid=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Decided by user does not exist")
        return value
    
    def validate_renewal_decision(self, value):
        """Validate renewal decision"""
        valid_decisions = ['RENEW', 'RENEGOTIATE', 'TERMINATE', 'PENDING']
        if value not in valid_decisions:
            raise serializers.ValidationError(f"Invalid renewal decision. Must be one of: {', '.join(valid_decisions)}")
        return value
    
    def validate_status(self, value):
        """Validate status"""
        valid_statuses = ['initiated', 'under_review', 'decision_made']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value
    
    def validate_renewal_documents(self, value):
        """Validate renewal documents JSON format"""
        if value is not None:
            if isinstance(value, str):
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    raise serializers.ValidationError("Renewal documents must be valid JSON")
        return value
    
    def validate_dates(self, data):
        """Validate renewal dates"""
        renewal_date = data.get('renewal_date')
        decision_date = data.get('decision_date')
        decision_due_date = data.get('decision_due_date')
        notification_sent_date = data.get('notification_sent_date')
        
        # Date validation removed - allow any date combinations
        
        # Date validation removed - allow any date combinations
        
        # Date validation removed - allow any date combinations
        
        return data
    
    def validate_decision_consistency(self, data):
        """Validate decision consistency"""
        renewal_decision = data.get('renewal_decision')
        decision_date = data.get('decision_date')
        decided_by = data.get('decided_by')
        # new_contract_id removed as field is no longer used
        
        if renewal_decision != 'PENDING':
            if not decision_date:
                raise serializers.ValidationError("Decision date is required when renewal decision is not pending")
            if not decided_by:
                raise serializers.ValidationError("Decided by is required when renewal decision is not pending")
        
        # Note: new_contract_id validation removed as field is no longer used
        
        return data
    
    def validate(self, data):
        """Validate the entire renewal data"""
        # Validate dates
        data = self.validate_dates(data)
        
        # Validate decision consistency
        data = self.validate_decision_consistency(data)
        
        return data


class ContractRenewalSearchSerializer(serializers.Serializer):
    """Serializer for contract renewal search parameters"""
    
    contract_id = serializers.IntegerField(required=False)
    renewal_decision = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    initiated_by = serializers.IntegerField(required=False)
    decided_by = serializers.IntegerField(required=False)
    renewal_date_from = serializers.DateField(required=False)
    renewal_date_to = serializers.DateField(required=False)
    decision_date_from = serializers.DateField(required=False)
    decision_date_to = serializers.DateField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)


class ContractApprovalSerializer(AutoDecryptingModelSerializer):
    """Serializer for ContractApproval model"""
    
    is_overdue = serializers.SerializerMethodField()
    contract_object = serializers.SerializerMethodField()
    assigner = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()
    object_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ContractApproval
        fields = [
            'approval_id', 'workflow_id', 'workflow_name', 'assigner_id', 'assigner_name',
            'assignee_id', 'assignee_name', 'object_type', 'object_id', 'assigned_date',
            'due_date', 'status', 'comment_text', 'approved_date', 'created_at', 'updated_at',
            'is_overdue', 'contract_object', 'assigner', 'assignee', 'object_type_display', 'status_display'
        ]
        read_only_fields = ['approval_id', 'created_at', 'updated_at']
    
    def get_is_overdue(self, obj):
        """Check if the approval is overdue"""
        return obj.is_overdue()
    
    def get_contract_object(self, obj):
        """Get the related contract object details"""
        contract = obj.get_contract()
        if contract:
            if hasattr(contract, 'contract_title'):
                return {
                    'id': getattr(contract, 'contract_id', getattr(contract, 'amendment_id', getattr(contract, 'renewal_id', None))),
                    'title': getattr(contract, 'contract_title', getattr(contract, 'amendment_title', getattr(contract, 'renewal_title', 'N/A'))),
                    'type': obj.object_type,
                    'status': getattr(contract, 'status', 'N/A')
                }
        return None
    
    def get_assigner(self, obj):
        """Get assigner user details"""
        try:
            from tprm_backend.mfa_auth.models import User
            user = User.objects.get(userid=obj.assigner_id)
            return {
                'userid': user.userid,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email
            }
        except User.DoesNotExist:
            return {
                'userid': obj.assigner_id,
                'username': obj.assigner_name,
                'first_name': '',
                'last_name': '',
                'email': ''
            }
    
    def get_assignee(self, obj):
        """Get assignee user details"""
        try:
            from tprm_backend.mfa_auth.models import User
            user = User.objects.get(userid=obj.assignee_id)
            return {
                'userid': user.userid,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email
            }
        except User.DoesNotExist:
            return {
                'userid': obj.assignee_id,
                'username': obj.assignee_name,
                'first_name': '',
                'last_name': '',
                'email': ''
            }
    
    def get_object_type_display(self, obj):
        """Get human-readable object type"""
        return obj.get_object_type_display()
    
    def get_status_display(self, obj):
        """Get human-readable status"""
        return obj.get_status_display()


class ContractApprovalCreateSerializer(AutoDecryptingModelSerializer):
    """Serializer for creating ContractApproval instances"""
    
    class Meta:
        model = ContractApproval
        fields = [
            'workflow_id', 'workflow_name', 'assigner_id', 'assigner_name',
            'assignee_id', 'assignee_name', 'object_type', 'object_id',
            'assigned_date', 'due_date', 'status', 'comment_text', 'approved_date'
        ]
    
    def validate(self, data):
        """Validate approval data"""
        # Validate due_date is not before assigned_date
        if data.get('due_date') and data.get('assigned_date') and data['due_date'] < data['assigned_date']:
            raise serializers.ValidationError("Due date cannot be before assigned date")
        
        # Validate object_id exists for the given object_type
        if data.get('object_id') and data.get('object_type'):
            approval = ContractApproval(
                object_type=data['object_type'],
                object_id=data['object_id']
            )
            contract = approval.get_contract()
            if not contract:
                raise serializers.ValidationError(f"Object with ID {data['object_id']} not found for type {data['object_type']}")
        
        return data


class ContractApprovalUpdateSerializer(AutoDecryptingModelSerializer):
    """Serializer for updating ContractApproval instances"""
    
    class Meta:
        model = ContractApproval
        fields = ['status', 'comment_text', 'approved_date']
    
    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance:
            current_status = self.instance.status
            valid_transitions = {
                'ASSIGNED': ['IN_PROGRESS', 'COMMENTED', 'SKIPPED', 'CANCELLED'],
                'IN_PROGRESS': ['COMMENTED', 'SKIPPED', 'CANCELLED'],
                'COMMENTED': ['IN_PROGRESS', 'SKIPPED', 'CANCELLED'],
                'SKIPPED': ['IN_PROGRESS', 'CANCELLED'],
                'EXPIRED': ['CANCELLED'],
                'CANCELLED': []
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(f"Invalid status transition from {current_status} to {value}")
        
        return value


class ContractApprovalFilterSerializer(serializers.Serializer):
    """Serializer for filtering ContractApproval instances"""
    
    workflow_id = serializers.IntegerField(required=False)
    assignee_id = serializers.IntegerField(required=False)
    object_type = serializers.ChoiceField(choices=ContractApproval.OBJECT_TYPE_CHOICES, required=False)
    object_id = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(choices=ContractApproval.STATUS_CHOICES, required=False)
    is_overdue = serializers.BooleanField(required=False)
    assigned_date_from = serializers.DateTimeField(required=False)
    assigned_date_to = serializers.DateTimeField(required=False)
    due_date_from = serializers.DateTimeField(required=False)
    due_date_to = serializers.DateTimeField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)
