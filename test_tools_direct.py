"""
Simple Direct Tool Execution Test
اختبار مباشر لتنفيذ الأدوات

This bypasses all complexity and directly tests tool execution.
"""

import logging
from agents.tools.unified_tools import UnifiedToolSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_tools():
    """Test tools directly"""
    
    # Use a real lawyer_id from database
    test_lawyer_id = "5632cc0e-dc9d-4d34-b094-a6826b186ce4"
    test_lawyer_name = "المحامي"
    
    print("\n" + "=" * 60)
    print("🧪 Testing Unified Tool System")
    print("=" * 60 + "\n")
    
    # Initialize tools
    print("1️⃣ Initializing tools...")
    tools = UnifiedToolSystem(test_lawyer_id, test_lawyer_name)
    print(f"✅ Registered {len(tools.get_available_tools_list())} tools\n")
    
    # Test 1: Get today's hearings
    print("2️⃣ Testing get_today_hearings...")
    result = tools.execute_tool("get_today_hearings")
    print(f"Result: {result}\n")
    
    # Test 2: List all clients
    print("3️⃣ Testing list_all_clients...")
    result = tools.execute_tool("list_all_clients")
    print(f"Result: {result}\n")
    
    # Test 3: Search clients
    print("4️⃣ Testing search_clients...")
    result = tools.execute_tool("search_clients", query="أحمد")
    print(f"Result: {result}\n")
    
    print("=" * 60)
    print("✅ All tests complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_tools()
