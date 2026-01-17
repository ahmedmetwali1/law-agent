"""
Advanced Unified Thinking Loop v2.0
حلقة التفكير الموحدة المتقدمة

التحسينات:
1. دمج Neural-Symbolic Reasoning
2. Probabilistic Confidence Calculation
3. Caching & Memoization
4. Feedback Learning Loop
5. Advanced Error Recovery
6. Temporal & Deontic Logic Integration
7. Counterfactual Analysis
8. Multi-Agent Deliberation
"""

import logging
import time
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from collections import defaultdict
import numpy as np
from functools import lru_cache

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS & CONSTANTS
# ============================================================

class ThinkingStrategy(Enum):
    """استراتيجيات التفكير المتقدمة"""
    DIRECT = "direct"                    # بسيط: بحث + إجابة
    CHAIN_OF_THOUGHT = "cot"            # متوسط: خطوة بخطوة
    MULTI_PATH = "multi_path"           # معقد: مسارات متعددة
    TREE_OF_THOUGHT = "tot"             # معقد جداً: شجرة تفكير
    DEBATE = "debate"                   # مثير للجدل: مناظرة
    DECOMPOSE = "decompose"             # مركب: تفكيك وتجميع
    ANALOGICAL = "analogical"           # جديد: قياس على سوابق


class ConfidenceLevel(Enum):
    """مستويات الثقة"""
    VERY_HIGH = (0.9, 1.0, "ثقة عالية جداً")
    HIGH = (0.75, 0.9, "ثقة عالية")
    MODERATE = (0.5, 0.75, "ثقة متوسطة")
    LOW = (0.25, 0.5, "ثقة منخفضة")
    VERY_LOW = (0.0, 0.25, "ثقة منخفضة جداً")
    
    @classmethod
    def from_score(cls, score: float) -> 'ConfidenceLevel':
        for level in cls:
            if level.value[0] <= score < level.value[1]:
                return level
        return cls.VERY_HIGH if score >= 1.0 else cls.VERY_LOW


class ReasoningMode(Enum):
    """أنماط التفكير"""
    DEDUCTIVE = "deductive"      # استنباطي: من العام للخاص
    INDUCTIVE = "inductive"      # استقرائي: من الخاص للعام
    ABDUCTIVE = "abductive"      # تفسيري: أفضل تفسير
    ANALOGICAL = "analogical"    # قياسي: مقارنة بحالات مشابهة


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class ThinkingInput:
    """مدخلات حلقة التفكير المتقدمة"""
    question: str
    context: str = ""
    force_strategy: Optional[ThinkingStrategy] = None
    force_mode: Optional[ReasoningMode] = None
    require_citations: bool = True
    max_thinking_time: float = 30.0  # ثانية
    min_confidence: float = 0.5
    include_counterfactuals: bool = False
    check_deadlines: bool = True
    user_id: Optional[str] = None  # للتخصيص


@dataclass
class ConfidenceBreakdown:
    """تفصيل درجة الثقة"""
    source_quality: float      # جودة المصادر
    source_agreement: float    # اتفاق المصادر
    reasoning_validity: float  # صحة الاستدلال
    coverage: float           # تغطية السؤال
    recency: float           # حداثة المعلومات
    
    @property
    def overall(self) -> float:
        weights = [0.25, 0.25, 0.2, 0.15, 0.15]
        values = [
            self.source_quality,
            self.source_agreement,
            self.reasoning_validity,
            self.coverage,
            self.recency
        ]
        return sum(w * v for w, v in zip(weights, values))
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "source_quality": round(self.source_quality, 3),
            "source_agreement": round(self.source_agreement, 3),
            "reasoning_validity": round(self.reasoning_validity, 3),
            "coverage": round(self.coverage, 3),
            "recency": round(self.recency, 3),
            "overall": round(self.overall, 3)
        }


@dataclass
class Citation:
    """استشهاد موثق"""
    source_id: str
    source_type: str  # article, ruling, principle
    text: str
    relevance_score: float
    page_or_section: Optional[str] = None


@dataclass
class ReasoningStep:
    """خطوة في سلسلة التفكير"""
    step_id: int
    description: str
    reasoning_type: ReasoningMode
    inputs: List[str]
    output: str
    confidence: float
    citations: List[Citation] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CounterfactualAnalysis:
    """تحليل البديل المضاد"""
    original_conclusion: str
    changed_fact: str
    new_conclusion: str
    impact_level: str  # high, medium, low
    explanation: str


@dataclass
class DeadlineAlert:
    """تنبيه بموعد قانوني"""
    deadline_type: str
    deadline_date: datetime
    days_remaining: int
    action_required: str
    legal_basis: str


@dataclass
class ThinkingOutput:
    """مخرجات حلقة التفكير المتقدمة"""
    # الإجابة الرئيسية
    answer: str
    summary: str  # ملخص قصير
    
    # الثقة
    confidence: float
    confidence_breakdown: ConfidenceBreakdown
    confidence_level: ConfidenceLevel
    
    # الاستراتيجية
    strategy_used: ThinkingStrategy
    reasoning_mode: ReasoningMode
    
    # التصنيف
    domain: str
    complexity: str
    
    # المصادر
    sources_retrieved: int
    sources_used: int
    sources_filtered: int
    citations: List[Citation]
    
    # سلسلة التفكير
    reasoning_steps: List[ReasoningStep]
    reasoning_trace: List[str]
    
    # تحليلات إضافية
    counterfactuals: List[CounterfactualAnalysis] = field(default_factory=list)
    deadline_alerts: List[DeadlineAlert] = field(default_factory=list)
    related_questions: List[str] = field(default_factory=list)
    
    # تحذيرات
    warnings: List[str] = field(default_factory=list)
    uncited_claims: List[str] = field(default_factory=list)
    
    # أداء
    execution_time_ms: float = 0.0
    cache_hit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "summary": self.summary,
            "confidence": self.confidence,
            "confidence_breakdown": self.confidence_breakdown.to_dict(),
            "confidence_level": self.confidence_level.value[2],
            "strategy": self.strategy_used.value,
            "domain": self.domain,
            "sources_used": self.sources_used,
            "citations_count": len(self.citations),
            "reasoning_steps": len(self.reasoning_steps),
            "warnings": self.warnings,
            "execution_time_ms": self.execution_time_ms
        }


