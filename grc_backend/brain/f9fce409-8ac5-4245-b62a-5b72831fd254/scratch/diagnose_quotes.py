file_path = r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\grc\routes\Incident\incident_views.py'

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

state = None  # None, 'single', 'double', 'triple_single', 'triple_double'
start_pos = 0

i = 0
while i < len(content):
    if state is None:
        if content[i:i+3] == '"""':
            state = 'triple_double'
            start_pos = i
            i += 3
            continue
        if content[i:i+3] == "'''":
            state = 'triple_single'
            start_pos = i
            i += 3
            continue
        if content[i] == '"':
            state = 'double'
            start_pos = i
        elif content[i] == "'":
            state = 'single'
            start_pos = i
    elif state == 'single':
        if content[i] == "'":
            if content[i-1] != '\\':
                state = None
        elif content[i] == '\n':
            print(f"Unclosed single quote started at position {start_pos} (around line {content[:start_pos].count('\n') + 1})")
            state = None
    elif state == 'double':
        if content[i] == '"':
            if content[i-1] != '\\':
                state = None
        elif content[i] == '\n':
            print(f"Unclosed double quote started at position {start_pos} (around line {content[:start_pos].count('\n') + 1})")
            state = None
    elif state == 'triple_double':
        if content[i:i+3] == '"""':
            if content[i-1] != '\\':
                state = None
                i += 3
                continue
    elif state == 'triple_single':
        if content[i:i+3] == "'''":
            if content[i-1] != '\\':
                state = None
                i += 3
                continue
    i += 1

if state:
    print(f"Unclosed {state} started at position {start_pos} (around line {content[:start_pos].count('\n') + 1})")
