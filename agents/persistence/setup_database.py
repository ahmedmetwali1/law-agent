"""
Database Setup Script
إعداد قاعدة البيانات للمثابرة (Persistence)
"""
import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from agents.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_database():
    """Create necessary tables for LangGraph checkpointing"""
    try:
        import psycopg
        from psycopg import AsyncConnection
    except ImportError:
        logger.error("❌ psycopg is not installed. Please install it: pip install psycopg[binary]")
        return

    db_url = settings.database_url
    logger.info(f"🔌 Connecting to database...")
    
    # DDL Statements for LangGraph Checkpointer
    # Based on standard langgraph-checkpoint-postgres schema
    DDL_STATEMENTS = [
        """
        CREATE TABLE IF NOT EXISTS checkpoints (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            checkpoint_id TEXT NOT NULL,
            parent_checkpoint_id TEXT,
            type TEXT,
            checkpoint BYTEA,
            metadata BYTEA,
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS checkpoint_blobs (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            channel TEXT NOT NULL,
            version TEXT NOT NULL,
            type TEXT,
            blob BYTEA,
            PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS checkpoint_writes (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            checkpoint_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            idx INTEGER NOT NULL,
            channel TEXT NOT NULL,
            type TEXT,
            blob BYTEA,
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
        );
        """
    ]

    try:
        async with await AsyncConnection.connect(db_url) as aconn:
            async with aconn.cursor() as acur:
                for statement in DDL_STATEMENTS:
                    await acur.execute(statement)
                    logger.info("✅ Executed DDL statement")
                
                await aconn.commit()
                logger.info("🎉 Database setup completed successfully!")
                
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(setup_database())
