"""
🧪 Quick Test for HybridSearchToolV3
"""
import sys
sys.path.append('e:/law')

import asyncio
from agents.tools.hybrid_search_tool import HybridSearchTool

async def test_v3():
    print("\n" + "="*80)
    print("🚀 HybridSearchTool V3 - Quick Test")
    print("="*80)
    
    tool = HybridSearchTool()
    
    # Test Quick Scout
    print("\n📊 Testing Quick Scout...")
    try:
        quick_result = await tool.quick_scout(
            query="ما هي الهبة؟",
            country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01",
            limit=5
        )
        
        print(f"✅ Quick Scout:")
        print(f"   Keywords: {quick_result.keywords}")
        print(f"   Results: {len(quick_result.results)}")
        print(f"   Quality: {quick_result.context_quality:.2f}")
        
        # Test Smart Scout
        print("\n📊 Testing Smart Scout...")
        smart_result = await tool.smart_scout(
            query="ما هي الهبة؟",
            quick_result=quick_result,
            country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01",
            limit=15
        )
        
        print(f"✅ Smart Scout:")
        print(f"   Base Keywords: {smart_result.keywords_base[:5]}")
        print(f"   Expanded: {len(smart_result.keywords_expanded)} keywords")
        print(f"   Results: {len(smart_result.results)}")
        print(f"   Citations: {len(smart_result.citations_map)} articles")
        
        # Test Full Run
        print("\n📊 Testing Full Run...")
        result = await tool.run(
            query="ما هي الهبة؟",
            country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01",
            limit=10
        )
        
        if result.success:
            print(f"✅ Full Run Success:")
            print(f"   Results: {len(result.data)}")
            print(f"   Metadata: {result.metadata.keys()}")
        else:
            print(f"❌ Failed: {result.error}")
        
        print("\n" + "="*80)
        print("✅ All Tests Complete!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_v3())
