import os

file_path = r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_frontend\src\components\Login\UserProfile.vue'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Match the patterns for unused accessToken and legacy headers
    if "const accessToken = sessionStorage.getItem('access_token');" in line:
        continue
    if "if (accessToken) {" in line:
        # We need to skip the next few lines too if it's the block we want to remove
        # But let's be more specific
        continue
    if "headers['Authorization'] = `Bearer ${accessToken}`;" in line:
        continue
    if "headers['Authorization'] = `Bearer ${token}`;" in line:
        continue
    if line.strip() == "}":
        # This is tricky because there are many }
        # Let's just remove the specific lines we know are unused
        pass
    
    new_lines.append(line)

# Let's try a more robust way to remove the blocks
content = "".join(lines)
import re

# Remove accessToken assignments
content = re.sub(r'^\s*const accessToken = sessionStorage\.getItem\(\'access_token\'\);\s*\n', '', content, flags=re.MULTILINE)

# Remove the blocks:
# if (accessToken) {
#   headers['Authorization'] = `Bearer ${accessToken}`;
# }
content = re.sub(r'^\s*if \(accessToken\) \{\s*\n\s*headers\[\'Authorization\'\] = `Bearer \$\{accessToken\}`;\s*\n\s*\}\s*\n', '', content, flags=re.MULTILINE)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacement complete")