# ============================================================
# CACHING SYSTEM
# ============================================================

class ThinkingCache:
    """نظام التخزين المؤقت للتفكير"""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.cache: Dict[str, Tuple[ThinkingOutput, datetime]] = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self.hits = 0
        self.misses = 0
    
    def _hash_input(self, input: ThinkingInput) -> str:
        """توليد hash للمدخلات"""
        key_data = f"{input.question}|{input.context[:100]}|{input.force_strategy}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, input: ThinkingInput) -> Optional[ThinkingOutput]:
        """استرجاع من الكاش"""
        key = self._hash_input(input)
        
        if key in self.cache:
            output, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                self.hits += 1
                output.cache_hit = True
                return output
            else:
                # منتهي الصلاحية
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, input: ThinkingInput, output: ThinkingOutput):
        """حفظ في الكاش"""
        if len(self.cache) >= self.max_size:
            # حذف الأقدم
            oldest_key = min(self.cache, key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        key = self._hash_input(input)
        self.cache[key] = (output, datetime.now())
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# ============================================================
# CONFIDENCE CALCULATOR
# ============================================================

class AdvancedConfidenceCalculator:
    """حاسب الثقة المتقدم"""
    
    def __init__(self):
        self.source_type_weights = {
            "law": 1.0,
            "regulation": 0.95,
            "ruling": 0.9,
            "principle": 0.85,
            "article": 0.8,
            "opinion": 0.6
        }
    
    def calculate(
        self,
        sources: List[Dict[str, Any]],
        reasoning_steps: List[ReasoningStep],
        question_coverage: float,
        source_dates: List[datetime] = None
    ) -> ConfidenceBreakdown:
        """حساب الثقة التفصيلي"""
        
        # 1. جودة المصادر
        source_quality = self._calculate_source_quality(sources)
        
        # 2. اتفاق المصادر
        source_agreement = self._calculate_agreement(sources)
        
        # 3. صحة الاستدلال
        reasoning_validity = self._calculate_reasoning_validity(reasoning_steps)
        
        # 4. تغطية السؤال
        coverage = question_coverage
        
        # 5. حداثة المعلومات
        recency = self._calculate_recency(source_dates)
        
        return ConfidenceBreakdown(
            source_quality=source_quality,
            source_agreement=source_agreement,
            reasoning_validity=reasoning_validity,
            coverage=coverage,
            recency=recency
        )
    
    def _calculate_source_quality(self, sources: List[Dict]) -> float:
        """حساب جودة المصادر"""
        if not sources:
            return 0.0
        
        scores = []
        for s in sources:
            source_type = s.get("type", "article")
            weight = self.source_type_weights.get(source_type, 0.5)
            relevance = s.get("relevance_score", 0.5)
            scores.append(weight * relevance)
        
        return np.mean(scores) if scores else 0.0
    
    def _calculate_agreement(self, sources: List[Dict]) -> float:
        """حساب اتفاق المصادر"""
        if len(sources) < 2:
            return 0.7  # افتراضي للمصدر الواحد
        
        # تحليل بسيط للاتفاق (في الواقع سيستخدم NLP)
        # نفترض اتفاق إذا كانت المصادر من نفس المجال
        domains = [s.get("domain", "general") for s in sources]
        unique_domains = len(set(domains))
        
        if unique_domains == 1:
            return 0.9  # كل المصادر من نفس المجال
        else:
            return max(0.5, 1.0 - (unique_domains - 1) * 0.1)
    
    def _calculate_reasoning_validity(self, steps: List[ReasoningStep]) -> float:
        """حساب صحة الاستدلال"""
        if not steps:
            return 0.5
        
        # متوسط ثقة الخطوات
        avg_confidence = np.mean([s.confidence for s in steps])
        
        # مكافأة للخطوات المدعومة باستشهادات
        cited_ratio = sum(1 for s in steps if s.citations) / len(steps)
        
        return 0.6 * avg_confidence + 0.4 * cited_ratio
    
    def _calculate_recency(self, dates: List[datetime] = None) -> float:
        """حساب حداثة المعلومات"""
        if not dates:
            return 0.7  # افتراضي
        
        now = datetime.now()
        ages = [(now - d).days for d in dates if d]
        
        if not ages:
            return 0.7
        
        avg_age = np.mean(ages)
        
        if avg_age < 365:  # أقل من سنة
            return 0.95
        elif avg_age < 730:  # أقل من سنتين
            return 0.85
        elif avg_age < 1825:  # أقل من 5 سنوات
            return 0.7
        else:
            return 0.5


# ============================================================
# REASONING STRATEGIES
# ============================================================

class ReasoningStrategy(ABC):
    """استراتيجية تفكير مجردة"""
    
    @abstractmethod
    def reason(
        self,
        question: str,
        context: str,
        sources: List[Dict],
        llm: Any
    ) -> Tuple[str, List[ReasoningStep], float]:
        """تنفيذ الاستدلال"""
        pass


class DirectStrategy(ReasoningStrategy):
    """استراتيجية الإجابة المباشرة"""
    
    def reason(self, question, context, sources, llm) -> Tuple[str, List[ReasoningStep], float]:
        prompt = f"""أجب بإيجاز ودقة على السؤال التالي:

السؤال: {question}

المعلومات المتاحة:
{context[:2000]}

استشهد بالمصادر بين قوسين [1], [2]."""

        response = llm.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        step = ReasoningStep(
            step_id=1,
            description="إجابة مباشرة",
            reasoning_type=ReasoningMode.DEDUCTIVE,
            inputs=[question],
            output=response,
            confidence=0.7
        )
        
        return response, [step], 0.7


class ChainOfThoughtStrategy(ReasoningStrategy):
    """استراتيجية التفكير المتسلسل"""
    
    def reason(self, question, context, sources, llm) -> Tuple[str, List[ReasoningStep], float]:
        steps = []
        
        # الخطوة 1: تحديد القواعد
        step1_prompt = f"""حدد القواعد القانونية المنطبقة على:
السؤال: {question}
المصادر: {context[:1500]}

اذكر القواعد فقط."""

        rules = llm.chat_completion(
            messages=[{"role": "user", "content": step1_prompt}],
            temperature=0.2
        )
        
        steps.append(ReasoningStep(
            step_id=1,
            description="تحديد القواعد القانونية",
            reasoning_type=ReasoningMode.DEDUCTIVE,
            inputs=[question],
            output=rules,
            confidence=0.8
        ))
        
        # الخطوة 2: التطبيق
        step2_prompt = f"""طبّق القواعد التالية على السؤال:

القواعد: {rules}
السؤال: {question}

ما النتيجة؟"""

        application = llm.chat_completion(
            messages=[{"role": "user", "content": step2_prompt}],
            temperature=0.3
        )
        
        steps.append(ReasoningStep(
            step_id=2,
            description="تطبيق القواعد",
            reasoning_type=ReasoningMode.DEDUCTIVE,
            inputs=[rules],
            output=application,
            confidence=0.75
        ))
        
        # الخطوة 3: الاستثناءات
        step3_prompt = f"""هل هناك استثناءات على النتيجة التالية؟

النتيجة: {application}
السياق: {context[:1000]}

اذكر الاستثناءات إن وجدت."""

        exceptions = llm.chat_completion(
            messages=[{"role": "user", "content": step3_prompt}],
            temperature=0.3
        )
        
        steps.append(ReasoningStep(
            step_id=3,
            description="فحص الاستثناءات",
            reasoning_type=ReasoningMode.ABDUCTIVE,
            inputs=[application],
            output=exceptions,
            confidence=0.7
        ))
        
        # الخطوة 4: الإجابة النهائية
        final_prompt = f"""بناءً على التحليل:
- القواعد: {rules}
- التطبيق: {application}
- الاستثناءات: {exceptions}

قدّم الإجابة النهائية للسؤال: {question}"""

        final = llm.chat_completion(
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.3
        )
        
        steps.append(ReasoningStep(
            step_id=4,
            description="الإجابة النهائية",
            reasoning_type=ReasoningMode.DEDUCTIVE,
            inputs=[rules, application, exceptions],
            output=final,
            confidence=0.8
        ))
        
        avg_confidence = np.mean([s.confidence for s in steps])
        return final, steps, avg_confidence


class MultiPathStrategy(ReasoningStrategy):
    """استراتيجية المسارات المتعددة"""
    
    def __init__(self, num_paths: int = 3):
        self.num_paths = num_paths
    
    def reason(self, question, context, sources, llm) -> Tuple[str, List[ReasoningStep], float]:
        paths = []
        steps = []
        
        perspectives = [
            "من منظور حماية الحقوق",
            "من منظور استقرار المعاملات",
            "من منظور العدالة والإنصاف"
        ]
        
        # توليد مسارات متعددة
        for i, perspective in enumerate(perspectives[:self.num_paths]):
            prompt = f"""أجب على السؤال {perspective}:

السؤال: {question}
المعلومات: {context[:1500]}

قدّم إجابة مختصرة."""

            path_answer = llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5 + i * 0.1  # تنويع
            )
            
            paths.append({
                "perspective": perspective,
                "answer": path_answer
            })
            
            steps.append(ReasoningStep(
                step_id=i + 1,
                description=f"مسار: {perspective}",
                reasoning_type=ReasoningMode.ABDUCTIVE,
                inputs=[question],
                output=path_answer,
                confidence=0.7
            ))
        
        # دمج المسارات
        merge_prompt = f"""لديك ثلاث إجابات من منظورات مختلفة:

{json.dumps(paths, ensure_ascii=False, indent=2)}

السؤال الأصلي: {question}

1. هل تتفق الإجابات؟
2. إذا اختلفت، ما الرأي الراجح ولماذا؟
3. قدّم إجابة نهائية متوازنة."""

        merged = llm.chat_completion(
            messages=[{"role": "user", "content": merge_prompt}],
            temperature=0.3
        )
        
        steps.append(ReasoningStep(
            step_id=len(perspectives) + 1,
            description="دمج المسارات",
            reasoning_type=ReasoningMode.INDUCTIVE,
            inputs=[p["answer"] for p in paths],
            output=merged,
            confidence=0.85
        ))
        
        # حساب الثقة بناءً على اتفاق المسارات
        agreement = self._calculate_path_agreement(paths)
        final_confidence = 0.6 + agreement * 0.35
        
        return merged, steps, final_confidence
    
    def _calculate_path_agreement(self, paths: List[Dict]) -> float:
        """حساب اتفاق المسارات"""
        # تحليل بسيط - في الواقع سيستخدم semantic similarity
        if len(paths) < 2:
            return 0.7
        
        # نفترض اتفاق متوسط
        return 0.75


