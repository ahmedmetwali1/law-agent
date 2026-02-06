
import sys
sys.path.append('e:/law')
from agents.tools.hybrid_search_tool import HybridSearchTool

def test_context_quality():
    tool = HybridSearchTool()
    
    query = "ما هي الهبة؟"
    
    # Mock results similar to what we might get (but maybe slightly different wording)
    # Using words that definitely SHOULD match 'الهبة' if normalization works
    results = [
        {"content": "المادة 368: الهبة تمليك مال أو حق مالي لآخر حال حياة الواهب دون عوض."},
        {"content": "يجوز للواهب أن يرجِع في الهبة إذا قبل الموهوب له."},
        {"content": "شروط عقد الهبة في القانون المدني."}
    ]
    
    # 1. Test Extraction
    q_terms = tool._extract_legal_nouns_from_query(query)
    c_terms = tool._extract_legal_nouns_from_query(" ".join([r['content'] for r in results]))
    
    print(f"Query Terms: {q_terms}")
    print(f"Context Terms Sample: {list(c_terms)[:10]}")
    
    # 2. Test Quality Score
    quality = tool._validate_context_quality(query, results)
    print(f"Quality Score: {quality}")
    
    if quality == 0.0:
        print("❌ FAIL: Quality is 0.0 despite obvious matches")
    else:
        print(f"✅ PASS: Quality > 0 ({quality})")

if __name__ == "__main__":
    test_context_quality()
