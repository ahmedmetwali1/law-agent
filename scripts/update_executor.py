import re

file_path = r'e:\law\agents\core\graph_agent.py'

new_executor = r'''    def execute_plan_node(state: AgentState):
        """
        ⚙️ Executor Node - Executes plan or handles simple queries
        This is where tools are actually called
        """
        # ✅ Update UI status
        update_session_status(session_id, "⚙️ تنفيذ الخطة...")
        
        # Deserialize decision and plan from dicts
        decision_dict = state.get('cognitive_decision')
        plan_dict = state.get('execution_plan')
        messages = state['messages']
        
        decision = CognitiveDecision(**decision_dict) if decision_dict else None
        plan = ExecutionPlan(**plan_dict) if plan_dict else None
        
        # For SIMPLE queries: direct LLM call
        if decision and decision.complexity == QueryComplexity.SIMPLE:
            logger.info("⚙️ Executor: Direct execution (simple)")
            
            # Prepare context
            lawyer_context = state.get("lawyer_context")
            system_msg = SystemMessage(content=str(lawyer_context)) if lawyer_context else SystemMessage(content="أنت مساعد قانوني ذكي.")
            
            full_history = [system_msg] + messages if not (messages and isinstance(messages[0], SystemMessage)) else messages
            
            response = llm_with_tools.invoke(full_history)
            return {"messages": [response]}
        
        # For COMPLEX queries with plan: execute steps
        if plan and plan.steps:
            logger.info(f"⚙️ Executor: Executing {len(plan.steps)}-step plan")
            results = []
            context_manager = state.get('context_manager')
            step_outputs = {}  # Store results for chaining: {1: "uuid...", 2: "uuid..."}
            
            for step in plan.steps:
                step_start = time.time()
                logger.info(f"⚙️ Step {step.step_number}/{len(plan.steps)}: {step.action}")
                
                # ✅ Update UI status for each step
                update_session_status(session_id, f"⚙️ تنفيذ خطوة {step.step_number}: {step.action}")
                
                try:
                    # Get the tool function
                    tool_func = tools_map.get(step.action)
                    
                    if tool_func:
                        # ✅ Dependency Injection Logic
                        # 1. Resolve {{STEP_X_RESULT}} placeholders
                        params = step.parameters.copy()
                        for key, value in params.items():
                            if isinstance(value, str) and value.startswith("{{STEP_") and value.endswith("_RESULT}}"):
                                step_ref = int(value.replace("{{STEP_", "").replace("_RESULT}}", ""))
                                if step_ref in step_outputs:
                                    # Try to extract ID from previous result
                                    prev_result = step_outputs[step_ref]
                                    if isinstance(prev_result, dict) and "id" in prev_result:
                                        params[key] = prev_result["id"]
                                        logger.info(f"🔗 Linked {key} to Step {step_ref} result: {prev_result['id']}")
                                    else:
                                        logger.warning(f"⚠️ Could not extract ID from Step {step_ref} result")
                        
                        # 2. Resolve {{AUTO}} using ContextManager
                        if context_manager:
                            params = context_manager.inject_context_into_params(params)
                            
                        # Execute tool
                        logger.info(f"▶️ Invoking {step.action} with params: {params}")
                        result = tool_func.invoke(params) if hasattr(tool_func, 'invoke') else tool_func(**params)
                        
                        # Store result for future steps
                        step_outputs[step.step_number] = result
                        
                        # ✅ Register created entities
                        if context_manager and isinstance(result, dict) and "id" in result:
                            # Heuristic: created entity type from tool name
                            entity_type = step.action.replace("create_", "").replace("add_", "")
                            entity_name = result.get("full_name") or result.get("title") or result.get("name", "Unknown")
                            context_manager.register_entity(entity_type, result["id"], entity_name, result)

                        exec_result = ExecutionResult(
                            step_number=step.step_number,
                            action=step.action,
                            success=True,
                            output=result,
                            execution_time=time.time() - step_start
                        )
                        results.append(exec_result)
                        logger.info(f"✅ Step {step.step_number} completed")
                    else:
                        logger.warning(f"⚠️ Tool not found: {step.action}")
                        exec_result = ExecutionResult(
                            step_number=step.step_number,
                            action=step.action,
                            success=False,
                            error_message=f"Tool '{step.action}' not found",
                            execution_time=time.time() - step_start
                        )
                        results.append(exec_result)
                except Exception as e:
                    logger.error(f"❌ Step {step.step_number} failed: {e}")
                    exec_result = ExecutionResult(
                        step_number=step.step_number,
                        action=step.action,
                        success=False,
                        error_message=str(e),
                        execution_time=time.time() - step_start
                    )
                    results.append(exec_result)
                    # Stop execution on failure
                    break
        
            # Serialize for state
            serialized_results = [res.model_dump() for res in results]
            return {"execution_results": serialized_results}
        
        # Fallback
        logger.warning("⚙️ Executor: No plan found, fallback to simple execution")
        # Reuse simple logic...
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}'''

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to safe replacement: from 'def execute_plan_node' until 'def route_after_execution'
pattern = r'(    def execute_plan_node\(state: AgentState\):.*?)(\n\s+def route_after_execution)'

match = re.search(pattern, content, re.DOTALL)
if match:
    print("Found execute_plan_node, replacing...")
    new_content = content.replace(match.group(1), new_executor)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replacement successful!")
else:
    print("Could not find execute_plan_node function block.")
