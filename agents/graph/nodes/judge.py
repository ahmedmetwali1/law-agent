from typing import Dict, Any
from datetime import datetime
import json
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from ..state import AgentState
from ..schemas import JudgeDecision
from ...prompts.judge_prompts import JUDGE_ORCHESTRATOR_PROMPT
from agents.core.llm_factory import get_llm
import logging
import time

import logging
import time
from ...tools.legal_blackboard_tool import LegalBlackboardTool

# ✅ PHASE 1 FIX: Semantic Understanding
from ...core.semantic_classifier import determine_complexity_hybrid

logger = logging.getLogger(__name__)
blackboard = LegalBlackboardTool()

async def judge_node(state: AgentState) -> Dict[str, Any]:
    """
    The General Counsel (System Supervisor).
    Role:
    1. Intent Classification.
    2. Progress Monitoring (The Silent Observer).
    3. Final Delivery.
    """
    logger.info("--- GENERAL COUNSEL (SYSTEM SUPERVISOR) ---")
    
    session_id = state.get("session_id")
    if not session_id:
         # Generate default if missing (should be rare)
         import uuid
         session_id = str(uuid.uuid4())
         state["session_id"] = session_id

    # 1. READ BLACKBOARD STATE
    current_board = blackboard.read_latest_state(session_id)
    if not current_board:
        current_board = blackboard.initialize_state(session_id)
        
    status = current_board.get("workflow_status", {})
    
    # --- PHASE A: DELIVERY (The Interface) ---
    # If final output exists and Drafter is done, deliver it!
    if status.get("drafter") == "DONE":
        final_text = current_board.get("final_output", "")
        if final_text:
            return {
                "intent": "FINAL_DELIVERY",
                "next_agent": "end",
                "final_response": final_text,
                "conversation_stage": "COMPLETED"
            }

    # --- PHASE B: PROGRESS NOTIFICATIONS ---
    # Check if we just finished a stage (Research or Strategy)
    # Ideally, we want to inform the user.
    # We can detect this by checking what the PREVIOUS agent was.
    last_agent = state.get("next_agent") # This is actually the one we are evaluating routing FOR.
    # LangGraph state usually holds the last output.
    # If we are coming here from 'deep_research' or 'council', we can speak.
    
    # However, judge_node is the Router logic usually.
    # If we want to send a notification WITHOUT stopping, we might need to yield a message.
    # In LangGraph, returning a dict merges into state.
    # We rely on the Frontend to observe "conversation_stage" updates?
    # Or we can return a "partial_response" if supported.
    # For now, let's trust the "conversation_stage" update.
    
    # --- PHASE C: DETERMINISTIC ROUTING (The Circuit Breaker) ---
    # 🎯 ROOT CAUSE FIX: Prevent re-routing completed tasks back to agents.
    # If we are coming from 'deep_research' with results in a SIMPLE flow,
    # we MUST deliver the answer. We do NOT ask the Manager (LLM) "What to do?".
    # We ask the Orator (LLM) "How to say it?".
    
    intent_trace = state.get("intent")
    conversation_stage = state.get("conversation_stage")
    
    # ✅ STRICT EXIT CONDITION 1: Return from Simple Research
    if conversation_stage == "RESEARCH_COMPLETE" and intent_trace == "LEGAL_SIMPLE":
        logger.info("🛑 CIRCUIT BREAKER: Detected return from Research in Simple Flow.")
        
        # 1. Get Research from Blackboard (Source of Truth)
        research_blob = current_board.get("research_data") or {}
        res_data = research_blob.get("results", [])
        
        if not res_data:
             # Edge case: Researcher claims DONE but no data
             logger.warning("⚠️ Researcher DONE but no results - asking for clarification.")
             return {
                 "intent": "CLARIFICATION_NEEDED",
                 "next_agent": "end",
                 "final_response": "عذراً، لم أتمكن من العثور على المعلومات المطلوبة في قاعدة البيانات.",
                 "conversation_stage": "COMPLETED"
             }
             
        # 2. Summarize (Orator Mode - NOT Decision Mode)
        llm = get_llm(temperature=0.2, json_mode=False)
        summary_prompt = f"""
        You are the General Counsel delivering research results.
        
        User Query: {state.get('input')}
        Research Results: {str(res_data)[:2500]}
        
        Task: Provide a direct, professional, and concise answer in Arabic.
        Style: Formal Legal Arabic (الفصحى).
        Format: Start with the answer directly. Cite article numbers if applicable.
        
        CRITICAL: Do NOT ask "Do you want more details?". Just answer.
        """
        
        response = await llm.ainvoke([SystemMessage(content=summary_prompt)])
        
        logger.info("✅ Simple Query Delivered - ENDING.")
        return {
            "intent": "FINAL_DELIVERY",
            "next_agent": "end",
            "final_response": response.content,
            "complexity_score": "low",
            "conversation_stage": "COMPLETED"
        }
    
    # ✅ STRICT EXIT CONDITION 2: Check if agent already completed task
    # Prevent re-sending to agents that marked themselves as DONE
    status = current_board.get("workflow_status", {})
    
    # If Researcher is DONE and we're about to route to research again, STOP
    if status.get("researcher") == "DONE" and state.get("next_agent") == "deep_research":
        logger.warning("🚫 Researcher already DONE - preventing re-routing loop.")
        
        # Check complexity to decide next step
        complexity = state.get("complexity_score", "low")
        if complexity == "low":
            # Simple query - just deliver what we have
            research_blob = current_board.get("research_data") or {}
            res_data = research_blob.get("results", [])
            
            if res_data:
                llm = get_llm(temperature=0.2, json_mode=False)
                summary_prompt = f"Summarize these research results in Arabic: {str(res_data)[:2000]}"
                response = await llm.ainvoke([SystemMessage(content=summary_prompt)])
                
                return {
                    "intent": "FINAL_DELIVERY",
                    "next_agent": "end",
                    "final_response": response.content
                }
            else:
                return {
                    "intent": "CLARIFICATION_NEEDED",
                    "next_agent": "end",
                    "final_response": "تم إكمال البحث ولكن لم أجد نتائج."
                }
        else:
            # Complex query - route to council
            logger.info("📊 Complex task - routing to Council.")
            return {
                "intent": "LEGAL_COMPLEX",
                "next_agent": "council",
                "complexity_score": "high"
            }


    # --- PHASE D: DECISION (The Brain) ---
    
    # If we are hearing from the User (Input exists), we deliberate.
    user_input = state.get('input', '')
    
    # 1. Setup Parser & Prompt
    user_context = state.get("context", {}).get("user_context", {})
    lawyer_name = state.get("lawyer_name") or user_context.get("full_name") or "Lawyer"
    today = datetime.now().strftime("%Y-%m-%d")
    chat_history = state.get('chat_history', [])

    parser = PydanticOutputParser(pydantic_object=JudgeDecision)
    format_instructions = parser.get_format_instructions()
    final_system_msg = f"{JUDGE_ORCHESTRATOR_PROMPT.format(lawyer_name=lawyer_name, current_date=today)}\n\n{format_instructions}"
    
    # 1. Prepare Prompt Context
    # Check for Research Data (Blackboard or State)
    research_summary = ""
    # Safe access for JSONB columns which might be None
    research_blob = current_board.get("research_data") or {}
    res_data = research_blob.get("results", []) or state.get("research_results", [])
    
    if res_data:
        summary_lines = []
        for r in res_data[:3]:
            content = r.get('content', 'No content')[:300]
            summary_lines.append(f"- {content}...")
        research_summary = "\n\nAvailable Research:\n" + "\n".join(summary_lines)

    messages = [
        SystemMessage(content=final_system_msg),
        HumanMessage(content=f"User Input: '{user_input}'\nHistory: {str(chat_history[-3:])}{research_summary}")
    ]
    
    try:
        # ✅ PHASE 1 FIX: Use Semantic Classification Instead of Keywords
        
        # 1. Get LLM for classification
        llm = get_llm(temperature=0.0, json_mode=True)
        
        # 2. Determine complexity using hybrid approach
        complexity = await determine_complexity_hybrid(
            query=user_input,
            context=current_board,
            llm=llm
        )
        
        # 3. Route based on complexity (deterministic!)
        if complexity == "simple":
            logger.info(f"⚖️ General Counsel Verdict: LEGAL_SIMPLE -> deep_research")
            
            return {
                "intent": "LEGAL_SIMPLE",
                "next_agent": "deep_research",
                "reasoning": "Simple query - direct research",
                "complexity_score": "low"
            }
        
        elif complexity == "complex":
            logger.info(f"⚖️ General Counsel Verdict: LEGAL_COMPLEX -> council")
            
            return {
                "intent": "LEGAL_COMPLEX",
                "next_agent": "deep_research",  # Research first, then council
                "reasoning": "Complex query - needs strategy",
                "complexity_score": "high"
            }
        
        else:  # medium
            logger.info(f"⚖️ General Counsel Verdict: LEGAL_MEDIUM -> deep_research")
            
            return {
                "intent": "LEGAL_MEDIUM",
                "next_agent": "deep_research",
                "reasoning": "Medium complexity - research then evaluate",
                "complexity_score": "medium"
            }

        # Handle Revision (Forking) - if needed
        # if decision.intent == "REVISION":
        #      new_state = blackboard.fork_session(session_id)
        #      logger.info(f"🔱 Forked Session for Revision: Version {new_state.get('version')}")
              
        # return output_state

    except Exception as e:
        logger.error(f"❌ General Counsel Failed: {e}", exc_info=True)
        return {
            "intent": "CLARIFICATION_NEEDED",
            "next_agent": "user",
            "final_response": "عذراً، حدث خطأ في النظام. يرجى المحاولة مرة أخرى."
        }

# --- Legacy Function Stubs (Optional: Keep if imported elsewhere, otherwise remove) ---
# Currently we assume clean break.
