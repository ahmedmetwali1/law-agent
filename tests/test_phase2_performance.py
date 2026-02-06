"""
Tests for Phase 2 Performance Optimization Modules

Run with: pytest e:\law\tests\test_phase2_performance.py -v
"""

import pytest
from datetime import datetime, timedelta

# Import the modules we're testing
from agents.core.timeout_strategy import (
    AdaptiveTimeoutStrategy,
    QueryComplexity,
    TimeoutConfig,
    get_timeout
)
from agents.core.search_cache import (
    SearchCache,
    get_search_cache,
    CacheEntry
)
from agents.core.query_rewriter import (
    QueryRewriter,
    expand_query,
    RewriteResult
)


class TestAdaptiveTimeoutStrategy:
    """Tests for AdaptiveTimeoutStrategy."""
    
    def setup_method(self):
        self.strategy = AdaptiveTimeoutStrategy()
    
    def test_simple_query_complexity(self):
        """Short queries should be classified as simple."""
        complexity = self.strategy.estimate_complexity(
            query="ما هي الهبة",
            intent="LEGAL_SIMPLE"
        )
        assert complexity == QueryComplexity.SIMPLE
    
    def test_complex_query_complexity(self):
        """Queries with complex keywords should be classified as complex."""
        complexity = self.strategy.estimate_complexity(
            query="اشرح لي بالتفصيل الفرق بين الهبة والوصية مع تحليل كامل",
            entity_count=3
        )
        assert complexity in (QueryComplexity.COMPLEX, QueryComplexity.EXPERT)
    
    def test_timeout_config_simple(self):
        """Simple queries should have shorter timeouts."""
        config = self.strategy.get_timeout_config(QueryComplexity.SIMPLE)
        assert config.search <= 15  # Short search timeout
        assert config.council == 0  # No council needed
    
    def test_timeout_config_complex(self):
        """Complex queries should have longer timeouts."""
        config = self.strategy.get_timeout_config(QueryComplexity.COMPLEX)
        assert config.search >= 20  # Longer search timeout
        assert config.council > 0   # Council enabled
    
    def test_should_skip_council(self):
        """Simple queries should skip council."""
        assert self.strategy.should_skip_council(QueryComplexity.SIMPLE) == True
        assert self.strategy.should_skip_council(QueryComplexity.COMPLEX) == False
    
    def test_get_search_limit(self):
        """Search limits should vary by complexity."""
        simple_limit = self.strategy.get_search_limit(QueryComplexity.SIMPLE)
        complex_limit = self.strategy.get_search_limit(QueryComplexity.COMPLEX)
        assert simple_limit < complex_limit


class TestSearchCache:
    """Tests for SearchCache."""
    
    def setup_method(self):
        self.cache = SearchCache(max_size=10, ttl_hours=1)
    
    def test_cache_miss(self):
        """Non-existent key should return None."""
        result = self.cache.get("nonexistent_hash")
        assert result is None
    
    def test_cache_hit(self):
        """Stored items should be retrievable."""
        results = [{"id": 1, "text": "test"}]
        query_hash = "test_hash_123"
        
        self.cache.set(query_hash, results)
        cached = self.cache.get(query_hash)
        
        assert cached is not None
        assert cached == results
    
    def test_hash_query_deterministic(self):
        """Same inputs should produce same hash."""
        hash1 = SearchCache.hash_query("الهبة", articles=[368])
        hash2 = SearchCache.hash_query("الهبة", articles=[368])
        assert hash1 == hash2
    
    def test_hash_query_different_for_different_inputs(self):
        """Different inputs should produce different hashes."""
        hash1 = SearchCache.hash_query("الهبة", articles=[368])
        hash2 = SearchCache.hash_query("الوصية", articles=[400])
        assert hash1 != hash2
    
    def test_lru_eviction(self):
        """Oldest entries should be evicted when capacity is reached."""
        # Fill cache beyond capacity
        for i in range(15):
            self.cache.set(f"hash_{i}", [{"id": i}])
        
        # Cache should be at max size
        assert len(self.cache._cache) <= self.cache.max_size
    
    def test_normalize_query(self):
        """Query normalization should handle whitespace."""
        normalized = SearchCache.normalize_query("  ما   هي   الهبة  ")
        assert "  " not in normalized  # No double spaces
        assert normalized.strip() == normalized  # No leading/trailing spaces
    
    def test_cache_stats(self):
        """Statistics should be tracked correctly."""
        # Generate a miss
        self.cache.get("miss_hash")
        
        # Generate a hit
        self.cache.set("hit_hash", [{"id": 1}])
        self.cache.get("hit_hash")
        
        stats = self.cache.get_stats()
        assert stats.total_misses >= 1
        assert stats.total_hits >= 1


