from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from ..state import AgentState
from ...config.settings import settings
from ...config.settings import settings
from agents.skills.registry import SkillRegistry
from ...prompts.admin_prompts import ADMIN_PLANNER_PROMPT, ADMIN_SYNTHESIZE_PROMPT
from ..nodes.admin_schemas import AdminPlan
from agents.core.llm_factory import get_llm
from langchain_core.output_parsers import PydanticOutputParser
import json
import re
import logging

import logging
from agents.utils.sanitizer import Sanitizer
from agents.utils.resiliency import ResiliencyManager, FailoverError

logger = logging.getLogger(__name__)

# --- 1. Admin Graph State ---
class AdminState(AgentState):
    """Extended state for Admin Operations."""
    entities: Dict[str, Any]      # Extracted entities (Client Name, Dates)
    lookup_results: List[str]     # Results from context lookups
    execution_plan: str           # The approved plan
    tool_calls: List[Dict]        # Pending tools to run
    tool_results: List[Dict]      # ✅ Results from tool execution
    tool_results: List[Dict]      # ✅ Results from tool execution
    execution_summary: Dict[str, Any]  # ✅ Summary of execution (success/fail counts)
    loop_count: int               # ✅ Safety guardrail for Agentic Loop
    
# --- 2. Nodes ---


from ...tools.semantic_tools import LegalEntityExtractorTool

