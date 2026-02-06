from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .nodes.council_v2 import council_v2_node  # ✅ V2: Single LLM + CoT
from .nodes.drafter_v2 import drafter_v2_node  # ✅ V2: Structured + Validated
from .nodes.judge import judge_node
from .nodes.deep_research import deep_research_node
from .nodes.gatekeeper import gatekeeper_node, fast_track_node
from .subgraphs.admin_ops import admin_ops_node
from .nodes.reflector import reflect_node
from ..tools.legal_blackboard_tool import LegalBlackboardTool
import logging

logger = logging.getLogger(__name__)
blackboard = LegalBlackboardTool()


# --- Routing Logic ---

def route_gatekeeper_output(state: AgentState):
    """
    Decides where to go after the Gatekeeper checks the input.
    """
    next_agent = state.get("next_agent")
    
    if next_agent == "fast_track":
        return "fast_track"
    elif next_agent == "admin_ops":
        return "admin_ops"
    # Default to Judge for everything else
    return "judge"

def route_judge_output(state: AgentState):
    """
    Determines where to go after the General Counsel (Judge) speaks.
    """
    next_agent = state.get("next_agent")
    complexity = state.get("complexity_score", "low")
    
    if next_agent == "end" or next_agent == "user":
        return END

    if next_agent == "admin_ops":
        return "admin_ops"
        
    elif next_agent == "council":
        # Complex Legal Task -> Research First (Investigator)
        return "deep_research"

    elif next_agent == "deep_research":
        # Simple Legal Task -> Research Only
        return "deep_research"
        
    return END

def route_reflector_output(state: AgentState):
    """
    After Reflection, where do we go?
    Usually to the originally planned agent, unless Reflector changed it (not implemented yet).
    """
    next_agent = state.get("next_agent")
    
    if next_agent == "admin_ops":
        return "admin_ops"
    elif next_agent == "council":
        return "deep_research" # Council flow starts with research
        
    return END

def route_admin_output(state: AgentState):
    """
    Decides where to go after Admin Ops.
    Standard: END
    Escalation: judge
    """
    intent = state.get("intent")
    if intent == "ESCALATE_TO_JUDGE":
        return "judge"
    return END

def route_research_output(state: AgentState):
    """
    🎯 STRICT EXIT CONDITIONS - Anti-Loop Logic.
    Decides where to go after Deep Research.
    
    CRITICAL RULES (Root Cause Fix):
    1. Simple Query (low complexity) → MUST END if research is done.
    2. NO re-routing to 'judge' for reconsideration - that causes loops.
    3. Check Blackboard status, not just State.
    """
    # Use global blackboard and logger (imported at top)
    
    # 1. Check for Explicit Fail Signal
    if state.get("revisit_flag"):
        logger.info("🚫 Research Failed - Asking user for more info.")
        return END  # User needs to provide more context

    
    # 2. Read Blackboard Status (Source of Truth)
    session_id = state.get("session_id")
    if session_id:
        current_board = blackboard.read_latest_state(session_id)
        if current_board:
            status = current_board.get("workflow_status", {})
            researcher_status = status.get("researcher", "PENDING")
            
            # ✅ ROOT CAUSE FIX: If researcher is DONE, check complexity
            if researcher_status == "DONE":
                complexity = state.get("complexity_score", "medium")
                
                # 🛑 STRICT EXIT CONDITION for Simple Queries
                if complexity == "low":
                    # Check if we have a final response
                    if state.get("final_response"):
                        logger.info("✅ Simple Query Complete - ENDING.")
                        return END
                    
                    # If deep_research returned without final_response, 
                    # it means it wants Judge to summarize
                    # But Judge has Circuit Breaker for this
                    logger.info("⚡ Simple Query - Routing to Judge for final delivery.")
                    return "judge"
                
                # Complex Query → Council
                logger.info("🏛️ Complex Query - Routing to Council.")
                return "council"
    
    # 3. Fallback Logic (State-based if Blackboard unavailable)
    complexity = state.get("complexity_score", "medium")
    conversation_stage = state.get("conversation_stage", "")
    
    # If it was a simple query AND we have final_response
    if complexity == "low":
        if state.get("final_response"):
            logger.info("✅ [Fallback] Simple Query Complete - ENDING.")
            return END
        
        # Otherwise, let Judge handle it (should trigger Circuit Breaker)
        logger.warning("⚠️ [Fallback] Simple Query without response - routing to Judge.")
        return "judge"
    
    # Default: Complex tasks go to Council
    logger.info("🏛️ [Fallback] Routing to Council.")
    return "council"


def define_graph():
    """
    Builds the Legal AI StateGraph (LCE v2.0 - Hybrid Architecture).
    """
    workflow = StateGraph(AgentState)
    
    # --- Nodes ---
    workflow.add_node("gatekeeper", gatekeeper_node)
    workflow.add_node("fast_track", fast_track_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("admin_ops", admin_ops_node)
    workflow.add_node("deep_research", deep_research_node) # The Scout
    workflow.add_node("council", council_v2_node) # ✅ V2: The Strategic Analyst
    workflow.add_node("drafter", drafter_v2_node) # ✅ V2: The Document Generator
    workflow.add_node("reflect_node", reflect_node) # 🧠 Thinking Tunnel
    
    # --- Edges ---
    # 0. Entry Point: Gatekeeper
    workflow.set_entry_point("gatekeeper")
    
    # 1. From Gatekeeper -> (Fast Track | Judge)
    workflow.add_conditional_edges(
        "gatekeeper",
        route_gatekeeper_output,
        {
            "fast_track": "fast_track",
            "judge": "judge",
            "admin_ops": "admin_ops"
        }
    )
    
    # 1.a Fast Track -> END
    workflow.add_edge("fast_track", END)
    
    # 2. From Judge -> (Reflect | Admin | Council | End)
    workflow.add_conditional_edges(
        "judge",
        route_judge_output,
        {
            "reflect_node": "reflect_node",
            "admin_ops": "admin_ops",
            "deep_research": "deep_research", 
            END: END
        }
    )
    
    # 2.5 From Reflector -> (Admin | Council)
    workflow.add_conditional_edges(
        "reflect_node",
        route_reflector_output,
        {
            "admin_ops": "admin_ops",
            "deep_research": "deep_research",
            END: END
        }
    )
    
    # 3. From Admin -> (END | Judge)
    workflow.add_conditional_edges(
        "admin_ops",
        route_admin_output,
        {
            "judge": "judge",
            END: END
        }
    ) 
    
    # 4. From Research -> (Council | Judge | END)
    workflow.add_conditional_edges(
        "deep_research",
        route_research_output,
        {
            "council": "council",
            "judge": "judge",
            END: END
        }
    )
    
    # 5. From Council -> Drafter (Sequential)
    workflow.add_edge("council", "drafter")
    
    # 6. From Drafter -> Judge (for Final Delivery)
    workflow.add_edge("drafter", "judge")
    
    # Checkpointer
    checkpointer = MemorySaver()
    
    return workflow.compile(checkpointer=checkpointer)