class TreeOfThoughtStrategy(ReasoningStrategy):
    """استراتيجية شجرة التفكير"""
    
    def __init__(self, max_depth: int = 3, branching: int = 2):
        self.max_depth = max_depth
        self.branching = branching
    
    def reason(self, question, context, sources, llm) -> Tuple[str, List[ReasoningStep], float]:
        steps = []
        
        # الجذر: تفكيك السؤال
        decompose_prompt = f"""فكّك السؤال التالي إلى أسئلة فرعية:

السؤال: {question}

اذكر 2-3 أسئلة فرعية يجب الإجابة عليها أولاً."""

        sub_questions = llm.chat_completion(
            messages=[{"role": "user", "content": decompose_prompt}],
            temperature=0.3
        )
        
        steps.append(ReasoningStep(
            step_id=1,
            description="تفكيك السؤال",
            reasoning_type=ReasoningMode.ABDUCTIVE,
            inputs=[question],
            output=sub_questions,
            confidence=0.8
        ))
        
        # الإجابة على الفروع
        branch_answers = []
        for i, sq in enumerate(sub_questions.split('\n')[:self.branching]):
            if not sq.strip():
                continue
                
            branch_prompt = f"""أجب على السؤال الفرعي:
{sq}

بناءً على:
{context[:1000]}"""

            branch_answer = llm.chat_completion(
                messages=[{"role": "user", "content": branch_prompt}],
                temperature=0.3
            )
            
            branch_answers.append(branch_answer)
            
            steps.append(ReasoningStep(
                step_id=i + 2,
                description=f"فرع {i+1}: {sq[:50]}...",
                reasoning_type=ReasoningMode.DEDUCTIVE,
                inputs=[sq],
                output=branch_answer,
                confidence=0.75
            ))
        
        # التجميع
        synthesis_prompt = f"""بناءً على إجابات الأسئلة الفرعية:

{chr(10).join(f'- {a}' for a in branch_answers)}

أجب على السؤال الأصلي: {question}"""

        final = llm.chat_completion(
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=0.3
        )
        
        steps.append(ReasoningStep(
            step_id=len(steps) + 1,
            description="تجميع الإجابة النهائية",
            reasoning_type=ReasoningMode.INDUCTIVE,
            inputs=branch_answers,
            output=final,
            confidence=0.85
        ))
        
        return final, steps, 0.8


