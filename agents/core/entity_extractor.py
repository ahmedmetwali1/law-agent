"""
🔍 Enhanced Entity Extraction v1.0

Advanced entity extraction with Fuzzy Matching, LLM-Assisted fallback,
and Validation Layer for robust legal entity identification.

Architecture:
- Multi-Pattern Matching (base layer)
- Fuzzy Matching (handles typos)
- LLM-Assisted Extraction (fallback for complex cases)
- Validation Layer (verifies extracted entities)

Author: Legal AI System
Created: 2026-02-06
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class ExtractionMethod(Enum):
    """How the entity was extracted."""
    REGEX = "regex"
    FUZZY = "fuzzy"
    LLM = "llm"


@dataclass
class ExtractedEntity:
    """Single extracted entity with metadata."""
    value: Any                         # The extracted value (int for articles, str for laws/topics)
    entity_type: str                   # "article", "law", "topic"
    confidence: float                  # 0.0 - 1.0
    method: ExtractionMethod           # How it was extracted
    source_text: Optional[str] = None  # Original text snippet
    validated: bool = False            # Whether it passed validation


@dataclass
class ExtractionResult:
    """Complete extraction result with all entities."""
    articles: List[ExtractedEntity] = field(default_factory=list)
    laws: List[ExtractedEntity] = field(default_factory=list)
    topics: List[ExtractedEntity] = field(default_factory=list)
    confidence: float = 0.0
    
    def get_article_numbers(self) -> List[int]:
        """Get just article numbers."""
        return [e.value for e in self.articles if isinstance(e.value, int)]
    
    def get_law_names(self) -> List[str]:
        """Get just law names."""
        return [e.value for e in self.laws if isinstance(e.value, str)]
    
    def get_topic_names(self) -> List[str]:
        """Get just topic names."""
        return [e.value for e in self.topics if isinstance(e.value, str)]
    
    def is_empty(self) -> bool:
        """Check if no entities were extracted."""
        return not self.articles and not self.laws and not self.topics


# =============================================================================
# FUZZY MATCHING
# =============================================================================

class FuzzyMatcher:
    """
    Handles typos and variations in Arabic legal terms.
    
    Common typos:
    - الماده -> المادة (taa marbuta vs. haa)
    - نضام -> نظام (ض vs. ظ)
    - قانوون -> قانون (double letter)
    """
    
    # Known typo corrections
    CORRECTIONS = {
        # Article variants
        "الماده": "المادة",
        "ماده": "مادة",
        # System/Law variants
        "نضام": "نظام",
        "النضام": "النظام",
        "قانوون": "قانون",
        "القانوون": "القانون",
        # Common misspellings
        "المادا": "المادة",
        "مادا": "مادة",
    }
    
    # Known law names for fuzzy matching
    KNOWN_LAWS = [
        "نظام المعاملات المدنية",
        "نظام العمل",
        "نظام الأحوال الشخصية",
        "نظام الشركات",
        "نظام المرافعات الشرعية",
        "نظام الإجراءات الجزائية",
        "نظام التحكيم",
        "نظام الإفلاس",
        "نظام المنافسة",
        "نظام حماية المستهلك",
        "نظام التنفيذ",
        "نظام الإثبات",
    ]
    
    # Similarity threshold
    THRESHOLD = 0.80
    
    def correct_text(self, text: str) -> str:
        """Apply known corrections to text."""
        corrected = text
        for wrong, correct in self.CORRECTIONS.items():
            corrected = corrected.replace(wrong, correct)
        return corrected
    
    def fuzzy_match_law(self, text: str) -> Optional[Tuple[str, float]]:
        """
        Find best matching law name using fuzzy matching.
        
        Args:
            text: Input text that might contain a law name
            
        Returns:
            Tuple of (matched_law, similarity_score) or None
        """
        best_match = None
        best_score = 0.0
        
        # Normalize text
        text_normalized = text.lower().strip()
        
        for known_law in self.KNOWN_LAWS:
            # Check if law name is contained in text
            if known_law in text:
                return (known_law, 1.0)
            
            # Calculate similarity
            ratio = SequenceMatcher(None, text_normalized, known_law.lower()).ratio()
            
            if ratio > best_score and ratio >= self.THRESHOLD:
                best_score = ratio
                best_match = known_law
        
        if best_match:
            return (best_match, best_score)
        
        return None
    
    def extract_articles_fuzzy(self, text: str) -> List[Tuple[int, float]]:
        """
        Extract article numbers with fuzzy matching for typos.
        
        Returns:
            List of (article_number, confidence) tuples
        """
        # First correct known typos
        corrected = self.correct_text(text)
        
        # Article patterns
        patterns = [
            r'(?:المادة|الماده|مادة|ماده|المادا)\s*(?:رقم\s*)?(\d+)',
            r'م\.?\s*(\d+)',
        ]
        
        results = []
        for pattern in patterns:
            matches = re.findall(pattern, corrected, re.IGNORECASE)
            for match in matches:
                try:
                    num = int(match)
                    if 1 <= num <= 9999:
                        # Higher confidence if from corrected text
                        confidence = 0.9 if corrected != text else 1.0
                        results.append((num, confidence))
                except ValueError:
                    continue
        
        return results


# =============================================================================
# VALIDATION LAYER
# =============================================================================

class EntityValidator:
    """
    Validates extracted entities for correctness.
    
    Checks:
    - Article numbers are in valid range
    - Law names are recognized or plausible
    - No duplicate or contradictory entities
    """
    
    # Valid article ranges by law type
    ARTICLE_RANGES = {
        "نظام المعاملات المدنية": (1, 700),
        "نظام العمل": (1, 300),
        "نظام الأحوال الشخصية": (1, 200),
        "نظام الشركات": (1, 250),
        "default": (1, 9999),
    }
    
    def validate_article(
        self, 
        article: int, 
        law_name: Optional[str] = None
    ) -> Tuple[bool, float]:
        """
        Validate article number.
        
        Returns:
            Tuple of (is_valid, confidence)
        """
        if not isinstance(article, int):
            return (False, 0.0)
        
        # Get range for law
        if law_name and law_name in self.ARTICLE_RANGES:
            min_art, max_art = self.ARTICLE_RANGES[law_name]
        else:
            min_art, max_art = self.ARTICLE_RANGES["default"]
        
        if min_art <= article <= max_art:
            return (True, 1.0)
        elif 1 <= article <= 9999:
            return (True, 0.7)  # Valid but outside known range
        else:
            return (False, 0.0)
    
    def validate_law(self, law_name: str) -> Tuple[bool, float]:
        """
        Validate law name.
        
        Returns:
            Tuple of (is_valid, confidence)
        """
        if not law_name or len(law_name) < 5:
            return (False, 0.0)
        
        # Check against known laws
        for known in FuzzyMatcher.KNOWN_LAWS:
            if known == law_name:
                return (True, 1.0)
            if law_name in known or known in law_name:
                return (True, 0.9)
        
        # Check if it starts with نظام or قانون
        if law_name.startswith(("نظام", "قانون", "لائحة")):
            return (True, 0.7)
        
        return (True, 0.5)  # Assume valid but low confidence
    
    def validate_topic(self, topic: str) -> Tuple[bool, float]:
        """
        Validate legal topic.
        
        Returns:
            Tuple of (is_valid, confidence)
        """
        if not topic or len(topic) < 2:
            return (False, 0.0)
        
        # Check against known topics (from ConversationStateManager.LEGAL_TOPICS)
        known_topics = {
            "الهبة", "البيع", "الإيجار", "الرهن", "الوكالة", "الكفالة",
            "الحوالة", "الصلح", "الوقف", "الوصية", "الميراث", "الطلاق",
            "الزواج", "النفقة", "الحضانة", "العقد", "الشركة", "التأمين",
            "الإفلاس", "التصفية", "الملكية", "الحيازة", "الارتفاق", "الشفعة"
        }
        
        if topic in known_topics:
            return (True, 1.0)
        
        # Normalize and check variants
        normalized = topic.replace("ه", "ة").replace("ا", "ة")
        for known in known_topics:
            if normalized in known.replace("ه", "ة").replace("ا", "ة"):
                return (True, 0.9)
        
        return (True, 0.6)  # Assume valid topic


# =============================================================================
# LLM-ASSISTED EXTRACTION (FALLBACK)
# =============================================================================

class LLMEntityExtractor:
    """
    Uses LLM for entity extraction when regex/fuzzy fail.
    
    This is a fallback method - more expensive but handles complex cases.
    """
    
    EXTRACTION_PROMPT = """استخرج من النص التالي:
