"""
🧠 Conversation State Manager v1.0

Maintains conversational context across turns to prevent context loss.
Solves the "في أي نظام" problem by tracking active entities.

Architecture:
- Extract entities from each message
- Maintain active context (articles, laws, topics)
- Provide context for query enrichment

Author: Legal AI System
Created: 2026-02-06
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ConversationContext:
    """
    Immutable snapshot of conversation context at a point in time.
    
    Attributes:
        active_articles: Article numbers mentioned (e.g., [368, 375])
        active_laws: Law/system names mentioned (e.g., ["نظام المعاملات المدنية"])
        active_topics: Legal topics discussed (e.g., ["الهبة", "الوقف"])
        last_entity_type: Most recent entity type ("article", "law", "topic")
        query_history: Last N user queries
        confidence: Confidence score (0.0 - 1.0)
        extracted_at: Timestamp of extraction
    """
    active_articles: List[int] = field(default_factory=list)
    active_laws: List[str] = field(default_factory=list)
    active_topics: List[str] = field(default_factory=list)
    last_entity_type: Optional[str] = None
    query_history: List[str] = field(default_factory=list)
    confidence: float = 0.0
    extracted_at: Optional[datetime] = None
    
    def is_empty(self) -> bool:
        """Check if context has any meaningful data."""
        return (
            not self.active_articles and 
            not self.active_laws and 
            not self.active_topics
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "active_articles": self.active_articles,
            "active_laws": self.active_laws,
            "active_topics": self.active_topics,
            "last_entity_type": self.last_entity_type,
            "query_history": self.query_history[-3:],  # Limit for serialization
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None
        }


@dataclass  
class EnrichedQuery:
    """
    Result of query enrichment with context.
    
    Attributes:
        original: Original user query
        enriched: Query with context added
        entities_used: Entities that were used to enrich
        fallback_used: Whether fallback strategy was used
        requires_clarification: If true, should ask user for clarification
        confidence: Confidence in the enrichment
    """
    original: str
    enriched: str = ""
    entities_used: List[str] = field(default_factory=list)
    fallback_used: bool = False
    requires_clarification: bool = False
    confidence: float = 0.0
    
    def __post_init__(self):
        if not self.enriched:
            self.enriched = self.original


# =============================================================================
# CONVERSATION STATE MANAGER
# =============================================================================

class ConversationStateManager:
    """
    Manages conversation context across turns.
    
    Responsibilities:
    1. Extract entities from chat history
    2. Track active context (articles, laws, topics)
    3. Provide context for query enrichment
    4. Handle context decay (older messages = lower weight)
    
    Usage:
        manager = ConversationStateManager()
        context = manager.extract_context_from_history(chat_history)
        enriched = manager.enrich_query(query, context)
    """
    
    # =========================================================================
    # EXTRACTION PATTERNS
    # =========================================================================
    
    # Article patterns (reusing from hybrid_search_tool.py for consistency)
    ARTICLE_PATTERNS = [
        # Arabic patterns - standard
        r'(?:المادة|الماده)\s*(?:رقم\s*)?(\d+)',
        r'(?:مادة|ماده)\s*(?:رقم\s*)?(\d+)',
        r'م\.?\s*(\d+)',
        # Arabic patterns - with parens
        r'(?:المادة|الماده)\s*\((\d+)\)',
        # Arabic numerals
        r'(?:المادة|الماده)\s*([٠-٩]+)',
        # English patterns
        r'(?:article|Article)\s*(?:no\.?\s*)?(\d+)',
        r'(?:Art|art)\.?\s*(\d+)',
        r'(?:Section|section)\s*(\d+)',
    ]
    
    # Law/System patterns
    LAW_PATTERNS = [
        r'نظام\s+([\w\s]{5,40}?)(?:\s+(?:الصادر|رقم|لعام|في)|\s*$)',
        r'قانون\s+([\w\s]{5,40}?)(?:\s+(?:الصادر|رقم|لعام|في)|\s*$)',
        r'لائحة\s+([\w\s]{5,40}?)(?:\s+(?:الصادر|رقم|لعام|في)|\s*$)',
    ]
    
    # Common legal topics (for fallback detection)
    LEGAL_TOPICS = {
        # Arabic
        "الهبة", "الهبه", "البيع", "الإيجار", "الايجار", "الرهن", "الوكالة", "الوكاله",
        "الكفالة", "الكفاله", "الحوالة", "الحواله", "الصلح", "الوقف", "الوصية", "الوصيه",
        "الميراث", "الطلاق", "الزواج", "النفقة", "النفقه", "الحضانة", "الحضانه",
        "العقد", "الشركة", "الشركه", "التأمين", "الإفلاس", "التصفية", "التصفيه",
        "الملكية", "الملكيه", "الحيازة", "الحيازه", "الارتفاق", "الشفعة", "الشفعه",
        # English
        "gift", "sale", "lease", "mortgage", "agency", "guarantee", "settlement",
        "endowment", "will", "inheritance", "divorce", "marriage", "custody",
        "contract", "company", "insurance", "bankruptcy", "ownership", "possession"
    }
    
    # Arabic numeral conversion
    ARABIC_TO_WESTERN = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    
    def __init__(self, max_history_messages: int = 5):
        """
        Initialize the state manager.
        
        Args:
            max_history_messages: Maximum number of messages to consider for context
        """
        self.max_history_messages = max_history_messages
    
    # =========================================================================
    # ENTITY EXTRACTION
    # =========================================================================
    
    def _extract_articles(self, text: str) -> List[int]:
        """
        Extract article numbers from text.
        
        Args:
            text: Input text to search
            
        Returns:
            List of article numbers found (deduplicated, sorted)
        """
        if not text:
            return []
        
        # Convert Arabic numerals first
        text = text.translate(self.ARABIC_TO_WESTERN)
        
        articles = set()
        
        for pattern in self.ARTICLE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Handle tuple matches from groups
                    num_str = match[0] if isinstance(match, tuple) else match
                    # Convert Arabic-Indic if present
                    num_str = str(num_str).translate(self.ARABIC_TO_WESTERN)
                    num = int(num_str)
                    if 1 <= num <= 9999:  # Reasonable article range
                        articles.add(num)
                except (ValueError, IndexError):
                    continue
        
        return sorted(list(articles))
    
    def _extract_laws(self, text: str) -> List[str]:
        """
        Extract law/system names from text.
        
        Args:
            text: Input text to search
            
        Returns:
            List of law names found (deduplicated)
        """
        if not text:
            return []
        
        laws = set()
        
        for pattern in self.LAW_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                law_name = match.strip() if isinstance(match, str) else match[0].strip()
                if len(law_name) >= 5:  # Minimum reasonable length
                    laws.add(law_name)
        
        return list(laws)
    
    def _extract_topics(self, text: str) -> List[str]:
        """
        Extract legal topics from text.
        
        Args:
            text: Input text to search
            
        Returns:
            List of topics found
        """
        if not text:
            return []
        
        topics = []
        text_lower = text.lower()
        
        for topic in self.LEGAL_TOPICS:
            if topic.lower() in text_lower or topic in text:
                topics.append(topic)
        
        return topics
    
    def _extract_all_entities(self, text: str) -> Dict[str, List]:
        """
        Extract all entity types from text.
        
        Args:
            text: Input text
            
        Returns:
            Dict with 'articles', 'laws', 'topics' keys
        """
        return {
            'articles': self._extract_articles(text),
            'laws': self._extract_laws(text),
            'topics': self._extract_topics(text)
        }
    
    def _get_message_content(self, message: Any) -> str:
        """
        Extract text content from various message formats.
        
        Handles:
        - LangChain BaseMessage objects
        - Dict with 'content' key
        - Dict with 'role' and 'content' keys
        - Plain strings
        """
        if isinstance(message, BaseMessage):
            return message.content or ""
        elif isinstance(message, dict):
            return message.get('content', '') or ""
        elif isinstance(message, str):
            return message
        else:
            return str(message)
    
    def _is_user_message(self, message: Any) -> bool:
        """Check if message is from user."""
        if isinstance(message, HumanMessage):
            return True
        elif isinstance(message, dict):
            return message.get('role', '').lower() in ('user', 'human')
        return False
    
    # =========================================================================
    # CONTEXT EXTRACTION
    # =========================================================================
    
    def extract_context_from_history(
        self, 
        chat_history: List[Any],
        current_query: Optional[str] = None
    ) -> ConversationContext:
        """
        Extract conversation context from chat history.
        
        This is the main entry point for context extraction.
        
        Args:
            chat_history: List of messages (BaseMessage or dict)
            current_query: Optional current user query to include
            
        Returns:
            ConversationContext with extracted entities
            
        Example:
            >>> history = [
            ...     HumanMessage("ما هي الهبة"),
            ...     AIMessage("الهبة هي عقد..."),
            ...     HumanMessage("المادة 368")
            ... ]
            >>> context = manager.extract_context_from_history(history)
            >>> context.active_articles
            [368]
            >>> context.active_topics
            ['الهبة']
        """
        if not chat_history:
            logger.debug("No chat history provided for context extraction")
            return ConversationContext(extracted_at=datetime.now())
        
        # Limit to recent messages
        recent_messages = chat_history[-self.max_history_messages:]
        
        # Aggregate all entities
        all_articles = []
        all_laws = []
        all_topics = []
        user_queries = []
        last_entity_type = None
        
        # Process messages with recency weighting
        # More recent messages get higher priority
        for i, message in enumerate(recent_messages):
            content = self._get_message_content(message)
            if not content:
                continue
            
            # Track user queries
            if self._is_user_message(message):
                user_queries.append(content)
            
            # Extract entities
            entities = self._extract_all_entities(content)
            
            # Add to aggregates (no weighting for now, just presence)
            if entities['articles']:
                all_articles.extend(entities['articles'])
                last_entity_type = 'article'
            
            if entities['laws']:
                all_laws.extend(entities['laws'])
                last_entity_type = 'law'
            
            if entities['topics']:
                all_topics.extend(entities['topics'])
                if last_entity_type is None:  # Topics have lower priority
                    last_entity_type = 'topic'
        
        # Include current query if provided
        if current_query:
            user_queries.append(current_query)
            current_entities = self._extract_all_entities(current_query)
            all_articles.extend(current_entities['articles'])
            all_laws.extend(current_entities['laws'])
            all_topics.extend(current_entities['topics'])
        
        # Deduplicate while preserving order (most recent first)
        active_articles = list(dict.fromkeys(reversed(all_articles)))[:10]
        active_laws = list(dict.fromkeys(reversed(all_laws)))[:5]
        active_topics = list(dict.fromkeys(reversed(all_topics)))[:5]
        
        # Reverse back to chronological order
        active_articles.reverse()
        active_laws.reverse()
        active_topics.reverse()
        
        # Calculate confidence based on entity richness
        total_entities = len(active_articles) + len(active_laws) + len(active_topics)
        confidence = min(1.0, total_entities / 5) if total_entities > 0 else 0.0
        
        context = ConversationContext(
            active_articles=active_articles,
            active_laws=active_laws,
            active_topics=active_topics,
            last_entity_type=last_entity_type,
            query_history=user_queries[-5:],  # Keep last 5 queries
            confidence=confidence,
            extracted_at=datetime.now()
        )
        
        logger.info(f"📊 Context extracted: {context.to_dict()}")
        
        return context
    
    # =========================================================================
    # CONTEXT PERSISTENCE (For Blackboard Integration)
    # =========================================================================
    
    def save_context_to_blackboard(
        self, 
        context: ConversationContext, 
        session_id: str,
        blackboard: Any
    ) -> bool:
        """
        Save context to LegalBlackboardTool for persistence.
        
        Args:
            context: The context to save
            session_id: Session ID for the blackboard
            blackboard: LegalBlackboardTool instance
            
        Returns:
            True if saved successfully
        """
        try:
            blackboard.update_segment(
                session_id,
                "conversation_context",
                context.to_dict()
            )
            logger.debug(f"Context saved to blackboard for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save context to blackboard: {e}")
            return False
    
    def load_context_from_blackboard(
        self, 
        session_id: str,
        blackboard: Any
    ) -> Optional[ConversationContext]:
        """
        Load context from LegalBlackboardTool.
        
        Args:
            session_id: Session ID
            blackboard: LegalBlackboardTool instance
            
        Returns:
            ConversationContext or None if not found
        """
        try:
            board_state = blackboard.read_latest_state(session_id)
            if not board_state:
                return None
            
            ctx_data = board_state.get("conversation_context")
            if not ctx_data:
                return None
            
            return ConversationContext(
                active_articles=ctx_data.get("active_articles", []),
                active_laws=ctx_data.get("active_laws", []),
                active_topics=ctx_data.get("active_topics", []),
                last_entity_type=ctx_data.get("last_entity_type"),
                query_history=ctx_data.get("query_history", []),
                confidence=ctx_data.get("confidence", 0.0),
                extracted_at=datetime.fromisoformat(ctx_data["extracted_at"]) if ctx_data.get("extracted_at") else None
            )
        except Exception as e:
            logger.warning(f"Failed to load context from blackboard: {e}")
            return None
