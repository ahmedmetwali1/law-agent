"""
Persistent Memory System for Agent
نظام الذاكرة الدائمة للوكيل

Stores permanent facts about the lawyer that don't change across sessions.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PersistentMemory:
    """
    Permanent memory that persists across all sessions
    الذاكرة الدائمة التي تستمر عبر جميع الجلسات
    """
    
    def __init__(self, lawyer_id: str, lawyer_data: Dict[str, Any] = None):
        """
        Initialize persistent memory with lawyer data
        
        Args:
            lawyer_id: Unique lawyer identifier
            lawyer_data: Initial lawyer profile data
        """
        self.lawyer_id = lawyer_id
        
        # Core identity (never changes)
        self.lawyer_name = lawyer_data.get("full_name", "المحامي") if lawyer_data else "المحامي"
        self.email = lawyer_data.get("email") if lawyer_data else None
        self.phone = lawyer_data.get("phone") if lawyer_data else None
        self.role = lawyer_data.get("role", "محامي") if lawyer_data else "محامي"
        
        # Preferences (can be updated)
        self.preferences = {
            "greeting_style": "warm",  # warm, formal, casual
            "communication_style": "honest",  # honest, diplomatic, direct
            "language": "ar",  # ar, en
        }
        
        # Statistics (tracked over time)
        self.stats = {
            "total_sessions": 0,
            "total_clients": 0,
            "total_hearings": 0,
            "favorite_queries": []
        }
        
        logger.info(f"🧠 Persistent memory initialized for {self.lawyer_name}")
    
    def get_greeting(self) -> str:
        """Get personalized greeting"""
        if self.preferences["greeting_style"] == "warm":
            return f"مرحباً أستاذ {self.lawyer_name}! 😊 سعيد بلقائك!"
        elif self.preferences["greeting_style"] == "formal":
            return f"السلام عليكم أستاذ {self.lawyer_name}"
        else:
            return f"أهلاً {self.lawyer_name}!"
    
    def get_identity_response(self) -> str:
        """Get response about who the user is"""
        return f"""بالتأكيد! أنت الأستاذ **{self.lawyer_name}**، محامي محترف.
        
أنا مدير مكتبك الشخصي، أعرفك جيداً:
📧 بريدك: {self.email or 'غير مسجل'}
📞 هاتفك: {self.phone or 'غير مسجل'}

أنا هنا لمساعدتك في كل شيء يخص مكتبك. 💪"""
    
    def to_context(self) -> str:
        """Convert to context string for LLM"""
        context = f"""
=== معلومات دائمة عن المحامي ===
الاسم: {self.lawyer_name}
المعرف: {self.lawyer_id}
البريد: {self.email or 'غير متوفر'}
الهاتف: {self.phone or 'غير متوفر'}
الدور: {self.role}

أسلوب التواصل المفضل: {self.preferences['communication_style']}
- كن صريحاً وصادقاً
- لا تجامل
- قل الحقيقة دائماً
- أنت الصديق الأمين والناصح
"""
        return context.strip()
    
    def update_stats(self, stat_name: str, increment: int = 1):
        """Update statistics"""
        if stat_name in self.stats:
            self.stats[stat_name] += increment
            logger.info(f"📊 Updated {stat_name}: {self.stats[stat_name]}")


# Global persistent memories (keyed by lawyer_id)
_persistent_memories: Dict[str, PersistentMemory] = {}


def get_or_create_persistent_memory(lawyer_id: str, lawyer_data: Dict[str, Any] = None) -> PersistentMemory:
    """
    Get existing or create new persistent memory
    
    Args:
        lawyer_id: Lawyer's unique ID
        lawyer_data: Lawyer profile data
        
    Returns:
        PersistentMemory instance
    """
    if lawyer_id not in _persistent_memories:
        _persistent_memories[lawyer_id] = PersistentMemory(lawyer_id, lawyer_data)
        logger.info(f"🧠 Created new persistent memory for {lawyer_id}")
    
    return _persistent_memories[lawyer_id]


__all__ = ["PersistentMemory", "get_or_create_persistent_memory"]
