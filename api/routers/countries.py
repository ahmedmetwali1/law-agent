"""
Countries API Router
Public endpoint for fetching countries list
Uses Redis caching with 7-day TTL for optimal performance
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import logging

from api.database import get_supabase_client
from api.cache import get_cache, CacheKeys, CacheTTL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/countries", tags=["countries"])


# --- Models ---

class CountryResponse(BaseModel):
    id: str
    name_ar: str
    name_en: str
    code: str
    phone_prefix: str
    flag_emoji: str


# --- Endpoints ---

@router.get("", response_model=List[CountryResponse])
async def get_countries() -> List[CountryResponse]:
    """
    Get all countries with Redis caching.
    
    Cache Strategy:
    - TTL: 7 days (rarely changes)
    - Pattern: Cache-Aside
    - Key: app:public:countries
    """
    cache = get_cache()
    cache_key = CacheKeys.COUNTRIES
    
    # 1. محاولة القراءة من Cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.info("✅ Countries loaded from Redis cache")
        return [CountryResponse(**country) for country in cached_data]
    
    # 2. Cache MISS - القراءة من Database
    try:
        logger.info("❌ Cache MISS - Loading countries from database")
        supabase = get_supabase_client()
        
        result = supabase.table('countries')\
            .select('id, name_ar, name_en, code, phone_prefix, flag_emoji')\
            .order('name_ar', desc=False)\
            .execute()
        
        countries = result.data or []
        
        # 3. حفظ في Cache لمدة 7 أيام
        cache.set(cache_key, countries, ttl=CacheTTL.COUNTRIES)
        logger.info(f"💾 Cached {len(countries)} countries for 7 days")
        
        return [CountryResponse(**country) for country in countries]
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch countries: {e}")
        raise HTTPException(status_code=500, detail=str(e))
