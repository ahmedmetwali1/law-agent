import re

file_path = r'e:\law\agents\core\graph_agent.py'

new_function = r'''    def analyze_request_node(state: AgentState):
        """
        🧠 Analyst Node - Enhanced with Multi-Entity Detection
        Analyzes user intent and query complexity with smart entity recognition
        """
        messages = state['messages']
        last_user_msg = messages[-1].content if messages else ""
        
        # ✅ Update UI status
        # Note: session_id is captured from closure in create_graph_agent
        update_session_status(session_id, "🧠 تحليل النية...")
        start_time = time.time()
        
        # Enhanced classification prompt
        classification_prompt = f"""أنت محلل ذكي للطلبات القانونية.

سؤال المستخدم:
"{last_user_msg}"

حلل هذا الطلب وصنفه:

**قواعد التصنيف:**

1. **SIMPLE** - طلب واحد بسيط بدون إنشاء كيانات أو بحث معقد:
   - "اعرض القضايا"
   - "ابحث عن موكل اسمه أحمد"
   - "ما هي الجلسات القادمة؟"

2. **MODERATE** - إنشاء كيان واحد أو استعلام محدد:
   - "أضف موكل جديد اسمه أحمد"
   - "أنشئ قضية عمالية"
   - "ابحث في القوانين عن موضوع معين"

3. **COMPLEX** - طلبات متعددة أو وجود تبعيات (dependencies):
   - "أضف موكل + أنشئ له قضية" (← 2 كيانات مترابطة)
   - "أضف موكل ثم قضية ثم جلسة" (← 3 خطوات متتالية)
   - "أنشئ قضية للموكل الأخير" (← يحتاج سياق)

**الكيانات الأساسية:**
- client (موكل)
- case (قضية)
- hearing (جلسة)
- task (مهمة)
- document (مستند)

**تحديد التبعيات:**
- إنشاء قضية يحتاج موكل (case depends on client)
- إنشاء جلسة يحتاج قضية (hearing depends on case)
- إنشاء مهمة قد يحتاج قضية (task may depend on case)

أجب بـ JSON فقط بصيغة صارمة:
{{
  "complexity": "simple|moderate|complex",
  "intent": "add_client|add_case|search|list|admin_task|legal_research",
  "entities_mentioned": ["client", "case"],
  "steps_required": 2,
  "has_dependencies": true,
  "reasoning": "شرح مختصر بالعربية"
}}"""

        try:
            # Call LLM for classification
            llm_analyst = ChatOpenAI(
                base_url=settings.openwebui_api_url,
                api_key=settings.openwebui_api_key or "sk-placeholder",
                model=settings.openwebui_model,
                temperature=0.3
            )
            
            response = llm_analyst.invoke([
                SystemMessage(content="You are a legal request analyzer. Respond ONLY with valid JSON."),
                HumanMessage(content=classification_prompt)
            ])
            
            # Parse response
            import json
            result_text = response.content.strip()
            result_text = strip_markdown_json(result_text)
            
            try:
                result = json.loads(result_text)
            except Exception:
                logger.warning(f"Failed to parse JSON: {result_text}")
                import re
                json_match = re.search(r'\{[^{}]*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError("Could not find JSON object")

            complexity_str = result.get('complexity', 'simple').lower()
            entities = result.get('entities_mentioned', [])
            steps = result.get('steps_required', 1)
            has_deps = result.get('has_dependencies', False)
            reasoning = result.get('reasoning', '')
            
            # Map complexity
            if complexity_str == 'complex':
                complexity_enum = QueryComplexity.COMPLEX
            elif complexity_str == 'moderate':
                complexity_enum = QueryComplexity.MODERATE
            else:
                complexity_enum = QueryComplexity.SIMPLE
            
            # Create decision object
            decision = CognitiveDecision(
                complexity=complexity_enum,
                intent=IntentType.ADMIN_TASK,
                reasoning=reasoning,
                needs_deep_thinking=(complexity_enum == QueryComplexity.COMPLEX or has_deps),
                confidence=0.9
            )
            
            # Store advanced metadata in reasoning for Planner to use
            decision.reasoning += f" | Entities: {entities} | Steps: {steps} | Deps: {has_deps}"
            
            # Update session status
            update_session_status(session_id, f"🧠 تحليل: {complexity_str}")
            
            elapsed = time.time() - start_time
            logger.info(f"🧠 Analyst: {complexity_str} (Entities: {len(entities)}, Deps: {has_deps}) - {elapsed:.2f}s")
            
            return {
                "cognitive_decision": decision.model_dump(),
                "scratchpad": [f"Analysis: {complexity_str} | Entities: {entities}"]
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            fallback_decision = CognitiveDecision(
                complexity=QueryComplexity.SIMPLE,
                intent=IntentType.ADMIN_TASK,
                needs_deep_thinking=False,
                reasoning=f"Fallback due to error: {str(e)}"
            )
            return {"cognitive_decision": fallback_decision.model_dump()}'''

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match the existing analyze_request_node function
# Matches from 'def analyze_request_node' until 'def create_plan_node'
pattern = r'(    def analyze_request_node\(state: AgentState\):.*?)(\n\s+def create_plan_node)'

# Check if pattern exists
match = re.search(pattern, content, re.DOTALL)
if match:
    print("Found analyze_request_node, replacing...")
    new_content = content.replace(match.group(1), new_function)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replacement successful!")
else:
    print("Could not find analyze_request_node function block.")
