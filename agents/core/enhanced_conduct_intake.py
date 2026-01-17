"""
Enhanced conduct_intake - Ultra Simple & Smart
Let LLM intelligence + native function calling do the work
"""

import json
import logging

logger = logging.getLogger(__name__)

# Import orchestrator for multi-step tasks
from agents.planning import IntentAnalyzer, PlanningEngine
from agents.orchestration import TaskOrchestrator, ProgressStreamer

def conduct_intake_with_tools(self, chat_history, memory_context="", conversation_context=None):
    """
    Smart conversation flow with session caching
    
    Philosophy:
    - Minimal intervention
    - LLM intelligence + function calling handles most cases
    - Session cache eliminates redundant DB queries
    - Only special handling for unauthenticated users
    
    Args:
        chat_history: List of conversation messages
        memory_context: Additional context string
        
    Returns:
        Response dictionary with thought, response_text, internal_state, extracted_data
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 🧠 Store conversation context for entity tracking
    self.conversation_context = conversation_context
    
    logger.info("🚀 Enhanced conduct_intake - Smart mode")
    
    # Get last user message
    last_message = chat_history[-1]["content"] if chat_history else ""
    logger.info(f"📝 User message: {last_message[:100]}")
    
    # ✅ Initialize and use session cache
    if hasattr(self, 'lawyer_id') and self.lawyer_id:
        # Initialize session cache if not exists
        if not hasattr(self, 'session_cache'):
            from agents.memory.session_cache import SessionCache
            self.session_cache = SessionCache(self.lawyer_id, ttl=300)  # 5 min TTL
            logger.info("🆕 SessionCache created")
        
        # Load profile with caching ONLY if tools are available
        if hasattr(self, 'unified_tools') and self.unified_tools:
            def fetch_profile_from_db():
                """Fetch profile from database (expensive operation)"""
                result = self.unified_tools.execute_tool("get_my_profile")
                if result.get("success"):
                    return result.get("profile", {})
                return {}
            
            # Get profile (cached or fresh)
            profile = self.session_cache.get_profile(fetch_profile_from_db)
            
            # Add to memory context
            if profile:
                memory_context += f"\n\n=== Lawyer Context ===\n"
                memory_context += f"Name: {profile.get('full_name', 'Unknown')}\n"
                memory_context += f"Email: {profile.get('email', 'N/A')}\n"
                memory_context += f"Phone: {profile.get('phone', 'N/A')}\n"
                
                # Log cache stats
                stats = self.session_cache.get_stats()
                logger.debug(f"📊 Cache stats: Hit rate={stats['hit_rate']:.1%}")
        else:
            logger.warning("⚠️ unified_tools not available - profile not loaded")
    
    # 🎭 ORCHESTRATOR: Check if this is a multi-step request
    try:
        # Initialize intent analyzer if not exists
        if not hasattr(self, 'intent_analyzer'):
            # Pass reasoning engine for intelligent analysis
            reasoning_engine = getattr(self, 'reasoning_engine', None)
            self.intent_analyzer = IntentAnalyzer(self.llm_client, reasoning_engine)
        
        # Quick check for multi-step indicators
        if self.intent_analyzer.is_multi_step_request(last_message):
            logger.info("🎭 Detected multi-step request, using orchestrator...")
            
            # Get available tools for intelligent selection
            available_tools = self.unified_tools.get_available_tools_list() if hasattr(self, 'unified_tools') else []
            
            # 1. Analyze intent with intelligent reasoning
            tasks = self.intent_analyzer.analyze(
                last_message, 
                chat_history,
                available_tools=available_tools  # ✅ Pass available tools
            )
            
            if len(tasks) > 1:
                logger.info(f"✅ Extracted {len(tasks)} tasks, creating execution plan...")
                
                # 2. Create execution plan
                planning_engine = PlanningEngine()
                plan = planning_engine.create_plan(tasks)
                
                # 3. Create progress streamer
                progress = ProgressStreamer()
                
                # 4. Execute plan with orchestrator
                orchestrator = TaskOrchestrator(self.unified_tools, progress)
                result = orchestrator.execute_plan(plan)
                
                # 5. Format response with progress summary
                response_text = progress.format_summary()
                
                # Add final summary
                if result.success:
                    response_text += f"\n\n🎉 **اكتملت جميع المهام!**\n\n"
                    response_text += f"⏱️ الوقت المستغرق: {result.duration:.1f} ثانية"
                else:
                    response_text += f"\n\n⚠️ **تم تنفيذ بعض المهام، لكن حدثت أخطاء:**\n"
                    for error in result.errors:
                        response_text += f"\n❌ {error}"
                
                return {
                    "thought": f"Executed {len(tasks)}-step plan",
                    "response_text": response_text,
                    "internal_state": "ORCHESTRATED",
                    "extracted_data": {
                        "tasks_executed": len(tasks),
                        "success": result.success,
                        "results": result.results
                    }
                }
            else:
                logger.info("ℹ️ Only one task extracted, using standard flow")
                
    except Exception as e:
        logger.error(f"❌ Orchestration failed: {e}")
        logger.info("⤵️ Falling back to standard flow")
        # Fall through to standard flow
    
    # ⚠️ ONLY special case: User not authenticated
    if not hasattr(self, 'lawyer_id') or not self.lawyer_id:
        query_lower = last_message.lower()
        
        # Simple greetings work without auth
        simple_greetings = ["مرحبا", "مرحباً", "السلام", "أهلا", "هلا", "hi", "hello"]
        if any(g in query_lower for g in simple_greetings) and len(last_message.split()) <= 3:
            return {
                "thought": "Guest greeting - not authenticated",
                "response_text": "مرحباً! 👋\n\nأنا مساعدك الذكي.\n\n🔑 سجل دخولك لأساعدك في:\n✅ إدارة موكليك\n✅ متابعة قضاياك\n✅ تنظيم جلساتك\n\nجاهز لخدمتك! 💪",
                "internal_state": "GREETING",
                "extracted_data": {}
            }
        
        # Identity questions without auth
        identity_keywords = ["من انت", "من أنت", "ما مهمتك", "ماذا تستطيع"]
        if any(kw in query_lower for kw in identity_keywords):
            return {
                "thought": "Identity query - not authenticated",
                "response_text": "أنا مساعدك الشخصي الذكي! 💼\n\n🎯 **مهمتي:**\nمساعدتك في كل ما يخص مكتبك القانوني\n\n💪 **قدراتي:**\n✅ إدارة الموكلين والقضايا\n✅ تنظيم الجلسات\n✅ البحث القانوني\n✅ تحليل القضايا\n\n🔑 سجل دخولك لأستطيع مساعدتك بشكل شخصي!",
                "internal_state": "IDENTITY",
                "extracted_data": {}
            }
    
    # ✅ Everything else: Use LLM with professional prompt + function calling
    logger.info("⏩ Using LLM with function calling (smart mode)")
    
    # Build messages for LLM
    messages = []
    
    # Add system prompt from professional_prompt.py
    system_prompt = self._default_system_prompt()
    messages.append({"role": "system", "content": system_prompt})
    
    # 🧠 INJECT CONVERSATION CONTEXT (like Antigravity does!)
    if self.conversation_context and hasattr(self.conversation_context, 'get_last_entity'):
        last_entity = self.conversation_context.get_last_entity()
        if last_entity:
            context_instruction = f"""
