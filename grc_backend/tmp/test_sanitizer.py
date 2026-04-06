import re
import json

# Mimic the logic from s3_fucntions.py
TEMPLATE_TOKEN_RE = re.compile(r"(\{\{|\}\}|\{\%|\%\}|\{\#|\#\})")
EXPORT_MAX_NESTED_DEPTH = 8
EXPORT_MAX_DICT_KEYS = 300
EXPORT_MAX_LIST_ITEMS = 10_000
EXPORT_MAX_STRING_LEN = 10_000

def _sanitize_export_scalar(value):
    if value is None:
        return ""
    
    text = str(value)
    
    # TRUNCATE
    if len(text) > EXPORT_MAX_STRING_LEN:
        text = text[:EXPORT_MAX_STRING_LEN-3] + "..."
        
    # REMOVE TEMPLATE TOKENS
    text = TEMPLATE_TOKEN_RE.sub("", text)
    
    return text

def _sanitize_export_payload(data, depth=0):
    if depth > EXPORT_MAX_NESTED_DEPTH:
        return "[TRUNCATED: Max Depth Reached]"
        
    if isinstance(data, dict):
        if len(data) > EXPORT_MAX_DICT_KEYS:
            data = dict(list(data.items())[:EXPORT_MAX_DICT_KEYS])
        return {str(k): _sanitize_export_payload(v, depth + 1) for k, v in data.items()}
    
    if isinstance(data, list):
        if len(data) > EXPORT_MAX_LIST_ITEMS:
            data = data[:EXPORT_MAX_LIST_ITEMS]
        return [_sanitize_export_payload(item, depth + 1) for item in data]
        
    return _sanitize_export_scalar(data)

# TEST PAYLOADS
malicious_payloads = [
    "{{ 7*7 }}",
    "{% for i in range(10) %} {{ i }} {% endfor %}",
    "A" * 10005, # Oversized
    {"a": "b", "nested": {"deep": "{{ payload }}"}}
]

print("--- Testing Sanitizer ---")
for p in malicious_payloads:
    sanitized = _sanitize_export_payload(p)
    print(f"Original: {str(p)[:100]}...")
    print(f"Sanitized: {json.dumps(sanitized)}")
    print("-" * 20)

# Test Deep Nesting
deep_nest = {}
curr = deep_nest
for i in range(15):
    curr["next"] = {}
    curr = curr["next"]

sanitized_deep = _sanitize_export_payload(deep_nest)
print(f"Deep Nest Test (Depth 15): {json.dumps(sanitized_deep)}")
