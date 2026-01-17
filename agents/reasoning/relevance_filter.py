"""
Relevance Filter System
نظام فلترة الصلة - يقيّم ويفلتر النتائج غير ذات الصلة

Features:
- Topic matching with semantic understanding
- Legal domain verification
- Context fitness scoring
- Auto-exclusion of irrelevant results
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .intelligent_prompts import (
    LegalDomain,
    LEGAL_DOMAIN_KEYWORDS,
    PromptBuilder
)
from ..config.openwebui import openwebui_client

logger = logging.getLogger(__name__)


@dataclass
class RelevanceScore:
    """نتيجة تقييم الصلة"""
    content_id: str
    topic_match: float      # 0-1: مطابقة الموضوع
    domain_match: float     # 0-1: مطابقة المجال القانوني
    context_fit: float      # 0-1: مناسبة السياق
    overall_score: float    # 0-1: الدرجة الإجمالية
    is_relevant: bool       # هل ذو صلة؟
    reason: str             # سبب التقييم


class RelevanceFilter:
    """
    مرشّح الصلة للنتائج
    
    يستخدم طريقتين:
    1. Fast Filter: فلترة سريعة بالكلمات المفتاحية
    2. Deep Filter: فلترة عميقة بالـ LLM
    """
    
    # Thresholds
    RELEVANCE_THRESHOLD = 0.4   # الحد الأدنى للصلة
    HIGH_CONFIDENCE = 0.7       # صلة عالية
    FAST_FILTER_THRESHOLD = 0.3 # حد الفلترة السريعة
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.prompt_builder = PromptBuilder()
        self.llm = openwebui_client
        logger.info(f"🔍 RelevanceFilter initialized (LLM={use_llm})")
    
    def filter_results(
        self,
        question: str,
        results: List[Dict[str, Any]],
        domain: LegalDomain = LegalDomain.UNKNOWN,
        keywords: List[str] = None
    ) -> Tuple[List[Dict[str, Any]], List[RelevanceScore]]:
        """
        تصفية النتائج حسب الصلة
        
        Returns:
            (relevant_results, all_scores)
        """
        if not results:
            return [], []
        
        logger.info(f"🔍 Filtering {len(results)} results for relevance...")
        
        # Extract keywords if not provided
        if not keywords:
            keywords = self._extract_question_keywords(question)
        
        all_scores = []
        relevant_results = []
        
        for result in results:
            content = self._get_content(result)
            content_id = result.get("id", "unknown")
            
            # Stage 1: Fast filter (keyword-based)
            fast_score = self._fast_relevance_check(content, keywords, domain)
            
            if fast_score < self.FAST_FILTER_THRESHOLD:
                # إستبعاد سريع
                score = RelevanceScore(
                    content_id=content_id,
                    topic_match=fast_score,
                    domain_match=0.0,
                    context_fit=0.0,
                    overall_score=fast_score,
                    is_relevant=False,
                    reason="فشل الفلترة السريعة - لا توجد كلمات دالة"
                )
                all_scores.append(score)
                continue
            
            # Stage 2: Deep filter (LLM-based) for borderline cases
            if self.use_llm and fast_score < self.HIGH_CONFIDENCE:
                score = self._deep_relevance_check(question, content, domain, content_id)
            else:
                # Score is high enough, accept without LLM
                score = RelevanceScore(
                    content_id=content_id,
                    topic_match=fast_score,
                    domain_match=self._domain_match(content, domain),
                    context_fit=fast_score,
                    overall_score=fast_score,
                    is_relevant=True,
                    reason="مطابقة عالية بالكلمات المفتاحية"
                )
            
            all_scores.append(score)
            
            if score.is_relevant:
                result["relevance_score"] = score.overall_score
                relevant_results.append(result)
        
        # Sort by relevance
        relevant_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        logger.info(f"✅ Filtered: {len(relevant_results)}/{len(results)} relevant")
        
        return relevant_results, all_scores
    
    def _get_content(self, result: Dict[str, Any]) -> str:
        """استخراج المحتوى من النتيجة"""
        content = (
            result.get("content") or 
            result.get("template_text") or 
            result.get("title") or
            result.get("full_content_md") or
            str(result)
        )
        return content[:2000]  # تقليص للأداء
    
    def _extract_question_keywords(self, question: str) -> List[str]:
        """استخراج الكلمات المفتاحية من السؤال"""
        # تنظيف النص
        words = re.findall(r'[\u0600-\u06FF]+', question)
        
        # إزالة الكلمات الشائعة
        stop_words = {
            "في", "من", "إلى", "على", "عن", "هل", "ما", "هي", "هو", 
            "أن", "كان", "التي", "الذي", "هذا", "هذه", "بعد", "قبل",
            "حول", "عند", "كل", "بين", "إذا", "ثم", "أو", "و"
        }
        
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        
        # إضافة الكلمات القانونية
        for domain_keywords in LEGAL_DOMAIN_KEYWORDS.values():
            for kw in domain_keywords:
                if kw in question and kw not in keywords:
                    keywords.append(kw)
        
        return keywords[:15]
    
    def _fast_relevance_check(
        self,
        content: str,
        keywords: List[str],
        domain: LegalDomain
    ) -> float:
        """فحص سريع بالكلمات المفتاحية"""
        if not content or not keywords:
            return 0.0
        
        content_lower = content.lower()
        
        # حساب تطابق الكلمات
        matches = 0
        for kw in keywords:
            if kw in content:
                matches += 1
        
        keyword_score = matches / len(keywords) if keywords else 0
        
        # حساب تطابق المجال
        domain_score = self._domain_match(content, domain)
        
        # الدرجة المركبة
        overall = (keyword_score * 0.7) + (domain_score * 0.3)
        
        return min(1.0, overall)
    
    def _domain_match(self, content: str, domain: LegalDomain) -> float:
        """حساب تطابق المجال القانوني"""
        if domain == LegalDomain.UNKNOWN:
            return 0.5  # محايد
        
        domain_keywords = LEGAL_DOMAIN_KEYWORDS.get(domain, [])
        if not domain_keywords:
            return 0.5
        
        matches = sum(1 for kw in domain_keywords if kw in content)
        score = min(1.0, matches / 5)  # نحتاج 5 كلمات للدرجة الكاملة
        
        return score
    
    def _deep_relevance_check(
        self,
        question: str,
        content: str,
        domain: LegalDomain,
        content_id: str
    ) -> RelevanceScore:
        """فحص عميق بالـ LLM"""
        try:
            prompt = self.prompt_builder.build_relevance_prompt(
                question=question,
                content=content[:1000],
                domain=domain.value.replace("_", " ")
            )
            
            response = self.llm.chat_completion(
                messages=[
                    {"role": "system", "content": "أنت مدقق صلة قانوني. أجب بـ JSON فقط."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            # Parse JSON response
            result = self._parse_json(response)
            
            topic_match = float(result.get("topic_match", 0.5))
            domain_match = float(result.get("domain_match", 0.5))
            context_fit = float(result.get("context_fit", 0.5))
            overall = float(result.get("overall_relevance", (topic_match + domain_match + context_fit) / 3))
            
            return RelevanceScore(
                content_id=content_id,
                topic_match=topic_match,
                domain_match=domain_match,
                context_fit=context_fit,
                overall_score=overall,
                is_relevant=overall >= self.RELEVANCE_THRESHOLD,
                reason=result.get("reason", "تقييم LLM")
            )
            
        except Exception as e:
            logger.error(f"Deep relevance check failed: {e}")
            # Fallback to fast filter
            return RelevanceScore(
                content_id=content_id,
                topic_match=0.5,
                domain_match=0.5,
                context_fit=0.5,
                overall_score=0.5,
                is_relevant=True,  # في حالة الخطأ نقبل
                reason=f"Fallback due to error: {str(e)[:50]}"
            )
    
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            # Try direct parse
            if text.strip().startswith("{"):
                return json.loads(text.strip())
            
            # Find JSON in text
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


class SmartSearcher:
    """
    باحث ذكي يدمج البحث مع الفلترة
    """
    
    def __init__(self, relevance_filter: RelevanceFilter = None):
        self.filter = relevance_filter or RelevanceFilter()
        self.prompt_builder = PromptBuilder()
        logger.info("🔎 SmartSearcher initialized")
    
    def search_and_filter(
        self,
        question: str,
        search_results: List[Dict[str, Any]],
        min_relevance: float = 0.4,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        بحث وفلترة ذكية
        
        Returns:
            {
                "relevant": [...],
                "excluded": [...],
                "stats": {...}
            }
        """
        # تحليل السؤال
        analyzed = self.prompt_builder.query_generator.analyze_question(question)
        
        # فلترة النتائج
        relevant, scores = self.filter.filter_results(
            question=question,
            results=search_results,
            domain=analyzed.domain,
            keywords=analyzed.legal_keywords
        )
        
        # تقسيم النتائج
        excluded = [s for s in scores if not s.is_relevant]
        
        # الإحصائيات
        stats = {
            "total_results": len(search_results),
            "relevant_count": len(relevant),
            "excluded_count": len(excluded),
            "domain": analyzed.domain.value,
            "keywords_used": analyzed.legal_keywords,
            "avg_relevance": sum(s.overall_score for s in scores) / len(scores) if scores else 0
        }
        
        logger.info(f"📊 Search stats: {stats['relevant_count']}/{stats['total_results']} relevant")
        
        return {
            "relevant": relevant[:max_results],
            "excluded": [{"id": s.content_id, "reason": s.reason} for s in excluded],
            "scores": scores,
            "stats": stats,
            "analysis": analyzed
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RelevanceScore",
    "RelevanceFilter",
    "SmartSearcher"
]
