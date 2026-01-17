from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict

# =============================================================================
# Authentication Models
# =============================================================================

class SignupRequest(BaseModel):
    """Request model for user signup"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    full_name: str = Field(..., min_length=2, description="Full name")
    phone: Optional[str] = None
    country_id: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    bio: Optional[str] = None


class LoginRequest(BaseModel):
    """Request model for user login"""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Response model for authentication"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserProfile(BaseModel):
    """User profile model"""
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    country_id: Optional[str] = None
    role_id: str
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    created_at: str


# =============================================================================
# Chat Models
# =============================================================================

class StreamChatRequest(BaseModel):
    """Request model for streaming chat"""
    message: str = Field(..., description="User message")
    history: Optional[List[Dict[str, str]]] = Field(default=[], description="Chat history")
    lawyer_id: Optional[str] = Field(None, description="Lawyer ID for context")
