"""
Redis Cache Client
نظام التخزين المؤقت المركزي للنظام مع إمكانية التحكم الكامل
"""
import redis
from redis.connection import ConnectionPool
from typing import Any, Optional, Union
import json
import logging
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis Cache Client مع Fallback التلقائي والتحكم الكامل
    
    Features:
    - ✅ Enable/Disable toggle control via environment variable
    - ✅ Connection pooling للأداء العالي
    - ✅ Automatic fallback عند فشل Redis
    - ✅ Serialization/Deserialization تلقائي
    - ✅ TTL management
    - ✅ Graceful degradation
    - ✅ Performance monitoring (cache hits/misses)
    """
    
    def __init__(self):
        self.enabled = self._is_cache_enabled()
        self.client: Optional[redis.Redis] = None
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        
        if self.enabled:
            self._initialize_client()
        else:
            logger.info("🔴 Redis caching is DISABLED by configuration (REDIS_ENABLED=False)")
    
    def _is_cache_enabled(self) -> bool:
        """التحقق من تفعيل Cache من .env"""
        enabled = os.getenv('REDIS_ENABLED', 'True').lower() == 'true'
        return enabled
    
    def _initialize_client(self):
        """تهيئة اتصال Redis مع معالجة الأخطاء الاحترافية"""
        try:
            # قراءة الإعدادات من .env
            redis_config = {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': int(os.getenv('REDIS_DB', 0)),
                'password': os.getenv('REDIS_PASSWORD'),
                'decode_responses': True,
                'socket_timeout': int(os.getenv('REDIS_SOCKET_TIMEOUT', 5)),
                'socket_connect_timeout': int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', 5)),
                'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', 50)),
                'health_check_interval': 30,  # Check connection health every 30s
            }
            
            # إضافة SSL إذا كان مفعلاً
            if os.getenv('REDIS_SSL', 'False').lower() == 'true':
                import ssl
                redis_config['ssl'] = True
                ssl_cert_reqs = os.getenv('REDIS_SSL_CERT_REQS', 'none').lower()
                
                if ssl_cert_reqs == 'required':
                    redis_config['ssl_cert_reqs'] = ssl.CERT_REQUIRED
                elif ssl_cert_reqs == 'optional':
                    redis_config['ssl_cert_reqs'] = ssl.CERT_OPTIONAL
                else:
                    redis_config['ssl_cert_reqs'] = ssl.CERT_NONE
                
                if os.getenv('REDIS_SSL_CA_CERTS'):
                    redis_config['ssl_ca_certs'] = os.getenv('REDIS_SSL_CA_CERTS')
            
            # إنشاء Connection Pool
            pool = ConnectionPool(**redis_config)
            self.client = redis.Redis(connection_pool=pool)
            
            # اختبار الاتصال
            self.client.ping()
            logger.info(f"✅ Redis connected successfully to {redis_config['host']}:{redis_config['port']}")
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️ Running without cache - falling back to database")
            self.enabled = False
            self.client = None
        except Exception as e:
            logger.error(f"❌ Redis initialization error: {e}")
            logger.warning("⚠️ Running without cache - falling back to database")
            self.enabled = False
            self.client = None
    
    def is_available(self) -> bool:
        """
        التحقق من توفر Redis
        
        Returns:
            True إذا كان Redis متاحاً ومفعّلاً
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.ping()
            return True
        except:
            logger.warning("⚠️ Redis unavailable - using database fallback")
            return False
    
    def _serialize(self, value: Any) -> str:
        """تحويل البيانات إلى JSON"""
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Serialization error: {e}")
            raise
    
    def _deserialize(self, value: str) -> Any:
        """استرجاع البيانات من JSON"""
        try:
            return json.loads(value)
        except Exception as e:
            logger.error(f"❌ Deserialization error: {e}")
            return value
    
    def get(self, key: str) -> Optional[Any]:
        """
        قراءة قيمة من Cache
        
        Args:
            key: مفتاح Cache
        
        Returns:
            القيمة المخزنة أو None إذا:
            - المفتاح غير موجود
            - Redis غير متاح
            - حدث خطأ
        """
        if not self.is_available():
            return None
        
        try:
            value = self.client.get(key)
            
            if value is None:
                self.stats['misses'] += 1
                if os.getenv('REDIS_LOG_CACHE_MISSES', 'False').lower() == 'true':
                    logger.debug(f"❌ Cache MISS: {key}")
                return None
            
            self.stats['hits'] += 1
            if os.getenv('REDIS_LOG_CACHE_HITS', 'True').lower() == 'true':
                logger.debug(f"✅ Cache HIT: {key}")
            
            return self._deserialize(value)
            
        except redis.RedisError as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Cache GET error for key '{key}': {e}")
            return None
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Unexpected error in cache GET for key '{key}': {e}")
            return None
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        حفظ قيمة في Cache
        
        Args:
            key: مفتاح Cache
            value: القيمة (يتم تحويلها لـ JSON تلقائياً)
            ttl: مدة الصلاحية بالثواني (None = بلا انتهاء)
        
        Returns:
            True إذا نجحت العملية
        """
        if not self.is_available():
            return False
        
        try:
            serialized = self._serialize(value)
            
            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
            
            self.stats['sets'] += 1
            logger.debug(f"💾 Cache SET: {key} (TTL: {ttl}s)")
            return True
            
        except redis.RedisError as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Cache SET error for key '{key}': {e}")
            return False
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Unexpected error in cache SET for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """حذف مفتاح من Cache"""
        if not self.is_available():
            return False
        
        try:
            self.client.delete(key)
            self.stats['deletes'] += 1
            logger.debug(f"🗑️ Cache DELETE: {key}")
            return True
        except redis.RedisError as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Cache DELETE error for key '{key}': {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        حذف جميع المفاتيح المطابقة لنمط معين
        
        Args:
            pattern: نمط البحث (مثال: "lawyer:123:*")
        
        Returns:
            عدد المفاتيح المحذوفة
        """
        if not self.is_available():
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                count = self.client.delete(*keys)
                self.stats['deletes'] += count
                logger.debug(f"🗑️ Cache DELETE_PATTERN: {pattern} ({count} keys)")
                return count
            return 0
        except redis.RedisError as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Cache DELETE_PATTERN error for pattern '{pattern}': {e}")
            return 0
    
    def clear_all(self) -> bool:
        """
        مسح جميع البيانات من Cache (خطير - للتطوير فقط!)
        
        ⚠️ تحذير: يحذف جميع البيانات من DB الحالية
        """
        if not self.is_available():
            return False
        
        try:
            self.client.flushdb()
            logger.warning("⚠️ Cache cleared completely (FLUSHDB)")
            return True
        except redis.RedisError as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Cache CLEAR error: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """
        الحصول على الوقت المتبقي لانتهاء المفتاح
        
        Returns:
            -2: المفتاح غير موجود
            -1: المفتاح بلا انتهاء
            >0: الثواني المتبقية
        """
        if not self.is_available():
            return -2
        
        try:
            return self.client.ttl(key)
        except:
            return -2
    
    def get_stats(self) -> dict:
        """
        الحصول على إحصائيات الأداء
        
        Returns:
            Dict مع: hits, misses, sets, deletes, errors, hit_rate
        """
        total_reads = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_reads * 100) if total_reads > 0 else 0
        
        return {
            **self.stats,
            'hit_rate': round(hit_rate, 2),
            'enabled': self.enabled,
            'available': self.is_available()
        }
    
    def reset_stats(self):
        """إعادة تعيين الإحصائيات"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        logger.info("📊 Cache statistics reset")
    
    def get_info(self) -> dict:
        """
        الحصول على معلومات Redis Server
        
        Returns:
            معلومات الخادم أو dict فارغ إذا كان Redis غير متاح
        """
        if not self.is_available():
            return {}
        
        try:
            info = self.client.info()
            return {
                'redis_version': info.get('redis_version'),
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace': info.get('db0', {})
            }
        except:
            return {}


# ===== Singleton Instance =====
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """
    الحصول على Redis Cache Instance (Singleton)
    
    Returns:
        نفس الـ instance في كل مرة لتوفير الموارد
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


# ===== Decorator لتسهيل الاستخدام =====

def cached(
    key_prefix: str,
    ttl: int = 300,
    key_builder: Optional[callable] = None
):
    """
    Decorator للتخزين المؤقت التلقائي
    
    Args:
        key_prefix: بادئة المفتاح
        ttl: مدة الصلاحية بالثواني
        key_builder: دالة لبناء المفتاح من المعاملات
    
    Usage:
        @cached(key_prefix="countries", ttl=604800)  # 7 days
        async def get_countries():
            # ... database query
            return countries
        
        # With dynamic key
        @cached(
            key_prefix="user_profile",
            ttl=1800,
            key_builder=lambda user_id: f"user:{user_id}:profile"
        )
        async def get_user_profile(user_id: str):
            # ... database query
            return profile
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # بناء المفتاح
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = key_prefix
            
            # محاولة القراءة من Cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Cache MISS - تنفيذ الدالة
            result = await func(*args, **kwargs)
            
            # حفظ في Cache
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator
