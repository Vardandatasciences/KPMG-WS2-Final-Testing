import os

files_to_fix = [
    r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\grc\routes\Incident\incident_views.py',
    r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\grc\routes\Audit\audit_views.py',
    r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\grc\routes\Risk\risk_views.py'
]

for path in files_to_fix:
    if os.path.exists(path):
        try:
            # Read with ignore to skip any weird legacy characters
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 1. Fix the corrupted quote escaping from previous PowerShell edits
            # We replace literal \" with just "
            new_content = content.replace('\\"', '"')
            
            # 2. Fix potential mismatched quotes in docstrings if they exist
            # (Heuristic: docstrings should be """...""")
            
            # Write back as clean UTF-8 without BOM
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(new_content)
            print(f"Cleaned and fixed: {path}")
        except Exception as e:
            print(f"Error fixing {path}: {e}")
    else:
        print(f"File not found: {path}")
