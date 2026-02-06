"""
🎯 Response Quality Predictor v1.0

Validates response quality before sending to user.
Prevents hallucinations by checking relevance, source grounding, and consistency.

Architecture:
- Multi-dimension quality scoring
- Source verification
- Context consistency check
- Hallucination detection

Author: Legal AI System
Created: 2026-02-06
"""

import re
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class QualityLevel(Enum):
    """Quality classification levels."""
    HIGH = "high"          # >0.8 - Ready to send
    MEDIUM = "medium"      # 0.6-0.8 - May need clarification
    LOW = "low"            # 0.4-0.6 - Should clarify
    FAILED = "failed"      # <0.4 - Should not send


@dataclass
class QualityScore:
    """Comprehensive quality assessment result."""
    overall: float                              # 0.0 - 1.0
    level: QualityLevel = QualityLevel.MEDIUM
    checks: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    should_clarify: bool = False
    clarification_prompt: Optional[str] = None
    
    def __post_init__(self):
        # Set level based on overall score
        if self.overall >= 0.8:
            self.level = QualityLevel.HIGH
        elif self.overall >= 0.6:
            self.level = QualityLevel.MEDIUM
        elif self.overall >= 0.4:
            self.level = QualityLevel.LOW
        else:
            self.level = QualityLevel.FAILED
        
        # Set clarification flag
        self.should_clarify = self.overall < 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "level": self.level.value,
            "checks": self.checks,
            "issues": self.issues,
            "should_clarify": self.should_clarify
        }


# =============================================================================
# RESPONSE QUALITY PREDICTOR
# =============================================================================

