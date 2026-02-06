"""
🧪 اختبار HybridSearchTool المُصلح
"""
import sys
sys.path.append('e:/law')

import asyncio
from agents.tools.hybrid_search_tool import HybridSearchTool


async def test_hybrid_search():
    """اختبار البحث عن 'الهبة'"""
    
    tool = HybridSearchTool()
    
    print("=" * 100)
    print("🧪 اختبار HybridSearchTool المُصلح")
    print("=" * 100)
    
    # Test 1: Arabic variants generation
    print("\n[Test 1] Arabic Variants Generation:")
    variants = tool._generate_arabic_variants("الهبة")
    print(f"  Input: 'الهبة'")
    print(f"  Variants: {variants}")
    
    # Test 2: Query building (without dilution)
    print("\n[Test 2] Query Building (No Dilution):")
    query = tool._build_sniper_query(
        query_type="DEFINITION",
        expanded_keywords=["الهبة", "تعريف", "معنى", "شروط"],
        query_entities={}
    )
    print(f"  Result: '{query}'")
    print(f"  ✅ Should NOT contain too many generic terms!")
    
    #Test 3: Full search
    print("\n[Test 3] Full Search:")
    result = await tool.run(
        query="الهبة",
        limit=5
    )
    
    if result.success:
        print(f"\n✅ Success! Found {len(result.data)} results")
        for i, doc in enumerate(result.data, 1):
            print(f"\n  [{i}] Score: {doc.get('relevance_score', 0):.3f}")
            print(f"      {doc.get('content', '')[:150]}...")
    else:
        print(f"\n❌ Failed: {result.error}")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    asyncio.run(test_hybrid_search())
