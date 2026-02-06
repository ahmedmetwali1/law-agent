"""
Intent Classification Utilities
أدوات تصنيف النوايا

Extracted from api/ai_helper.py during cleanup operation.
This module provides functions to detect whether a user query is a legal question
that requires deep research or an administrative task requiring direct execution.
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def detect_legal_query(message: str) -> bool:
    """
    كشف ما إذا كان السؤال قانونياً يحتاج بحث متعمق
    
    Legal Query = يحتاج بحث في قاعدة المعرفة القانونية
    Administrative Query = تنفيذ مباشر (إضافة عميل، جلسة، إلخ)
    
    Args:
        message: رسالة المستخدم
        
    Returns:
        True إذا كان سؤال قانوني، False إذا كان مهمة إدارية
    
    Examples:
        >>> detect_legal_query("ابحث عن قانون العمل السعودي")
        True
        >>> detect_legal_query("أضف عميل جديد")
        False
    """
    message_lower = message.lower()
    
    # كلمات تدل على سؤال قانوني
    legal_keywords = [
        # بحث
        "ابحث", "بحث", "ابحث عن", "ابحث لي",
        # قانون ومواد
        "قانون", "مادة", "نص قانوني", "المادة", "مواد",
        # أحكام وسوابق
        "حكم", "سابقة", "اجتهاد", "قاضي", "محكمة", "أحكام",
        # استفسارات قانونية
        "ما حكم", "هل يجوز", "ما القانون", "ما هي المادة",
        "ثغرة", "دفع", "دفاع", "استئناف", "طعن", "نقض",
        # تحليل
        "تحليل قانوني", "رأي قانوني", "استشارة قانونية"
    ]
    
    # كلمات تدل على مهمة إدارية (لا تحتاج بحث)
    admin_keywords = [
        "أضف", "إضافة", "تعديل", "حذف", "عرض", "قائمة",
        "عميل جديد", "قضية جديدة", "جلسة جديدة", "موعد",
        "تذكير", "مهمة", "فاتورة", "دفعة"
    ]
    
    # Check for admin first (takes priority)
    for kw in admin_keywords:
        if kw in message_lower:
            logger.debug(f"Admin keyword detected: {kw}")
            return False
    
    # Check for legal keywords
    for kw in legal_keywords:
        if kw in message_lower:
            logger.info(f"✅ Legal keyword detected: {kw}")
            return True
    
    # Default: not a legal query
    return False


def classify_intent(message: str) -> Dict[str, any]:
    """
    تصنيف شامل للنية مع تفاصيل
    
    Args:
        message: رسالة المستخدم
        
    Returns:
        Dictionary containing:
        - type: "legal" | "administrative" | "general"
        - confidence: float (0.0-1.0)
        - is_legal: bool
        - detected_keywords: List[str] (keywords that matched)
    
    Examples:
        >>> classify_intent("ابحث عن قانون العمل")
        {'type': 'legal', 'confidence': 0.8, 'is_legal': True, 'detected_keywords': ['ابحث', 'قانون']}
    """
    is_legal = detect_legal_query(message)
    
    # TODO: Enhance with ML model for better confidence scoring
    # TODO: Extract and return matched keywords for debugging
    
    return {
        "type": "legal" if is_legal else "administrative",
        "confidence": 0.8,
        "is_legal": is_legal,
        "detected_keywords": []  # TODO: implement keyword extraction
    }


def is_multi_step_request(message: str) -> bool:
    """
    كشف ما إذا كان الطلب يحتاج خطوات متعددة
    
    Args:
        message: رسالة المستخدم
        
    Returns:
        True إذا كان طلب متعدد الخطوات
        
    Examples:
        >>> is_multi_step_request("أضف عميل جديد وأنشئ له قضية")
        True
        >>> is_multi_step_request("أضف عميل جديد")
        False
    """
    message_lower = message.lower()
    
    # Indicators of multi-step requests
    multi_step_indicators = [
        " ثم ", " و ", " بعد ذلك ", " أيضا ",
        "وأنشئ", "وأضف", "وعدل", "واحذف"
    ]
    
    # Check for conjunctions indicating multiple actions
    count = sum(1 for indicator in multi_step_indicators if indicator in message_lower)
    
    return count >= 1


__all__ = ["detect_legal_query", "classify_intent", "is_multi_step_request"]
