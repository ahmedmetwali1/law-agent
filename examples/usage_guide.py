"""
Usage Guide: How to Use the Genius Legal AI System
دليل استخدام نظام الذكاء القانوني العبقري

Quick start guide for all new features
"""

from agents.core.enhanced_general_lawyer_agent import EnhancedGeneralLawyerAgent
from agents.memory import MultiTieredMemory, MemoryImportance
from agents.reasoning import HybridReasoningEngine, ReasoningMode
from agents.retrieval import SelfRegulatedRetrieval, ThinkingSpeed
from agents.communication import MCPProtocol

# ============================================
# Example 1: Basic Usage (Simplest)
# ============================================

def example_basic():
    """Simple question answering"""
    
    # Create genius agent
    agent = EnhancedGeneralLawyerAgent()
    
    # Ask a question
    response = agent.think_deeply("ما هي شروط صحة العقد؟")
    
    # Get answer
    print(response["answer"])
    print(f"Confidence: {response['confidence']:.0%}")
    
    # Get reasoning trace
    trace = agent.get_reasoning_trace(response)
    print(trace)


# ============================================
# Example 2: Advanced Usage with Context
# ============================================

def example_advanced():
    """Complex case analysis"""
    
    agent = EnhancedGeneralLawyerAgent(
        reasoning_mode="auto",  # Auto-select best mode
        enable_consolidation=True
    )
    
    # Complex legal analysis
    case_text = """
    وقع الطرفان عقداً تجارياً بقيمة 500,000 ريال.
    تم الإيجاب كتابةً والقبول شفاهةً.
    الطرف الأول شركة مساهمة والطرف الثاني فرد.
    """
    
    response = agent.think_deeply(
        query="هل العقد صحيح قانونياً؟",
        context={
            "case_facts": case_text,
            "domain": "commercial_law",
            "urgency": "high"
        }
    )
    
    print(f"Answer: {response['answer']}")
    print(f"Confidence: {response['confidence']:.0%}")
    print(f"Complexity: {response['complexity']}")
    print(f"Mode used: {response['reasoning_mode']}")
    print(f"Retrieved memories: {response['retrieved_memories_count']}")


# ============================================
# Example 3: Memory System
# ============================================

def example_memory():
    """Using multi-tiered memory"""
    
    agent = EnhancedGeneralLawyerAgent()
    
    # Remember important information
    agent.memory_system.remember(
        content="المادة 10 من نظام المعاملات: يشترط لصحة العقد...",
        importance=MemoryImportance.CRITICAL,
        tags=["contract_law", "article_10"],
        confidence=1.0,
        source="legal_code"
    )
    
    # Retrieve context
    context = agent.memory_system.retrieve_context()
    print(f"Working memory: {len(context)} items")
    
    # Search knowledge
    knowledge = agent.memory_system.retrieve_knowledge(tags=["contract_law"])
    print(f"Relevant knowledge: {len(knowledge)} items")
    
    # Get memory summary
    summary = agent.get_memory_summary()
    print(summary)


# ============================================
# Example 4: Hybrid Reasoning
# ============================================

def example_reasoning():
    """Using different reasoning modes"""
    
    from agents.reasoning import HybridReasoningEngine, ReasoningMode
    
    reasoning = HybridReasoningEngine()
    
    # Chain of Thought
    result_cot = reasoning.reason(
        query="ما هو العقد؟",
        mode=ReasoningMode.CHAIN_OF_THOUGHT
    )
    
    # ReAct (with tools)
    result_react = reasoning.reason(
        query="ابحث عن أحدث القوانين التجارية",
        mode=ReasoningMode.REACT
    )
    
    # Hybrid (best of both)
    result_hybrid = reasoning.reason(
        query="تحليل شامل لشروط العقد",
        mode=ReasoningMode.HYBRID
    )
    
    # Auto-routing
    result_auto = reasoning.reason(
        query="سؤال معقد يحتاج تحليل عميق..."
        # No mode specified - auto-selects based on complexity
    )


# ============================================
# Example 5: Self-Regulated Retrieval
# ============================================

def example_retrieval():
    """Smart retrieval decisions"""
    
    from agents.retrieval import SelfReg ulatedRetrieval, ThinkingSpeed
    
    memory = MultiTieredMemory()
    retrieval = SelfRegulatedRetrieval(memory)
    
    # Fast thinking (quick answer)
    fast_result = retrieval.retrieve(
        query="ما هو العقد؟",
        thinking_speed=ThinkingSpeed.FAST
    )
    
    # Slow thinking (deep analysis)
    slow_result = retrieval.retrieve(
        query="تحليل معقد...",
        thinking_speed=ThinkingSpeed.SLOW
    )
    
    print(f"Fast: {fast_result.decision.value} (cost: {fast_result.cost_estimate})")
    print(f"Slow: {slow_result.decision.value} (cost: {slow_result.cost_estimate})")


# ============================================
# Example 6: Multi-Agent Communication (MCP)
# ============================================

async def example_mcp():
    """Agent-to-agent communication"""
    
    protocol = MCPProtocol()
    
    # Create agents
    lawyer = protocol.create_agent("lawyer_agent", "legal")
    researcher = protocol.create_agent("researcher_agent", "research")
    
    # Send request
    response = await protocol.send_request(
        sender_id="lawyer_agent",
        receiver_id="researcher_agent",
        request_data={
            "task": "research",
            "query": "أحدث التعديلات على نظام العمل"
        }
    )
    
    # Send command
    await protocol.send_command(
        sender_id="lawyer_agent",
        receiver_id="researcher_agent",
        command="start_analysis",
        params={"case_id": "12345"}
    )
    
    # Get stats
    stats = protocol.get_protocol_info()
    print(stats)


# ============================================
# Example 7: Complete Workflow
# ============================================

def example_complete_workflow():
    """End-to-end usage"""
    
    # Initialize genius agent
    agent = EnhancedGeneralLawyerAgent(
        use_multi_tiered_memory=True,
        reasoning_mode="auto",
        self_regulated_retrieval=True,
        enable_consolidation=True
    )
    
    # Session 1: First query
    response1 = agent.think_deeply("ما هي شروط صحة العقد؟")
    print(f"Q1: {response1['answer']}")
    
    # Session 2: Related query (will use memory)
    response2 = agent.think_deeply("هل يشترط الكتابة للعقد؟")
    print(f"Q2: {response2['answer']}")
    
    # Session 3: Complex analysis
    response3 = agent.think_deeply(
        query="أريد تحليل قانوني شامل لقضية تجارية",
        context={"urgency": "high"}
    )
    print(f"Q3: {response3['answer']}")
    
    # Get session statistics
    stats = agent.get_session_stats()
    print(f"\nSession Stats:")
    print(f"- Interactions: {stats['interactions']}")
    print(f"- Duration: {stats['duration_minutes']:.1f} minutes")
    print(f"- Memory consolidations: {stats.get('memory_consolidations', 0)}")
    
    # Get memory summary
    memory_summary = agent.get_memory_summary()
    print(f"\nMemory Summary:")
    print(f"- Working: {memory_summary['working_memory']['current_items']} items")
    print(f"- Episodic: {memory_summary['episodic_memory']['total_episodes']} episodes")
    print(f"- Long-term: {memory_summary['long_term_memory']['total_knowledge']} items")


# ============================================
# Run Examples
# ============================================

if __name__ == "__main__":
    print("="  * 60)
    print("Legal AI System - Usage Examples")
    print("=" * 60)
    
    # Run basic example
    print("\n1. Basic Usage:")
    example_basic()
    
    # Run advanced example
    print("\n2. Advanced Usage:")
    example_advanced()
    
    # Run memory example
    print("\n3. Memory System:")
    example_memory()
    
    # Run complete workflow
    print("\n7. Complete Workflow:")
    example_complete_workflow()
