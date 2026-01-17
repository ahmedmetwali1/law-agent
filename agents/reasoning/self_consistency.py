"""
Self-Consistency Reasoning Engine with Legal Conflict Resolution
محرك التناسق الذاتي مع حل التعارضات القانونية

Enhanced Features:
- Multi-path generation with different perspectives
- Legal Conflict Resolution (not just majority voting)
- Citation Mapping for all claims
- Confidence calibration
- Contradiction detection with deep analysis
"""

import logging
import json
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter

from .intelligent_prompts import (
    LegalDomain,
    MAGIC_WORDS,
    PromptBuilder
)
from ..config.openwebui import openwebui_client

logger = logging.getLogger(__name__)


class ReasoningPerspective(Enum):
    """وجهات النظر للتفكير المتعدد"""
    LEGAL_EXPERT = "خبير_قانوني"
    JUDGE = "قاضي"
    OPPOSING_COUNSEL = "محامي_خصم"
    PRACTICAL = "تطبيقي"
    TEXTUAL = "نصي_حرفي"


@dataclass
class Citation:
    """استشهاد بمصدر"""
    chunk_id: str
    source_id: str
    content_snippet: str
    relevance_score: float


@dataclass 
class CitedClaim:
    """ادعاء موثق بمصدر"""
    claim: str
    citations: List[Citation]
    has_source: bool
    confidence: float


@dataclass
class ReasoningPath:
    """مسار تفكير واحد"""
    path_id: int
    perspective: ReasoningPerspective
    reasoning: str
    conclusion: str
    confidence: float
    key_points: List[str]
    source_ids: List[str] = field(default_factory=list)  # المصادر المستخدمة
    execution_time_ms: float = 0.0


@dataclass
class LegalConflict:
    """تعارض قانوني بين مسارين"""
    path_a: ReasoningPath
    path_b: ReasoningPath
    conflict_type: str  # "newer_vs_older", "specific_vs_general", "exception_vs_rule"
    resolution: str
    winning_path_id: int
    analysis: str


@dataclass
class ConsistencyResult:
    """نتيجة التناسق الذاتي"""
    final_answer: str
    confidence: float
    paths_count: int
    agreement_ratio: float
    majority_conclusion: str
    contradictions: List[str]
    conflicts_resolved: List[LegalConflict]
    cited_claims: List[CitedClaim]
    uncited_warnings: List[str]
    reasoning_summary: str
    all_paths: List[ReasoningPath]


