"""
Task Models for Orchestrator
نماذج المهام والتنفيذ
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """Represents a single task to execute"""
    id: str
    type: str  # Tool name (e.g., "create_client")
    params: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    description: str = ""
    is_critical: bool = True  # If fails, stop execution
    
    def __post_init__(self):
        if not self.description:
            self.description = f"Execute {self.type}"


@dataclass
class ExecutionStep:
    """Represents a step in execution plan"""
    id: str
    task: Task
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_time: int = 5  # seconds
    
    @property
    def description(self) -> str:
        """Get user-friendly description"""
        descriptions = {
            'create_client': f"إضافة الموكل {self.task.params.get('full_name', '')}",
            'create_case': f"فتح القضية {self.task.params.get('case_title', '')}",
            'create_hearing': f"جدولة جلسة",
            'search_knowledge': f"البحث في القوانين",
            'get_client_details': f"جلب بيانات الموكل",
            'list_all_clients': f"عرض قائمة الموكلين"
        }
        return descriptions.get(self.task.type, self.task.description)
    
    @property
    def success_message(self) -> str:
        """Get success message"""
        messages = {
            'create_client': f"تم إضافة الموكل بنجاح",
            'create_case': f"تم فتح القضية بنجاح",
            'create_hearing': f"تم جدولة الجلسة",
            'search_knowledge': f"اكتمل البحث",
        }
        return messages.get(self.task.type, "تم التنفيذ بنجاح")
    
    @property
    def error_message(self) -> str:
        """Get error message"""
        return f"فشل في {self.description}"


@dataclass
class ExecutionPlan:
    """Complete execution plan"""
    id: str
    steps: List[ExecutionStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_step(self, step: ExecutionStep):
        """Add step to plan"""
        self.steps.append(step)
    
    @property
    def total_estimated_time(self) -> int:
        """Total estimated execution time"""
        return sum(step.estimated_time for step in self.steps)
    
    @property
    def progress(self) -> float:
        """Current progress (0-1)"""
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status in [TaskStatus.SUCCESS, TaskStatus.FAILED])
        return completed / len(self.steps)


@dataclass
class ExecutionResult:
    """Result of plan execution"""
    plan_id: str
    success: bool
    results: List[Any] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Execution duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'plan_id': self.plan_id,
            'success': self.success,
            'results': self.results,
            'errors': self.errors,
            'duration': self.duration
        }


__all__ = [
    'Task',
    'TaskStatus', 
    'ExecutionStep',
    'ExecutionPlan',
    'ExecutionResult'
]
