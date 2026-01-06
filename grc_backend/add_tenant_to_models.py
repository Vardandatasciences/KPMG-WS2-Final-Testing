"""
Script to add tenant_id field to all models in models.py
This script adds the tenant ForeignKey to all remaining models that don't have it yet.
"""

import re

# Models that already have tenant_id
MODELS_WITH_TENANT = [
    'Tenant',
    'Users',
    'Framework',
    'Policy',
    'SubPolicy',
    'Compliance',
    'Audit',
    'Incident',
    'Risk',
    'RiskInstance'
]

# Models that should NOT have tenant_id (system/configuration models)
MODELS_WITHOUT_TENANT = [
    'ProductVersion',  # System versioning
    'Module',  # System modules
    'EventType',  # System event types
]

# Tenant field template
TENANT_FIELD = '''    # MULTI-TENANCY: Link to tenant
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='{related_name}', null=True, blank=True,
                               help_text="Tenant this {model_name_lower} belongs to")
'''

def get_related_name(model_name):
    """Generate related_name from model name"""
    # Convert CamelCase to snake_case and pluralize
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', model_name)
    snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    # Simple pluralization
    if snake_case.endswith('y'):
        return snake_case[:-1] + 'ies'
    elif snake_case.endswith('s'):
        return snake_case + 'es'
    else:
        return snake_case + 's'

def process_models_file(input_file='grc/models.py', output_file='grc/models_with_tenant.py'):
    """Process models.py and add tenant_id to all eligible models"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all model class definitions
    model_pattern = r'^class (\w+)\(models\.Model\):\s*\n((?:\s+.*\n)*?)\s+(\w+)\s*=\s*models\.'
    
    def add_tenant_to_model(match):
        model_name = match.group(1)
        class_body_before = match.group(2)  # Everything between class definition and first field
        first_field_line = match.group(3)
        
        # Skip if already has tenant or should not have tenant
        if model_name in MODELS_WITH_TENANT or model_name in MODELS_WITHOUT_TENANT:
            return match.group(0)
        
        # Check if first field is an AutoField (primary key)
        if 'AutoField' in match.group(0):
            # Add tenant field after primary key
            related_name = get_related_name(model_name)
            model_name_lower = model_name.lower()
            tenant_field = TENANT_FIELD.format(
                related_name=related_name,
                model_name_lower=model_name_lower
            )
            
            # Find the primary key line
            pk_pattern = r'(\s+\w+\s*=\s*models\.AutoField\(.*?\)\s*\n)'
            pk_match = re.search(pk_pattern, match.group(0))
            
            if pk_match:
                # Insert tenant field after primary key
                result = match.group(0)[:pk_match.end()] + tenant_field + match.group(0)[pk_match.end():]
                print(f"✓ Added tenant_id to {model_name}")
                return result
        
        return match.group(0)
    
    # Process the file
    modified_content = re.sub(model_pattern, add_tenant_to_model, content, flags=re.MULTILINE)
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print(f"\n✅ Processing complete. Output written to {output_file}")
    print(f"⚠️  Review the changes and replace the original file if satisfied.")

if __name__ == '__main__':
    print("="*80)
    print("MULTI-TENANCY MODEL UPDATER")
    print("="*80)
    print("\nThis script will add tenant_id to all models that don't have it yet.")
    print("Models already updated:", ', '.join(MODELS_WITH_TENANT))
    print("Models excluded:", ', '.join(MODELS_WITHOUT_TENANT))
    print("\n" + "="*80 + "\n")
    
    # Process the file
    process_models_file()

