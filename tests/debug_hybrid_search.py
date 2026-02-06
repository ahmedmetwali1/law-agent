"""
🔍 Debug Script for HybridSearchTool
Minimal test to find the root cause of "No Results"
"""
import sys
sys.path.append('e:/law')

import asyncio
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

from agents.tools.hybrid_search_tool import HybridSearchTool
from agents.config.database import db


async def test_direct_sql_search():
    """Test direct SQL query to verify data exists"""
    print("\n" + "=" * 80)
    print("🧪 Test 1: Direct SQL Query")
    print("=" * 80)
    
    # Direct SQL query without any tools
    try:
        result = db.client.table('document_chunks') \
            .select('id, content, source_id') \
            .ilike('content', '%المادة%') \
            .limit(3) \
            .execute()
        
        if result.data:
            print(f"\n✅ Found {len(result.data)} chunks with 'المادة':")
            for i, row in enumerate(result.data, 1):
                print(f"\n{i}. Content: {row['content'][:150]}...")
                print(f"   Source ID: {row['source_id']}")
        else:
            print("\n❌ No data found - DATABASE IS EMPTY!")
    except Exception as e:
        print(f"\n❌ SQL Error: {e}")


async def test_hybrid_search_minimal():
    """Test HybridSearchTool with minimal query"""
    print("\n" + "=" * 80)
    print("🧪 Test 2: HybridSearchTool - Minimal Query")
    print("=" * 80)
    
    tool = HybridSearchTool()
    
    try:
        result = await tool.run(
            query="المادة",
            limit=3
        )
        
        print(f"\nSuccess: {result.success}")
        print(f"Data: {len(result.data) if result.data else 0} results")
        print(f"Error: {result.error if hasattr(result, 'error') else 'None'}")
        
        if result.data:
            print("\n✅ Results:")
            for i, doc in enumerate(result.data, 1):
                print(f"\n{i}. {doc.get('content', '')[:100]}...")
        else:
            print("\n❌ No results returned")
            
            # Check metadata for debugging
            if hasattr(result, 'metadata'):
                print(f"\nMetadata: {result.metadata}")
                
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()


async def test_law_identifier():
    """Test LawIdentifierTool separately"""
    print("\n" + "=" * 80)
    print("🧪 Test 3: LawIdentifierTool")
    print("=" * 80)
    
    from agents.tools.law_identifier_tool import LawIdentifierTool
    
    tool = LawIdentifierTool()
    
    result = tool.run(
        law_query="المعاملات المدنية",
        country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01"
    )
    
    print(f"\nSuccess: {result.success}")
    
    if result.success:
        print(f"Best Match: {result.data['best_match']['official_title']}")
        print(f"Source ID: {result.data['best_match']['source_id']}")
    else:
        print(f"Error: {result.error}")


async def test_law_filter_sql():
    """Test SQL query with source_id filter"""
    print("\n" + "=" * 80)
    print("🧪 Test 4: SQL with Law Filter")
    print("=" * 80)
    
    # First, get source_id from LawIdentifier
    from agents.tools.law_identifier_tool import LawIdentifierTool
    
    law_tool = LawIdentifierTool()
    law_result = law_tool.run(
        law_query="المعاملات المدنية",
        country_id="61a2dd4b-cf18-4d88-b210-4d3687701b01"
    )
    
    if not law_result.success:
        print(f"❌ Law not found: {law_result.error}")
        return
    
    source_id = law_result.data['best_match']['source_id']
    print(f"\n📘 Law: {law_result.data['best_match']['official_title']}")
    print(f"   Source ID: {source_id}")
    
    # Now search with filter
    try:
        result = db.client.table('document_chunks') \
            .select('id, content, source_id, sequence_number') \
            .eq('source_id', source_id) \
            .ilike('content', '%المادة%') \
            .limit(5) \
            .execute()
        
        if result.data:
            print(f"\n✅ Found {len(result.data)} chunks in this law:")
            for i, row in enumerate(result.data, 1):
                print(f"\n{i}. Seq: {row.get('sequence_number')}")
                print(f"   Content: {row['content'][:150]}...")
        else:
            print(f"\n⚠️ No chunks found for this source_id")
            
            # Check if chunks exist at all for this source
            count = db.client.table('document_chunks') \
                .select('id', count='exact') \
                .eq('source_id', source_id) \
                .execute()
            
            print(f"\nTotal chunks for this law: {count.count if hasattr(count, 'count') else 'unknown'}")
            
    except Exception as e:
        print(f"\n❌ SQL Error: {e}")


if __name__ == "__main__":
    print("\n🚀 Starting HybridSearchTool Debugging...")
    
    async def run_all():
        await test_direct_sql_search()
        await test_hybrid_search_minimal()
        await test_law_identifier()
        await test_law_filter_sql()
    
    asyncio.run(run_all())
    
    print("\n" + "=" * 80)
    print("✅ Debug complete!")
    print("=" * 80)
