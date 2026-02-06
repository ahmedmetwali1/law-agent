"""
Test script for ContextManager
Tests auto-ID resolution and entity tracking
"""

import sys
sys.path.append('e:/law')

from agents.core.context_manager import ContextManager

def test_context_manager():
    """Test ContextManager functionality"""
    
    print("=" * 60)
    print("Testing ContextManager")
    print("=" * 60)
    
    # Initialize context
    ctx = ContextManager(
        session_id="test-session-123",
        lawyer_id="4e22ac65-9024-42f9-9b94-dc4980c51ad6"
    )
    
    print("\n✅ ContextManager initialized")
    print(f"   Session: {ctx.session_id}")
    print(f"   Lawyer ID: {ctx.lawyer_id}")
    
    # Test 1: Auto-fill lawyer_id
    print("\n" + "=" * 60)
    print("Test 1: Auto-fill lawyer_id")
    print("=" * 60)
    
    params = {
        "full_name": "أحمد محمد العتيبي",
        "phone": "0551234567",
        "lawyer_id": "{{AUTO}}"
    }
    
    print(f"\nBefore: {params}")
    filled_params = ctx.inject_context_into_params(params)
    print(f"After:  {filled_params}")
    
    assert filled_params["lawyer_id"] == ctx.lawyer_id, "lawyer_id should be auto-filled!"
    print("✅ lawyer_id auto-filled successfully")
    
    # Test 2: Register client entity
    print("\n" + "=" * 60)
    print("Test 2: Register created entity")
    print("=" * 60)
    
    ctx.register_entity(
        entity_type="client",
        entity_id="client-abc-123",
        entity_name="أحمد محمد العتيبي",
        metadata={"phone": "0551234567"}
    )
    
    print(ctx.get_context_summary())
    
    # Test 3: Auto-fill client_id from context
    print("\n" + "=" * 60)
    print("Test 3: Auto-fill client_id from recent context")
    print("=" * 60)
    
    case_params = {
        "subject": "قضية عمالية",
        "case_number": "2024/100",
        "client_id": "{{AUTO}}",
        "lawyer_id": "{{AUTO}}"
    }
    
    print(f"\nBefore: {case_params}")
    filled_case = ctx.inject_context_into_params(case_params)
    print(f"After:  {filled_case}")
    
    assert filled_case["client_id"] == "client-abc-123", "client_id should be auto-filled from context!"
    assert filled_case["lawyer_id"] == ctx.lawyer_id, "lawyer_id should be auto-filled!"
    print("✅ Both IDs auto-filled successfully")
    
    # Test 4: Multiple entities
    print("\n" + "=" * 60)
    print("Test 4: Multiple entity tracking")
    print("=" * 60)
    
    ctx.register_entity(
        entity_type="case",
        entity_id="case-xyz-456",
        entity_name="قضية 2024/100",
        metadata={"case_number": "2024/100"}
    )
    
    print(ctx.get_context_summary())
    
    # Test 5: Search by name
    print("\n" + "=" * 60)
    print("Test 5: Search entity by name")
    print("=" * 60)
    
    found = ctx.get_entity_by_name("أحمد")
    if found:
        print(f"✅ Found entity: {found.entity_name} (ID: {found.entity_id})")
    else:
        print("❌ Entity not found")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✅")
    print("=" * 60)

if __name__ == "__main__":
    test_context_manager()
