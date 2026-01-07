#!/usr/bin/env python3
"""
Script to update remaining .objects.filter() calls with existing parameters
"""

import re

def update_remaining_filters(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    models_to_filter = [
        'Policy', 'SubPolicy', 'Framework', 'PolicyApproval', 'PolicyVersion',
        'FrameworkVersion', 'FrameworkApproval', 'Users', 'PolicyCategory',
        'Entity', 'Department', 'FrameworkControl', 'AuditFinding',
        'PolicyAcknowledgementRequest', 'PolicyAcknowledgementUser'
    ]
    
    update_count = 0
    
    for model in models_to_filter:
        # Pattern to match: Model.objects.filter( followed by any parameter that's NOT tenant_id
        # This handles cases like: Policy.objects.filter(PolicyId=123)
        pattern = rf'({model}\.objects\.filter\()([A-Za-z_][A-Za-z0-9_]*=)'
        
        def add_tenant_before_param(match):
            nonlocal update_count
            full_match = match.group(0)
            
            # Check if this already has tenant_id (check backwards in content for context)
            # Get position and check nearby context
            if 'tenant_id=tenant_id' in full_match:
                return full_match
            
            filter_start = match.group(1)  # Model.objects.filter(
            first_param = match.group(2)    # FirstParam=
            
            # Only add if first_param is not already tenant_id
            if 'tenant_id' not in first_param:
                update_count += 1
                return filter_start + 'tenant_id=tenant_id, ' + first_param
            
            return full_match
        
        content = re.sub(pattern, add_tenant_before_param, content)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return update_count

if __name__ == '__main__':
    file_path = 'grc_backend/grc/routes/Policy/policy.py'
    print("Updating remaining .filter() calls with parameters...")
    count = update_remaining_filters(file_path)
    
    print(f"\n[SUCCESS] Updated {count} .objects.filter() calls")

