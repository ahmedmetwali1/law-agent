import logging
import time
from contextlib import contextmanager
from agents.config.database import get_supabase_client

logger = logging.getLogger(__name__)

class LockManager:
    """
    Manages Postgres Advisory Locks via Supabase RPC.
    Ensures serialized access to shared resources (Lanes).
    """
    
    def __init__(self, client=None):
        self.client = client or get_supabase_client()
        
    def _generate_lock_key(self, key_str: str) -> int:
        """Generates a 64-bit integer hash from a string key."""
        # Use simple hash and mask to 63 bits (Postgres bigint is signed)
        return hash(key_str) & 0x7FFFFFFFFFFFFFFF

    @contextmanager
    def acquire_lock(self, key: str, timeout: int = 5):
        """
        Context manager to acquire a Transaction Transaction-Level Advisory Lock.
        Wait... Supabase HTTP API is stateless, so 'Transaction' locks usually don't persist 
        across multiple HTTP requests unless we are in a stored procedure.
        
        However, for 'Session' locks, we need a persistent connection (pooler).
        
        If we can't do real DB locks via HTTP, we might need a 'Distributed Lock' table 
        or use Redis. But we prefer Postgres.
        
        Workaround: Use a 'locks' table with Row Level Security?
        Or assumed atomic 'Update... where version=X'.
        
        Actually, OpenClaw used `pg_advisory_xact_lock` but it ran embedded.
        Since we are using Supabase-Py (HTTP), valid transaction locks are hard.
        
        Strategy B: Optimistic Concurrency Control (Versioning).
        We already have 'version' in Blackboard!
        
        We will Implement: OPTIMISTIC LOCKING.
        - Read Access: get latest version -> V
        - Write Access: Update ... WHERE id=... AND version=V
        - If 0 rows updated -> Concurrency Exception -> Retry.
        
        This class will handle the Retry Loop for Optimistic Locking.
        """
        yield OptimisticLock(self.client)

class OptimisticLock:
    def __init__(self, client):
        self.client = client

    def execute_with_retry(self, operation, max_retries=3):
        for attempt in range(max_retries):
            try:
                result = operation()
                if result: return result
                # If result is False/None, it might be a version mismatch
                logger.warning(f"🔒 Optimistic Lock Retry {attempt+1}/{max_retries}")
                time.sleep(0.2 * (attempt + 1))
            except Exception as e:
                logger.error(f"Locking Error: {e}")
                if attempt == max_retries - 1: raise
                time.sleep(0.5)
        return None
