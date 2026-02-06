
import sys
sys.path.append('e:/law')

import asyncio
import json
from unittest.mock import MagicMock, AsyncMock

# 1. Setup Mocks
mock_search_result = MagicMock()
mock_search_result.success = True
# Mock a "Legal Chapter" context
mock_search_result.data = [
    {"id": "1", "content": "المادة 368: الهبة عقد يتصرف بمقتضاه الواهب في مال له..."},
    {"id": "2", "content": "المادة 369: لا تتم الهبة إلا بقبض الموهوب له..."}
]
mock_search_result.metadata = {
    "smart_scout": {"citations_map": {"Article 368": {}, "Article 369": {}}}
}

# Mock LLM Factory
import agents.core.llm_factory
mock_llm = AsyncMock()

# Define response for Planning (Phase 1)
plan_response = MagicMock(content='{"queries": ["ما هي الهبة؟"]}')

# Define response for HCF (Phase 3)
hcf_json = {
    "selected_path": "DIRECT",
    "verification_status": "VERIFIED_SOURCE",
    "final_answer_ar": "الهبة هي عقد يتصرف بمقتضاه الواهب في مال له...",
    "citations": ["المادة 368"],
    "confidence_score": 0.98
}
# Wrap in Thinking Block
hcf_content = f"""
### التفكير التحليلي
بما أن المادة 368 موجودة في النص، فالمسار المباشر هو الأنسب.
```json
{json.dumps(hcf_json)}
```
"""
hcf_response = MagicMock(content=hcf_content)

# Define side_effect for multiple calls
# 1. Planning -> plan_response
# 2. HCF Synthesis -> hcf_response
mock_llm.ainvoke.side_effect = [plan_response, hcf_response]

agents.core.llm_factory.get_llm.return_value = mock_llm

# Mock Hybrid Tool
import agents.tools.hybrid_search_tool
mock_hybrid_tool = AsyncMock()
mock_hybrid_tool.run.return_value = mock_search_result
agents.tools.hybrid_search_tool.HybridSearchTool = MagicMock(return_value=mock_hybrid_tool)

# Mock Blackboard
from agents.tools.legal_blackboard_tool import LegalBlackboardTool
mock_blackboard = MagicMock()
mock_blackboard.read_latest_state.return_value = {
    "workflow_status": {"investigator": "DONE"},
    "facts_snapshot": {"structured_facts": {"query": "ما هي الهبة؟"}}
}

# Import Node
from agents.graph.nodes.deep_research import deep_research_node, hybrid_search, blackboard
agents.graph.nodes.deep_research.blackboard = mock_blackboard
agents.graph.nodes.deep_research.hybrid_search = mock_hybrid_tool

async def test_hcf_simple_query():
    print("🚀 Testing HCF Simple Query Integration...")
    
    state = {
        "session_id": "hcf_test_session", 
        "intent": "LEGAL_SIMPLE",  # Trigger HCF
        "input": "ما هي الهبة؟"
    }
    
    try:
        # Run Node
        result = await deep_research_node(state)
        
        # Verify
        print(f"✅ Result keys: {result.keys()}")
        
        if result.get("next_agent") == "end":
            print("✅ Correctly routed to 'end'")
        else:
            print(f"❌ Wrong routing: {result.get('next_agent')}")
            
        final_resp = result.get("final_response", "")
        print(f"📄 Final Response: {final_resp[:50]}...")
        
        if "الهبة هي عقد" in final_resp:
            print("✅ Final response contains expected text")
        else:
            print(f"❌ Unexpected response content: {final_resp}")
            
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_hcf_simple_query())
