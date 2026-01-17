"""
Stream Manager - إدارة مركزية لجميع الـ streamers
"""

import logging
from typing import Dict, Optional
from .streamer import EventStreamer

logger = logging.getLogger(__name__)


class StreamManager:
    """Stream Manager - مدير الـ Streamers (Singleton)"""
    
    _instance: Optional['StreamManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.streamers: Dict[str, EventStreamer] = {}
        self._initialized = True
        logger.info("🎛️ StreamManager initialized")
    
    def register(self, plan_id: str, buffer_size: int = 100) -> EventStreamer:
        """تسجيل streamer جديد"""
        if plan_id in self.streamers:
            logger.warning(f"⚠️ Streamer already exists for plan: {plan_id}")
            return self.streamers[plan_id]
        
        streamer = EventStreamer(plan_id, buffer_size)
        self.streamers[plan_id] = streamer
        logger.info(f"✅ Streamer registered for plan: {plan_id}")
        return streamer
    
    def get(self, plan_id: str) -> Optional[EventStreamer]:
        """الحصول على streamer"""
        return self.streamers.get(plan_id)
    
    def unregister(self, plan_id: str):
        """إلغاء تسجيل streamer"""
        if plan_id in self.streamers:
            streamer = self.streamers[plan_id]
            streamer.close()
            del self.streamers[plan_id]
            logger.info(f"🗑️ Streamer unregistered for plan: {plan_id}")
    
    def cleanup_inactive(self):
        """تنظيف الـ streamers غير النشطة"""
        inactive = [plan_id for plan_id, streamer in self.streamers.items() if not streamer.active]
        for plan_id in inactive:
            self.unregister(plan_id)
        if inactive:
            logger.info(f"🧹 Cleaned up {len(inactive)} inactive streamers")
    
    def get_active_count(self) -> int:
        """عدد الـ streamers النشطة"""
        return sum(1 for s in self.streamers.values() if s.active)
    
    def get_all_plan_ids(self) -> list:
        """قائمة معرفات جميع الخطط النشطة"""
        return list(self.streamers.keys())


# Singleton instance
stream_manager = StreamManager()

__all__ = ["StreamManager", "stream_manager"]
