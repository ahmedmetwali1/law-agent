"""
اختبار البحث عن كلمة "الهبة" في قاعدة المعرفة
"""
import sys
sys.path.append('e:/law')

import asyncio
from agents.config.database import db
from agents.tools.hybrid_search_tool import HybridSearchTool
from agents.tools.fetch_tools import FlexibleSearchTool
from agents.tools.vector_tools import VectorSearchTool
from agents.core.llm_factory import get_embeddings
import json

async def test_hiba_search():
    """اختبار شامل للبحث عن 'الهبة'"""
    
    print("=" * 80)
    print("🔍 اختبار البحث عن كلمة 'الهبة' في قاعدة المعرفة")
    print("=" * 80)
    
    # ========== Test 1: SQL Direct Search ==========
    print("\n[Test 1] البحث المباشر في SQL (ILIKE):")
    print("-" * 80)
    
    try:
        # البحث في document_chunks
        result = db.client.table('document_chunks') \
            .select('id, content, country_id, sequence_number') \
            .ilike('content', '%الهبة%') \
            .limit(5) \
            .execute()
        
        print(f"✅ عدد النتائج: {len(result.data)}")
        
        if result.data:
            for i, chunk in enumerate(result.data[:3], 1):
                print(f"\n  [{i}] Chunk ID: {chunk['id']}")
                print(f"      Country: {chunk.get('country_id', 'N/A')}")
                print(f"      Sequence: {chunk.get('sequence_number', 'N/A')}")
                content_preview = chunk['content'][:200].replace('\n', ' ')
                print(f"      Content: {content_preview}...")
        else:
            print("  ⚠️ لا توجد نتائج!")
            
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
    
    # ========== Test 2: Flexible Search Tool ==========
    print("\n\n[Test 2] FlexibleSearchTool (الأداة المرنة):")
    print("-" * 80)
    
    try:
        flex_tool = FlexibleSearchTool()
        result = flex_tool.run(query="الهبة", limit=5)
        
        print(f"✅ Success: {result.success}")
        print(f"✅ عدد النتائج: {len(result.data) if result.data else 0}")
        
        if result.data:
            for i, chunk in enumerate(result.data[:3], 1):
                print(f"\n  [{i}] {chunk.get('id', 'N/A')[:20]}...")
                content_preview = chunk.get('content', '')[:200].replace('\n', ' ')
                print(f"      {content_preview}...")
        else:
            print(f"  ⚠️ Message: {result.message}")
            
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
    
    # ========== Test 3: Vector Search ==========
    print("\n\n[Test 3] Vector Search (البحث الدلالي):")
    print("-" * 80)
    
    try:
        embeddings = get_embeddings()
        query_vector = await embeddings.aembed_query("الهبة")
        
        print(f"✅ Embedding Generated: {len(query_vector)} dimensions")
        
        vector_tool = VectorSearchTool()
        result = vector_tool.run(query_vector=query_vector, match_count=5)
        
        print(f"✅ Success: {result.success}")
        print(f"✅ عدد النتائج: {len(result.data) if result.data else 0}")
        
        if result.data:
            for i, chunk in enumerate(result.data[:3], 1):
                similarity = chunk.get('similarity', 0)
                print(f"\n  [{i}] Similarity: {similarity:.4f}")
                print(f"      ID: {chunk.get('id', 'N/A')[:20]}...")
                content_preview = chunk.get('content', '')[:200].replace('\n', ' ')
                print(f"      {content_preview}...")
        else:
            print(f"  ⚠️ Message: {result.message}")
            
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
    
    # ========== Test 4: Hybrid Search Tool ==========
    print("\n\n[Test 4] HybridSearchTool (المحرك الرئيسي):")
    print("-" * 80)
    
    try:
        hybrid_tool = HybridSearchTool()
        result = await hybrid_tool.run(query="ما هي الهبة", limit=5)
        
        print(f"✅ Success: {result.success}")
        print(f"✅ عدد النتائج: {len(result.data) if result.data else 0}")
        
        if result.metadata:
            print(f"\n  📊 Metadata:")
            print(f"      Scout Keywords: {result.metadata.get('scout_keywords', [])[:5]}")
            entities = result.metadata.get('extracted_entities', {})
            print(f"      Articles Found: {entities.get('articles', [])[:5]}")
        
        if result.data:
            for i, chunk in enumerate(result.data[:3], 1):
                score = chunk.get('final_score', 0)
                print(f"\n  [{i}] Score: {score:.4f}")
                print(f"      ID: {chunk.get('id', 'N/A')[:20]}...")
                content_preview = chunk.get('content', '')[:200].replace('\n', ' ')
                print(f"      {content_preview}...")
        else:
            print(f"  ⚠️ Message: {result.message}")
            
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
    
    # ========== Test 5: RLS Policy Check ==========
    print("\n\n[Test 5] فحص Row Level Security (RLS):")
    print("-" * 80)
    
    try:
        # محاولة الوصول بدون فلتر
        result_no_rls = db.client.table('document_chunks') \
            .select('id', count='exact') \
            .limit(1) \
            .execute()
        
        print(f"✅ إجمالي الشرائح القابلة للوصول: {result_no_rls.count}")
        
        # البحث عن "الهبة" مرة أخرى
        result_hiba = db.client.table('document_chunks') \
            .select('id', count='exact') \
            .ilike('content', '%الهبة%') \
            .execute()
        
        print(f"✅ الشرائح التي تحتوي على 'الهبة': {result_hiba.count}")
        
        if result_hiba.count == 0:
            print("\n  ⚠️ تحذير: RLS قد يمنع الوصول أو البيانات غير موجودة!")
            
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
    
    # ========== Test 6: Normalization Check ==========
    print("\n\n[Test 6] فحص تطبيع النص العربي:")
    print("-" * 80)
    
    variants = ["الهبة", "الهبه", "الهبه", "هبة", "هبه"]
    
    for variant in variants:
        try:
            result = db.client.table('document_chunks') \
                .select('id', count='exact') \
                .ilike('content', f'%{variant}%') \
                .limit(1) \
                .execute()
            
            print(f"  '{variant}': {result.count} results")
            
        except Exception as e:
            print(f"  '{variant}': Error - {e}")
    
    print("\n" + "=" * 80)
    print("✅ الاختبار اكتمل!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_hiba_search())
