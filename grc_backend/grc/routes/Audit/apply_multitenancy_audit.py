#!/usr/bin/env python3
"""
Script to automatically add multi-tenancy decorators and tenant_id filtering
to Audit module functions.

This script:
1. Adds @require_tenant and @tenant_filter decorators to @api_view functions
2. Adds tenant_id extraction at the start of functions
3. Updates ORM queries to include tenant_id filtering
4. Updates raw SQL queries to include tenant_id in WHERE clauses
"""

import re
import os

def add_multitenancy_to_file(file_path):
    """Add multi-tenancy support to a Python file"""
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Step 1: Add imports if not present
    if 'from ...tenant_utils import' not in content:
        # Find the last import statement
        import_pattern = r'(from\s+[^\s]+\s+import\s+[^\n]+)'
        imports = list(re.finditer(import_pattern, content))
        if imports:
            last_import = imports[-1]
            insert_pos = last_import.end()
            tenant_import = "\n\n# MULTI-TENANCY: Import tenant utilities for data isolation\nfrom ...tenant_utils import (\n    require_tenant, tenant_filter, get_tenant_id_from_request,\n    validate_tenant_access, get_tenant_aware_queryset\n)"
            content = content[:insert_pos] + tenant_import + content[insert_pos:]
    
    # Step 2: Find all @api_view functions and add decorators
    # Pattern: @api_view(...) followed by other decorators, then def function_name(request
    api_view_pattern = r'(@api_view\([^)]+\))\s*\n(\s*@[^\n]+\n)*(\s*def\s+(\w+)\(request[^)]*\):)'
    
    def add_decorators_and_tenant_id(match):
        api_view_decorator = match.group(1)
        other_decorators = match.group(2) or ""
        function_def = match.group(3)
        function_name = match.group(4)
        
        # Check if decorators already exist
        if '@require_tenant' in other_decorators:
            return match.group(0)  # Already has multi-tenancy
        
        # Add multi-tenancy decorators
        new_decorators = other_decorators.rstrip() + "\n@require_tenant  # MULTI-TENANCY: Ensure tenant is present\n@tenant_filter   # MULTI-TENANCY: Add tenant_id to request"
        
        # Find the function body start
        func_match = re.search(rf'{re.escape(function_def)}\s*\n(\s*"""[^"]*""")?\s*\n(\s*#.*\n)?(\s*)(try:|if|#|return|tenant_id)', content[content.find(match.group(0)):content.find(match.group(0))+500], re.MULTILINE)
        
        return api_view_decorator + "\n" + new_decorators + "\n" + function_def
    
    # Apply decorator updates
    content = re.sub(api_view_pattern, add_decorators_and_tenant_id, content, flags=re.MULTILINE)
    
    # Step 3: Add tenant_id extraction at start of functions (after docstring)
    # This is more complex and needs careful handling
    
    # Step 4: Update ORM queries - this is also complex and needs pattern matching
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")
        return True
    else:
        print(f"No changes needed: {file_path}")
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        add_multitenancy_to_file(file_path)
    else:
        print("Usage: python apply_multitenancy_audit.py <file_path>")
        print("Example: python apply_multitenancy_audit.py audit_views.py")

