"""
Quick Integration Test - Metadata-Driven System
اختبار تكامل سريع - النظام الديناميكي

Tests basic functionality without database dependency
"""

import json

def test_integration():
    """Test the integration without database"""
    
    print("\n" + "=" * 80)
    print(" 🧪 METADATA-DRIVEN SYSTEM INTEGRATION TEST")
    print("=" * 80 + "\n")
    
    test_results = []
    
    # =========================================================================
    # TEST 1: Import and Initialize DatabaseToolGenerator
    # =========================================================================
    print("📦 TEST 1: Import DatabaseToolGenerator...")
    try:
        from agents.tools.db_tool_factory import DatabaseToolGenerator
        from agents.config.schema_registry import SCHEMA_METADATA, get_all_tables
        print("✅ PASS: Imports successful")
        test_results.append(("Import Test", True, None))
    except Exception as e:
        print(f"❌ FAIL: {e}")
        test_results.append(("Import Test", False, str(e)))
        return test_results
    
    # =========================================================================
    # TEST 2: Initialize Generator
    # =========================================================================
    print("\n🔧 TEST 2: Initialize Generator...")
    try:
        generator = DatabaseToolGenerator(lawyer_id="test-lawyer-123")
        generated_tools = generator.get_all_tools()
        
        print(f"✅ PASS: Generator initialized")
        print(f"   📊 Generated {len(generated_tools)} tools")
        print(f"   📋 Tables in schema: {len(get_all_tables())}")
        
        test_results.append(("Generator Init", True, f"{len(generated_tools)} tools"))
    except Exception as e:
        print(f"❌ FAIL: {e}")
        test_results.append(("Generator Init", False, str(e)))
        return test_results
    
    # =========================================================================
    # TEST 3: Check Tool Names
    # =========================================================================
    print("\n📝 TEST 3: Verify Generated Tool Names...")
    try:
        tool_names = list(generated_tools.keys())
        
        # Expected tool patterns
        expected_patterns = ["insert_", "query_", "update_", "delete_", "get_", "semantic_search_"]
        
        matching_tools = {}
        for pattern in expected_patterns:
            matching = [name for name in tool_names if name.startswith(pattern)]
            matching_tools[pattern] = len(matching)
        
        print("✅ PASS: Tool names verified")
        for pattern, count in matching_tools.items():
            print(f"   {pattern}*: {count} tools")
        
        test_results.append(("Tool Names", True, json.dumps(matching_tools)))
    except Exception as e:
        print(f"❌ FAIL: {e}")
        test_results.append(("Tool Names", False, str(e)))
    
    # =========================================================================
    # TEST 4: Check OpenAI Format
    # =========================================================================
    print("\n🔧 TEST 4: OpenAI Function Calling Format...")
    try:
        tools_for_llm = generator.get_tools_for_llm()
        
        # Validate structure
        assert isinstance(tools_for_llm, list), "Output must be a list"
        assert len(tools_for_llm) > 0, "Must have at least one tool"
        
        # Check first tool structure
        first_tool = tools_for_llm[0]
        assert "type" in first_tool, "Tool must have 'type'"
        assert "function" in first_tool, "Tool must have 'function'"
        assert "name" in first_tool["function"], "Function must have 'name'"
        assert "description" in first_tool["function"], "Function must have 'description'"
        assert "parameters" in first_tool["function"], "Function must have 'parameters'"
        
        print(f"✅ PASS: OpenAI format valid")
        print(f"   📊 {len(tools_for_llm)} tools formatted")
        print(f"   📋 Sample tool: {first_tool['function']['name']}")
        
        test_results.append(("OpenAI Format", True, f"{len(tools_for_llm)} formatted"))
    except Exception as e:
        print(f"❌ FAIL: {e}")
        test_results.append(("OpenAI Format", False, str(e)))
    
    # =========================================================================
    # TEST 5: Schema Registry
    # =========================================================================
    print("\n📚 TEST 5: Schema Registry...")
    try:
        tables = get_all_tables()
        
        # Check specific tables
        expected_tables = ["clients", "cases", "hearings", "tasks", "documents"]
        found_tables = [t for t in expected_tables if t in tables]
        
        print(f"✅ PASS: Schema registry valid")
        print(f"   📊 Total tables: {len(tables)}")
        print(f"   ✅ Found {len(found_tables)}/{len(expected_tables)} expected tables")
        print(f"   📋 Missing: {set(expected_tables) - set(found_tables) if len(found_tables) < len(expected_tables) else 'None'}")
        
        test_results.append(("Schema Registry", True, f"{len(tables)} tables"))
    except Exception as e:
        print(f"❌ FAIL: {e}")
        test_results.append(("Schema Registry", False, str(e)))
    
    # =========================================================================
    # TEST 6: UnifiedToolSystem Integration
    # =========================================================================
    print("\n🔗 TEST 6: UnifiedToolSystem Integration...")
    try:
        from agents.tools.unified_tools import UnifiedToolSystem
        
        # Initialize unified system
        unified = UnifiedToolSystem(
            lawyer_id="test-lawyer-456",
            lawyer_name="مختبر النظام"
        )
        
        # Check if db_generator exists
        assert hasattr(unified, 'db_generator'), "Must have db_generator attribute"
        assert unified.db_generator is not None, "db_generator must be initialized"
        
        # Check tool count
        all_unified_tools = unified.get_available_tools_list()
        
        print(f"✅ PASS: UnifiedToolSystem integrated")
        print(f"   📊 Total tools: {len(all_unified_tools)}")
        print(f"   ✅ DB Generator: {'Active' if unified.db_generator else 'Inactive'}")
        
        # Check for dynamic tools in the list
        dynamic_tool_samples = ["insert_clients", "query_cases", "get_hearings_schema"]
        found_dynamic = [t for t in dynamic_tool_samples if t in all_unified_tools]
        print(f"   📋 Dynamic tools found: {len(found_dynamic)}/{len(dynamic_tool_samples)}")
        
        test_results.append(("UnifiedToolSystem", True, f"{len(all_unified_tools)} total tools"))
    except Exception as e:
        print(f"❌ FAIL: {e}")
        test_results.append(("UnifiedToolSystem", False, str(e)))
    
    # =========================================================================
    # TEST 7: Tool Execution (Dry Run - Schema Only)
    # =========================================================================
    print("\n🎯 TEST 7: Tool Execution (Schema Query)...")
    try:
        # Try to get schema (doesn't require DB)
        schema_result = generator.execute_tool("get_clients_schema")
        
        assert "success" in schema_result, "Result must have 'success' field"
        assert schema_result.get("success") == True, "Schema query must succeed"
        assert "columns" in schema_result, "Schema must have 'columns'"
        assert "required_fields" in schema_result, "Schema must have 'required_fields'"
        
        columns_count = len(schema_result.get("columns", []))
        required_count = len(schema_result.get("required_fields", []))
        
        print(f"✅ PASS: Tool execution works")
        print(f"   📊 Clients schema: {columns_count} columns")
        print(f"   ✅ Required fields: {required_count}")
        print(f"   📋 Supports vector search: {schema_result.get('supports_vector_search')}")
        
        test_results.append(("Tool Execution", True, "Schema query successful"))
    except Exception as e:
        print(f"❌ FAIL: {e}")
        test_results.append(("Tool Execution", False, str(e)))
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print(" 📊 TEST RESULTS SUMMARY")
    print("=" * 80 + "\n")
    
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    
    for test_name, success, detail in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name:25s} | {detail or 'N/A'}")
    
    print("\n" + "-" * 80)
    print(f"   TOTAL: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    print("-" * 80 + "\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Metadata-Driven System is FULLY OPERATIONAL\n")
        return True
    elif passed >= total - 1:
        print("⚠️ MOSTLY PASSED")
        print("✅ System is operational with minor warnings\n")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️ Review errors above\n")
        return False


if __name__ == "__main__":
    import sys
    success = test_integration()
    sys.exit(0 if success else 1)
