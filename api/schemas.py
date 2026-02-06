from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class ChatRequest(BaseModel):
    message: str
    office_id: Optional[str] = None # Legacy support
    session_id: Optional[str] = None # For start requests

class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: str
    content: str
    created_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class ChatSessionBase(BaseModel):
    title: str
    session_type: str = "main"

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSession(ChatSessionBase):
    id: str
    lawyer_id: str
    created_at: str
    updated_at: str
    last_message_at: Optional[str] = None
    is_pinned: bool = False
    message_count: int = 0
    current_action: Optional[str] = None
    messages: Optional[List[ChatMessage]] = []

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    session_id: str
    message: str
    stage: Optional[str] = "active"
    completed: bool = False
    case_data: Optional[Dict[str, Any]] = None
    case_id: Optional[str] = None
    
    # Extended fields
    user_message: Optional[ChatMessage] = None
    ai_message: Optional[ChatMessage] = None
    suggested_title: Optional[str] = None

from enum import Enum

class EventType(str, Enum):
    THOUGHT = "thought"
    EXECUTION = "execution"
    FINAL_ANSWER = "final_answer"
    ERROR = "error"
    STATUS_UPDATE = "status_update"

class AgentEvent(BaseModel):
    """
    Standardized event schema for real-time agent perception.
    """
    type: EventType
    content: str
    step: int = 0
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
