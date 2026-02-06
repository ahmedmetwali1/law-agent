"""
Postgres Persistence Layer (Wrapper for Supabase)
طبقة المثابرة باستخدام Supabase REST
"""
import logging
from typing import List, Dict, Any, Optional

# New SupabaseSaver
from agents.persistence.supabase_saver import SupabaseSaver
from agents.config.settings import settings

logger = logging.getLogger(__name__)

class PostgresPersistence:
    """
    Persistence Manager (Refactored for Production)
    Wrapper around SupabaseSaver to maintain Singleton pattern and utility methods.
    """
    
    _instance: Optional['PostgresPersistence'] = None
    
    def __init__(self):
        self._saver: Any = None
        self.is_postgres_available = False # Deprecated flag, kept for compat
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self):
        """Initialize with SupabaseSaver"""
        if self._saver is not None:
            return

        logger.info("🔌 Initializing Persistence Layer (Production Mode)...")
        
        # ✅ Production Fix: Use SupabaseSaver
        self._saver = SupabaseSaver()
        logger.info("✅ Supabase Checkpointer initialized (State persists in DB)")

            
    async def close(self):
        """No connection pool to close in REST mode"""
        pass
            
    @property
    def checkpointer(self) -> Any:
        """Get the LangGraph Checkpointer"""
        if self._saver is None:
            self.initialize()
        return self._saver

    async def get_session_history(self, session_id: str, window_size: int = 30) -> List[Dict[str, Any]]:
        """
        Retrieve session history using SupabaseSaver
        """
        config = {"configurable": {"thread_id": session_id}}
        
        # Use aget from checkpointer
        checkpoint = await self.checkpointer.aget(config)
        
        if not checkpoint:
            return []
            
        # Extract state
        # SupabaseSaver returns standardized CheckpointTuple
        state = checkpoint.get("channel_values", {})
        messages = state.get("messages", [])
        
        if not messages:
            return []
            
        # Apply Windowing
        if len(messages) > window_size:
            return messages[-window_size:]
        
        return messages

    async def fetch_archived_messages(
        self, 
        session_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetch older messages from the archive.
        Delegates to get_session_history with manual slicing for now.
        For true pagination, we might query DB directly in the future.
        """
        all_messages = await self.get_session_history(session_id, window_size=1000)
        
        total = len(all_messages)
        if total <= offset:
            return []
            
        # Calculate slice (reverse order usually desired for chat UI pagination)
        end = total - offset
        start = max(0, end - limit)
        
        return all_messages[start:end]

# Global instance
persistence = PostgresPersistence.get_instance()
