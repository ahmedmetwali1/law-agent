"""
Self-Regulated Retrieval System
نظام الاسترجاع الذكي الذاتي

Based on 2025 research:
- "Memory in the Age of AI Agents" - Self-regulation patterns
- Fast & Slow Thinking approach (Kahneman-inspired)

Features:
- Intelligent decision when to retrieve from memory
- Cost-efficient retrieval
- Confidence-based routing
- Adaptive thresholds
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class RetrievalDecision(str, Enum):
    """Decision on whether to retrieve from memory"""
    USE_INTERNAL = "use_internal"      # Use internal knowledge
    RETRIEVE_WORKING = "retrieve_working"  # Quick retrieval from working memory
    RETRIEVE_EPISODIC = "retrieve_episodic"  # Moderate retrieval from episodes
    RETRIEVE_LONGTERM = "retrieve_longterm"  # Deep retrieval from long-term
    RETRIEVE_ALL = "retrieve_all"           # Full retrieval across all layers
    NO_RETRIEVAL = "no_retrieval"           # Skip retrieval


class ThinkingSpeed(str, Enum):
    """Thinking speed (Fast vs Slow)"""
    FAST = "fast"   # Quick, intuitive (System 1)
    SLOW = "slow"   # Deliberate, analytical (System 2)


@dataclass
class RetrievalContext:
    """Context for retrieval decision"""
    query: str
    confidence_threshold: float = 0.7
    current_context_size: int = 0
    has_recent_retrieval: bool = False
    query_complexity: str = "moderate"
    available_knowledge: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.available_knowledge is None:
            self.available_knowledge = {}


@dataclass
class RetrievalResult:
    """Result of retrieval operation"""
    decision: RetrievalDecision
    items_retrieved: List[Any]
    confidence: float
    cost_estimate: float  # Estimated computational cost
    reasoning: str
    metadata: Dict[str, Any]


class SelfRegulatedRetrieval:
    """
    Intelligent self-regulated retrieval system
    
    Makes smart decisions about when and where to retrieve information:
    - Fast thinking: Use internal knowledge when confident
    - Slow thinking: Retrieve from memory when needed
    """
    
    def __init__(self, memory_system=None):
        self.memory = memory_system
        self.retrieval_history: List[RetrievalResult] = []
        
        # Adaptive thresholds
        self.confidence_threshold = 0.7
        self.cost_budget = 1.0  # Relative cost budget
        
        logger.info("✅ Self-Regulated Retrieval initialized")
    
    def should_retrieve(self, context: RetrievalContext) -> Tuple[bool, str]:
        """
        Decide if retrieval is necessary
        
        Args:
            context: Retrieval context
        
        Returns:
            (should_retrieve, reasoning)
        """
        reasons = []
        score = 0.0
        
        # Factor 1: Internal confidence
        if context.confidence_threshold < 0.5:
            score += 3.0
            reasons.append("ثقة داخلية منخفضة")
        elif context.confidence_threshold < 0.7:
            score += 1.5
            reasons.append("ثقة داخلية متوسطة")
        
        # Factor 2: Query complexity
        if context.query_complexity == "complex":
            score += 2.0
            reasons.append("سؤال معقد")
        elif context.query_complexity == "moderate":
            score += 1.0
            reasons.append("سؤال متوسط")
        
        # Factor 3: Recent retrieval
        if not context.has_recent_retrieval:
            score += 0.5
            reasons.append("لم نسترجع معلومات مؤخراً")
        
        # Factor 4: Context size
        if context.current_context_size < 5:
            score += 1.0
            reasons.append("سياق محدود")
        
        # Decision
        should_retrieve = score >= 2.0
        reasoning = " | ".join(reasons) if reasons else "لا داعي للاسترجاع"
        
        logger.info(f"Retrieval decision: {should_retrieve} (score={score:.1f}) - {reasoning}")
        return should_retrieve, reasoning
    
    def decide_retrieval_strategy(self, context: RetrievalContext) -> RetrievalDecision:
        """
        Decide which retrieval strategy to use
        
        Args:
            context: Retrieval context
        
        Returns:
            RetrievalDecision
        """
        # Check if retrieval is needed
        should_retrieve, reasoning = self.should_retrieve(context)
        
        if not should_retrieve:
            return RetrievalDecision.USE_INTERNAL
        
        # Determine retrieval depth based on query complexity
        if context.query_complexity == "simple":
            # Quick retrieval from working memory
            return RetrievalDecision.RETRIEVE_WORKING
        
        elif context.query_complexity == "moderate":
            # Moderate retrieval from episodic
            return RetrievalDecision.RETRIEVE_EPISODIC
        
        elif context.query_complexity == "complex":
            # Deep retrieval from long-term
            return RetrievalDecision.RETRIEVE_LONGTERM
        
        else:  # expert
            # Full retrieval across all layers
            return RetrievalDecision.RETRIEVE_ALL
    
    def retrieve(
        self,
        query: str,
        context: Optional[RetrievalContext] = None,
        thinking_speed: ThinkingSpeed = ThinkingSpeed.SLOW
    ) -> RetrievalResult:
        """
        Main retrieval method with self-regulation
        
        Args:
            query: Query to retrieve information for
            context: Retrieval context (optional)
            thinking_speed: Fast or slow thinking
        
        Returns:
            RetrievalResult
        """
        # Create default context if not provided
        if context is None:
            context = RetrievalContext(query=query)
        
        # Fast thinking: quick decision, minimal retrieval
        if thinking_speed == ThinkingSpeed.FAST:
            return self._fast_retrieval(query, context)
        
        # Slow thinking: deliberate, comprehensive retrieval
        else:
            return self._slow_retrieval(query, context)
    
    def _fast_retrieval(self, query: str, context: RetrievalContext) -> RetrievalResult:
        """
        Fast retrieval (System 1 thinking)
        Quick, intuitive, low cost
        """
        logger.info("⚡ Fast retrieval mode")
        
        # Only retrieve from working memory (cheapest)
        items = []
        
        if self.memory and self.memory.working:
            items = self.memory.working.get_context(max_items=3)
        
        return RetrievalResult(
            decision=RetrievalDecision.RETRIEVE_WORKING,
            items_retrieved=items,
            confidence=0.7,
            cost_estimate=0.1,  # Low cost
            reasoning="استرجاع سريع من الذاكرة العاملة فقط",
            metadata={
                "thinking_speed": "fast",
                "items_count": len(items)
            }
        )
    
    def _slow_retrieval(self, query: str, context: RetrievalContext) -> RetrievalResult:
        """
        Slow retrieval (System 2 thinking)
        Deliberate, comprehensive, higher cost but more accurate
        """
        logger.info("🧠 Slow retrieval mode")
        
        # Decide strategy
        decision = self.decide_retrieval_strategy(context)
        
        items = []
        cost = 0.0
        
        if decision == RetrievalDecision.USE_INTERNAL:
            # No retrieval needed
            cost = 0.0
            reasoning = "المعرفة الداخلية كافية"
        
        elif decision == RetrievalDecision.RETRIEVE_WORKING:
            # Retrieve from working memory
            if self.memory and self.memory.working:
                items = self.memory.working.get_context()
            cost = 0.1
            reasoning = "استرجاع من الذاكرة العاملة"
        
        elif decision == RetrievalDecision.RETRIEVE_EPISODIC:
            # Retrieve from episodic memory
            if self.memory and self.memory.episodic:
                tags = self._extract_tags(query)
                items = self.memory.episodic.retrieve_by_tags(tags, limit=5)
            cost = 0.3
            reasoning = "استرجاع من الذاكرة الحدثية"
        
        elif decision == RetrievalDecision.RETRIEVE_LONGTERM:
            # Retrieve from long-term memory
            if self.memory and self.memory.long_term:
                tags = self._extract_tags(query)
                items = self.memory.long_term.search(tags, limit=5)
            cost = 0.5
            reasoning = "استرجاع من الذاكرة طويلة المدى"
        
        elif decision == RetrievalDecision.RETRIEVE_ALL:
            # Comprehensive retrieval from all layers
            if self.memory:
                tags = self._extract_tags(query)
                items.extend(self.memory.working.get_context())
                items.extend(self.memory.episodic.retrieve_by_tags(tags, limit=3))
                items.extend(self.memory.long_term.search(tags, limit=3))
            cost = 0.8
            reasoning = "استرجاع شامل من جميع طبقات الذاكرة"
        
        # Calculate confidence based on items retrieved
        confidence = min(0.95, 0.5 + (len(items) * 0.1))
        
        result = RetrievalResult(
            decision=decision,
            items_retrieved=items,
            confidence=confidence,
            cost_estimate=cost,
            reasoning=reasoning,
            metadata={
                "thinking_speed": "slow",
                "items_count": len(items),
                "query": query
            }
        )
        
        self.retrieval_history.append(result)
        return result
    
    def _extract_tags(self, query: str) -> List[str]:
        """Extract semantic tags from query"""
        # Simple keyword extraction
        # In real implementation, would use NLP
        words = query.split()
        
        # Filter out common words
        stopwords = ['في', 'من', 'إلى', 'على', 'هل', 'ما', 'the', 'is', 'in', 'on']
        tags = [w.lower() for w in words if len(w) > 3 and w.lower() not in stopwords]
        
        return tags[:5]  # Top 5 tags
    
    def optimize_thresholds(self) -> Dict[str, float]:
        """
        Optimize retrieval thresholds based on history
        
        Returns:
            Updated thresholds
        """
        if len(self.retrieval_history) < 10:
            return {"confidence": self.confidence_threshold}
        
        # Calculate average confidence of successful retrievals
        successful = [
            r for r in self.retrieval_history
            if len(r.items_retrieved) > 0
        ]
        
        if successful:
            avg_conf = sum(r.confidence for r in successful) / len(successful)
            
            # Adjust threshold
            if avg_conf > 0.8:
                # High success rate, can lower threshold
                self.confidence_threshold = max(0.5, self.confidence_threshold - 0.05)
            elif avg_conf < 0.6:
                # Low success rate, raise threshold
                self.confidence_threshold = min(0.9, self.confidence_threshold + 0.05)
        
        logger.info(f"Optimized confidence threshold: {self.confidence_threshold:.2f}")
        return {"confidence": self.confidence_threshold}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        if not self.retrieval_history:
            return {"retrievals": 0}
        
        return {
            "total_retrievals": len(self.retrieval_history),
            "avg_cost": sum(r.cost_estimate for r in self.retrieval_history) / len(self.retrieval_history),
            "avg_confidence": sum(r.confidence for r in self.retrieval_history) / len(self.retrieval_history),
            "avg_items": sum(len(r.items_retrieved) for r in self.retrieval_history) / len(self.retrieval_history),
            "decision_distribution": self._get_decision_distribution()
        }
    
    def _get_decision_distribution(self) -> Dict[str, int]:
        """Get distribution of retrieval decisions"""
        dist = {}
        for result in self.retrieval_history:
            decision = result.decision.value
            dist[decision] = dist.get(decision, 0) + 1
        return dist


__all__ = [
    "SelfRegulatedRetrieval",
    "RetrievalDecision",
    "ThinkingSpeed",
    "RetrievalContext",
    "RetrievalResult"
]
