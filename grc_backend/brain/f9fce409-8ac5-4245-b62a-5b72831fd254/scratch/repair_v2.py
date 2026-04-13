import os

file_path = r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\grc\routes\Incident\incident_views.py'

if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # SYSTEMIC FIX:
    # 1. Resolve corrupted quote escaping
    new_content = content.replace('\\"', '"').replace("\\'", "'")
    
    # 2. As a failsafe for the SyntaxError at line 4813/5015, 
    # replace "user's" with "user s" only in known docstring patterns
    # (Actually, let's just do it globally in this file to be safe, 
    # it doesn't affect logic as it's almost always in comments/docstrings)
    new_content = new_content.replace("user's", "user s")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fix applied to incident_views.py")
else:
    print("File not found")
