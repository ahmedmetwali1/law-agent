"""
SSE Streaming Endpoint (نقطة البث المباشر)
Real-time updates for legal research pipeline

Endpoints:
- POST /api/ai/stream - Start streaming legal research
- GET /api/ai/stream/{session_id} - Connect to existing stream
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.streaming import stream_manager, EventStreamer
from agents.core.multi_agent_orchestrator import MultiAgentOrchestrator
from api.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["streaming"])


class StreamingChatRequest(BaseModel):
    """طلب بث الدردشة"""
    message: str
    session_id: str
    country_id: Optional[str] = None
    case_id: Optional[str] = None


@router.post("/stream")
async def start_streaming_research(
    request: StreamingChatRequest,
    user: dict = Depends(get_current_user)
):
    """
    بدء بحث قانوني مع بث مباشر للتحديثات
    
    Returns:
        StreamingResponse with SSE events
    """
    session_id = request.session_id
    
    # Create or get streamer for this session
    streamer = stream_manager.register(session_id)
    
    # Start orchestrator in background
    async def run_orchestrator():
        try:
            # Initialize orchestrator with event streamer
            orchestrator = MultiAgentOrchestrator()
            orchestrator.event_streamer = streamer  # Inject streamer
            
            # Send initial event
            await streamer.emit_step_update(
                step_id=0,
                status="pending",
                message="بدأت معالجة طلبك..."
            )
            
            # Run the full pipeline
            result = await orchestrator.run(
                query=request.message,
                session_id=session_id,
                country_id=request.country_id,
                case_id=request.case_id,
                user_context={"lawyer_id": user.get("id")}
            )
            
            # Send completion event
            await streamer.emit_plan_event(
                event_type="completed",
                payload={
                    "message": result.get("memo", "انتهى البحث"),
                    "worksheet_id": result.get("worksheet_id"),
                    "confidence_score": result.get("confidence_score", 0.85)
                }
            )
            
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            await streamer.emit_plan_event(
                event_type="error",
                payload={"error": str(e), "recoverable": False}
            )
        finally:
            stream_manager.unregister(session_id)
    
    # Start background task
    asyncio.create_task(run_orchestrator())
    
    # Return streaming response
    return StreamingResponse(
        streamer.stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/stream/{session_id}")
async def connect_to_stream(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """
    الاتصال بقناة بث موجودة
    
    يُستخدم لإعادة الاتصال بجلسة قائمة
    """
    streamer = stream_manager.get(session_id)
    
    if not streamer:
        raise HTTPException(
            status_code=404,
            detail="Stream not found or already closed"
        )
    
    return StreamingResponse(
        streamer.stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.delete("/stream/{session_id}")
async def close_stream(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """إغلاق قناة البث"""
    stream_manager.unregister(session_id)
    return {"status": "closed", "session_id": session_id}
