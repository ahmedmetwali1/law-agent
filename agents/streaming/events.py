"""
Event Classes
أنواع الأحداث للبث الحي
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
import json


class EventType(Enum):
    """أنواع الأحداث"""
    PLAN_CREATED = "plan_created"
    STEP_UPDATE = "step_update"
    PLAN_COMPLETED = "plan_completed"
    PLAN_FAILED = "plan_failed"
    PROGRESS_UPDATE = "progress_update"


class StepStatus(Enum):
    """حالات الخطوة"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class StepEvent:
    """حدث تحديث خطوة"""
    step_id: int
    status: StepStatus
    message: str = ""
    progress: int = 0
    result: Optional[str] = None
    error: Optional[str] = None
    attempt: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "status": self.status.value if isinstance(self.status, StepStatus) else self.status,
            "message": self.message,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "attempt": self.attempt,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class PlanEvent:
    """حدث متعلق بالخطة الكاملة"""
    event_type: EventType
    plan_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "plan_id": self.plan_id,
            "payload": self.payload,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class ProgressEvent:
    """حدث تحديث التقدم الإجمالي"""
    plan_id: str
    total_steps: int
    completed_steps: int
    current_step: Optional[int] = None
    percentage: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "current_step": self.current_step,
            "percentage": self.percentage,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


def create_sse_message(event: Any, event_name: str = "message") -> str:
    """إنشاء رسالة SSE بالصيغة الصحيحة"""
    json_data = event.to_json() if hasattr(event, 'to_json') else json.dumps(event, ensure_ascii=False)
    return f"event: {event_name}\ndata: {json_data}\n\n"


__all__ = ["EventType", "StepStatus", "StepEvent", "PlanEvent", "ProgressEvent", "create_sse_message"]
