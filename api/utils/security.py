from fastapi import HTTPException, Header
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def validate_message_content(message: str) -> bool:
    """
    Validate message content for security and quality
    
    Returns:
        bool: True if valid, raises HTTPException if invalid
    """
    # Check if empty
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="رسالة فارغة")
    
    # Check length limits
    if len(message) > 10000:
        raise HTTPException(status_code=400, detail="الرسالة طويلة جداً (الحد الأقصى 10000 حرف)")
    
    if len(message.strip()) < 2:
        raise HTTPException(status_code=400, detail="الرسالة قصيرة جداً")
    
    # Basic XSS prevention (additional to react-markdown sanitization)
    dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
    message_lower = message.lower()
    
    for pattern in dangerous_patterns:
        if pattern in message_lower:
            logger.warning(f"Potential XSS attempt detected: {pattern}")
            raise HTTPException(status_code=400, detail="محتوى غير صالح")
    
    return True


def validate_lawyer_id(lawyer_id: Optional[str], authorization: Optional[str] = None) -> bool:
    """
    Validate that lawyer_id is provided and matches token
    
    Note: This is a basic check. For full security, decode JWT and verify.
    """
    if not lawyer_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")
    
    # TODO: Add JWT token validation here
    # For now, we trust that the backend auth middleware handles this
    
    return True


def validate_session_ownership(session_id: str, lawyer_id: str) -> bool:
    """
    Validate that the session belongs to the lawyer
    
    Note: This should be done via database query in the endpoint
    """
    # This is a placeholder - actual validation happens in endpoint
    return True
