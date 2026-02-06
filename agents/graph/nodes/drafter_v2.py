"""
✍️ Drafter V2 - Structured Legal Document Generator

الميزات:
✅ Planning Phase: بناء outline منظم
✅ Writing Phase: كتابة section بـ section
✅ Validation Phase: التحقق من الجودة
✅ Revision Phase: إعادة كتابة الأجزاء الضعيفة
✅ Assembly Phase: تجميع النص النهائي
"""

from typing import Dict, Any, List
import json
import uuid
import logging
import asyncio  # ✅ PHASE 1: For timeout protection
from langchain_core.messages import SystemMessage

from .. state import AgentState
from agents.core.llm_factory import get_llm
from ...tools.legal_blackboard_tool import LegalBlackboardTool

logger = logging.getLogger(__name__)
blackboard = LegalBlackboardTool()


# ==================== PROMPTS ====================

PLANNER_PROMPT = """
أنت مخطط المستندات القانونية - خبير في تنظيم الوثائق القانونية.

## الاستراتيجية المقترحة:
{strategy}

## السياق:
شريكك المحامي: {lawyer_name}
الدولة/النظام: {user_country_id}
{facts}

## البحث القانوني:
{research}

---

## المهمة:

قم ببناء **هيكل منظم** للمستند النهائي على شكل أقسام واضحة، بما يتوافق مع الأنظمة المرعية في **{user_country_id}**.

**الصيغة المطلوبة (JSON):**

```json
{{
  "sections": [
    {{
      "title": "عنوان القسم",
      "purpose": "الهدف من هذا القسم",
      "key_points": ["النقطة 1", "النقطة 2"],
      "estimated_length": "قصير/متوسط/طويل"
    }}
  ],
  "structure_notes": "ملاحظات عامة عن الهيكل"
}}
```

**معايير:**
1. الأقسام يجب أن تكون **منطقية ومتسلسلة**
2. كل قسم له **هدف واضح**
3. التنوع في الطول حسب الأهمية
4. عدد الأقسام: **3-7 أقسام**

**أمثلة على أقسام:**
- المقدمة والخلفية
- التحليل القانوني
- الأسس النظامية
- التوصيات
- الخلاصة

ابدأ الآن:
"""

WRITER_PROMPT = """
أنت كاتب المستندات القانونية - خبير في الكتابة القانونية الاحترافية.

## القسم المطلوب كتابته:
## القسم المطلوب كتابته:
**العنوان:** {section_title}
**الهدف:** {section_purpose}
**النقاط الرئيسية:** {section_points}

**السياق:** محامي: {lawyer_name} | دولة: {user_country_id}

## الاستراتيجية:
{strategy}

## البحث القانوني:
{research}

---

## المهمة:

اكتب هذا القسم بشكل احترافي.

**معايير الكتابة:**

1. **اللغة:**
   - عربية فصيحة احترافية
   - مصطلحات قانونية دقيقة
   - جمل واضحة ومباشرة

2. **المحتوى:**
   - الالتزام بالـ purpose المحدد
   - تغطية كل النقاط الرئيسية
   - الاستشهاد بالمراجع القانونية (المادة X من نظام...)
   - ربط التحليل بالواقع

3. **الطول:**
   - **قصير:** 100-200 كلمة
   - **متوسط:** 200-400 كلمة
   - **طويل:** 400-600 كلمة

4. **التنسيق:**
   - استخدم نقاط bullet إذا لزم الأمر
   - استخدم أرقام للخطوات المتسلسلة
   - اذكر المراجع بوضوح

---

**ابدأ الكتابة الآن (النص مباشرة بدون JSON):**
"""

