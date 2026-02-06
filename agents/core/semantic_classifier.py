"""
🎯 Semantic Complexity Classifier

بدلاً من الاعتماد على keywords جامدة، نستخدم LLM للفهم السياقي.
"""

import asyncio
import json
import re
import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)

# ==================== SEMANTIC ANALYSIS PROMPT ====================

COMPLEXITY_ANALYSIS_PROMPT = """
أنت خبير تصنيف الاستفسارات القانونية حسب التعقيد.

## الاستفسار:
{query}

## السياق السابق (إن وُجد):
{context}

---

## المهمة:

صنّف هذا الاستفسار حسب مستوى التعقيد:

### 1️⃣ بسيط (simple):
**الخصائص:**
- سؤال مباشر عن مادة قانونية محددة
- طلب تعريف أو معلومة واضحة
- سؤال إجرائي بسيط (كيف أثبت؟ ما الإجراءات؟)
- استفسار عن مفهوم قانوني واحد

**أمثلة:**
- "ما هي شروط الهبة؟"
- "كيف يتم إثبات الهبة؟"
- "ما تعريف العقد؟"
- "المادة 375 عن إيه؟"

---

### 2️⃣ متوسط (medium):
**الخصائص:**
- يحتاج تحليل عدة مواد قانونية
- مقارنة بين أحكام مختلفة
- سؤال عن تطبيق عملي لقاعدة قانونية
- استفسار متعدد الجوانب

**أمثلة:**
- "ما الفرق بين الهبة والوصية؟"
- "كيف أطبق المادة 375 في حالتي؟"
- "ما إجراءات الرجوع في الهبة العقارية؟"

---

### 3️⃣ معقد (complex):
**الخصائص:**
- يحتاج استراتيجية قانونية كاملة
- تحليل متعدد الأبعاد (قانوني + عملي + زمني)
- استشارة شاملة لقضية أو موقف
- يتطلب تخطيط ووثائق

**أمثلة:**
- "أحتاج استراتيجية للتعامل مع قضية..."
- "كيف أحمي نفسي قانونياً في هذا الموقف..."
- "ساعدني في بناء خطة قانونية..."

---

## الصيغة المطلوبة (JSON):

**CRITICAL: Return ONLY valid JSON - no markdown, no explanations.**

```json
{{
  "complexity": "simple",
  "confidence": 0.95,
  "reasoning": "سؤال مباشر عن معلومة محددة",
  "estimated_time": "15s"
}}
```

**complexity values:** "simple" | "medium" | "complex"  
**confidence:** 0.0 - 1.0 (ثقتك في التصنيف)  
**estimated_time:** تقدير الوقت المطلوب

---

ابدأ التصنيف الآن:
"""


# ==================== HELPER FUNCTIONS ====================

def _is_obviously_simple(query: str) -> bool:
    """
    Fast heuristics للـ obviously simple queries
    
    Returns True إذا كان السؤال بسيط بوضوح (بدون حاجة لـ LLM)
    """
    query_lower = query.lower().strip()
    words = query.split()
    
    # 1. Very short queries (≤ 8 words) often simple
    if len(words) <= 8:
        # Direct question patterns
        simple_starts = [
            "ما هو", "ما هي", "من هو", "من هي",
            "كيف يتم", "متى يتم", "أين",
            "ماذا", "هل يجوز", "هل يمكن"
        ]
        
        if any(query_lower.startswith(start) for start in simple_starts):
            return True
    
    # 2. Direct article reference (e.g., "المادة 375")
    if re.search(r"المادة\s+\d+", query_lower):
        # If query is JUST asking about the article
        if len(words) <= 10:
            return True
    
    # 3. Definition requests
    definition_patterns = [
        r"ما\s+(هو|هي)\s+تعريف",
        r"تعريف\s+\w+",
        r"معنى\s+\w+"
    ]
    
    if any(re.search(p, query_lower) for p in definition_patterns):
        return True
    
    return False


