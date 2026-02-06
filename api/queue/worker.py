import asyncio
import logging
from typing import Dict, Any
from arq import create_pool
from arq.connections import RedisSettings as ArqRedisSettings
from api.queue.config import redis_settings, QUEUE_NAME
from agents.config.settings import settings
from api.services.chat_service import chat_service # We will refactor this to expose internal method

logger = logging.getLogger(__name__)

async def startup(ctx):
    logger.info("🚀 Worker starting up...")
    # Initialize any global connections if needed (DB, etc.)
    # chat_service should already be initialized globally in its module

async def shutdown(ctx):
    logger.info("👋 Worker shutting down...")

async def run_agent_task(ctx, session_id: str, message_text: str, user_context: Dict[str, Any], generate_title: bool):
    """
    The main worker function that runs the agent graph.
    This persists across server restarts (if queue is persistent).
    """
    logger.info(f"👷 processing task for session {session_id}")
    try:
        # We call the synchronous/internal version of process_message
        # We need to ensure chat_service.process_message_internal exists
        result = await chat_service.process_message_internal(
            session_id=session_id,
            message_text=message_text,
            user_context=user_context,
            generate_title=False # Title generation usually fast, can happen here
        )
        return result.dict()
    except Exception as e:
        logger.error(f"❌ Worker failed task {session_id}: {e}")
        # We could re-raise to let ARQ retry, but maybe we want to log failure to DB?
        raise

class WorkerSettings:
    functions = [run_agent_task]
    redis_settings = ArqRedisSettings(
        host=redis_settings.host,
        port=redis_settings.port,
        database=redis_settings.database
    )
    queue_name = QUEUE_NAME
    max_jobs = 10 # Concurrency