VALIDATOR_PROMPT = """
أنت مُدقق المستندات القانونية - خبير في مراجعة الجودة.

## القسم المطلوب تدقيقه:
**العنوان:** {section_title}

## المحتوى:
{section_content}

## الهدف المفترض:
{section_purpose}

---

## المهمة:

قيّم هذا القسم من 3 جوانب:

### 1. الصلة بالهدف (Relevance):
   هل المحتوى يحقق الهدف المطلوب؟

### 2. الدقة القانونية (Accuracy):
   هل المراجع صحيحة؟ هل هناك أخطاء قانونية؟

### 3. جودة الكتابة (Quality):
   هل اللغة احترافية؟ هل الأفكار واضحة؟

---

**الصيغة المطلوبة (JSON):**

**CRITICAL: Return ONLY valid JSON - no markdown, no code blocks, no explanations.**

```json
{{
  "valid": true/false,
  "scores": {{
    "relevance": 0-10,
    "accuracy": 0-10,
    "quality": 0-10
  }},
  "issues": [
    "المشكلة 1",
    "المشكلة 2"
  ],
  "suggestions": [
    "اقتراح التحسين 1",
    "اقتراح التحسين 2"
  ],
  "decision": "قبول/إعادة كتابة/تعديل طفيف"
}}
```

**معايير القبول:**
- `valid = true` إذا كانت كل `scores >= 7`
- `valid = false` إذا أي `score < 7`

ابدأ التدقيق:
"""

REWRITER_PROMPT = """
أنت مُعيد كتابة المستندات القانونية - خبير في التحسين.

## النص الأصلي:
{original_content}

## المشاكل المكتشفة:
{issues}

## الاقتراحات:
{suggestions}

---

## المهمة:

أعد كتابة هذا القسم **mُعالجاً كل المشاكل** وتطبيقاً للاقتراحات.

**تذكر:**
- احتفظ بما هو جيد
- أصلح ما هو سيء
- حسّن ما يمكن تحسينه

**النص الجديد (مباشرة بدون JSON):**
"""


# ==================== NODE ====================

async def drafter_v2_node(state: AgentState) -> Dict[str, Any]:
    """
    ✍️ Drafter V2: Structured + Validated Document Generator
    
    Pipeline:
    1. Planning: بناء outline
    2. Writing: كتابة section بـ section
    3. Validation: تدقيق كل section
    4. Revision: إعادة كتابة الضعيف
    5. Assembly: تجميع النص النهائي
    """
    logger.info("=" * 100)
    logger.info("✍️ DRAFTER V2: Structured Legal Document Generator")
    logger.info("=" * 100)
    
    # 1. Session Management
    session_id = state.get("session_id") or str(uuid.uuid4())
    if not state.get("session_id"):
        state["session_id"] = session_id
    
    # 2. Load Context
    current_board = blackboard.read_latest_state(session_id)
    if not current_board:
        current_board = blackboard.initialize_state(session_id)
    
    status = current_board.get("workflow_status", {})
    drafter_status = status.get("drafter", "PENDING")
    
    # 3. Check if already done
    if drafter_status == "DONE":
        logger.info("✅ Drafter already completed - skipping")
        final_output = current_board.get("final_output", "")
        
        return {
            "next_agent": "judge",
            "final_response": final_output,
            "conversation_stage": "DRAFTING_COMPLETE"
        }
    
    # 4. Prepare Inputs
    strategy = current_board.get("debate_strategy", {})
    facts = current_board.get("facts_snapshot", {})
    research = current_board.get("research_data", {})
    
    facts_text = json.dumps(facts, ensure_ascii=False, indent=2)
    research_text = _format_research(research)
    strategy_text = json.dumps(strategy, ensure_ascii=False, indent=2)
    
    # Prepare lawyer context
    user_context = state.get("context", {}).get("user_context", {})
    lawyer_name = user_context.get("full_name", "المحامي")
    user_country_id = user_context.get("country_id", "غير محدد")

    # ===== PHASE 1: PLANNING =====
    logger.info("📋 Phase 1: Planning Document Structure...")
    
    logger.info("📋 Phase 1: Planning Document Structure...")
    
    plan = await _plan_document(strategy_text, facts_text, research_text, lawyer_name, user_country_id)
    
    logger.info(f"✅ Plan created: {len(plan.get('sections', []))} sections")
    
    # حفظ الخطة
    blackboard.update_segment(session_id, "drafting_plan", plan)
    
    # ===== PHASE 2: WRITING =====
    logger.info("📝 Phase 2: Writing Sections...")
    
    sections_content = await _write_sections(
        plan.get("sections", []),
        strategy_text,
        research_text,
        lawyer_name,
        user_country_id
    )
    
    logger.info(f"✅ Wrote {len(sections_content)} sections")
    
    # ===== PHASE 3: VALIDATION =====
    logger.info("🔍 Phase 3: Validating Quality...")
    
    validated_sections = await _validate_and_revise(sections_content)
    
    logger.info(f"✅ Validated {len(validated_sections)} sections")
    
    # ===== PHASE 4: ASSEMBLY =====
    logger.info("🔧 Phase 4: Assembling Final Document...")
    
    final_output = _assemble_document(validated_sections)
    
    logger.info(f"✅ Final document: {len(final_output)} characters")
    
    # 5. Save to Blackboard
    blackboard.update_segment(
        session_id,
        "final_output",
        final_output,
        status_update={"drafter": "DONE"}
    )
    
    logger.info("💾 Document saved to Blackboard")
    logger.info("🔄 Routing to Judge...")
    
    # 6. Return
    return {
        "next_agent": "judge",
        "final_response": final_output,
        "conversation_stage": "DRAFTING_COMPLETE"
    }


