"""
💬 Interactive Clarification Handler v1.0

Generates smart clarification prompts when queries are ambiguous.
Creates numbered options for users to select from.

Architecture:
- Context-aware option generation
- Multi-choice clarification prompts
- Fallback to open-ended questions

Author: Legal AI System
Created: 2026-02-06
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class ClarificationType(Enum):
    """Types of clarification requests."""
    ARTICLE_SELECTION = "article_selection"     # Which article?
    LAW_SELECTION = "law_selection"             # Which law/system?
    TOPIC_SELECTION = "topic_selection"         # Which topic?
    INTENT_SELECTION = "intent_selection"       # What do you want to know?
    OPEN_ENDED = "open_ended"                   # General clarification


@dataclass
class ClarificationOption:
    """Single clarification option."""
    id: int
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_display(self) -> str:
        """Format for display."""
        emoji_map = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣"}
        emoji = emoji_map.get(self.id, f"{self.id}.")
        return f"{emoji} {self.text}"


@dataclass
class ClarificationPrompt:
    """Complete clarification prompt with options."""
    message: str
    options: List[ClarificationOption]
    clarification_type: ClarificationType
    original_query: str
    context_summary: Optional[str] = None
    
    def to_display(self) -> str:
        """Format complete prompt for display."""
        lines = [self.message, ""]
        for option in self.options:
            lines.append(option.to_display())
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "message": self.message,
            "options": [{"id": o.id, "text": o.text} for o in self.options],
            "type": self.clarification_type.value,
            "original_query": self.original_query
        }


# =============================================================================
# CLARIFICATION HANDLER
# =============================================================================

class ClarificationHandler:
    """
    Generates smart clarification prompts for ambiguous queries.
    
    Features:
    - Context-aware option generation
    - Multi-choice clarifications
    - Arabic language support
    - Fallback to open-ended questions
    
    Usage:
        handler = ClarificationHandler()
        prompt = handler.generate(
            query="في أي نظام",
            articles=[368, 375],
            laws=["نظام المعاملات المدنية"],
            topics=["الهبة"]
        )
        
        # Display to user
        print(prompt.to_display())
    """
    
    # Maximum options to show
    MAX_OPTIONS = 4
    
    # Templates for different clarification types
    MESSAGES = {
        ClarificationType.ARTICLE_SELECTION: "تم ذكر عدة مواد في المحادثة. أي مادة تقصد؟",
        ClarificationType.LAW_SELECTION: "أي نظام تقصد؟",
        ClarificationType.TOPIC_SELECTION: "ما الموضوع الذي تريد الاستفسار عنه؟",
        ClarificationType.INTENT_SELECTION: "ماذا تريد أن تعرف؟",
        ClarificationType.OPEN_ENDED: "يرجى توضيح سؤالك أكثر:",
    }
    
    # Intent options for ambiguous queries
    INTENT_OPTIONS = [
        ("definition", "تعريف ومفهوم"),
        ("conditions", "الشروط والأركان"),
        ("procedure", "الإجراءات القانونية"),
        ("effects", "الآثار والأحكام"),
    ]
    
    def __init__(self, max_options: int = 4):
        """
        Initialize the handler.
        
        Args:
            max_options: Maximum number of options to display
        """
        self.max_options = max_options
    
    # =========================================================================
    # MAIN GENERATION
    # =========================================================================
    
    def generate(
        self,
        query: str,
        articles: Optional[List[int]] = None,
        laws: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        ambiguity_type: Optional[str] = None
    ) -> ClarificationPrompt:
        """
        Generate clarification prompt based on context.
        
        Args:
            query: Original ambiguous query
            articles: Active articles from context
            laws: Active laws from context
            topics: Active topics from context
            ambiguity_type: Type of ambiguity detected
            
        Returns:
            ClarificationPrompt with options
        """
        articles = articles or []
        laws = laws or []
        topics = topics or []
        
        # Determine clarification type based on context
        if ambiguity_type == "LOCATION_QUESTION" and laws:
            return self._generate_law_selection(query, laws)
        
        if len(articles) > 1:
            return self._generate_article_selection(query, articles, laws)
        
        if len(laws) > 1:
            return self._generate_law_selection(query, laws)
        
        if topics:
            return self._generate_intent_selection(query, topics)
        
        # Fallback to open-ended
        return self._generate_open_ended(query)
    
    # =========================================================================
    # SPECIFIC GENERATORS
    # =========================================================================
    
    def _generate_article_selection(
        self,
        query: str,
        articles: List[int],
        laws: List[str]
    ) -> ClarificationPrompt:
        """Generate article selection prompt."""
        options = []
        law_name = laws[0] if laws else "النظام"
        
        for i, article in enumerate(articles[:self.max_options - 1], 1):
            options.append(ClarificationOption(
                id=i,
                text=f"المادة {article} من {law_name}",
                metadata={"article": article, "law": law_name}
            ))
        
        # Add "other" option
        options.append(ClarificationOption(
            id=len(options) + 1,
            text="مادة أخرى (حددها)",
            metadata={"type": "other"}
        ))
        
        return ClarificationPrompt(
            message=self.MESSAGES[ClarificationType.ARTICLE_SELECTION],
            options=options,
            clarification_type=ClarificationType.ARTICLE_SELECTION,
            original_query=query
        )
    
    def _generate_law_selection(
        self,
        query: str,
        laws: List[str]
    ) -> ClarificationPrompt:
        """Generate law selection prompt."""
        options = []
        
        for i, law in enumerate(laws[:self.max_options - 1], 1):
            options.append(ClarificationOption(
                id=i,
                text=law,
                metadata={"law": law}
            ))
        
        # Add "other" option
        options.append(ClarificationOption(
            id=len(options) + 1,
            text="نظام آخر (حدده)",
            metadata={"type": "other"}
        ))
        
        return ClarificationPrompt(
            message=self.MESSAGES[ClarificationType.LAW_SELECTION],
            options=options,
            clarification_type=ClarificationType.LAW_SELECTION,
            original_query=query
        )
    
    def _generate_intent_selection(
        self,
        query: str,
        topics: List[str]
    ) -> ClarificationPrompt:
        """Generate intent selection prompt."""
        topic = topics[0] if topics else "الموضوع"
        options = []
        
        for i, (intent_key, intent_text) in enumerate(self.INTENT_OPTIONS[:self.max_options], 1):
            options.append(ClarificationOption(
                id=i,
                text=f"{intent_text} {topic}",
                metadata={"intent": intent_key, "topic": topic}
            ))
        
        return ClarificationPrompt(
            message=f"ماذا تريد أن تعرف عن {topic}؟",
            options=options,
            clarification_type=ClarificationType.INTENT_SELECTION,
            original_query=query
        )
    
    def _generate_open_ended(self, query: str) -> ClarificationPrompt:
        """Generate open-ended clarification."""
        options = [
            ClarificationOption(id=1, text="أريد تعريف مفهوم قانوني"),
            ClarificationOption(id=2, text="أريد معرفة شروط أو إجراءات"),
            ClarificationOption(id=3, text="أريد نص مادة قانونية"),
            ClarificationOption(id=4, text="شيء آخر (حدده)")
        ]
        
        return ClarificationPrompt(
            message=self.MESSAGES[ClarificationType.OPEN_ENDED],
            options=options,
            clarification_type=ClarificationType.OPEN_ENDED,
            original_query=query
        )
    
    # =========================================================================
    # RESPONSE PARSING
    # =========================================================================
    
    def parse_response(
        self,
        user_input: str,
        prompt: ClarificationPrompt
    ) -> Optional[ClarificationOption]:
        """
        Parse user response to clarification prompt.
        
        Args:
            user_input: User's response (number or text)
            prompt: The original prompt
            
        Returns:
            Selected option or None if unparseable
        """
        # Try to parse as number
        user_input = user_input.strip()
        
        try:
            option_id = int(user_input)
            for option in prompt.options:
                if option.id == option_id:
                    return option
        except ValueError:
            pass
        
        # Try to match text
        user_lower = user_input.lower()
        for option in prompt.options:
            if option.text.lower() in user_lower or user_lower in option.text.lower():
                return option
        
        return None
    
    def build_enriched_query(
        self,
        original_query: str,
        selected_option: ClarificationOption
    ) -> str:
        """
        Build enriched query from selected option.
        
        Args:
            original_query: Original ambiguous query
            selected_option: User's selection
            
        Returns:
            Enriched query string
        """
        metadata = selected_option.metadata
        
        if "article" in metadata:
            law = metadata.get("law", "")
            return f"المادة {metadata['article']} من {law}"
        
        if "law" in metadata:
            return f"{original_query} في {metadata['law']}"
        
        if "intent" in metadata and "topic" in metadata:
            intent_map = {
                "definition": "تعريف",
                "conditions": "شروط",
                "procedure": "إجراءات",
                "effects": "آثار"
            }
            intent_text = intent_map.get(metadata["intent"], "")
            return f"{intent_text} {metadata['topic']}"
        
        # Fallback: use option text
        return selected_option.text


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global instance
_handler = ClarificationHandler()

def generate_clarification(
    query: str,
    articles: Optional[List[int]] = None,
    laws: Optional[List[str]] = None,
    topics: Optional[List[str]] = None
) -> ClarificationPrompt:
    """
    Convenience function to generate clarification prompt.
    """
    return _handler.generate(query, articles, laws, topics)


def needs_clarification(
    query: str,
    articles: Optional[List[int]] = None,
    context_empty: bool = False
) -> bool:
    """
    Quick check if clarification is likely needed.
    
    Returns True if:
    - Query is very short
    - Multiple articles without specific reference
    - Context is empty and query is ambiguous
    """
    query = query.strip()
    
    # Very short queries likely need clarification
    if len(query) < 15:
        return True
    
    # Multiple articles but no specific reference
    if articles and len(articles) > 1 and not any(
        str(a) in query for a in articles
    ):
        return True
    
    return False
