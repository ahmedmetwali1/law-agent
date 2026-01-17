"""
Continuation Tools - أدوات الاستمرارية والتحكم
Tools for continuing thinking, waiting, and error recovery
"""

import time
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class ThinkingState:
    """
    حالة التفكير المحفوظة
    Saved thinking state for continuation
    """
    session_id: str
    current_question: str
    gathered_info: List[Dict[str, Any]] = field(default_factory=list)
    verified_facts: List[str] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)
    contradictions: List[Dict[str, str]] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    iteration_count: int = 0
    continuation_count: int = 0
    last_checkpoint: Optional[str] = None
    confidence_level: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThinkingState':
        return cls(**data)


class ContinueThinkingTool(BaseTool):
    """
    أداة استكمال التفكير
    
    Allows the agent to save its thinking state and request
    continuation in a new turn to avoid context overflow.
    
    Features:
    - Save current progress
    - Request continuation
    - Prevent infinite loops (max 5 continuations)
    - Transfer state between turns
    """
    
    MAX_CONTINUATIONS = 5
    
    def __init__(self):
        super().__init__(
            name="continue_thinking",
            description="حفظ حالة التفكير وطلب استكمال في جولة جديدة"
        )
        self._active_sessions: Dict[str, ThinkingState] = {}
    
    def run(
        self,
        action: str,  # "save", "load", "continue", "complete"
        session_id: Optional[str] = None,
        state_data: Optional[Dict[str, Any]] = None,
        next_action: Optional[str] = None,
        reason: Optional[str] = None
    ) -> ToolResult:
        """
        Manage thinking continuation.
        
        Args:
            action: 
                - "save": Save current state
                - "load": Load existing state
                - "continue": Request continuation
                - "complete": Mark thinking as complete
            session_id: Unique session identifier
            state_data: Current thinking state to save
            next_action: What to do next after continuation
            reason: Why continuation is needed
            
        Returns:
            ToolResult with state info or continuation request
        """
        self._track_usage()
        start_time = time.time()
        
        try:
            if action == "save":
                return self._save_state(session_id, state_data)
                
            elif action == "load":
                return self._load_state(session_id)
                
            elif action == "continue":
                return self._request_continuation(session_id, next_action, reason)
                
            elif action == "complete":
                return self._complete_session(session_id)
                
            else:
                return ToolResult(
                    success=False,
                    error=f"إجراء غير معروف: {action}",
                    metadata={
                        "valid_actions": ["save", "load", "continue", "complete"],
                        "error_code": "INVALID_ACTION"
                    },
                    execution_time_ms=(time.time() - start_time) * 1000
                )
                
        except Exception as e:
            logger.error(f"❌ ContinueThinking failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"error_code": "CONTINUATION_ERROR"},
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _save_state(self, session_id: str, state_data: Dict[str, Any]) -> ToolResult:
        """Save current thinking state"""
        if not session_id:
            session_id = f"session_{int(time.time())}"
        
        # Create or update state
        if session_id in self._active_sessions:
            state = self._active_sessions[session_id]
            # Update fields
            for key, value in state_data.items():
                if hasattr(state, key):
                    setattr(state, key, value)
        else:
            state = ThinkingState(
                session_id=session_id,
                current_question=state_data.get("current_question", ""),
                **{k: v for k, v in state_data.items() if k != "current_question" and k != "session_id"}
            )
        
        state.last_checkpoint = datetime.now().isoformat()
        self._active_sessions[session_id] = state
        
        logger.info(f"💾 Saved thinking state for session {session_id}")
        
        return ToolResult(
            success=True,
            data={"session_id": session_id, "state": state.to_dict()},
            metadata={
                "action": "save",
                "iteration": state.iteration_count,
                "continuations": state.continuation_count
            }
        )
    
    def _load_state(self, session_id: str) -> ToolResult:
        """Load existing thinking state"""
        if session_id not in self._active_sessions:
            return ToolResult(
                success=False,
                error=f"جلسة غير موجودة: {session_id}",
                metadata={"error_code": "SESSION_NOT_FOUND"}
            )
        
        state = self._active_sessions[session_id]
        logger.info(f"📂 Loaded thinking state for session {session_id}")
        
        return ToolResult(
            success=True,
            data=state.to_dict(),
            metadata={
                "action": "load",
                "iteration": state.iteration_count,
                "continuations": state.continuation_count
            }
        )
    
    def _request_continuation(
        self, 
        session_id: str, 
        next_action: str, 
        reason: str
    ) -> ToolResult:
        """Request thinking continuation"""
        if session_id not in self._active_sessions:
            return ToolResult(
                success=False,
                error="يجب حفظ الحالة أولاً قبل طلب الاستمرار",
                metadata={"error_code": "NO_STATE_SAVED"}
            )
        
        state = self._active_sessions[session_id]
        
        # Check continuation limit
        if state.continuation_count >= self.MAX_CONTINUATIONS:
            logger.warning(f"⚠️ Max continuations reached for {session_id}")
            return ToolResult(
                success=False,
                error=f"تم الوصول للحد الأقصى من الاستمرارات ({self.MAX_CONTINUATIONS})",
                metadata={
                    "error_code": "MAX_CONTINUATIONS_REACHED",
                    "suggestion": "يجب إنهاء التفكير وتقديم إجابة بالمعلومات المتوفرة"
                }
            )
        
        state.continuation_count += 1
        state.next_actions = [next_action] if next_action else []
        
        logger.info(f"🔄 Requesting continuation {state.continuation_count}/{self.MAX_CONTINUATIONS}")
        
        return ToolResult(
            success=True,
            data={
                "continuation_requested": True,
                "session_id": session_id,
                "next_action": next_action,
                "reason": reason,
                "state_summary": {
                    "gathered_info_count": len(state.gathered_info),
                    "verified_facts_count": len(state.verified_facts),
                    "confidence": state.confidence_level
                }
            },
            metadata={
                "action": "continue",
                "continuation_number": state.continuation_count,
                "remaining": self.MAX_CONTINUATIONS - state.continuation_count
            }
        )
    
    def _complete_session(self, session_id: str) -> ToolResult:
        """Mark session as complete and clean up"""
        if session_id in self._active_sessions:
            state = self._active_sessions.pop(session_id)
            logger.info(f"✅ Completed session {session_id} after {state.iteration_count} iterations")
            
            return ToolResult(
                success=True,
                data={
                    "session_completed": True,
                    "total_iterations": state.iteration_count,
                    "total_continuations": state.continuation_count,
                    "final_confidence": state.confidence_level
                },
                metadata={"action": "complete"}
            )
        
        return ToolResult(
            success=True,
            data={"session_completed": True, "message": "لا توجد جلسة نشطة"},
            metadata={"action": "complete"}
        )


class WaitTool(BaseTool):
    """
    أداة الانتظار الديناميكي
    
    Allows the agent to request a wait/pause for:
    - Rate limiting
    - Waiting for resources
    - Pacing API calls
    
    Max wait: 10 seconds
    """
    
    MAX_WAIT_SECONDS = 10
    
    def __init__(self):
        super().__init__(
            name="wait",
            description="انتظار لفترة محددة (1-10 ثواني)"
        )
    
    def run(
        self,
        seconds: float,
        reason: Optional[str] = None
    ) -> ToolResult:
        """
        Wait for specified duration.
        
        Args:
            seconds: Duration to wait (1-10 seconds)
            reason: Why waiting is needed
            
        Returns:
            ToolResult after wait completes
        """
        self._track_usage()
        
        # Validate and cap duration
        seconds = max(0.5, min(seconds, self.MAX_WAIT_SECONDS))
        
        logger.info(f"⏳ Waiting for {seconds}s: {reason or 'No reason provided'}")
        
        time.sleep(seconds)
        
        logger.info(f"✅ Wait complete")
        
        return ToolResult(
            success=True,
            data={
                "waited_seconds": seconds,
                "reason": reason
            },
            metadata={"action": "wait"}
        )


class ErrorRecoveryTool(BaseTool):
    """
    أداة استرداد الأخطاء
    
    Analyzes errors and suggests recovery strategies.
    Helps the agent understand what went wrong and how to proceed.
    """
    
    ERROR_STRATEGIES = {
        "SEARCH_FAILED": {
            "description": "فشل البحث",
            "suggestions": [
                "جرب كلمات مفتاحية أبسط",
                "قلل عدد الكلمات في البحث",
                "استخدم method='any' بدلاً من 'all'",
                "جرب البحث في جدول مختلف"
            ],
            "retry_allowed": True
        },
        "NOT_FOUND": {
            "description": "لم يتم العثور على النتائج",
            "suggestions": [
                "تحقق من صحة الـ ID",
                "جرب البحث بكلمات مختلفة",
                "قد تكون البيانات غير موجودة بعد"
            ],
            "retry_allowed": True
        },
        "TIMEOUT": {
            "description": "انتهت المهلة الزمنية",
            "suggestions": [
                "انتظر قليلاً ثم أعد المحاولة",
                "قلل حجم الطلب",
                "جرب طلب أصغر"
            ],
            "retry_allowed": True
        },
        "MAX_CONTINUATIONS_REACHED": {
            "description": "تم الوصول للحد الأقصى من الاستمرارات",
            "suggestions": [
                "قدم إجابة بالمعلومات المتوفرة",
                "اذكر أن الإجابة قد تكون غير مكتملة",
                "اقترح متابعة البحث لاحقاً"
            ],
            "retry_allowed": False
        },
        "UNKNOWN": {
            "description": "خطأ غير معروف",
            "suggestions": [
                "سجل الخطأ للمراجعة",
                "جرب طريقة بديلة"
            ],
            "retry_allowed": True
        }
    }
    
    def __init__(self):
        super().__init__(
            name="error_recovery",
            description="تحليل الأخطاء واقتراح خطوات الاسترداد"
        )
    
    def run(
        self,
        error_code: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Analyze error and suggest recovery.
        
        Args:
            error_code: Error code from failed tool
            error_message: Detailed error message
            context: Additional context about the error
            
        Returns:
            ToolResult with recovery suggestions
        """
        self._track_usage()
        start_time = time.time()
        
        logger.info(f"🔧 ErrorRecovery: Analyzing {error_code}")
        
        # Get strategy for this error
        strategy = self.ERROR_STRATEGIES.get(
            error_code, 
            self.ERROR_STRATEGIES["UNKNOWN"]
        )
        
        # Build recovery plan
        recovery_plan = {
            "error_code": error_code,
            "error_message": error_message,
            "error_description": strategy["description"],
            "suggestions": strategy["suggestions"],
            "retry_allowed": strategy["retry_allowed"],
            "context": context or {}
        }
        
        # Add specific advice based on context
        if context:
            if context.get("table"):
                recovery_plan["suggestions"].append(
                    f"جرب جدول آخر غير {context['table']}"
                )
            if context.get("query"):
                query_words = context["query"].split()
                if len(query_words) > 3:
                    recovery_plan["suggestions"].append(
                        f"استخدم كلمة واحدة مثل: {query_words[0]}"
                    )
        
        elapsed = (time.time() - start_time) * 1000
        
        logger.info(f"✅ ErrorRecovery: Suggested {len(recovery_plan['suggestions'])} actions")
        
        return ToolResult(
            success=True,
            data=recovery_plan,
            metadata={
                "error_analyzed": error_code,
                "retry_recommended": strategy["retry_allowed"]
            },
            execution_time_ms=elapsed
        )


class CheckpointTool(BaseTool):
    """
    أداة نقاط الحفظ
    
    Creates safety checkpoints during long thinking processes.
    Allows recovery from interruptions.
    """
    
    def __init__(self):
        super().__init__(
            name="checkpoint",
            description="إنشاء نقطة حفظ للاسترجاع عند الانقطاع"
        )
        self._checkpoints: Dict[str, Dict[str, Any]] = {}
    
    def run(
        self,
        action: str,  # "create", "restore", "list"
        checkpoint_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        label: Optional[str] = None
    ) -> ToolResult:
        """
        Manage checkpoints.
        
        Args:
            action: "create", "restore", or "list"
            checkpoint_id: ID for the checkpoint
            data: Data to save at checkpoint
            label: Human-readable label
            
        Returns:
            ToolResult with checkpoint info
        """
        self._track_usage()
        
        if action == "create":
            if not checkpoint_id:
                checkpoint_id = f"cp_{int(time.time())}"
            
            self._checkpoints[checkpoint_id] = {
                "data": data,
                "label": label,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"📌 Created checkpoint: {checkpoint_id}")
            
            return ToolResult(
                success=True,
                data={"checkpoint_id": checkpoint_id, "label": label},
                metadata={"action": "create"}
            )
            
        elif action == "restore":
            if checkpoint_id not in self._checkpoints:
                return ToolResult(
                    success=False,
                    error=f"نقطة حفظ غير موجودة: {checkpoint_id}",
                    metadata={"error_code": "CHECKPOINT_NOT_FOUND"}
                )
            
            checkpoint = self._checkpoints[checkpoint_id]
            logger.info(f"🔄 Restored checkpoint: {checkpoint_id}")
            
            return ToolResult(
                success=True,
                data=checkpoint,
                metadata={"action": "restore"}
            )
            
        elif action == "list":
            checkpoints_list = [
                {"id": cp_id, "label": cp["label"], "created_at": cp["created_at"]}
                for cp_id, cp in self._checkpoints.items()
            ]
            
            return ToolResult(
                success=True,
                data=checkpoints_list,
                metadata={"action": "list", "count": len(checkpoints_list)}
            )
        
        return ToolResult(
            success=False,
            error=f"إجراء غير معروف: {action}",
            metadata={"valid_actions": ["create", "restore", "list"]}
        )


__all__ = [
    "ContinueThinkingTool",
    "WaitTool",
    "ErrorRecoveryTool",
    "CheckpointTool",
    "ThinkingState"
]
