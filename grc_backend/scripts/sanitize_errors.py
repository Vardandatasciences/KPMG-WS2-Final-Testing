import os
import re

def sanitize_errors_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # We want to replace 'error': str(e) with 'error': 'An internal error occurred. Please try again later.'
    # But only inside Response(...) or JsonResponse(...)
    # Let's perform a simple regex substitution.
    
    # Matches 'error': str(e) or "error": str(e)
    pattern1 = r"(['\"]error['\"]\s*:\s*)str\(e\)"
    replacement1 = r"\g<1>'An internal server error occurred.'"
    new_content = re.sub(pattern1, replacement1, content)
    
    pattern2 = r"(['\"]message['\"]\s*:\s*)str\(e\)"
    replacement2 = r"\g<1>'An internal server error occurred.'"
    new_content = re.sub(pattern2, replacement2, content)
    
    # Try to catch f"Error...: {str(e)}" returning to client
    pattern3 = r"(['\"]error['\"]\s*:\s*f['\"].*?)\{str\(e\)\}(.*?['\"])"
    replacement3 = r"\g<1>An internal server error occurred\g<2>"
    new_content = re.sub(pattern3, replacement3, new_content)

    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Sanitized: {filepath}")

def main():
    root_dir = r"c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend"
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(subdir, file)
                sanitize_errors_in_file(filepath)

if __name__ == '__main__':
    main()