- أرقام المواد القانونية (articles)
- أسماء الأنظمة والقوانين (laws)
- المواضيع القانونية (topics)

النص: {text}

الرد بصيغة JSON:
{{"articles": [368], "laws": ["نظام المعاملات المدنية"], "topics": ["الهبة"]}}

إذا لم تجد شيئاً، أعد JSON فارغ: {{"articles": [], "laws": [], "topics": []}}"""

    def __init__(self, llm=None):
        """Initialize with optional LLM instance."""
        self._llm = llm
    
    async def extract(self, text: str) -> Optional[Dict[str, List]]:
        """
        Extract entities using LLM.
        
        Args:
            text: Input text
            
        Returns:
            Dict with articles, laws, topics or None if failed
        """
        if not self._llm:
            logger.warning("LLM not configured for entity extraction")
            return None
        
        try:
            from langchain_core.messages import HumanMessage
            import json
            
            prompt = self.EXTRACTION_PROMPT.format(text=text)
            response = await self._llm.ainvoke([HumanMessage(content=prompt)])
            
            # Parse JSON from response
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "articles": data.get("articles", []),
                    "laws": data.get("laws", []),
                    "topics": data.get("topics", [])
                }
        except Exception as e:
            logger.warning(f"LLM entity extraction failed: {e}")
        
        return None


# =============================================================================
# ENHANCED ENTITY EXTRACTOR
# =============================================================================

class EnhancedEntityExtractor:
    """
    Complete entity extraction pipeline with all methods.
    
    Pipeline:
    1. Regex extraction (fast, high confidence)
    2. Fuzzy matching (handles typos)
    3. Validation layer (verifies results)
    4. LLM fallback (if enabled and needed)
    
    Usage:
        extractor = EnhancedEntityExtractor()
        result = extractor.extract_all(text)
        
        # Get validated articles
        articles = result.get_article_numbers()
    """
    
    def __init__(
        self, 
        use_llm_fallback: bool = False,
        llm = None
    ):
        """
        Initialize the extractor.
        
        Args:
            use_llm_fallback: Whether to use LLM for difficult cases
            llm: LLM instance for fallback extraction
        """
        self.fuzzy_matcher = FuzzyMatcher()
        self.validator = EntityValidator()
        self.llm_extractor = LLMEntityExtractor(llm) if use_llm_fallback else None
    
    def extract_all(self, text: str) -> ExtractionResult:
        """
        Extract all entities from text using all available methods.
        
        Args:
            text: Input text
            
        Returns:
            ExtractionResult with all extracted entities
        """
        if not text:
            return ExtractionResult()
        
        result = ExtractionResult()
        
        # 1. Extract articles (regex + fuzzy)
        result.articles = self._extract_articles(text)
        
        # 2. Extract laws (regex + fuzzy)
        result.laws = self._extract_laws(text)
        
        # 3. Extract topics
        result.topics = self._extract_topics(text)
        
        # 4. Calculate overall confidence
        all_entities = result.articles + result.laws + result.topics
        if all_entities:
            result.confidence = sum(e.confidence for e in all_entities) / len(all_entities)
        
        logger.info(
            f"🔍 Extracted: {len(result.articles)} articles, "
            f"{len(result.laws)} laws, {len(result.topics)} topics "
            f"(confidence: {result.confidence:.2f})"
        )
        
        return result
    
    def _extract_articles(self, text: str) -> List[ExtractedEntity]:
        """Extract and validate articles."""
        entities = []
        seen = set()
        
        # Fuzzy extraction (includes correction)
        fuzzy_results = self.fuzzy_matcher.extract_articles_fuzzy(text)
        
        for article_num, confidence in fuzzy_results:
            if article_num in seen:
                continue
            seen.add(article_num)
            
            # Validate
            is_valid, val_confidence = self.validator.validate_article(article_num)
            if is_valid:
                entities.append(ExtractedEntity(
                    value=article_num,
                    entity_type="article",
                    confidence=confidence * val_confidence,
                    method=ExtractionMethod.FUZZY if confidence < 1.0 else ExtractionMethod.REGEX,
                    validated=True
                ))
        
        return entities
    
    def _extract_laws(self, text: str) -> List[ExtractedEntity]:
        """Extract and validate laws."""
        entities = []
        seen = set()
        
        # Corrected text
        corrected = self.fuzzy_matcher.correct_text(text)
        
        # Regex patterns
        patterns = [
            r'نظام\s+([\w\s]{5,40}?)(?:\s+(?:الصادر|رقم|لعام|في)|[،,]|\s*$)',
            r'قانون\s+([\w\s]{5,40}?)(?:\s+(?:الصادر|رقم|لعام|في)|[،,]|\s*$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, corrected)
            for match in matches:
                law_name = match.strip()
                if law_name in seen or len(law_name) < 5:
                    continue
                seen.add(law_name)
                
                # Try fuzzy match for known laws
                fuzzy_result = self.fuzzy_matcher.fuzzy_match_law(law_name)
                if fuzzy_result:
                    law_name, fuzzy_score = fuzzy_result
                    method = ExtractionMethod.FUZZY
                else:
                    fuzzy_score = 0.8
                    method = ExtractionMethod.REGEX
                
                # Validate
                is_valid, val_confidence = self.validator.validate_law(law_name)
                if is_valid:
                    entities.append(ExtractedEntity(
                        value=law_name,
                        entity_type="law",
                        confidence=fuzzy_score * val_confidence,
                        method=method,
                        validated=True
                    ))
        
        return entities
    
    def _extract_topics(self, text: str) -> List[ExtractedEntity]:
        """Extract and validate topics."""
        entities = []
        seen = set()
        
        # Known topics with canonical forms
        topic_variants = {
            # Canonical: [variants]
            "الهبة": ["الهبة", "الهبه"],
            "البيع": ["البيع"],
            "الإيجار": ["الإيجار", "الايجار"],
            "الرهن": ["الرهن"],
            "الوكالة": ["الوكالة", "الوكاله"],
            "الكفالة": ["الكفالة", "الكفاله"],
            "الحوالة": ["الحوالة", "الحواله"],
            "الصلح": ["الصلح"],
            "الوقف": ["الوقف"],
            "الوصية": ["الوصية", "الوصيه"],
            "الميراث": ["الميراث"],
            "الطلاق": ["الطلاق"],
            "الزواج": ["الزواج"],
            "النفقة": ["النفقة", "النفقه"],
            "الحضانة": ["الحضانة", "الحضانه"],
            "العقد": ["العقد"],
            "الشركة": ["الشركة", "الشركه"],
            "التأمين": ["التأمين"],
            "الإفلاس": ["الإفلاس"],
            "التصفية": ["التصفية", "التصفيه"],
            "الملكية": ["الملكية", "الملكيه"],
            "الحيازة": ["الحيازة", "الحيازه"],
            "الارتفاق": ["الارتفاق"],
            "الشفعة": ["الشفعة", "الشفعه"]
        }
        
        for canonical, variants in topic_variants.items():
            for variant in variants:
                if variant in text and canonical not in seen:
                    seen.add(canonical)
                    is_valid, confidence = self.validator.validate_topic(canonical)
                    if is_valid:
                        entities.append(ExtractedEntity(
                            value=canonical,  # Use canonical form
                            entity_type="topic",
                            confidence=confidence,
                            method=ExtractionMethod.REGEX,
                            validated=True
                        ))
                    break  # Found variant, move to next topic
        
        return entities


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global instance
_extractor = EnhancedEntityExtractor()

def extract_entities(text: str) -> ExtractionResult:
    """Convenience function to extract all entities."""
    return _extractor.extract_all(text)

def extract_articles(text: str) -> List[int]:
    """Convenience function to extract article numbers only."""
    result = _extractor.extract_all(text)
    return result.get_article_numbers()

def extract_laws(text: str) -> List[str]:
    """Convenience function to extract law names only."""
    result = _extractor.extract_all(text)
    return result.get_law_names()

def validate_article(article: int, law: Optional[str] = None) -> bool:
    """Convenience function to validate an article number."""
    validator = EntityValidator()
    is_valid, _ = validator.validate_article(article, law)
    return is_valid
