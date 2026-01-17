"""
Advanced Deep Thinking Tool v2.0
أداة التفكير العميق المتقدمة

التحسينات:
1. دمج المنطق الرمزي (PSL)
2. ذاكرة طويلة المدى
3. تقييم الأفكار تلقائياً
4. كشف تناقضات منطقي
5. تعلم من التغذية الراجعة
6. معالجة JSON محسّنة
7. Caching ذكي
8. تتبع سلسلة التفكير
"""

import time
import json
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict
import numpy as np

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS & DATA STRUCTURES
# ============================================================

class ThinkingMode(Enum):
    """أوضاع التفكير"""
    DECOMPOSE = "decompose"
    HYPOTHESIZE = "hypothesize"
    SIMULATE = "simulate"
    BRAINSTORM = "brainstorm"
    CONTRADICTIONS = "contradictions"
    PERSPECTIVES = "perspectives"
    CHALLENGE = "challenge"
    ANALOGICAL = "analogical"      # جديد: القياس
    CAUSAL = "causal"              # جديد: التحليل السببي
    TEMPORAL = "temporal"          # جديد: التحليل الزمني
    FULL = "full"


class IdeaCategory(Enum):
    """تصنيف الأفكار"""
    LEGAL = "legal"
    PROCEDURAL = "procedural"
    CREATIVE = "creative"
    UNCONVENTIONAL = "unconventional"
    RISKY = "risky"


class ContradictionType(Enum):
    """أنواع التناقضات"""
    DIRECT = "direct"          # تناقض مباشر صريح
    IMPLICIT = "implicit"      # تناقض ضمني
    APPARENT = "apparent"      # تناقض ظاهري قابل للحل
    TEMPORAL = "temporal"      # تناقض زمني (كان صحيحاً ثم تغير)


@dataclass
class Viewpoint:
    """وجهة نظر محسّنة"""
    perspective: str
    position: str
    arguments: List[str]
    weaknesses: List[str]
    confidence: float = 0.7
    sources: List[str] = field(default_factory=list)
    
    def strength_score(self) -> float:
        """حساب قوة وجهة النظر"""
        arg_score = min(1.0, len(self.arguments) / 3)
        weak_penalty = min(0.5, len(self.weaknesses) * 0.1)
        return (arg_score - weak_penalty) * self.confidence


@dataclass
class Contradiction:
    """تناقض محسّن"""
    item1: str
    item2: str
    contradiction_type: ContradictionType
    explanation: str
    severity: float  # 0-1
    resolution_suggestion: Optional[str] = None
    is_resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "item1": self.item1,
            "item2": self.item2,
            "type": self.contradiction_type.value,
            "explanation": self.explanation,
            "severity": self.severity,
            "resolution": self.resolution_suggestion,
            "resolved": self.is_resolved
        }


@dataclass
class Idea:
    """فكرة مع تقييم"""
    content: str
    category: IdeaCategory
    potential: float  # 0-1
    feasibility: float  # 0-1
    risk: float  # 0-1
    source_ideas: List[str] = field(default_factory=list)  # الأفكار المبنية عليها
    
    @property
    def score(self) -> float:
        """حساب نقاط الفكرة"""
        return (self.potential * 0.4 + self.feasibility * 0.4 - self.risk * 0.2)


@dataclass
class ThinkingStep:
    """خطوة في التفكير"""
    step_id: int
    mode: ThinkingMode
    input_summary: str
    output_summary: str
    confidence: float
    duration_ms: float
    insights: List[str] = field(default_factory=list)


