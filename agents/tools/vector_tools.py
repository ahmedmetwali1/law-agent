import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base_tool import BaseTool, ToolResult
from ..config.database import db

logger = logging.getLogger(__name__)

@dataclass
class VectorSearchResult:
    id: str
    content: str
    similarity: float
    metadata: Dict[str, Any]

class VectorSearchTool(BaseTool):
    """
    Advanced Vector Search Tool (Infrastructure Ready)
    Uses Supabase `match_documents` RPC for cosine similarity.
    """
    
    def __init__(self):
        super().__init__(
            name="vector_search",
            description="بحث دلالي باستخدام تقنية المتجهات (Embeddings)"
        )
        # Default configuration meant to be overridden by config
        # ✅ FIX 4: Lowered threshold for better recall
        self.match_threshold = 0.3  # Was 0.5, now more lenient
        self.match_count = 10

    def run(
        self,
        query_vector: List[float],
        match_threshold: Optional[float] = None,
        match_count: Optional[int] = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute vector search using pre-calculated embedding.
        """
        self._track_usage()
        start_time = time.time()
        
        threshold = match_threshold or self.match_threshold
        count = match_count or self.match_count
        
        # We fetch slightly more to allow for post-filtering
        fetch_count = count * 2 if filter else count
        
        try:
            # RPC Call to Supabase function 'match_documents_v2'
            params = {
                "query_embedding": query_vector,
                "match_threshold": threshold,
                "match_count": fetch_count,
                "filter": filter or {}
            }
            
            # Using Supabase rpc method
            response = db.client.rpc("match_documents_v2", params).execute()
            
            elapsed = (time.time() - start_time) * 1000
            
            if not response.data:
                logger.info(f"🕸️ VectorSearch: No matches above threshold {threshold}")
                return ToolResult(success=True, data=[], execution_time_ms=elapsed)
                
            results = []
            for item in response.data:
                meta = item.get("metadata", {})
                
                # --- Post-Filtering (Python Side) ---
                if filter:
                    # Check if all filter keys match metadata
                    # Special handling for "country_id" which might be top-level in some RPCs or inside metadata
                    # We check both
                    
                    match = True
                    for k, v in filter.items():
                        # Check metadata first
                        val = meta.get(k)
                        # If not in metadata, check top-level item (unlikely for match_documents usually, but possible)
                        if val is None:
                            val = item.get(k)
                        
                        if str(val) != str(v):
                            match = False
                            break
                    
                    if not match:
                        continue
                
                results.append(VectorSearchResult(
                    id=item.get("id"),
                    content=item.get("content"),
                    similarity=item.get("similarity"),
                    metadata=meta
                ))
                
                if len(results) >= count:
                    break
                
            logger.info(f"✅ VectorSearch: Found {len(results)} matches in {elapsed:.0f}ms")
            
            return ToolResult(
                success=True, 
                data=[r.__dict__ for r in results],
                execution_time_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"❌ VectorSearch RPC failed: {e}")
            return ToolResult(
                success=False, 
                error=f"Vector Infrastructure Error: {str(e)}",
                metadata={"suggestion": "Check if 'match_documents' function exists in DB"},
                execution_time_ms=(time.time() - start_time) * 1000
            )
