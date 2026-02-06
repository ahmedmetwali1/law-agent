"""
🧪 Tests for Law Identifier Tool

Tests fuzzy matching, variants, and caching.
"""
import sys
sys.path.append('e:/law')

import asyncio
from agents.tools.law_identifier_tool import LawIdentifierTool


def test_exact_match():
    """Test exact law name match"""
    print("\n" + "=" * 80)
    print("🧪 Test 1: Exact Match")
    print("=" * 80)
    
    tool = LawIdentifierTool()
    
    # Test exact name
    result = tool.run(
        law_query="نظام المعاملات المدنية",
        country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01"  # Saudi Arabia
    )
    
    if result.success:
        best = result.data["best_match"]
        print(f"\n✅ Success!")
        print(f"   Title: {best['official_title']}")
        print(f"   Confidence: {best['confidence']:.2%}")
        print(f"   Source ID: {best['source_id']}")
    else:
        print(f"\n❌ Failed: {result.error}")


def test_partial_match():
    """Test partial/fuzzy matching"""
    print("\n" + "=" * 80)
    print("🧪 Test 2: Partial Match")
    print("=" * 80)
    
    tool = LawIdentifierTool()
    
    # Test with partial name
    queries = [
        "معاملات مدنية",
        "المعاملات",
        "نظام معاملات",
        "المدني"
    ]
    
    for query in queries:
        result = tool.run(
            law_query=query,
            country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01"
        )
        
        if result.success:
            best = result.data["best_match"]
            print(f"\n📝 Query: '{query}'")
            print(f"   → {best['official_title']}")
            print(f"   Confidence: {best['confidence']:.2%}")
        else:
            print(f"\n❌ Query: '{query}' - {result.error}")


def test_multiple_matches():
    """Test when multiple laws match"""
    print("\n" + "=" * 80)
    print("🧪 Test 3: Multiple Matches")
    print("=" * 80)
    
    tool = LawIdentifierTool()
    
    # Generic query that might match multiple
    result = tool.run(
        law_query="نظام",
        country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01",
        max_results=5
    )
    
    if result.success:
        matches = result.data["all_matches"]
        print(f"\n✅ Found {len(matches)} matches:")
        
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. {match['official_title']}")
            print(f"   Confidence: {match['confidence']:.2%}")
    else:
        print(f"\n❌ Failed: {result.error}")


def test_no_match():
    """Test when no law matches"""
    print("\n" + "=" * 80)
    print("🧪 Test 4: No Match")
    print("=" * 80)
    
    tool = LawIdentifierTool()
    
    result = tool.run(
        law_query="xyz123",
        country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01"
    )
    
    if not result.success:
        print(f"\n✅ Correctly failed: {result.error}")
        if result.data and "suggestions" in result.data:
            print(f"\n📝 Suggestions:")
            for sug in result.data["suggestions"]:
                print(f"   - {sug['title']} ({sug['confidence']:.2%})")
    else:
        print(f"\n❌ Should have failed but succeeded")


def test_caching():
    """Test caching behavior"""
    print("\n" + "=" * 80)
    print("🧪 Test 5: Caching")
    print("=" * 80)
    
    tool = LawIdentifierTool()
    
    query = "المعاملات المدنية"
    country = "61a2dd4b-cf18-4d88-b210-4d3687701b01"
    
    # First call (should query DB)
    result1 = tool.run(law_query=query, country_id=country)
    time1 = result1.data["search_time_ms"] if result1.success else 0
    
    # Second call (should use cache)
    result2 = tool.run(law_query=query, country_id=country)
    time2 = result2.data["search_time_ms"] if result2.success else 0
    
    print(f"\n1st call: {time1}ms")
    print(f"2nd call: {time2}ms (cached)")
    
    if time2 < time1:
        print(f"✅ Cache working! {((time1-time2)/time1*100):.1f}% faster")
    else:
        print(f"⚠️ Cache may not be working")


if __name__ == "__main__":
    print("\n🚀 Starting Law Identifier Tool Tests...")
    
    test_exact_match()
    test_partial_match()
    test_multiple_matches()
    test_no_match()
    test_caching()
    
    print("\n" + "=" * 80)
    print("✅ All tests complete!")
    print("=" * 80)
