"""
💾 Smart Search Cache v1.0

In-memory caching system for frequent legal searches.
Reduces repeated database/vector queries and improves response time.

Architecture:
- LRU cache with TTL expiration
- Hash-based key generation from query + context
- Automatic eviction of stale entries
- Thread-safe operations

Author: Legal AI System
Created: 2026-02-06
"""

import hashlib
import logging
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    results: List[Dict[str, Any]]
    created_at: datetime
    hit_count: int = 0
    query_hash: str = ""
    
    def is_expired(self, ttl: timedelta) -> bool:
        """Check if entry has expired."""
        return datetime.now() > self.created_at + ttl


@dataclass
class CacheStats:
    """Cache performance statistics."""
    total_hits: int = 0
    total_misses: int = 0
    evictions: int = 0
    current_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.total_hits + self.total_misses
        return self.total_hits / total if total > 0 else 0.0


# =============================================================================
# SEARCH CACHE
# =============================================================================

class SearchCache:
    """
    In-memory LRU cache for legal search results.
    
    Features:
    - LRU eviction when max size reached
    - TTL-based expiration (default 24 hours)
    - Thread-safe operations
    - Query normalization for better hit rates
    
    Usage:
        cache = SearchCache(max_size=500, ttl_hours=24)
        
        # Try to get cached result
        query_hash = cache.hash_query(query, context)
        cached = cache.get(query_hash)
        
        if cached:
            return cached
        
        # Compute result
        results = await search(query)
        
        # Cache it
        cache.set(query_hash, results)
    """
    
    def __init__(
        self, 
        max_size: int = 500, 
        ttl_hours: int = 24,
        enable_stats: bool = True
    ):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of entries to store
            ttl_hours: Time-to-live for entries in hours
            enable_stats: Whether to track statistics
        """
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self.enable_stats = enable_stats
        
        # OrderedDict for LRU ordering
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats() if enable_stats else None
    
    # =========================================================================
    # QUERY HASHING
    # =========================================================================
    
    @staticmethod
    def normalize_query(query: str) -> str:
        """
        Normalize query for consistent hashing.
        
        - Remove extra whitespace
        - Lowercase
        - Remove common stopwords that don't affect results
        """
        if not query:
            return ""
        
        # Basic normalization
        normalized = " ".join(query.strip().split())
        
        # Remove very common Arabic stopwords
        stopwords = {"هل", "هي", "هو", "في", "من", "إلى", "على", "عن", "مع", "و", "أو"}
        words = normalized.split()
        
        # Only remove if query has enough content
        if len(words) > 3:
            words = [w for w in words if w not in stopwords]
        
        return " ".join(words)
    
    @staticmethod
    def hash_query(
        query: str, 
        articles: Optional[List[int]] = None,
        laws: Optional[List[str]] = None,
        country_id: Optional[int] = None
    ) -> str:
        """
        Generate a deterministic hash for cache lookup.
        
        Args:
            query: The search query
            articles: List of article numbers in context
            laws: List of law names in context
            country_id: Country filter
            
        Returns:
            MD5 hash string
        """
        normalized = SearchCache.normalize_query(query)
        
        # Build key components
        key_parts = [normalized]
        
        if articles:
            key_parts.append(f"arts:{sorted(articles)}")
        
        if laws:
            key_parts.append(f"laws:{sorted(laws)}")
        
        if country_id:
            key_parts.append(f"cid:{country_id}")
        
        key = "|".join(key_parts)
        return hashlib.md5(key.encode("utf-8")).hexdigest()
    
    # =========================================================================
    # CACHE OPERATIONS
    # =========================================================================
    
    def get(self, query_hash: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached results by hash.
        
        Args:
            query_hash: Hash generated by hash_query()
            
        Returns:
            Cached results or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(query_hash)
            
            if entry is None:
                if self._stats:
                    self._stats.total_misses += 1
                return None
            
            # Check expiration
            if entry.is_expired(self.ttl):
                self._cache.pop(query_hash, None)
                if self._stats:
                    self._stats.total_misses += 1
                    self._stats.evictions += 1
                logger.debug(f"Cache entry expired: {query_hash[:8]}...")
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(query_hash)
            entry.hit_count += 1
            
            if self._stats:
                self._stats.total_hits += 1
            
            logger.info(f"🎯 Cache HIT: {query_hash[:8]}... (hits: {entry.hit_count})")
            
            return entry.results
    
    def set(self, query_hash: str, results: List[Dict[str, Any]]) -> None:
        """
        Store results in cache.
        
        Args:
            query_hash: Hash generated by hash_query()
            results: Search results to cache
        """
        with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            # Store new entry
            self._cache[query_hash] = CacheEntry(
                results=results,
                created_at=datetime.now(),
                query_hash=query_hash
            )
            self._cache.move_to_end(query_hash)
            
            if self._stats:
                self._stats.current_size = len(self._cache)
            
            logger.debug(f"💾 Cached: {query_hash[:8]}... ({len(results)} results)")
    
    def _evict_oldest(self) -> None:
        """Evict the least recently used entry."""
        if self._cache:
            oldest_key = next(iter(self._cache))
            self._cache.pop(oldest_key)
            if self._stats:
                self._stats.evictions += 1
                self._stats.current_size = len(self._cache)
            logger.debug(f"🗑️ Evicted: {oldest_key[:8]}...")
    
    def invalidate(self, query_hash: str) -> bool:
        """
        Manually invalidate a cache entry.
        
        Args:
            query_hash: Hash to invalidate
            
        Returns:
            True if entry was found and removed
        """
        with self._lock:
            if query_hash in self._cache:
                self._cache.pop(query_hash)
                if self._stats:
                    self._stats.current_size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            if self._stats:
                self._stats.current_size = 0
            logger.info("🧹 Cache cleared")
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired = [
                key for key, entry in self._cache.items()
                if entry.is_expired(self.ttl)
            ]
            
            for key in expired:
                self._cache.pop(key)
            
            if self._stats:
                self._stats.evictions += len(expired)
                self._stats.current_size = len(self._cache)
            
            if expired:
                logger.info(f"🧹 Cleaned up {len(expired)} expired entries")
            
            return len(expired)
    
    def get_stats(self) -> Optional[CacheStats]:
        """Get cache statistics."""
        if self._stats:
            self._stats.current_size = len(self._cache)
        return self._stats


# =============================================================================
# GLOBAL CACHE INSTANCE
# =============================================================================

# Singleton cache instance for the application
_global_cache: Optional[SearchCache] = None
_cache_lock = threading.Lock()

def get_search_cache() -> SearchCache:
    """
    Get the global search cache instance (singleton).
    
    Returns:
        SearchCache instance
    """
    global _global_cache
    
    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = SearchCache(max_size=500, ttl_hours=24)
                logger.info("🏗️ Initialized global search cache")
    
    return _global_cache


# =============================================================================
# CACHE DECORATOR
# =============================================================================

from functools import wraps

def cached_search(
    query_extractor=None,
    context_extractor=None
):
    """
    Decorator to add caching to search functions.
    
    Usage:
        @cached_search(
            query_extractor=lambda q, **kw: q,
            context_extractor=lambda **kw: kw.get('context', {})
        )
        async def hybrid_search(query: str, context: dict = None):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_search_cache()
            
            # Extract query and context for hashing
            query = query_extractor(*args, **kwargs) if query_extractor else args[0] if args else ""
            context = context_extractor(*args, **kwargs) if context_extractor else {}
            
            articles = context.get("active_articles", [])
            laws = context.get("active_laws", [])
            country_id = kwargs.get("country_id")
            
            # Generate hash
            query_hash = cache.hash_query(query, articles, laws, country_id)
            
            # Check cache
            cached = cache.get(query_hash)
            if cached is not None:
                return cached
            
            # Execute search
            results = await func(*args, **kwargs)
            
            # Cache results (only if we got valid results)
            if results and isinstance(results, list):
                cache.set(query_hash, results)
            
            return results
        
        return wrapper
    return decorator
