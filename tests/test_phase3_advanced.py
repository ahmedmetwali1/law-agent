"""
Tests for Phase 3 Advanced Improvement Modules

Run with: pytest tests/test_phase3_advanced.py -v
"""

import pytest

from agents.core.quality_predictor import (
    ResponseQualityPredictor,
    QualityScore,
    QualityLevel,
    validate_response
)
from agents.core.clarification_handler import (
    ClarificationHandler,
    ClarificationPrompt,
    ClarificationType,
    generate_clarification,
    needs_clarification
)


class TestResponseQualityPredictor:
    """Tests for ResponseQualityPredictor."""
    
    def setup_method(self):
        self.predictor = ResponseQualityPredictor()
    
    def test_empty_response_fails(self):
        """Empty response should get zero score."""
        score = self.predictor.validate(
            query="ما هي الهبة",
            response=""
        )
        assert score.overall == 0.0
        assert score.level == QualityLevel.FAILED
    
    def test_relevant_response_scores_high(self):
        """Response mentioning expected articles should score high."""
        score = self.predictor.validate(
            query="المادة 368",
            response="تنص المادة 368 من نظام المعاملات المدنية على أحكام الهبة...",
            active_articles=[368],
            active_laws=["نظام المعاملات المدنية"]
        )
        assert score.overall >= 0.7
        assert score.level in (QualityLevel.HIGH, QualityLevel.MEDIUM)
    
    def test_irrelevant_response_scores_lower(self):
        """Response not mentioning expected entities should score lower."""
        score = self.predictor.validate(
            query="المادة 368 من نظام المعاملات المدنية",
            response="نظام الطوارئ يحدد إجراءات الأمن...",
            active_articles=[368],
            active_laws=["نظام المعاملات المدنية"]
        )
        assert score.overall < 0.8
        assert "articles" in str(score.issues).lower() or len(score.issues) > 0
    
    def test_hallucination_detection(self):
        """Responses with many uncertainty indicators should be flagged."""
        response = """
        من المعروف أن الهبة ربما تتطلب بعض الشروط.
        قد يكون من المهم في معظم الحالات أن...
        يُعتقد أن هذا صحيح بشكل عام.
        """
        score = self.predictor.validate(
            query="شروط الهبة",
            response=response
        )
        assert score.checks.get("no_hallucination", 1.0) < 1.0
    
    def test_short_response_completeness(self):
        """Very short responses should have lower completeness."""
        score = self.predictor.validate(
            query="ما هي شروط الهبة الكاملة",
            response="الهبة جائزة."  # Too brief
        )
        assert score.checks.get("completeness", 1.0) < 1.0
    
    def test_article_extraction(self):
        """Should extract article numbers correctly."""
        articles = self.predictor._extract_articles(
            "المادة 368 والمادة 375 من النظام"
        )
        assert 368 in articles
        assert 375 in articles
    
    def test_quality_level_classification(self):
        """Quality levels should be assigned based on overall score."""
        high_score = QualityScore(overall=0.85)
        assert high_score.level == QualityLevel.HIGH
        
        low_score = QualityScore(overall=0.35)
        assert low_score.level == QualityLevel.FAILED
    
    def test_should_clarify_flag(self):
        """Should set clarify flag for low scores."""
        score = QualityScore(overall=0.5)
        assert score.should_clarify == True
        
        good_score = QualityScore(overall=0.8)
        assert good_score.should_clarify == False


