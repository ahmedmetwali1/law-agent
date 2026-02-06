import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.getcwd()))

from agents.knowledge.deep_search_strategy import deep_search

def test_country_extraction():
    print("Testing Country Extraction Logic...")
    queries = [
        ("ما هي حقوق الزوجة في القانون المصري؟", "مصر"),
        ("شروط بيع العقار في النظام السعودي", "السعودية"),
        ("قانون العمل في دبي", "الإمارات"),
        ("حقوق الطفل", None)
    ]
    
    passed = 0
    for query, expected in queries:
        result = deep_search.extract_country_from_query(query)
        if result == expected:
            print(f"✅ Query: '{query}' -> {result}")
            passed += 1
        else:
            print(f"❌ Query: '{query}' -> Expected '{expected}', got '{result}'")
            
    print(f"\nResult: {passed}/{len(queries)} passed")

if __name__ == "__main__":
    test_country_extraction()