# ==================== HELPER FUNCTIONS ====================

async def _plan_document(strategy: str, facts: str, research: str, lawyer_name: str, user_country_id: str) -> Dict:
    """Planning Phase"""
    
    llm = get_llm(temperature=0.2, json_mode=True)
    
    prompt = PLANNER_PROMPT.format(
        strategy=strategy,
        facts=facts,
        research=research,
        lawyer_name=lawyer_name,
        user_country_id=user_country_id
    )
    
    # ✅ PHASE 1 FIX: Timeout for planning
    PLANNING_TIMEOUT = 30  # seconds (was 20s - increased by 50%)
    
    try:
        response = await asyncio.wait_for(
            llm.ainvoke([SystemMessage(content=prompt)]),
            timeout=PLANNING_TIMEOUT
        )
        plan = json.loads(response.content)
        
        return plan
    
    except asyncio.TimeoutError:
        logger.error(f"⏱️ Planning timeout after {PLANNING_TIMEOUT}s")
        # Use fallback plan
        return {
            "sections": [
                {"title": "المقدمة", "purpose": "تقديم السياق", "key_points": [], "estimated_length": "قصير"},
                {"title": "التحليل القانوني", "purpose": "التحليل", "key_points": [], "estimated_length": "متوسط"},
                {"title": "الخلاصة", "purpose": "الخلاصة", "key_points": [], "estimated_length": "قصير"}
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Planning failed: {e}")
        # Same fallback
        return {
            "sections": [
                {"title": "المقدمة", "purpose": "تقديم السياق", "key_points": [], "estimated_length": "قصير"},
                {"title": "التحليل القانوني", "purpose": "التحليل", "key_points": [], "estimated_length": "متوسط"},
                {"title": "الخلاصة", "purpose": "الخلاصة", "key_points": [], "estimated_length": "قصير"}
            ]
        }


async def _write_sections(sections: List[Dict], strategy: str, research: str, lawyer_name: str, user_country_id: str) -> Dict[str, str]:
    """Writing Phase"""
    
    llm = get_llm(temperature=0.4)
    sections_content = {}
    
    # ✅ PHASE 1 FIX: Timeout for section writing
    WRITING_TIMEOUT = 20  # seconds per section (was 15s - increased by 33%)
    
    for section in sections:
        title = section.get("title", "قسم")
        purpose = section.get("purpose", "")
        points = section.get("key_points", [])
        
        logger.info(f"  ✍️ Writing: {title}")
        
        prompt = WRITER_PROMPT.format(
            section_title=title,
            section_purpose=purpose,
            section_points=json.dumps(points, ensure_ascii=False),
            strategy=strategy,
            research=research,
            lawyer_name=lawyer_name,
            user_country_id=user_country_id
        )
        
        try:
            response = await asyncio.wait_for(
                llm.ainvoke([SystemMessage(content=prompt)]),
                timeout=WRITING_TIMEOUT
            )
            sections_content[title] = response.content
        
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Writing {title} timeout after {WRITING_TIMEOUT}s")
            sections_content[title] = f"[تم تجاوز الوقت المحدد لكتابة {title}]"
            
        except Exception as e:
            logger.error(f"❌ Writing {title} failed: {e}")
            sections_content[title] = f"[خطأ في كتابة {title}]"
    
    return sections_content


async def _validate_and_revise(sections: Dict[str, str]) -> Dict[str, str]:
    """Validation + Revision Phase"""
    
    validator_llm = get_llm(temperature=0.1, json_mode=True)
    writer_llm = get_llm(temperature=0.4)
    
    validated = {}
    
    for title, content in sections.items():
        logger.info(f"  🔍 Validating: {title}")
        
        # Validation
        val_prompt = VALIDATOR_PROMPT.format(
            section_title=title,
            section_content=content,
            section_purpose="تحليل قانوني"  # يمكن تحسينه
        )
        
        try:
            val_res = await asyncio.wait_for(
                validator_llm.ainvoke([SystemMessage(content=val_prompt)]),
                timeout=15  # ✅ PHASE 1: Add validation timeout
            )
            
            # ✅ BUG FIX #1: Extract JSON from markdown if present
            clean_content = _extract_json_from_response(val_res.content)
            validation = json.loads(clean_content)
            
            if not validation.get("valid", False):
                logger.warning(f"  ⚠️ {title} failed validation - rewriting...")
                
                # Rewrite
                rewrite_prompt = REWRITER_PROMPT.format(
                    original_content=content,
                    issues=json.dumps(validation.get("issues", []), ensure_ascii=False),
                    suggestions=json.dumps(validation.get("suggestions", []), ensure_ascii=False)
                )
                
                rewrite_res = await writer_llm.ainvoke([SystemMessage(content=rewrite_prompt)])
                validated[title] = rewrite_res.content
                
                logger.info(f"  ✅ {title} rewritten")
            else:
                validated[title] = content
                logger.info(f"  ✅ {title} accepted")
        
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Validation {title} timeout - accepting as-is")
            validated[title] = content
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Validation {title} JSON parse failed even after cleaning: {e}")
            logger.debug(f"Raw content: {val_res.content[:200]}")
            # Fallback: assume valid
            validated[title] = content
            
        except Exception as e:
            logger.error(f"❌ Validation {title} failed: {e}")
            validated[title] = content  # استخدم الأصلي
    
    return validated


def _assemble_document(sections: Dict[str, str]) -> str:
    """Assembly Phase"""
    
    assembled = []
    
    for title, content in sections.items():
        assembled.append(f"## {title}\n\n{content}\n")
    
    return "\n".join(assembled)


def _extract_json_from_response(content: str) -> str:
    """
    ✅ BUG FIX #1: Extract JSON from markdown code blocks
    
    LLMs often return JSON wrapped in markdown:
    ```json
    {"key": "value"}
    ```
    
    This function strips the markdown and returns clean JSON.
    """
    content = content.strip()
    
    # Check if wrapped in ```json...```
    if content.startswith("```json"):
        lines = content.split('\n')
        json_lines = []
        in_block = False
        
        for line in lines:
            if line.strip() == "```json":
                in_block = True
                continue
            elif line.strip() == "```":
                break
            elif in_block:
                json_lines.append(line)
        
        return '\n'.join(json_lines).strip()
    
    # Check if wrapped in generic ```...```
    elif content.startswith("```"):
        lines = content.split('\n')
        if len(lines) > 2:
            return '\n'.join(lines[1:-1]).strip()
    
    # Already clean JSON
    return content


def _format_research(research: Dict) -> str:
    """Format research"""
    
    if not research or not research.get("results"):
        return "لا تتوفر نتائج بحث."
    
    formatted = []
    
    for i, r in enumerate(research.get("results", [])[:3], 1):
        content = r.get("content", "")[:300]
        formatted.append(f"[{i}] {content}...")
    
    return "\n\n".join(formatted)


# ==================== EXPORT ====================

__all__ = ["drafter_v2_node"]
