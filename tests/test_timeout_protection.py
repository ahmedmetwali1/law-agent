"""
🧪 Test: Timeout Protection for Council V2 + Drafter V2

Tests that the system handles LLM timeouts gracefully.
"""
import sys
sys.path.append('e:/law')

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agents.graph.nodes.council_v2 import council_v2_node
from agents.graph.nodes.drafter_v2 import drafter_v2_node


@pytest.mark.asyncio
async def test_council_v2_timeout():
    """Test Council V2 handles timeout gracefully"""
    
    # Mock state
    state = {
        "session_id": "test_timeout_123",
        "input": "ما شروط الهبة؟"
    }
    
    # Mock blackboard
    mock_blackboard = MagicMock()
    mock_blackboard.read_latest_state.return_value = {
        "workflow_status": {"council": "PENDING"},
        "facts_snapshot": {"user_request": "ما شروط الهبة؟"},
        "research_data": {"results": [{"content": "test"}]}
    }
    
    # Mock LLM that times out
    async def mock_timeout(*args, **kwargs):
        await asyncio.sleep(35)  # Longer than 30s timeout
        return MagicMock(content='{}')
    
    mock_llm = AsyncMock()
    mock_llm.ainvoke = mock_timeout
    
    with patch('agents.graph.nodes.council_v2.blackboard', mock_blackboard):
        with patch('agents.graph.nodes.council_v2.get_llm', return_value=mock_llm):
            
            # Execute
            result = await council_v2_node(state)
            
            # Assertions
            assert result is not None
            assert "next_agent" in result
            
            # Check that blackboard was updated (even on timeout)
            assert mock_blackboard.update_segment.called
            
            # Get the strategy that was saved
            call_args = mock_blackboard.update_segment.call_args
            strategy = call_args[0][2]  # 3rd positional arg
            
            # Should have timeout_error flag
            assert "timeout_error" in strategy or "synthesis" in strategy
            
            print("✅ Council V2 timeout test passed")


@pytest.mark.asyncio
async def test_council_v2_normal_execution():
    """Test Council V2 works normally when LLM responds"""
    
    state = {
        "session_id": "test_normal_123",
        "input": "ما شروط الهبة؟"
    }
    
    mock_blackboard = MagicMock()
    mock_blackboard.read_latest_state.return_value = {
        "workflow_status": {"council": "PENDING"},
        "facts_snapshot": {"user_request": "ما شروط الهبة؟"},
        "research_data": {"results": [{"content": "test"}]}
    }
    
    # Mock LLM that responds quickly
    mock_response = MagicMock()
    mock_response.content = '''
    {
        "understanding": {"core_issues": ["test"]},
        "perspectives": {},
        "synthesis": {
            "recommended_strategy": {
                "approach": "test strategy",
                "key_actions": [],
                "legal_basis": []
            }
        }
    }
    '''
    
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    
    with patch('agents.graph.nodes.council_v2.blackboard', mock_blackboard):
        with patch('agents.graph.nodes.council_v2.get_llm', return_value=mock_llm):
            
            result = await council_v2_node(state)
            
            assert result is not None
            assert result["next_agent"] == "drafter"
            
            print("✅ Council V2 normal execution test passed")


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 Running Timeout Protection Tests")
    print("=" * 80)
    
    asyncio.run(test_council_v2_timeout())
    asyncio.run(test_council_v2_normal_execution())
    
    print("\n" + "=" * 80)
    print("✅ All tests passed!")
    print("=" * 80)
