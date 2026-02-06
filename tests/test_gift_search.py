"""
اختبار البحث عن الهبة في نظام المعاملات المدنية
=====================================================
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.tools.hybrid_search_tool import HybridSearchTool
from agents.tools.vector_tools import VectorSearchTool
from agents.tools.fetch_tools import FlexibleSearchTool
from config.database import db


async def test_1_direct_keyword_search():
    """
    Test 1: البحث المباشر بالكلمة المفتاحية 'الهبة'
    """
    print("\n" + "="*60)
    print("Test 1: Direct Keyword Search for 'الهبة'")
    print("="*60)
    
    try:
        result = db.client.from_("document_chunks")\
            .select("id, ai_summary, source_id, content")\
            .ilike("content", "%هبة%")\
            .limit(10)\
            .execute()
        
        print(f"✅ وجد {len(result.data)} نتيجة تحتوي على 'الهبة'")
        
        for i, item in enumerate(result.data[:3], 1):
            print(f"\n{i}. Summary: {item.get('ai_summary', 'No summary')[:100]}...")
            print(f"   Content preview: {item.get('content', '')[:150]}...")
        
        return len(result.data) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_2_check_civil_transactions_system():
    """
    Test 2: التحقق من وجود نظام المعاملات المدنية
    """
    print("\n" + "="*60)
    print("Test 2: Check for نظام المعاملات المدنية")
    print("="*60)
    
    try:
        # البحث عن النظام
        result = db.client.from_("legal_sources")\
            .select("id, title, country_id")\
            .or_("title.ilike.%معاملات%,title.ilike.%مدنية%")\
            .execute()
        
        if result.data:
            print(f"✅ وجد {len(result.data)} مستند متعلق بالمعاملات المدنية:")
            
            for doc in result.data:
                print(f"\n📄 {doc['title']}")
                
                # البحث عن chunks تحتوي "هبة"
                chunks = db.client.from_("document_chunks")\
                    .select("id, ai_summary")\
                    .eq("source_id", doc['id'])\
                    .ilike("content", "%هبة%")\
                    .limit(5)\
                    .execute()
                
                if chunks.data:
                    print(f"   ✅ يحتوي على {len(chunks.data)} chunks عن الهبة")
                    for chunk in chunks.data[:2]:
                        print(f"      - {chunk.get('ai_summary', 'No summary')[:80]}...")
                else:
                    print(f"   ❌ لا يحتوي على chunks عن الهبة")
            
            return True
        else:
            print("❌ نظام المعاملات المدنية غير موجود في قاعدة البيانات!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_3_vector_search():
    """
    Test 3: Vector Search للهبة
    """
    print("\n" + "="*60)
    print("Test 3: Vector Search for 'الهبة'")
    print("="*60)
    
    try:
        vector_tool = VectorSearchTool()
        
        result = await vector_tool.run(
            query="الهبة في نظام المعاملات المدنية",
            limit=10,
            threshold=0.3  # خفّضنا threshold
        )
        
        if result.success and result.data:
            print(f"✅ Vector Search وجد {len(result.data)} نتيجة")
            for i, item in enumerate(result.data[:3], 1):
                score = item.get('similarity', 0)
                summary = item.get('ai_summary', 'No summary')
                print(f"\n{i}. Score: {score:.3f}")
                print(f"   {summary[:100]}...")
            return True
        else:
            print(f"❌ Vector Search فشل: {result.error if hasattr(result, 'error') else 'No results'}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_4_hybrid_search():
    """
    Test 4: Hybrid Search (كما يستخدمه النظام)
    """
    print("\n" + "="*60)
    print("Test 4: Hybrid Search (Full Pipeline)")
    print("="*60)
    
    try:
        hybrid_tool = HybridSearchTool()
        
        result = await hybrid_tool.run(
            query="الهبة نظام المعاملات المدنية",
            limit=10,
            country_id="sa"
        )
        
        if result.success and result.data:
            print(f"✅ Hybrid Search وجد {len(result.data)} نتيجة")
            
            for i, item in enumerate(result.data[:3], 1):
                score = item.get('relevance_score', 0)
                summary = item.get('ai_summary', 'No summary')
                print(f"\n{i}. Relevance: {score:.3f}")
                print(f"   {summary[:100]}...")
            
            return True
        else:
            print(f"❌ Hybrid Search فشل")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_5_flexible_search():
    """
    Test 5: Flexible Search (Keyword Fallback)
    """
    print("\n" + "="*60)
    print("Test 5: Flexible Search (Keyword)")
    print("="*60)
    
    try:
        flex_tool = FlexibleSearchTool()
        
        result = await flex_tool.run(
            query="الهبة",
            tables=["document_chunks"],
            mode="any",
            limit=10
        )
        
        if result.success and result.data:
            print(f"✅ Flexible Search وجد {len(result.data)} نتيجة")
            for i, item in enumerate(result.data[:3], 1):
                summary = item.get('ai_summary', 'No summary')
                print(f"\n{i}. {summary[:100]}...")
            return True
        else:
            print(f"❌ Flexible Search فشل")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def run_all_tests():
    """
    شغّل جميع الاختبارات
    """
    print("\n" + "🧪 " + "="*58)
    print("   اختبار البحث عن 'الهبة في نظام المعاملات المدنية'")
    print("="*60 + "\n")
    
    results = {}
    
    # Test 1
    results['keyword'] = await test_1_direct_keyword_search()
    await asyncio.sleep(1)
    
    # Test 2
    results['system_exists'] = await test_2_check_civil_transactions_system()
    await asyncio.sleep(1)
    
    # Test 3
    results['vector'] = await test_3_vector_search()
    await asyncio.sleep(1)
    
    # Test 4
    results['hybrid'] = await test_4_hybrid_search()
    await asyncio.sleep(1)
    
    # Test 5
    results['flexible'] = await test_5_flexible_search()
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n{'='*60}")
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
