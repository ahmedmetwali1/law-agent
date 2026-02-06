"""
Test Country Validation and Protection Layer
Tests that the system rejects non-Arabic countries and handles no-results gracefully
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tools.hybrid_search_tool import HybridSearchTool

print("=" * 60)
print("🛡️  Country Validation & Protection Test")
print("=" * 60)
print()

# Initialize tool
hybrid = HybridSearchTool()

async def run_tests():
    # ========================================
    # Test 1: Valid Egyptian Country ✅
    # ========================================
    print("📋 Test 1: Valid Egyptian Country")
    print("-" * 60)
    
    egypt_id = "3216b40a-9c9b-4c0a-adde-9b680f6b9481"
    result = await hybrid.run(
        query="الهبة",
        country_id=egypt_id,
        limit=3
    )
    
    if result.success:
        print(f"✅ {result.message}")
        print(f"   Found: {result.metadata.get('total_found', 0)} results")
    else:
        print(f"❌ Error: {result.error}")
    
    print()
    
    # ========================================
    # Test 2: Non-Existent Country (e.g., Germany) ❌
    # ========================================
    print("📋 Test 2: Non-Existent Country (Germany)")
    print("-" * 60)
    
    fake_country_id = "00000000-0000-0000-0000-000000000000"
    result = await hybrid.run(
        query="قوانين ألمانيا",
        country_id=fake_country_id,
        limit=3
    )
    
    if result.success:
        print(f"⚠️  Unexpected success: {result.message}")
    else:
        print(f"✅ Correctly rejected: {result.error}")
        print(f"   Message: {result.message}")
    
    print()
    
    # ========================================
    # Test 3: Valid Country but No Results
    # ========================================
    print("📋 Test 3: Valid Country but No Results")
    print("-" * 60)
    
    saudi_id = "61a2dd4b-cf18-4d88-b210-4d3687701b01"
    result = await hybrid.run(
        query="الهبة في المريخ",  # Nonsensical but should search
        country_id=saudi_id,
        limit=3
    )
    
    if result.success:
        if result.data:
            print(f"⚠️  Found results: {result.message}")
        else:
            print(f"✅ No results (as expected): {result.message}")
    else:
        print(f"❌ Error: {result.error}")
    
    print()
    
    # ========================================
    # Test 4: No Country ID (Should use default or work)
    # ========================================
    print("📋 Test 4: No Country ID Specified")
    print("-" * 60)
    
    result = await hybrid.run(
        query="المادة 368",
        limit=3
    )
    
    if result.success:
        print(f"✅ {result.message}")
        print(f"   Found: {result.metadata.get('total_found', 0)} results")
        print(f"   Country: {result.metadata.get('country_id', 'Not specified')}")
    else:
        print(f"❌ Error: {result.error}")
    
    print()

# Run tests
asyncio.run(run_tests())

print("=" * 60)
print("✅ Validation Tests Complete!")
print("=" * 60)
