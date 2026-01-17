"""
Hybrid Search Module
محرك البحث الهجين (Keyword + Vector Search)
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

from ..config.database import db
from ..config.settings import settings, TableNames
from .embeddings import create_query_embedding

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result data structure"""
    chunk_id: str
    source_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    
    # Additional fields from document_chunks
    hierarchy_path: Optional[str] = None
    ai_summary: Optional[str] = None
    legal_logic: Optional[str] = None
    keywords: Optional[List[str]] = None


class HybridSearchEngine:
    """Hybrid search combining keyword and vector search"""
    
    def __init__(
        self,
        keyword_weight: float = None,
        vector_weight: float = None,
        top_k: int = None
    ):
        """
        Initialize hybrid search engine
        
        Args:
            keyword_weight: Weight for keyword search (0-1)
            vector_weight: Weight for vector search (0-1)
            top_k: Number of top results to return
        """
        self.keyword_weight = keyword_weight or settings.keyword_weight
        self.vector_weight = vector_weight or settings.vector_weight
        self.top_k = top_k or settings.top_k_results
        
        # Validate weights
        if abs(self.keyword_weight + self.vector_weight - 1.0) > 0.01:
            logger.warning(f"Weights don't sum to 1.0: {self.keyword_weight + self.vector_weight}")
    
    def keyword_search(
        self,
        query: str,
        limit: int = None,
        filters: Dict[str, Any] = None
    ) -> List[SearchResult]:
        """
        Keyword-based search using Full-Text Search
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Additional filters (e.g., source_id, doc_type)
            
        Returns:
            List of search results
        """
        limit = limit or self.top_k
        
        try:
            # Build the query using PostgreSQL's to_tsquery for Arabic text
            # We use plainto_tsquery which is more forgiving with user input
            rpc_query = {
                "search_query": query,
                "result_limit": limit
            }
            
            # Use simple ilike search instead of text_search
            # text_search API has changed in newer supabase-py versions
            query_builder = db.document_chunks.select(
                "id, source_id, content, hierarchy_path, ai_summary, legal_logic, keywords, legal_domain"
            )
            
            # Use ilike for simpler keyword matching
            # Split query into words and search for any match
            words = query.split()[:3]  # Take first 3 words
            if words:
                # Search in content using ilike
                query_builder = query_builder.or_(",".join([f"content.ilike.%{w}%" for w in words]))
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if key == "legal_domain" and value:
                        # Filter by legal domain column (new feature)
                        query_builder = query_builder.eq("legal_domain", value)
                        logger.info(f"🔍 Filtering by legal_domain: {value}")
                    else:
                        query_builder = query_builder.eq(key, value)
            
            # Execute query
            response = query_builder.limit(limit).execute()
            
            results = []
            for idx, row in enumerate(response.data):
                results.append(SearchResult(
                    chunk_id=row['id'],
                    source_id=row['source_id'],
                    content=row['content'],
                    score=1.0 - (idx * 0.05),  # Simple ranking by position
                    metadata={'search_type': 'keyword'},
                    hierarchy_path=row.get('hierarchy_path'),
                    ai_summary=row.get('ai_summary'),
                    legal_logic=row.get('legal_logic'),
                    keywords=row.get('keywords', [])
                ))
            
            logger.info(f"✅ Keyword search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Keyword search failed: {e}")
            return []
    
    def vector_search(
        self,
        query: str,
        query_embedding: List[float] = None,
        limit: int = None,
        filters: Dict[str, Any] = None
    ) -> List[SearchResult]:
        """
        Vector-based semantic search using embeddings
        
        Args:
            query: Search query (used if query_embedding not provided)
            query_embedding: Pre-computed query embedding
            limit: Maximum number of results
            filters: Additional filters
            
        Returns:
            List of search results
        """
        limit = limit or self.top_k
        
        try:
            # Generate embedding if not provided
            if query_embedding is None:
                query_embedding = create_query_embedding(query)
            
            # Note: RPC functions (match_documents, match_document_chunks) don't match our schema
            # Using direct vector search instead
            logger.info("Using direct vector search (RPC not configured)")
            return self._vector_search_fallback(query_embedding, limit, filters)
            
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return []
    
    def _vector_search_fallback(
        self,
        query_embedding: List[float],
        limit: int,
        filters: Dict[str, Any] = None
    ) -> List[SearchResult]:
        """Fallback vector search without RPC (slower but works)"""
        # Note: This is less efficient and should only be used if RPC is not set up
        # For production, create the RPC function in Supabase
        
        query_builder = db.document_chunks.select(
            "id, source_id, content, embedding, hierarchy_path, ai_summary, legal_logic, keywords"
        )
        
        if filters:
            for key, value in filters.items():
                query_builder = query_builder.eq(key, value)
        
        response = query_builder.limit(limit * 3).execute()  # Get more to filter
        
        # Calculate similarity manually (cosine similarity)
        results = []
        for row in response.data:
            embedding_data = row.get('embedding')
            if embedding_data:
                # Parse embedding - it comes as string from database
                try:
                    if isinstance(embedding_data, str):
                        # Remove brackets and split
                        embedding_str = embedding_data.strip('[]')
                        doc_embedding = [float(x) for x in embedding_str.split(',')]
                    else:
                        doc_embedding = embedding_data
                    
                    similarity = self._cosine_similarity(query_embedding, doc_embedding)
                    results.append(SearchResult(
                        chunk_id=row['id'],
                        source_id=row['source_id'],
                        content=row['content'],
                        score=similarity,
                        metadata={'search_type': 'vector_fallback'},
                        hierarchy_path=row.get('hierarchy_path'),
                        ai_summary=row.get('ai_summary'),
                        legal_logic=row.get('legal_logic'),
                        keywords=row.get('keywords', [])
                    ))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse embedding: {e}")
                    continue
        
        # Sort by similarity and return top-k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def hybrid_search(
        self,
        query: str,
        limit: int = None,
        filters: Dict[str, Any] = None,
        query_embedding: List[float] = None
    ) -> List[SearchResult]:
        """
        Hybrid search combining keyword and vector search
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Additional filters
            query_embedding: Pre-computed query embedding
            
        Returns:
            List of merged and ranked search results
        """
        limit = limit or self.top_k
        
        logger.info(f"🔍 Starting hybrid search for: {query[:100]}...")
        
        # Perform both searches
        keyword_results = self.keyword_search(query, limit=limit*2, filters=filters)
        vector_results = self.vector_search(query, query_embedding, limit=limit*2, filters=filters)
        
        # Merge results
        merged_results = self._merge_results(keyword_results, vector_results)
        
        # Return top-k
        top_results = merged_results[:limit]
        
        logger.info(f"✅ Hybrid search returned {len(top_results)} results")
        return top_results
    
    def _merge_results(
        self,
        keyword_results: List[SearchResult],
        vector_results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Merge and rank results from keyword and vector search
        
        Uses weighted scoring to combine relevance from both methods
        """
        # Create a dictionary to hold combined scores
        combined: Dict[str, SearchResult] = {}
        
        # Process keyword results
        for result in keyword_results:
            chunk_id = result.chunk_id
            weighted_score = result.score * self.keyword_weight
            
            if chunk_id in combined:
                combined[chunk_id].score += weighted_score
                combined[chunk_id].metadata['has_keyword_match'] = True
            else:
                result.score = weighted_score
                result.metadata['has_keyword_match'] = True
                result.metadata['has_vector_match'] = False
                combined[chunk_id] = result
        
        # Process vector results
        for result in vector_results:
            chunk_id = result.chunk_id
            weighted_score = result.score * self.vector_weight
            
            if chunk_id in combined:
                combined[chunk_id].score += weighted_score
                combined[chunk_id].metadata['has_vector_match'] = True
            else:
                result.score = weighted_score
                result.metadata['has_keyword_match'] = False
                result.metadata['has_vector_match'] = True
                combined[chunk_id] = result
        
        # Convert to list and sort by combined score
        merged_list = list(combined.values())
        merged_list.sort(key=lambda x: x.score, reverse=True)
        
        return merged_list
    
    def get_full_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the full source document from legal_sources
        
        Args:
            source_id: ID of the source document
            
        Returns:
            Full source document data
        """
        try:
            response = db.legal_sources.select("*").eq("id", source_id).execute()
            
            if response.data:
                logger.info(f"✅ Retrieved full source: {source_id}")
                return response.data[0]
            else:
                logger.warning(f"⚠️ Source not found: {source_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve source: {e}")
            return None


# Global search engine instance
search_engine = HybridSearchEngine()


def search(
    query: str, 
    limit: int = None, 
    method: str = "hybrid",
    filters: Dict[str, Any] = None
) -> List[SearchResult]:
    """
    Convenience function for searching
    
    Args:
        query: Search query
        limit: Maximum number of results
        method: Search method ('keyword', 'vector', 'hybrid')
        filters: Optional filters (e.g., {"legal_domain": "أحوال شخصية"})
        
    Returns:
        List of search results
    """
    if method == "keyword":
        return search_engine.keyword_search(query, limit, filters=filters)
    elif method == "vector":
        return search_engine.vector_search(query, limit=limit, filters=filters)
    else:  # hybrid
        return search_engine.hybrid_search(query, limit, filters=filters)


__all__ = [
    "HybridSearchEngine",
    "SearchResult",
    "search_engine",
    "search"
]
