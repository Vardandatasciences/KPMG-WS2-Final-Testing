"""
Vendor Core Serializers - DRF serializers for vendor models
"""

from rest_framework import serializers
from .models import (
    VendorCategories, Vendors, VendorContacts, 
    VendorDocuments, VendorLifecycleStages, Users, TempVendor,
    ExternalScreeningResult, ScreeningMatch, S3Files
)


class VendorCategoriesSerializer(serializers.ModelSerializer):
    """Serializer for vendor categories with vendor_ prefix"""
    
    class Meta:
        model = VendorCategories
        fields = [
            'category_id', 'category_name', 'category_code',
            'description', 'risk_weight', 'assessment_frequency_months',
            'approval_required', 'criticality_level', 'created_at', 'updated_at'
        ]
        read_only_fields = ['category_id', 'created_at', 'updated_at']
    
    def vendor_validate_category_name(self, value):
        """Validate category name with vendor_ prefix"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Category name must be at least 2 characters long")
        return value.strip()
    
    def vendor_validate_risk_weight(self, value):
        """Validate risk weight with vendor_ prefix"""
        if value is not None and (value < 0 or value > 1):
            raise serializers.ValidationError("Risk weight must be between 0 and 1")
        return value


class VendorLifecycleStagesSerializer(serializers.ModelSerializer):
    """Serializer for vendor lifecycle stages with vendor_ prefix"""
    
    class Meta:
        model = VendorLifecycleStages
        fields = [
            'stage_id', 'stage_name', 'stage_code', 'stage_order',
            'description', 'is_active', 'approval_required', 
            'max_duration_days', 'created_at'
        ]
        read_only_fields = ['stage_id', 'created_at']


class VendorsSerializer(serializers.ModelSerializer):
    """Serializer for vendors with vendor_ prefix"""
    
    vendor_category_name = serializers.CharField(
        source='vendor_category.category_name', 
        read_only=True
    )
    vendor_created_by_username = serializers.CharField(
        source='created_by.username', 
        read_only=True
    )
    
    class Meta:
        model = Vendors
        fields = [
            'vendor_id', 'vendor_code', 'company_name', 'legal_name',
            'business_type', 'incorporation_date', 'tax_id', 'duns_number',
            'website', 'industry_sector', 'annual_revenue', 'employee_count',
            'headquarters_country', 'headquarters_address', 'description',
            'vendor_category', 'vendor_category_name', 'risk_level', 'status',
            'lifecycle_stage', 'onboarding_date', 'last_assessment_date',
            'next_assessment_date', 'is_critical_vendor', 'has_data_access',
            'has_system_access', 'created_by', 'vendor_created_by_username',
            'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'vendor_id', 'created_at', 'updated_at', 
            'vendor_category_name', 'vendor_created_by_username'
        ]
    
    def vendor_validate_company_name(self, value):
        """Validate company name with vendor_ prefix"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Company name must be at least 2 characters long")
        return value.strip()
    
    def vendor_validate_vendor_code(self, value):
        """Validate vendor code with vendor_ prefix"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Vendor code must be at least 3 characters long")
        return value.strip().upper()
    
    def vendor_validate_annual_revenue(self, value):
        """Validate annual revenue with vendor_ prefix"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Annual revenue cannot be negative")
        return value
    
    def vendor_validate_employee_count(self, value):
        """Validate employee count with vendor_ prefix"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Employee count cannot be negative")
        return value


class VendorContactsSerializer(serializers.ModelSerializer):
    """Serializer for vendor contacts with vendor_ prefix"""
    
    vendor_company_name = serializers.CharField(
        source='vendor.company_name', 
        read_only=True
    )
    vendor_full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorContacts
        fields = [
            'contact_id', 'vendor', 'vendor_company_name', 'contact_type',
            'first_name', 'last_name', 'vendor_full_name', 'email',
            'phone', 'mobile', 'designation', 'department',
            'is_primary', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'contact_id', 'created_at', 'updated_at',
            'vendor_company_name', 'vendor_full_name'
        ]
    
    def vendor_get_full_name(self, obj):
        """Get full name with vendor_ prefix"""
        vendor_first = obj.first_name or ""
        vendor_last = obj.last_name or ""
        return f"{vendor_first} {vendor_last}".strip()

    def get_vendor_full_name(self, obj):
        """
        DRF SerializerMethodField expects a method named `get_<field_name>`.
        Provide a thin wrapper around the existing vendor-prefixed helper so
        existing logic keeps working while the field resolves correctly.
        """
        return self.vendor_get_full_name(obj)
    
    def vendor_validate_email(self, value):
        """Validate email with vendor_ prefix"""
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value
    
    def vendor_validate_first_name(self, value):
        """Validate first name with vendor_ prefix"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("First name is required")
        return value.strip()