@dataclass
class ThinkingSession:
    """جلسة تفكير كاملة"""
    session_id: str
    question: str
    context: str
    steps: List[ThinkingStep] = field(default_factory=list)
    ideas: List[Idea] = field(default_factory=list)
    contradictions: List[Contradiction] = field(default_factory=list)
    viewpoints: List[Viewpoint] = field(default_factory=list)
    final_insights: List[str] = field(default_factory=list)
    confidence: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    
    def add_step(self, step: ThinkingStep):
        self.steps.append(step)
    
    def get_summary(self) -> Dict:
        return {
            "session_id": self.session_id,
            "question": self.question[:100],
            "steps_count": len(self.steps),
            "ideas_count": len(self.ideas),
            "contradictions_count": len(self.contradictions),
            "viewpoints_count": len(self.viewpoints),
            "confidence": self.confidence,
            "duration_ms": sum(s.duration_ms for s in self.steps)
        }


# ============================================================
# CACHING & MEMORY
# ============================================================

class ThinkingMemory:
    """ذاكرة التفكير العميق"""
    
    def __init__(self, max_sessions: int = 100):
        self.sessions: Dict[str, ThinkingSession] = {}
        self.idea_bank: List[Idea] = []  # بنك الأفكار
        self.contradiction_patterns: List[Contradiction] = []  # أنماط التناقضات
        self.max_sessions = max_sessions
    
    def store_session(self, session: ThinkingSession):
        """حفظ جلسة"""
        if len(self.sessions) >= self.max_sessions:
            oldest = min(self.sessions.values(), key=lambda s: s.start_time)
            del self.sessions[oldest.session_id]
        
        self.sessions[session.session_id] = session
        
        # إضافة الأفكار الجيدة للبنك
        for idea in session.ideas:
            if idea.score > 0.7:
                self.idea_bank.append(idea)
        
        # حفظ أنماط التناقضات
        self.contradiction_patterns.extend(session.contradictions)
    
    def find_similar_session(self, question: str) -> Optional[ThinkingSession]:
        """البحث عن جلسة مشابهة"""
        # بحث بسيط بالكلمات المشتركة
        question_words = set(question.split())
        
        best_match = None
        best_score = 0
        
        for session in self.sessions.values():
            session_words = set(session.question.split())
            overlap = len(question_words & session_words)
            score = overlap / max(len(question_words), len(session_words))
            
            if score > best_score and score > 0.5:
                best_score = score
                best_match = session
        
        return best_match
    
    def get_relevant_ideas(self, context: str, top_k: int = 5) -> List[Idea]:
        """استرجاع أفكار ذات صلة"""
        # ترتيب حسب النقاط
        sorted_ideas = sorted(self.idea_bank, key=lambda i: i.score, reverse=True)
        return sorted_ideas[:top_k]


class ThinkingCache:
    """كاش للتفكير"""
    
    def __init__(self, max_size: int = 500):
        self.cache: Dict[str, Tuple[Dict, datetime]] = {}
        self.max_size = max_size
        self.ttl_hours = 24
    
    def _hash(self, question: str, mode: str, context: str) -> str:
        key = f"{question}|{mode}|{context[:200]}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, question: str, mode: str, context: str = "") -> Optional[Dict]:
        key = self._hash(question, mode, context)
        if key in self.cache:
            result, timestamp = self.cache[key]
            age = (datetime.now() - timestamp).total_seconds() / 3600
            if age < self.ttl_hours:
                return result
            del self.cache[key]
        return None
    
    def set(self, question: str, mode: str, context: str, result: Dict):
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache, key=lambda k: self.cache[k][1])
            del self.cache[oldest]
        
        key = self._hash(question, mode, context)
        self.cache[key] = (result, datetime.now())


# ============================================================
# LOGICAL CONTRADICTION DETECTOR
# ============================================================

