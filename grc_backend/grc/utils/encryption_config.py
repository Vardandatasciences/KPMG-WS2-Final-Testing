"""
Encryption Configuration for GRC Models
Defines which fields should be encrypted for each model.

Fields that should NOT be encrypted:
- Primary keys (AutoField, BigAutoField)
- Foreign keys (ForeignKey, OneToOneField)
- Dates/DateTime (DateField, DateTimeField, TimeField)
- Booleans (BooleanField, NullBooleanField)
- Numbers used as IDs or codes (IntegerField, BigIntegerField, DecimalField, FloatField)
- JSON fields (JSONField) - encrypt content if needed
- Binary fields (BinaryField) - already encoded
- UUID fields (UUIDField)

Fields that MAY be encrypted (configure per model):
- CharField (if contains sensitive data)
- TextField (if contains sensitive data)
- EmailField (should be encrypted)
- URLField (if sensitive)
- FilePathField (if sensitive)

Note: Passwords should use hashing (bcrypt/argon2), NOT encryption!
"""

# Configuration: Map model name to list of field names that should be encrypted
ENCRYPTED_FIELDS_CONFIG = {
    # Users model
    'Users': [
        'Email',
        'PhoneNumber',
        'Address',
        'UserName',  # Optional: encrypt username if sensitive
        'FirstName',  # Optional: encrypt names
        'LastName',  # Optional: encrypt names
        # NOTE: Password field is EXCLUDED - passwords must be HASHED (using make_password), not encrypted!
        'session_token',
        'license_key',
    ],
    
    # Policy models
    'Policy': [
        'PolicyName',
        'PolicyDescription',
        'Applicability',
        'Scope',
        'Objective',
        'DocURL',  # URLs might contain sensitive info
    ],
    
    'SubPolicy': [
        'SubPolicyName',
        'Description',
        'Control',
    ],
    
    'Framework': [
        'FrameworkName',
        'FrameworkDescription',
        'DocURL',
        'Identifier',
    ],
    
    # Compliance models
    'Compliance': [
        'ComplianceTitle',
        'ComplianceItemDescription',
        'Scope',
        'Objective',
        'PossibleDamage',
        'PotentialRiskScenarios',
        'BusinessUnitsCovered',
        'Applicability',
    ],
    
    # Audit models
    'Audit': [
        'Title',
        'Scope',
        'Objective',
        'BusinessUnit',
        'Evidence',
        'Comments',
    ],
    
    'AuditFinding': [
        'Evidence',
        'HowToVerify',
        'Impact',
        'Recommendation',
        'DetailsOfFinding',
        'Comments',
    ],
    
    'AuditReport': [
        'Report',
    ],
    
    # Incident models
    'Incident': [
        'IncidentTitle',
        'Description',
        'Comments',
        'InitialImpactAssessment',
        'LessonsLearned',
        'AffectedBusinessUnit',
        'SystemsAssetsInvolved',
        'GeographicLocation',
        'InternalContacts',
        'ExternalPartiesInvolved',
        'RegulatoryBodies',
        'RelevantPoliciesProceduresViolated',
        'ControlFailures',
        'PossibleDamage',
        'AssignmentNotes',
    ],
    
    # Risk models
    'Risk': [
        'RiskTitle',
        'RiskDescription',
        'PossibleDamage',
        'BusinessImpact',
        'RiskMitigation',
    ],
    
    'RiskInstance': [
        'RiskTitle',
        'RiskDescription',
        'PossibleDamage',
        'BusinessImpact',
        'RiskMitigation',
        'RiskResponseDescription',
    ],
    
    # Event models
    'Event': [
        'EventTitle',
        'Description',
        'Comments',
        'LinkedRecordName',
    ],
    
    # External Applications
    'ExternalApplication': [
        'name',
        'description',
        'api_endpoint',
        'oauth_url',
    ],
    
    'ExternalApplicationConnection': [
        'connection_token',
        'refresh_token',
        'projects_data',  # JSON field - encrypt as string if sensitive
    ],
    
    # Document models
    'AuditDocument': [
        'DocumentName',
        'DocumentSummary',
        'ExtractedText',
    ],
    
    'S3File': [
        'file_name',
        'url',  # S3 URLs might be sensitive
    ],
    
    # Business/Organization models
    'BusinessUnit': [
        'Name',
        'Description',
    ],
    
    'Category': [
        'CategoryName',
        'Description',
    ],
    
    'Department': [
        'DepartmentName',
    ],
    
    'Entity': [
        'EntityName',
        'Location',
    ],
    
    'Location': [
        'AddressLine',
        'City',
        'State',
        'Country',
        'PostalCode',
    ],
    
    # Other models
    'Kpi': [
        'Name',
        'Description',
        'Value',
        'FromWhereToAccessData',
        'Formula',
        'AuditTrail',
    ],
    
    'PolicyCategory': [
        'PolicyType',
        'PolicyCategory',
        'PolicySubCategory',
    ],
    
    # AWS Credentials - VERY SENSITIVE
    'AWSCredentials': [
        'accessKey',
        'secretKey',
        'bucketName',
        'microServiceUrl',
    ],
    
    # MFA models
    'MfaEmailChallenge': [
        'OtpHash',  # Already hashed, but double-check
        'IpAddress',
        'UserAgent',
    ],
    
    # Data Subject Requests
    'DataSubjectRequest': [
        # Most fields are metadata, but audit_trail might contain sensitive info
        'audit_trail',  # JSON field
    ],
    
    # Organizational Controls
    'OrganizationalControl': [
        'ControlText',
        'ExtractedText',
    ],
    
    'OrganizationalControlDocument': [
        'DocumentName',
        'DocumentPath',
        'ExtractedText',
    ],
    
    # File Operations
    'FileOperations': [
        'file_name',
        'original_name',
        'stored_name',
        's3_url',
        's3_key',
        'error',  # Error messages might contain sensitive info
        'summary',
    ],
    
    # Integration Data
    'IntegrationDataList': [
        'heading',
        'source',
        'username',
        'data',  # JSON field - might contain sensitive data
        'metadata',  # JSON field
    ],
    
    # OAuth States
    'OAuthState': [
        'state',
        'subdomain',
    ],
    
    # Policy Acknowledgement
    'PolicyAcknowledgementRequest': [
        'Title',
        'Description',
    ],
    
    'PolicyAcknowledgementUser': [
        'Comments',
        'IpAddress',
        'UserAgent',
        'Token',
    ],
    
    # Consent Management
    'ConsentConfiguration': [
        'action_label',
        'consent_text',
    ],
    
    'ConsentAcceptance': [
        'ip_address',
        'user_agent',
    ],
    
    'ConsentWithdrawal': [
        'ip_address',
        'user_agent',
        'reason',
    ],
    
    # Cookie Preferences
    'CookiePreferences': [
        'SessionId',
        'IpAddress',
        'UserAgent',
    ],
    
    # Retention Timeline
    'RetentionTimeline': [
        'RecordName',
        'archive_location',
        'pause_reason',
        'backup_location',
    ],
    
    # Data Lifecycle Audit Log
    'DataLifecycleAuditLog': [
        'record_name',
        'reason',
        'details',  # JSON field
        'notification_recipients',
    ],
    
    # Users Project List
    'UsersProjectList': [
        'project_name',
        'project_details',  # JSON field
    ],
    
    # Notification
    'Notification': [
        'recipient',
        'error',
    ],
    
    # RBAC
    'RBAC': [
        'username',
    ],
    
    # Export Task
    'ExportTask': [
        'file_name',
        's3_url',
        'error',
        'summary',
    ],
    
    # GRC Log
    'GRCLog': [
        'UserName',
        'Description',
        'IPAddress',
    ],
    
    # Password Log
    'PasswordLog': [
        'UserName',
        'OldPassword',  # Already hashed, but for consistency
        'NewPassword',  # Already hashed, but for consistency
        'IPAddress',
        'UserAgent',
    ],
    
    # Access Request
    'AccessRequest': [
        'requested_url',
        'requested_feature',
        'required_permission',
        'requested_role',
        'message',
        'audit_trail',  # JSON field
    ],
    
    # Compliance Baseline
    'ComplianceBaseline': [
        # Mostly metadata, no sensitive text fields
    ],
    
    # Last Checklist Item Verified
    'LastChecklistItemVerified': [
        'Comments',
    ],
    
    # Workflow
    'Workflow': [
        # Mostly foreign keys and dates
    ],
    
    # Audit Document Mapping
    'AuditDocumentMapping': [
        'SectionTitle',
        'SectionContent',
        'AIRecommendations',
        'ReviewComments',
    ],
    
    # External Application Sync Log
    'ExternalApplicationSyncLog': [
        'error_message',
    ],
    
    # Risk Assessment
    'RiskAssessment': [
        'document_url',
        'filename',
        'error_message',
    ],
    
    # Risk Approval
    'RiskApproval': [
        # ExtractedInfo is JSON, handle separately
    ],
    
    # Audit Version
    'AuditVersion': [
        # ExtractedInfo is JSON, handle separately
    ],
    
    # Incident Approval
    'IncidentApproval': [
        # ExtractedInfo is JSON, handle separately
    ],
    
    # Policy Approval
    'PolicyApproval': [
        # ExtractedData is JSON, handle separately
    ],
    
    # Compliance Approval
    'ComplianceApproval': [
        # ExtractedData is JSON, handle separately
    ],
    
    # Framework Approval
    'FrameworkApproval': [
        # ExtractedData is JSON, handle separately
    ],
}


