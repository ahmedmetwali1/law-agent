"""
⏱️ Adaptive Timeout Strategy v1.0

Dynamic timeout configuration based on query complexity.
Prevents timeout errors by allocating appropriate time for each phase.

Architecture:
- Estimate query complexity from word count, entity count, and intent
- Return phase-specific timeouts based on complexity
- Support graceful degradation when approaching limits

Author: Legal AI System
Created: 2026-02-06
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# COMPLEXITY LEVELS
# =============================================================================

class QueryComplexity(Enum):
    """Query complexity classification."""
    SIMPLE = "simple"      # Direct lookups, single article
    MEDIUM = "medium"      # Standard queries, 1-2 topics
    COMPLEX = "complex"    # Multi-part, legal analysis
    EXPERT = "expert"      # Requires council deliberation


@dataclass
class TimeoutConfig:
    """Timeout configuration for each processing phase."""
    classifier: int    # Intent classification
    search: int        # Vector/hybrid search
    council: int       # Council deliberation (if needed)
    drafter: int       # Response drafting
    total: int         # Total request timeout
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "classifier": self.classifier,
            "search": self.search,
            "council": self.council,
            "drafter": self.drafter,
            "total": self.total
        }


# =============================================================================
# ADAPTIVE TIMEOUT STRATEGY
# =============================================================================

class AdaptiveTimeoutStrategy:
    """
    Dynamic timeout management based on query complexity.
    
    Prevents timeout failures by:
    1. Analyzing query complexity
    2. Allocating appropriate time for each phase
    3. Supporting early termination for simple queries
    
    Usage:
        strategy = AdaptiveTimeoutStrategy()
        complexity = strategy.estimate_complexity(query, context)
        timeout = strategy.get_timeout_config(complexity)
        
        # Use timeout.search for search phase, etc.
    """
    
    # Phase-specific timeout configurations (in seconds)
    TIMEOUT_CONFIGS: Dict[QueryComplexity, TimeoutConfig] = {
        QueryComplexity.SIMPLE: TimeoutConfig(
            classifier=5,
            search=10,      # Fast lookup
            council=0,      # Skip council
            drafter=15,
            total=30
        ),
        QueryComplexity.MEDIUM: TimeoutConfig(
            classifier=10,
            search=20,      # Standard search
            council=30,     # Brief council
            drafter=30,
            total=90
        ),
        QueryComplexity.COMPLEX: TimeoutConfig(
            classifier=10,
            search=30,      # Deep search
            council=60,     # Full deliberation
            drafter=60,
            total=160
        ),
        QueryComplexity.EXPERT: TimeoutConfig(
            classifier=10,
            search=45,      # Exhaustive search
            council=90,     # Extended council
            drafter=90,
            total=240
        ),
    }
    
    # Complexity estimation thresholds
    SIMPLE_MAX_WORDS = 8
    MEDIUM_MAX_WORDS = 25
    COMPLEX_MAX_WORDS = 50
    
    # Intent classifications that indicate simple queries
    SIMPLE_INTENTS = {"LEGAL_SIMPLE", "ARTICLE_LOOKUP", "GREETING", "SMALL_TALK"}
    
    # Keywords that indicate complex queries
    COMPLEX_KEYWORDS = [
        "مقارنة", "تحليل", "اختلاف", "شرح مفصل",
        "جميع", "كافة", "تفصيلي", "متعمق",
        "compare", "analyze", "detailed", "comprehensive"
    ]
    
    def estimate_complexity(
        self, 
        query: str,
        intent: Optional[str] = None,
        entity_count: int = 0,
        is_multi_turn: bool = False
    ) -> QueryComplexity:
        """
        Estimate query complexity for timeout allocation.
        
        Args:
            query: The user's query text
            intent: Classified intent (if available)
            entity_count: Number of entities (articles + laws)
            is_multi_turn: Whether this is part of a multi-turn conversation
            
        Returns:
            QueryComplexity enum value
            
        Example:
            >>> strategy.estimate_complexity("ما هي المادة 368")
            QueryComplexity.SIMPLE
            >>> strategy.estimate_complexity("اشرح لي بالتفصيل الفرق بين الهبة والوصية")
            QueryComplexity.COMPLEX
        """
        if not query:
            return QueryComplexity.SIMPLE
        
        query_clean = query.strip()
        word_count = len(query_clean.split())
        
        # Check for simple intent classification
        if intent and intent in self.SIMPLE_INTENTS:
            logger.debug(f"Simple intent detected: {intent}")
            return QueryComplexity.SIMPLE
        
        # Check for complex keywords
        has_complex_keywords = any(kw in query_clean for kw in self.COMPLEX_KEYWORDS)
        
        # Score-based complexity estimation
        complexity_score = 0
        
        # Word count contribution (0-3 points)
        if word_count <= self.SIMPLE_MAX_WORDS:
            complexity_score += 0
        elif word_count <= self.MEDIUM_MAX_WORDS:
            complexity_score += 1
        elif word_count <= self.COMPLEX_MAX_WORDS:
            complexity_score += 2
        else:
            complexity_score += 3
        
        # Entity count contribution (0-2 points)
        if entity_count <= 1:
            complexity_score += 0
        elif entity_count <= 3:
            complexity_score += 1
        else:
            complexity_score += 2
        
        # Complex keywords contribution (0-2 points)
        if has_complex_keywords:
            complexity_score += 2
        
        # Multi-turn contribution (0-1 points)
        if is_multi_turn:
            complexity_score += 1
        
        # Map score to complexity
        if complexity_score <= 1:
            result = QueryComplexity.SIMPLE
        elif complexity_score <= 3:
            result = QueryComplexity.MEDIUM
        elif complexity_score <= 5:
            result = QueryComplexity.COMPLEX
        else:
            result = QueryComplexity.EXPERT
        
        logger.info(f"⏱️ Complexity: {result.value} (score={complexity_score}, words={word_count})")
        
        return result
    
    def get_timeout_config(self, complexity: QueryComplexity) -> TimeoutConfig:
        """
        Get timeout configuration for a complexity level.
        
        Args:
            complexity: QueryComplexity enum value
            
        Returns:
            TimeoutConfig with phase-specific timeouts
        """
        return self.TIMEOUT_CONFIGS.get(complexity, self.TIMEOUT_CONFIGS[QueryComplexity.MEDIUM])
    
    def get_phase_timeout(self, phase: str, complexity: QueryComplexity) -> int:
        """
        Get timeout for a specific processing phase.
        
        Args:
            phase: One of "classifier", "search", "council", "drafter", "total"
            complexity: QueryComplexity enum value
            
        Returns:
            Timeout in seconds
        """
        config = self.get_timeout_config(complexity)
        return getattr(config, phase, 30)  # Default 30s
    
    def should_skip_council(self, complexity: QueryComplexity) -> bool:
        """
        Determine if council phase should be skipped.
        
        Simple queries don't need council deliberation.
        """
        return complexity == QueryComplexity.SIMPLE
    
    def get_search_limit(self, complexity: QueryComplexity) -> int:
        """
        Get result limit for search based on complexity.
        
        Simpler queries need fewer results.
        """
        limits = {
            QueryComplexity.SIMPLE: 5,
            QueryComplexity.MEDIUM: 10,
            QueryComplexity.COMPLEX: 15,
            QueryComplexity.EXPERT: 20,
        }
        return limits.get(complexity, 10)


# =============================================================================
# TIMEOUT DECORATOR (OPTIONAL)
# =============================================================================

import asyncio
from functools import wraps

def with_adaptive_timeout(phase: str):
    """
    Decorator to apply adaptive timeout to async functions.
    
    Usage:
        @with_adaptive_timeout("search")
        async def search_documents(query, complexity):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            complexity = kwargs.get("complexity", QueryComplexity.MEDIUM)
            strategy = AdaptiveTimeoutStrategy()
            timeout_seconds = strategy.get_phase_timeout(phase, complexity)
            
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Timeout in {phase} phase after {timeout_seconds}s")
                raise TimeoutError(f"{phase} phase exceeded timeout of {timeout_seconds}s")
        
        return wrapper
    return decorator


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global instance for easy access
_default_strategy = AdaptiveTimeoutStrategy()

def get_timeout(phase: str, query: str, intent: Optional[str] = None) -> int:
    """
    Convenience function to get timeout for a phase.
    
    Args:
        phase: Processing phase name
        query: User query for complexity estimation
        intent: Optional intent classification
        
    Returns:
        Timeout in seconds
    """
    complexity = _default_strategy.estimate_complexity(query, intent=intent)
    return _default_strategy.get_phase_timeout(phase, complexity)