class LogicalContradictionDetector:
    """كاشف التناقضات المنطقي"""
    
    def __init__(self):
        # أنماط التناقض المعروفة
        self.contradiction_patterns = [
            # (نمط 1، نمط 2، نوع التناقض)
            (r"يجوز", r"لا يجوز", ContradictionType.DIRECT),
            (r"يجب", r"لا يجب", ContradictionType.DIRECT),
            (r"صحيح", r"باطل", ContradictionType.DIRECT),
            (r"(\d+) يوم", r"(\d+) يوم", ContradictionType.APPARENT),  # أرقام مختلفة
        ]
    
    def detect(self, items: List[Dict]) -> List[Contradiction]:
        """كشف التناقضات في قائمة المعلومات"""
        contradictions = []
        
        for i, item1 in enumerate(items):
            content1 = item1.get("content", str(item1))
            
            for item2 in items[i+1:]:
                content2 = item2.get("content", str(item2))
                
                # فحص التناقضات المباشرة
                for pattern1, pattern2, ctype in self.contradiction_patterns:
                    if self._matches(content1, pattern1) and self._matches(content2, pattern2):
                        contradictions.append(Contradiction(
                            item1=content1[:200],
                            item2=content2[:200],
                            contradiction_type=ctype,
                            explanation=f"تناقض محتمل بين '{pattern1}' و '{pattern2}'",
                            severity=0.7 if ctype == ContradictionType.DIRECT else 0.4
                        ))
                
                # فحص التناقضات العددية
                num_contradiction = self._check_numerical_contradiction(content1, content2)
                if num_contradiction:
                    contradictions.append(num_contradiction)
        
        return contradictions
    
    def _matches(self, text: str, pattern: str) -> bool:
        """فحص تطابق النمط"""
        import re
        return bool(re.search(pattern, text))
    
    def _check_numerical_contradiction(self, text1: str, text2: str) -> Optional[Contradiction]:
        """فحص التناقضات العددية"""
        import re
        
        # استخراج الأرقام مع سياقها
        pattern = r'(\d+)\s*(يوم|شهر|سنة|ريال|٪)'
        
        matches1 = re.findall(pattern, text1)
        matches2 = re.findall(pattern, text2)
        
        for num1, unit1 in matches1:
            for num2, unit2 in matches2:
                if unit1 == unit2 and num1 != num2:
                    return Contradiction(
                        item1=f"{num1} {unit1}",
                        item2=f"{num2} {unit2}",
                        contradiction_type=ContradictionType.APPARENT,
                        explanation=f"اختلاف في القيمة: {num1} vs {num2} {unit1}",
                        severity=0.5,
                        resolution_suggestion="تحقق من السياق - قد تكون لحالات مختلفة"
                    )
        
        return None


# ============================================================
# IDEA EVALUATOR
# ============================================================

class IdeaEvaluator:
    """مقيّم الأفكار"""
    
    def __init__(self):
        # معايير التقييم
        self.feasibility_keywords = {
            "high": ["ممكن", "سهل", "مباشر", "واضح"],
            "low": ["صعب", "معقد", "نادر", "مستحيل"]
        }
        
        self.risk_keywords = {
            "high": ["خطر", "غرامة", "عقوبة", "رفض"],
            "low": ["آمن", "مضمون", "مؤكد"]
        }
    
    def evaluate(self, idea_text: str, context: str = "") -> Idea:
        """تقييم فكرة"""
        # تحديد الفئة
        category = self._categorize(idea_text)
        
        # حساب الجدوى
        feasibility = self._calculate_feasibility(idea_text)
        
        # حساب المخاطر
        risk = self._calculate_risk(idea_text)
        
        # حساب الإمكانية
        potential = self._calculate_potential(idea_text, context)
        
        return Idea(
            content=idea_text,
            category=category,
            potential=potential,
            feasibility=feasibility,
            risk=risk
        )
    
    def _categorize(self, text: str) -> IdeaCategory:
        """تصنيف الفكرة"""
        legal_keywords = ["دعوى", "محكمة", "قانون", "مادة", "نظام"]
        procedural_keywords = ["إجراء", "خطوة", "تقديم", "رفع"]
        creative_keywords = ["بديل", "جديد", "مبتكر"]
        
        if any(kw in text for kw in legal_keywords):
            return IdeaCategory.LEGAL
        elif any(kw in text for kw in procedural_keywords):
            return IdeaCategory.PROCEDURAL
        elif any(kw in text for kw in creative_keywords):
            return IdeaCategory.CREATIVE
        else:
            return IdeaCategory.UNCONVENTIONAL
    
    def _calculate_feasibility(self, text: str) -> float:
        """حساب الجدوى"""
        score = 0.5
        
        for kw in self.feasibility_keywords["high"]:
            if kw in text:
                score += 0.1
        
        for kw in self.feasibility_keywords["low"]:
            if kw in text:
                score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_risk(self, text: str) -> float:
        """حساب المخاطر"""
        score = 0.3
        
        for kw in self.risk_keywords["high"]:
            if kw in text:
                score += 0.15
        
        for kw in self.risk_keywords["low"]:
            if kw in text:
                score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_potential(self, text: str, context: str) -> float:
        """حساب الإمكانية"""
        # تحليل بسيط
        base_score = 0.5
        
        # زيادة إذا كانت الفكرة مرتبطة بالسياق
        context_words = set(context.split())
        idea_words = set(text.split())
        overlap = len(context_words & idea_words)
        
        relevance_bonus = min(0.3, overlap * 0.05)
        
        return min(1.0, base_score + relevance_bonus)