async def action_node(state: AdminState) -> Dict[str, Any]:
    """
    Step 1: Action Planning (Fused Node).
    Replaces Extract -> Lookup -> Plan chain.
    Directly converts User Input -> Tool Calls.
    Now with Semantic Hygiene! 🧼
    """
    print("--- ADMIN: ACTION NODE (Fused + Semantic Hygiene) ---")
    import json
    import re
    
    lawyer_id = state.get("lawyer_id")
    user_id = state.get("user_id")
    user_input = state['input']
    
    # 🧼 Semantic Hygiene Step
    # Before we ask the Planner, let's extract clean entities
    entity_extractor = LegalEntityExtractorTool()
    extraction_result = entity_extractor.run(user_input)
    
    extracted_entities_str = ""
    if extraction_result.success:
         data = extraction_result.data
         # Format friendly string for LLM
         parts = []
         if data.get("persons"):
             parts.append(f"Persons: {[p['guess'] for p in data['persons'] if 'guess' in p]}")
         if data.get("courts"):
             parts.append(f"Courts: {[c['type'] for c in data['courts']]}")
         if data.get("laws"):
             parts.append(f"Laws: {data['laws']}")
         
         if parts:
             extracted_entities_str = "\n".join(parts)
             logger.info(f"🧼 Semantic Hygiene: Found {extracted_entities_str}")

    # 1. Initialize Skills (Skill-Based Architecture)
    registry = SkillRegistry(lawyer_id=lawyer_id, current_user={"id": user_id, "role": "admin"})
    
    # Get Tool Definitions (Progressive: Show Definitions, allow all tools implicitly for now)
    # Ideally we'd ask it to PICK a skill, but to keep it simple v1, we expose all tools descriptions
    # BUT grouped by skill to be cleaner.
    
    # Actually, let's just get all tools for now, but formatted better.
    tools_map = registry.get_all_tools()
    
    # Create Tool Definitions for Prompt
    tools_desc = []
    # Optimization: Use Skill Definitions instead of raw tools list if list is too long?
    # For now, let's keep full list but sorted.
    for name, func in tools_map.items():
        doc = func.__doc__ or "No description"
        tools_desc.append(f"- {name}: {doc.strip()}")
    tools_str = "\n".join(tools_desc)
    
    llm = get_llm(temperature=0, streaming=False)
    
    
    # Context
    ctx = state.get("context", {}).get("user_context", {})
    lawyer_name = ctx.get("full_name") or "Lawyer"
    user_role = ctx.get("role_name_ar") or ctx.get("role_name") or "محامي"
    user_country = ctx.get("country_name_ar") or ctx.get("country_name") or "المملكة العربية السعودية"
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Optimized Prompt for Direct Action (v2.1 Planner)
    formatted_prompt = ADMIN_PLANNER_PROMPT.format(
        lawyer_name=lawyer_name,
        lawyer_id=lawyer_id,
        current_date=today,
        tools_desc=tools_str,
        user_input=user_input,
        chat_history=str(state.get("chat_history", [])[-3:]),
        user_role=user_role,
        user_country=user_country
    )
    
    system_msg = SystemMessage(content=formatted_prompt)
    
    # Build Context from Previous Execution
    tool_results = state.get("tool_results", [])
    results_context = ""
    if tool_results:
        results_context = f"\n    📊 Previous Execution Results (Use these IDs/Data):\n"
        for tr in tool_results:
            results_context += f"    - Tool: {tr.get('tool_call_id', 'unknown')}\n      Result: {tr.get('content', '')[:500]}\n"

    user_msg_content = f"""
    User Request: {user_input}
    {results_context}
    
    💡 Semantic Hints (Use these for better data accuracy):
    {extracted_entities_str}
    
    PLAN AND EXECUTE using the structured schema provided.
    """
    user_msg = HumanMessage(content=user_msg_content)
    
    messages = [system_msg] + state["chat_history"][-3:] + [user_msg]
    
    # Valid calls list
    valid_calls = []
    

    # Setup Parser (Robust Prompt Engineering Approach)
    parser = PydanticOutputParser(pydantic_object=AdminPlan)
    format_instructions = parser.get_format_instructions()
    
    # Inject instructions into system prompt
    # We append it to the end of the system prompt to ensure it's dominant
    complete_system_content = system_msg.content + "\n\n" + format_instructions
    
    # 🧹 Sanitize History to prevent Context Overflow
    original_history = state["chat_history"][-3:]
    sanitized_history = Sanitizer.compact_history(original_history, max_tokens=3000)
    
    # Update System Message
    messages = [SystemMessage(content=complete_system_content)] + sanitized_history + [user_msg]
    
    execution_plan_text = "Thinking..."
    
    # --- 🛡️ RESILIENT EXECUTION LOOP ---
    async def _invoke_llm():
        return await llm.ainvoke(messages)

    async def _handle_retry(error, attempt):
        error_type = ResiliencyManager.classify_error(error)
        if error_type == "context_overflow":
            logger.info("♻️ Triggering Auto-Compaction due to Context Overflow...")
            # Modify 'messages' in outer scope? No, we need to modify 'messages' that _invoke_llm usage.
            # But python closures bind late. So if we modify list content it might work?
            # Better: pass a mutable context container or just rely on 'Sanitizer' being aggressive next time?
            # Actually, we can pop older messages here.
            if len(messages) > 2:
                messages.pop(1) # Remove oldest chat message (idx 0 is system)
            return True
        return True # Continue retry for other errors (like JSON parsing)

    try:
        # Run with Retries
        response = await ResiliencyManager.run_with_retries(
            _invoke_llm, 
            max_attempts=3,
            on_error=_handle_retry
        )
        content = response.content
        
        # Parse Result
        try:
            plan: AdminPlan = parser.parse(content)
        except Exception as parse_error:
            logger.error(f"JSON Parse Error: {parse_error}. Content: {content[:100]}")
            # Fallback: Try manual cleaning via ResiliencyManager helper
            try:
                clean_json = ResiliencyManager.parse_json_safely(content)
                plan = AdminPlan(**clean_json)
            except:
                # Last resort: Treat as "Clarification Needed" if parsing fails entirely
                logger.warning("Parsing failed completely. Treating as unstructed query.")
                plan = AdminPlan(
                    plan_overview="تعذر فهم الهيكل، الرد كنص عادي.",
                    steps=[],
                    clarification_needed=content # Dump raw content as clarification
                )

        if plan:
            execution_plan_text = plan.plan_overview
            if plan.clarification_needed:
                execution_plan_text += f"\n\n❓ Clarification Needed: {plan.clarification_needed}"
            
            if plan.is_executable():
                valid_calls = plan.get_tool_calls()
                logger.info(f"✅ Generated Structured Plan: {len(valid_calls)} steps")
            else:
                logger.info("ℹ️ Plan has no executable steps (Info Query or Clarification)")
        else:
             execution_plan_text = "Failed to generate structured plan."
                
    except FailoverError as fe:
        logger.error(f"Action Node Critical Failure: {fe}")
        valid_calls = []
        execution_plan_text = f"System Error: {fe}"
    except Exception as e:
        logger.error(f"Action Node Unexpected Error: {e}")
        valid_calls = []
        execution_plan_text = f"Error planning steps: {str(e)}"

    return {
        "execution_plan": execution_plan_text,
        "tool_calls": valid_calls,
        "entities": {}, 
        "lookup_results": [],
        "loop_count": state.get("loop_count", 0) + 1 # Increment loop
    }


