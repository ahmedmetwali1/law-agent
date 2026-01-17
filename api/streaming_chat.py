"""
Streaming Chat Endpoint
للاتصال بـ AINexus Frontend
"""

import json
import asyncio
import logging
from typing import AsyncGenerator, List, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

class StreamChatRequest(BaseModel):
    """Request model for streaming chat"""
    message: str = Field(..., description="User message")
    history: Optional[List[Dict[str, str]]] = Field(default=[], description="Chat history")
    lawyer_id: Optional[str] = Field(None, description="Lawyer ID for context")



async def generate_ai_response(message: str, history: List[Dict], lawyer_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Generator function for streaming AI responses with Thinking Steps
    يولد استجابات الذكاء الاصطناعي بشكل متدفق مع خطوات التفكير
    """
    from starlette.concurrency import run_in_threadpool
    from agents.core.enhanced_general_lawyer_agent import EnhancedGeneralLawyerAgent
    # Removed GeneralLawyerAgent import
    from agents.storage.user_storage import user_storage

    # Queue for inter-thread communication
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def on_thought(thought_msg: str):
        """Callback from agent running in threadpool"""
        # Safely put into queue from background thread
        loop.call_soon_threadsafe(queue.put_nowait, {"type": "thought", "content": thought_msg})

    async def run_agent_task():
        """Run blocking agent code in threadpool"""
        try:
            agent = None
            
            # Determine User Context (Lawyer vs Assistant)
            active_user_id = lawyer_id 
            
            if active_user_id:
                # 1. Get the current user details
                current_user = user_storage.get_user_by_id(active_user_id)
                
                if current_user:
                    current_user.pop("password_hash", None)
                    
                    # 2. Determine who the "Office Owner" (Lawyer) is
                    if current_user.get("office_id"):
                        # This is an ASSISTANT
                        target_lawyer_id = current_user.get("office_id")
                        agent = EnhancedGeneralLawyerAgent(
                            lawyer_id=target_lawyer_id,
                            lawyer_name=None, 
                            current_user=current_user
                        )
                    else:
                        # This is the LAWYER
                        target_lawyer_id = active_user_id
                        agent = EnhancedGeneralLawyerAgent(
                            lawyer_id=target_lawyer_id,
                            lawyer_name=None,
                            current_user=current_user
                        )
                else:
                     # Fallback
                     from api.main import general_agent 
                     agent = general_agent
            else:
                from api.main import general_agent 
                agent = general_agent
            
            logger.info(f"🤖 Processing message with streaming thoughts: {message[:50]}...")
            
            # Execute blocking call
            # We use process_user_message which we modified to accept on_thought
            if hasattr(agent, 'process_user_message'):
                response = await run_in_threadpool(
                    agent.process_user_message, 
                    message, 
                    on_thought=on_thought
                )
            else:
                 # Fallback for old agents
                 response = await run_in_threadpool(agent.process_message, message)
            
            # Put final result
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "result", "data": response})
            
        except Exception as e:
            logger.error(f"❌ Error in agent task: {e}")
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "error", "content": str(e)})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None) # Sentinel

    # Start background task
    asyncio.create_task(run_agent_task())

    # Consumer Loop
    while True:
        item = await queue.get()
        
        if item is None:
            break
            
        msg_type = item.get("type")
        
        if msg_type == "thought":
            # Send thought event
            yield f"data: {json.dumps(item)}\n\n"
            
        elif msg_type == "error":
             yield f"data: {json.dumps(item)}\n\n"
             
        elif msg_type == "result":
            response = item["data"]
            # Simulate streaming typewriting for the final text
            if isinstance(response, dict):
                text_content = response.get("response", response.get("message", ""))
                task_json = response.get("task") or response.get("action")
            else:
                text_content = str(response)
                task_json = None

            # Stream text chars
            if text_content:
                chunk_size = 5 # Group chars to reduce overhead
                for i in range(0, len(text_content), chunk_size):
                    chunk = text_content[i:i+chunk_size]
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.01)
            
            # Send task JSON if exists
            if task_json:
                yield f"data: {json.dumps({'type': 'task_json', 'task': task_json})}\n\n"

    # Done
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