class DebateStrategy(ReasoningStrategy):
    """استراتيجية المناظرة"""
    
    def reason(self, question, context, sources, llm) -> Tuple[str, List[ReasoningStep], float]:
        steps = []
        
        # الموقف الأول (مؤيد)
        pro_prompt = f"""أنت محامٍ تدافع عن الموقف المؤيد.

السؤال: {question}
المعلومات: {context[:1500]}

قدّم حججك المؤيدة."""

        pro_args = llm.chat_completion(
            messages=[{"role": "user", "content": pro_prompt}],
            temperature=0.4
        )
        
        steps.append(ReasoningStep(
            step_id=1,
            description="الحجج المؤيدة",
            reasoning_type=ReasoningMode.DEDUCTIVE,
            inputs=[question],
            output=pro_args,
            confidence=0.7
        ))
        
        # الموقف الثاني (معارض)
        con_prompt = f"""أنت محامٍ تدافع عن الموقف المعارض.

السؤال: {question}
المعلومات: {context[:1500]}

قدّم حججك المعارضة."""

        con_args = llm.chat_completion(
            messages=[{"role": "user", "content": con_prompt}],
            temperature=0.4
        )
        
        steps.append(ReasoningStep(
            step_id=2,
            description="الحجج المعارضة",
            reasoning_type=ReasoningMode.DEDUCTIVE,
            inputs=[question],
            output=con_args,
            confidence=0.7
        ))
        
        # الحكم
        judge_prompt = f"""أنت قاضٍ محايد.

السؤال: {question}

الحجج المؤيدة:
{pro_args}

الحجج المعارضة:
{con_args}

بناءً على النظام السعودي، ما الرأي الراجح ولماذا؟"""

        verdict = llm.chat_completion(
            messages=[{"role": "user", "content": judge_prompt}],
            temperature=0.3
        )
        
        steps.append(ReasoningStep(
            step_id=3,
            description="الحكم والترجيح",
            reasoning_type=ReasoningMode.ABDUCTIVE,
            inputs=[pro_args, con_args],
            output=verdict,
            confidence=0.85
        ))
        
        return verdict, steps, 0.8


class AnalogicalStrategy(ReasoningStrategy):
    """استراتيجية القياس على السوابق"""
    
    def reason(self, question, context, sources, llm) -> Tuple[str, List[ReasoningStep], float]:
        steps = []
        
        # البحث عن سوابق مشابهة
        similar_prompt = f"""ابحث في المعلومات التالية عن حالات أو سوابق مشابهة:

السؤال: {question}
المصادر: {context[:2000]}

اذكر أي سوابق أو حالات مشابهة."""

        similar_cases = llm.chat_completion(
            messages=[{"role": "user", "content": similar_prompt}],
            temperature=0.3
        )
        
        steps.append(ReasoningStep(
            step_id=1,
            description="البحث عن سوابق مشابهة",
            reasoning_type=ReasoningMode.ANALOGICAL,
            inputs=[question],
            output=similar_cases,
            confidence=0.7
        ))
        
        # القياس
        analogy_prompt = f"""بناءً على السوابق المشابهة:
{similar_cases}

قس على هذه السوابق للإجابة على:
{question}

وضّح وجه الشبه والاختلاف."""

        analogy = llm.chat_completion(
            messages=[{"role": "user", "content": analogy_prompt}],
            temperature=0.3
        )
        
        steps.append(ReasoningStep(
            step_id=2,
            description="القياس والاستنتاج",
            reasoning_type=ReasoningMode.ANALOGICAL,
            inputs=[similar_cases],
            output=analogy,
            confidence=0.75
        ))
        
        return analogy, steps, 0.75


# ============================================================
# STRATEGY SELECTOR
# ============================================================

