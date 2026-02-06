"""
🔍 Test: البحث عن المادة 368 من نظام المعاملات المدنية

اختبار للتحقق من وجود المادة في قاعدة المعرفة.
"""
import sys
sys.path.append('e:/law')

import asyncio
from agents.tools.hybrid_search_tool import HybridSearchTool


def search_article_368():
    """البحث عن المادة الثامنة والستون بعد الثلاثمائة"""
    
    print("=" * 80)
    print("🔍 البحث عن: المادة الثامنة والستون بعد الثلاثمائة")
    print("   (المادة 368 من نظام المعاملات المدنية)")
    print("=" * 80)
    
    # Initialize search tool
    search_tool = HybridSearchTool()
    
    # Search queries to try
    queries = [
        "المادة 368 نظام المعاملات المدنية",
        "المادة الثامنة والستون بعد الثلاثمائة",
        "المادة ٣٦٨",
        "368"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"🔎 محاولة {i}: {query}")
        print(f"{'='*80}")
        
        try:
            # Execute search (using _run which is sync)
            result = search_tool._run(
                query=query,
                country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01"  # Saudi Arabia
            )
            
            # Parse results
            if result and result.get("results"):
                results = result["results"]
                print(f"\n✅ وُجدت {len(results)} نتيجة:")
                
                for j, res in enumerate(results[:3], 1):  # Show top 3
                    print(f"\n📄 النتيجة {j}:")
                    print(f"   المصدر: {res.get('hierarchy_path', 'غير محدد')}")
                    print(f"   النص: {res.get('content', '')[:300]}...")
                    print(f"   التشابه: {res.get('similarity_score', 0):.2f}")
                    
                    # Check if this is article 368
                    content = res.get('content', '').lower()
                    if '368' in content or 'ثامنة وستون' in content:
                        print(f"   ✨ هذه هي المادة 368!")
                
                # If found, stop searching
                if len(results) > 0:
                    print(f"\n{'='*80}")
                    print(f"✅ نجح البحث بـ Query: {query}")
                    print(f"{'='*80}")
                    break
            else:
                print(f"\n❌ لم يُعثر على نتائج")
                
        except Exception as e:
            print(f"\n❌ خطأ في البحث: {e}")
    
    print(f"\n{'='*80}")
    print("✅ اختبار البحث مكتمل")
    print(f"{'='*80}")


def search_with_details():
    """بحث مفصل مع عرض كامل النتائج"""
    
    print("\n" + "=" * 80)
    print("🔬 البحث المفصل")
    print("=" * 80)
    
    search_tool = HybridSearchTool()
    
    query = "المادة الثامنة والستون بعد الثلاثمائة نظام المعاملات المدنية"
    
    print(f"\nالاستعلام: {query}")
    
    try:
        result = search_tool._run(
            query=query,
            country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01"
        )
        
        if result and result.get("results"):
            results = result["results"]
            
            print(f"\n📊 إحصائيات:")
            print(f"   عدد النتائج: {len(results)}")
            print(f"   طريقة البحث: {result.get('search_method', 'N/A')}")
            print(f"   الوقت: {result.get('search_time_ms', 0)}ms")
            
            print(f"\n📄 النتائج الكاملة:")
            
            for i, res in enumerate(results, 1):
                print(f"\n{'─'*80}")
                print(f"النتيجة #{i}:")
                print(f"{'─'*80}")
                print(f"المسار: {res.get('hierarchy_path', 'N/A')}")
                print(f"المصدر: {res.get('source_id', 'N/A')}")
                print(f"التشابه: {res.get('similarity_score', 0):.3f}")
                print(f"\nالنص الكامل:")
                print(res.get('content', 'لا يوجد نص'))
                
                # Highlight if article 368
                if '368' in str(res.get('content', '')):
                    print(f"\n✨✨✨ المادة 368 موجودة هنا! ✨✨✨")
        else:
            print(f"\n❌ لم يُعثر على أي نتائج")
            print(f"   قد تكون المادة غير موجودة في قاعدة البيانات")
            
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 بدء الاختبار...")
    
    # Run basic search (sync - no asyncio needed)
    search_article_368()
    
    # Run detailed search (optional - uncomment to run)
    # search_with_details()
    
    print("\n✅ اكتمل الاختبار!")
