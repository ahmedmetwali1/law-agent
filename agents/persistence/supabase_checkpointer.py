"""
Supabase Checkpointer for LangGraph
بديل لـ PostgresSaver يستخدم Supabase REST API بدلاً من psycopg

Why: Port 8000 (REST API) is OPEN, but Postgres ports (5432/6543) are CLOSED
Solution: Use existing Supabase infrastructure instead of direct Postgres
"""
import logging
from typing import Optional, Dict, Any, Sequence, Iterator
from datetime import datetime
import json

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)


class SupabaseCheckpointer(BaseCheckpointSaver):
    """
    LangGraph Checkpointer using Supabase REST API
    
    Stores checkpoints in 'langgraph_checkpoints' table via HTTP instead of Postgres
    """
    
    def __init__(self):
        """Initialize with Supabase client"""
        super().__init__()
        # Import here to avoid circular dependency
        from agents.config.database import get_supabase_client
        self.client = get_supabase_client()  # ← Call the function!
        self.table_name = "langgraph_checkpoints"
        logger.info("✅ SupabaseCheckpointer initialized (REST API)")
    
    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> RunnableConfig:
        """
        Save a checkpoint to Supabase
        
        Args:
            config: Runtime configuration with thread_id
            checkpoint: The checkpoint data to save
            metadata: Checkpoint metadata
            
        Returns:
            Updated config with checkpoint_id
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]
        
        # Serialize checkpoint data
        checkpoint_data = {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "parent_checkpoint_id": checkpoint.get("parent_id"),
            "checkpoint_data": json.dumps(checkpoint),
            "metadata": json.dumps(metadata),
            "created_at": datetime.now().isoformat()
        }
        
        try:
            # Upsert to Supabase (insert or update)
            self.client.table(self.table_name)\
                .upsert(checkpoint_data, on_conflict="thread_id,checkpoint_id")\
                .execute()
            
            logger.debug(f"💾 Saved checkpoint: {thread_id}/{checkpoint_id}")
            
            # Return config with checkpoint info
            return {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to save checkpoint: {e}")
            raise
    
    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """
        Retrieve latest checkpoint tuple for a thread (required by LangGraph)
        
        Args:
            config: Runtime configuration with thread_id
            
        Returns:
            CheckpointTuple or None
        """
        thread_id = config["configurable"]["thread_id"]
        
        try:
            # Get latest checkpoint for this thread
            response = self.client.table(self.table_name)\
                .select("*")\
                .eq("thread_id", thread_id)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if response.data:
                row = response.data[0]
                checkpoint = json.loads(row["checkpoint_data"])
                metadata = json.loads(row["metadata"])
                
                logger.debug(f"📂 Retrieved checkpoint: {thread_id}")
                
                # Return as CheckpointTuple
                return CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_id": row["checkpoint_id"]
                        }
                    },
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config=None
                )
            
            logger.debug(f"📭 No checkpoint found: {thread_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get checkpoint: {e}")
            return None
    
    def list(
        self,
        config: RunnableConfig,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """
        List checkpoints for a thread
        
        Args:
            config: Runtime configuration with thread_id
            filter: Optional filters
            before: Get checkpoints before this config
            limit: Maximum number of results
            
        Returns:
            Iterator of CheckpointTuple
        """
        thread_id = config["configurable"]["thread_id"]
        
        try:
            query = self.client.table(self.table_name)\
                .select("*")\
                .eq("thread_id", thread_id)\
                .order("created_at", desc=True)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            
            for row in response.data:
                checkpoint = json.loads(row["checkpoint_data"])
                metadata = json.loads(row["metadata"])
                
                yield CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_id": row["checkpoint_id"]
                        }
                    },
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config=None
                )
            
            logger.debug(f"📚 Listed checkpoints for {thread_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to list checkpoints: {e}")
            return
    
    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Async version of get_tuple"""
        return self.get_tuple(config)
    
    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> RunnableConfig:
        """Async version of put"""
        return self.put(config, checkpoint, metadata)
    
    async def alist(
        self,
        config: RunnableConfig,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """Async version of list"""
        return self.list(config, filter=filter, before=before, limit=limit)

