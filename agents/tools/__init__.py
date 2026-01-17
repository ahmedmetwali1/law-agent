"""
Agent Tools Module
أدوات الوكلاء الذكية - مجموعة شاملة من الأدوات للبحث والتفكير والتحكم
"""

from .base_tool import BaseTool, ToolResult
from .search_tool import SearchKnowledgeTool
from .quick_answer_tool import QuickAnswerTool
from .deep_thinking import DeepThinkingTool, Viewpoint, Contradiction
from .lookup_tools import LookupPrincipleTool, LegalSourceTool
from .react_engine import ReActEngine, ThinkingStep

# New enhanced tools
from .fetch_tools import (
    FetchByIdTool, 
    FlexibleSearchTool, 
    GetRelatedDocumentTool,
    SUPPORTED_TABLES,
    PaginationInfo
)
from .continuation_tools import (
    ContinueThinkingTool,
    WaitTool,
    ErrorRecoveryTool,
    CheckpointTool,
    ThinkingState
)

# Plan Tracker Tool (NEW)
from .plan_tracker_tool import (
    PlanTrackerTool,
    ExecutionPlan,
    PlanStep,
    StepStatus
)

__all__ = [
    # Base
    "BaseTool",
    "ToolResult",
    
    # Search Tools
    "SearchKnowledgeTool",
    "QuickAnswerTool",
    "LookupPrincipleTool",
    "LegalSourceTool",
    
    # Fetch Tools (NEW)
    "FetchByIdTool",
    "FlexibleSearchTool",
    "GetRelatedDocumentTool",
    "SUPPORTED_TABLES",
    "PaginationInfo",
    
    # Thinking Tools
    "DeepThinkingTool",
    "Viewpoint",
    "Contradiction",
    "ReActEngine",
    "ThinkingStep",
    
    # Continuation & Control Tools (NEW)
    "ContinueThinkingTool",
    "WaitTool",
    "ErrorRecoveryTool",
    "CheckpointTool",
    "ThinkingState",
    
    # Plan Tracker (NEW)
    "PlanTrackerTool",
    "ExecutionPlan",
    "PlanStep",
    "StepStatus"
]
