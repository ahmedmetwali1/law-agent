"""
Progress Streamer
بث تقدم التنفيذ للمستخدم
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ProgressUpdate:
    """Represents a progress update"""
    
    def __init__(self, status: str, message: str, step: Optional[int] = None, 
                 total: Optional[int] = None, data: Optional[Any] = None):
        self.timestamp = datetime.now()
        self.status = status  # 'running', 'success', 'error', 'completed', 'failed'
        self.message = message
        self.step = step
        self.total = total
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'message': self.message,
            'step': self.step,
            'total': self.total,
            'progress': self.step / self.total if (self.step and self.total) else None,
            'data': self.data
        }


class ProgressStreamer:
    """Streams progress updates to user"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id
        self.updates: List[ProgressUpdate] = []
    
    def update(self, status: str, message: str, step: Optional[int] = None,
               total: Optional[int] = None, data: Optional[Any] = None):
        """
        Send progress update
        
        Args:
            status: Update status ('running', 'success', 'error', etc.)
            message: User-friendly message in Arabic
            step: Current step number (1-indexed)
            total: Total number of steps
            data: Additional data (tool result, etc.)
        """
        
        update = ProgressUpdate(status, message, step, total, data)
        self.updates.append(update)
        
        # Log update
        progress_pct = f" ({update.step}/{update.total})" if update.step and update.total else ""
        logger.info(f"📡 {status.upper()}{progress_pct}: {message}")
        
        # TODO: Send via WebSocket or SSE when available
        # For now, just store in memory
    
    def get_all_updates(self) -> List[Dict[str, Any]]:
        """Get all updates as dictionaries"""
        return [update.to_dict() for update in self.updates]
    
    def get_latest_update(self) -> Optional[Dict[str, Any]]:
        """Get latest update"""
        if self.updates:
            return self.updates[-1].to_dict()
        return None
    
    def clear(self):
        """Clear all updates"""
        self.updates.clear()
    
    def format_summary(self) -> str:
        """Format a summary of all updates in Arabic"""
        
        if not self.updates:
            return ""
        
        summary = []
        
        for update in self.updates:
            if update.status == 'success':
                summary.append(f"✅ {update.message}")
            elif update.status == 'error':
                summary.append(f"❌ {update.message}")
            elif update.status == 'completed':
                summary.append(f"\n🎉 {update.message}")
        
        return "\n".join(summary)


__all__ = ['ProgressStreamer', 'ProgressUpdate']
