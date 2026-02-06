import sys
import asyncio
import os

sys.path.append("e:\\law")

# Mock Environment for testing
os.environ["OPENWEBUI_API_KEY"] = "sk-test" # Mock/Real key if needed for actual call, assuming system has one

async def test_reviewer():
    print("⚖️ Testing Reviewer Node Guardrails...")
    
    from agents.graph.nodes.reviewer import reviewer_node
    
    # 1. Test Unsafe Draft
    unsafe_state = {
        "draft": "You will definitely win the case 100%. The judge has no choice but to rule in your favor.",
        "current_step": 1
    }
    
    print("\n📝 Input Draft (Unsafe):")
    print(f"'{unsafe_state['draft']}'")
    
    try:
        result = await reviewer_node(unsafe_state)
        print("\n🛡️ Reviewer Output:")
        print(result["final_response"])
        
        if "disclaimer" in result["final_response"].lower() or "ملاحظة" in result["final_response"]:
             print("\n✅ Success: Disclaimer added.")
        else:
             print("\n⚠️ Warning: Disclaimer might be missing.")
             
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")

if __name__ == "__main__":
    asyncio.run(test_reviewer())
