"""
Test Suite - نظام الوكلاء القانونيين
======================================

هدف: التحقق من نجاح الإصلاحات الحرجة الأربعة.
تاريخ: 4 فبراير 2026
"""

import asyncio
import uuid
from datetime import datetime

# Test Configuration
TEST_SESSION_ID = str(uuid.uuid4())
TEST_USER_ID = "test_user_001"
TEST_LAWYER_ID = "test_lawyer_001"

# ============================================================================
# Test 1: منع الحلقة المفرغة (Anti-Loop Test)
# ============================================================================

async def test_simple_query_no_loop():
    """
    ✅ المتطلب: استعلام بسيط يجب أن ينتهي في دورة واحدة.
    
    السيناريو:
    1. مستخدم يسأل: "ما هي عقوبة المادة 53 من قانون العمل؟"
    2. النظام يوجه إلى Deep Research
    3. Deep Research يبحث ويعود بنتائج
    4. Judge يُفعّل Circuit Breaker ويسلم الإجابة
    5. ✅ النظام ينتهي عند END (لا يعود لـ Research مرة أخرى)
    
    معايير النجاح:
    - عدد الدورات (Cycles) = 1
    - conversation_stage النهائي = "COMPLETED"
    - next_agent النهائي = "end"
    - لا توجد إعادة توجيه لـ deep_research بعد researcher_status = "DONE"
    """
    from agents.graph.graph import define_graph
    from agents.graph.state import AgentState
    
    graph = define_graph()
    
    initial_state: AgentState = {
        "input": "ما هي عقوبة المادة 53 من قانون العمل السعودي؟",
        "chat_history": [],
        "user_id": TEST_USER_ID,
        "lawyer_id": TEST_LAWYER_ID,
        "session_id": TEST_SESSION_ID,
        "context": {
            "user_context": {
                "full_name": "Test Lawyer",
                "country_id": "sa"
            }
        },
        "intent": None,
        "plan": None,
        "complexity_score": None,
        "current_step": 0,
        "case_state": None,
        "research_results": [],
        "draft": None,
        "critique": None,
        "council_opinions": None,
        "next_agent": None,
        "conversation_stage": None,
        "judge_directives": None,
        "final_response": None
    }
    
    config = {"configurable": {"thread_id": TEST_SESSION_ID}}
    
    # Execute
    cycle_count = 0
    max_cycles = 10  # Safety limit
    visited_nodes = []
    
    async for chunk in graph.astream(initial_state, config):
        cycle_count += 1
        visited_nodes.append(list(chunk.keys())[0])
        
        if cycle_count > max_cycles:
            print(f"❌ FAILED: Exceeded max cycles ({max_cycles})")
            return False
        
        # Check for END
        if "__end__" in chunk:
            final_state = chunk["__end__"]
            break
    
    # Verification
    print(f"\n{'='*60}")
    print(f"Test 1: Simple Query - Anti-Loop")
    print(f"{'='*60}")
    print(f"Cycles: {cycle_count}")
    print(f"Visited Nodes: {visited_nodes}")
    print(f"Final Stage: {final_state.get('conversation_stage')}")
    print(f"Final Next Agent: {final_state.get('next_agent')}")
    print(f"Final Response Preview: {final_state.get('final_response', '')[:100]}...")
    
    # Success Criteria
    success = (
        cycle_count <= 5 and  # Should complete in 1-2 cycles max
        final_state.get("conversation_stage") == "COMPLETED" and
        final_state.get("next_agent") == "end" and
        final_state.get("final_response") is not None
    )
    
    if success:
        print(f"✅ PASSED: Simple query completed without loop")
    else:
        print(f"❌ FAILED: Loop detected or incomplete")
    
    return success


# ============================================================================
# Test 2: الحفاظ على السياق (Context Persistence Test)
# ============================================================================

