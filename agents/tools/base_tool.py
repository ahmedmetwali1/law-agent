"""
Base Tool Class
الفئة الأساسية للأدوات
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result returned by a tool execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms
        }


class BaseTool(ABC):
    """
    Abstract base class for all agent tools.
    
    Each tool should:
    1. Have a unique name and description.
    2. Implement `run(args)` to perform the action.
    3. Optionally implement `can_handle(query)` for auto-routing.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.usage_count = 0
        self.last_used: Optional[datetime] = None
        logger.info(f"🔧 Tool initialized: {self.name}")
    
    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given arguments.
        
        Returns:
            ToolResult with success status and data.
        """
        pass
    
    def can_handle(self, query: str) -> float:
        """
        Check if this tool can handle the given query.
        
        Args:
            query: The user query or request.
            
        Returns:
            Confidence score (0.0 to 1.0). 0 means cannot handle.
        """
        # Default: cannot determine, return 0
        return 0.0
    
    def _track_usage(self):
        """Track tool usage statistics"""
        self.usage_count += 1
        self.last_used = datetime.now()
    
    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"


__all__ = ["BaseTool", "ToolResult"]
