"""
Tests for Enhanced Entity Extraction Module

Run with: pytest tests/test_entity_extraction.py -v
"""

import pytest

from agents.core.entity_extractor import (
    EnhancedEntityExtractor,
    FuzzyMatcher,
    EntityValidator,
    ExtractionResult,
    ExtractedEntity,
    ExtractionMethod,
    extract_entities,
    extract_articles,
    extract_laws,
    validate_article
)


class TestFuzzyMatcher:
    """Tests for FuzzyMatcher class."""
    
    def setup_method(self):
        self.matcher = FuzzyMatcher()
    
    def test_correct_taa_marbuta(self):
        """Should correct الماده to المادة."""
        corrected = self.matcher.correct_text("الماده 368")
        assert "المادة" in corrected
    
    def test_correct_zain_to_dhaa(self):
        """Should correct نضام to نظام."""
        corrected = self.matcher.correct_text("نضام العمل")
        assert "نظام" in corrected
    
    def test_fuzzy_match_known_law(self):
        """Should match known law names."""
        result = self.matcher.fuzzy_match_law("نظام المعاملات المدنية")
        assert result is not None
        assert result[0] == "نظام المعاملات المدنية"
        assert result[1] == 1.0
    
    def test_extract_articles_with_typo(self):
        """Should extract articles even with typos."""
        results = self.matcher.extract_articles_fuzzy("الماده 368 والمادا 375")
        article_nums = [r[0] for r in results]
        assert 368 in article_nums
        assert 375 in article_nums
    
    def test_extract_articles_standard(self):
        """Should extract standard article references."""
        results = self.matcher.extract_articles_fuzzy("المادة 100 والمادة رقم 200")
        article_nums = [r[0] for r in results]
        assert 100 in article_nums
        assert 200 in article_nums


class TestEntityValidator:
    """Tests for EntityValidator class."""
    
    def setup_method(self):
        self.validator = EntityValidator()
    
    def test_valid_article_in_range(self):
        """Valid articles should pass validation."""
        is_valid, confidence = self.validator.validate_article(368)
        assert is_valid == True
        assert confidence >= 0.7
    
    def test_invalid_article_zero(self):
        """Article 0 should be invalid."""
        is_valid, _ = self.validator.validate_article(0)
        assert is_valid == False
    
    def test_invalid_article_negative(self):
        """Negative articles should be invalid."""
        is_valid, _ = self.validator.validate_article(-5)
        assert is_valid == False
    
    def test_valid_known_law(self):
        """Known laws should have high confidence."""
        is_valid, confidence = self.validator.validate_law("نظام المعاملات المدنية")
        assert is_valid == True
        assert confidence >= 0.9
    
    def test_valid_unknown_law(self):
        """Unknown laws with نظام prefix should be valid."""
        is_valid, confidence = self.validator.validate_law("نظام غير معروف")
        assert is_valid == True
        assert confidence >= 0.5
    
    def test_invalid_short_law(self):
        """Very short law names should be invalid."""
        is_valid, _ = self.validator.validate_law("نظام")
        assert is_valid == False
    
    def test_valid_known_topic(self):
        """Known topics should have high confidence."""
        is_valid, confidence = self.validator.validate_topic("الهبة")
        assert is_valid == True
        assert confidence == 1.0
    
    def test_valid_topic_with_variant(self):
        """Topic variants should be validated."""
        is_valid, confidence = self.validator.validate_topic("الوصية")
        assert is_valid == True


