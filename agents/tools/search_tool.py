"""
Search Knowledge Tool
أداة البحث في قاعدة المعرفة القانونية
"""

import time
import logging
from typing import List, Optional

from .base_tool import BaseTool, ToolResult
from ..knowledge.hybrid_search import search, SearchResult

logger = logging.getLogger(__name__)


class SearchKnowledgeTool(BaseTool):
    """
    Tool to search the legal knowledge base.
    
    Uses hybrid search (keyword + vector) to find relevant
    laws, articles, and legal principles.
    """
    
    def __init__(self):
        super().__init__(
            name="search_knowledge",
            description="البحث في قاعدة المعرفة القانونية عن قوانين ومواد ومبادئ"
        )
        
        # Keywords that indicate a search intent
        self.search_keywords = [
            "ابحث", "بحث", "ما هو", "ما هي", "عقوبة", "نص", "مادة",
            "قانون", "حكم", "ماذا", "كيف", "متى", "أين"
        ]
    
    def run(
        self,
        query: str,
        limit: int = 5,
        method: str = "hybrid",
        legal_domain: str = None
    ) -> ToolResult:
        """
        Execute search and return results.
        
        Args:
            query: Search query text.
            limit: Maximum results.
            method: 'keyword', 'vector', or 'hybrid'.
            legal_domain: Filter by legal domain (e.g. "أحوال شخصية", "جنائي").
            
        Returns:
            ToolResult with search results.
        """
        self._track_usage()
        start_time = time.time()
        
        try:
            domain_info = f" [domain={legal_domain}]" if legal_domain else ""
            logger.info(f"🔍 SearchTool: Searching for '{query[:50]}...'{domain_info}")
            
            # Build filters
            filters = {}
            if legal_domain:
                filters["legal_domain"] = legal_domain
            
            results: List[SearchResult] = search(
                query, 
                limit=limit, 
                method=method,
                filters=filters if filters else None
            )
            
            # Format results for easier consumption
            formatted = []
            for res in results:
                formatted.append({
                    "content": res.content[:500] + "..." if len(res.content) > 500 else res.content,
                    "score": round(res.score, 3),
                    "summary": res.ai_summary,
                    "hierarchy": res.hierarchy_path,
                    "keywords": res.keywords,
                    "source_id": res.source_id
                })
            
            elapsed = (time.time() - start_time) * 1000
            
            logger.info(f"✅ SearchTool: Found {len(formatted)} results in {elapsed:.0f}ms")
            
            return ToolResult(
                success=True,
                data=formatted,
                metadata={"query": query, "method": method, "result_count": len(formatted)},
                execution_time_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"❌ SearchTool failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def can_handle(self, query: str) -> float:
        """
        Check if this tool can handle the query.
        
        Returns higher confidence for queries that look like searches.
        """
        query_lower = query.lower()
        
        # Count matching keywords
        matches = sum(1 for kw in self.search_keywords if kw in query_lower)
        
        if matches >= 2:
            return 0.9
        elif matches == 1:
            return 0.6
        elif "?" in query or len(query.split()) <= 10:
            return 0.4  # Short questions might be searches
        
        return 0.2  # Default low confidence


__all__ = ["SearchKnowledgeTool"]
