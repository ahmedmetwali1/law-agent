"""
🧪 اختبار بدون Limit - جلب كل النتائج
"""
import sys
sys.path.append('e:/law')

import asyncio
from agents.tools.hybrid_search_tool import HybridSearchTool


async def test_all_results():
    """اختبار مع limit كبير"""
    
    tool = HybridSearchTool()
    
    print("=" * 100)
    print("🔍 اختبار: جلب كل النتائج عن 'الهبة'")
    print("=" * 100)
    
    # Test with large limit
    result = await tool.run(
        query="الهبة",
        limit=20  # زيادة الحد الأقصى
    )
    
    if result.success:
        print(f"\n✅ وجدنا {len(result.data)} نتيجة\n")
        
        # تجميع حسب المصدر
        from collections import defaultdict
        by_source = defaultdict(list)
        
        for doc in result.data:
            # نحتاج جلب معلومات المصدر
            source_id = doc.get('source_id')
            by_source[source_id].append(doc)
        
        # عرض النتائج
        for i, doc in enumerate(result.data, 1):
            score = doc.get('relevance_score', 0)
            content = doc.get('content', '')[:150]
            print(f"[{i}] Score: {score:.1f}")
            print(f"    {content}...")
            print()
        
        # إحصائيات
        print("\n" + "=" * 100)
        print(f"📊 الإحصائيات:")
        print(f"   • إجمالي النتائج: {len(result.data)}")
        print(f"   • عدد المصادر: {len(by_source)}")
        
    else:
        print(f"❌ خطأ: {result.error}")


if __name__ == "__main__":
    asyncio.run(test_all_results())
