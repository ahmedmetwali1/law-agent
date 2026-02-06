
import asyncio
from agents.graph.nodes.router import router_node
from agents.graph.state import AgentState
from langchain_core.messages import HumanMessage

async def test_router():
    test_cases = [
        "What is the penalty for theft in UAE?",
        "Draft a non-disclosure agreement for me.",
        "Add a new client named Ahmed.",
        "Hello, how are you today?",
        "I need a legal opinion on a commercial dispute.",
        "Delete the hearing for tomorrow.",
    ]

    print("=== STARTING ROUTER TEST ===")
    
    for message in test_cases:
        print(f"\nUser: {message}")
        
        # Mock State
        state = {
            "chat_history": [HumanMessage(content=message)],
            "input": message
        }
        
        try:
            result = await router_node(state)
            intent = result.get("intent")
            print(f"-> Classified as: {intent}")
            print(f"-> Scratchpad: {result.get('scratchpad')}")
        except Exception as e:
            print(f"-> ERROR: {e}")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_router())