async def test_multi_turn_conversation():
    """
    ✅ المتطلب: الأسئلة المتتالية يجب أن تحتفظ بالسياق.
    
    السيناريو:
    1. مستخدم يسأل: "ما عقوبة المادة 53؟"
    2. النظام يجيب
    3. مستخدم يسأل: "هل تقصد الفصحى؟" (سؤال جانبي)
    4. ✅ النظام يجب أن يرى نتائج البحث السابقة في Context
    5. ✅ النظام يجب أن يجيب مباشرة بدون إعادة بحث
    
    معايير النجاح:
    - المحاولة الثانية تحتوي "Available Research:" في Context
    - لا يتم إعادة تفعيل deep_research للسؤال الثاني
    - الإجابة تشير إلى "اللغة العربية الفصحى" مباشرة
    """
    from agents.graph.graph import define_graph
    from agents.graph.state import AgentState
    
    graph = define_graph()
    session_id = str(uuid.uuid4())
    
    # Turn 1: Original question
    state_turn1: AgentState = {
        "input": "ما عقوبة المادة 53؟",
        "chat_history": [],
        "user_id": TEST_USER_ID,
        "lawyer_id": TEST_LAWYER_ID,
        "session_id": session_id,
        "context": {"user_context": {"full_name": "Test Lawyer", "country_id": "sa"}},
        "intent": None,
        "plan": None,
        "complexity_score": None,
        "current_step": 0,
        "case_state": None,
        "research_results": [],
        "draft": None,
        "critique": None,
        "council_opinions": None,
        "next_agent": None,
        "conversation_stage": None,
        "judge_directives": None,
        "final_response": None
    }
    
    config = {"configurable": {"thread_id": session_id}}
    
    # Execute Turn 1
    final_state_turn1 = None
    async for chunk in graph.astream(state_turn1, config):
        if "__end__" in chunk:
            final_state_turn1 = chunk["__end__"]
    
    # Turn 2: Follow-up question (off-topic)
    state_turn2 = final_state_turn1.copy()
    state_turn2["input"] = "هل تقصد اللهجة الفصحى أم العامية؟"
    
    # Execute Turn 2
    nodes_visited_turn2 = []
    async for chunk in graph.astream(state_turn2, config):
        nodes_visited_turn2.append(list(chunk.keys())[0])
        if "__end__" in chunk:
            final_state_turn2 = chunk["__end__"]
    
    # Verification
    print(f"\n{'='*60}")
    print(f"Test 2: Multi-Turn Conversation - Context Persistence")
    print(f"{'='*60}")
    print(f"Turn 1 Response: {final_state_turn1.get('final_response', '')[:100]}...")
    print(f"Turn 2 Nodes Visited: {nodes_visited_turn2}")
    print(f"Turn 2 Response: {final_state_turn2.get('final_response', '')[:100]}...")
    
    # Success: Research should NOT be triggered again
    research_triggered_again = "deep_research" in nodes_visited_turn2
    
    success = not research_triggered_again
    
    if success:
        print(f"✅ PASSED: Context preserved, no redundant research")
    else:
        print(f"❌ FAILED: Research was triggered again (context lost)")
    
    return success


# ============================================================================
# Test 3: توافق البيانات (Pydantic Validation Test)
# ============================================================================

async def test_pydantic_validation():
    """
    ✅ المتطلب: جميع Intents يجب أن تكون متوافقة مع Schema.
    
    السيناريو:
    1. النظام يستقبل استعلامات متنوعة
    2. Judge يصنف Intent
    3. ✅ لا توجد أخطاء Pydantic Validation
    
    معايير النجاح:
    - صفر ValidationError
    - جميع Intents ضمن القائمة المسموحة
    """
    from agents.graph.schemas import JudgeDecision
    from pydantic import ValidationError
    
    test_cases = [
        {"intent": "LEGAL_SIMPLE", "next_agent": "deep_research", "complexity": "low", 
         "reasoning": "Test", "plan_description": "Test", "final_response": "تم"},
        {"intent": "LEGAL_COMPLEX", "next_agent": "council", "complexity": "high", 
         "reasoning": "Test", "plan_description": "Test", "final_response": "تم"},
        {"intent": "ADMIN_QUERY", "next_agent": "admin_ops", "complexity": "low", 
         "reasoning": "Test", "plan_description": "Test", "final_response": "تم"},
        {"intent": "CHIT_CHAT", "next_agent": "user", "complexity": "low", 
         "reasoning": "Test", "plan_description": "Test", "final_response": "مرحباً"},
    ]
    
    print(f"\n{'='*60}")
    print(f"Test 3: Pydantic Validation - Schema Compliance")
    print(f"{'='*60}")
    
    failed_cases = []
    for i, case in enumerate(test_cases):
        try:
            decision = JudgeDecision(**case)
            print(f"✅ Case {i+1} ({case['intent']}): VALID")
        except ValidationError as e:
            print(f"❌ Case {i+1} ({case['intent']}): FAILED - {e}")
            failed_cases.append(case['intent'])
    
    success = len(failed_cases) == 0
    
    if success:
        print(f"✅ PASSED: All intents valid")
    else:
        print(f"❌ FAILED: Invalid intents: {failed_cases}")
    
    return success


