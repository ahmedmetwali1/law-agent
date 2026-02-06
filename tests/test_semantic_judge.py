"""
🧪 Test: Semantic Judge Classification

Tests the semantic classifier with various query types.
"""
import sys
sys.path.append('e:/law')

import asyncio
from agents.core.semantic_classifier import (
    determine_complexity_hybrid,
    _is_obviously_simple,
    _is_obviously_complex
)
from agents.core.llm_factory import get_llm


# Test queries
TEST_QUERIES = [
    # Obviously SIMPLE
    ("ما هي شروط الهبة؟", "simple"),
    ("كيف يتم إثبات الهبة؟", "simple"),
    ("المادة 375 عن إيه؟", "simple"),
    ("ما تعريف العقد؟", "simple"),
    
    # Obviously COMPLEX
    ("أحتاج استراتيجية كاملة للتعامل مع قضيتي", "complex"),
    ("ساعدني في بناء خطة قانونية للدفاع", "complex"),
    ("كيف أحمي نفسي قانونياً في هذا الموقف المعقد: ...", "complex"),
    
    # UNCERTAIN (needs LLM)
    ("ما الفرق بين الهبة والوصية؟", "medium"),
    ("ماذا عن إثبات الهبة للعقار أو المنقول؟", "simple"),  # User's actual query!
    ("هل يمكن الرجوع في الهبة بعد وفاة الواهب؟", "simple")
]


def test_heuristics():
    """Test fast heuristics"""
    print("=" * 80)
    print("🧪 Testing Fast Heuristics")
    print("=" * 80)
    
    for query, expected in TEST_QUERIES:
        is_simple = _is_obviously_simple(query)
        is_complex = _is_obviously_complex(query)
        
        result = "unknown"
        if is_simple:
            result = "simple"
        elif is_complex:
            result = "complex"
        
        status = "✅" if result == expected or result == "unknown" else "❌"
        
        print(f"\n{status} Query: {query[:60]}...")
        print(f"   Expected: {expected} | Heuristic: {result}")


async def test_semantic_classification():
    """Test full semantic classification"""
    print("\n" + "=" * 80)
    print("🧪 Testing Semantic Classification")
    print("=" * 80)
    
    llm = get_llm(temperature=0.1, json_mode=True)
    
    # Test the user's actual query
    user_query = "ماذا عن إثبات الهبة للعقار أو المنقول؟"
    
    print(f"\n🎯 Testing User's Query: {user_query}")
    
    complexity = await determine_complexity_hybrid(
        query=user_query,
        context={},
        llm=llm
    )
    
    print(f"   Result: {complexity.upper()}")
    print(f"   Expected: SIMPLE (إجرائي مباشر)")
    
    if complexity == "simple":
        print("   ✅ CORRECT - روح research مباشرة!")
    else:
        print(f"   ❌ WRONG - راح يروح {complexity} (هدر وقت!)")


async def test_all_queries():
    """Test all queries"""
    print("\n" + "=" * 80)
    print("🧪 Testing All Queries with Semantic Classifier")
    print("=" * 80)
    
    llm = get_llm(temperature=0.1, json_mode=True)
    
    results = {
        "correct": 0,
        "wrong": 0,
        "total": len(TEST_QUERIES)
    }
    
    for query, expected in TEST_QUERIES:
        complexity = await determine_complexity_hybrid(
            query=query,
            context={},
            llm=llm
        )
        
        is_correct = complexity == expected
        if is_correct:
            results["correct"] += 1
        else:
            results["wrong"] += 1
        
        status = "✅" if is_correct else "❌"
        
        print(f"\n{status} Query: {query[:50]}...")
        print(f"   Expected: {expected} | Got: {complexity}")
    
    print("\n" + "=" * 80)
    print("📊 Results:")
    print(f"   Correct: {results['correct']}/{results['total']} ({results['correct']/results['total']*100:.1f}%)")
    print("=" * 80)


if __name__ == "__main__":
    # Run tests
    test_heuristics()
    
    asyncio.run(test_semantic_classification())
    
    # Full test (optional - costs API calls)
    # asyncio.run(test_all_queries())
    
    print("\n✅ Tests complete!")
