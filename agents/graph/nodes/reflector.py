from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
import json
import logging
from ..state import AgentState
from agents.core.llm_factory import get_llm
from ...tools.lookup_tools import LookupPrincipleTool

logger = logging.getLogger(__name__)

# Initialize Tool
lookup_tool = LookupPrincipleTool()

REFLECT_PROMPT = """
أنت **المراجع النقدي (Critical Reflector)** للنظام.
مهمتك: مراجعة خطة العمل المقترحة من "القاضي" قبل تنفيذها، لأنها مصنفة على أنها **عالية التعقيد/الخطورة**.

**الخطة الحالية:**
النية: {intent}
الوكيل المنفذ: {next_agent}
تفاصيل الخطة: {plan}

**تحليل المخاطر:**
1. هل هذه الخطة قانونية وآمنة؟
2. هل المعلومات كافية للتنفيذ؟
3. هل هناك احتمال للخطأ (Hallucination)؟

**المطلوب:**
- إذا كانت الخطة سليمة: أعدها كما هي مع "status": "approved".
- إذا كانت ناقصة أو خطيرة: 
  - يمكنك طلب بحث إضافي (عن طريق اقتراح تعديل الخطة).
  - أو قم بتحسين الصياغة.
  - أرجع "status": "revised" والخطة المعدلة.

**المخرجات (JSON):**
{{
  "status": "approved" | "revised",
  "revised_plan": "نص الخطة (نفس القديم أو المعدل)",
  "reasoning": "لماذا قمت بالتعديل أو الموافقة؟"
}}
"""

async def reflect_node(state: AgentState) -> Dict[str, Any]:
    """
    🤔 Thinking Tunnel (Reflector Node).
    Intercepts High/Critical tasks for review.
    """
    logger.info("🤔 Entering Thinking Tunnel (Reflection Phase)...")
    
    intent = state.get("intent")
    next_agent = state.get("next_agent")
    plan = state.get("plan") or state.get("reasoning") # Fallback to reasoning if plan field empty
    
    llm = get_llm(temperature=0.1, json_mode=True)
    
    # Optional: Bind tools if we want the reflector to *actively* check things.
    # The requirement says: "If yes [error likely]: asks for search..."
    # We can bind lookup_principle to let it verify automatically.
    llm_with_tools = llm.bind_tools([lookup_tool.to_langchain_tool()])
    
    prompt = REFLECT_PROMPT.format(
        intent=intent,
        next_agent=next_agent,
        plan=str(plan)
    )
    
    try:
        response = await llm_with_tools.ainvoke([SystemMessage(content=prompt)])
        
        # Handle Tool Calls (Active Reflection)
        if response.tool_calls:
            logger.info(f"🤔 Reflector decided to use tool: {response.tool_calls[0]['name']}")
            # In a real loop, we'd execute and recurse. 
            # For this V2 implementation, we treat a tool call as a "Revised Plan" to Consult.
            # But wait, if it's Admin Action, we can't switch to 'council' easily without changing next_agent.
            # Let's keep it simple: Use reasoning to decide.
            
            # If tool call, it means we need info. 
            # Let's Assume the Reflector is smart enough to just *improve the plan* telling the Admin to "Check X first".
            pass

        content = json.loads(response.content)
        
        status = content.get("status")
        revised_plan = content.get("revised_plan")
        reasoning = content.get("reasoning")
        
        logger.info(f"🤔 Reflection Result: {status}. Reasoning: {reasoning}")
        
        if status == "revised":
             # Update the reasoning/plan descriptions in state
             # We might need to map this back to where 'plan' is stored.
             # In Judge, plan is in 'reasoning' string or 'plan' field?
             # State has 'plan' field (Any).
             return {
                 "plan": revised_plan,
                 "judge_directives": [f"Reflector Note: {reasoning}"], # Pass note to next agent
                 "reasoning": f"{state.get('reasoning')} | Reflected: {reasoning}"
             }
        
        # If approved, pass through
        return {"reasoning": f"{state.get('reasoning')} | Verified Safe"}
        
    except Exception as e:
        logger.error(f"Reflection Failed: {e}")
        return {} # No change