class ResponseQualityPredictor:
    """
    Validates response quality before sending to user.
    
    Checks:
    1. Relevance - Does response match the query intent?
    2. Source Grounding - Is response supported by sources?
    3. Consistency - Is response consistent with context?
    4. Completeness - Does response fully answer the question?
    5. Hallucination - Are there unsupported claims?
    
    Usage:
        predictor = ResponseQualityPredictor()
        score = predictor.validate(query, response, context, sources)
        
        if score.should_clarify:
            ask_user(score.clarification_prompt)
    """
    
    # Keywords that indicate potential hallucination
    HALLUCINATION_INDICATORS = [
        "من المعروف أن",      # "It is known that" - often unsupported
        "بشكل عام",           # "Generally" - vague
        "يُعتقد أن",          # "It is believed" - uncertain
        "ربما",               # "Maybe" - uncertain
        "قد يكون",            # "Might be" - uncertain
        "في معظم الحالات",    # "In most cases" - vague
    ]
    
    # Article pattern for extraction
    ARTICLE_PATTERN = r'(?:المادة|الماده|مادة|ماده)\s*(?:رقم\s*)?(\d+)'
    
    # Law pattern for extraction
    LAW_PATTERN = r'(?:نظام|قانون)\s+([\w\s]+?)(?:\s+(?:الصادر|رقم|\.)|$)'
    
    def __init__(self, min_sources: int = 1, strict_mode: bool = False):
        """
        Initialize the predictor.
        
        Args:
            min_sources: Minimum number of sources required
            strict_mode: If True, be more strict with quality checks
        """
        self.min_sources = min_sources
        self.strict_mode = strict_mode
    
    # =========================================================================
    # MAIN VALIDATION
    # =========================================================================
    
    def validate(
        self,
        query: str,
        response: str,
        active_articles: Optional[List[int]] = None,
        active_laws: Optional[List[str]] = None,
        active_topics: Optional[List[str]] = None,
        sources: Optional[List[Dict]] = None
    ) -> QualityScore:
        """
        Validate response quality.
        
        Args:
            query: Original user query
            response: Generated response
            active_articles: Articles from conversation context
            active_laws: Laws from conversation context
            active_topics: Topics from conversation context
            sources: Source documents used to generate response
            
        Returns:
            QualityScore with detailed assessment
        """
        if not response:
            return QualityScore(
                overall=0.0,
                issues=["Response is empty"]
            )
        
        sources = sources or []
        active_articles = active_articles or []
        active_laws = active_laws or []
        active_topics = active_topics or []
        
        # Run all checks
        checks = {}
        issues = []
        
        # 1. Relevance Check
        relevance, relevance_issues = self._check_relevance(
            query, response, active_articles, active_laws, active_topics
        )
        checks["relevance"] = relevance
        issues.extend(relevance_issues)
        
        # 2. Source Grounding Check
        grounding, grounding_issues = self._check_source_grounding(response, sources)
        checks["source_grounding"] = grounding
        issues.extend(grounding_issues)
        
        # 3. Consistency Check
        consistency, consistency_issues = self._check_consistency(
            response, active_articles, active_laws
        )
        checks["consistency"] = consistency
        issues.extend(consistency_issues)
        
        # 4. Completeness Check
        completeness, completeness_issues = self._check_completeness(query, response)
        checks["completeness"] = completeness
        issues.extend(completeness_issues)
        
        # 5. Hallucination Check
        hallucination, hallucination_issues = self._check_hallucination(response)
        checks["no_hallucination"] = hallucination
        issues.extend(hallucination_issues)
        
        # Calculate overall score (weighted average)
        weights = {
            "relevance": 0.25,
            "source_grounding": 0.25,
            "consistency": 0.20,
            "completeness": 0.15,
            "no_hallucination": 0.15
        }
        
        overall = sum(
            checks.get(check, 0.5) * weight 
            for check, weight in weights.items()
        )
        
        # Build clarification prompt if needed
        clarification = None
        if overall < 0.7 and issues:
            clarification = self._build_clarification_prompt(query, issues)
        
        score = QualityScore(
            overall=overall,
            checks=checks,
            issues=issues[:5],  # Limit issues
            clarification_prompt=clarification
        )
        
        logger.info(f"🎯 Quality Score: {overall:.2f} ({score.level.value})")
        
        return score
    
    # =========================================================================
    # INDIVIDUAL CHECKS
    # =========================================================================
    
    def _check_relevance(
        self,
        query: str,
        response: str,
        active_articles: List[int],
        active_laws: List[str],
        active_topics: List[str]
    ) -> tuple[float, List[str]]:
        """Check if response is relevant to query and context."""
        issues = []
        score = 1.0
        
        # Extract mentioned entities from response
        response_articles = self._extract_articles(response)
        response_laws = self._extract_laws(response)
        
        # Check article relevance
        if active_articles:
            if not any(a in response_articles for a in active_articles):
                score -= 0.3
                issues.append(f"Response doesn't mention expected articles: {active_articles}")
        
        # Check law relevance
        if active_laws:
            law_mentioned = any(
                law.lower() in response.lower() 
                for law in active_laws
            )
            if not law_mentioned:
                score -= 0.2
                issues.append(f"Response doesn't mention expected laws: {active_laws}")
        
        # Check topic relevance
        if active_topics:
            topic_mentioned = any(
                topic in response 
                for topic in active_topics
            )
            if not topic_mentioned:
                score -= 0.2
                issues.append(f"Response doesn't address expected topics: {active_topics}")
        
        return max(0.0, score), issues
    
    def _check_source_grounding(
        self,
        response: str,
        sources: List[Dict]
    ) -> tuple[float, List[str]]:
        """Check if response is grounded in sources."""
        issues = []
        
        if not sources:
            if self.strict_mode:
                return 0.3, ["No sources provided for response"]
            return 0.6, []  # Lenient if no sources required
        
        if len(sources) < self.min_sources:
            issues.append(f"Only {len(sources)} sources, minimum {self.min_sources} required")
            return 0.5, issues
        
        # Check if response articles are in sources
        response_articles = self._extract_articles(response)
        source_articles = set()
        
        for source in sources:
            content = source.get("content", "") or source.get("text", "")
            source_articles.update(self._extract_articles(content))
        
        if response_articles:
            grounded = sum(1 for a in response_articles if a in source_articles)
            grounding_ratio = grounded / len(response_articles) if response_articles else 1.0
            
            if grounding_ratio < 0.5:
                issues.append("Some articles mentioned are not in sources")
                return 0.5, issues
        
        return 1.0, issues
    
    def _check_consistency(
        self,
        response: str,
        active_articles: List[int],
        active_laws: List[str]
    ) -> tuple[float, List[str]]:
        """Check response consistency with context."""
        issues = []
        
        # Check for contradictory article references
        response_articles = self._extract_articles(response)
        
        # If context has specific articles but response mentions very different ones
        if active_articles and response_articles:
            # Allow some flexibility (nearby articles are okay)
            has_relevant = any(
                any(abs(ra - ca) <= 10 for ca in active_articles)
                for ra in response_articles
            )
            if not has_relevant:
                issues.append("Response mentions unrelated articles")
                return 0.6, issues
        
        return 1.0, issues
    
    def _check_completeness(
        self,
        query: str,
        response: str
    ) -> tuple[float, List[str]]:
        """Check if response fully answers the question."""
        issues = []
        
        # Check response length (too short might be incomplete)
        if len(response) < 50:
            issues.append("Response may be too brief")
            return 0.5, issues
        
        # Check for question indicators that should be answered
        question_words = ["ما هي", "ما هو", "كيف", "متى", "أين", "لماذا", "شروط"]
        has_question = any(qw in query for qw in question_words)
        
        # Check for answer indicators
        answer_indicators = ["هي", "هو", "يجب", "يمكن", "تشمل", "تتضمن", "من خلال"]
        has_answer = any(ai in response for ai in answer_indicators)
        
        if has_question and not has_answer:
            issues.append("Response may not directly answer the question")
            return 0.7, issues
        
        return 1.0, issues
    
    def _check_hallucination(
        self,
        response: str
    ) -> tuple[float, List[str]]:
        """Check for potential hallucination indicators."""
        issues = []
        
        # Count hallucination indicators
        indicator_count = sum(
            1 for indicator in self.HALLUCINATION_INDICATORS
            if indicator in response
        )
        
        if indicator_count >= 3:
            issues.append("Response contains multiple uncertainty indicators")
            return 0.4, issues
        elif indicator_count >= 1:
            return 0.8, []
        
        return 1.0, issues
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _extract_articles(self, text: str) -> Set[int]:
        """Extract article numbers from text."""
        matches = re.findall(self.ARTICLE_PATTERN, text)
        return {int(m) for m in matches if m.isdigit()}
    
    def _extract_laws(self, text: str) -> Set[str]:
        """Extract law names from text."""
        matches = re.findall(self.LAW_PATTERN, text)
        return {m.strip() for m in matches if len(m.strip()) > 3}
    
    def _build_clarification_prompt(
        self,
        query: str,
        issues: List[str]
    ) -> str:
        """Build clarification prompt for user."""
        if "articles" in str(issues).lower():
            return "هل يمكنك تحديد رقم المادة القانونية المطلوبة؟"
        elif "laws" in str(issues).lower():
            return "هل يمكنك تحديد اسم النظام أو القانون المطلوب؟"
        elif "sources" in str(issues).lower():
            return "لم أجد مصادر كافية. هل يمكنك توضيح سؤالك أكثر؟"
        else:
            return "هل يمكنك توضيح سؤالك أكثر حتى أتمكن من الإجابة بدقة؟"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global instance
_predictor = ResponseQualityPredictor()

def validate_response(
    query: str,
    response: str,
    articles: Optional[List[int]] = None,
    laws: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    sources: Optional[List[Dict]] = None
) -> QualityScore:
    """
    Convenience function to validate a response.
    
    Returns QualityScore with overall quality assessment.
    """
    return _predictor.validate(
        query=query,
        response=response,
        active_articles=articles,
        active_laws=laws,
        active_topics=topics,
        sources=sources
    )
