import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from agents.config.database import get_supabase_client
from langchain_core.messages import BaseMessage, messages_to_dict, messages_from_dict

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Manages long-term memory for the Graph Agent using PostgreSQL/Supabase.
    Handles State Persistence, Case Summaries, and Atomic Updates.
    """
    def __init__(self):
        self.supabase = get_supabase_client()
        self.table_sessions = "ai_chat_sessions"
        self.table_messages = "ai_chat_messages"

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves session metadata and the last saved AgentState (checkpoint).
        """
        try:
            response = self.supabase.table(self.table_sessions)\
                .select("*")\
                .eq("id", session_id)\
                .single()\
                .execute()
            
            if not response.data:
                return None
            
            data = response.data
            return {
                "id": data['id'],
                "title": data.get('title'),
                "case_summary": data.get('case_summary'),
                "agent_state": data.get('agent_state'), # The checkpoint
                "status": data.get('current_action'),
                "created_at": data['created_at']
            }
        except Exception as e:
            logger.error(f"❌ Failed to get session {session_id}: {e}")
            return None

    async def save_step(self, session_id: str, state: Dict[str, Any], message: Any):
        """
        Atomically saves a new message and updates the agent's state checkpoint.
        """
        try:
            # 1. Prepare Message Record
            msg_content = message.content if hasattr(message, 'content') else str(message)
            msg_role = "assistant"
            if "HumanMessage" in str(type(message)): msg_role = "user"
            elif "ToolMessage" in str(type(message)): msg_role = "tool"
            
            # 2. Serialize State
            serialized_state = json.loads(json.dumps(state, default=str)) 

            # 3. Call Atomic RPC
            # Params: p_session_id, p_role, p_content, p_metadata, p_agent_state
            params = {
                "p_session_id": session_id,
                "p_role": msg_role,
                "p_content": msg_content,
                "p_metadata": message.metadata if hasattr(message, 'metadata') else {},
                "p_agent_state": serialized_state
            }
            
            response = self.supabase.rpc("atomic_step_transaction", params).execute()
            
            if response.data and response.data.get("success"):
                logger.debug(f"✅ Atomic save success for session {session_id}")
                return True
            else:
                logger.error(f"❌ Atomic save failed: {response.data}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to save step (Atomic RPC): {e}")
            return False

    async def update_summary(self, session_id: str, summary: str):
        """Updates the case summary"""
        try:
            self.supabase.table(self.table_sessions).update({
                "case_summary": summary
            }).eq("id", session_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to update summary: {e}")
            return False

# Global Instance
memory_manager = MemoryManager()
