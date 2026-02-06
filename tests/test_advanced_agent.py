import pytest
import asyncio
from app.agents.nodes.router import router_node, RouterDecision
from app.agents.nodes.responder import responder_node
from app.agents.state import LegalState
from langchain_core.messages import HumanMessage

@pytest.mark.asyncio
async def test_advanced_router_legal_research():
    """Test if router correctly identifies a legal research request."""
    state = LegalState(
        messages=[HumanMessage(content="ابحث عن المادة 77 من نظام العمل السعودي")],
        session_id="test",
        user_id="test",
        lawyer_id="test",
        tool_activities=[]
    )
    
    result = await router_node(state)
    print(f"Router Result: {result}")
    
    assert result["router_decision"] == "LEGAL_RESEARCH"
    assert "legal_search" in [t["name"] for t in result["tool_calls"]]

@pytest.mark.asyncio
async def test_advanced_router_contract_draft():
    """Test if router correctly identifies a drafting request."""
    state = LegalState(
        messages=[HumanMessage(content="اكتب عقد إيجار شقة في الرياض")],
        session_id="test",
        user_id="test",
        lawyer_id="test"
    )
    
    result = await router_node(state)
    print(f"Router Result: {result}")
    
    assert result["router_decision"] == "CONTRACT_DRAFT"

@pytest.mark.asyncio
async def test_responder_logic():
    """Test if responder generates a structured response."""
    # Mock state coming from Router
    state = LegalState(
        messages=[HumanMessage(content="ما هي عقوبة التزوير؟")],
        router_decision="LEGAL_RESEARCH",
        tool_outputs={"tool_results": ["MOCK Search Result: 5 years prison."]},
        session_id="test",
        user_id="test",
        lawyer_id="test"
    )
    
    result = await responder_node(state)
    output = result["tool_outputs"]["responder_output"]
    
    assert "reasoning_trace" in output
    assert "final_response" in output
    print(f"Responder Reasoning: {output['reasoning_trace']}")
    print(f"Responder Arabic: {output['final_response']}")
