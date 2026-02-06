"""
Cache Invalidation Helpers
إدارة مركزية لإبطال Cache عند التحديثات
"""
import logging
from typing import Optional
from .redis_client import get_cache
from .keys import CacheKeys

logger = logging.getLogger(__name__)


def invalidate_user_caches(user_id: str):
    """
    إبطال جميع caches متعلقة بمستخدم معين
    
    Args:
        user_id: معرف المستخدم
    """
    cache = get_cache()
    
    keys_to_delete = [
        CacheKeys.user_profile(user_id),
        CacheKeys.user_stats(user_id),
    ]
    
    for key in keys_to_delete:
        cache.delete(key)
    
    logger.info(f"🗑️ Invalidated user caches for: {user_id}")


def invalidate_lawyer_dashboard(lawyer_id: str):
    """
    إبطال caches لوحة التحكم
    
    Args:
        lawyer_id: معرف المحامي
    """
    cache = get_cache()
    
    # حذف جميع بيانات Dashboard
    pattern = f"lawyer:{lawyer_id}:dashboard:*"
    count = cache.delete_pattern(pattern)
    
    # حذف إحصائيات المستخدم أيضاً
    cache.delete(CacheKeys.user_stats(lawyer_id))
    
    logger.info(f"🗑️ Invalidated {count} dashboard caches for lawyer: {lawyer_id}")


def invalidate_tasks_caches(lawyer_id: str):
    """
    إبطال caches المهام
    
    Args:
        lawyer_id: معرف المحامي
    """
    cache = get_cache()
    
    pattern = f"lawyer:{lawyer_id}:tasks:*"
    count = cache.delete_pattern(pattern)
    
    logger.info(f"🗑️ Invalidated {count} tasks caches for lawyer: {lawyer_id}")


def invalidate_case_caches(case_id: str):
    """
    إبطال جميع caches متعلقة بقضية
    
    Args:
        case_id: معرف القضية
    """
    cache = get_cache()
    
    pattern = CacheKeys.case_all_data(case_id)
    count = cache.delete_pattern(pattern)
    
    logger.info(f"🗑️ Invalidated {count} case caches for: {case_id}")


def invalidate_police_records_caches(lawyer_id: str):
    """
    إبطال caches المحاضر
    
    Args:
        lawyer_id: معرف المحامي
    """
    cache = get_cache()
    
    cache.delete(CacheKeys.lawyer_police_records(lawyer_id))
    logger.info(f"🗑️ Invalidated police records cache for lawyer: {lawyer_id}")


def invalidate_notifications_caches(lawyer_id: str):
    """
    إبطال caches الإشعارات
    
    Args:
        lawyer_id: معرف المحامي
    """
    cache = get_cache()
    
    cache.delete(CacheKeys.lawyer_notifications(lawyer_id))
    logger.info(f"🗑️ Invalidated notifications cache for lawyer: {lawyer_id}")


# ===== Combined Invalidation Functions =====

def invalidate_after_task_change(lawyer_id: str):
    """
    إبطال Caches بعد تغيير في المهام
    
    يُستدعى بعد: Create, Update, Delete task
    
    Args:
        lawyer_id: معرف المحامي
    """
    invalidate_tasks_caches(lawyer_id)
    invalidate_lawyer_dashboard(lawyer_id)
    invalidate_notifications_caches(lawyer_id)


def invalidate_after_case_change(lawyer_id: str, case_id: Optional[str] = None):
    """
    إبطال Caches بعد تغيير في القضايا
    
    يُستدعى بعد: Create, Update, Delete case
    
    Args:
        lawyer_id: معرف المحامي
        case_id: معرف القضية (اختياري)
    """
    cache = get_cache()
    
    # Cases list
    cache.delete(CacheKeys.lawyer_cases(lawyer_id))
    
    # Dashboard
    invalidate_lawyer_dashboard(lawyer_id)
    
    # Case details
    if case_id:
        invalidate_case_caches(case_id)


def invalidate_after_police_record_change(lawyer_id: str):
    """
    إبطال Caches بعد تغيير في المحاضر
    
    Args:
        lawyer_id: معرف المحامي
    """
    invalidate_police_records_caches(lawyer_id)
    invalidate_lawyer_dashboard(lawyer_id)


def invalidate_after_profile_update(user_id: str):
    """
    إبطال Caches بعد تحديث الملف الشخصي
    
    Args:
        user_id: معرف المستخدم
    """
    invalidate_user_caches(user_id)


def invalidate_all_for_lawyer(lawyer_id: str):
    """
    إبطال جميع Caches لمحامي معين
    
    استخدام حذر - يحذف كل شيء!
    
    Args:
        lawyer_id: معرف المحامي
    """
    cache = get_cache()
    
    pattern = CacheKeys.lawyer_all_data(lawyer_id)
    count = cache.delete_pattern(pattern)
    
    # حذف بيانات المستخدم أيضاً
    invalidate_user_caches(lawyer_id)
    
    logger.warning(f"⚠️ Invalidated ALL caches ({count} keys) for lawyer: {lawyer_id}")
