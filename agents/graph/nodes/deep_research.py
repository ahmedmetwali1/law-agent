from typing import Dict, Any, List
import re
import json
import asyncio
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import AgentState
from ...tools.hybrid_search_tool import HybridSearchTool
from ...tools.fetch_tools import GetRelatedDocumentTool, FlexibleSearchTool
from ...config.database import db
from agents.core.llm_factory import get_llm
import logging

from ...tools.legal_blackboard_tool import LegalBlackboardTool

logger = logging.getLogger(__name__)

# Initialize tools
hybrid_search = HybridSearchTool()
blackboard = LegalBlackboardTool()
doc_tool = GetRelatedDocumentTool()
principle_search = FlexibleSearchTool()

async def deep_research_node(state: AgentState) -> Dict[str, Any]:
    """
    Combined Node: Investigator & Researcher.
    Role determines behavior based on 'intent' or 'status'.
    """
    logger.info("--- DEEP RESEARCH / INVESTIGATOR NODE ---")
    
    session_id = state.get("session_id") or "unknown_session"
    intent = state.get("intent", "LEGAL_COMPLEX")
    user_input = state.get("input", "")
    
    # Load Current Board
    current_board = blackboard.read_latest_state(session_id)
    if not current_board:
        current_board = blackboard.initialize_state(session_id)
        
    status = current_board.get("workflow_status", {})
    investigator_status = status.get("investigator", "PENDING")
    
    # --- MODE 1: INVESTIGATOR (Fact Keeper) ---
    # ✅ FIX: Skip Investigator for SIMPLE queries to prevent clarification loops
    # Trigger: If we haven't confirmed facts yet, OR explicit 'REVISION'
    # BUT NOT for LEGAL_SIMPLE (they already have enough info)
    if (intent == "REVISION" or investigator_status != "DONE") and intent != "LEGAL_SIMPLE":
        logger.info("🕵️ Mode: INVESTIGATOR (Fact Extraction)")
        
        # 1. Analyze Facts (Checklist Logic)
        # Use LLM to extract facts from History + Input
        llm = get_llm(temperature=0.1, json_mode=True)
        
        extraction_prompt = f"""
        You are the **Investigator (Fact Keeper)**.
        User Input: {user_input}
        History: {state.get('chat_history', [])[-3:]}
        
        Task: Extract structured facts. Identify missing critical info.
        Output JSON:
        {{
            "status": "COMPLETE" | "INCOMPLETE",
            "missing_info": ["list", "of", "missing"],
            "next_question": "Question to user if incomplete",
            "structured_facts": {{ "key": "value" }}
        }}
        """
        
        response = await llm.ainvoke([SystemMessage(content=extraction_prompt)])
        try:
            result = json.loads(response.content)
        except:
            # Fallback
            result = {"status": "INCOMPLETE", "next_question": "Could you provide more details?", "structured_facts": {}}
            
        # 2. Action
        if result.get("status") == "COMPLETE":
            # Write to Blackboard
            blackboard.update_segment(
                session_id, 
                "facts_snapshot", 
                result["structured_facts"],
                status_update={"investigator": "DONE"}
            )
            return {
                "next_agent": "deep_research", # Go to Researcher (Self-Loop but will switch mode next time)
                "conversation_stage": "INVESTIGATION_COMPLETE"
            }
        else:
            # Ask Question (Route to User)
            return {
                "next_agent": "user",
                "final_response": result.get("next_question"),
                "conversation_stage": "GATHERING_FACTS"
            }
    
    # ✅ FIX: For LEGAL_SIMPLE, mark investigator as DONE immediately
    if intent == "LEGAL_SIMPLE" and investigator_status != "DONE":
        logger.info("⚡ Simple Query - skipping Investigator, going straight to Research")
        
        # Build consolidated facts from chat history
        chat_history = state.get('chat_history', [])
        original_question = user_input
        
        # Try to extract original question from history
        for msg in chat_history:
            if isinstance(msg, dict) and msg.get('role') == 'user':
                original_question = msg.get('content', '')
                break
        
        # Merge current input with original if different
        full_context = original_question
        if user_input != original_question and user_input.strip():
            full_context = f"{original_question} ({user_input})"
        
        structured_facts = {
            "query": full_context,
            "original": original_question,
            "clarification": user_input if user_input != original_question else None
        }
        
        # Write to Blackboard and mark done
        blackboard.update_segment(
            session_id, 
            "facts_snapshot", 
            structured_facts,
            status_update={"investigator": "DONE"}
        )
        logger.info(f"✅ Facts saved: {structured_facts}")


    # --- MODE 2: RESEARCHER (The Librarian) ---
    # Trigger: Investigator is DONE (or skipped for Simple Queries)
    logger.info("📚 Mode: RESEARCHER (RAG)")
    
    # Read Facts
    facts = current_board.get("facts_snapshot") or {"raw": user_input}
    
    # 1. Plan Queries (Keyword Extraction)
    # Re-using strict search logic...
    # [Code simplified for brevity, using existing logic]
    # ...
    
    # EXECUTE SEARCH (Mocking the call to existing tools for now, leveraging existing code structure)
    # In real implementation, we invoke hybrid_search.run()
    
    # 2. Fail Fast Logic
    # Imagine we got 'results' list
    # results = [] # ... perform search ...
    
    # Existing Deep Research Logic Reuse:
    # We will call the internal logic of previous `deep_research_node` but tailored.
    
    # For MVP Integration, let's keep the existing `deep_research_node` body 
    # but wrap it with the Blackboard state check.
    
    # ... [Execute Search Logic] ...
    # (Assuming we run search here)
    
    # Placeholder for actual search execution (copying essential parts from old node)
    search_res = await _execute_search_logic(state, facts, user_input)
    results = search_res.get("research_results", [])
    
    if not results:
        logger.warning("⚠️ Researcher found NOTHING. Reverting to Investigator.")
        # Trigger Revisit
        blackboard.update_status(session_id, "investigator", "PENDING") # Reset
        return {
            "next_agent": "user",
            "final_response": "عذراً، لم أجد معلومات كافية بناءً على الوقائع الحالية. هل يمكنك تزويدي بتفاصيل أكثر حول...؟",
            "revisit_flag": True
        }
        
    # 3. Success -> Write to Blackboard
    
    # Write Thinking Trace (V3 Strategy)
    research_metadata = search_res.get("research_metadata", {})
    if research_metadata.get("v3_metadata"):
        blackboard.update_segment(
            session_id,
            "agent_thinking",
            {
                "researcher": {
                    "strategy": research_metadata["v3_metadata"].get("smart_scout", {}).get("search_strategy"),
                    "context_quality": research_metadata["v3_metadata"].get("quick_scout", {}).get("context_quality"),
                    "citations_found": len(research_metadata.get("citations_map", {})),
                    "timestamp": datetime.now().isoformat()
                }
            }
        )

    blackboard.update_segment(
        session_id,
        "research_data",
        {"results": results, "metadata": research_metadata},
        status_update={"researcher": "DONE"}
    )
    
    # --- CIRCUIT BREAKER: Direct Reply for Simple Queries ---
    if intent == "LEGAL_SIMPLE":
        logger.info("⚡ Simple Query Detected: Synthesizing Answer directly.")
        
        summary_llm = get_llm(temperature=0.2)
        summary_prompt = f"""
        You are the Legal Researcher.
        User Query: {user_input}
        
        Found Information:
        {str(results)[:2500]}
        
        Task: You are a Direct Legal Assistant.
        1. Answer the user's question IMMEDIATELY based on the found info.
        2. Use Standard Legal Arabic (Fosha) ONLY. Do NOT ask about dialects.
        3. Do NOT ask "Do you want me to explain?". Just explain. 
        4. Cite the article numbers if available.
        
        Refusal to Answer Policy:
        - If the search results are empty, apologize.
        - If the search results are present, YOU MUST ANSWER.
        """
        
        answer = await summary_llm.ainvoke([SystemMessage(content=summary_prompt)])
        
        return {
            "next_agent": "end", # Signal to Graph
            "conversation_stage": "COMPLETED",
            "final_response": answer.content
        }

    return {
        "next_agent": "council",
        "conversation_stage": "RESEARCH_COMPLETE"
    }

