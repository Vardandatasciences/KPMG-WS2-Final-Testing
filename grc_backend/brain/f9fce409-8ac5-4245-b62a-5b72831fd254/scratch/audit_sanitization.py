import os
import re

files_to_sanitize = [
    r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\grc\routes\Audit\audit_views.py',
    r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\grc\routes\Audit\audit_report_views.py',
    r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\grc\routes\Audit\assign_audit.py'
]

# Patterns to replace
# 1. 'message': f'... {str(e)}'
# 2. 'error': str(e)
# 3. 'error': f'... {str(e)}'

replacements = [
    (r"(['\"]message['\"]\s*:\s*f['\"].*?)\{str\(e\)\}(['\"])", r"\1An internal error occurred\2"),
    (r"(['\"]error['\"]\s*:\s*str\(e\))", r"'error': 'An internal error occurred'"),
    (r"(['\"]error['\"]\s*:\s*f['\"].*?)\{str\(e\)\}(['\"])", r"\1An internal error occurred\2"),
    (r"(Response\(\{.*?)str\(e\)(.*?\}\))", r"\1'An internal error occurred'\2")
]

for file_path in files_to_sanitize:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content
        # Targeted replacement for 'message': f'... {str(e)}'
        new_content = re.sub(r"'message':\s*f'.*?\{str\(e\)\}'", "'message': 'An internal error occurred'", new_content)
        new_content = re.sub(r'"message":\s*f".*?\{str\(e\)\}"', '"message": "An internal error occurred"', new_content)
        
        # Targeted replacement for 'error': str(e)
        new_content = re.sub(r"'error':\s*str\(e\)", "'error': 'An internal error occurred'", new_content)
        new_content = re.sub(r'"error":\s*str\(e\)', '"error": "An internal error occurred"', new_content)

        # Targeted replacement for 'details': str(e)
        new_content = re.sub(r"'details':\s*str\(e\)", "'details': 'An internal error occurred'", new_content)
        new_content = re.sub(r'"details":\s*str\(e\)', '"details": "An internal error occurred"', new_content)

        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Sanitized: {file_path}")
        else:
            print(f"No leaks found in: {file_path}")
    else:
        print(f"File not found: {file_path}")
