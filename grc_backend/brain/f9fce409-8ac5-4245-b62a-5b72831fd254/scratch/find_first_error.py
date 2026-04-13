import sys

path = r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\grc\routes\Incident\incident_views.py'

try:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i in range(len(lines)):
        code = ''.join(lines[:i+1])
        try:
            compile(code, path, 'exec')
        except SyntaxError as e:
            print(f"First error at line {i+1}: {e}")
            sys.exit(0)
    print("No errors found in file")
except Exception as e:
    print(f"Error reading file: {e}")
