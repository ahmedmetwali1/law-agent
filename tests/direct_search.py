"""
🎯 بحث مباشر باستخدام source_id المعروف
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_REST_URL = "http://152.67.159.164:8000/rest/v1"
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Source ID لنظام المعاملات المدنية (من المستخدم)
SOURCE_ID = "ca79a531-1e9b-4bef-b5b8-8d5482184e7e"

def get_headers():
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }

print("=" * 70)
print("🎯 بحث مباشر عن 'الهبة' في نظام المعاملات المدنية")
print("=" * 70)

# 1. تأكد من النظام
print("\n1️⃣ التحقق من النظام...")
url = f"{SUPABASE_REST_URL}/legal_sources"
params = {"select": "id,title", "id": f"eq.{SOURCE_ID}"}
response = requests.get(url, headers=get_headers(), params=params)

if response.status_code == 200 and response.json():
    source = response.json()[0]
    print(f"   ✅ {source['title']}")
    print(f"   ID: {source['id']}")
else:
    print(f"   ❌ خطأ: {response.status_code}")
    exit()

# 2. البحث عن "الهبة"
print("\n2️⃣ البحث عن chunks تحتوي على 'الهبة'...")
url = f"{SUPABASE_REST_URL}/document_chunks"
params = {
    "select": "id,content,sequence_number",
    "source_id": f"eq.{SOURCE_ID}",
    "content": "ilike.%الهبة%",
    "order": "sequence_number.asc",
    "limit": 10
}

response = requests.get(url, headers=get_headers(), params=params)

if response.status_code == 200:
    chunks = response.json()
    print(f"   ✅ وجدت {len(chunks)} نتيجة!")
    
    if chunks:
        print("\n   📄 النتائج:")
        for i, chunk in enumerate(chunks, 1):
            print(f"\n   {i}. Seq: {chunk['sequence_number']}")
            
            # استخراج أرقام المواد
            import re
            articles = re.findall(r'المادة\s*(\d+)', chunk['content'])
            if articles:
                print(f"      المواد: {', '.join(articles)}")
            
            # Content preview
            lines = chunk['content'].split('\n')[:3]
            for line in lines:
                if line.strip():
                    print(f"      {line.strip()[:80]}")
    else:
        print("   ❌ لا توجد نتائج")
        
        # محاولة بديلة - بحث عن أي محتوى
        print("\n   🔍 محاولة: عرض أي محتوى من هذا النظام...")
        params2 = {
            "select": "id,content,sequence_number",
            "source_id": f"eq.{SOURCE_ID}",
            "order": "sequence_number.asc",
            "limit": 3
        }
        response2 = requests.get(url, headers=get_headers(), params=params2)
        
        if response2.status_code == 200:
            any_chunks = response2.json()
            if any_chunks:
                print(f"   ✅ إجمالي chunks في النظام: موجودة")
                print(f"   📄 أول chunk:")
                first = any_chunks[0]
                preview = first['content'][:300].replace('\n', ' ')
                print(f"      {preview}...")
else:
    print(f"   ❌ خطأ: {response.status_code}")
    print(f"   Response: {response.text[:500]}")

print("\n" + "=" * 70)
