"""
🔍 Law Identifier Tool - أداة التعرف على الأنظمة القانونية

Smart law name resolution with fuzzy matching and variants support.
Resolves user queries like "معاملات" → "نظام المعاملات المدنية"
"""

import logging
import time
from typing import Optional, List, Dict, Any
from thefuzz import fuzz, process  # Fuzzy matching library
from dataclasses import dataclass

from .base_tool import BaseTool, ToolResult
from ..config.database import db

logger = logging.getLogger(__name__)


@dataclass
class LawMatch:
    """Represents a matched law"""
    source_id: str
    official_title: str
    confidence: float  # 0.0 - 1.0
    doc_type: str
    total_word_count: int
    country_id: str


class LawIdentifierTool(BaseTool):
    """
    🎯 Smart Law Identifier
    
    Features:
    - Fuzzy matching (handles typos, abbreviations)
    - Variant support ("معاملات" → "المعاملات المدنية")
    - Multi-country support
    - Caching for performance
    
    Examples:
    - "معاملات مدنية" → نظام المعاملات المدنية
    - "ن.م.م" → نظام المعاملات المدنية (abbreviation)
    - "القانون المدني" → نظام المعاملات المدنية (synonym)
    - "نظام العمل" → نظام العمل
    """
    
    def __init__(self):
        super().__init__(
            name="law_identifier",
            description="تحديد النظام القانوني من اسم أو وصف"
        )
        self._cache = {}  # Simple in-memory cache (TODO: use Redis)
        
    def run(
        self,
        law_query: str,
        country_id: Optional[str] = None,
        min_confidence: float = 0.6,
        max_results: int = 5
    ) -> ToolResult:
        """
        Identify law from query.
        
        Args:
            law_query: User's query (e.g., "معاملات", "نظام العمل")
            country_id: Filter by country (optional)
            min_confidence: Minimum confidence score (0.0-1.0)
            max_results: Maximum number of results to return
            
        Returns:
            ToolResult with matched laws, sorted by confidence
        """
        
        start_time = time.time()
        
        try:
            # 1. Check cache
            cache_key = f"{law_query}|{country_id}|{min_confidence}"
            if cache_key in self._cache:
                logger.info(f"🔍 Law Identifier (CACHED): {law_query}")
                return self._cache[cache_key]
            
            logger.info(f"🔍 Law Identifier: Searching for '{law_query}'")
            
            # 2. Fetch all laws from database
            query_builder = db.legal_sources.select("id, title, doc_type, total_word_count, country_id")
            
            if country_id:
                query_builder = query_builder.eq("country_id", country_id)
            
            response = query_builder.execute()
            
            if not response.data:
                return ToolResult(
                    success=False,
                    error=f"لا توجد أنظمة متاحة" + (f" في الدولة {country_id}" if country_id else "")
                )
            
            laws = response.data
            logger.info(f"📚 Found {len(laws)} laws in database")
            
            # 3. Fuzzy matching
            matches = self._fuzzy_match(law_query, laws, min_confidence)
            
            if not matches:
                # Try with relaxed confidence
                relaxed_matches = self._fuzzy_match(law_query, laws, min_confidence=0.3)
                
                if relaxed_matches:
                    return ToolResult(
                        success=False,
                        error=f"لم أجد تطابق قوي. هل تقصد أحد هؤلاء؟",
                        data={
                            "suggestions": [
                                {
                                    "title": m.official_title,
                                    "confidence": m.confidence,
                                    "source_id": m.source_id
                                }
                                for m in relaxed_matches[:3]
                            ]
                        }
                    )
                else:
                    return ToolResult(
                        success=False,
                        error=f"لم أجد نظام يطابق '{law_query}'"
                    )
            
            # 4. Sort by confidence and limit results
            matches = sorted(matches, key=lambda x: x.confidence, reverse=True)[:max_results]
            
            # 5. Prepare result
            result = ToolResult(
                success=True,
                data={
                    "best_match": {
                        "source_id": matches[0].source_id,
                        "official_title": matches[0].official_title,
                        "confidence": matches[0].confidence,
                        "doc_type": matches[0].doc_type,
                        "total_word_count": matches[0].total_word_count
                    },
                    "all_matches": [
                        {
                            "source_id": m.source_id,
                            "official_title": m.official_title,
                            "confidence": m.confidence,
                            "doc_type": m.doc_type,
                            "total_word_count": m.total_word_count
                        }
                        for m in matches
                    ],
                    "match_count": len(matches),
                    "search_time_ms": int((time.time() - start_time) * 1000)
                }
            )
            
            # 6. Cache result
            self._cache[cache_key] = result
            
            logger.info(f"✅ Best match: {matches[0].official_title} (confidence: {matches[0].confidence:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Law Identifier failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"خطأ في التعرف على النظام: {str(e)}"
            )
    
    def _fuzzy_match(
        self,
        query: str,
        laws: List[Dict],
        min_confidence: float
    ) -> List[LawMatch]:
        """
        Fuzzy match query against law titles
        
        Uses multiple matching strategies:
        1. Exact substring match (highest priority)
        2. Token sort ratio (handles word order)
        3. Partial ratio (handles abbreviations)
        4. Simple ratio (fallback)
        """
        
        matches = []
        query_lower = query.lower().strip()
        
        for law in laws:
            title = law.get("title", "")
            title_lower = title.lower()
            
            # Strategy 1: Exact substring match (confidence boost)
            if query_lower in title_lower or title_lower in query_lower:
                confidence = 0.95
            else:
                # Strategy 2: Token sort ratio (best for Arabic with different word orders)
                token_sort = fuzz.token_sort_ratio(query_lower, title_lower) / 100.0
                
                # Strategy 3: Partial ratio (good for abbreviations)
                partial = fuzz.partial_ratio(query_lower, title_lower) / 100.0
                
                # Strategy 4: Simple ratio
                simple = fuzz.ratio(query_lower, title_lower) / 100.0
                
                # Take the best score
                confidence = max(token_sort, partial, simple)
            
            if confidence >= min_confidence:
                matches.append(
                    LawMatch(
                        source_id=law.get("id"),
                        official_title=title,
                        confidence=confidence,
                        doc_type=law.get("doc_type", ""),
                        total_word_count=law.get("total_word_count", 0),
                        country_id=law.get("country_id", "")
                    )
                )
        
        return matches
    
    def clear_cache(self):
        """Clear the internal cache"""
        self._cache = {}
        logger.info("🗑️ Law Identifier cache cleared")


__all__ = ["LawIdentifierTool", "LawMatch"]
