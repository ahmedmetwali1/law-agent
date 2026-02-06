
import sys
sys.path.append('e:/law')

import asyncio
import json
from unittest.mock import MagicMock, AsyncMock

# 1. Mock dependencies (Blackboard, LLM)
from agents.tools.legal_blackboard_tool import LegalBlackboardTool
mock_blackboard = MagicMock()
mock_blackboard.read_latest_state.return_value = {
    "workflow_status": {"researcher": "DONE", "council": "PENDING"},
    "facts_snapshot": {"query": "Test Facts"},
    "research_data": {"results": []}
}

# Mock LLM Factory
import agents.core.llm_factory
mock_llm = AsyncMock()

# HCF Response with Preamble (The Trap)
council_json = {
    "understanding": {"hidden_intent": "Test"},
    "perspectives": {
        "legislator": {"finding": "Testing HCF", "strength": "High"},
        "strategist": {"maneuver": "Analogical", "viability": "Medium"},
        "skeptic": {"blind_spot": "None"}
    },
    "synthesis": {
        "recommended_strategy": {"approach": "Test Strategy"}
    }
}
# Simulate "Thinking First" preamble
model_output = f"""
Here is my thinking:
The legislator perspective will use HCF.

```json
{json.dumps(council_json)}
```
"""
mock_llm.ainvoke.return_value = MagicMock(content=model_output)
agents.core.llm_factory.get_llm.return_value = mock_llm

# Import Node
from agents.graph.nodes.council_v2 import council_v2_node, blackboard
agents.graph.nodes.council_v2.blackboard = mock_blackboard

async def test_council_parsing():
    print("🚀 Testing Council V2 Legacy vs Robust Parsing...")
    
    state = {
        "session_id": "test_council_robustness",
        "input": "test inputs"
    }
    
    try:
        # Run Node
        result = await council_v2_node(state)
        
        # Verify
        print(f"✅ Result keys: {result.keys()}")
        
        # Check if Blackboard updated (means parsing worked)
        calls = mock_blackboard.update_segment.call_args_list
        strategy_saved = any(c[0][1] == "debate_strategy" for c in calls)
        
        if strategy_saved:
            print("✅ Strategy successfully parsed and saved to Blackboard")
            # Get the saved args to verify content
            # (In a real test we'd inspect the call args more deeply)
        else:
            print("❌ Strategy NOT saved (Parsing Logic Failed)")
            
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_council_parsing())
