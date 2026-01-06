#!/usr/bin/env python3
"""
Simple script to add tenant_id extraction to all functions in policy.py
"""

import re

def add_tenant_id(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified_lines = []
    i = 0
    added_count = 0
    
    while i < len(lines):
        line = lines[i]
        modified_lines.append(line)
        
        # Check if this is a function definition
        if line.strip().startswith('def ') and '(request' in line and line.strip().endswith(':'):
            # Check next few lines for docstring
            j = i + 1
            
            # Skip past docstring if it exists
            if j < len(lines) and (lines[j].strip().startswith('"""') or lines[j].strip().startswith("'''")):
                # Multi-line docstring
                modified_lines.append(lines[j])
                j += 1
                
                # Find end of docstring
                while j < len(lines):
                    modified_lines.append(lines[j])
                    if '"""' in lines[j] or "'''" in lines[j]:
                        j += 1
                        break
                    j += 1
            
            # Now j points to the first line after function def (and docstring if any)
            # Check if tenant_id extraction already exists
            if j < len(lines) and 'tenant_id = get_tenant_id_from_request(request)' not in ''.join(lines[i:min(i+10, len(lines))]):
                # Add tenant_id extraction
                modified_lines.append("    # MULTI-TENANCY: Extract tenant_id from request\n")
                modified_lines.append("    tenant_id = get_tenant_id_from_request(request)\n")
                modified_lines.append("    \n")
                added_count += 1
            
            i = j
            continue
        
        i += 1
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)
    
    return added_count

if __name__ == '__main__':
    file_path = 'grc_backend/grc/routes/Policy/policy.py'
    added = add_tenant_id(file_path)
    print(f"[SUCCESS] Added tenant_id extraction to {added} functions")