# --- Helpers ---

async def _resolve_country_id(country_name: str) -> str:
    """Helper to resolve country name to ID and check if laws exist."""
    if not country_name:
        return None
    try:
        # Simple lookup
        res = db.client.from_("countries").select("id, name_ar, name_en").or_(f"name_en.ilike.%{country_name}%,name_ar.ilike.%{country_name}%").limit(1).execute()
        
        if res.data:
            country_id = res.data[0]["id"]
            country_name_ar = res.data[0]["name_ar"]
            
            # Check availability (Do we have chunks?)
            data_check = db.client.from_("document_chunks").select("id", count="exact").eq("country_id", country_id).limit(1).execute()
            
            if data_check.count == 0:
                logger.warning(f"Country {country_name} found but has 0 documents.")
                # Don't raise, just return None to fallback
                return None
                
            return country_id
            
    except Exception as e:
        logger.warning(f"Country resolution failed: {e}")
        
    return None

from ...prompts.research_prompts import DEEP_RESEARCH_PROMPT

async def _execute_search_logic(state, facts, query) -> Dict[str, Any]:
    """
    Executes the actual Research Logic (Plan -> Search -> Expand).
    Restored from original deep_research_node.
    """
    user_context = state.get("context", {}).get("user_context", {})
    user_country_id = user_context.get("country_id") 
    
    # 1. Plan Queries
    llm = get_llm(temperature=0.3, json_mode=False)
    
    # Format inputs
    facts_list = facts.get("structured_facts", {}) if isinstance(facts, dict) else {}
    facts_text = json.dumps(facts_list, ensure_ascii=False)
    
    # Get lawyer context from state
    from datetime import datetime
    user_context = state.get("context", {}).get("user_context", {})
    lawyer_name = user_context.get("full_name", "المحامي")
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = DEEP_RESEARCH_PROMPT.format(
        lawyer_name=lawyer_name,
        current_date=current_date,
        case_summary=query,
        facts=facts_text,
        missing="None",
        user_country_id=user_country_id
    )
    
    queries = []
    jurisdiction_name = None
    final_country_id = None
    
    try:
        response = await llm.ainvoke([SystemMessage(content=prompt)])
        content = response.content.strip()
        
        # Robust JSON Extraction
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx+1]
            try:
                plan = json.loads(json_str)
            except:
                plan = {}
        else:
            plan = {}
            
        queries = plan.get("queries", [query]) # Fallback to query
        jurisdiction_name = plan.get("explicit_country")
        
        # Country Logic
        if jurisdiction_name and str(jurisdiction_name).lower() not in ["null", "none", "", "implied"]:
            final_country_id = await _resolve_country_id(jurisdiction_name)
            
        if not final_country_id:
            final_country_id = user_country_id

    except Exception as e:
        logger.error(f"Research Planning Failed: {e}")
        queries = [query]
        final_country_id = user_country_id

    
    # 2. Execute V3 Scout (The new Smart Search)
    # V3 handles keyword expansion and multi-phase search internally.
    try:
        # We use the ORIGINAL user query for V3, as it has its own extraction logic.
        # But we pass the resolved country_id.
        search_result = await hybrid_search.run(
            query=query, 
            limit=15, 
            country_id=final_country_id
        )
        
        flat_results = search_result.data if search_result.success else []
        v3_metadata = search_result.metadata or {}
        
        # Extract Citations Map
        smart_scout_meta = v3_metadata.get("smart_scout", {})
        citations_map = smart_scout_meta.get("citations_map", {})
        
        # Log V3 Strategy
        strategy_used = smart_scout_meta.get("search_strategy", "unknown")
        logger.info(f"🧠 V3 Strategy: {strategy_used} | Citations Found: {len(citations_map)}")

    except Exception as e:
        logger.error(f"V3 Search Failed: {e}")
        flat_results = []
        citations_map = {}
        strategy_used = "error_fallback"

    # 3. Expand Context (Siblings) - Keep this enrichment
    seen_ids = set(r.get("id") for r in flat_results)
    
    for item in flat_results[:5]: # Top 5 only
        item_id = item.get("id")
        meta = item.get("metadata", {}) or {}
        if meta.get("sequence_number") is not None and item_id:
             sib_res = doc_tool.run(chunk_id=item_id, include_siblings=True, sibling_limit=2)
             if sib_res.success:
                 siblings = sib_res.data.get("siblings", [])
                 if siblings:
                     siblings.sort(key=lambda x: x.get("sequence_number", 0))
                     full_text = "\n".join([s.get("content", "") for s in siblings])
                     item["content"] = f"__EXPANDED_CONTEXT__:\n{full_text}"
                     item["metadata"]["expanded"] = True

    # 4. Legal Principles (Flexible Search) - Keep this enrichment
    # We use the generated queries from step 1 for this, as they might catch principles
    async def run_principle_search(q):
        res = principle_search.run(query=q, tables=["thought_templates"], limit=2, method="any")
        return res.data if res.success else []

    p_tasks = [run_principle_search(q) for q in queries[:2]]
    p_results_list = await asyncio.gather(*p_tasks)
    
    for sublist in p_results_list:
        for item in sublist:
            if isinstance(item, dict):
                 item["metadata"]["type"] = "principle"
                 item["content"] = f"__LEGAL_PRINCIPLE__:\n{item['content']}"
                 identifier = item["content"][:50]
                 if identifier not in seen_ids:
                     flat_results.append(item)
                     seen_ids.add(identifier)

    # 5. Format Output for Blackboard
    return {
        "research_results": flat_results,
        "research_metadata": {
            "source": "HybridSearchV3",
            "country_id": final_country_id,
            "citations_map": citations_map,
            "queries_used": queries,
            "v3_metadata": v3_metadata if 'v3_metadata' in locals() else {}
        }
    }

