import re

file_path = r'e:\law\agents\core\graph_agent.py'

new_planner = r'''    def create_plan_node(state: AgentState):
        """
        📋 Planner Node - Creates execution strategy
        Only runs for MODERATE/COMPLEX queries
        """
        # ✅ Update UI status
        update_session_status(session_id, "📋 جاري التخطيط...")
        
        try:
            decision_data = state.get('cognitive_decision', {})
            # Deserialize if needed
            if isinstance(decision_data, dict):
                decision = CognitiveDecision(**decision_data)
            else:
                decision = decision_data
                
            messages = state['messages']
            last_msg = messages[-1].content
            
            # Smart Context Injection
            context_manager = state.get('context_manager')
            context_summary = context_manager.get_context_summary() if context_manager else "لا يوجد سياق"
            
            planning_prompt = f"""أنت مخطط استراتيجي لنظام قانوني.
            
طلب المستخدم: "{last_msg}"

تحليل المحلل:
- التعقيد: {decision.complexity}
- الاستنتاج: {decision.reasoning}

السياق الحالي:
{context_summary}

المهمة: قم بإنشاء خطة تنفيذية (JSON) لتحقيق الطلب.

**قواعد التخطيط:**
1. قسّم الطلب إلى خطوات متسلسلة منطقياً.
2. **الترتيب إجباري**: (مثال: إنشاء موكل أولاً ← ثم إنشاء قضية ← ثم جلسة).
3. استخدم أسماء الأدوات الدقيقة:
   - `create_client` (لإضافة موكل)
   - `create_case` (لإضافة قضية)
   - `create_hearing` (لإضافة جلسة)
   - `search_clients` (للبحث)
   
4. **الربط بين الخطوات**:
   - إذا أنشأت موكلاً في الخطوة 1، استخدم `{{STEP_1_RESULT}}` كـ `client_id` في الخطوة 2.
   - هذا ضروري لربط القضية بالموكل الجديد.

5. **استخراج البيانات**:
   - استخرج كل البيانات المتاحة من النص (الاسم، الهوية، الجوال، رقم القضية، المحكمة).
   - لا تترك حقولاً فارغة إذا كانت موجودة في النص.

أجب بـ JSON فقط بصيغة `ExecutionPlan`:
{{
  "steps": [
    {{
      "step_number": 1,
      "action": "create_client",
      "parameters": {{
        "full_name": "...",
        "phone": "...",
        "lawyer_id": "{{AUTO}}"
      }},
      "reasoning": "إنشاء الموكل أولاً للحصول على ID"
    }},
    {{
      "step_number": 2,
      "action": "create_case",
      "parameters": {{
        "client_id": "{{STEP_1_RESULT}}",
        "case_number": "...",
        "case_type": "...",
        "lawyer_id": "{{AUTO}}"
      }},
      "reasoning": "إنشاء القضية وربطها بالموكل"
    }}
  ],
  "strategy": "تسلسلي: موكل ← قضية"
}}"""

            # Call LLM
            llm_planner = ChatOpenAI(
                base_url=settings.openwebui_api_url,
                api_key=settings.openwebui_api_key or "sk-placeholder",
                model=settings.openwebui_model,
                temperature=0.2  # Low temp for precise planning
            )
            
            response = llm_planner.invoke([
                SystemMessage(content="You are a strict execution planner. Respond ONLY with valid JSON."),
                HumanMessage(content=planning_prompt)
            ])
            
            # Parse JSON safely
            plan_text = response.content.strip()
            plan_text = strip_markdown_json(plan_text)
            
            import json
            try:
                plan_dict = json.loads(plan_text)
            except Exception:
                # Retry regex extraction
                import re
                json_match = re.search(r'\{[^{}]*\}', plan_text, re.DOTALL)
                if json_match:
                    plan_dict = json.loads(json_match.group())
                else:
                    raise ValueError("Planner failed to produce valid JSON")
            
            # Validate against model
            plan = ExecutionPlan(**plan_dict)
            
            logger.info(f"📋 Planner created {len(plan.steps)} steps: {plan.strategy}")
            
            return {
                "execution_plan": plan.model_dump(),
                "scratchpad": [f"Plan created: {plan.strategy}"]
            }
            
        except Exception as e:
            logger.error(f"❌ Planner failed: {e}")
            # Fallback to direct execution (let the simple executor handle it attempt)
            return {
                "execution_plan": None,
                "scratchpad": [f"Planning failed: {str(e)}"]
            }'''

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match create_plan_node until execute_node
pattern = r'(    def create_plan_node\(state: AgentState\):.*?)(\n\s+def execute_node)'

match = re.search(pattern, content, re.DOTALL)
if match:
    print("Found create_plan_node, replacing...")
    new_content = content.replace(match.group(1), new_planner)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replacement successful!")
else:
    print("Could not find create_plan_node function block.")
