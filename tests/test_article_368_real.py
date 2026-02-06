"""
🧪 Test for Article 368 Specifically
"""
import sys
sys.path.append('e:/law')

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

from agents.tools.hybrid_search_tool import HybridSearchTool


async def test_article_368_no_filter():
    """Test: المادة 368 without law filter"""
    print("\n" + "=" * 80)
    print("🧪 Test: المادة 368 (NO law filter)")
    print("=" * 80)
    
    tool = HybridSearchTool()
    
    result = await tool.run(
        query="المادة 368",
        country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01",
        limit=3
    )
    
    if result.success and result.data:
        print(f"\n✅ Found {len(result.data)} results:")
        for i, doc in enumerate(result.data, 1):
            print(f"\n{i}. {doc.get('content', '')[:200]}...")
            print(f"   Source: {doc.get('source_id')}")
    else:
        print(f"\n❌ No results")


async def test_article_368_with_filter():
    """Test: المادة 368 من نظام المعاملات المدنية"""
    print("\n" + "=" * 80)
    print("🧪 Test: المادة 368 من نظام المعاملات المدنية (WITH law filter)")
    print("=" * 80)
    
    tool = HybridSearchTool()
    
    result = await tool.run(
        query="المادة 368",
        country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01",
        law_filter="المعاملات المدنية",
        limit=3
    )
    
    if result.success and result.data:
        print(f"\n✅ Found {len(result.data)} results (filtered to المعاملات المدنية):")
        for i, doc in enumerate(result.data, 1):
            content = doc.get('content', '')
            # Check if it contains "368" or "الثامنة والستون بعد الثلاثمائة"
            has_368 = "368" in content or "الثامنة والستون بعد الثلاثمائة" in content
            
            print(f"\n{i}. Contains '368': {has_368}")
            print(f"   Preview: {content[:250]}...")
            print(f"   Source: {doc.get('source_id')}")
    elif not result.success:
        print(f"\n❌ Failed: {result.error}")
    else:
        print(f"\n⚠️ No results (but no error)")


if __name__ == "__main__":
    print("\n🚀 Testing Article 368 Specifically...")
    
    async def run_all():
        await test_article_368_no_filter()
        await test_article_368_with_filter()
    
    asyncio.run(run_all())
    
    print("\n" + "=" * 80)
    print("✅ Tests complete!")
    print("=" * 80)