class VendorDocumentsSerializer(serializers.ModelSerializer):
    """Serializer for vendor documents with vendor_ prefix"""
    
    vendor_company_name = serializers.CharField(
        source='vendor.company_name', 
        read_only=True
    )
    vendor_uploaded_by_username = serializers.CharField(
        source='uploaded_by.username', 
        read_only=True
    )
    vendor_file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorDocuments
        fields = [
            'document_id', 'vendor', 'vendor_company_name', 'document_type',
            'document_name', 'file_name', 'file_path', 'file_size',
            'vendor_file_size_mb', 'mime_type', 'document_category',
            'expiry_date', 'version_number', 'status', 'uploaded_by',
            'vendor_uploaded_by_username', 'approved_by', 'upload_date',
            'approval_date', 'created_at'
        ]
        read_only_fields = [
            'document_id', 'upload_date', 'created_at',
            'vendor_company_name', 'vendor_uploaded_by_username',
            'vendor_file_size_mb'
        ]
    
    def vendor_get_file_size_mb(self, obj):
        """Get file size in MB with vendor_ prefix"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None
    
    def vendor_validate_document_name(self, value):
        """Validate document name with vendor_ prefix"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Document name must be at least 2 characters long")
        return value.strip()
    
    def vendor_validate_file_size(self, value):
        """Validate file size with vendor_ prefix (max 100MB)"""
        vendor_max_size = 100 * 1024 * 1024  # 100MB
        if value and value > vendor_max_size:
            raise serializers.ValidationError("File size cannot exceed 100MB")
        return value


class UsersSerializer(serializers.ModelSerializer):
    """Serializer for users with vendor_ prefix"""
    
    class Meta:
        model = Users
        fields = [
            'userid', 'username', 'email', 'createdat', 'updatedat'
        ]
        read_only_fields = ['userid', 'createdat', 'updatedat']
        extra_kwargs = {
            'password': {'write_only': True}  # Never expose password
        }
    
    def vendor_validate_username(self, value):
        """Validate username with vendor_ prefix"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long")
        return value.strip()
    
    def vendor_validate_email(self, value):
        """Validate email with vendor_ prefix"""
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value


class TempVendorSerializer(serializers.ModelSerializer):
    """Serializer for temporary vendor registration with vendor_ prefix"""
    
    class Meta:
        model = TempVendor
        fields = [
            'id', 'userid', 'vendor_code', 'company_name', 'legal_name', 'lifecycle_stage',
            'business_type', 'tax_id', 'duns_number', 'incorporation_date', 
            'industry_sector', 'website', 'annual_revenue', 'employee_count', 
            'headquarters_address', 'vendor_category', 'risk_level', 'status', 
            'is_critical_vendor', 'has_data_access', 'has_system_access', 
            'description', 'contacts', 'documents', 'created_at', 'updated_at', 
            'response_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def vendor_validate_company_name(self, value):
        """Validate company name with vendor_ prefix"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Company name must be at least 2 characters long")
        return value.strip()
    
    def vendor_validate_vendor_code(self, value):
        """Validate vendor code with vendor_ prefix"""
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("Vendor code must be at least 3 characters long")
        return value.strip().upper() if value else value
    
    def vendor_validate_annual_revenue(self, value):
        """Validate annual revenue with vendor_ prefix"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Annual revenue cannot be negative")
        return value
    
    def vendor_validate_employee_count(self, value):
        """Validate employee count with vendor_ prefix"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Employee count cannot be negative")
        return value
    
    def vendor_validate_website(self, value):
        """Validate website URL with vendor_ prefix"""
        if value and not (value.startswith('http://') or value.startswith('https://')):
            raise serializers.ValidationError("Website must start with http:// or https://")
        return value
    
    def vendor_validate_contacts(self, value):
        """Validate contacts JSON structure with vendor_ prefix"""
        if value:
            if not isinstance(value, list):
                raise serializers.ValidationError("Contacts must be a list")
            for contact in value:
                if not isinstance(contact, dict):
                    raise serializers.ValidationError("Each contact must be an object")
                required_fields = ['name', 'email']
                for field in required_fields:
                    if field not in contact or not contact[field]:
                        raise serializers.ValidationError(f"Contact {field} is required")
        return value
    
    def vendor_validate_documents(self, value):
        """Validate documents JSON structure with vendor_ prefix"""
        if value:
            if not isinstance(value, list):
                raise serializers.ValidationError("Documents must be a list")
            for document in value:
                if not isinstance(document, dict):
                    raise serializers.ValidationError("Each document must be an object")
                required_fields = ['name', 'type']
                for field in required_fields:
                    if field not in document or not document[field]:
                        raise serializers.ValidationError(f"Document {field} is required")
        return value
    
    def create(self, validated_data):
        """Create new temp vendor with admin user as default"""
        from .views import get_lifecycle_stage_id_by_code
        from django.utils import timezone
        from .models import LifecycleTracker
        
        # Set initial lifecycle stage to 1 (Registration) if not provided
        if not validated_data.get('lifecycle_stage'):
            # Get Registration stage ID, default to 1 if not found
            reg_stage = get_lifecycle_stage_id_by_code('REG')
            validated_data['lifecycle_stage'] = reg_stage or 1
        
        # Create the temp vendor record
        temp_vendor = TempVendor.objects.create(**validated_data)
        
        # Create initial lifecycle tracker entry for Registration stage
        try:
            current_time = timezone.now()
            LifecycleTracker.objects.create(
                vendor_id=temp_vendor.id,
                lifecycle_stage=validated_data['lifecycle_stage'],
                started_at=current_time,
                ended_at=None  # Still in progress
            )
        except Exception as e:
            print(f"Warning: Could not create initial lifecycle tracker entry: {str(e)}")
        
        return temp_vendor
    