async def execute_node(state: AdminState) -> Dict[str, Any]:
    """
    Step 4: Execute Tools with Progress Reporting.
    Now with Smart Dependency Resolution (Context-Aware).
    """
    print("--- ADMIN: EXECUTE NODE (Smart Dependencies) ---")
    tool_calls = state.get("tool_calls", [])
    lawyer_id = state.get("lawyer_id")
    user_id = state.get("user_id")
    
    registry = SkillRegistry(lawyer_id=lawyer_id, current_user={"id": user_id, "role": "admin"})
    tools_map = registry.get_all_tools()
    
    tool_outputs = []
    
    # Track produced entities specifically: {"case": "uuid", "client": "uuid", ...}
    # This matches tool names like "insert_cases" -> "case"
    entity_tracker = {}
    
    for i, tc in enumerate(tool_calls):
        name = tc["name"]
        args = tc["args"]
        tc_id = tc["id"]
        
        # --- 1. Smart Dependency Resolution ---
        resolved_args = args.copy()
        dependency_error = False
        
        # Helper to extract ID from a result
        def _extract_id(content_dict: Dict) -> Optional[str]:
            # Try specific keys first
            if "inserted_id" in content_dict: return content_dict["inserted_id"]
            if "updated_id" in content_dict: return content_dict["updated_id"]
            
            # Try standard "id" in root or data list
            if "id" in content_dict: return content_dict["id"]
            
            data = content_dict.get("data")
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                 return data[0].get("id")
            if isinstance(data, dict):
                 return data.get("id")
            return None

        for k, v in resolved_args.items():
            # Check if this arg looks like a dependency (placeholder string)
            if isinstance(v, str) and ("من النتيجة السابقة" in v or "previous" in v.lower() or "first execution" in v.lower()):
                
                # Heuristic: Determine desired entity type from argument name
                # e.g., "case_id" -> "case", "client_id" -> "client"
                desired_entity = None
                if "_id" in k:
                    desired_entity = k.replace("_id", "") # "case", "client", "opponent"
                
                found_id = None
                
                # Strategy A: Look in our specific entity tracker (most accurate)
                if desired_entity and desired_entity in entity_tracker:
                    found_id = entity_tracker[desired_entity]
                    logger.info(f"🔗 Smart Resolve: Used tracked '{desired_entity}' -> {found_id}")
                
                # Strategy B: Fallback to finding ANY valid ID in previous results (LIFO)
                if not found_id:
                    for res in reversed(tool_outputs):
                        try:
                            data = json.loads(res["content"])
                            possible_id = _extract_id(data)
                            if possible_id:
                                # Validation: Don't use a Client ID for a Case ID if we can help it?
                                # For now, if we lack specific tracking, we accept it but log warning
                                found_id = possible_id
                                break
                        except: continue
                
                if found_id:
                    logger.info(f"🔗 Resolved dependency '{k}': '{v}' -> '{found_id}'")
                    resolved_args[k] = found_id
                else:
                    logger.error(f"⛔ CRITICAL: Could not resolve dependency for '{k}': '{v}'")
                    dependency_error = True
                    # Stop processing this tool to prevent DB crash
                    break

        if dependency_error:
            error_msg = f"Skipped execution due to unresolved dependency for tool {name}"
            logger.error(error_msg)
            tool_outputs.append({
                "tool_call_id": tc_id,
                "content": json.dumps({"success": False, "error": error_msg})
            })
            continue

        # --- 2. Execute Tool ---
        if name in tools_map:
            try:
                print(f"   🔨 Executing: {name} ({i+1}/{len(tool_calls)})")
                
                func = tools_map[name]
                res = func(**resolved_args)
                
                # Snapshot the output
                output_json = json.dumps(res, ensure_ascii=False)
                tool_outputs.append({
                    "tool_call_id": tc_id,
                    "content": output_json
                })
                
                # --- 3. Update Entity Tracker ---
                if res.get("success"):
                    # Infer entity type from tool name
                    # e.g. insert_cases -> case
                    # e.g. query_clients -> client
                    entity_type = None
                    if "_" in name:
                        parts = name.split("_")
                        if len(parts) >= 2:
                            # handling names like 'insert_cases', 'query_clients'
                            raw_type = parts[1] # 'cases', 'clients'
                            # SINGULARIZE (Naive)
                            if raw_type.endswith("ies"): entity_type = raw_type[:-3] + "y"
                            elif raw_type.endswith("s"): entity_type = raw_type[:-1]
                            else: entity_type = raw_type
                    
                    extracted_id = _extract_id(res)
                    if entity_type and extracted_id:
                        entity_tracker[entity_type] = extracted_id
                        logger.info(f"🧠 Tracker Updated: {entity_type} = {extracted_id}")

            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                tool_outputs.append({
                    "tool_call_id": tc_id,
                    "content": json.dumps({"success": False, "error": str(e)})
                })
        else:
            tool_outputs.append({
                "tool_call_id": tc_id,
                "content": json.dumps({"success": False, "error": "Tool not found"})
            })
            
    # Calculate statistics
    success_count = sum(1 for out in tool_outputs if '"success": true' in out.get("content", "").lower())
    fail_count = len(tool_outputs) - success_count
    
    return {
        "tool_results": tool_outputs,
        "execution_summary": {
            "total_tools": len(tool_calls),
            "successful": success_count,
            "failed": fail_count
        }
    }


