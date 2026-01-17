# Quick fix script to add get_supabase() before remaining supabase.table calls
import re

file_path = r'e:\law\api\routers\documents.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Lines that need get_supabase() added before them (line numbers from view)
# Line 168, 185, 245, 285, 295, 360

lines = content.split('\n')

# Find and fix each occurrence
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if this line has supabase.table but previous 3 lines don't have get_supabase()
    if 'supabase.table' in line:
        prev_lines = '\n'.join(lines[max(0, i-3):i])
        if 'get_supabase()' not in prev_lines and 'supabase = get_supabase()' not in prev_lines:
            # Add get_supabase() before this line
            indent = len(line) - len(line.lstrip())
            fixed_lines.append(' ' * indent + 'supabase = get_supabase()')
    
    fixed_lines.append(line)
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print("Fixed!")
