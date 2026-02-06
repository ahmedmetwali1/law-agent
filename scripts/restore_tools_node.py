import re

file_path = r'e:\law\agents\core\graph_agent.py'

tools_node_code = r'''    def tools_node(state: AgentState):
        """
        🔧 Tool Execution Node
        Executes tools requested by the agent
        """
        messages = state['messages']
        last_message = messages[-1]
        context_mgr = state.get('context_manager')
        
        outputs = []
        
        if hasattr(last_message, 'tool_calls'):
            for tool_call in last_message.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_id = tool_call['id']
                
                # Auto-inject context into parameters
                if context_mgr:
                    tool_args = context_mgr.inject_context_into_params(tool_args)
                    logger.info(f"🔧 Executing {tool_name} with auto-filled params")
                
                try:
                    if tool_name in tools_map:
                        tool_func = tools_map[tool_name]
                        result = tool_func.invoke(tool_args) if hasattr(tool_func, 'invoke') else tool_func(**tool_args)
                        
                        # Register created entities
                        if context_mgr and isinstance(result, dict) and "id" in result:
                            # Heuristic: created entity type from tool name
                            entity_type = tool_name.replace("create_", "").replace("add_", "")
                            entity_name = result.get("full_name") or result.get("title") or result.get("name", "Unknown")
                            context_mgr.register_entity(
                                entity_type=entity_type, 
                                entity_id=result["id"], 
                                entity_name=entity_name, 
                                metadata=result
                            )
                        
                        outputs.append(
                            ToolMessage(
                                content=json.dumps(result, ensure_ascii=False),
                                tool_call_id=tool_id
                            )
                        )
                    else:
                        outputs.append(ToolMessage(content=f"Error: Unknown tool {tool_name}", tool_call_id=tool_id))
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    outputs.append(ToolMessage(content=f"Error: {str(e)}", tool_call_id=tool_id))
        
        return {"messages": outputs}

'''

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Insert before route_after_execution
if "def tools_node" not in content:
    print("tools_node missing, inserting...")
    pattern = r'(\s+def route_after_execution)'
    
    match = re.search(pattern, content)
    if match:
        # Insert before match
        new_content = content.replace(match.group(1), '\n' + tools_node_code + match.group(1))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Insertion successful!")
    else:
        print("Could not find route_after_execution to verify.")
else:
    print("tools_node already exists.")