🧠 IMPORTANT CONTEXT AWARENESS:

Last mentioned entity:
- Type: {last_entity['type']}
- ID: {last_entity['id']}

If user says "له" (for him), "لها" (for her), or "للعميل/للقضية" - they mean THIS entity!

DO NOT search again! Use the ID directly:
- For client questions → get_client_details(client_id="{last_entity['id']}")
- For client cases → list_client_cases(client_id="{last_entity['id']}")
"""
            messages.append({"role": "system", "content": context_instruction})
    
    # Add context if provided
    if memory_context:
        messages.append({"role": "system", "content": f"Context:\n{memory_context}"})
    
    # Add chat history
    for msg in chat_history:
        if isinstance(msg, dict):
            messages.append(msg)
    
    # Get tools for function calling
    tools = []
    if hasattr(self, 'unified_tools') and self.unified_tools:
        tools = self.unified_tools.get_openai_tools()
    
    # Call LLM with function calling
    try:
        response = self.llm_client.chat_completion(
            messages=messages,
            temperature=0.7,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None
        )
        
        # Check if LLM wants to call tools
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info(f"🔧 LLM requested {len(response.tool_calls)} tool calls")
            
            # Execute tools
            for tool_call in response.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                
                logger.info(f"🔧 Executing: {tool_name} with args {tool_args}")
                
                # Execute tool
                result = self.unified_tools.execute_tool(tool_name, **tool_args)
                
                # 🧠 UPDATE CONTEXT (like Antigravity tracks state!)
                if self.conversation_context:
                    # Remember searched/found clients
                    if tool_name == "search_clients" and result.get("clients"):
                        for client in result["clients"]:
                            self.conversation_context.remember_client(client)
                            logger.info(f"💭 Remembered client: {client.get('full_name')}")
                    
                    # Remember case details
                    elif tool_name == "get_client_details" and result.get("client"):
                        self.conversation_context.remember_client(result["client"])
                    
                    elif tool_name == "create_case" and result.get("case"):
                        self.conversation_context.remember_case(result["case"])
                
                # ✅ Safety: Ensure result is serializable
                if result is None:
                    result = {"success": False, "message": "No data"}
                
                result_json = json.dumps(result, ensure_ascii=False)
                
                # ✅ CRITICAL OpenWebUI FIX:
                # DON'T add assistant message with tool_calls!
                # Just add the result directly as system message
                tool_result_text = f"""Tool Execution Complete:

Tool Used: {tool_name}
Arguments: {json.dumps(tool_args, ensure_ascii=False)}

Result:
{result_json}

Now provide a natural conversational response in Arabic based on this data."""

                messages.append({
                    "role": "system",
                    "content": tool_result_text
                })
            
            # Call LLM again to get natural language response
            logger.info("🔄 Sending tool results back to LLM for natural response...")
            final_response = self.llm_client.chat_completion(
                messages=messages,
                temperature=0.7
            )
            
            response_text = final_response if isinstance(final_response, str) else final_response.content
            
            return {
                "thought": f"Executed tools and generated natural response",
                "response_text": response_text,
                "internal_state": "GENERAL_QA",
                "extracted_data": {}
            }
        
        # No tool calls - just return LLM response
        response_text = response if isinstance(response, str) else response.content
        
    except Exception as e:
        logger.error(f"❌ LLM call failed: {e}")
        response_text = "عذراً، حدث خطأ. يرجى المحاولة مرة أخرى."
    
    # Return in expected format
    return {
        "thought": "LLM responded",
        "response_text": response_text,
        "internal_state": "GENERAL_QA",
        "extracted_data": {}
    }


# This function will be added as a method to EnhancedGeneralLawyerAgent
__all__ = ["conduct_intake_with_tools"]
