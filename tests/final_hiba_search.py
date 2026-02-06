"""
البحث النهائي عن "الهبة" - مع كتابة النتائج في ملف
"""

import requests
import os
import sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_REST_URL = "http://152.67.159.164:8000/rest/v1"
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SOURCE_ID = "ca79a531-1e9b-4bef-b5b8-8d5482184e7e"

# Redirect output to file
output_file = open("tests/final_hiba_results.txt", "w", encoding="utf-8")
sys.stdout = output_file

def get_headers():
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }

print("=" * 70)
print("🎯 البحث النهائي عن 'الهبة' في نظام المعاملات المدنية")
print("=" * 70)

# 1. التحقق
print("\n1️⃣ التحقق من النظام...")
url = f"{SUPABASE_REST_URL}/legal_sources"
params = {"select": "id,title", "id": f"eq.{SOURCE_ID}"}
response = requests.get(url, headers=get_headers(), params=params)

if response.status_code == 200 and response.json():
    source = response.json()[0]
    print(f"   ✅ {source['title']}")
else:
    print(f"   ❌ خطأ: {response.status_code}")
    output_file.close()
    sys.exit(1)

# 2. البحث عن "الهبة"
print("\n2️⃣ البحث عن 'الهبة'...")
url = f"{SUPABASE_REST_URL}/document_chunks"
params = {
    "select": "id,content,sequence_number",
    "source_id": f"eq.{SOURCE_ID}",
    "content": "il ike.%الهبة%",
    "order": "sequence_number.asc",
    "limit": 10
}

response = requests.get(url, headers=get_headers(), params=params)

if response.status_code == 200:
    chunks = response.json()
    print(f"   ✅ وجدت {len(chunks)} نتيجة!")
    
    if chunks:
        print("\n   📄 النتائج:")
        import re
        for i, chunk in enumerate(chunks, 1):
            print(f"\n   {i}. Seq: {chunk['sequence_number']}")
            
            # Extract article numbers
            articles = re.findall(r'المادة\s*(\d+)', chunk['content'])
            if articles:
                print(f"      المواد: {', '.join(articles)}")
            
            # Show content
            content = chunk['content'][:500]
            print(f"      المحتوى:")
            for line in content.split('\n')[:10]:
                if line.strip():
                    print(f"        {line.strip()}")
    else:
        print("   ❌ لا توجد نتائج تحتوي على 'الهبة'")
        
        # Fallback - show any content
        print("\n   🔍 عرض أي محتوى من النظام...")
        params2 = {
            "select": "id,content,sequence_number",
            "source_id": f"eq.{SOURCE_ID}",
            "order": "sequence_number.asc",
            "limit": 2
        }
        response2 = requests.get(url, headers=get_headers(), params=params2)
        
        if response2.status_code == 200:
            any_chunks = response2.json()
            if any_chunks:
                print(f"   ✅ النظام يحتوي على {len(any_chunks)}+ chunks")
                first = any_chunks[0]
                print(f"\n   📄 أول chunk (Seq {first['sequence_number']}):")
                for line in first['content'].split('\n')[:15]:
                    if line.strip():
                        print(f"      {line.strip()}")
else:
    print(f"   ❌ خطأ: {response.status_code}")
    print(f"   {response.text[:500]}")

print("\n" + "=" * 70)
print("✅ تم!")
print("=" * 70)

output_file.close()
print("💾 النتائج في: tests/final_hiba_results.txt", file=sys.stderr)
