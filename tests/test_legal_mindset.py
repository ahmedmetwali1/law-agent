"""
🧪 Test Agent Behavior Improvements
Test: "ما هي الهبة؟" - should use legal terms, not academic
"""
import sys
sys.path.append('e:/law')

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

from agents.tools.hybrid_search_tool import HybridSearchTool


async def test_gift_query():
    """
    Test: ما هي الهبة؟
    
    Expected behavior:
    - NO academic keywords like "تعريف", "معنى"
    - YES legal terms like "هبة", "واهب", "موهوب له"
    """
    print("\n" + "=" * 80)
    print("🧪 Test: Agent Behavior - Legal Mindset")
    print("Query: 'ما هي الهبة؟'")
    print("=" * 80)
    
    tool = HybridSearchTool()
    
    result = await tool.run(
        query="ما هي الهبة؟",
        country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01",
        limit=5
    )
    
    if result.success and result.data:
        print(f"\n✅ Found {len(result.data)} results:")
        
        for i, doc in enumerate(result.data, 1):
            content = doc.get('content', '')
            print(f"\n{i}. {content[:300]}...")
            print(f"   Source: {doc.get('source_id')}")
    elif not result.success:
        print(f"\n❌ Failed: {result.error}")
    else:
        print(f"\n⚠️ No results")
    
    # Check logs for keywords used
    print("\n" + "=" * 80)
    print("📊 Review the logs above to verify:")
    print("   ✓ Keywords include: هبة, واهب, موهوب له")
    print("   ✗ Keywords should NOT include: تعريف, معنى, شرح")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🚀 Testing Legal Practitioner Mindset...")
    asyncio.run(test_gift_query())
    print("\n✅ Test complete!")
