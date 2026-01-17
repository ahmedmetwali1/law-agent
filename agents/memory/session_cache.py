"""
Session-Level Caching System
Eliminates redundant database queries for better performance
"""

import time
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class SessionCache:
    """
    Session-level cache for lawyer data
    
    Implements TTL (Time-To-Live) caching to reduce database load
    and improve response times.
    
    Benefits:
    - Eliminates redundant DB queries (100ms+ per query)
    - Reduces latency significantly
    - Simple LRU-like behavior with TTL
    """
    
    def __init__(self, lawyer_id: str, ttl: int = 300):
        """
        Initialize session cache
        
        Args:
            lawyer_id: Lawyer's unique ID
            ttl: Time to live in seconds (default: 5 minutes)
        """
        self.lawyer_id = lawyer_id
        self.ttl = ttl
        
        # Cache storage
        self._profile_cache: Optional[Dict[str, Any]] = None
        self._profile_timestamp: Optional[float] = None
        
        # Statistics
        self.stats = {
            "profile_hits": 0,
            "profile_misses": 0
        }
        
        logger.info(f"✅ SessionCache initialized for lawyer {lawyer_id} (TTL: {ttl}s)")
    
    def get_profile(self, fetch_fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get lawyer profile with caching
        
        Args:
            fetch_fn: Function to fetch profile from database
            
        Returns:
            Profile data dictionary
            
        Example:
            >>> def fetch():
            ...     return db.get_user_by_id(lawyer_id)
            >>> profile = cache.get_profile(fetch)
        """
        now = time.time()
        
        # Check cache validity
        if (self._profile_cache and 
            self._profile_timestamp and 
            (now - self._profile_timestamp) < self.ttl):
            # Cache HIT
            self.stats["profile_hits"] += 1
            logger.debug(f"💨 Profile cache HIT for {self.lawyer_id} "
                        f"(hit rate: {self.get_hit_rate():.1%})")
            return self._profile_cache
        
        # Cache MISS - fetch from database
        self.stats["profile_misses"] += 1
        logger.debug(f"🔄 Profile cache MISS for {self.lawyer_id} - fetching from DB...")
        
        try:
            self._profile_cache = fetch_fn()
            self._profile_timestamp = now
            logger.info(f"✅ Profile cached for {self.lawyer_id}")
            return self._profile_cache
        except Exception as e:
            logger.error(f"❌ Failed to fetch profile: {e}")
            # Return stale cache if available as fallback
            if self._profile_cache:
                logger.warning("⚠️ Returning stale cache due to fetch error")
                return self._profile_cache
            raise
    
    def invalidate_profile(self):
        """
        Invalidate profile cache
        
        Call this when profile data changes (e.g., after update)
        """
        self._profile_cache = None
        self._profile_timestamp = None
        logger.info(f"🗑️ Profile cache invalidated for {self.lawyer_id}")
    
    def clear_all(self):
        """Clear all caches"""
        self.invalidate_profile()
        self.stats = {"profile_hits": 0, "profile_misses": 0}
        logger.info(f"🗑️ All caches cleared for {self.lawyer_id}")
    
    def get_hit_rate(self) -> float:
        """
        Calculate cache hit rate
        
        Returns:
            Hit rate as a float between 0 and 1
        """
        total = self.stats["profile_hits"] + self.stats["profile_misses"]
        if total == 0:
            return 0.0
        return self.stats["profile_hits"] / total
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        return {
            "lawyer_id": self.lawyer_id,
            "ttl": self.ttl,
            "profile_cached": self._profile_cache is not None,
            "profile_age_seconds": (
                time.time() - self._profile_timestamp 
                if self._profile_timestamp else None
            ),
            "hit_rate": self.get_hit_rate(),
            **self.stats
        }


__all__ = ["SessionCache"]
