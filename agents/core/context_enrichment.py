"""
🔍 Context Enrichment Layer v1.0

Enriches ambiguous queries with conversation context.
Solves the "في أي نظام" problem by detecting ambiguity and resolving with context.

Architecture:
1. Detect if query is ambiguous (references without clear subject)
2. If ambiguous, use ConversationContext to enrich the query
3. Return enriched query for search

Author: Legal AI System
Created: 2026-02-06
"""

import re
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

from .conversation_state_manager import ConversationContext, EnrichedQuery

logger = logging.getLogger(__name__)


# =============================================================================
# AMBIGUITY DETECTION
# =============================================================================

class AmbiguityDetector:
    """
    Detects ambiguous queries that reference previous context.
    
    Categories of ambiguity:
    1. Pronoun references: "هذا", "ذلك", "هي"
    2. Incomplete questions: "في أي", "ماذا عن"
    3. Implicit references: "المادة" (without number), "النظام" (without name)
    """
    
    # Patterns that indicate ambiguous queries requiring context
    # NOTE: We use [أا] to match both with and without hamza
    AMBIGUOUS_PATTERNS = [
        # Incomplete locational questions - handles أي and اي
        (r'^في\s*[أا]ي\s*(نظام|قانون|باب|فصل|مادة)?[؟?]?$', 'LOCATION_QUESTION'),
        (r'^ب[أا]ي\s*(نظام|قانون)?[؟?]?$', 'LOCATION_QUESTION'),
        (r'^[أا]ين\s+(ه[ذي]ا?|تجد|يوجد|توجد)?[؟?]?$', 'LOCATION_QUESTION'),
        
        # Pronoun-based questions
        (r'^ماذا\s+عنه?ا?[؟?]?$', 'PRONOUN_REFERENCE'),
        (r'^و?ما\s+ه[يو]ا?[؟?]?$', 'PRONOUN_REFERENCE'),
        (r'^و?ه[ذي]ا?[؟?]?$', 'PRONOUN_REFERENCE'),
        (r'^وكذلك[؟?]?$', 'PRONOUN_REFERENCE'),
        
        # Continuation patterns - handles أيضا and ايضا
        (r'^و?\s*([أا]يضا|كذلك|كمان)[؟?]?$', 'CONTINUATION'),
        (r'^المزيد[؟?]?$', 'CONTINUATION'),
        (r'^[أا]كثر[؟?]?$', 'CONTINUATION'),
        (r'^تفاصيل[؟?]?$', 'CONTINUATION'),
        
        # Implicit article reference (المادة without number)
        (r'^الماد[ةه]\s*(التالية|السابقة|[أا]لأولى)?[؟?]?$', 'IMPLICIT_ARTICLE'),
        (r'^والماد[ةه]\s*(التالية)?[؟?]?$', 'IMPLICIT_ARTICLE'),
        
        # Short ambiguous queries
        (r'^(نعم|لا|طيب|تمام|[أا]كيد)[؟?]?$', 'CONFIRMATION'),
    ]
    
    # Minimum query length to be considered complete
    MIN_COMPLETE_QUERY_LENGTH = 8
    
    # Words that make a short query complete
    COMPLETENESS_INDICATORS = [
        'المادة', 'نظام', 'قانون', 'تعريف', 'شروط', 'إجراءات',
        'ما هي', 'ما هو', 'كيف', 'متى', 'أين', 'لماذا'
    ]
    
    def detect_ambiguity(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Detect if a query is ambiguous and needs context enrichment.
        
        Args:
            query: User's query string
            
        Returns:
            Tuple of (is_ambiguous, ambiguity_type)
            
        Example:
            >>> detector.detect_ambiguity("في أي نظام")
            (True, 'LOCATION_QUESTION')
            >>> detector.detect_ambiguity("ما هي الهبة")
            (False, None)
        """
        if not query:
            return True, 'EMPTY'
        
        query_clean = query.strip()
        
        # Check against ambiguous patterns
        for pattern, ambiguity_type in self.AMBIGUOUS_PATTERNS:
            if re.match(pattern, query_clean, re.IGNORECASE):
                logger.info(f"🔍 Ambiguity detected: {ambiguity_type} for query '{query_clean}'")
                return True, ambiguity_type
        
        # Check for very short queries without completeness indicators
        if len(query_clean) < self.MIN_COMPLETE_QUERY_LENGTH:
            has_indicator = any(ind in query_clean for ind in self.COMPLETENESS_INDICATORS)
            if not has_indicator:
                logger.info(f"🔍 Short ambiguous query detected: '{query_clean}'")
                return True, 'SHORT_QUERY'
        
        return False, None
    
    def get_ambiguity_explanation(self, ambiguity_type: str) -> str:
        """Get human-readable explanation of ambiguity type."""
        explanations = {
            'LOCATION_QUESTION': 'السؤال عن الموقع/النظام بدون تحديد الموضوع',
            'PRONOUN_REFERENCE': 'استخدام ضمير إشارة بدون مرجع واضح',
            'CONTINUATION': 'طلب المتابعة بدون تحديد الموضوع',
            'IMPLICIT_ARTICLE': 'إشارة للمادة بدون رقم محدد',
            'CONFIRMATION': 'رد تأكيدي قصير',
            'SHORT_QUERY': 'استفسار قصير جداً',
            'EMPTY': 'استفسار فارغ'
        }
        return explanations.get(ambiguity_type, 'نوع غير معروف من الغموض')


# =============================================================================
# CONTEXT ENRICHMENT LAYER
# =============================================================================

class ContextEnrichmentLayer:
    """
    Enriches ambiguous queries with conversation context.
    
    Workflow:
    1. Check if query is ambiguous
    2. If ambiguous, use conversation context to enrich
    3. If context insufficient, flag for clarification
    
    Usage:
        enrichment = ContextEnrichmentLayer()
        context = state_manager.extract_context_from_history(history)
        
        if enrichment.is_ambiguous(query):
            enriched = enrichment.resolve_with_context(query, context)
            search_query = enriched.enriched
    """
    
    def __init__(self):
        self.detector = AmbiguityDetector()
    
    def is_ambiguous(self, query: str) -> bool:
        """Quick check if query needs enrichment."""
        is_ambiguous, _ = self.detector.detect_ambiguity(query)
        return is_ambiguous
    
    def resolve_with_context(
        self, 
        query: str, 
        context: ConversationContext
    ) -> EnrichedQuery:
        """
        Resolve an ambiguous query using conversation context.
        
        Args:
            query: The ambiguous query
            context: Extracted conversation context
            
        Returns:
            EnrichedQuery with either enriched text or clarification flag
            
        Example:
            Query: "في أي نظام"
            Context: {articles: [368], topics: ["الهبة"], laws: ["المعاملات المدنية"]}
            Result: "في أي نظام توجد المادة 368 المتعلقة بالهبة"
        """
        is_ambiguous, ambiguity_type = self.detector.detect_ambiguity(query)
        
        if not is_ambiguous:
            # Query is complete, return as-is
            return EnrichedQuery(
                original=query,
                enriched=query,
                confidence=1.0
            )
        
        # Check if we have enough context
        if context.is_empty():
            logger.warning(f"⚠️ Ambiguous query but no context available: '{query}'")
            return EnrichedQuery(
                original=query,
                enriched=query,
                fallback_used=True,
                requires_clarification=True,
                confidence=0.2
            )
        
        # Build enriched query based on ambiguity type
        enriched, entities_used = self._build_enriched_query(
            query, 
            context, 
            ambiguity_type
        )
        
        # Calculate confidence based on context completeness
        confidence = self._calculate_confidence(context, entities_used)
        
        logger.info(f"✅ Query enriched: '{query}' → '{enriched}' (confidence: {confidence:.2f})")
        
        return EnrichedQuery(
            original=query,
            enriched=enriched,
            entities_used=entities_used,
            fallback_used=False,
            requires_clarification=confidence < 0.5,
            confidence=confidence
        )
    
    def _build_enriched_query(
        self, 
        query: str, 
        context: ConversationContext,
        ambiguity_type: Optional[str]
    ) -> Tuple[str, List[str]]:
        """
        Build the enriched query string.
        
        Args:
            query: Original query
            context: Conversation context
            ambiguity_type: Type of ambiguity detected
            
        Returns:
            Tuple of (enriched_query, entities_used)
        """
        entities_used = []
        parts = [query.strip()]
        
        # Handle different ambiguity types
        if ambiguity_type == 'LOCATION_QUESTION':
            # "في أي نظام" → Add article and topic context
            if context.active_articles:
                article = context.active_articles[-1]  # Most recent
                parts.append(f"المادة {article}")
                entities_used.append(f"المادة {article}")
            
            if context.active_topics:
                topic = context.active_topics[-1]
                parts.append(f"المتعلقة بـ{topic}")
                entities_used.append(topic)
            
            if context.active_laws:
                law = context.active_laws[-1]
                parts.append(f"في {law}")
                entities_used.append(law)
        
        elif ambiguity_type in ('PRONOUN_REFERENCE', 'CONTINUATION'):
            # "ماذا عنها" → Use all available context
            if context.active_topics:
                topic = context.active_topics[-1]
                parts = [f"{query} {topic}"]
                entities_used.append(topic)
            
            if context.active_articles:
                article = context.active_articles[-1]
                parts.append(f"المادة {article}")
                entities_used.append(f"المادة {article}")
            
            if context.active_laws:
                law = context.active_laws[-1]
                parts.append(f"في {law}")
                entities_used.append(law)
        
        elif ambiguity_type == 'IMPLICIT_ARTICLE':
            # "المادة التالية" → Use article context
            if context.active_articles:
                # Try to infer next article
                last_article = context.active_articles[-1]
                next_article = last_article + 1
                parts = [f"المادة {next_article}"]
                entities_used.append(f"المادة {next_article}")
                
                if context.active_laws:
                    law = context.active_laws[-1]
                    parts.append(f"من {law}")
                    entities_used.append(law)
        
        elif ambiguity_type in ('SHORT_QUERY', 'CONFIRMATION'):
            # Add topic and article context
            if context.active_topics:
                topic = context.active_topics[-1]
                parts.append(topic)
                entities_used.append(topic)
            
            if context.active_articles:
                article = context.active_articles[-1]
                parts.append(f"المادة {article}")
                entities_used.append(f"المادة {article}")
        
        else:
            # Generic enrichment - add most relevant context
            if context.active_topics:
                parts.append(context.active_topics[-1])
                entities_used.append(context.active_topics[-1])
        
        # Build final enriched query
        enriched = " ".join(parts)
        
        # Clean up any awkward spacing
        enriched = re.sub(r'\s+', ' ', enriched).strip()
        
        return enriched, entities_used
    
    def _calculate_confidence(
        self, 
        context: ConversationContext, 
        entities_used: List[str]
    ) -> float:
        """
        Calculate confidence in the enrichment.
        
        Higher confidence when:
        - More entities were available
        - Multiple entity types were used
        - Context is recent
        """
        if not entities_used:
            return 0.3
        
        # Base confidence from number of entities used
        base_confidence = min(0.5 + (len(entities_used) * 0.15), 0.95)
        
        # Bonus for having article + topic
        has_article = any('المادة' in e for e in entities_used)
        has_topic = any(e in str(context.active_topics) for e in entities_used)
        
        if has_article and has_topic:
            base_confidence += 0.1
        
        # Use original context confidence as a factor
        final_confidence = base_confidence * (0.5 + context.confidence * 0.5)
        
        return min(1.0, final_confidence)
    
    # =========================================================================
    # CLARIFICATION HANDLING
    # =========================================================================
    
    def build_clarification_prompt(
        self, 
        query: str, 
        context: ConversationContext
    ) -> str:
        """
        Build a clarification prompt to ask the user.
        
        Used when context is insufficient to resolve ambiguity.
        
        Args:
            query: Original query
            context: Available context (may be partial)
            
        Returns:
            Arabic clarification prompt
        """
        options = []
        
        # Build options from context
        if context.active_articles:
            for article in context.active_articles[-3:]:  # Last 3 articles
                options.append(f"المادة {article}")
        
        if context.active_topics:
            for topic in context.active_topics[-3:]:
                options.append(topic)
        
        if not options:
            return "عذراً، هل يمكنك توضيح سؤالك أكثر؟ ما الموضوع أو المادة التي تستفسر عنها؟"
        
        # Build numbered options
        options_text = "\n".join([f"{i+1}️⃣ {opt}" for i, opt in enumerate(options)])
        
        return f"""
لم أفهم بالضبط. هل تقصد:
{options_text}

أو يمكنك توضيح سؤالك بشكل أكثر تفصيلاً.
""".strip()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def enrich_query_with_context(
    query: str,
    chat_history: List,
    max_context_messages: int = 5
) -> EnrichedQuery:
    """
    Convenience function to enrich a query with context in one call.
    
    Args:
        query: Current user query
        chat_history: List of previous messages
        max_context_messages: Number of previous messages to consider
        
    Returns:
        EnrichedQuery object
        
    Example:
        >>> history = [
        ...     {"role": "user", "content": "ما هي الهبة"},
        ...     {"role": "assistant", "content": "الهبة هي..."},
        ...     {"role": "user", "content": "المادة 368"}
        ... ]
        >>> result = enrich_query_with_context("في أي نظام", history)
        >>> result.enriched
        "في أي نظام المادة 368 المتعلقة بـالهبة"
    """
    from .conversation_state_manager import ConversationStateManager
    
    state_manager = ConversationStateManager(max_history_messages=max_context_messages)
    enrichment_layer = ContextEnrichmentLayer()
    
    # Extract context
    context = state_manager.extract_context_from_history(chat_history, current_query=query)
    
    # Check if enrichment needed
    if not enrichment_layer.is_ambiguous(query):
        return EnrichedQuery(original=query, enriched=query, confidence=1.0)
    
    # Enrich the query
    return enrichment_layer.resolve_with_context(query, context)
