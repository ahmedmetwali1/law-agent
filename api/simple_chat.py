"""
Simple Chat Endpoint (Non-Streaming)
استقبال الرسالة كاملة ثم عرضها بث مباشر على Frontend
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class SimpleChatRequest(BaseModel):
    """Request model for simple chat"""
    message: str = Field(..., description="User message")
    history: Optional[List[Dict[str, str]]] = Field(default=[], description="Chat history")
    lawyer_id: Optional[str] = Field(None, description="Lawyer ID for context")


class SimpleChatResponse(BaseModel):
    """Response model for simple chat"""
    message: str
    task_json: Optional[Dict] = None