class SelfConsistencyEngine:
    """
    محرك التناسق الذاتي مع حل التعارضات القانونية
    
    يولّد 3-5 مسارات تفكير مختلفة ويحل التعارضات بذكاء
    """
    
    DEFAULT_PATHS = 3
    MAX_PATHS = 5
    
    # وجهات النظر وتركيزها
    PERSPECTIVES_CONFIG = {
        ReasoningPerspective.LEGAL_EXPERT: {
            "role": "أنت محامٍ سعودي خبير بخبرة 20 عاماً",
            "focus": "النصوص القانونية والأنظمة والسوابق",
            "magic": MAGIC_WORDS["step_by_step"][0]
        },
        ReasoningPerspective.JUDGE: {
            "role": "أنت قاضٍ في محكمة الأحوال الشخصية",
            "focus": "تطبيق القانون وتحقيق العدالة",
            "magic": MAGIC_WORDS["verification"][0]
        },
        ReasoningPerspective.OPPOSING_COUNSEL: {
            "role": "أنت محامي الطرف الآخر تبحث عن ثغرات",
            "focus": "الحجج المضادة والاستثناءات",
            "magic": MAGIC_WORDS["counter_argument"][0]
        },
        ReasoningPerspective.PRACTICAL: {
            "role": "أنت مستشار قانوني عملي",
            "focus": "التطبيق العملي وإجراءات المحاكم",
            "magic": MAGIC_WORDS["expert_role"][0]
        },
        ReasoningPerspective.TEXTUAL: {
            "role": "أنت باحث قانوني دقيق",
            "focus": "النصوص الحرفية والمصادر الموثوقة",
            "magic": MAGIC_WORDS["deep_thinking"][0]
        }
    }
    
    def __init__(self):
        self.llm = openwebui_client
        self.prompt_builder = PromptBuilder()
        self.available_sources: Dict[str, Dict] = {}  # للتتبع
        logger.info("🔄 SelfConsistencyEngine initialized with Legal Conflict Resolution")
    
    def set_available_sources(self, sources: List[Dict[str, Any]]):
        """تعيين المصادر المتاحة للاستشهاد"""
        self.available_sources = {}
        for s in sources:
            source_id = s.get("id") or s.get("chunk_id") or str(len(self.available_sources))
            self.available_sources[source_id] = s
        logger.info(f"📚 Set {len(self.available_sources)} available sources for citation")
    
    def reason_with_consistency(
        self,
        question: str,
        context: str,
        sources: List[Dict[str, Any]] = None,
        domain: LegalDomain = LegalDomain.UNKNOWN,
        num_paths: int = None
    ) -> ConsistencyResult:
        """
        تفكير متعدد المسارات مع تناسق ذاتي وحل التعارضات
        """
        start_time = time.time()
        num_paths = min(num_paths or self.DEFAULT_PATHS, self.MAX_PATHS)
        
        # تعيين المصادر
        if sources:
            self.set_available_sources(sources)
        
        logger.info(f"🔄 Starting enhanced self-consistency with {num_paths} paths...")
        
        # اختيار وجهات النظر
        perspectives = self._select_perspectives(domain, num_paths)
        
        # توليد المسارات
        paths = []
        for i, perspective in enumerate(perspectives):
            path = self._generate_reasoning_path(
                path_id=i + 1,
                perspective=perspective,
                question=question,
                context=context,
                domain=domain
            )
            paths.append(path)
            logger.info(f"   Path {i+1}/{num_paths} ({perspective.value}): confidence={path.confidence:.2f}")
        
        # تحليل التناسق مع حل التعارضات
        result = self._analyze_consistency_enhanced(question, paths, context)
        
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"✅ Self-consistency complete in {elapsed:.0f}ms: agreement={result.agreement_ratio:.2f}, conflicts_resolved={len(result.conflicts_resolved)}")
        
        return result
    
    def _select_perspectives(
        self, 
        domain: LegalDomain, 
        num_paths: int
    ) -> List[ReasoningPerspective]:
        """اختيار وجهات النظر المناسبة"""
        perspectives = [
            ReasoningPerspective.LEGAL_EXPERT,
            ReasoningPerspective.JUDGE
        ]
        
        if domain == LegalDomain.PERSONAL_STATUS:
            perspectives.append(ReasoningPerspective.PRACTICAL)
        elif domain == LegalDomain.CRIMINAL:
            perspectives.append(ReasoningPerspective.TEXTUAL)
        else:
            perspectives.append(ReasoningPerspective.OPPOSING_COUNSEL)
        
        all_perspectives = list(ReasoningPerspective)
        for p in all_perspectives:
            if len(perspectives) >= num_paths:
                break
            if p not in perspectives:
                perspectives.append(p)
        
        return perspectives[:num_paths]
    
    def _generate_reasoning_path(
        self,
        path_id: int,
        perspective: ReasoningPerspective,
        question: str,
        context: str,
        domain: LegalDomain
    ) -> ReasoningPath:
        """توليد مسار تفكير واحد مع تتبع المصادر"""
        start_time = time.time()
        
        config = self.PERSPECTIVES_CONFIG[perspective]
        
        prompt = f"""{config['role']}

{config['magic']}

**السؤال:** {question}

**السياق والمعلومات:**
{context[:1500]}

**المطلوب:**
من وجهة نظرك كـ{perspective.value}، وبالتركيز على {config['focus']}:

1. حلل المسألة خطوة بخطوة
2. حدد النقاط الرئيسية (3-5 نقاط)
3. حدد أرقام المصادر التي تستند إليها (من [1] إلى [10])
4. قدّم استنتاجك النهائي
5. قيّم مستوى ثقتك (0-1)

**أجب بـ JSON:**
{{
    "reasoning": "تحليلك المفصل خطوة بخطوة",
    "key_points": ["نقطة 1", "نقطة 2", "نقطة 3"],
    "source_refs": [1, 2, 5],
    "conclusion": "الاستنتاج النهائي في جملة واحدة",
    "confidence": 0.0-1.0
}}"""

        try:
            response = self.llm.chat_completion(
                messages=[
                    {"role": "system", "content": f"أنت {config['role']}. فكّر بعمق وأجب بـ JSON. استند دائماً للمصادر."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1200
            )
            
            result = self._parse_json(response)
            elapsed = (time.time() - start_time) * 1000
            
            # استخراج المصادر المشار إليها
            source_refs = result.get("source_refs", [])
            source_ids = [str(ref) for ref in source_refs if isinstance(ref, (int, str))]
            
            return ReasoningPath(
                path_id=path_id,
                perspective=perspective,
                reasoning=result.get("reasoning", response[:500]),
                conclusion=result.get("conclusion", "لم يتم تحديد استنتاج"),
                confidence=float(result.get("confidence", 0.5)),
                key_points=result.get("key_points", []),
                source_ids=source_ids,
                execution_time_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"Path generation failed: {e}")
            return ReasoningPath(
                path_id=path_id,
                perspective=perspective,
                reasoning=f"فشل التحليل: {str(e)}",
                conclusion="غير متاح",
                confidence=0.0,
                key_points=[],
                source_ids=[],
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _analyze_consistency_enhanced(
        self,
        question: str,
        paths: List[ReasoningPath],
        context: str
    ) -> ConsistencyResult:
        """تحليل التناسق مع حل التعارضات القانونية"""
        
        if not paths:
            return ConsistencyResult(
                final_answer="لم يتم توليد إجابة",
                confidence=0.0,
                paths_count=0,
                agreement_ratio=0.0,
                majority_conclusion="",
                contradictions=[],
                conflicts_resolved=[],
                cited_claims=[],
                uncited_warnings=[],
                reasoning_summary="لا توجد مسارات",
                all_paths=[]
            )
        
        # حساب التوافق
        agreement = self._calculate_agreement(paths)
        
        # كشف التناقضات
        contradictions = self._detect_contradictions(paths)
        
        # حل التعارضات القانونية (بدلاً من مجرد التصويت)
        conflicts_resolved = []
        if contradictions:
            conflicts_resolved = self._resolve_legal_conflicts(paths, context)
        
        # تحديد الاستنتاج النهائي بناءً على حل التعارضات
        if conflicts_resolved:
            majority = self._conclusion_from_conflicts(paths, conflicts_resolved)
        else:
            majority = self._majority_vote(paths)
        
        # بناء الإجابة النهائية
        final_answer = self._synthesize_answer(question, paths, majority, conflicts_resolved)
        
        # استخراج الادعاءات مع الاستشهادات
        cited_claims, uncited_warnings = self._extract_citations(final_answer)
        
        # حساب الثقة
        avg_confidence = sum(p.confidence for p in paths) / len(paths)
        conflict_penalty = 0.1 * len(contradictions) if contradictions else 0
        citation_bonus = 0.1 if len(uncited_warnings) == 0 else 0
        final_confidence = min(1.0, avg_confidence * agreement - conflict_penalty + citation_bonus)
        
        # ملخص التفكير
        summary = self._create_summary(paths, conflicts_resolved)
        
        return ConsistencyResult(
            final_answer=final_answer,
            confidence=final_confidence,
            paths_count=len(paths),
            agreement_ratio=agreement,
            majority_conclusion=majority,
            contradictions=contradictions,
            conflicts_resolved=conflicts_resolved,
            cited_claims=cited_claims,
            uncited_warnings=uncited_warnings,
            reasoning_summary=summary,
            all_paths=paths
        )
    
    def _resolve_legal_conflicts(
        self,
        paths: List[ReasoningPath],
        context: str
    ) -> List[LegalConflict]:
        """حل التعارضات القانونية بالتحليل العميق"""
        conflicts = []
        
        # إيجاد أزواج متعارضة
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                p1, p2 = paths[i], paths[j]
                
                # تحديد ما إذا كان هناك تعارض حقيقي
                if abs(p1.confidence - p2.confidence) > 0.3:
                    conflict = self._analyze_conflict(p1, p2, context)
                    if conflict:
                        conflicts.append(conflict)
                        logger.info(f"⚖️ Resolved conflict: {conflict.conflict_type} -> Path {conflict.winning_path_id}")
        
        return conflicts[:3]  # أقصى 3 تعارضات
    
    def _analyze_conflict(
        self,
        path_a: ReasoningPath,
        path_b: ReasoningPath,
        context: str
    ) -> Optional[LegalConflict]:
        """تحليل تعارض واحد باستخدام التفكير العميق"""
        
        prompt = f"""أنت خبير في حل التعارضات القانونية.

**التعارض:**
- الرأي الأول ({path_a.perspective.value}): {path_a.conclusion}
  الثقة: {path_a.confidence:.1f}
  
- الرأي الثاني ({path_b.perspective.value}): {path_b.conclusion}
  الثقة: {path_b.confidence:.1f}

**السياق:**
{context[:1000]}

**حلل التعارض وحدد:**
1. نوع التعارض:
   - newer_vs_older: نص أحدث يلغي الأقدم
   - specific_vs_general: نص خاص يقيد العام
   - exception_vs_rule: استثناء للقاعدة العامة
   - interpretation_diff: اختلاف في التفسير فقط
   
2. أي الرأيين أصح ولماذا؟

**أجب بـ JSON:**
{{
    "conflict_type": "نوع التعارض",
    "winning_opinion": 1 أو 2,
    "analysis": "تحليل مختصر للسبب",
    "resolution": "كيف تم حل التعارض"
}}"""

        try:
            response = self.llm.chat_completion(
                messages=[
                    {"role": "system", "content": "أنت خبير قانوني متخصص في حل التعارضات. أجب بـ JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            result = self._parse_json(response)
            
            winning = result.get("winning_opinion", 1)
            
            return LegalConflict(
                path_a=path_a,
                path_b=path_b,
                conflict_type=result.get("conflict_type", "interpretation_diff"),
                resolution=result.get("resolution", "لم يتم تحديد"),
                winning_path_id=path_a.path_id if winning == 1 else path_b.path_id,
                analysis=result.get("analysis", "")
            )
            
        except Exception as e:
            logger.error(f"Conflict analysis failed: {e}")
            return None
    
    def _conclusion_from_conflicts(
        self,
        paths: List[ReasoningPath],
        conflicts: List[LegalConflict]
    ) -> str:
        """استخراج الاستنتاج بناءً على حل التعارضات"""
        # ترجيح المسارات الفائزة
        winning_ids = [c.winning_path_id for c in conflicts]
        
        for path in paths:
            if path.path_id in winning_ids:
                return path.conclusion
        
        # Fallback
        return max(paths, key=lambda p: p.confidence).conclusion
    
    def _extract_citations(
        self,
        answer: str
    ) -> Tuple[List[CitedClaim], List[str]]:
        """استخراج الادعاءات والتحقق من الاستشهادات"""
        cited_claims = []
        uncited_warnings = []
        
        # تقسيم الإجابة لجمل
        sentences = re.split(r'[.،؛]', answer)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # تجاهل الجمل القصيرة جداً
                continue
            
            # البحث عن إشارات للمصادر [1], [2], etc.
            source_refs = re.findall(r'\[(\d+)\]', sentence)
            
            if source_refs:
                # جملة موثقة
                citations = []
                for ref in source_refs:
                    if ref in self.available_sources:
                        src = self.available_sources[ref]
                        citations.append(Citation(
                            chunk_id=src.get("id", ref),
                            source_id=src.get("source_id", ""),
                            content_snippet=src.get("content", "")[:100],
                            relevance_score=src.get("relevance_score", 0.5)
                        ))
                
                cited_claims.append(CitedClaim(
                    claim=sentence,
                    citations=citations,
                    has_source=len(citations) > 0,
                    confidence=0.9 if citations else 0.5
                ))
            else:
                # ادعاء بدون مصدر
                # تحقق إذا كان ادعاءً قانونياً يحتاج توثيق
                if self._is_legal_claim(sentence):
                    uncited_warnings.append(f"⚠️ لم يتم العثور على مصدر: «{sentence[:50]}...»")
        
        return cited_claims, uncited_warnings
    
    def _is_legal_claim(self, sentence: str) -> bool:
        """تحديد إذا كانت الجملة ادعاءً قانونياً يحتاج توثيق"""
        legal_indicators = [
            "يجب", "لا يجوز", "حق", "واجب", "يحظر", "يلزم",
            "القانون", "النظام", "المادة", "الفقرة", "المحكمة",
            "الحكم", "القاضي", "القضاء", "الشريعة", "الفقه"
        ]
        
        return any(ind in sentence for ind in legal_indicators)
    
    def _calculate_agreement(self, paths: List[ReasoningPath]) -> float:
        """حساب نسبة التوافق بين المسارات"""
        if len(paths) < 2:
            return 1.0
        
        all_points = []
        for p in paths:
            all_points.extend(p.key_points)
        
        if not all_points:
            return 0.5
        
        point_counts = Counter(all_points)
        common_points = sum(1 for count in point_counts.values() if count > 1)
        
        agreement = common_points / len(set(all_points)) if all_points else 0.5
        
        confidences = [p.confidence for p in paths]
        confidence_variance = max(confidences) - min(confidences) if confidences else 0
        confidence_factor = 1 - (confidence_variance * 0.3)
        
        return min(1.0, agreement * confidence_factor + 0.3)
    
    def _majority_vote(self, paths: List[ReasoningPath]) -> str:
        """اختيار الاستنتاج الأكثر شيوعاً"""
        weighted_conclusions = {}
        for p in paths:
            if p.conclusion:
                key = p.conclusion[:100]
                weighted_conclusions[key] = weighted_conclusions.get(key, 0) + p.confidence
        
        if weighted_conclusions:
            return max(weighted_conclusions, key=weighted_conclusions.get)
        
        best_path = max(paths, key=lambda p: p.confidence)
        return best_path.conclusion
    
    def _detect_contradictions(self, paths: List[ReasoningPath]) -> List[str]:
        """كشف التناقضات بين المسارات"""
        contradictions = []
        
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                p1, p2 = paths[i], paths[j]
                
                if abs(p1.confidence - p2.confidence) > 0.4:
                    contradictions.append(
                        f"تباين كبير بين {p1.perspective.value} ({p1.confidence:.1f}) و {p2.perspective.value} ({p2.confidence:.1f})"
                    )
        
        return contradictions[:3]
    
    def _synthesize_answer(
        self,
        question: str,
        paths: List[ReasoningPath],
        majority: str,
        conflicts: List[LegalConflict]
    ) -> str:
        """تجميع الإجابة النهائية مع التعارضات المحلولة"""
        
        conflict_notes = ""
        if conflicts:
            conflict_notes = "\n**ملاحظات حول التعارضات المحلولة:**\n"
            for c in conflicts:
                conflict_notes += f"- {c.conflict_type}: {c.resolution}\n"
        
        prompt = f"""بناءً على تحليلات متعددة من وجهات نظر مختلفة:

**السؤال:** {question}

**الاستنتاج الرئيسي:** {majority}

**النقاط الرئيسية:**
{self._collect_key_points(paths)}

{conflict_notes}

**المطلوب:**
1. اكتب إجابة نهائية شاملة ومتوازنة
2. لكل ادعاء قانوني، أضف رقم المصدر بين قوسين مربعين [1], [2] etc.
3. اذكر أي استثناءات أو تحفظات مهمة

**الإجابة:**"""

        try:
            response = self.llm.chat_completion(
                messages=[
                    {"role": "system", "content": "أنت محامٍ خبير. قدّم إجابة قانونية دقيقة ومتوازنة مع الاستشهاد بالمصادر."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            return response
        except:
            return majority
    
    def _collect_key_points(self, paths: List[ReasoningPath]) -> str:
        """جمع النقاط الرئيسية"""
        points = []
        for p in paths:
            for point in p.key_points[:2]:
                if point not in points:
                    points.append(f"- {point}")
        return "\n".join(points[:10])
    
    def _create_summary(
        self, 
        paths: List[ReasoningPath],
        conflicts: List[LegalConflict]
    ) -> str:
        """ملخص التفكير"""
        perspectives = [p.perspective.value for p in paths]
        avg_conf = sum(p.confidence for p in paths) / len(paths) if paths else 0
        
        summary = f"تم التحليل من {len(paths)} وجهات نظر ({', '.join(perspectives)}) بمتوسط ثقة {avg_conf:.2f}"
        
        if conflicts:
            summary += f". تم حل {len(conflicts)} تعارض قانوني."
        
        return summary
    
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from response"""
        try:
            if text.strip().startswith("{"):
                return json.loads(text.strip())
            
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
            else:
                start = text.find("{")
                end = text.rfind("}") + 1
                json_str = text[start:end] if start != -1 else "{}"
            
            return json.loads(json_str)
        except:
            return {}


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ReasoningPerspective",
    "ReasoningPath",
    "Citation",
    "CitedClaim",
    "LegalConflict",
    "ConsistencyResult",
    "SelfConsistencyEngine"
]