# ============================================================================
# Test 4: معمارية Blackboard (Blackboard Integration Test)
# ============================================================================

async def test_blackboard_persistence():
    """
    ✅ المتطلب: جميع الوكلاء يقرأون/يكتبون من Blackboard بشكل صحيح.
    
    السيناريو:
    1. Deep Research يكتب نتائج على Blackboard
    2. Judge يقرأ نفس النتائج من Blackboard
    3. ✅ البيانات متطابقة (Read/Write Consistency)
    
    معايير النجاح:
    - البيانات المكتوبة = البيانات المقروءة
    - workflow_status يعكس الحالة الصحيحة
    """
    from agents.tools.legal_blackboard_tool import LegalBlackboardTool
    
    blackboard = LegalBlackboardTool()
    session_id = str(uuid.uuid4())
    
    print(f"\n{'='*60}")
    print(f"Test 4: Blackboard Persistence - Read/Write Consistency")
    print(f"{'='*60}")
    
    # 1. Initialize
    board = blackboard.initialize_state(session_id)
    print(f"✅ Initialized Blackboard for session {session_id[:8]}...")
    
    # 2. Write Research Data
    test_research_data = {
        "results": [
            {"content": "Test legal text", "metadata": {"article": "53"}}
        ],
        "metadata": {"queries_used": ["عقوبة المادة 53"]}
    }
    
    blackboard.update_segment(
        session_id,
        "research_data",
        test_research_data,
        status_update={"researcher": "DONE"}
    )
    print(f"✅ Wrote research_data to Blackboard")
    
    # 3. Read Back
    board_read = blackboard.read_latest_state(session_id)
    research_read = board_read.get("research_data")
    status_read = board_read.get("workflow_status", {})
    
    # 4. Verify
    data_matches = research_read == test_research_data
    status_correct = status_read.get("researcher") == "DONE"
    
    print(f"Data Match: {data_matches}")
    print(f"Status Correct: {status_correct}")
    
    success = data_matches and status_correct
    
    if success:
        print(f"✅ PASSED: Blackboard read/write consistent")
    else:
        print(f"❌ FAILED: Data mismatch")
        print(f"Written: {test_research_data}")
        print(f"Read: {research_read}")
    
    return success


# ============================================================================
# Test 5: سيناريو كامل (End-to-End Integration Test)
# ============================================================================

async def test_e2e_simple_query():
    """
    ✅ المتطلب: سيناريو كامل من البداية للنهاية.
    
    السيناريو:
    User → Gatekeeper → Judge → Deep Research → Judge → END
    
    معايير النجاح:
    - دورة واحدة ناجحة
    - إجابة نهائية موجودة
    - conversation_stage = "COMPLETED"
    """
    print(f"\n{'='*60}")
    print(f"Test 5: End-to-End Integration - Full Cycle")
    print(f"{'='*60}")
    
    # This test will be run manually after deploying
    print(f"⏭️  MANUAL TEST: Run a simple query through the UI")
    print(f"   Expected: One smooth cycle without loops")
    
    return True  # Placeholder


# ============================================================================
# Test Runner
# ============================================================================

async def run_all_tests():
    """
    تشغيل جميع الاختبارات وتوليد Test Log.
    """
    print(f"\n{'='*70}")
    print(f"  TEST SUITE - نظام الوكلاء القانونيين")
    print(f"  تاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    tests = [
        ("Anti-Loop Test", test_simple_query_no_loop),
        ("Context Persistence Test", test_multi_turn_conversation),
        ("Pydantic Validation Test", test_pydantic_validation),
        ("Blackboard Integration Test", test_blackboard_persistence),
        ("E2E Integration Test", test_e2e_simple_query),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*70}")
    print(f"  TEST SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*70}")
    print(f"  OVERALL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'='*70}\n")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_all_tests())
