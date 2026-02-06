
import sys
import os
import re

# Add project root to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.graph.nodes.gatekeeper import gatekeeper_node

# Mock AgentState
class MockState(dict):
    pass

TEST_CASES = [
    # Admin Queries (Expected: admin_ops)
    ("كم موكل لدي", "admin_ops"),
    ("ما هي جلساتي القادمة", "admin_ops"),
    ("أعطني إحصائيات المهام", "admin_ops"),
    ("كم قضية مفتوحة", "admin_ops"),
    ("عدد الموكلين النشطين", "admin_ops"),
    
    # Legal Queries (Expected: judge)
    ("ما حكم التقادم في القانون المدني", "judge"),
    ("اشرح لي المادة 77 من قانون الإجراءات", "judge"),
    ("هل يجوز للموكل سحب الوكالة", "judge"),
    ("ما الفرق بين البطلان والانعدام", "judge"),
    ("أريد صياغة مذكرة دفاع", "judge"),
    
    # Mixed/Ambiguous (Expected: judge or admin based on strict logic)
    # "Client" in legal context -> Should be Judge
    ("موكلي يسأل عن حكم التقادم", "judge"), 
    # "Task" statistics -> Admin
    ("كم قضية تقادم لدي", "admin_ops"), 
    
    # 🚨 Edge Cases (User Feedback Refinement)
    # Typo tolerance
    ("كم موكلل لديي", "admin_ops"), 
    # Slang (Gulf dialect example)
    ("شكثر عميل عندي", "admin_ops"),
    # Ambiguous single word -> Judge (Complex/Fallback) or Clarification? Gatekeeper routes Complex to Judge.
    ("موكل", "judge"), 
    # Long query
    ("أريد معرفة عدد الموكلين الذين لديهم قضايا نشطة ومفتوحة في النظام", "admin_ops"),
]

def run_tests():
    print("🚀 Starting Routing System Tests...\n")
    correct = 0
    total = len(TEST_CASES)
    
    for query, expected_agent in TEST_CASES:
        # Mock State
        state = MockState({"input": query})
        
        # Run Gatekeeper
        result = gatekeeper_node(state)
        next_agent = result.get("next_agent")
        
        # Check Result
        status = "✅ PASS" if next_agent == expected_agent else "❌ FAIL"
        if next_agent == expected_agent:
            correct += 1
            
        print(f"{status} | Query: '{query}'")
        print(f"       -> Got: {next_agent} | Expected: {expected_agent}")
        if next_agent != expected_agent:
            print(f"       -> Intent: {result.get('intent')}")
    
    accuracy = (correct / total) * 100
    print(f"\n📊 Results: {correct}/{total} passed.")
    print(f"🎯 Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 90:
        print("\n✨ SUCCESS: Routing logic meets accuracy requirements!")
    else:
        print("\n⚠️ FAILURE: Accuracy below 90%.")

if __name__ == "__main__":
    run_tests()
