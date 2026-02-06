"""
Redis Cache Module
نظام التخزين المؤقت المركزي للنظام
"""
from .redis_client import get_cache, cached, RedisCache
from .keys import CacheKeys, CacheTTL
from .invalidation import (
    invalidate_user_caches,
    invalidate_lawyer_dashboard,
    invalidate_tasks_caches,
    invalidate_case_caches,
    invalidate_after_task_change,
    invalidate_after_case_change
)

__all__ = [
    'get_cache',
    'cached',
    'RedisCache',
    'CacheKeys',
    'CacheTTL',
    'invalidate_user_caches',
    'invalidate_lawyer_dashboard',
    'invalidate_tasks_caches',
    'invalidate_case_caches',
    'invalidate_after_task_change',
    'invalidate_after_case_change'
]