def _manual_synthesis(tool_results: List[Dict], user_input: str) -> str:
    """
    Fallback: Manual synthesis if LLM fails.
    صياغة يدوية للرد إذا فشل LLM.
    """
    if not tool_results:
        return "لم أتمكن من العثور على نتائج. يرجى التحقق من الطلب."
    
    # Parse first result
    try:
        first_result = json.loads(tool_results[0]["content"])
        
        if first_result.get("success"):
            count = first_result.get("count", 0)
            data = first_result.get("data", [])
            
            # Infer query type from user input
            if "موكل" in user_input or "عميل" in user_input or "client" in user_input.lower():
                if count == 0:
                    return "لا يوجد موكلين مسجلين في النظام."
                elif count == 1:
                    client = data[0] if data else {}
                    return f"لديك موكل واحد: {client.get('full_name', 'غير معروف')}"
                else:
                    return f"لديك {count} موكل مسجل في النظام."
            
            elif "قضية" in user_input or "case" in user_input.lower():
                if count == 0:
                    return "لا توجد قضايا مسجلة."
                else:
                    return f"لديك {count} قضية في النظام."
            
            elif "جلسة" in user_input or "hearing" in user_input.lower():
                if count == 0:
                    return "لا توجد جلسات قادمة."
                else:
                    return f"لديك {count} جلسة مسجلة."
            
            else:
                # Generic response
                if count == 0:
                    return "لم يتم العثور على نتائج."
                else:
                    return f"تم العثور على {count} سجل."
        
        else:
            error = first_result.get("error", "خطأ غير معروف")
            # Clean error message
            if "does not exist" in error:
                return "عذراً، حدث خطأ في الاستعلام. يرجى التحقق من البيانات المطلوبة."
            return f"عذراً، حدث خطأ: {error}"
    
    except Exception as e:
        logger.error(f"Manual synthesis parsing error: {e}")
        # ✅ FIX: Do not pretend success on error
        return "عذراً، حدث خطأ أثناء معالجة النتائج. يرجى المحاولة مرة أخرى."