class TestQueryRewriter:
    """Tests for QueryRewriter."""
    
    def setup_method(self):
        self.rewriter = QueryRewriter(max_variants=5)
    
    def test_detect_definition_intent(self):
        """Should detect definition intent."""
        intent = self.rewriter.detect_intent("ما هي الهبة")
        assert intent == "definition"
    
    def test_detect_conditions_intent(self):
        """Should detect conditions intent."""
        intent = self.rewriter.detect_intent("شروط الهبة")
        assert intent == "conditions"
    
    def test_detect_article_lookup_intent(self):
        """Should detect article lookup intent."""
        intent = self.rewriter.detect_intent("المادة 368")
        assert intent == "article_lookup"
    
    def test_expand_includes_original(self):
        """Expansion should always include original query."""
        result = self.rewriter.expand("ما هي الهبة")
        assert "ما هي الهبة" in result.variants
    
    def test_expand_generates_variants(self):
        """Expansion should generate multiple variants."""
        result = self.rewriter.expand(
            "ما هي الهبة",
            active_topics=["الهبة"]
        )
        assert len(result.variants) > 1
    
    def test_expand_with_context(self):
        """Expansion should use context."""
        result = self.rewriter.expand(
            "شروط",
            active_articles=[368],
            active_laws=["نظام المعاملات المدنية"],
            active_topics=["الهبة"]
        )
        
        # Should have article-topic combination
        has_article_variant = any("368" in v for v in result.variants)
        assert has_article_variant or len(result.variants) > 1
    
    def test_topic_extraction(self):
        """Should extract known legal topics."""
        topics = self.rewriter.extract_topics("أريد معرفة أحكام الهبة والوصية")
        assert "الهبة" in topics or len(topics) > 0
    
    def test_max_variants_respected(self):
        """Should not exceed max variants."""
        result = self.rewriter.expand(
            "شروط الهبة والوصية",
            active_topics=["الهبة", "الوصية"]
        )
        assert len(result.variants) <= self.rewriter.max_variants


class TestIntegration:
    """Integration tests for Phase 2 modules."""
    
    def test_full_pipeline(self):
        """Test the full search optimization pipeline."""
        # 1. Estimate complexity
        strategy = AdaptiveTimeoutStrategy()
        complexity = strategy.estimate_complexity(
            query="المادة 368 من نظام المعاملات المدنية",
            intent="LEGAL_SIMPLE",
            entity_count=1
        )
        
        # 2. Get appropriate timeout
        timeout = strategy.get_phase_timeout("search", complexity)
        assert timeout > 0
        
        # 3. Expand query
        variants = expand_query(
            "المادة 368",
            articles=[368],
            laws=["نظام المعاملات المدنية"]
        )
        assert len(variants) >= 1
        
        # 4. Check cache (should miss since nothing cached)
        cache = SearchCache(max_size=10, ttl_hours=1)
        query_hash = cache.hash_query(variants[0], articles=[368])
        assert cache.get(query_hash) is None
        
        # 5. Cache result
        mock_results = [{"id": 1, "article": 368}]
        cache.set(query_hash, mock_results)
        
        # 6. Verify cache hit
        cached = cache.get(query_hash)
        assert cached == mock_results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