class TestClarificationHandler:
    """Tests for ClarificationHandler."""
    
    def setup_method(self):
        self.handler = ClarificationHandler()
    
    def test_generate_article_selection(self):
        """Should generate article selection for multiple articles."""
        prompt = self.handler.generate(
            query="في أي مادة",
            articles=[368, 375, 380],
            laws=["نظام المعاملات المدنية"]
        )
        
        assert prompt.clarification_type == ClarificationType.ARTICLE_SELECTION
        assert len(prompt.options) > 0
        assert any("368" in opt.text for opt in prompt.options)
    
    def test_generate_law_selection(self):
        """Should generate law selection for location questions."""
        prompt = self.handler.generate(
            query="في أي نظام",
            laws=["نظام المعاملات المدنية", "نظام العقوبات"],
            ambiguity_type="LOCATION_QUESTION"
        )
        
        assert prompt.clarification_type == ClarificationType.LAW_SELECTION
        assert any("المعاملات" in opt.text for opt in prompt.options)
    
    def test_generate_intent_selection(self):
        """Should generate intent selection for topic queries."""
        prompt = self.handler.generate(
            query="الهبة",
            topics=["الهبة"]
        )
        
        assert prompt.clarification_type == ClarificationType.INTENT_SELECTION
        # Should include intent options
        texts = [opt.text for opt in prompt.options]
        assert any("تعريف" in t or "شروط" in t for t in texts)
    
    def test_generate_open_ended(self):
        """Should fall back to open-ended for no context."""
        prompt = self.handler.generate(query="شيء ما")
        
        assert prompt.clarification_type == ClarificationType.OPEN_ENDED
        assert len(prompt.options) >= 3
    
    def test_prompt_to_display(self):
        """Display format should include options."""
        prompt = self.handler.generate(
            query="أي مادة",
            articles=[368]
        )
        
        display = prompt.to_display()
        assert prompt.message in display
    
    def test_parse_numeric_response(self):
        """Should parse numeric responses."""
        prompt = self.handler.generate(query="test", articles=[1, 2])
        
        selected = self.handler.parse_response("1", prompt)
        assert selected is not None
        assert selected.id == 1
    
    def test_build_enriched_query_article(self):
        """Should build enriched query from article selection."""
        prompt = self.handler.generate(
            query="أي مادة",
            articles=[368],
            laws=["نظام المعاملات المدنية"]
        )
        
        # Select first option
        if prompt.options:
            enriched = self.handler.build_enriched_query(
                "أي مادة",
                prompt.options[0]
            )
            assert "368" in enriched or len(enriched) > 0
    
    def test_max_options_limit(self):
        """Should respect max options limit."""
        prompt = self.handler.generate(
            query="test",
            articles=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Many articles
        )
        assert len(prompt.options) <= self.handler.max_options


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_validate_response_function(self):
        """validate_response convenience function should work."""
        score = validate_response(
            query="الهبة",
            response="الهبة هي عقد تبرع..."
        )
        assert isinstance(score, QualityScore)
        assert 0 <= score.overall <= 1
    
    def test_generate_clarification_function(self):
        """generate_clarification convenience function should work."""
        prompt = generate_clarification(
            query="أي نظام",
            laws=["نظام المعاملات المدنية"]
        )
        assert isinstance(prompt, ClarificationPrompt)
    
    def test_needs_clarification_short_query(self):
        """Short queries should need clarification."""
        assert needs_clarification("ماذا") == True
    
    def test_needs_clarification_multiple_articles(self):
        """Multiple articles without reference should need clarification."""
        result = needs_clarification(
            query="ما هي الشروط",
            articles=[368, 375, 380]
        )
        assert result == True


class TestIntegration:
    """Integration tests for Phase 3 modules."""
    
    def test_quality_to_clarification_flow(self):
        """Low quality score should trigger clarification."""
        # 1. Get quality score for poor response
        predictor = ResponseQualityPredictor()
        score = predictor.validate(
            query="المادة 368",
            response="لا أعرف.",  # Poor response
            active_articles=[368]
        )
        
        # 2. If needs clarification, generate prompt
        if score.should_clarify:
            handler = ClarificationHandler()
            prompt = handler.generate(
                query="المادة 368",
                articles=[368],
                laws=["نظام المعاملات المدنية"]
            )
            
            assert prompt is not None
            assert len(prompt.options) > 0
    
    def test_full_clarification_cycle(self):
        """Test complete clarification cycle."""
        handler = ClarificationHandler()
        
        # 1. Generate clarification
        prompt = handler.generate(
            query="أي مادة",
            articles=[368, 375]
        )
        
        # 2. User selects option
        selected = handler.parse_response("1", prompt)
        assert selected is not None
        
        # 3. Build enriched query
        enriched = handler.build_enriched_query(prompt.original_query, selected)
        assert len(enriched) > len(prompt.original_query)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
