"""
🔍 البحث الصحيح عن "الهبة" - مع country context
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Supabase REST API
SUPABASE_REST_URL = "http://152.67.159.164:8000/rest/v1"
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Lawyer ID للمحامي الحالي
LAWYER_ID = "4e22ac65-9024-42f9-9b94-dc4980c51ad6"

def get_headers():
    """Headers للـ REST API"""
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }

def search_hiba_correct():
    """البحث عن 'الهبة' مع country_id الصحيح"""
    
    print("=" * 60)
    print("🔍 البحث عن 'الهبة' (مع country context)")
    print("=" * 60)
    
    # 1. احصل على country_id للمحامي
    print("\n1️⃣ الحصول على country المحامي...")
    try:
        url = f"{SUPABASE_REST_URL}/users"
        params = {
            "select": "id,country_id",
            "id": f"eq.{LAWYER_ID}",
            "limit": 1
        }
        
        response = requests.get(url, headers=get_headers(), params=params)
        
        if response.status_code == 200 and response.json():
            user = response.json()[0]
            country_id = user.get('country_id')
            print(f"   ✅ Country ID: {country_id}")
        else:
            print(f"   ❌ خطأ: {response.status_code}")
            print("   ⚠️ سأستخدم البحث بدون country filter...")
            country_id = None
    
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
        country_id = None
    
    # 2. بحث عن نظام المعاملات المدنية
    print("\n2️⃣ البحث عن نظام المعاملات المدنية...")
    try:
        url = f"{SUPABASE_REST_URL}/legal_sources"
        params = {
            "select": "id,title,country_id",
            "title": "ilike.%المعاملات المدنية%",
            "limit": 5
        }
        
        # أضف country filter إذا كان موجوداً
        if country_id:
            params["country_id"] = f"eq.{country_id}"
        
        response = requests.get(url, headers=get_headers(), params=params)
        
        if response.status_code == 200 and response.json():
            sources = response.json()
            print(f"   ✅ وجدت {len(sources)} نظام:")
            
            for idx, src in enumerate(sources, 1):
                print(f"      {idx}. {src['title']}")
                print(f"         ID: {src['id']}")
                print(f"         Country: {src.get('country_id', 'N/A')}")
            
            # استخدم أول نظام
            source = sources[0]
            source_id = source['id']
            print(f"\n   🎯 اختيار: {source['title']}")
        else:
            print(f"   ❌ لم يتم العثور على النظام")
            return
    
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
        return
    
    # 3. بحث عن chunks تحتوي على "الهبة"
    print("\n3️⃣ البحث عن chunks تحتوي على 'الهبة'...")
    try:
        url = f"{SUPABASE_REST_URL}/document_chunks"
        params = {
            "select": "id,content,sequence_number,ai_summary",
            "source_id": f"eq.{source_id}",
            "or": "(content.ilike.%الهبة%,content.ilike.%الهبه%,ai_summary.ilike.%الهبة%)",
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
                    print(f"\n      {i}. Sequence: {chunk['sequence_number']}")
                    content_preview = chunk['content'][:250].replace('\n', ' ')
                    print(f"         Content: {content_preview}...")
                    
                    if chunk.get('ai_summary'):
                        summary_preview = chunk['ai_summary'][:100]
                        print(f"         Summary: {summary_preview}...")
            else:
                print("   ⚠️ لم يتم العثور على نتائج تحتوي على 'الهبة' في هذا النظام")
        else:
            print(f"   ❌ خطأ: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    # 4. استخراج أرقام المواد
    print("\n4️⃣ البحث عن أرقام المواد...")
    try:
        url = f"{SUPABASE_REST_URL}/document_chunks"
        params = {
            "select": "id,content,sequence_number",
            "source_id": f"eq.{source_id}",
            "content": "ilike.%المادة%الهبة%",
            "order": "sequence_number.asc",
            "limit": 5
        }
        
        response = requests.get(url, headers=get_headers(), params=params)
        
        if response.status_code == 200:
            chunks = response.json()
            if chunks:
                print(f"   ✅ وجدت {len(chunks)} مادة:")
                for chunk in chunks:
                    # استخراج رقم المادة من المحتوى
                    import re
                    matches = re.findall(r'المادة\s*(\d+)', chunk['content'])
                    if matches:
                        print(f"      المادة {matches[0]} (Seq: {chunk['sequence_number']})")
    
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    print("\n" + "=" * 60)
    print("✅ انتهى البحث")
    print("=" * 60)

if __name__ == "__main__":
    search_hiba_correct()
