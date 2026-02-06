import re
import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from agents.core.llm_factory import get_llm
from ..state import AgentState

# Configure logging
logger = logging.getLogger(__name__)

# Zero-Token Patterns for Greetings (Keep checks fast)
GREETING_PATTERNS = [
    r"^(hi|hello|hey|hola|marhaba|مرحبا|هلا|سلام|السلام عليكم|يا هلا|peace|greetings)$",
    r"^(good morning|good evening|good afternoon|sabah|masaa|صباح الخير|مساء الخير)$",
    r"^(thank you|thanks|shukran|شكرا|يعطيك العافية|جزاك الله خير)$"
]

GATEKEEPER_SYSTEM_PROMPT = """
You are the Gatekeeper of a specialized Law Firm AI.
Your ONLY job is to classify the User's Intent into one of these 5 categories.

Categories:
1. ADMIN_ACTION: User wants to CHANGE data (Database Write).
   - Keywords (Any Language/Dialect): Delete, Remove, Add, Create, Update, Cancel, Stop, Suspend.
   - Dialects (Egyptian/Gulf/etc): "طير الاسم", "شيله", "مش عايزه", "كنسل", "امسحه", "خلّص عليه".
   - Context: Any request to modify clients, cases, tasks, or sessions.

2. ADMIN_QUERY: User wants to READ data (Database Read).
   - Keywords: Count, List, Show, Statistics, Status, Who is, When is.
   - Examples: "كم موكل عندي؟", "وريني الجلسات", "إحصائيات".

3. LEGAL_QUERY: User asks for Legal Advice, Analysis, or Information.
   - Keywords: Law, Article, Rights, Punishment, Valid, Invalid, Opinion.
   - Examples: "ما عقوبة السرقة؟", "شرح المادة 77", "رأيك في القضية".

4. GREETING: Conversational fillers.
   - Examples: "كيف حالك", "من أنت".

5. COMPLEX: Ambiguous, Mixed, or Unclear.

Rules:
- Output ONLY the Category Name (e.g., "ADMIN_ACTION").
- Do NOT output reasoning or JSON.
- If unsure between Admin Action and Query, prefer ACTION (Safety checks handle it later).
"""

async def _classify_with_llm(user_input: str) -> str:
    """Use Fast LLM to classify intent."""
    try:
        # Use temperature=0 for consistent classification
        llm = get_llm(temperature=0.0, json_mode=False)
        
        messages = [
            SystemMessage(content=GATEKEEPER_SYSTEM_PROMPT),
            HumanMessage(content=user_input)
        ]
        
        # Tags for observability
        response = await llm.ainvoke(messages, config={"tags": ["gatekeeper_classification"]})
        intent = response.content.strip().upper()
        
        # Validation
        valid_intents = ["ADMIN_ACTION", "ADMIN_QUERY", "LEGAL_QUERY", "GREETING", "COMPLEX"]
        if intent not in valid_intents:
            # Fallback for weird LLM outputs
            if "ADMIN" in intent: return "ADMIN_QUERY"
            if "LEGAL" in intent: return "LEGAL_QUERY"
            return "COMPLEX"
            
        return intent
        
    except Exception as e:
        logger.error(f"Gatekeeper LLM Error: {e}")
        return "COMPLEX" # Fail safe to Judge

async def gatekeeper_node(state: AgentState) -> Dict[str, Any]:
    """
    The Semantic Gatekeeper.
    Uses LLM to understand context and dialects.
    """
    user_input = state.get("input", "").strip()
    logger.info(f"🚪 Gatekeeper checking input: '{user_input}'")

    # 1. Deterministic Regex Check (Speed Optimization for common greetings)
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, user_input, re.IGNORECASE):
            logger.info("⚡ Gatekeeper: GREETING detected (Regex) -> Fast Track")
            return {"intent": "GREETING", "next_agent": "fast_track"}

    # 2. Semantic Analysis (The Red Pill Solution)
    # No more rigid regex lists. We ask the brain.
    intent = await _classify_with_llm(user_input)
    logger.info(f"🧠 Gatekeeper Semantic Classification: {intent}")

    # 3. Routing Logic
    if intent == "ADMIN_ACTION":
        # Direct route to Admin Ops (The "Adaptive Admin Agent" will handle extraction)
        return {
            "intent": "ADMIN_ACTION",
            "next_agent": "admin_ops", 
            "summary": "Gatekeeper detected Admin Action (Semantic)"
        }
        
    elif intent == "ADMIN_QUERY":
        # Direct route to Admin Ops
        return {
            "intent": "ADMIN_QUERY", 
            "next_agent": "admin_ops",
            "summary": "Gatekeeper detected Admin Query (Semantic)"
        }
        
    elif intent == "LEGAL_QUERY":
        # Route to Judge
        return {
            "intent": "LEGAL_TASK",
            "next_agent": "judge"
        }
        
    elif intent == "GREETING":
         return {"intent": "GREETING", "next_agent": "fast_track"}

    # Default / Complex
    return {
        "intent": "COMPLEX", 
        "next_agent": "judge"
    }

def fast_track_node(state: AgentState) -> Dict[str, Any]:
    """
    The Fast Responder. Handles simple queries directly.
    """
    logger.info("🚀 Fast Track executing...")
    
    user_context = state.get("context", {}).get("user_context", {})
    lawyer_name = user_context.get("full_name", "المحامي")
    user_input = state.get("input", "").lower()
    
    # Simple Template Responses
    response = f"مرحباً أستاذ {lawyer_name}! أنا مارد، مساعدك القانوني الذكي. كيف يمكنني مساعدتك اليوم؟"
    
    if "morning" in user_input or "صباح" in user_input:
        response = f"صباح النور يا أستاذ {lawyer_name}! تفضل، أنا في الخدمة."
    elif "evening" in user_input or "مساء" in user_input:
        response = f"مساء الخير أستاذ {lawyer_name}! كيف أخدمك الليلة؟"
    elif "thank" in user_input or "شكرا" in user_input or "عافية" in user_input:
        response = f"العفو يا أستاذ {lawyer_name}! واجبي. هل لديك أي استفسار آخر؟"
        
    logger.info(f"🚀 Fast Track Response: {response}")
    
    return {
        "final_response": response,
        "conversation_stage": "CHAT"
    }
