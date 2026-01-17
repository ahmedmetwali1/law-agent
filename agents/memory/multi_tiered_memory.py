"""
Multi-Tiered Memory System
نظام ذاكرة متعدد الطبقات مستوحى من الذاكرة البشرية

Based on research:
- "Memory in the Age of AI Agents" (arXiv:2512.13564)
- "O-Mem: Omni Memory System" (2025)

Architecture:
    Working Memory: Current context (short-term)
    Episodic Memory: Specific experiences and events
    Long-term Memory: Consolidated knowledge
    Meta-Memory: Knowledge about knowledge
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from collections import deque

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Types of memory in the system"""
    WORKING = "working"
    EPISODIC = "episodic"
    LONG_TERM = "long_term"
    META = "meta"


class MemoryImportance(str, Enum):
    """Importance levels for memory items"""
    CRITICAL = "critical"  # Must retain
    HIGH = "high"         # Important
    MEDIUM = "medium"     # Useful
    LOW = "low"          # Can be consolidated/removed


@dataclass
class MemoryItem:
    """Individual memory item with metadata"""
    content: str
    memory_type: MemoryType
    timestamp: datetime = field(default_factory=datetime.now)
    importance: MemoryImportance = MemoryImportance.MEDIUM
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0  # 0.0 to 1.0
    source: str = "internal"  # internal, external, derived
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance.value,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "confidence": self.confidence,
            "source": self.source,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """Create from dictionary"""
        return cls(
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            importance=MemoryImportance(data["importance"]),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            confidence=data.get("confidence", 1.0),
            source=data.get("source", "internal"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )


class WorkingMemory:
    """
    Working Memory (Short-term)
    Handles immediate context - limited capacity
    
    Features:
    - FIFO with importance-based retention
    - Automatic overflow to episodic memory
    - Fast access for current context
    """
    
    def __init__(self, max_capacity: int = 20):
        self.max_capacity = max_capacity
        self.items: deque = deque(maxlen=max_capacity)
        self._overflow_buffer: List[MemoryItem] = []
    
    def add(self, item: MemoryItem) -> None:
        """Add item to working memory"""
        # If at capacity and new item is important, push less important to overflow
        if len(self.items) >= self.max_capacity:
            self._handle_overflow(item)
        else:
            self.items.append(item)
        
        logger.debug(f"Added to working memory: {item.content[:50]}...")
    
    def _handle_overflow(self, new_item: MemoryItem) -> None:
        """Handle memory overflow intelligently"""
        # Find least important item
        least_important = min(
            self.items,
            key=lambda x: (x.importance.value, x.access_count, -x.timestamp.timestamp())
        )
        
        # If new item is more important, swap
        if new_item.importance.value < least_important.importance.value:
            self._overflow_buffer.append(least_important)
            self.items.remove(least_important)
            self.items.append(new_item)
        else:
            self._overflow_buffer.append(new_item)
    
    def get_context(self, max_items: int = None) -> List[MemoryItem]:
        """Get current context"""
        items = list(self.items)
        if max_items:
            items = items[-max_items:]
        
        # Update access stats
        for item in items:
            item.access_count += 1
            item.last_accessed = datetime.now()
        
        return items
    
    def clear_overflow(self) -> List[MemoryItem]:
        """Get and clear overflow buffer"""
        items = self._overflow_buffer.copy()
        self._overflow_buffer.clear()
        return items
    
    def clear(self) -> None:
        """Clear working memory"""
        self.items.clear()
        self._overflow_buffer.clear()


class EpisodicMemory:
    """
    Episodic Memory
    Stores specific experiences and events
    
    Features:
    - Time-indexed events
    - Experience consolidation
    - Pattern extraction
    """
    
    def __init__(self):
        self.episodes: List[MemoryItem] = []
        self._index_by_tags: Dict[str, List[int]] = {}
    
    def add(self, item: MemoryItem) -> None:
        """Add episodic memory"""
        item.memory_type = MemoryType.EPISODIC
        idx = len(self.episodes)
        self.episodes.append(item)
        
        # Index by tags
        for tag in item.tags:
            if tag not in self._index_by_tags:
                self._index_by_tags[tag] = []
            self._index_by_tags[tag].append(idx)
        
        logger.debug(f"Added to episodic memory: {item.content[:50]}...")
    
    def retrieve_by_tags(self, tags: List[str], limit: int = 10) -> List[MemoryItem]:
        """Retrieve episodes by tags"""
        indices = set()
        for tag in tags:
            if tag in self._index_by_tags:
                indices.update(self._index_by_tags[tag])
        
        episodes = [self.episodes[i] for i in sorted(indices, reverse=True)[:limit]]
        
        # Update access stats
        for ep in episodes:
            ep.access_count += 1
            ep.last_accessed = datetime.now()
        
        return episodes
    
    def retrieve_recent(self, limit: int = 10) -> List[MemoryItem]:
        """Get recent episodes"""
        recent = sorted(self.episodes, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        for ep in recent:
            ep.access_count += 1
            ep.last_accessed = datetime.now()
        
        return recent
    
    def get_frequently_accessed(self, limit: int = 10) -> List[MemoryItem]:
        """Get frequently accessed episodes"""
        return sorted(self.episodes, key=lambda x: x.access_count, reverse=True)[:limit]


class LongTermMemory:
    """
    Long-term Memory
    Consolidated, strategic knowledge
    
    Features:
    - Persistent storage
    - Consolidated facts and principles
    - Semantic organization
    """
    
    def __init__(self):
        self.knowledge: Dict[str, MemoryItem] = {}  # keyed by unique identifier
        self._semantic_index: Dict[str, List[str]] = {}  # concept -> memory_ids
    
    def add(self, key: str, item: MemoryItem) -> None:
        """Add to long-term memory"""
        item.memory_type = MemoryType.LONG_TERM
        self.knowledge[key] = item
        
        # Semantic indexing by tags
        for tag in item.tags:
            if tag not in self._semantic_index:
                self._semantic_index[tag] = []
            if key not in self._semantic_index[tag]:
                self._semantic_index[tag].append(key)
        
        logger.debug(f"Added to long-term memory: {key}")
    
    def retrieve(self, key: str) -> Optional[MemoryItem]:
        """Retrieve specific knowledge"""
        item = self.knowledge.get(key)
        if item:
            item.access_count += 1
            item.last_accessed = datetime.now()
        return item
    
    def search(self, tags: List[str], limit: int = 10) -> List[MemoryItem]:
        """Search by semantic tags"""
        keys = set()
        for tag in tags:
            if tag in self._semantic_index:
                keys.update(self._semantic_index[tag])
        
        items = [self.knowledge[k] for k in list(keys)[:limit]]
        
        for item in items:
            item.access_count += 1
            item.last_accessed = datetime.now()
        
        return items
    
    def consolidate(self, items: List[MemoryItem]) -> str:
        """Consolidate multiple items into single knowledge"""
        # This would use LLM to extract common patterns
        # For now, simple concatenation
        key = f"consolidated_{datetime.now().timestamp()}"
        consolidated_content = "\n".join([item.content for item in items])
        
        all_tags = set()
        for item in items:
            all_tags.update(item.tags)
        
        consolidated = MemoryItem(
            content=consolidated_content,
            memory_type=MemoryType.LONG_TERM,
            importance=MemoryImportance.HIGH,
            tags=list(all_tags),
            source="consolidated",
            metadata={"source_count": len(items)}
        )
        
        self.add(key, consolidated)
        return key


class MetaMemory:
    """
    Meta-Memory
    Knowledge about what the system knows
    
    Features:
    - Confidence tracking
    - Source provenance
    - Knowledge gaps identification
    """
    
    def __init__(self):
        self.confidence_map: Dict[str, float] = {}
        self.source_map: Dict[str, str] = {}
        self.last_updated: Dict[str, datetime] = {}
        self.knowledge_gaps: List[str] = []
    
    def track(self, key: str, confidence: float, source: str) -> None:
        """Track metadata about knowledge"""
        self.confidence_map[key] = confidence
        self.source_map[key] = source
        self.last_updated[key] = datetime.now()
    
    def get_confidence(self, key: str) -> float:
        """Get confidence level"""
        return self.confidence_map.get(key, 0.0)
    
    def is_reliable(self, key: str, threshold: float = 0.7) -> bool:
        """Check if knowledge is reliable"""
        return self.get_confidence(key) >= threshold
    
    def add_knowledge_gap(self, gap: str) -> None:
        """Record identified knowledge gap"""
        if gap not in self.knowledge_gaps:
            self.knowledge_gaps.append(gap)
            logger.info(f"Knowledge gap identified: {gap}")
    
    def get_knowledge_gaps(self) -> List[str]:
        """Get all identified knowledge gaps"""
        return self.knowledge_gaps.copy()


class MultiTieredMemory:
    """
    Complete Multi-Tiered Memory System
    
    Integrates all memory layers with intelligent routing
    """
    
    def __init__(self, working_capacity: int = 20):
        self.working = WorkingMemory(max_capacity=working_capacity)
        self.episodic = EpisodicMemory()
        self.long_term = LongTermMemory()
        self.meta = MetaMemory()
        
        logger.info("✅ Multi-Tiered Memory System initialized")
    
    def remember(
        self,
        content: str,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        tags: List[str] = None,
        confidence: float = 1.0,
        source: str = "internal"
    ) -> None:
        """
        Add memory to appropriate layer(s)
        
        Args:
            content: Memory content
            importance: How important this memory is
            tags: Semantic tags for indexing
            confidence: Confidence level (0-1)
            source: Source of information
        """
        item = MemoryItem(
            content=content,
            memory_type=MemoryType.WORKING,
            importance=importance,
            confidence=confidence,
            source=source,
            tags=tags or []
        )
        
        # Always add to working memory
        self.working.add(item)
        
        # If important, also add to episodic
        if importance in [MemoryImportance.HIGH, MemoryImportance.CRITICAL]:
            self.episodic.add(item)
        
        # Track in meta-memory
        key = f"memory_{datetime.now().timestamp()}"
        self.meta.track(key, confidence, source)
    
    def retrieve_context(self, max_items: int = 10) -> List[MemoryItem]:
        """Get current working memory context"""
        return self.working.get_context(max_items)
    
    def retrieve_similar_experiences(self, tags: List[str], limit: int = 5) -> List[MemoryItem]:
        """Retrieve similar past experiences"""
        return self.episodic.retrieve_by_tags(tags, limit)
    
    def retrieve_knowledge(self, tags: List[str], limit: int = 5) -> List[MemoryItem]:
        """Retrieve long-term knowledge"""
        return self.long_term.search(tags, limit)
    
    def consolidate_memory(self) -> Dict[str, Any]:
        """
        Consolidate working memory overflow to episodic/long-term
        
        Returns statistics about consolidation
        """
        stats = {
            "items_processed": 0,
            "to_episodic": 0,
            "to_long_term": 0
        }
        
        # Get overflow from working memory
        overflow = self.working.clear_overflow()
        stats["items_processed"] = len(overflow)
        
        for item in overflow:
            # Important items go to episodic
            if item.importance in [MemoryImportance.HIGH, MemoryImportance.CRITICAL]:
                self.episodic.add(item)
                stats["to_episodic"] += 1
            
            # Critical items also go to long-term
            if item.importance == MemoryImportance.CRITICAL:
                key = f"ltm_{datetime.now().timestamp()}"
                self.long_term.add(key, item)
                stats["to_long_term"] += 1
        
        if stats["items_processed"] > 0:
            logger.info(f"Memory consolidation: {stats}")
        
        return stats
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of memory system state"""
        return {
            "working_memory": {
                "current_items": len(self.working.items),
                "capacity": self.working.max_capacity,
                "overflow_pending": len(self.working._overflow_buffer)
            },
            "episodic_memory": {
                "total_episodes": len(self.episodic.episodes),
                "indexed_tags": len(self.episodic._index_by_tags)
            },
            "long_term_memory": {
                "total_knowledge": len(self.long_term.knowledge),
                "semantic_concepts": len(self.long_term._semantic_index)
            },
            "meta_memory": {
                "tracked_items": len(self.meta.confidence_map),
                "knowledge_gaps": len(self.meta.knowledge_gaps)
            }
        }


__all__ = [
    "MultiTieredMemory",
    "MemoryItem",
    "MemoryType",
    "MemoryImportance",
    "WorkingMemory",
    "EpisodicMemory",
    "LongTermMemory",
    "MetaMemory"
]
