import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.specialists.facts_agent import FactsAgent

async def test_interrogation_flow():
    print("🧪 Testing FactsAgent Interrogation Protocol...")
    
    # Mock LLM
    mock_llm = AsyncMock()
    
    # Cycle 1 Response (Deconstruction): Detect "Commercial Contract" but missing parties
    cycle_1_response = MagicMock()
    cycle_1_response.content = '''```json
    {
        "topic": "Commercial Contract",
        "facts": {
            "jurisdiction": "KSA",
            "material_facts": ["Draft a contract"],
            "dates": [],
            "parties": [],
            "parties_roles": null
        }
    }
    ```'''
    
    # Cycle 2 Response (Gap Analysis): Detect missing "Parties" and "Date"
    cycle_2_response = MagicMock()
    cycle_2_response.content = '''```json
    {
        "missing_critical": ["Identity of the Second Party", "Contract Value"]
    }
    ```'''
    
    mock_llm.ainvoke.side_effect = [cycle_1_response, cycle_2_response]
    
    # Initialize Agent
    agent = FactsAgent(
        llm=mock_llm,
        name="facts_test",
        name_ar="Test Agent",
        session_id="test_session",
        worksheet_id="test_worksheet"
    )
    
    # Mock chat callback to avoid errors
    agent.chat_update = AsyncMock()
    agent.write_to_worksheet = AsyncMock()
    # Mock tool usage (read_case_file)
    agent.use_tool = AsyncMock(return_value={"success": False}) # No case file
    
    # Execute
    context = {
        "query": "I want to draft a commercial contract.",
        "case_id": None,
        "country_id": "KSA"
    }
    
    result = await agent.execute(context)
    
    # Assertions
    print(f"📊 Result Status: {result.get('status')}")
    
    if result.get("status") == "WAITING_FOR_INPUT":
        print("✅ PASS: Agent paused for interrogation.")
        print(f"❓ Generated Question: {result.get('question')}")
        
        missing = result.get("missing", [])
        if "Identity of the Second Party" in missing:
            print("✅ PASS: Correctly identified missing 'Second Party'.")
        else:
            print("❌ FAIL: Did not identify missing parties.")
    else:
        print(f"❌ FAIL: Agent did not pause. Status: {result.get('status')}")

if __name__ == "__main__":
    asyncio.run(test_interrogation_flow())