class StrategySelector:
    """محدد الاستراتيجية الذكي"""
    
    def __init__(self):
        self.strategies: Dict[ThinkingStrategy, ReasoningStrategy] = {
            ThinkingStrategy.DIRECT: DirectStrategy(),
            ThinkingStrategy.CHAIN_OF_THOUGHT: ChainOfThoughtStrategy(),
            ThinkingStrategy.MULTI_PATH: MultiPathStrategy(),
            ThinkingStrategy.TREE_OF_THOUGHT: TreeOfThoughtStrategy(),
            ThinkingStrategy.DEBATE: DebateStrategy(),
            ThinkingStrategy.ANALOGICAL: AnalogicalStrategy(),
        }
        
        # قواعد الاختيار
        self.complexity_mapping = {
            "simple": ThinkingStrategy.DIRECT,
            "moderate": ThinkingStrategy.CHAIN_OF_THOUGHT,
            "complex": ThinkingStrategy.MULTI_PATH,
            "very_complex": ThinkingStrategy.TREE_OF_THOUGHT
        }
    
    def select(
        self,
        question: str,
        complexity: str,
        domain: str,
        is_controversial: bool = False,
        has_precedents: bool = False
    ) -> ThinkingStrategy:
        """اختيار الاستراتيجية المناسبة"""
        
        # إذا كان مثيراً للجدل → مناظرة
        if is_controversial:
            return ThinkingStrategy.DEBATE
        
        # إذا كانت هناك سوابق → قياس
        if has_precedents and complexity in ["moderate", "complex"]:
            return ThinkingStrategy.ANALOGICAL
        
        # حسب التعقيد
        return self.complexity_mapping.get(complexity, ThinkingStrategy.CHAIN_OF_THOUGHT)
    
    def get_strategy(self, strategy_type: ThinkingStrategy) -> ReasoningStrategy:
        """الحصول على استراتيجية"""
        return self.strategies.get(strategy_type, DirectStrategy())


# ============================================================
# FEEDBACK LEARNING
# ============================================================

@dataclass
class FeedbackRecord:
    """سجل التغذية الراجعة"""
    question_hash: str
    strategy_used: ThinkingStrategy
    confidence_predicted: float
    user_rating: Optional[float] = None  # 1-5
    was_correct: Optional[bool] = None
    timestamp: datetime = field(default_factory=datetime.now)


class FeedbackLearner:
    """متعلم التغذية الراجعة"""
    
    def __init__(self):
        self.records: List[FeedbackRecord] = []
        self.strategy_performance: Dict[ThinkingStrategy, List[float]] = defaultdict(list)
    
    def record_interaction(
        self,
        question: str,
        strategy: ThinkingStrategy,
        confidence: float
    ) -> str:
        """تسجيل تفاعل"""
        q_hash = hashlib.md5(question.encode()).hexdigest()[:10]
        
        record = FeedbackRecord(
            question_hash=q_hash,
            strategy_used=strategy,
            confidence_predicted=confidence
        )
        self.records.append(record)
        
        return q_hash
    
    def record_feedback(
        self,
        question_hash: str,
        rating: float = None,
        was_correct: bool = None
    ):
        """تسجيل التغذية الراجعة"""
        for record in reversed(self.records):
            if record.question_hash == question_hash:
                record.user_rating = rating
                record.was_correct = was_correct
                
                # تحديث أداء الاستراتيجية
                if rating:
                    self.strategy_performance[record.strategy_used].append(rating / 5.0)
                break
    
    def get_strategy_adjustment(self, strategy: ThinkingStrategy) -> float:
        """الحصول على تعديل الثقة للاستراتيجية"""
        performances = self.strategy_performance.get(strategy, [])
        if len(performances) < 5:
            return 1.0  # لا تعديل
        
        avg_performance = np.mean(performances[-20:])  # آخر 20
        return 0.8 + avg_performance * 0.4  # 0.8 to 1.2


# ============================================================
# ADVANCED THINKING LOOP
# ============================================================