async def synthesize_node(state: AdminState) -> Dict[str, Any]:
    """
    ✅ REVOLUTIONARY FIX: The Synthesis Node
    
    This is THE ONLY node that sets final_response.
    Converts raw tool execution results into clear Arabic responses.
    
    المسؤولية: تحويل نتائج الأدوات إلى رد عربي واضح ومفهوم.
    """
    logger.info("--- ADMIN: SYNTHESIZE NODE ---")
    
    original_input = state["input"]
    entities = state.get("entities", {})
    tool_results = state.get("tool_results", [])
    execution_plan = state.get("execution_plan", "")
    execution_summary = state.get("execution_summary", {})
    
    # Build context for LLM
    context_parts = []
    context_parts.append(f"طلب المستخدم الأصلي: {original_input}")
    
    if entities:
        context_parts.append(f"\nالبيانات المُستخرجة: {json.dumps(entities, ensure_ascii=False)}")
    
    if execution_summary:
        context_parts.append(f"\nملخص التنفيذ: {execution_summary.get('successful', 0)} نجح، {execution_summary.get('failed', 0)} فشل")
    
    if tool_results:
        # 🧹 Sanitize Tool Outputs (Truncate massive results)
        clean_tool_results = Sanitizer.sanitize_tools_context(tool_results, max_len=2000)
        
        context_parts.append(f"\nنتائج تنفيذ الأدوات:")
        for i, result in enumerate(clean_tool_results):
            content = result.get("content", "{}")
            try:
                result_data = json.loads(content)
                # Format nicely
                if result_data.get("success"):
                    context_parts.append(f"  ✅ أداة {i+1}: {json.dumps(result_data, ensure_ascii=False, indent=2)}")
                else:
                    context_parts.append(f"  ❌ أداة {i+1}: فشلت - {result_data.get('error', 'خطأ غير معروف')}")
            except:
                context_parts.append(f"  أداة {i+1}: {content}")
    
    context = "\n".join(context_parts)
    
    context = "\n".join(context_parts)
    
    # Context (User Context)
    ctx = state.get("context", {}).get("user_context", {})
    lawyer_name = ctx.get("full_name") or "شريكي"

    # --- 🛡️ SMART FINALIZER CHECK ---
    # Only verify IF we are not in a manual fallback
    # And only if tools were actually executed (implies an action was taken)
    if tool_results:
        # We need to temporarily instantiate the tools to access the finalizer
        # Optimization: We could pass it, but re-init is safer for state
        lawyer_id = state.get("lawyer_id")
        user_id = state.get("user_id")
        registry = SkillRegistry(lawyer_id=lawyer_id, current_user={"id": user_id, "role": "admin"})
        all_tools = registry.get_all_tools()
        
        if "finalize_task" in all_tools:
            finalizer = all_tools["finalize_task"]
            # Assume successful if no explicit errors, but let Finalizer decide rigor
            # We don't have a specific task_id tracked in state easily, 
            # but we can pass a dummy or try to find one from context?
            # actually, maybe we just pass "completed" and let it check constraints?
            # The prompt says: finalizer_result = tools[0].invoke({"task_id": state.task_id, ...})
            # We don't strictly track task_id in AdminState yet. 
            # Let's assume we skip precise task_id for now or grab if available.
            # But wait, finalizer needs context.
            
            # Let's try to run it.
            try:
                # We'll run it with a generic claim for now to enforce "Generic Checks"
                # or if we inserted a task, we might have its ID in tool_results?
                # Optimization: Look for task_id in tool outputs
                task_id = None
                for res in tool_results:
                    if '"id":' in res["content"] and '"title":' in res["content"]: # Potential task
                         try:
                             d = json.loads(res["content"])
                             if "id" in d: task_id = d["id"]
                         except: pass
                
                logger.info(f"🕵️ Finalizer checking task... (ID: {task_id})")
                fin_res = finalizer.run(task_id=task_id, new_status="completed")
                
                if not fin_res.success:
                     logger.warning(f"⛔ Finalizer blocked completion: {fin_res.error}")
                     # Append this critical failure to the context so LLM Explains it
                     context_parts.append(f"\n❌ تنبيه هام من النظام: لا يمكن إغلاق المهمة كمنجزة. السبب: {fin_res.error}")
                     # Force status? The LLM will read this and explain.
                else:
                     logger.info("✅ Finalizer approved completion.")
                     context_parts.append(f"\n✅ تم التحقق من سلامة العملية بواسطة النظام.")
            except Exception as e:
                logger.warning(f"Finalizer check skipped: {e}")

    # Use the User-Defined Prompt (Imported)

    # Use the User-Defined Prompt (Imported)
    synthesizer_prompt = ADMIN_SYNTHESIZE_PROMPT.format(
        lawyer_name=lawyer_name,
        tool_outputs=context # We pass the full context (including query) as tool_outputs
    )
    
    # For compatibility where we construct the prompt string manually above:
    prompt_content = synthesizer_prompt
    
    llm = get_llm(temperature=0, streaming=False)
    
    # Include chat history for context awareness
    messages = [
        SystemMessage(content="أنت مدير مكتب ذكي ومرن. تتحدث بطبيعية وبدون تكلف."),
    ] + state["chat_history"][-5:] + [
        HumanMessage(content=prompt_content)
    ]
    
    # 🛡️ HONESTY CHECK & GUARDRAILS (Anti-Hallucination)
    # Detect if user wanted a WRITE action (Delete/Update/Insert)
    write_keywords = ["حذف", "امسح", "شيل", "delete", "remove", "cancel", "تعديل", "غير", "update", "edit", "change", "إضافة", "سجل", "add", "create", "insert"]
    user_intent_is_write = any(kw in original_input.lower() for kw in write_keywords)
    
    # Check if ANY write tool was actually attempted AND succeeded
    write_tools_executed = 0
    write_tools_successful = 0
    
    for res in tool_results:
        content_str = res.get("content", "")
        # Heuristic to detect write tools from content or ID implies looking at plan, 
        # but here we only have results. Ideally we look at tool_calls but they are upstream.
        # Let's check the tool_call_id or content for success.
        # Wait, we have tool_calls in state from previous node, but synthesize receives them in state?
        # Yes, state has "tool_calls".
        pass 

    # Better approach: Iterate over tool_calls to find intent, match with results
    # We need to rely on 'input' state["tool_calls"]? No, synthesize node receives 'tool_results' populated by execute node.
    # We can infer tool type from the function name if we tracked it, but we only have ID/Content here.
    # However, 'execution_summary' might be extended or we scan content for "deleted", "updated", "inserted" if tools return that.
    # BUT, our tools usually return {success: true, data: ...}.
    
    # 🛡️ ANTI-HALLUCINATION GUARD:
    # If the user wanted to WRITE, and we see FAILURES in the logs, we MUST NOT report success.
    if user_intent_is_write and execution_summary.get("failed", 0) > 0:
        logger.warning(f"⛔ WRITER BLOCK: User wanted write, but {execution_summary.get('failed')} tools failed.")
        
        # Inject forceful context
        failed_tools_context = []
        for res in tool_results:
             if '"success": false' in res.get("content", "").lower() or "error" in res.get("content", "").lower():
                 failed_tools_context.append(f"- Tool Failed: {res.get('content')}")
        
        fail_msg = "\n".join(failed_tools_context)
        context_parts.append(f"\n⚠️ SYSTEM ALERT: CRITICAL FAILURE IN EXECUTION.\nSome operations FAILED. DO NOT CLAIM SUCCESS.\nErrors:\n{fail_msg}\nExplain clearly what failed.")
        
        # We can also modify the prompt to be stricter
        prompt_content += "\n\nCRITICAL INSTRUCTION: There were ERRORS in execution. You MUST report them. Do NOT say 'Success' if tools failed."

    try:
        # ✅ FIX: Add 'final_response' tag to allow streaming
        # 🛡️ RESILIENT EXECUTION LOOP
        async def _invoke_synthesizer():
            return await llm.ainvoke(messages, config={"tags": ["final_response"]})

        async def _handle_synth_retry(error, attempt):
            error_type = ResiliencyManager.classify_error(error)
            if error_type == "context_overflow":
                logger.warning("♻️ Synthesis Overflow. Aggressively compacting context...")
                # Reduce chat history in messages
                # Messages structure: [System, ...History, Human]
                # We can try to trim History or simplify the Tool Output prompts
                if len(messages) > 2:
                    messages.pop(1) # Remove oldest chat
                return True
            return True

        response = await ResiliencyManager.run_with_retries(
            _invoke_synthesizer,
            max_attempts=3,
            on_error=_handle_synth_retry
        )
        final_response = response.content.strip()
        
        # 🛡️ Defense: Robust Cleaner
        # 1. Remove Markdown Code Blocks
        final_response = re.sub(r"```.*?```", "", final_response, flags=re.DOTALL)
        
        # 2. Remove leading JSON-like structures (List or Dict) that might appear before text
        # Match [ ... ] or { ... } at the start, possibly spanning lines
        final_response = re.sub(r"^\s*\[.*?\]", "", final_response, flags=re.DOTALL)
        final_response = re.sub(r"^\s*\{.*?\}", "", final_response, flags=re.DOTALL)
        
        # 3. Aggressive: If line starts with [ or {, remove the whole line (common artifact)
        lines = final_response.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('[') or stripped.startswith('{') or stripped.startswith(']'):
                continue
            if '"name":' in stripped or '"args":' in stripped: # Heuristic for tool call leakage
                continue
            clean_lines.append(line)
        final_response = "\n".join(clean_lines).strip()

        # Safety check
        if not final_response:
             final_response = "تمت العملية بنجاح."

        # ✅ HARDENED CHECK: If it still looks like JSON, kill it.
        # The user reported: {"action": "ADMIN_QUERY", ...} which is likely the PLAN leaking or a tool result.
        if final_response.strip().startswith('{') or '"action":' in final_response:
            logger.warning("⚠️ LLM returned JSON in Synthesis, forcing fallback")
            final_response = _manual_synthesis(tool_results, original_input)
            
            # Double check manual synthesis didn't fail
            if final_response.strip().startswith('{'):
                 final_response = "تمت العملية بنجاح. (تعذر صياغة الرد)"
        
        # 🛡️ REALITY CHECK (The "Fake Delete" Prevention)
        # If user asked to "Delete/Remove" and the response claims "I deleted/removed",
        # BUT we (the system) suspect no delete tool ran (e.g. only queries in context), block it.
        # Since we don't have perfect structured tool history in this node scope easily (without parsing raw state),
        # we will rely on the "execution_summary" and text context.
        # If execution_summary['total_tools'] > 0 but they were all queries? 
        
        # Override logic: If User Input contains "Delete/Remove" AND final_response contains "تم الحذف/deleted"
        # We verify if we actually see "delete_" in the tool logs passed to context.
        context_str = str(context)
        if "حذف" in original_input or "delete" in original_input.lower():
            # Check broad match for any delete tool variant (delete_, safe_delete_, etc)
            if "delete" not in context_str.lower() and "update" not in context_str.lower():
                # User asked to delete, we generated response, but no delete tool is in the context log!
                logger.warning("⛔ HALLUCINATION DETECTED: Claiming delete without delete tool execution.")
                final_response = "عذراً، لم أتمكن من تنفيذ الحذف. واجهت مشكلة في تحديد البيانات بدقة أو فشل التحقق من العملية."

        logger.info(f"✅ Synthesized response: {final_response[:150]}...")
        
    except Exception as e:
        logger.error(f"❌ Synthesis error: {e}")
        final_response = _manual_synthesis(tool_results, original_input)
    
    return {
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)]
    }


# --- 3. Build Graph ---
def build_admin_graph():
    """
    ✅ REVOLUTIONARY FIX: Optimized Linear Graph
    
    Flow: Action (extract+plan) → Execute → Synthesize → END
                                 ↓ (no tools)
                                 └─→ Synthesize → END
    """
    workflow = StateGraph(AdminState)
    
    # Add nodes (Reduced set)
    workflow.add_node("action", action_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("synthesize", synthesize_node)
    
    # Linear entry flow
    workflow.set_entry_point("action")
    
    # Conditional from action: tools needed or not?
    def check_tools(state: AdminState):
        """If tools are needed, execute them. Otherwise go straight to synthesis."""
        # loop_count check
        if state.get("loop_count", 0) > 3:
             logger.warning("🚫 Admin Loop Limit Reached (3). Forcing Synthesis.")
             return "synthesize"

        if state.get("tool_calls") and len(state.get("tool_calls", [])) > 0:
            return "execute"
        else:
            # No tools needed (simple query or informational request)
            return "synthesize"

    workflow.add_conditional_edges("action", check_tools)
    
    # ✅ CIRCULAR EXECUTION: Execute -> Action (Re-plan)
    # BUT! If we just did a successful write, we should probably verify or stop, not blindly re-plan.
    
    def check_result_and_loop(state: AdminState):
        """
        After Execution: Decide to Loop (Re-plan) or Stop (Synthesize).
        Smart Check: Only stop if we GENUINELY performed a write (Delete/Update/Insert).
        """
        tool_results = state.get("tool_results", [])
        
        # Check for successful write operations
        write_success = False
        for res in tool_results:
            try:
                content = res.get("content", "")
                data = json.loads(content)
                
                # Check for explicit success flag
                if data.get("success") is True:
                    # Check for explicit write confirmation keys from our DB tools
                    # These keys are only present in _generate_X_tool outputs for writes
                    if "deleted_id" in data or "updated_id" in data or "inserted_id" in data:
                        write_success = True
                        break
                    
                    # Fallback: Check message for specific action verbs (Arabic or English)
                    msg = data.get("message", "").lower()
                    if "deleted" in msg or "updated" in msg or "inserted" in msg:
                        # Avoid "found 0 matches" false positives
                         write_success = True
                         break
                    if "تم الحذف" in msg or "تم التعديل" in msg or "تمت الإضافة" in msg:
                        write_success = True
                        break
                
                # ✅ RELAXED CHECK: If success is True and it's not a read-only query
                # We assume if the tool didn't fail and it wasn't just a "select", it's a write.
                # But "select" also returns success=True.
                # However, our DB tools usually return {success: true} for writes.
                # Let's trust the "success": true if we can't differentiate, 
                # OR relay on the fact that if we are here, we executed tools.
                # If we executed tools and they succeeded, we should probably stop looping unless we need to verify.
                # The issue was "Failed to delete" loop.
                if data.get("success") is True:
                     # Check if it was a SELECT
                     # Heuristic: Selects usually have "data": [list] or "count": N.
                     # Writes usually have "data": {dict} or null or "message".
                     is_likely_select = isinstance(data.get("data"), list)
                     if not is_likely_select:
                         write_success = True
                         break
                         
            except: pass
            
        # ✅ Checks for Partial Success (Query Retries)
        successful_steps = [r for r in tool_results if r.get("content") and '"success": true' in r.get("content", "")] # string match heuristic or parse?
        # Better: parse content.
        parsed_results = []
        for r in tool_results:
            try:
                parsed_results.append(json.loads(r["content"]))
            except: pass
            
        success_count = sum(1 for p in parsed_results if p.get("success"))
        
        # If we have ANY successful data retrieval or action, we should synthesize.
        # Don't loop unless EVERYTHING failed.
        if success_count > 0:
             logger.info("✅ Partial/Full Success detected. Proceeding to Synthesis.")
             return "synthesize"
             
        # If no success, retry (action)
        return "action"

    workflow.add_conditional_edges("execute", check_result_and_loop)
    
    # ✅ Synthesize is the FINAL node - always ends the graph
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()

# --- 4. Main Entry Node for Parent Graph ---
admin_graph_runnable = build_admin_graph()

async def admin_ops_node(state: AgentState) -> Dict[str, Any]:
    """
    The main node that the Parent Graph calls.
    It delegates work to the 'admin_graph'.
    """
    # Mapping AgentState to AdminState input
    admin_input = {
        "input": state["input"] if "input" in state else state["messages"][-1].content,
        "chat_history": state["chat_history"],
        "user_id": state.get("user_id"),
        "lawyer_id": state.get("lawyer_id"),
        "context": state.get("context", {}),
        "entities": {},
        "lookup_results": [],
        "execution_plan": "",
        "tool_calls": [],
        "tool_results": [], 
        "execution_summary": {},
        "loop_count": 0
    }
    
    logger.info("🔄 Invoking Admin Subgraph...")
    final_state = await admin_graph_runnable.ainvoke(admin_input)
    
    # ✅ Extract final_response
    final_response = final_state.get("final_response", "تم تنفيذ العملية.")
    execution_summary = final_state.get("execution_summary", {})
    
    logger.info(f"✅ Admin Subgraph complete. Response: {final_response[:100]}...")
    
    # --- REVERSE ESCALATION CHECK ---
    # If all tools failed, or if we have 0 successes and >0 failures, Escalate.
    # Also if the response explicitly contains "Escalate" (can be prompt engineered later)
    failed = execution_summary.get("failed", 0)
    success = execution_summary.get("successful", 0)
    
    intent = "REPORTING_BACK"
    
    # If we tried tools and ALL failed, assume we need Higher Judgment (or human Clarification)
    if failed > 0 and success == 0:
        logger.warning(f"⚠️ Admin Failure Detected ({failed} failed). Escalating to Judge.")
        intent = "ESCALATE_TO_JUDGE"
        # We append a note to the response so the Judge knows why
        state["scratchpad"] = state.get("scratchpad", []) + [f"Admin Failed: {final_response}"]
    
    return {
        "final_response": final_response,
        "current_step": state.get("current_step", 1) + 1,
        "scratchpad": state.get("scratchpad", []) + [f"Admin Subgraph: {final_response[:100]}..."],
        "intent": intent 
    }
