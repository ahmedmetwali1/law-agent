"""
Event Streamer - المبث
مسؤول عن إرسال الأحداث للواجهة
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator, Dict, Any
from datetime import datetime
from .events import StepEvent, PlanEvent, ProgressEvent, EventType, StepStatus, create_sse_message

logger = logging.getLogger(__name__)


class EventStreamer:
    """Event Streamer - طبقة البث"""
    
    def __init__(self, plan_id: str, buffer_size: int = 100):
        self.plan_id = plan_id
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=buffer_size)
        self.active = True
        self.history: list = []
        self.start_time = datetime.now()
        logger.info(f"📡 EventStreamer initialized for plan: {plan_id}")
    
    async def emit(self, event: Any, event_name: str = "message"):
        """إرسال حدث للواجهة"""
        if not self.active:
            logger.warning(f"⚠️ Streamer for {self.plan_id} is not active")
            return
        
        try:
            await self.queue.put((event, event_name))
            self.history.append({"event": event, "event_name": event_name, "timestamp": datetime.now().isoformat()})
            logger.debug(f"📤 Event emitted: {event_name} for plan {self.plan_id}")
        except asyncio.QueueFull:
            logger.error(f"❌ Event queue full for plan {self.plan_id}")
    
    async def emit_step_update(self, step_id: int, status: str, message: str = "", **kwargs):
        """اختصار لإرسال تحديث خطوة"""
        status_enum = StepStatus(status) if isinstance(status, str) else status
        event = StepEvent(step_id=step_id, status=status_enum, message=message, **kwargs)
        await self.emit(event, event_name="step_update")
    
    async def emit_plan_event(self, event_type: str, payload: Dict[str, Any] = None):
        """اختصار لإرسال حدث خطة"""
        event_type_enum = EventType(event_type) if isinstance(event_type, str) else event_type
        event = PlanEvent(event_type=event_type_enum, plan_id=self.plan_id, payload=payload or {})
        await self.emit(event, event_name=event_type)
    
    async def emit_progress(self, total_steps: int, completed_steps: int, current_step: Optional[int] = None):
        """اختصار لإرسال تحديث التقدم"""
        percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        event = ProgressEvent(
            plan_id=self.plan_id,
            total_steps=total_steps,
            completed_steps=completed_steps,
            current_step=current_step,
            percentage=round(percentage, 2)
        )
        await self.emit(event, event_name="progress_update")
    
    async def stream(self) -> AsyncGenerator[str, None]:
        """Generator للـ SSE"""
        logger.info(f"🌊 Starting SSE stream for plan: {self.plan_id}")
        
        try:
            yield f"event: connected\ndata: {{\"plan_id\": \"{self.plan_id}\", \"status\": \"connected\"}}\n\n"
            
            while self.active:
                try:
                    event, event_name = await asyncio.wait_for(self.queue.get(), timeout=30.0)
                    sse_message = create_sse_message(event, event_name)
                    yield sse_message
                except asyncio.TimeoutError:
                    yield f": heartbeat\n\n"
        except asyncio.CancelledError:
            logger.info(f"🛑 Stream cancelled for plan: {self.plan_id}")
        except Exception as e:
            logger.error(f"❌ Stream error for plan {self.plan_id}: {e}")
        finally:
            logger.info(f"👋 Stream ended for plan: {self.plan_id}")
            self.active = False
    
    def close(self):
        """إغلاق الـ streamer"""
        self.active = False
        logger.info(f"🔒 Streamer closed for plan: {self.plan_id}")
    
    def get_history(self, limit: int = 50) -> list:
        """الحصول على تاريخ الأحداث"""
        return self.history[-limit:]


__all__ = ["EventStreamer"]