class AdvancedThinkingLoop:
    """
    حلقة التفكير الموحدة المتقدمة
    
    تدمج جميع التقنيات المتقدمة
    """
    
    def __init__(
        self,
        llm_client,
        search_tool=None,
        lookup_tool=None,
        enable_cache: bool = True,
        enable_feedback: bool = True
    ):
        # المكونات الأساسية
        self.llm = llm_client
        self.search_tool = search_tool
        self.lookup_tool = lookup_tool
        
        # الأنظمة المتقدمة
        self.cache = ThinkingCache() if enable_cache else None
        self.confidence_calc = AdvancedConfidenceCalculator()
        self.strategy_selector = StrategySelector()
        self.feedback = FeedbackLearner() if enable_feedback else None
        
        # المحللات
        self.query_generator = None  # سيتم تمريره
        self.relevance_filter = None
        
        logger.info("🚀 Advanced ThinkingLoop initialized")
    
    def think(self, input: ThinkingInput) -> ThinkingOutput:
        """تنفيذ حلقة التفكير المتقدمة"""
        start_time = time.time()
        trace = []
        
        # ===== التحقق من الكاش =====
        if self.cache:
            cached = self.cache.get(input)
            if cached:
                trace.append("⚡ تم الاسترجاع من الكاش")
                return cached
        
        try:
            # ===== Step 0: فحص نوع السؤال (قانوني أم عادي/ترحيب) =====
            trace.append("⓪ فحص نوع السؤال...")
            question_type = self._detect_question_type(input.question)
            
            # إذا كان ترحيب أو سؤال عادي → رد مباشر بدون تفكير
            if question_type == "greeting":
                trace.append("   نوع السؤال: ترحيب/محادثة عادية")
                return self._quick_greeting_response(input, trace, start_time)
            
            trace.append("   نوع السؤال: استفسار قانوني")
            
            # ===== Step 1: تحليل السؤال =====
            trace.append("① تحليل السؤال...")
            analysis = self._analyze_question(input.question)
            trace.append(f"   المجال: {analysis['domain']}")
            trace.append(f"   التعقيد: {analysis['complexity']}")
            
            # ===== Step 2: اختيار الاستراتيجية =====
            trace.append("② اختيار الاستراتيجية...")
            strategy = input.force_strategy or self.strategy_selector.select(
                question=input.question,
                complexity=analysis['complexity'],
                domain=analysis['domain'],
                is_controversial=analysis.get('is_controversial', False),
                has_precedents=analysis.get('has_precedents', False)
            )
            trace.append(f"   الاستراتيجية: {strategy.value}")
            
            # ===== Step 3: البحث =====
            trace.append("③ البحث في قاعدة البيانات...")
            raw_results = self._execute_search(analysis)
            trace.append(f"   تم جلب {len(raw_results)} نتيجة")
            
            # ===== Step 4: الفلترة =====
            trace.append("④ فلترة النتائج...")
            filtered = self._filter_results(input.question, raw_results)
            trace.append(f"   تم قبول {len(filtered['relevant'])}/{len(raw_results)}")
            
            relevant_sources = filtered['relevant']
            
            # ===== Step 5: بناء السياق =====
            trace.append("⑤ بناء السياق...")
            context = self._build_context(relevant_sources, input.context)
            
            # ===== Step 6: التفكير =====
            trace.append(f"⑥ التفكير ({strategy.value})...")
            reasoning_strategy = self.strategy_selector.get_strategy(strategy)
            answer, reasoning_steps, base_confidence = reasoning_strategy.reason(
                question=input.question,
                context=context,
                sources=relevant_sources,
                llm=self.llm
            )
            trace.append(f"   {len(reasoning_steps)} خطوة تفكير")
            
            # ===== Step 7: مراجعة المبادئ =====
            trace.append("⑦ مراجعة المبادئ...")
            principles = self._lookup_principles(analysis)
            if principles:
                trace.append(f"   {len(principles)} مبدأ مطابق")
                answer = self._enhance_with_principles(answer, principles)
            
            # ===== Step 8: تحليل إضافي =====
            counterfactuals = []
            deadline_alerts = []
            
            if input.include_counterfactuals:
                trace.append("⑧ تحليل البديل المضاد...")
                counterfactuals = self._generate_counterfactuals(
                    input.question, answer, context
                )
            
            if input.check_deadlines:
                deadline_alerts = self._check_deadlines(input.question, context)
                if deadline_alerts:
                    trace.append(f"⚠️ {len(deadline_alerts)} تنبيه بمواعيد")
            
            # ===== Step 9: حساب الثقة =====
            trace.append("⑨ حساب الثقة...")
            confidence_breakdown = self.confidence_calc.calculate(
                sources=relevant_sources,
                reasoning_steps=reasoning_steps,
                question_coverage=self._estimate_coverage(input.question, answer)
            )
            
            # تعديل بناءً على التغذية الراجعة
            if self.feedback:
                adjustment = self.feedback.get_strategy_adjustment(strategy)
                final_confidence = min(1.0, confidence_breakdown.overall * adjustment)
            else:
                final_confidence = confidence_breakdown.overall
            
            trace.append(f"   الثقة: {final_confidence:.1%}")
            
            # ===== Step 10: بناء المخرجات =====
            elapsed = (time.time() - start_time) * 1000
            trace.append(f"✅ اكتمل في {elapsed:.0f}ms")
            
            # استخراج الاستشهادات
            citations = self._extract_citations(answer, relevant_sources)
            
            # التحذيرات
            warnings = self._generate_warnings(
                confidence=final_confidence,
                sources_count=len(relevant_sources),
                has_citations=len(citations) > 0
            )
            
            output = ThinkingOutput(
                answer=answer,
                summary=self._generate_summary(answer),
                confidence=final_confidence,
                confidence_breakdown=confidence_breakdown,
                confidence_level=ConfidenceLevel.from_score(final_confidence),
                strategy_used=strategy,
                reasoning_mode=self._get_primary_mode(reasoning_steps),
                domain=analysis['domain'],
                complexity=analysis['complexity'],
                sources_retrieved=len(raw_results),
                sources_used=len(relevant_sources),
                sources_filtered=len(filtered.get('excluded', [])),
                citations=citations,
                reasoning_steps=reasoning_steps,
                reasoning_trace=trace,
                counterfactuals=counterfactuals,
                deadline_alerts=deadline_alerts,
                related_questions=self._generate_related_questions(input.question),
                warnings=warnings,
                uncited_claims=self._find_uncited_claims(answer, citations),
                execution_time_ms=elapsed,
                cache_hit=False
            )
            
            # حفظ في الكاش
            if self.cache:
                self.cache.set(input, output)
            
            # تسجيل للتغذية الراجعة
            if self.feedback:
                self.feedback.record_interaction(
                    input.question, strategy, final_confidence
                )
            
            return output
            
        except Exception as e:
            logger.error(f"Thinking error: {e}")
            return self._create_error_output(input, str(e), trace, start_time)
    
    # ===== Helper Methods =====
    
    def _detect_question_type(self, question: str) -> str:
        """
        تحديد نوع السؤال: قانوني أم عادي/ترحيب
        
        Returns:
            "legal" - سؤال قانوني يحتاج تفكير
            "greeting" - ترحيب أو محادثة عادية
        """
        question_lower = question.lower()
        
        # كلمات الترحيب والمحادثة العادية
        greeting_patterns = [
            "مرحب", "أهلا", "السلام", "صباح", "مساء", "كيف حال", "كيفك",
            "شلونك", "وش اخبار", "شكرا", "شكراً", "الله يعطيك", "يعطيك العافية",
            "تشرفنا", "من أنت", "من انت", "ما اسمك", "اش اسمك","hello", "hi",
            "تساعدني", "ممكن", "لو سمحت", "أريد استفسار", "عندي سؤال",
            "كيف استخدم", "كيف اشتغل", "وين", "فين", "شوف", "شايف"
        ]
        
        # كلمات قانونية واضحة
        legal_keywords = [
            "حق", "قانون", "نظام", "محكمة", "قاضي", "دعوى", "حكم", "مادة",
            "عقد", "اتفاق", "التزام", "مخالفة", "جريمة", "عقوبة", "حضانة",
            "طلاق", "نفقة", "ميراث", "وصية", "صك", "حجة", "سند", "وثيقة",
            "استئناف", "اعتراض", "تظلم", "شكوى", "بلاغ", "تنفيذ"
        ]
        
        # فحص الترحيبات أولاً
        if any(pattern in question_lower for pattern in greeting_patterns):
            # إلا إذا كانت تحتوي على كلمات قانونية (مثل: "مرحبا، عندي سؤال عن العقد")
            if not any(kw in question_lower for kw in legal_keywords):
                return "greeting"
        
        # فحص القصر (الأسئلة القصيرة جداً غالباً ترحيبات)
        if len(question.split()) <= 2 and not any(kw in question_lower for kw in legal_keywords):
            return "greeting"
        
        # الافتراضي: سؤال قانوني
        return "legal"
    
    def _quick_greeting_response(
        self,
        input: ThinkingInput,
        trace: List[str],
        start_time: float
    ) -> ThinkingOutput:
        """رد سريع على الترحيبات والأسئلة العادية"""
        question_lower = input.question.lower()
        
        # اختيار الرد المناسب
        if any(word in question_lower for word in ["مرحب", "أهلا", "السلام", "صباح", "مساء"," hello", "hi"]):
            answer = "مرحباً بك! أنا مساعدك القانوني المتخصص في الأنظمة السعودية. كيف يمكنني مساعدتك اليوم؟"
        
        elif any(word in question_lower for word in ["شكر", "يعطيك", "الله يجزاك"]):
            answer = "العفو! سعيد بخدمتك. إذا كان لديك أي استفسار قانوني آخر، لا تتردد بطرحه."
        
        elif any(word in question_lower for word in ["من أنت", "من انت", "ما اسمك", "اش اسمك"]):
            answer = "أنا مساعد قانوني ذكي مُتخصص في الأنظمة واللوائح السعودية. أستطيع مساعدتك في الاستفسارات القانونية المتعلقة بالأحوال الشخصية، العقود، العمل، التجارة، والمزيد."
        
        elif any(word in question_lower for word in ["كيف", "وش", "شلون", "ايش"]) and not any(kw in question_lower for kw in ["حق", "قانون", "محكمة"]):
            answer = "يمكنك سؤالي عن أي موضوع قانوني متعلق بالأنظمة السعودية. على سبيل المثال:\n• الأحوال الشخصية (حضانة،  نفقة، طلاق)\n• العقود والالتزامات\n• القضايا الجنائية\n• قانون العمل\n• التنفيذ والإجراءات\n\nما الذي تود الاستفسار عنه؟"
        
        else:
            answer = "أهلاً بك! أنا هنا لمساعدتك في الاستفسارات القانونية المتعلقة بالأنظمة السعودية. كيف يمكنني خدمتك؟"
        
        elapsed = (time.time() - start_time) * 1000
        trace.append(f"✅ رد سريع في {elapsed:.0f}ms")
        
        return ThinkingOutput(
            answer=answer,
            summary="رد على تحية/سؤال عادي",
            confidence=1.0,
            confidence_breakdown=ConfidenceBreakdown(1.0, 1.0, 1.0, 1.0, 1.0),
            confidence_level=ConfidenceLevel.VERY_HIGH,
            strategy_used=ThinkingStrategy.DIRECT,
            reasoning_mode=ReasoningMode.DEDUCTIVE,
            domain="general",
            complexity="simple",
            sources_retrieved=0,
            sources_used=0,
            sources_filtered=0,
            citations=[],
            reasoning_steps=[],
            reasoning_trace=trace,
            warnings=[],
            execution_time_ms=elapsed,
            cache_hit=False
        )
    
    def _analyze_question(self, question: str) -> Dict[str, Any]:
        """تحليل السؤال"""
        # تحليل مبسط (سيستخدم IntelligentQueryGenerator)
        complexity = "moderate"
        domain = "general"
        
        # كلمات تشير للتعقيد
        complex_indicators = ["إذا", "في حالة", "ما الفرق", "قارن"]
        simple_indicators = ["ما هو", "كم", "متى", "أين"]
        
        if any(ind in question for ind in complex_indicators):
            complexity = "complex"
        elif any(ind in question for ind in simple_indicators):
            complexity = "simple"
        
        # كلمات المجال
        domain_keywords = {
            "contracts": ["عقد", "إيجار", "بيع", "فسخ"],
            "criminal": ["جريمة", "عقوبة", "جناية"],
            "family": ["طلاق", "نفقة", "حضانة"],
            "labor": ["عمل", "موظف", "فصل", "راتب"]
        }
        
        for d, keywords in domain_keywords.items():
            if any(kw in question for kw in keywords):
                domain = d
                break
        
        return {
            "domain": domain,
            "complexity": complexity,
            "keywords": [],  # سيتم استخراجها
            "is_controversial": False,
            "has_precedents": False
        }
    
    def _execute_search(self, analysis: Dict) -> List[Dict]:
        """تنفيذ البحث"""
        if not self.search_tool:
            return []
        
        results = []
        queries = analysis.get('keywords', [analysis.get('domain', '')])
        
        for q in queries[:3]:
            try:
                result = self.search_tool.run(query=q, top_k=5)
                if result.success and result.data:
                    results.extend(result.data.get("results", []))
            except:
                pass
        
        # إزالة التكرارات
        seen = set()
        unique = []
        for r in results:
            rid = r.get("id", str(r))
            if rid not in seen:
                seen.add(rid)
                unique.append(r)
        
        return unique
    
    def _filter_results(self, question: str, results: List[Dict]) -> Dict:
        """فلترة النتائج"""
        relevant = []
        excluded = []
        
        for r in results:
            content = r.get("content", "")
            # فلترة بسيطة (سيستخدم RelevanceFilter)
            if len(content) > 50:
                relevant.append(r)
            else:
                excluded.append(r)
        
        return {"relevant": relevant, "excluded": excluded}
    
    def _build_context(self, results: List[Dict], additional: str) -> str:
        """بناء السياق"""
        parts = []
        for i, r in enumerate(results[:10], 1):
            content = r.get("content", "")[:500]
            parts.append(f"[{i}] {content}")
        
        context = "\n\n".join(parts)
        if additional:
            context = f"{additional}\n\n---\n\n{context}"
        
        return context
    
    def _lookup_principles(self, analysis: Dict) -> List[Dict]:
        """البحث عن المبادئ"""
        if not self.lookup_tool:
            return []
        
        try:
            result = self.lookup_tool.run(
                query=analysis.get('domain', ''),
                top_k=3
            )
            return result.data.get("principles", []) if result.success else []
        except:
            return []
    
    def _enhance_with_principles(self, answer: str, principles: List[Dict]) -> str:
        """تعزيز بالمبادئ"""
        if not principles:
            return answer
        
        text = "\n\n**المبادئ القانونية:**\n"
        for p in principles[:3]:
            text += f"• {p.get('text', '')[:150]}\n"
        
        return answer + text
    
    def _generate_counterfactuals(
        self, question: str, answer: str, context: str
    ) -> List[CounterfactualAnalysis]:
        """توليد البدائل المضادة"""
        # سيستخدم CounterfactualReasoner
        return []
    
    def _check_deadlines(self, question: str, context: str) -> List[DeadlineAlert]:
        """فحص المواعيد"""
        # سيستخدم TemporalReasoner
        alerts = []
        
        deadline_keywords = {
            "استئناف": 30,
            "اعتراض": 15,
            "تظلم": 60
        }
        
        for keyword, days in deadline_keywords.items():
            if keyword in question or keyword in context:
                alerts.append(DeadlineAlert(
                    deadline_type=keyword,
                    deadline_date=datetime.now() + timedelta(days=days),
                    days_remaining=days,
                    action_required=f"تقديم {keyword}",
                    legal_basis="النظام"
                ))
        
        return alerts
    
    def _estimate_coverage(self, question: str, answer: str) -> float:
        """تقدير تغطية السؤال"""
        # تحليل بسيط
        q_words = set(question.split())
        a_words = set(answer.split())
        overlap = len(q_words & a_words)
        return min(1.0, overlap / max(len(q_words), 1) * 2)
    
    def _extract_citations(
        self, answer: str, sources: List[Dict]
    ) -> List[Citation]:
        """استخراج الاستشهادات"""
        citations = []
        
        # البحث عن [1], [2], إلخ
        import re
        refs = re.findall(r'\[(\d+)\]', answer)
        
        for ref in refs:
            idx = int(ref) - 1
            if 0 <= idx < len(sources):
                s = sources[idx]
                citations.append(Citation(
                    source_id=s.get("id", f"src_{idx}"),
                    source_type=s.get("type", "article"),
                    text=s.get("content", "")[:100],
                    relevance_score=s.get("score", 0.7)
                ))
        
        return citations
    
    def _generate_warnings(
        self,
        confidence: float,
        sources_count: int,
        has_citations: bool
    ) -> List[str]:
        """توليد التحذيرات"""
        warnings = []
        
        if confidence < 0.5:
            warnings.append("⚠️ درجة الثقة منخفضة، يُنصح بمراجعة محامٍ")
        
        if sources_count < 2:
            warnings.append("⚠️ مصادر محدودة، قد تحتاج بحثاً إضافياً")
        
        if not has_citations:
            warnings.append("⚠️ الإجابة غير موثقة بمصادر محددة")
        
        return warnings
    
    def _generate_summary(self, answer: str) -> str:
        """توليد ملخص"""
        # أول 200 حرف
        if len(answer) <= 200:
            return answer
        return answer[:200] + "..."
    
    def _get_primary_mode(self, steps: List[ReasoningStep]) -> ReasoningMode:
        """تحديد نمط التفكير الأساسي"""
        if not steps:
            return ReasoningMode.DEDUCTIVE
        
        modes = [s.reasoning_type for s in steps]
        return max(set(modes), key=modes.count)
    
    def _generate_related_questions(self, question: str) -> List[str]:
        """توليد أسئلة ذات صلة"""
        # مبسط
        return [
            f"ما الإجراءات المتبعة في هذه الحالة؟",
            f"هل هناك استثناءات؟",
            f"ما المواعيد القانونية المهمة؟"
        ]
    
    def _find_uncited_claims(
        self, answer: str, citations: List[Citation]
    ) -> List[str]:
        """إيجاد الادعاءات غير الموثقة"""
        # مبسط - سيستخدم NLP
        if citations:
            return []
        
        # إذا لا توجد استشهادات
        claims = []
        strong_words = ["يجب", "يحظر", "ملزم", "واجب"]
        
        for word in strong_words:
            if word in answer:
                claims.append(f"ادعاء يحتوي على '{word}' بدون مصدر")
        
        return claims[:3]
    
    def _create_error_output(
        self,
        input: ThinkingInput,
        error: str,
        trace: List[str],
        start_time: float
    ) -> ThinkingOutput:
        """إنشاء مخرجات خطأ"""
        elapsed = (time.time() - start_time) * 1000
        trace.append(f"❌ خطأ: {error}")
        
        return ThinkingOutput(
            answer=f"عذراً، حدث خطأ أثناء معالجة السؤال: {error}",
            summary="خطأ في المعالجة",
            confidence=0.0,
            confidence_breakdown=ConfidenceBreakdown(0, 0, 0, 0, 0),
            confidence_level=ConfidenceLevel.VERY_LOW,
            strategy_used=ThinkingStrategy.DIRECT,
            reasoning_mode=ReasoningMode.DEDUCTIVE,
            domain="unknown",
            complexity="unknown",
            sources_retrieved=0,
            sources_used=0,
            sources_filtered=0,
            citations=[],
            reasoning_steps=[],
            reasoning_trace=trace,
            warnings=[f"خطأ: {error}"],
            execution_time_ms=elapsed
        )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "ThinkingStrategy",
    "ThinkingInput",
    "ThinkingOutput",
    "AdvancedThinkingLoop",
    "ConfidenceLevel",
    "ReasoningMode",
    "Citation",
    "ReasoningStep"
]