#!/usr/bin/env python3
"""
Script to add tenant_id extraction to all @api_view functions in policy.py
"""

import re

def add_tenant_id_extraction(file_path):
    """Add tenant_id extraction to all functions that don't have it"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match function definition with or without docstring
    # Matches: def function_name(request...):
    #          """docstring""" or '''docstring''' (optional)
    #          [existing code]
    
    def add_extraction(match):
        """Add tenant_id extraction if not already present"""
        full_match = match.group(0)
        
        # Check if tenant_id extraction already exists
        if 'tenant_id = get_tenant_id_from_request(request)' in full_match:
            return full_match
        
        function_def = match.group(1)  # def function_name(request...):
        docstring = match.group(2) if match.group(2) else ""  # Optional docstring
        first_line = match.group(3)  # First line of code
        
        # Build the new function with tenant_id extraction
        tenant_extraction = "\n    # MULTI-TENANCY: Extract tenant_id from request\n    tenant_id = get_tenant_id_from_request(request)\n    "
        
        if docstring:
            # If there's a docstring, add extraction after it
            return function_def + docstring + tenant_extraction + "\n    " + first_line
        else:
            # If no docstring, add extraction right after function definition
            return function_def + tenant_extraction + "\n    " + first_line
    
    # Pattern explanation:
    # (def \w+\(request[^)]*\):\n) - captures function definition
    # (?:    """[^"]*"""\n)?  - optional docstring with """
    # (?:    '''[^']*'''\n)?  - optional docstring with '''
    # (    .*) - captures first line of code
    
    pattern = r'(def \w+\(request[^)]*\):\n)(?:(    """.*?"""\n)|(    \'\'\'.*?\'\'\'\n))?(    [^\n]*)'
    
    modified_content = re.sub(pattern, add_extraction, content, flags=re.MULTILINE | re.DOTALL)
    
    # Count how many were added
    original_count = content.count('tenant_id = get_tenant_id_from_request(request)')
    new_count = modified_content.count('tenant_id = get_tenant_id_from_request(request)')
    added = new_count - original_count
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    return added

if __name__ == '__main__':
    file_path = 'grc_backend/grc/routes/Policy/policy.py'
    added = add_tenant_id_extraction(file_path)
    print(f"Added tenant_id extraction to {added} functions")

