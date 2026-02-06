"""
🔄 Query Rewriter Engine v1.0

Expands a single query into multiple semantic variants for improved search coverage.
Handles legal terminology, Arabic variations, and intent-based expansion.

Architecture:
- Template-based expansion for common patterns
- Arabic morphological variants
- Topic + Article combination queries
- Intent-specific rewrites

Author: Legal AI System
Created: 2026-02-06
"""

import re
import logging
from typing import List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RewriteResult:
    """Result of query rewriting."""
    original: str
    variants: List[str]
    intent_detected: Optional[str] = None
    expansion_type: Optional[str] = None


# =============================================================================
# QUERY REWRITER
# =============================================================================

class QueryRewriter:
    """
    Expands a single query into multiple semantic variants.
    
    Benefits:
    - Better search coverage (different phrasings of same question)
    - Handles user intent variations
    - Improves recall without sacrificing precision
    
    Usage:
        rewriter = QueryRewriter()
        variants = rewriter.expand(query, context)
        
        # Search with all variants
        for variant in variants:
            results.extend(await search(variant))
    """
    
    # =========================================================================
    # EXPANSION TEMPLATES
    # =========================================================================
    
    # Template patterns for query expansion
    EXPANSION_TEMPLATES = {
        "definition": [
            "تعريف {topic}",
            "ما هو {topic}",
            "ما هي {topic}",
            "معنى {topic}",
            "مفهوم {topic}",
        ],
        "conditions": [
            "شروط {topic}",
            "متطلبات {topic}",
            "أركان {topic}",
            "عناصر {topic}",
        ],
        "procedure": [
            "إجراءات {topic}",
            "خطوات {topic}",
            "كيفية {topic}",
            "طريقة {topic}",
        ],
        "effects": [
            "آثار {topic}",
            "نتائج {topic}",
            "أحكام {topic}",
        ],
        "article": [
            "المادة {num}",
            "نص المادة {num}",
            "المادة رقم {num}",
            "المادة {num} من {law}",
        ],
        "comparison": [
            "الفرق بين {topic1} و{topic2}",
            "مقارنة بين {topic1} و{topic2}",
            "{topic1} مقابل {topic2}",
        ],
    }
    
    # Intent detection patterns
    INTENT_PATTERNS = {
        "definition": [r"ما\s+ه[يو]", r"تعريف", r"معنى", r"مفهوم"],
        "conditions": [r"شروط", r"متطلبات", r"أركان", r"عناصر"],
        "procedure": [r"كيف", r"إجراءات", r"خطوات", r"طريقة"],
        "effects": [r"آثار", r"نتائج", r"ماذا\s+يحدث", r"ما\s+هي\s+أحكام"],
        "article_lookup": [r"المادة\s*\d+", r"الماده\s*\d+", r"م\.\s*\d+"],
        "comparison": [r"الفرق\s+بين", r"مقارنة", r"الاختلاف"],
    }
    
    # Arabic topic variations
    TOPIC_VARIATIONS = {
        "الهبة": ["الهبه", "هبة", "هبه", "التبرع", "العطية"],
        "الوصية": ["الوصيه", "وصية", "وصيه"],
        "الميراث": ["الإرث", "التركة", "التركه", "الورثة"],
        "الزواج": ["النكاح", "عقد الزواج", "الزفاف"],
        "الطلاق": ["الفسخ", "التفريق", "إنهاء الزواج"],
        "البيع": ["الشراء", "عقد البيع", "البيوع"],
        "الإيجار": ["الايجار", "الإجارة", "عقد الإيجار"],
        "الرهن": ["الرهان", "الضمان العيني"],
        "الكفالة": ["الكفاله", "الضمان الشخصي"],
        "الوكالة": ["الوكاله", "التوكيل", "التفويض"],
    }
    
    def __init__(self, max_variants: int = 5):
        """
        Initialize the rewriter.
        
        Args:
            max_variants: Maximum number of variants to generate
        """
        self.max_variants = max_variants
    
    # =========================================================================
    # INTENT DETECTION
    # =========================================================================
    
    def detect_intent(self, query: str) -> Optional[str]:
        """
        Detect the intent behind the query.
        
        Args:
            query: User's query
            
        Returns:
            Intent name or None
        """
        query_lower = query.lower()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        return None
    
    # =========================================================================
    # TOPIC EXTRACTION
    # =========================================================================
    
    def extract_topics(self, query: str) -> List[str]:
        """
        Extract legal topics from query.
        
        Args:
            query: User's query
            
        Returns:
            List of topics found
        """
        topics = []
        
        # Check for known topics
        for topic, variations in self.TOPIC_VARIATIONS.items():
            if topic in query:
                topics.append(topic)
            for var in variations:
                if var in query:
                    topics.append(topic)
                    break
        
        return list(set(topics))
    
    # =========================================================================
    # QUERY EXPANSION
    # =========================================================================
    
    def expand(
        self, 
        query: str, 
        active_articles: Optional[List[int]] = None,
        active_laws: Optional[List[str]] = None,
        active_topics: Optional[List[str]] = None
    ) -> RewriteResult:
        """
        Expand query into semantic variants.
        
        Args:
            query: Original query
            active_articles: Article numbers from context
            active_laws: Law names from context
            active_topics: Topics from context
            
        Returns:
            RewriteResult with original and variants
        """
        variants: Set[str] = {query}  # Always include original
        
        # Detect intent
        intent = self.detect_intent(query)
        
        # Extract topics from query
        query_topics = self.extract_topics(query)
        all_topics = list(set(query_topics + (active_topics or [])))
        
        # Get context
        articles = active_articles or []
        laws = active_laws or []
        
        # Apply expansions based on intent
        if intent == "definition" and all_topics:
            for topic in all_topics[:2]:
                variants.update(self._apply_templates("definition", topic=topic))
        
        elif intent == "conditions" and all_topics:
            for topic in all_topics[:2]:
                variants.update(self._apply_templates("conditions", topic=topic))
        
        elif intent == "procedure" and all_topics:
            for topic in all_topics[:2]:
                variants.update(self._apply_templates("procedure", topic=topic))
        
        elif intent == "effects" and all_topics:
            for topic in all_topics[:2]:
                variants.update(self._apply_templates("effects", topic=topic))
        
        elif intent == "article_lookup" and articles:
            for article in articles[:2]:
                law = laws[0] if laws else "النظام"
                variants.update(self._apply_templates("article", num=article, law=law))
        
        elif intent == "comparison" and len(all_topics) >= 2:
            variants.update(self._apply_templates(
                "comparison", 
                topic1=all_topics[0], 
                topic2=all_topics[1]
            ))
        
        # Add topic variations
        if all_topics:
            variants.update(self._get_topic_variations(query, all_topics))
        
        # Add article-topic combinations
        if articles and all_topics:
            for article in articles[:1]:
                for topic in all_topics[:1]:
                    variants.add(f"المادة {article} {topic}")
        
        # Limit and return
        variant_list = list(variants)[:self.max_variants]
        
        logger.info(f"🔄 Expanded '{query[:30]}...' into {len(variant_list)} variants")
        
        return RewriteResult(
            original=query,
            variants=variant_list,
            intent_detected=intent,
            expansion_type="template" if intent else "general"
        )
    
    def _apply_templates(self, template_name: str, **kwargs) -> Set[str]:
        """Apply expansion templates with given parameters."""
        results = set()
        templates = self.EXPANSION_TEMPLATES.get(template_name, [])
        
        for template in templates:
            try:
                expanded = template.format(**kwargs)
                results.add(expanded)
            except KeyError:
                continue
        
        return results
    
    def _get_topic_variations(self, query: str, topics: List[str]) -> Set[str]:
        """Generate query variations with topic synonyms."""
        variations = set()
        
        for topic in topics:
            if topic in self.TOPIC_VARIATIONS:
                for variant in self.TOPIC_VARIATIONS[topic][:2]:
                    # Replace topic with variant in query
                    new_query = query.replace(topic, variant)
                    if new_query != query:
                        variations.add(new_query)
        
        return variations
    
    # =========================================================================
    # ARABIC NORMALIZATION
    # =========================================================================
    
    def normalize_arabic(self, text: str) -> str:
        """
        Normalize Arabic text for consistent matching.
        
        - Normalize alef variations
        - Normalize taa marbuta/haa
        - Remove diacritics
        """
        # Alef normalization
        text = re.sub(r'[إأآا]', 'ا', text)
        
        # Taa marbuta at end of word
        text = re.sub(r'ة\b', 'ه', text)
        
        # Remove diacritics (tashkeel)
        text = re.sub(r'[\u064B-\u0652]', '', text)
        
        return text


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global rewriter instance
_rewriter = QueryRewriter(max_variants=5)

def expand_query(
    query: str,
    articles: Optional[List[int]] = None,
    laws: Optional[List[str]] = None,
    topics: Optional[List[str]] = None
) -> List[str]:
    """
    Convenience function to expand a query.
    
    Returns just the list of variants.
    """
    result = _rewriter.expand(
        query,
        active_articles=articles,
        active_laws=laws,
        active_topics=topics
    )
    return result.variants
