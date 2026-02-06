"""
🧪 Tests for Law Filtering in HybridSearchTool

Tests the integration of LawIdentifierTool with HybridSearchTool.
"""
import sys
sys.path.append('e:/law')

import asyncio
from agents.tools.hybrid_search_tool import HybridSearchTool


async def test_without_law_filter():
    """Test search WITHOUT law filter (old behavior)"""
    print("\n" + "=" * 80)
    print("🧪 Test 1: Search WITHOUT law filter")
    print("=" * 80)
    
    tool = HybridSearchTool()
    
    # Search for "المادة 368" without specifying law
    result = await tool.run(
        query="المادة 368",
        country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01",  # Saudi Arabia
        limit=3
    )
    
    if result.success and result.data:
        print(f"\n✅ Found {len(result.data)} results:")
        for i, doc in enumerate(result.data, 1):
            content_preview = doc.get('content', '')[:200]
            print(f"\n{i}. {content_preview}...")
            print(f"   Source ID: {doc.get('source_id')}")
    else:
        print(f"\n❌ No results or failed")


async def test_with_law_filter():
    """Test search WITH law filter (new behavior)"""
    print("\n" + "=" * 80)
    print("🧪 Test 2: Search WITH law filter")
    print("=" * 80)
    
    tool = HybridSearchTool()
    
    # Search for "المادة 368" in المعاملات المدنية specifically
    result = await tool.run(
        query="المادة 368",
        country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01",
        law_filter="المعاملات المدنية",  # NEW parameter!
        limit=3
    )
    
    if result.success and result.data:
        print(f"\n✅ Found {len(result.data)} results (filtered to المعاملات المدنية):")
        for i, doc in enumerate(result.data, 1):
            content_preview = doc.get('content', '')[:200]
            print(f"\n{i}. {content_preview}...")
            print(f"   Source ID: {doc.get('source_id')}")
    else:
        print(f"\n❌ Failed: {result.error if not result.success else 'No results'}")


async def test_invalid_law_filter():
    """Test with invalid law name"""
    print("\n" + "=" * 80)
    print("🧪 Test 3: Invalid law filter")
    print("=" * 80)
    
    tool = HybridSearchTool()
    
    result = await tool.run(
        query="المادة 368",
        country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01",
        law_filter="نظام غير موجود xyz123",
        limit=3
    )
    
    if not result.success:
        print(f"\n✅ Correctly failed with error:")
        print(f"   {result.error}")
    else:
        print(f"\n❌ Should have failed but succeeded")


async def test_article_in_different_laws():
    """Test same article number in different laws"""
    print("\n" + "=" * 80)
    print("🧪 Test 4: Same article in different laws")
    print("=" * 80)
    
    tool = HybridSearchTool()
    
    # Test المادة 1 in two different laws
    laws_to_test = [
        "المعاملات المدنية",
        "العمل"
    ]
    
    for law in laws_to_test:
        print(f"\n📘 Testing in: {law}")
        
        result = await tool.run(
            query="المادة 1",
            country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01",
            law_filter=law,
            limit=1
        )
        
        if result.success and result.data:
            content = result.data[0].get('content', '')[:150]
            print(f"   Found: {content}...")
        else:
            print(f"   Not found or error")


if __name__ == "__main__":
    print("\n🚀 Starting Law Filtering Tests...")
    
    # Fix: Use a single event loop for all tests
    async def run_all_tests():
        await test_without_law_filter()
        await test_with_law_filter()
        await test_invalid_law_filter()
        await test_article_in_different_laws()
    
    asyncio.run(run_all_tests())
    
    print("\n" + "=" * 80)
    print("✅ All tests complete!")
    print("=" * 80)