class ScreeningMatchSerializer(serializers.ModelSerializer):
    """Serializer for screening matches"""
    
    class Meta:
        model = ScreeningMatch
        fields = [
            'match_id', 'screening', 'match_type', 'match_score', 
            'match_details', 'is_false_positive', 'resolution_status',
            'resolution_notes', 'resolved_by', 'resolved_date'
        ]
        read_only_fields = ['match_id']


class ExternalScreeningResultSerializer(serializers.ModelSerializer):
    """Serializer for external screening results"""
    
    vendor = TempVendorSerializer(read_only=True)
    matches = ScreeningMatchSerializer(many=True, read_only=True)
    vendor_name = serializers.CharField(source='vendor.company_name', read_only=True)
    
    class Meta:
        model = ExternalScreeningResult
        fields = [
            'screening_id', 'vendor', 'vendor_name', 'screening_type', 
            'screening_date', 'search_terms', 'total_matches', 
            'high_risk_matches', 'status', 'last_updated', 
            'reviewed_by', 'review_date', 'review_comments', 'matches'
        ]
        read_only_fields = ['screening_id', 'screening_date', 'last_updated']


class ScreeningRequestSerializer(serializers.Serializer):
    """Serializer for screening request data"""
    
    vendor_id = serializers.IntegerField()
    screening_types = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            'WORLDCHECK', 'OFAC', 'PEP', 'SANCTIONS', 'ADVERSE_MEDIA'
        ]),
        default=['OFAC']
    )
    threshold = serializers.IntegerField(default=85, min_value=50, max_value=100)


class MatchUpdateSerializer(serializers.Serializer):
    """Serializer for updating match status"""
    
    match_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=[
        'PENDING', 'CLEARED', 'ESCALATED', 'BLOCKED'
    ])
    notes = serializers.CharField(required=False, allow_blank=True)


class S3FilesSerializer(serializers.ModelSerializer):
    """Serializer for S3 files with vendor_ prefix"""
    
    class Meta:
        model = S3Files
        fields = [
            'id', 'url', 'file_type', 'file_name', 'user_id', 
            'metadata', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']
    
    def vendor_validate_file_name(self, value):
        """Validate file name with vendor_ prefix"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("File name is required")
        return value.strip()
    
    def vendor_validate_file_type(self, value):
        """Validate file type with vendor_ prefix"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("File type is required")
        return value.strip().lower()
    
    def vendor_validate_user_id(self, value):
        """Validate user ID with vendor_ prefix"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("User ID is required")
        return value.strip()


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload requests"""
    
    file = serializers.FileField()
    document_name = serializers.CharField(max_length=255)
    document_type = serializers.CharField(max_length=50)
    version = serializers.CharField(max_length=20, required=False, default='1.0')
    status = serializers.CharField(max_length=20, required=False, default='Pending')
    expiry_date = serializers.DateField(required=False, allow_null=True)
    vendor_id = serializers.IntegerField(required=False, allow_null=True)
    user_id = serializers.CharField(max_length=100, required=False, allow_null=True)
    
    def vendor_validate_file(self, value):
        """Validate uploaded file with vendor_ prefix"""
        if not value:
            raise serializers.ValidationError("File is required")
        
        # Check file size (max 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 100MB")
        
        # Check file type
        allowed_types = ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'xlsx', 'xls']
        file_extension = value.name.split('.')[-1].lower() if '.' in value.name else ''
        
        if file_extension not in allowed_types:
            raise serializers.ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_types)}")
        
        return value
    
    def vendor_validate_document_name(self, value):
        """Validate document name with vendor_ prefix"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Document name must be at least 2 characters long")
        return value.strip()
    
    def vendor_validate_document_type(self, value):
        """Validate document type with vendor_ prefix"""
        allowed_types = ['License', 'Certificate', 'Contract', 'Insurance', 'Other']
        if value not in allowed_types:
            raise serializers.ValidationError(f"Invalid document type. Allowed types: {', '.join(allowed_types)}")
        return value
    
    def validate(self, data):
        """Ensure at least vendor_id or user_id is provided"""
        if not data.get('vendor_id') and not data.get('user_id'):
            raise serializers.ValidationError("Either vendor_id or user_id must be provided")
        return data
