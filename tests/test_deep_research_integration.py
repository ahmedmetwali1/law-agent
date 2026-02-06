
import sys
sys.path.append('e:/law')

import asyncio
from unittest.mock import MagicMock, AsyncMock

# Mock Search Results (moved up as it's needed for hybrid_tool mock)
mock_search_result = MagicMock()
mock_search_result.success = True
mock_search_result.data = [{"id": "1", "content": "Article 368: Donation is...", "metadata": {"sequence_number": 1}}]
mock_search_result.metadata = {
    "quick_scout": {"context_quality": 0.8},
    "smart_scout": {
        "search_strategy": "precision_search",
        "citations_map": {"Article 368": {}}
    }
}

# Mock dependencies BEFORE importing deep_research
import agents.core.llm_factory
# Mock LLM
mock_llm = AsyncMock()
mock_llm.ainvoke.return_value = MagicMock(content='{"queries": ["query1"]}')
agents.core.llm_factory.get_llm.return_value = mock_llm

import agents.tools.hybrid_search_tool
# Mock V3 Tool
mock_hybrid_tool = AsyncMock()
mock_hybrid_tool.run.return_value = mock_search_result
agents.tools.hybrid_search_tool.HybridSearchTool = MagicMock(return_value=mock_hybrid_tool)

# Now import the node
from agents.graph.nodes.deep_research import deep_research_node, hybrid_search

# Mock Other Tools (to avoid DB calls)
mock_doc_tool = MagicMock()
mock_doc_tool.run.return_value = MagicMock(success=True, data={"siblings": []})
agents.graph.nodes.deep_research.doc_tool = mock_doc_tool

mock_principle_tool = MagicMock()
mock_principle_tool.run.return_value = MagicMock(success=True, data=[])
agents.graph.nodes.deep_research.principle_search = mock_principle_tool

# Re-apply mocks to the imported module instance just in case
agents.graph.nodes.deep_research.hybrid_search = mock_hybrid_tool

# Mock Blackboard
from agents.tools.legal_blackboard_tool import LegalBlackboardTool
mock_blackboard = MagicMock()
mock_blackboard.read_latest_state.return_value = {
    "workflow_status": {"investigator": "DONE"},
    "facts_snapshot": {"structured_facts": {"query": "ما هي الهبة؟"}}
}
import agents.graph.nodes.deep_research
agents.graph.nodes.deep_research.blackboard = mock_blackboard

# Mock Search Results
mock_search_result = MagicMock()
mock_search_result.success = True
mock_search_result.data = [{"id": "1", "content": "Article 368: Donation is...", "metadata": {"sequence_number": 1}}]
mock_search_result.metadata = {
    "quick_scout": {"context_quality": 0.8},
    "smart_scout": {
        "search_strategy": "precision_search",
        "citations_map": {"Article 368": {}}
    }
}
hybrid_search.run = AsyncMock(return_value=mock_search_result)

async def test_integration():
    print("🚀 Testing Deep Research Integration...")
    
    state = {
        "session_id": "test_session", 
        "intent": "LEGAL_COMPLEX",
        "input": "ما هي الهبة؟"
    }
    
    # Run Node
    result = await deep_research_node(state)
    
    # Verify Search Called
    print(f"✅ Search Called: {hybrid_search.run.called}")
    
    # Verify Blackboard Writes
    print(f"✅ Blackboard Writes: {mock_blackboard.update_segment.call_count}")
    
    calls = mock_blackboard.update_segment.call_args_list
    thinking_update = any(c[0][1] == "agent_thinking" for c in calls)
    data_update = any(c[0][1] == "research_data" for c in calls)
    
    if thinking_update:
        print("✅ Thinking Trace written to 'agent_thinking'")
    else:
        print("❌ Thinking Trace NOT written")
        
    if data_update:
        print("✅ Research Data written to 'research_data'")
    else:
        print("❌ Research Data NOT written")
        
    print("✅ Integration Test Complete")

if __name__ == "__main__":
    asyncio.run(test_integration())