def _is_obviously_complex(query: str) -> bool:
    """
    Fast heuristics للـ obviously complex queries
    
    Returns True إذا كان السؤال معقد بوضوح
    """
    query_lower = query.lower()
    
    # 1. Strategy/planning keywords
    complex_keywords = [
        "استراتيجية", "خطة", "كيف أتعامل", "ماذا أفعل",
        "ساعدني في", "محتاج مشورة", "قضية", "موقف قانوني",
        "حماية قانونية", "دفاع", "اتخاذ إجراء"
    ]
    
    if any(kw in query_lower for kw in complex_keywords):
        return True
    
    # 2. Very long queries (> 40 words) often complex
    if len(query.split()) > 40:
        return True
    
    # 3. Multiple questions (contains "و" + question words multiple times)
    question_words = ["كيف", "ماذا", "ما", "هل", "متى", "أين"]
    question_count = sum(1 for qw in question_words if qw in query_lower)
    
    if question_count >= 3:  # 3+ questions in one → complex
        return True
    
    return False


async def _classify_complexity_semantic(
    query: str,
    context: Dict[str, Any],
    llm
) -> Dict[str, Any]:
    """
    استخدام LLM للتصنيف السياقي
    
    Returns:
        {
            "complexity": "simple|medium|complex",
            "confidence": 0.0-1.0,
            "reasoning": "...",
            "estimated_time": "..."
        }
    """
    
    # Format context
    context_str = "لا يوجد سياق سابق"
    if context and context.get("facts_snapshot"):
        facts = context.get("facts_snapshot", {})
        context_str = json.dumps(facts, ensure_ascii=False, indent=2)[:300]
    
    prompt = COMPLEXITY_ANALYSIS_PROMPT.format(
        query=query,
        context=context_str
    )
    
    try:
        response = await asyncio.wait_for(
            llm.ainvoke([SystemMessage(content=prompt)]),
            timeout=5  # Fast classification (5s max)
        )
        
        # Parse JSON (handle markdown if present)
        content = response.content.strip()
        
        # Strip markdown if present
        if content.startswith("```json"):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1])
        elif content.startswith("```"):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1])
        
        result = json.loads(content)
        
        # Validate
        if "complexity" not in result:
            raise ValueError("Missing 'complexity' field")
        
        return result
        
    except asyncio.TimeoutError:
        logger.warning("⏱️ Semantic classification timeout - defaulting to medium")
        return {
            "complexity": "medium",
            "confidence": 0.5,
            "reasoning": "Timeout - defaulted to medium",
            "estimated_time": "30s"
        }
        
    except Exception as e:
        logger.error(f"❌ Semantic classification failed: {e}")
        return {
            "complexity": "medium",
            "confidence": 0.5,
            "reasoning": f"Error: {str(e)} - defaulted to medium",
            "estimated_time": "30s"
        }


# ==================== MAIN FUNCTION ====================

async def determine_complexity_hybrid(
    query: str,
    context: Dict[str, Any],
    llm
) -> str:
    """
    🎯 Hybrid Approach: Fast heuristics + Semantic LLM
    
    Returns: "simple" | "medium" | "complex"
    """
    
    # ===== PHASE 1: Fast Heuristics (0.001s) =====
    
    # Check if obviously simple
    if _is_obviously_simple(query):
        logger.info(f"⚡ Fast classification: SIMPLE (heuristic)")
        return "simple"
    
    # Check if obviously complex
    if _is_obviously_complex(query):
        logger.info(f"⚡ Fast classification: COMPLEX (heuristic)")
        return "complex"
    
    # ===== PHASE 2: Semantic LLM (5s) =====
    
    logger.info(f"🧠 Uncertain - using semantic classification...")
    
    result = await _classify_complexity_semantic(query, context, llm)
    
    complexity = result.get("complexity", "medium")
    confidence = result.get("confidence", 0.5)
    reasoning = result.get("reasoning", "No reasoning")
    
    logger.info(f"🎯 Semantic classification: {complexity.upper()} (confidence: {confidence:.2f})")
    logger.info(f"   Reasoning: {reasoning}")
    
    return complexity


# ==================== EXPORT ====================

__all__ = [
    "determine_complexity_hybrid",
    "COMPLEXITY_ANALYSIS_PROMPT"
]
