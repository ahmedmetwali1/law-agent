"""
🔍 Python Script للبحث عن "الهبة" في Supabase
يستخدم REST API مباشرة
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Supabase REST API
SUPABASE_REST_URL = "http://152.67.159.164:8000/rest/v1"
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Country ID للسعودية
SAUDI_COUNTRY_ID = "61a2dd4b-cf18-4d88-b210-4d3687701b01"

def get_headers():
    """Headers للـ REST API"""
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }

def search_hiba():
    """البحث عن 'الهبة' في قاعدة البيانات"""
    
    print("=" * 60)
    print("🔍 البحث عن 'الهبة' في Supabase")
    print("=" * 60)
    
    # 1. بحث أساسي في document_chunks (بدون country filter)
    print("\n1️⃣ البحث في محتوى المستندات...")
    try:
        url = f"{SUPABASE_REST_URL}/document_chunks"
        params = {
            "select": "id,content,sequence_number,source_id",
            "or": "(content.ilike.%الهبة%,content.ilike.%الهبه%)",
            "limit": 10
        }
        
        response = requests.get(url, headers=get_headers(), params=params)
        
        if response.status_code == 200:
            results = response.json()
            print(f"   ✅ وجدت {len(results)} نتيجة")
            
            if results:
                print("\n   📄 أول 3 نتائج:")
                for i, result in enumerate(results[:3], 1):
                    content_preview = result['content'][:150].replace('\n', ' ') + "..."
                    print(f"      {i}. {content_preview}")
                    print(f"         Source ID: {result.get('source_id', 'N/A')}")
            else:
                print("   ❌ لم يتم العثور على نتائج")
        else:
            print(f"   ❌ خطأ {response.status_code}: {response.text[:200]}")
    
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    # 2. إحصائيات
    print("\n2️⃣ الإحصائيات...")
    try:
        url = f"{SUPABASE_REST_URL}/document_chunks"
        params = {
            "select": "id",
            "country_id": f"eq.{SAUDI_COUNTRY_ID}",
            "or": "(content.ilike.%الهبة%,content.ilike.%الهبه%)"
        }
        
        headers = get_headers()
        headers["Prefer"] = "count=exact"
        
        response = requests.head(url, headers=headers, params=params)
        
        if response.status_code == 200:
            total = response.headers.get('Content-Range', '0').split('/')[-1]
            print(f"   📊 إجمالي النتائج: {total}")
        else:
            # Fallback: GET and count
            response = requests.get(url, headers=get_headers(), params=params)
            if response.status_code == 200:
                total = len(response.json())
                print(f"   📊 إجمالي النتائج (تقريبي): {total}+")
    
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    # 3. البحث في نظام المعاملات المدنية
    print("\n3️⃣ البحث في نظام المعاملات المدنية...")
    try:
        # الخطوة 1: ابحث عن النظام (بدون country filter)
        url = f"{SUPABASE_REST_URL}/legal_sources"
        params = {
            "select": "id,title",
            "title": "ilike.%المعاملات%",
            "limit": 5
        }
        
        response = requests.get(url, headers=get_headers(), params=params)
        
        if response.status_code == 200 and response.json():
            sources = response.json()
            print(f"   ✅ وجدت {len(sources)} أنظمة تحتوي على 'المعاملات':")
            
            for idx, src in enumerate(sources, 1):
                print(f"      {idx}. {src['title']}")
            
            # استخدم أول نظام
            source = sources[0]
            print(f"\n   🎯 اختيار: {source['title']}")
            
            # الخطوة 2: ابحث عن chunks
            url = f"{SUPABASE_REST_URL}/document_chunks"
            params = {
                "select": "id,content,sequence_number",
                "source_id": f"eq.{source['id']}",
                "or": "(content.ilike.%الهبة%,content.ilike.%الهبه%)",
                "order": "sequence_number.asc",
                "limit": 5
            }
            
            response = requests.get(url, headers=get_headers(), params=params)
            
            if response.status_code == 200:
                chunks = response.json()
                print(f"   📄 وجدت {len(chunks)} نتيجة عن الهبة في هذا النظام")
                
                if chunks:
                    print("\n   🎯 أول نتيجة:")
                    first = chunks[0]
                    print(f"      Seq: {first['sequence_number']}")
                    content_preview = first['content'][:200].replace('\n', ' ')
                    print(f"      Content: {content_preview}...")
            else:
                print(f"   ❌ خطأ في البحث: {response.status_code}")
        else:
            print("   ❌ لم يتم العثور على أنظمة تحتوي على 'المعاملات'")
    
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    print("\n" + "=" * 60)
    print("✅ انتهى البحث")
    print("=" * 60)

if __name__ == "__main__":
    # حفظ النتائج في ملف أيضاً
    import sys
    from io import StringIO
    
    # Capture output
    output_buffer = StringIO()
    original_stdout = sys.stdout
    
    class TeeOutput:
        def __init__(self, *files):
            self.files = files
        def write(self, data):
            for f in self.files:
                f.write(data)
        def flush(self):
            for f in self.files:
                f.flush()
    
    # Tee to both stdout and buffer
    sys.stdout = TeeOutput(original_stdout, output_buffer)
    
    search_hiba()
    
    # Save to file
    sys.stdout = original_stdout
    with open("tests/hiba_search_results.txt", "w", encoding="utf-8") as f:
        f.write(output_buffer.getvalue())
    
    print("\n💾 النتائج محفوظة في: tests/hiba_search_results.txt")
