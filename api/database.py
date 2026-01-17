"""
Centralized Supabase Client
نقطة واحدة للتحكم في اتصال قاعدة البيانات
"""
import os
from supabase import create_client, Client
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global singleton instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client singleton
    
    Returns:
        Client: Supabase client instance
        
    Raises:
        ValueError: If Supabase credentials are not configured
    """
    global _supabase_client
    
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found in environment variables")
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required"
            )
        
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client initialized successfully")
    
    return _supabase_client


def reset_supabase_client():
    """
    Reset the Supabase client singleton (useful for testing)
    """
    global _supabase_client
    _supabase_client = None
    logger.info("Supabase client reset")