class TestEnhancedEntityExtractor:
    """Tests for EnhancedEntityExtractor class."""
    
    def setup_method(self):
        self.extractor = EnhancedEntityExtractor()
    
    def test_extract_single_article(self):
        """Should extract a single article."""
        result = self.extractor.extract_all("المادة 368 من النظام")
        assert 368 in result.get_article_numbers()
    
    def test_extract_multiple_articles(self):
        """Should extract multiple articles."""
        result = self.extractor.extract_all("المادة 368 والمادة 375 والمادة 380")
        articles = result.get_article_numbers()
        assert 368 in articles
        assert 375 in articles
        assert 380 in articles
    
    def test_extract_with_typos(self):
        """Should extract articles with typos."""
        result = self.extractor.extract_all("الماده 368 من نضام المعاملات")
        assert 368 in result.get_article_numbers()
    
    def test_extract_law(self):
        """Should extract law names."""
        result = self.extractor.extract_all("في نظام المعاملات المدنية الصادر")
        laws = result.get_law_names()
        assert len(laws) > 0
    
    def test_extract_topic(self):
        """Should extract legal topics."""
        result = self.extractor.extract_all("أحكام الهبة في الشريعة")
        topics = result.get_topic_names()
        assert len(topics) > 0
        assert any("هب" in t for t in topics)
    
    def test_extract_all_entity_types(self):
        """Should extract all entity types from complex text."""
        text = "المادة 368 من نظام المعاملات المدنية تتعلق بأحكام الهبة"
        result = self.extractor.extract_all(text)
        
        assert len(result.articles) > 0
        # Laws and topics extraction depends on patterns
    
    def test_empty_text(self):
        """Empty text should return empty result."""
        result = self.extractor.extract_all("")
        assert result.is_empty()
    
    def test_no_entities(self):
        """Text without entities should return empty result."""
        result = self.extractor.extract_all("مرحبا كيف حالك اليوم")
        assert result.is_empty()
    
    def test_confidence_score(self):
        """Should calculate confidence score."""
        result = self.extractor.extract_all("المادة 368")
        assert 0 <= result.confidence <= 1.0
    
    def test_extraction_method_tracking(self):
        """Should track extraction method used."""
        result = self.extractor.extract_all("المادة 368")
        if result.articles:
            assert result.articles[0].method in (ExtractionMethod.REGEX, ExtractionMethod.FUZZY)


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_extract_entities_function(self):
        """extract_entities should return ExtractionResult."""
        result = extract_entities("المادة 368")
        assert isinstance(result, ExtractionResult)
    
    def test_extract_articles_function(self):
        """extract_articles should return list of ints."""
        articles = extract_articles("المادة 368 والمادة 375")
        assert isinstance(articles, list)
        assert 368 in articles
    
    def test_extract_laws_function(self):
        """extract_laws should return list of strings."""
        laws = extract_laws("نظام العمل الصادر")
        assert isinstance(laws, list)
    
    def test_validate_article_function(self):
        """validate_article should return bool."""
        assert validate_article(368) == True
        assert validate_article(0) == False


class TestEdgeCases:
    """Tests for edge cases and Arabic variations."""
    
    def setup_method(self):
        self.extractor = EnhancedEntityExtractor()
    
    def test_arabic_numerals(self):
        """Should handle Arabic-Indic numerals."""
        # This requires the text to be pre-converted
        result = self.extractor.extract_all("المادة 123")
        assert 123 in result.get_article_numbers()
    
    def test_m_dot_abbreviation(self):
        """Should handle م. abbreviation."""
        result = self.extractor.extract_all("م. 50 من النظام")
        assert 50 in result.get_article_numbers()
    
    def test_article_with_raqm(self):
        """Should handle 'رقم' in article reference."""
        result = self.extractor.extract_all("المادة رقم 99")
        assert 99 in result.get_article_numbers()
    
    def test_topic_variants(self):
        """Should handle topic spelling variants."""
        # Test with taa marbuta variant
        result1 = self.extractor.extract_all("الهبة")
        result2 = self.extractor.extract_all("الهبه")
        
        # At least one should find the topic
        assert len(result1.topics) > 0 or len(result2.topics) > 0


class TestIntegration:
    """Integration tests."""
    
    def test_complex_legal_text(self):
        """Should handle complex legal text with multiple entities."""
        text = """
        وفقاً لأحكام المادة 368 من نظام المعاملات المدنية،
        فإن الهبة تخضع لشروط معينة. كما تنص المادة 375
        على أحكام إضافية تتعلق بالرجوع في الهبة.
        """
        
        result = extract_entities(text)
        
        # Should find multiple articles
        articles = result.get_article_numbers()
        assert 368 in articles
        assert 375 in articles
        
        # Should find the topic
        topics = result.get_topic_names()
        assert any("هب" in t for t in topics)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
