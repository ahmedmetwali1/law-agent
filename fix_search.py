# إصلاح مباشر لـ hybrid_search_tool.py
import re

# قراءة الملف
with open(r'e:\law\agents\tools\hybrid_search_tool.py', 'r', encoding='utf-8') as f:
    content = f.read()

# البحث والاستبدال
old_line = 'final_query = f"{original_query} {\' \'.join(expanded_keywords)} {\' \'.join(entity_terms)}"'
new_line = 'final_query = f"{\' \'.join(expanded_keywords)} {\' \'.join(entity_terms)}"  # FIX: use legal keywords only'

if old_line in content:
    content = content.replace(old_line, new_line)
    
    # كتابة الملف
    with open(r'e:\law\agents\tools\hybrid_search_tool.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ تم الإصلاح بنجاح!")
    print(f"استبدلت: {old_line[:50]}...")
    print(f"بـ: {new_line[:50]}...")
else:
    print("❌ لم أجد السطر المطلوب")
    print("البحث عن pattern مختلف...")
    
    # محاولة بدون f-string escaping
    import re
    pattern = r'final_query\s*=\s*f".*?original_query.*?"'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print(f"وجدت: {match.group()}")
