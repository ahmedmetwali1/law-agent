"""
Memory Consolidator
تجميع وتنظيف الذاكرة في الخلفية

Based on:
- Mem0 dynamic memory management
- "Memory in the Age of AI Agents" consolidation patterns

Features:
- Extract salient spans (المعلومات البارزة)
- Merge duplicates
- Background consolidation
- Pattern extraction
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from .multi_tiered_memory import (
    MemoryItem,
    MemoryType,
    MemoryImportance,
    MultiTieredMemory
)

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    """
    Intelligent memory consolidation
    Extracts patterns, removes duplicates, consolidates knowledge
    """
    
    def __init__(self, memory_system: MultiTieredMemory):
        self.memory = memory_system
        self.consolidation_history: List[Dict[str, Any]] = []
    
    def extract_salient_spans(self, items: List[MemoryItem]) -> List[MemoryItem]:
        """
        Extract most important/salient information
        
        Uses:
        - Importance scores
        - Access frequency
        - Recency
        """
        # Score each item
        scored_items = []
        now = datetime.now()
        
        for item in items:
            # Calculate composite score
            recency_score = 1.0 / (1 + (now - item.timestamp).total_seconds() / 3600)
            importance_score = {
                MemoryImportance.CRITICAL: 1.0,
                MemoryImportance.HIGH: 0.7,
                MemoryImportance.MEDIUM: 0.4,
                MemoryImportance.LOW: 0.1
            }[item.importance]
            access_score = min(item.access_count / 10.0, 1.0)
            
            composite = (
                0.3 * recency_score +
                0.4 * importance_score +
                0.3 * access_score
            )
            
            scored_items.append((composite, item))
        
        # Sort by score and return top items
        scored_items.sort(key=lambda x: x[0], reverse=True)
        
        # Keep top 70% by default
        keep_count = max(1, int(len(scored_items) * 0.7))
        salient = [item for score, item in scored_items[:keep_count]]
        
        logger.info(f"Extracted {len(salient)} salient items from {len(items)}")
        return salient
    
    def merge_duplicates(self, items: List[MemoryItem], similarity_threshold: float = 0.8) -> List[MemoryItem]:
        """
        Merge duplicate or highly similar memories
        
        Simple implementation: exact match on content
        Advanced: would use embeddings for semantic similarity
        """
        seen_content: Dict[str, MemoryItem] = {}
        merged: List[MemoryItem] = []
        duplicates_found = 0
        
        for item in items:
            # Simple content-based deduplication
            content_key = item.content.strip().lower()
            
            if content_key in seen_content:
                # Merge: increase access count, update importance
                existing = seen_content[content_key]
                existing.access_count += item.access_count
                
                # Keep higher importance
                if item.importance.value < existing.importance.value:
                    existing.importance = item.importance
                
                # Merge tags
                existing.tags = list(set(existing.tags + item.tags))
                
                duplicates_found += 1
            else:
                seen_content[content_key] = item
                merged.append(item)
        
        if duplicates_found > 0:
            logger.info(f"Merged {duplicates_found} duplicate memories")
        
        return merged
    
    def extract_patterns(self, items: List[MemoryItem]) -> List[Dict[str, Any]]:
        """
        Extract common patterns from memories
        
        Returns identified patterns with metadata
        """
        patterns = []
        
        # Group by tags
        tag_groups: Dict[str, List[MemoryItem]] = defaultdict(list)
        for item in items:
            for tag in item.tags:
                tag_groups[tag].append(item)
        
        # Find frequent patterns (tags appearing in multiple memories)
        for tag, tagged_items in tag_groups.items():
            if len(tagged_items) >= 3:  # Pattern threshold
                patterns.append({
                    "pattern_type": "tag_frequency",
                    "tag": tag,
                    "frequency": len(tagged_items),
                    "memories": [item.content[:100] for item in tagged_items[:3]]
                })
        
        # Temporal patterns (events happening at similar times)
        # Group by hour of day
        hour_groups: Dict[int, List[MemoryItem]] = defaultdict(list)
        for item in items:
            hour = item.timestamp.hour
            hour_groups[hour].append(item)
        
        for hour, hour_items in hour_groups.items():
            if len(hour_items) >= 3:
                patterns.append({
                    "pattern_type": "temporal",
                    "hour": hour,
                    "frequency": len(hour_items),
                    "description": f"Events often occur around {hour}:00"
                })
        
        logger.info(f"Extracted {len(patterns)} patterns")
        return patterns
    
    def consolidate_to_long_term(
        self,
        min_access_count: int = 3,
        min_age_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Consolidate episodic memories to long-term storage
        
        Args:
            min_access_count: Minimum accesses to qualify
            min_age_hours: Minimum age in hours
        
        Returns:
            Consolidation statistics
        """
        stats = {
            "candidates": 0,
            "consolidated": 0,
            "patterns_found": 0
        }
        
        # Get frequently accessed episodic memories
        frequent = self.memory.episodic.get_frequently_accessed(limit=100)
        
        # Filter by age and access count
        now = datetime.now()
        candidates = [
            item for item in frequent
            if item.access_count >= min_access_count
            and (now - item.timestamp).total_seconds() / 3600 >= min_age_hours
        ]
        
        stats["candidates"] = len(candidates)
        
        # Extract salient information
        salient = self.extract_salient_spans(candidates)
        
        # Merge duplicates
        merged = self.merge_duplicates(salient)
        
        # Extract patterns
        patterns = self.extract_patterns(merged)
        stats["patterns_found"] = len(patterns)
        
        # Move to long-term memory
        for item in merged:
            key = f"consolidated_{item.timestamp.isoformat()}_{hash(item.content) % 10000}"
            
            # Mark as consolidated
            item.metadata["consolidated"] = True
            item.metadata["consolidation_time"] = datetime.now().isoformat()
            
            self.memory.long_term.add(key, item)
            stats["consolidated"] += 1
        
        # Store patterns as knowledge
        for i, pattern in enumerate(patterns):
            pattern_item = MemoryItem(
                content=f"Pattern: {pattern}",
                memory_type=MemoryType.LONG_TERM,
                importance=MemoryImportance.HIGH,
                tags=["pattern", pattern["pattern_type"]],
                source="pattern_extraction",
                metadata=pattern
            )
            
            key = f"pattern_{i}_{datetime.now().timestamp()}"
            self.memory.long_term.add(key, pattern_item)
        
        # Record consolidation
        self.consolidation_history.append({
            "timestamp": datetime.now().isoformat(),
            "stats": stats
        })
        
        logger.info(f"Consolidation complete: {stats}")
        return stats
    
    def auto_consolidate(self) -> Dict[str, Any]:
        """
        Automatic consolidation routine
        Called periodically or when memory is full
        """
        logger.info("🔄 Starting automatic memory consolidation...")
        
        # Step 1: Consolidate working memory overflow
        working_stats = self.memory.consolidate_memory()
        
        # Step 2: Consolidate episodic to long-term
        lt_stats = self.consolidate_to_long_term(
            min_access_count=2,  # Lower threshold for auto
            min_age_hours=12     # Shorter time for auto
        )
        
        return {
            "working_memory": working_stats,
            "long_term": lt_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_consolidation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent consolidation history"""
        return self.consolidation_history[-limit:]


__all__ = ["MemoryConsolidator"]
