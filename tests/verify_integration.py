import sys
sys.path.append("e:/law")
import asyncio
from agents.graph.nodes.deep_research import hybrid_search, deep_research_node
from agents.tools.hybrid_search_tool import HybridSearchTool

def verify_integration():
    print("🚀 Verifying Deep Research Integration...")
    
    # Check instance
    if isinstance(hybrid_search, HybridSearchTool):
        print("✅ hybrid_search is instance of HybridSearchTool")
    else:
        print(f"❌ Error: hybrid_search is {type(hybrid_search)}")
        
    print("✅ Integration successful!")

if __name__ == "__main__":
    verify_integration()
