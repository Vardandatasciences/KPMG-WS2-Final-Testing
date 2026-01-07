#!/usr/bin/env python3
"""
Script to update .objects.filter() and .objects.get() calls to include tenant_id
"""

import re

def update_filters(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    models_to_filter = [
        'Policy', 'SubPolicy', 'Framework', 'PolicyApproval', 'PolicyVersion',
        'FrameworkVersion', 'FrameworkApproval', 'Users', 'PolicyCategory',
        'Entity', 'Department', 'FrameworkControl', 'AuditFinding'
    ]
    
    modified_lines = []
    filter_count = 0
    get_count = 0
    
    for i, line in enumerate(lines):
        modified_line = line
        
        # Check for .objects.filter( patterns
        for model in models_to_filter:
            # Pattern 1: Model.objects.filter(
            pattern1 = f'{model}.objects.filter('
            if pattern1 in modified_line and 'tenant_id=' not in modified_line:
                # Add tenant_id as first parameter
                modified_line = modified_line.replace(
                    pattern1,
                    f'{model}.objects.filter(tenant_id=tenant_id, '
                )
                filter_count += 1
            
            # Pattern 2: Model.objects.get(
            pattern2 = f'{model}.objects.get('
            if pattern2 in modified_line and 'tenant_id=' not in modified_line:
                # Add tenant_id as first parameter
                modified_line = modified_line.replace(
                    pattern2,
                    f'{model}.objects.get(tenant_id=tenant_id, '
                )
                get_count += 1
        
        modified_lines.append(modified_line)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)
    
    return filter_count, get_count

if __name__ == '__main__':
    file_path = 'grc_backend/grc/routes/Policy/policy.py'
    print("Updating .filter() and .get() calls...")
    filter_count, get_count = update_filters(file_path)
    
    print(f"\n[SUCCESS]")
    print(f"  - .objects.filter() updated: {filter_count}")
    print(f"  - .objects.get() updated: {get_count}")
    print(f"  - Total: {filter_count + get_count}")

