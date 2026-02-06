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

# ✅ Phase 1: Context Enrichment Integration
from agents.core.conversation_state_manager import ConversationStateManager, ConversationContext
from agents.core.context_enrichment import ContextEnrichmentLayer, enrich_query_with_context

# ✅ Phase 2: Performance Optimizations
from agents.core.timeout_strategy import AdaptiveTimeoutStrategy, QueryComplexity, get_timeout
from agents.core.search_cache import get_search_cache, SearchCache
from agents.core.query_rewriter import QueryRewriter, expand_query

logger = logging.getLogger(__name__)

# Initialize tools
hybrid_search = HybridSearchTool()
blackboard = LegalBlackboardTool()
doc_tool = GetRelatedDocumentTool()
principle_search = FlexibleSearchTool()

# ✅ Phase 1: Initialize context managers
context_state_manager = ConversationStateManager(max_history_messages=5)
context_enrichment_layer = ContextEnrichmentLayer()

# ✅ Phase 2: Initialize performance optimization tools
timeout_strategy = AdaptiveTimeoutStrategy()
search_cache = get_search_cache()
query_rewriter = QueryRewriter(max_variants=3)

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
        
        # ✅ FIX: HCF PROTOCOL (Honor Constraint Framework)
        # Replaces simple summary with 3-Phase Verification Loop
        
        # 1. Prepare Context (Full Chapter)
        full_context_str = str(results) # Current Context Window is large enough (128k+)
        
        # 2. Prepare Prompt
        # We use temperature=0.3 to allow "Divergent Generation" (Phase 1)
        # followed by strict "Verification" (Phase 2)
        hcf_llm = get_llm(temperature=0.3)
        
        hcf_formatted_prompt = HCF_RESEARCH_PROMPT.format(
            user_query=user_input,
            found_context=full_context_str
        )
        
        # 3. Execute with Circuit Breaker (Fallback Strategy)
        final_answer = ""
        
        try:
            logger.info("🛡️ Invoking HCF: 3-Phase Verification Protocol...")
            response = await hcf_llm.ainvoke([SystemMessage(content=hcf_formatted_prompt)])
            content = response.content
            
            # Robust Parsing: Look for JSON block (Flexible: with or without 'json' label)
            import re
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                
                # Check Verification Status
                status = data.get("verification_status", "UNKNOWN")
                selected_path = data.get("selected_path", "UNKNOWN")
                final_answer = data.get("final_answer_ar", "")
                
                logger.info(f"✅ HCF Success: Path={selected_path} | Status={status}")
                
            else:
                raise ValueError("No JSON block found in HCF response")

        except Exception as e:
            logger.warning(f"⚠️ HCF Failed (Circuit Breaker Triggered): {e}")
            logger.info("🔄 Fallback: Reverting to Legacy Direct Answer Prompt")
            
            # Fallback to Legacy Prompt (to ensure user gets an answer)
            fallback_llm = get_llm(temperature=0.2)
            fallback_prompt = f"""
            SYSTEM FAILURE RECOVERY MODE.
            User Query: {user_input}
            Context: {full_context_str[:15000]}
            
            Task: Provide a direct, professional legal answer in Arabic.
            Cite sources if visible. If not, state that no direct text was found.
            """
            fallback_res = await fallback_llm.ainvoke([SystemMessage(content=fallback_prompt)])
            final_answer = fallback_res.content
        
        return {
            "next_agent": "end", # Signal to Graph
            "conversation_stage": "COMPLETED",
            "final_response": final_answer,
            "hcf_details": {
                "selected_path": selected_path if 'selected_path' in locals() else "FALLBACK",
                "verification_status": status if 'status' in locals() else "UNVERIFIED",
                "confidence_score": data.get("confidence_score") if 'data' in locals() else 0.0
            }
        }
        
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

from ...prompts.research_prompts import DEEP_RESEARCH_PROMPT, HCF_RESEARCH_PROMPT

async def _execute_search_logic(state, facts, query) -> Dict[str, Any]:
    """
    Executes the actual Research Logic (Plan -> Search -> Expand).
    
    ✅ ENHANCED: Now uses Context Enrichment to prevent context loss.
    The "في أي نظام" problem is solved by enriching ambiguous queries
    with entities from chat history before search.
    """
    user_context = state.get("context", {}).get("user_context", {})
    user_country_id = user_context.get("country_id")
    chat_history = state.get("chat_history", [])
    
    # =========================================================================
    # ✅ CONTEXT ENRICHMENT (NEW - Solves "في أي نظام" problem)
    # =========================================================================
    original_query = query
    enriched_query_obj = None
    
    try:
        # Extract conversation context from history
        conversation_context = context_state_manager.extract_context_from_history(
            chat_history=chat_history,
            current_query=query
        )
        
        # Check if query is ambiguous and needs enrichment
        if context_enrichment_layer.is_ambiguous(query):
            logger.info(f"🔍 Ambiguous query detected: '{query}'")
            
            enriched_query_obj = context_enrichment_layer.resolve_with_context(
                query=query,
                context=conversation_context
            )
            
            if enriched_query_obj.enriched != query:
                query = enriched_query_obj.enriched
                logger.info(f"✨ Query enriched: '{original_query}' → '{query}'")
                logger.info(f"   Entities used: {enriched_query_obj.entities_used}")
                logger.info(f"   Confidence: {enriched_query_obj.confidence:.2f}")
            
            # If requires clarification and low confidence, could trigger user question
            if enriched_query_obj.requires_clarification and enriched_query_obj.confidence < 0.4:
                logger.warning(f"⚠️ Low confidence enrichment - may need user clarification")
        
        # Save context to blackboard for persistence
        session_id = state.get("session_id") or "unknown_session"
        if not conversation_context.is_empty():
            context_state_manager.save_context_to_blackboard(
                context=conversation_context,
                session_id=session_id,
                blackboard=blackboard
            )
    
    except Exception as e:
        logger.error(f"Context enrichment failed: {e}", exc_info=True)
        # Fallback: use original query
        query = original_query
    
    # =========================================================================
    # 1. Plan Queries (Keyword Extraction)
    # =========================================================================
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

    # 3. Expand Context (Rich Reading)
    # ✅ FIX: Automatically fetch Preceding (N-1) and Succeeding (N+1) articles
    # This solves the user complaint about "partial info" by reading the full neighborhood.
    from ...tools.read_tool import ReadDocumentTool
    read_tool = ReadDocumentTool()
    
    seen_ids = set(r.get("id") for r in flat_results)
    
    # Only expand the TOP 3 most relevant results to save tokens/time
    for item in flat_results[:3]: 
        item_id = item.get("id")
        meta = item.get("metadata", {}) or {}
        
        # Check if it has sequence_number (i.e., it's a Book/Page)
        if meta.get("sequence_number") is not None and item_id:
             # Use the new 'expand_context' feature
             read_res = read_tool.run(
                 doc_id=item_id, 
                 expand_context=True
             )
             
             if read_res.success:
                 expanded_content = read_res.data.get("content", "")
                 if expanded_content:
                     # Replace the short snippet with the Full Expanded Neighborhood
                     item["content"] = expanded_content
                     item["metadata"]["expanded"] = True
                     item["metadata"]["context_type"] = "neighborhood_n1_p1"
                     logger.info(f"📖 Auto-Expanded Doc {item_id}: Loaded Neighborhood (Prev/Next)")

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

