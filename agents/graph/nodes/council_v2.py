"""
🎯 Council Node V2 - Single LLM with Chain-of-Thought

المزايا:
✅ أبسط من Multi-Agent
✅ أسرع (1 LLM call بدلاً من 5)
✅ أرخص
✅ Structured thinking مع CoT
✅ بدون ترقيع - حل جذري
"""

from typing import Dict, Any
import json
import uuid
import logging
import asyncio  # ✅ PHASE 1: For timeout protection
from langchain_core.messages import SystemMessage

from ..state import AgentState
from ...prompts.council_v2_prompts import COUNCIL_V2_COT_PROMPT
from agents.core.llm_factory import get_llm
from ...tools.legal_blackboard_tool import LegalBlackboardTool

logger = logging.getLogger(__name__)
blackboard = LegalBlackboardTool()


async def council_v2_node(state: AgentState) -> Dict[str, Any]:
    """
    🎯 Council V2: Single LLM with Professional CoT
    
    Architecture:
    - بدلاً من 5 agents متوازية
    - LLM واحد قوي مع منهجية منظمة
    - 3 زوايا تحليل: Legal Scholar + Strategic Planner + Critical Skeptic
    - Synthesis نهائي واضح
    """
    logger.info("=" * 100)
    logger.info("🎯 COUNCIL V2: Professional Legal Analysis Engine")
    logger.info("=" * 100)
    
    # 1. Session Management
    session_id = state.get("session_id") or str(uuid.uuid4())
    if not state.get("session_id"):
        state["session_id"] = session_id
    
    # 2. Load Context from Blackboard
    current_board = blackboard.read_latest_state(session_id)
    if not current_board:
        current_board = blackboard.initialize_state(session_id)
    
    status = current_board.get("workflow_status", {})
    council_status = status.get("council", "PENDING")
    
    # 3. Check if already done
    if council_status == "DONE":
        logger.info("✅ Council already completed - skipping")
        return {
            "next_agent": "drafter",
            "conversation_stage": "STRATEGY_COMPLETE"
        }
    
    # 4. Prepare Input Context
    facts = current_board.get("facts_snapshot", {})
    research = current_board.get("research_data", {})
    
    # Fallback: use user input if facts empty
    if not facts:
        original_request = state.get("input", "")
        facts = {"user_request": original_request}
    
    # Format research results
    research_text = _format_research(research)
    facts_text = json.dumps(facts, ensure_ascii=False, indent=2)
    
    logger.info(f"📊 Context prepared:")
    logger.info(f"  • Facts: {len(facts_text)} chars")
    logger.info(f"  • Research: {len(research_text)} chars")
    
    # 5. Execute CoT Analysis
    logger.info("🧠 Invoking Council V2 with Chain-of-Thought...")
    
    llm = get_llm(temperature=0.3, json_mode=True)
    
    # Prepare lawyer context
    user_context = state.get("context", {}).get("user_context", {})
    lawyer_name = user_context.get("full_name", "المحامي")
    user_country_id = user_context.get("country_id", "غير محدد")

    prompt = COUNCIL_V2_COT_PROMPT.format(
        lawyer_name=lawyer_name,
        user_country_id=user_country_id,
        facts=facts_text,
        research=research_text
    )
    
    # ✅ PHASE 1 FIX: Timeout Protection
    COUNCIL_TIMEOUT = 45  # seconds (was 30s - increased by 50%)
    
    try:
        response = await asyncio.wait_for(
            llm.ainvoke([SystemMessage(content=prompt)]),
            timeout=COUNCIL_TIMEOUT
        )
        
        # Parse strategy
        # ✅ FIX: Robust JSON Extraction (Regex)
        import re
        content = response.content
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        
        if json_match:
             json_str = json_match.group(1)
             strategy = json.loads(json_str)
        else:
             # Try direct parse if no blocks
             strategy = json.loads(content)
        
        logger.info("✅ Council V2 Analysis Complete")
        logger.info(f"  • Understanding: {len(strategy.get('understanding', {}))} points")
        logger.info(f"  • Perspectives: {len(strategy.get('perspectives', {}))} views")
        logger.info(f"  • Strategy: {strategy.get('synthesis', {}).get('recommended_strategy', {}).get('approach', 'N/A')[:100]}...")
        
    except asyncio.TimeoutError:
        logger.error(f"⏱️ Council V2 timeout after {COUNCIL_TIMEOUT}s")
        logger.warning("🔄 Falling back to emergency strategy")
        
        # Emergency fallback strategy
        strategy = {
            "synthesis": {
                "recommended_strategy": {
                    "approach": f"تم تجاوز الوقت المحدد ({COUNCIL_TIMEOUT}s). يرجى المحاولة مرة أخرى أو تبسيط الاستعلام.",
                    "key_actions": ["إعادة المحاولة", "تبسيط الاستعلام"],
                    "legal_basis": [],
                    "risk_mitigation": [],
                    "timeline": "",
                    "success_criteria": []
                }
            },
            "timeout_error": True
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parsing failed: {e}")
        logger.warning("🔄 Falling back to text-based strategy")
        
        # Fallback: treat response as text
        strategy = {
            "synthesis": {
                "recommended_strategy": {
                    "approach": response.content,
                    "key_actions": [],
                    "legal_basis": [],
                    "risk_mitigation": [],
                    "timeline": "غير محدد",
                    "success_criteria": []
                }
            },
            "fallback_reason": "JSON parsing failed"
        }
    
    except Exception as e:
        logger.error(f"❌ Council V2 failed: {e}", exc_info=True)
        
        # Emergency fallback
        strategy = {
            "synthesis": {
                "recommended_strategy": {
                    "approach": "فشل التحليل - يرجى المراجعة اليدوية",
                    "key_actions": [],
                    "legal_basis": [],
                    "risk_mitigation": [],
                    "timeline": "",
                    "success_criteria": []
                }
            },
            "error": str(e)
        }
    
    # 6. Save to Blackboard
    blackboard.update_segment(
        session_id,
        "debate_strategy",
        strategy,
        status_update={"council": "DONE"}
    )
    
    logger.info("💾 Strategy saved to Blackboard")
    logger.info("🔄 Routing to Drafter...")
    
    # 7. Route to Drafter
    return {
        "next_agent": "drafter",
        "conversation_stage": "STRATEGY_COMPLETE"
    }


def _format_research(research: Dict) -> str:
    """تنسيق نتائج البحث بشكل قابل للقراءة"""
    
    if not research or not research.get("results"):
        return "لا تتوفر نتائج بحث قانوني."
    
    formatted = []
    
    for i, result in enumerate(research.get("results", [])[:5], 1):
        content = result.get("content", "")[:500]
        source_info = result.get("hierarchy_path", "مصدر غير محدد")
        
        formatted.append(f"""
### [{i}] {source_info}

{content}...

---
""")
    
    return "\n".join(formatted)


# ==================== EXPORT ====================

__all__ = ["council_v2_node"]
