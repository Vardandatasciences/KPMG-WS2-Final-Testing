import os

file_path = r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\grc\routes\Incident\incident_views.py'

if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Fix the corrupted quote escaping
    new_content = content.replace('\\"', '"')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fix applied to incident_views.py")
else:
    print("File not found")