def get_encrypted_fields_for_model(model_name):
    """
    Get list of field names that should be encrypted for a given model.
    
    Args:
        model_name: String name of the model class
        
    Returns:
        List of field names to encrypt, or empty list if none
    """
    return ENCRYPTED_FIELDS_CONFIG.get(model_name, [])


def should_encrypt_field(model_name, field_name):
    """
    Check if a specific field should be encrypted.
    
    Args:
        model_name: String name of the model class
        field_name: String name of the field
        
    Returns:
        True if field should be encrypted, False otherwise
    """
    encrypted_fields = get_encrypted_fields_for_model(model_name)
    return field_name in encrypted_fields


def get_field_type_from_model(model_class, field_name):
    """
    Get the Django field type for a field in a model.
    
    Args:
        model_class: Django model class
        field_name: String name of the field
        
    Returns:
        Field class name (e.g., 'CharField', 'TextField')
    """
    try:
        field = model_class._meta.get_field(field_name)
        return field.__class__.__name__
    except:
        return None


def is_field_encryptable(model_class, field_name):
    """
    Check if a field can/should be encrypted based on its type and configuration.
    
    Args:
        model_class: Django model class
        field_name: String name of the field
        
    Returns:
        True if field can be encrypted, False otherwise
    """
    # Check if field is in encryption config
    if should_encrypt_field(model_class.__name__, field_name):
        return True
    
    # Don't encrypt these field types regardless of config
    field_type = get_field_type_from_model(model_class, field_name)
    non_encryptable_types = [
        'AutoField',
        'BigAutoField',
        'ForeignKey',
        'OneToOneField',
        'ManyToManyField',
        'DateField',
        'DateTimeField',
        'TimeField',
        'BooleanField',
        'NullBooleanField',
        'IntegerField',
        'BigIntegerField',
        'PositiveIntegerField',
        'SmallIntegerField',
        'DecimalField',
        'FloatField',
        'BinaryField',
        'UUIDField',
    ]
    
    if field_type in non_encryptable_types:
        return False
    
    return False  # Only encrypt if explicitly configured


def get_all_encryptable_fields(model_class):
    """
    Get all fields in a model that should be encrypted.
    
    Args:
        model_class: Django model class
        
    Returns:
        List of field names that should be encrypted
    """
    model_name = model_class.__name__
    all_fields = [f.name for f in model_class._meta.get_fields()]
    encryptable_fields = []
    
    for field_name in all_fields:
        if is_field_encryptable(model_class, field_name):
            encryptable_fields.append(field_name)
    
    return encryptable_fields

