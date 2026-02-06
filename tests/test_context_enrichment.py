"""
Tests for Context Enrichment System

Run with: pytest e:\law\tests\test_context_enrichment.py -v
"""

import pytest
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

# Import the modules we're testing
from agents.core.conversation_state_manager import (
    ConversationStateManager,
    ConversationContext,
    EnrichedQuery
)
from agents.core.context_enrichment import (
    ContextEnrichmentLayer,
    AmbiguityDetector,
    enrich_query_with_context
)


class TestConversationStateManager:
    """Tests for ConversationStateManager entity extraction."""
    
    def setup_method(self):
        self.manager = ConversationStateManager(max_history_messages=5)
    
    def test_extract_article_number_arabic(self):
        """Test extracting Arabic article numbers."""
        text = "المادة 368 تتحدث عن الهبة"
        articles = self.manager._extract_articles(text)
        assert 368 in articles
    
    def test_extract_article_number_typo(self):
        """Test extracting 'الماده' with 'ه' instead of 'ة'."""
        text = "الماده 368 مهمة جداً"
        articles = self.manager._extract_articles(text)
        assert 368 in articles
    
    def test_extract_article_with_م_prefix(self):
        """Test extracting 'م. 77' format."""
        text = "راجع م. 77 من النظام"
        articles = self.manager._extract_articles(text)
        assert 77 in articles
    
    def test_extract_laws(self):
        """Test extracting law names."""
        text = "نظام المعاملات المدنية الصادر عام 2022"
        laws = self.manager._extract_laws(text)
        assert any("المعاملات المدنية" in law for law in laws)
    
    def test_extract_topics(self):
        """Test extracting legal topics."""
        text = "أريد معرفة أحكام الهبة والوصية"
        topics = self.manager._extract_topics(text)
        assert "الهبة" in topics or "الهبه" in topics
    
    def test_extract_context_from_history(self):
        """Test full context extraction from chat history."""
        history = [
            HumanMessage(content="ما هي الهبة"),
            AIMessage(content="الهبة هي عقد يتصرف بموجبه الواهب..."),
            HumanMessage(content="المادة 368")
        ]
        
        context = self.manager.extract_context_from_history(history)
        
        assert 368 in context.active_articles
        assert any("الهبة" in t or "الهبه" in t for t in context.active_topics)
    
    def test_context_empty_history(self):
        """Test handling empty history."""
        context = self.manager.extract_context_from_history([])
        assert context.is_empty()


class TestAmbiguityDetector:
    """Tests for AmbiguityDetector."""
    
    def setup_method(self):
        self.detector = AmbiguityDetector()
    
    def test_detect_location_question(self):
        """Test detecting 'في أي نظام' style questions."""
        is_ambiguous, ambiguity_type = self.detector.detect_ambiguity("في أي نظام")
        assert is_ambiguous is True
        assert ambiguity_type == 'LOCATION_QUESTION'
    
    def test_detect_pronoun_reference(self):
        """Test detecting 'ماذا عنها' style questions."""
        is_ambiguous, ambiguity_type = self.detector.detect_ambiguity("ماذا عنها")
        assert is_ambiguous is True
        assert ambiguity_type == 'PRONOUN_REFERENCE'
    
    def test_complete_query_not_ambiguous(self):
        """Test that complete queries are not flagged as ambiguous."""
        is_ambiguous, _ = self.detector.detect_ambiguity("ما هي شروط الهبة في النظام السعودي")
        assert is_ambiguous is False
    
    def test_short_query_ambiguous(self):
        """Test that very short queries are flagged."""
        is_ambiguous, ambiguity_type = self.detector.detect_ambiguity("وهذا")
        assert is_ambiguous is True


class TestContextEnrichmentLayer:
    """Tests for ContextEnrichmentLayer."""
    
    def setup_method(self):
        self.enrichment = ContextEnrichmentLayer()
    
    def test_enrich_location_question(self):
        """Test enriching 'في أي نظام' with context."""
        context = ConversationContext(
            active_articles=[368],
            active_laws=["المعاملات المدنية"],
            active_topics=["الهبة"],
            confidence=0.8,
            extracted_at=datetime.now()
        )
        
        result = self.enrichment.resolve_with_context("في أي نظام", context)
        
        # Should contain the article number
        assert "368" in result.enriched
        # Should reference the topic or law
        assert "الهبة" in result.enriched or "المعاملات المدنية" in result.enriched
        # Should have good confidence
        assert result.confidence > 0.5
    
    def test_no_enrichment_for_complete_query(self):
        """Test that complete queries are not modified."""
        context = ConversationContext(
            active_articles=[368],
            active_topics=["الهبة"]
        )
        
        query = "ما هي شروط الهبة"
        result = self.enrichment.resolve_with_context(query, context)
        
        assert result.enriched == query
    
    def test_requires_clarification_with_empty_context(self):
        """Test that ambiguous queries with no context flag clarification."""
        context = ConversationContext()  # Empty context
        
        result = self.enrichment.resolve_with_context("في أي نظام", context)
        
        assert result.requires_clarification is True
        assert result.confidence < 0.5


class TestEndToEndScenario:
    """Test the exact failing scenario from the bug report."""
    
    def test_gift_then_article_then_which_system(self):
        """
        Test the exact failing scenario:
        1. User asks about gift
        2. User mentions article 368
        3. User asks "which system"
        
        Expected: System should reference article 368 and gift topic.
        """
        # Simulate the conversation
        history = [
            {"role": "user", "content": "احتاج معلومات سريعه عن الهبه"},
            {"role": "assistant", "content": "الهبة هي عقد يتصرف بموجبه الواهب..."},
            {"role": "user", "content": "يوجد ماده ايضا تتكلم عن هذا وهي الماده 368"},
            {"role": "assistant", "content": "نعم، المادة 368 من نظام المعاملات المدنية تتحدث عن..."}
        ]
        
        # Use the convenience function
        result = enrich_query_with_context("في اي نظام", history)
        
        # Critical assertions
        assert result.enriched != "في اي نظام", "Query should be enriched"
        assert "368" in result.enriched, "Should reference article 368"
        assert result.confidence > 0.5, "Should have reasonable confidence"
        
        # Must NOT contain "emergency system" or similar hallucination triggers
        assert "الطوارئ" not in result.enriched
        
        print(f"\n✅ Enriched query: {result.enriched}")
        print(f"   Entities used: {result.entities_used}")
        print(f"   Confidence: {result.confidence:.2f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