# ============================================================
# ENHANCED DEEP THINKING TOOL
# ============================================================

class EnhancedDeepThinkingTool(BaseTool):
    """
    أداة التفكير العميق المتقدمة
    
    Features:
    1. All original modes + 3 new ones
    2. Logical contradiction detection
    3. Idea evaluation & ranking
    4. Session memory
    5. Caching
    6. Thinking trace
    7. Multi-step reasoning
    """
    
    def __init__(self, llm_client=None):
        super().__init__(
            name="enhanced_deep_thinking",
            description="تفكير عميق متقدم مع كشف تناقضات منطقي وتقييم أفكار"
        )
        self.llm_client = llm_client
        self.memory = ThinkingMemory()
        self.cache = ThinkingCache()
        self.contradiction_detector = LogicalContradictionDetector()
        self.idea_evaluator = IdeaEvaluator()
        
        self.current_session: Optional[ThinkingSession] = None
    
    def run(
        self,
        question: str,
        context: str = "",
        mode: str = "full",
        gathered_info: Optional[List[Dict]] = None,
        previous_conclusions: Optional[List[str]] = None,
        use_cache: bool = True,
        use_memory: bool = True
    ) -> ToolResult:
        """
        تنفيذ التفكير العميق
        """
        self._track_usage()
        start_time = time.time()
        
        try:
            # Check for trivial queries (Quick Exit)
            if len(question.strip().split()) < 3 and mode != "simulate":
                return ToolResult(
                    success=True,
                    data={"response": "Question too short for deep thinking", "recommendation": "Use direct chat"},
                    metadata={"skipped": True},
                    execution_time_ms=0
                )

            logger.info(f"🧠 EnhancedDeepThinking ({mode}): '{question[:50]}...'")
            
            # فحص الكاش
            if use_cache:
                cached = self.cache.get(question, mode, context)
                if cached:
                    logger.info("⚡ Cache hit")
                    return ToolResult(
                        success=True,
                        data=cached,
                        metadata={"cache_hit": True, "mode": mode},
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
            
            # فحص الذاكرة
            if use_memory:
                similar = self.memory.find_similar_session(question)
                if similar:
                    logger.info(f"💭 Found similar session: {similar.session_id}")
            
            # بدء جلسة جديدة
            session_id = hashlib.md5(f"{question}{time.time()}".encode()).hexdigest()[:10]
            self.current_session = ThinkingSession(
                session_id=session_id,
                question=question,
                context=context
            )
            
            # تنفيذ الوضع المطلوب
            mode_enum = ThinkingMode(mode) if mode in [m.value for m in ThinkingMode] else ThinkingMode.FULL
            
            result = self._execute_mode(
                mode=mode_enum,
                question=question,
                context=context,
                gathered_info=gathered_info or [],
                previous_conclusions=previous_conclusions or []
            )
            
            # حفظ في الكاش والذاكرة
            if use_cache:
                self.cache.set(question, mode, context, result)
            
            if use_memory:
                self.memory.store_session(self.current_session)
            
            elapsed = (time.time() - start_time) * 1000
            
            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "mode": mode,
                    "session_id": session_id,
                    "steps_count": len(self.current_session.steps),
                    "ideas_count": len(self.current_session.ideas),
                    "contradictions_found": len(self.current_session.contradictions),
                    "cache_hit": False
                },
                execution_time_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"❌ EnhancedDeepThinking failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"mode": mode},
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _execute_mode(
        self,
        mode: ThinkingMode,
        question: str,
        context: str,
        gathered_info: List[Dict],
        previous_conclusions: List[str]
    ) -> Dict[str, Any]:
        """تنفيذ الوضع المحدد"""
        
        mode_handlers = {
            ThinkingMode.DECOMPOSE: self._decompose,
            ThinkingMode.HYPOTHESIZE: self._hypothesize,
            ThinkingMode.SIMULATE: self._simulate,
            ThinkingMode.BRAINSTORM: self._brainstorm_enhanced,
            ThinkingMode.CONTRADICTIONS: self._find_contradictions_enhanced,
            ThinkingMode.PERSPECTIVES: self._multi_perspective,
            ThinkingMode.CHALLENGE: self._challenge_assumptions,
            ThinkingMode.ANALOGICAL: self._analogical_reasoning,
            ThinkingMode.CAUSAL: self._causal_analysis,
            ThinkingMode.TEMPORAL: self._temporal_analysis,
            ThinkingMode.FULL: self._full_analysis_enhanced
        }
        
        handler = mode_handlers.get(mode, self._full_analysis_enhanced)
        
        step_start = time.time()
        result = handler(question, context, gathered_info, previous_conclusions)
        step_duration = (time.time() - step_start) * 1000
        
        # تسجيل الخطوة
        self.current_session.add_step(ThinkingStep(
            step_id=len(self.current_session.steps) + 1,
            mode=mode,
            input_summary=question[:100],
            output_summary=str(result)[:200],
            confidence=result.get("confidence", 0.7),
            duration_ms=step_duration,
            insights=result.get("key_insights", [])
        ))
        
        return result
    
    def _decompose(self, question, context, gathered_info, conclusions) -> Dict:
        """تفكيك السؤال"""
        prompt = f"""حلل السؤال التالي وقسمه إلى أسئلة فرعية:

السؤال: {question}
السياق: {context if context else "لا يوجد"}

أجب بـ JSON:
{{
  "main_question": "...",
  "sub_questions": [
    {{"question": "...", "category": "وقائع/قانون/إجراء", "priority": "high/medium/low", "depends_on": []}}
  ],
  "missing_info": ["..."],
  "search_keywords": ["..."],
  "complexity_score": 5
}}"""
        return self._call_llm_json(prompt)
    
    def _hypothesize(self, question, context, gathered_info, conclusions) -> Dict:
        """توليد فرضيات"""
        prompt = f"""ولّد فرضيات للقضية:

القضية: {question}
السياق: {context if context else "لا يوجد"}

أجب بـ JSON:
{{
  "hypotheses": [
    {{
      "id": "H1",
      "statement": "...",
      "probability": 0.7,
      "supporting_evidence": ["..."],
      "contradicting_evidence": ["..."],
      "test_method": "..."
    }}
  ],
  "most_likely": "H1",
  "reasoning": "..."
}}"""
        return self._call_llm_json(prompt)
    
    def _simulate(self, question, context, gathered_info, conclusions) -> Dict:
        """محاكاة سيناريوهات"""
        prompt = f"""ضع سيناريوهات مختلفة:

القضية: {question}
الوقائع: {context if context else "لا يوجد"}

أجب بـ JSON:
{{
  "scenarios": [
    {{
      "id": "S1",
      "name": "...",
      "description": "...",
      "likelihood": 0.7,
      "outcome": "...",
      "pros": ["..."],
      "cons": ["..."],
      "required_actions": ["..."]
    }}
  ],
  "recommended": "S1",
  "comparison_matrix": {{}}
}}"""
        return self._call_llm_json(prompt)
    
    def _brainstorm_enhanced(self, question, context, gathered_info, conclusions) -> Dict:
        """عصف ذهني محسّن مع تقييم"""
        # أولاً: توليد الأفكار
        prompt = f"""عصف ذهني للسؤال (بدون تقييم):

السؤال: {question}
السياق: {context if context else "لا يوجد"}

ولّد أكبر عدد من الأفكار المتنوعة.

أجب بـ JSON:
{{
  "ideas": [
    {{"text": "...", "category": "قانونية/إجرائية/إبداعية/غير تقليدية"}}
  ],
  "wild_ideas": ["..."],
  "combinations": ["..."]
}}"""
        
        raw_result = self._call_llm_json(prompt)
        
        # ثانياً: تقييم الأفكار
        evaluated_ideas = []
        for idea_data in raw_result.get("ideas", []):
            idea = self.idea_evaluator.evaluate(idea_data.get("text", ""), context)
            evaluated_ideas.append({
                "text": idea.content,
                "category": idea.category.value,
                "potential": idea.potential,
                "feasibility": idea.feasibility,
                "risk": idea.risk,
                "score": idea.score
            })
            self.current_session.ideas.append(idea)
        
        # ترتيب حسب النقاط
        evaluated_ideas.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "ideas": evaluated_ideas,
            "top_ideas": evaluated_ideas[:5],
            "wild_ideas": raw_result.get("wild_ideas", []),
            "combinations": raw_result.get("combinations", []),
            "total_ideas": len(evaluated_ideas)
        }
    
    def _find_contradictions_enhanced(self, question, context, gathered_info, conclusions) -> Dict:
        """كشف التناقضات المحسّن"""
        # كشف منطقي أولاً
        logical_contradictions = self.contradiction_detector.detect(gathered_info)
        
        # كشف بـ LLM
        info_text = "\n".join([
            f"- {item.get('content', str(item))[:200]}"
            for item in gathered_info[:10]
        ])
        
        prompt = f"""ابحث عن تناقضات في المعلومات:

السؤال: {question}
المعلومات:
{info_text if info_text else "لا توجد معلومات"}

أجب بـ JSON:
{{
  "contradictions": [
    {{
      "item1": "...",
      "item2": "...",
      "type": "مباشر/ضمني/ظاهري/زمني",
      "explanation": "...",
      "severity": 0.7,
      "resolution": "..."
    }}
  ],
  "consistent_facts": ["..."],
  "needs_verification": ["..."]
}}"""
        
        llm_result = self._call_llm_json(prompt)
        
        # دمج النتائج
        all_contradictions = []
        
        # من الكاشف المنطقي
        for c in logical_contradictions:
            all_contradictions.append(c.to_dict())
            self.current_session.contradictions.append(c)
        
        # من LLM
        for c in llm_result.get("contradictions", []):
            all_contradictions.append(c)
        
        # إزالة التكرارات
        unique = []
        seen = set()
        for c in all_contradictions:
            key = f"{c.get('item1', '')}|{c.get('item2', '')}"
            if key not in seen:
                seen.add(key)
                unique.append(c)
        
        return {
            "contradictions_found": len(unique) > 0,
            "contradictions": unique,
            "logical_detections": len(logical_contradictions),
            "llm_detections": len(llm_result.get("contradictions", [])),
            "consistent_facts": llm_result.get("consistent_facts", []),
            "needs_verification": llm_result.get("needs_verification", [])
        }
    
    def _multi_perspective(self, question, context, gathered_info, conclusions) -> Dict:
        """تحليل متعدد الزوايا"""
        prompt = f"""حلل من وجهات نظر مختلفة:

القضية: {question}
السياق: {context if context else "لا يوجد"}

قدم 4 وجهات نظر: قانونية، عملية، أخلاقية، واقتصادية.

أجب بـ JSON:
{{
  "perspectives": [
    {{
      "viewpoint": "...",
      "position": "...",
      "arguments": ["..."],
      "weaknesses": ["..."],
      "confidence": 0.7,
      "key_sources": ["..."]
    }}
  ],
  "points_of_agreement": ["..."],
  "points_of_conflict": ["..."],
  "synthesis": "...",
  "recommended_position": "..."
}}"""
        
        result = self._call_llm_json(prompt)
        
        # تسجيل وجهات النظر
        for p in result.get("perspectives", []):
            viewpoint = Viewpoint(
                perspective=p.get("viewpoint", ""),
                position=p.get("position", ""),
                arguments=p.get("arguments", []),
                weaknesses=p.get("weaknesses", []),
                confidence=p.get("confidence", 0.7),
                sources=p.get("key_sources", [])
            )
            self.current_session.viewpoints.append(viewpoint)
        
        return result
    
    def _challenge_assumptions(self, question, context, gathered_info, conclusions) -> Dict:
        """تحدي الافتراضات"""
        conclusions_text = "\n".join([f"- {c}" for c in conclusions[:5]])
        
        prompt = f"""كن محامي الشيطان وتحدَّ الاستنتاجات:

السؤال: {question}
الاستنتاجات:
{conclusions_text if conclusions_text else "لا توجد"}

أجب بـ JSON:
{{
  "challenges": [
    {{
      "conclusion": "...",
      "challenge": "...",
      "potential_flaw": "...",
      "counter_argument": "...",
      "severity": 0.7
    }}
  ],
  "hidden_assumptions": ["..."],
  "overlooked_factors": ["..."],
  "stress_test": "...",
  "revised_confidence": 0.6
}}"""
        return self._call_llm_json(prompt)
    
    def _analogical_reasoning(self, question, context, gathered_info, conclusions) -> Dict:
        """التفكير بالقياس - جديد"""
        prompt = f"""قس على حالات مشابهة:

القضية: {question}
السياق: {context if context else "لا يوجد"}

ابحث عن سوابق أو حالات مشابهة وقس عليها.

أجب بـ JSON:
{{
  "similar_cases": [
    {{
      "case": "...",
      "similarity": 0.8,
      "outcome": "...",
      "applicable_rules": ["..."]
    }}
  ],
  "analogy_basis": "وجه الشبه الرئيسي",
  "differences": ["..."],
  "predicted_outcome": "...",
  "confidence": 0.7
}}"""
        return self._call_llm_json(prompt)
    
    def _causal_analysis(self, question, context, gathered_info, conclusions) -> Dict:
        """التحليل السببي - جديد"""
        prompt = f"""حلل العلاقات السببية:

القضية: {question}
السياق: {context if context else "لا يوجد"}

حدد الأسباب والنتائج.

أجب بـ JSON:
{{
  "causal_chain": [
    {{
      "cause": "...",
      "effect": "...",
      "strength": 0.8,
      "evidence": "..."
    }}
  ],
  "root_cause": "...",
  "contributing_factors": ["..."],
  "but_for_test": "لو لم يحدث X لما حدث Y",
  "counterfactual": "..."
}}"""
        return self._call_llm_json(prompt)
    
    def _temporal_analysis(self, question, context, gathered_info, conclusions) -> Dict:
        """التحليل الزمني - جديد"""
        prompt = f"""حلل الجوانب الزمنية:

القضية: {question}
السياق: {context if context else "لا يوجد"}

حدد التواريخ والمواعيد المهمة.

أجب بـ JSON:
{{
  "timeline": [
    {{"event": "...", "date": "...", "significance": "..."}}
  ],
  "deadlines": [
    {{"deadline": "...", "for": "...", "days_remaining": 30, "legal_basis": "..."}}
  ],
  "prescription_issues": ["..."],
  "time_sensitive_actions": ["..."]
}}"""
        return self._call_llm_json(prompt)
    
    def _full_analysis_enhanced(self, question, context, gathered_info, conclusions) -> Dict:
        """تحليل شامل محسّن"""
        results = {}
        
        # 1. تفكيك
        results["decomposition"] = self._decompose(question, context, gathered_info, conclusions)
        
        # 2. فرضيات
        results["hypotheses"] = self._hypothesize(question, context, gathered_info, conclusions)
        
        # 3. وجهات نظر
        results["perspectives"] = self._multi_perspective(question, context, gathered_info, conclusions)
        
        # 4. تناقضات
        if gathered_info:
            results["contradictions"] = self._find_contradictions_enhanced(
                question, context, gathered_info, conclusions
            )
        
        # 5. تحديات
        if conclusions:
            results["challenges"] = self._challenge_assumptions(
                question, context, gathered_info, conclusions
            )
        
        # حساب الثقة الإجمالية
        confidence_scores = [
            results.get("hypotheses", {}).get("most_likely_probability", 0.5),
            results.get("perspectives", {}).get("synthesis_confidence", 0.5)
        ]
        
        overall_confidence = np.mean([c for c in confidence_scores if c > 0])
        
        # تجميع الرؤى
        key_insights = []
        for r in results.values():
            if isinstance(r, dict):
                insights = r.get("key_insights", []) or r.get("insights", [])
                key_insights.extend(insights[:2])
        
        self.current_session.final_insights = key_insights
        self.current_session.confidence = overall_confidence
        
        return {
            "summary": f"تحليل شامل للسؤال: {question[:50]}...",
            "results": results,
            "key_insights": key_insights[:10],
            "confidence": overall_confidence,
            "complexity_score": results.get("decomposition", {}).get("complexity_score", 5),
            "session_id": self.current_session.session_id
        }
    
    def _call_llm_json(self, prompt: str) -> Dict[str, Any]:
        """استدعاء LLM مع معالجة JSON محسّنة"""
        if not self.llm_client:
            return {"error": "No LLM client configured"}
        
        messages = [
            {"role": "system", "content": "أنت محلل قانوني خبير. أجب دائماً بـ JSON صالح فقط."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_client.chat_completion(
            messages=messages,
            temperature=0.5,
            max_tokens=2000
        )
        
        return self._parse_json_response(response)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """معالجة JSON محسّنة"""
        try:
            # محاولة 1: استخراج من code block
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            
            # محاولة 2: استخراج من code block عام
            if "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            
            # محاولة 3: البحث عن {}
            if "{" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                return json.loads(json_str)
            
            # محاولة 4: الاستجابة كاملة
            return json.loads(response.strip())
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed: {e}")
            return {
                "raw_response": response,
                "parse_error": str(e),
                "partial_extraction": self._extract_partial_json(response)
            }
    
    def _extract_partial_json(self, text: str) -> Dict:
        """استخراج جزئي للبيانات"""
        result = {}
        
        # استخراج القوائم
        import re
        list_pattern = r'"(\w+)":\s*\[(.*?)\]'
        for match in re.finditer(list_pattern, text, re.DOTALL):
            key, value = match.groups()
            items = re.findall(r'"([^"]+)"', value)
            result[key] = items
        
        return result
    
    def can_handle(self, query: str) -> float:
        """تقييم القدرة على المعالجة"""
        score = 0.3
        
        # طول السؤال
        if len(query.split()) > 20:
            score += 0.2
        
        # كلمات التعقيد
        complex_keywords = ["إذا", "ما الفرق", "قارن", "لكن", "بالإضافة"]
        if any(kw in query for kw in complex_keywords):
            score += 0.2
        
        # أسئلة
        if "?" in query or "؟" in query:
            score += 0.1
        
        return min(1.0, score)


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

# Alias للتوافق مع الكود القديم
DeepThinkingTool = EnhancedDeepThinkingTool


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "EnhancedDeepThinkingTool",
    "DeepThinkingTool",  # Alias
    "ThinkingMode",
    "Viewpoint",
    "Contradiction",
    "Idea",
    "ThinkingSession"
]
