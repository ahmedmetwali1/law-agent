
import sys
sys.path.append("e:/law")
import asyncio
from agents.tools.hybrid_search_tool import HybridSearchTool
from tests.golden_dataset import GOLDEN_DATASET
import time

async def run_tuning_benchmark():
    tool = HybridSearchTool()
    print(f"\n🚀 STARTING LEGISLATIVE SEARCH BENCHMARK")
    print(f"=====================================")
    print(f"📚 Dataset Size: {len(GOLDEN_DATASET)} queries")
    print(f"=====================================\n")

    scores = []
    
    for case in GOLDEN_DATASET:
        query = case['query']
        category = case['category']
        expected_kw = case['expected_keywords']
        expected_ref = str(case['expected_article_ref']) # Ensure string
        
        print(f"🔍 Testing: '{query}' ({category})")
        
        start_time = time.time()
        
        # Run search
        # Note: We are testing the tool's ability to find relevant content
        result = await tool.run(query, limit=15)
        duration = time.time() - start_time
        
        # Analyze Result  
        found = False
        top_rank = -1
        # HybridSearchTool returns metadata with different structure
        found_keywords = result.metadata.get('scout_keywords', [])
        quality_score = 1.0 if result.data else 0.0  # Simple quality check

        
        # Check if expected keywords match results content
        match_count = 0
        article_found = False
        
        for idx, item in enumerate(result.data[:5]):  # Check top 5 results
            content = item.get('content', '').lower()
            
            # 1. Article Check (OPTIONAL - bonus if found)
            if expected_ref and expected_ref != "None":
                if f" {expected_ref} " in content or f"مادة {expected_ref}" in content or f"المادة {expected_ref}" in content:
                    article_found = True
            
            # 2. Keyword Check (PRIMARY SUCCESS CRITERION)
            # Check how many expected keywords appear in this chunk
            current_matches = sum(1 for kw in expected_kw if kw in content)
            
            # If at least 2 of the expected keywords are in this chunk, count it as relevant
            if current_matches >= 2:
                match_count += 1
                if top_rank == -1: 
                    top_rank = idx + 1
        
        # ✅ NEW SUCCESS CRITERIA:
        # PASS if we found at least 1-2 relevant chunks in top 5 
        # (chunks containing 2+ expected keywords)
        if expected_ref != "None":
            # If article ref exists, prefer it but also accept keyword matches
            found = article_found or (match_count >= 2)
        else:
            # No article ref? Just need keyword matches
            found = (match_count >= 1)

            
        status = "✅ PASS" if found else "❌ FAIL"
        scores.append({
            "query": query,
            "status": status,
            "rank": top_rank,
            "quality": quality_score,
            "keywords": found_keywords[:5] # Show first 5 generated keywords
        })
        
        print(f"   👉 {status} | Rank: {top_rank} | Keywords: {found_keywords[:3]}...")

    # Summary
    print("\n📊 FINAL REPORT")
    print("=====================================")
    pass_count = sum(1 for s in scores if s['status'] == "✅ PASS")
    total = len(scores)
    
    print(f"Success Rate: {pass_count}/{total} ({pass_count/total*100:.1f}%)")
    
    if pass_count < total:
        print("\n❌ FAILED QUERIES:")
        for s in scores:
            if s['status'] == "❌ FAIL":
                print(f"- {s['query']} (Gen Keywords: {s['keywords']})")

if __name__ == "__main__":
    asyncio.run(run_tuning_benchmark())
