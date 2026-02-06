from typing import Optional, Dict, Any
import logging
from datetime import datetime
from agents.config.database import get_supabase_client
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class UsageManager:
    """
    Centralized manager for AI Usage Tracking & Quota Enforcement.
    Prevents 'Free Infinite Loop' exploit.
    """
    
    def __init__(self):
        pass
        
    def _get_db(self):
        return get_supabase_client()
        
    async def track_usage(
        self, 
        lawyer_id: str, 
        request_type: str, 
        words_input: int,
        words_output: int,
        session_id: Optional[str] = None,
        model_name: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Record usage and increment subscription counter.
        """
        try:
            db = self._get_db()
            total_words = words_input + words_output
            
            # 1. Insert Log (db.md schema)
            log_data = {
                "lawyer_id": lawyer_id,
                "user_id": user_id or lawyer_id, # Fallback
                "request_type": request_type, # renamed from feature_type
                "words_input": words_input,
                "words_output": words_output,
                # "total_words": total_words, # REMOVED: Generated Column
                "session_id": session_id,
                "model_name": model_name,
                "provider": "openwebui" # Default or Dynamic
            }
            db.table("ai_usage_logs").insert(log_data).execute()
            
            # 2. Increment Subscription Counter (Atomic RPC call)
            # Use 'p_words' as defined in updated SQL
            db.rpc("increment_ai_usage", {
                "p_lawyer_id": lawyer_id, 
                "p_words": total_words
            }).execute()
            
            logger.info(f"📉 Tracked usage for {lawyer_id}: {total_words} words ({request_type})")
            
        except Exception as e:
            logger.error(f"❌ Failed to track usage: {e}")
            # Don't raise, let the user get their response, but alert admin needed in real sys
            
    async def check_limit(self, lawyer_id: str) -> bool:
        """
        Check if user has valid subscription and limits.
        Returns check boolean rather than raising exception for agent logic flow.
        """
        try:
            # Import inside method to avoid circular imports if any (though currently clean)
            from api.utils.subscription_enforcement import check_subscription_active
            
            # Use await since check_subscription_active is async
            await check_subscription_active(user_id=lawyer_id, require_ai=True)
            return True
            
        except HTTPException:
            # If 403 or other auth error, returns False
            return False
            
        except Exception as e:
            logger.error(f"⚠️ Usage Check Failed: {e}")
            # Fail safe: Block if check fails
            return False

usage_manager = UsageManager()
