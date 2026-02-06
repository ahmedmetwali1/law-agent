"""
Supabase Checkpoint Saver for LangGraph
مُحفظ الحالة باستخدام Supabase
"""
import asyncio
import json
from typing import Any, Dict, Iterator, Optional, Sequence, Tuple, AsyncIterator, List

import logging
from langchain_core.runnables import RunnableConfig
from langchain_core.load import dumpd, load
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
from agents.config.database import get_supabase_client

logger = logging.getLogger(__name__)

class SupabaseSaver(BaseCheckpointSaver):
    """
    سافير مخصص لحفظ حالة LangGraph في جدول Supabase
    Custom CheckpointSaver that uses Supabase (REST API).
    Uses standard langchain_core.load.dumpd for correct JSON serialization.
    """
    
    def __init__(self, client=None):
        super().__init__()
        self.client = client or get_supabase_client()
        self.table_name = "checkpoints"
        self.writes_table = "checkpoint_writes"
        
        # --- Throttling State ---
        self._last_save_time = 0
        self._save_interval = 4.0 # Seconds (User requested throttling)

    def _sanitize_json(self, obj: Any) -> Any:
        """Helper to sanitize JSON before loading with LangChain"""
        if isinstance(obj, dict):
            # Check for LangChain 'not_implemented' datetime struct
            if obj.get("type") == "not_implemented" and obj.get("id") == ["datetime", "datetime"]:
                # Extract repr or just return placeholder
                repr_str = obj.get("repr", "")
                # Try to extract ISO string if possible
                import re
                # Match datetime.datetime(Y, M, D, h, m, s, us) or (Y, M, D, h, m) etc
                # Example: datetime.datetime(2026, 1, 25, 16, 9, 28, 797808)
                m = re.search(r"datetime\.datetime\((\d+),\s*(\d+),\s*(\d+)(?:,\s*(\d+))?(?:,\s*(\d+))?(?:,\s*(\d+))?(?:,\s*(\d+))?", repr_str)
                if m:
                    try:
                        from datetime import datetime
                        groups = [int(g) for g in m.groups() if g is not None]
                        dt = datetime(*groups)
                        return dt.isoformat()
                    except Exception:
                        pass
                return repr_str
            return {k: self._sanitize_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_json(v) for v in obj]
        return obj

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Retrieve a checkpoint tuple from the database."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")

        try:
            query = self.client.table(self.table_name).select("*").eq("thread_id", thread_id)
            
            if checkpoint_id:
                query = query.eq("checkpoint_id", checkpoint_id)
            else:
                query = query.order("created_at", desc=True).limit(1)

            response = query.execute()

            if not response.data:
                return None

            row = response.data[0]
            
            # Rehydrate using langchain_core.load.load
            # Supabase returns dicts directly from JSONB columns
            # sanitize first to handle 'not_implemented' datetimes
            checkpoint_data = self._sanitize_json(row["checkpoint"])
            metadata_data = self._sanitize_json(row["metadata"])
            
            checkpoint = load(checkpoint_data)
            metadata = load(metadata_data)
            
            parent_id = row.get("parent_checkpoint_id")

            return CheckpointTuple(
                config=config,
                checkpoint=checkpoint, 
                metadata=metadata,
                parent_config={"configurable": {"thread_id": thread_id, "checkpoint_id": parent_id}} if parent_id else None
            )

        except Exception as e:
            logger.error(f"❌ Error fetching checkpoint: {e}", exc_info=True)
            return None

    def list(self, config: Optional[RunnableConfig], *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> Iterator[CheckpointTuple]:
        """List checkpoints."""
        thread_id = config["configurable"]["thread_id"]
        query = self.client.table(self.table_name).select("*").eq("thread_id", thread_id).order("created_at", desc=True)
        
        if limit:
            query = query.limit(limit)
            
        response = query.execute()
        
        for row in response.data:
            try:
                checkpoint = load(row["checkpoint"])
                metadata = load(row["metadata"])
                parent_id = row.get("parent_checkpoint_id")
                
                yield CheckpointTuple(
                    config={"configurable": {"thread_id": thread_id, "checkpoint_id": row["checkpoint_id"]}},
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config={"configurable": {"thread_id": thread_id, "checkpoint_id": parent_id}} if parent_id else None
                )
            except Exception:
                continue

    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: Dict[str, Any]) -> RunnableConfig:
        """Save a checkpoint to the database."""
        thread_id = config["configurable"]["thread_id"]
        parent_id = config["configurable"].get("checkpoint_id")
        checkpoint_id = checkpoint["id"]

        try:
            # Serialize using langchain_core.load.dumpd (returns dict)
            # This is what Supabase client expects for JSONB columns
            checkpoint_json = dumpd(checkpoint)
            metadata_json = dumpd(metadata)

            data = {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
                "parent_checkpoint_id": parent_id,
                "checkpoint": checkpoint_json,
                "metadata": metadata_json,
            }

            self.client.table(self.table_name).upsert(data).execute()
        except Exception as e:
            logger.error(f"❌ Error saving checkpoint: {e}", exc_info=True)
            
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(self, config: RunnableConfig, writes: Sequence[Tuple[str, Any]], task_id: str) -> None:
        """Save intermediate writes."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")
        
        if not checkpoint_id:
            return

        rows = []
        for idx, (channel, value) in enumerate(writes):
            try:
                # Serialize value
                value_json = dumpd(value)
                
                rows.append({
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id,
                    "task_id": task_id,
                    "idx": idx,
                    "channel": channel,
                    "type": type(value).__name__,
                    "value": value_json
                })
            except Exception as e:
                logger.warning(f"Failed to serialize write {channel}: {e}")

        if rows:
            try:
                self.client.table(self.writes_table).upsert(rows, ignore_duplicates=True).execute()
            except Exception as e:
                logger.error(f"❌ Error saving writes: {e}")

    # --- Async Implementations ---

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Async retrieve a checkpoint tuple from the database."""
        return await asyncio.to_thread(self.get_tuple, config)

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Dict[str, Any],
    ) -> RunnableConfig:
        """Async save a checkpoint to the database (Throttled)."""
        # Throttle check
        import time
        now = time.time()
        # Always save if it's the first step or explicitly forced (not handled here yet)
        # We allow skipping intermediate steps if they are too fast.
        # But LangGraph might rely on this for "next".
        # However, for pure logging/history, skipping is fine.
        # Critical: If we skip, 'checkpoint_id' is not stored. 
        # But put returns config with checkpoint_id.
        # If we return a config with ID that IS NOT in DB, subsequent steps might fail IF they try to load it.
        # LangGraph passes the checkpoint value in memory.
        # Persistence is for *resuming* or *history*.
        # So skipping writes is generally generic "unsafe" but "performant".
        
        # Strategy: Save only if > interval 
        if (now - self._last_save_time) < self._save_interval:
             # Skip write, but return config as if saved
             return {
                "configurable": {
                    "thread_id": config["configurable"]["thread_id"],
                    "checkpoint_id": checkpoint["id"],
                }
            }
            
        self._last_save_time = now
        return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """Async list checkpoints."""
        iterator = await asyncio.to_thread(self.list, config, filter=filter, before=before, limit=limit)
        for item in iterator:
            yield item

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Async save intermediate writes."""
        await asyncio.to_thread(self.put_writes, config, writes, task_id)
