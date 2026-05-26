import re

file_path = r"c:\Users\Admin\Desktop\KPMG-WS2-Final-Testing\grc_backend\grc\urls.py"
out_file_path = r"c:\Users\Admin\Desktop\KPMG-WS2-Final-Testing\grc_backend\grc\scratch\framework_apis_list.txt"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

path_regex = re.compile(r"path\s*\(\s*['\"]([^'\"]*)['\"]")

matches = []
for i, line in enumerate(lines, 1):
    m = path_regex.search(line)
    if m:
        path_str = m.group(1)
        if "framework" in path_str.lower():
            name_m = re.search(r"name\s*=\s*['\"]([^'\"]*)['\"]", line)
            name_str = name_m.group(1) if name_m else "N/A"
            matches.append((i, path_str, name_str))

with open(out_file_path, "w", encoding="utf-8") as out_f:
    out_f.write(f"Total matching paths: {len(matches)}\n\n")
    for line_num, path_str, name_str in matches:
        out_f.write(f"Line {line_num:4d} | Path: {path_str:<90} | Name: {name_str}\n")

print(f"Successfully wrote {len(matches)} matches to {out_file_path}")
