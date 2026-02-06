"""
Settings API Router
Account statistics and settings management for SettingsPage
Implements Redis caching with automatic invalidation
"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import os
import shutil
import uuid

from api.auth_middleware import get_current_user
from api.database import get_supabase_client
from api.cache import get_cache, CacheKeys, CacheTTL
from api.cache.invalidation import invalidate_user_caches

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.post("/upload-profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload profile image to local storage.
    """
    try:
        # Create directory if not exists
        upload_dir = os.path.join("uploads", "avatars")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_ext = file.filename.split(".")[-1]
        file_name = f"{current_user['id']}-{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(upload_dir, file_name)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Return the public URL
        public_url = f"/uploads/avatars/{file_name}"
        
        return {"publicUrl": public_url}
        
    except Exception as e:
        logger.error(f"❌ Failed to upload profile image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/public-settings")
async def get_public_settings():
    """
    Get public platform settings (contact info) for non-admin users.
    No authentication required.
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table('platform_settings')\
            .select('contact_email, contact_phone, contact_whatsapp, contact_address, support_hours')\
            .limit(1)\
            .execute()
        
        if not result.data:
            return {
                "contact_email": "support@example.com",
                "contact_phone": "+966XXXXXXXX",
                "contact_whatsapp": "+966XXXXXXXX"
            }
            
        return result.data[0]
    except Exception as e:
        logger.error(f"❌ Failed to fetch public settings: {e}")
        return {
            "contact_email": "support@example.com",
            "contact_phone": "+966XXXXXXXX",
            "contact_whatsapp": "+966XXXXXXXX"
        }


# --- Models ---

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    bio: Optional[str] = None
    license_number: Optional[str] = None
    lawyer_license_type: Optional[str] = None
    bar_association: Optional[str] = None
    years_of_experience: Optional[int] = None
    languages: Optional[list] = None
    website: Optional[str] = None
    linkedin_profile: Optional[str] = None
    profile_image_url: Optional[str] = None
    office_address: Optional[str] = None
    office_city: Optional[str] = None
    office_postal_code: Optional[str] = None
    business_hours: Optional[dict] = None
    timezone: Optional[str] = None
    notification_preferences: Optional[dict] = None


# --- Helper Functions ---

def log_audit(supabase, action: str, table: str, record_id: str,
              user: Dict[str, Any],
              old_values: Any = None, new_values: Any = None,
              description: str = None):
    """Log action to audit_logs table"""
    try:
        changes = None
        if old_values and new_values and action == 'update':
            changes = {}
            for key in new_values:
                if key in old_values and old_values[key] != new_values[key]:
                    changes[key] = {'old': old_values[key], 'new': new_values[key]}

        # Get lawyer_id
        if user.get('role') == 'assistant':
            lawyer_id = user.get('office_id', user['id'])
        else:
            lawyer_id = user['id']

        audit_data = {
            'action': action,
            'table_name': table,
            'record_id': record_id,
            'user_id': user['id'],
            'user_name': user.get('full_name'),
            'user_role': user.get('role', 'lawyer'),
            'old_values': old_values,
            'new_values': new_values,
            'changes': changes,
            'description': description,
            'lawyer_id': lawyer_id,
            'created_at': datetime.now().isoformat()
        }

        supabase.table('audit_logs').insert(audit_data).execute()
    except Exception as e:
        logger.warning(f"Failed to log audit: {e}")


# --- Endpoints ---


@router.get("/account-stats")
async def get_account_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> dict:
    """
    Get account statistics with Redis caching
    
    Cache Strategy:
    - TTL: 5 minutes
    - Pattern: Cache-Aside with Invalidation
    - Key: user:{user_id}:stats
    - Invalidated on: CRUD operations
    """
    lawyer_id = current_user['id']
    cache = get_cache()
    cache_key = CacheKeys.user_stats(lawyer_id)
    
    # محاولة القراءة من Cache
    cached_stats = cache.get(cache_key)
    if cached_stats:
        logger.info(f"✅ Account stats loaded from cache for {lawyer_id}")
        return cached_stats
    
    # Cache MISS - حساب الإحصائيات
    try:
        supabase = get_supabase_client()
        
        logger.info(f"⚙️ Fetching account stats from database for lawyer: {lawyer_id}")
        
        # Fetch all counts
        cases = supabase.table('cases')\
            .select('*', count='exact', head=True)\
            .eq('lawyer_id', lawyer_id)\
            .execute()
        
        clients = supabase.table('clients')\
            .select('*', count='exact', head=True)\
            .eq('lawyer_id', lawyer_id)\
            .execute()
        
        tasks = supabase.table('tasks')\
            .select('*', count='exact', head=True)\
            .eq('lawyer_id', lawyer_id)\
            .execute()
        
        hearings = supabase.table('hearings')\
            .select('*', count='exact', head=True)\
            .eq('lawyer_id', lawyer_id)\
            .execute()
        
        # Note: police_records uses user_id instead of lawyer_id
        police_records = supabase.table('police_records')\
            .select('*', count='exact', head=True)\
            .eq('user_id', lawyer_id)\
            .execute()
        
        stats = {
            'cases': cases.count or 0,
            'clients': clients.count or 0,
            'tasks': tasks.count or 0,
            'hearings': hearings.count or 0,
            'police_records': police_records.count or 0
        }
        
        # حفظ في Cache لمدة 5 دقائق
        cache.set(cache_key, stats, ttl=CacheTTL.ACCOUNT_STATS)
        logger.info(f"💾 Cached account stats for {lawyer_id}")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch account stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch account statistics: {str(e)}"
        )


# ✅ Phase 2: Profile Update Endpoint
@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update user profile.
    Enforces user_id from JWT (users can only update their own profile).
    """
    try:
        supabase = get_supabase_client()
        user_id = current_user['id']
        
        # Get old values for audit
        existing = supabase.table('users')\
            .select('*')\
            .eq('id', user_id)\
            .single()\
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        old_user = existing.data
        
        # Build update data (only non-None fields)
        update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
        
        if not update_data:
            # Remove sensitive data
            existing.data.pop('password_hash', None)
            return existing.data  # Nothing to update
        
        # Update user profile
        result = supabase.table('users')\
            .update(update_data)\
            .eq('id', user_id)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update profile")
        
        updated_user = result.data[0]
        
        # Log audit
        log_audit(
            supabase, 'update', 'users', user_id,
            current_user,
            old_values=old_user,
            new_values=updated_user,
            description='تحديث الملف الشخصي'
        )
        
        # ✅ إبطال Cache بعد التحديث
        invalidate_user_caches(user_id)
        
        logger.info(f"✅ Profile updated: {user_id}")
        
        # Remove sensitive data
        updated_user.pop('password_hash', None)
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public")
async def get_public_settings() -> dict:
    """
    Get public platform settings (Branding, Footer, etc.)
    No authentication required.
    Cache Strategy: 1 hour (public settings change rarely)
    """
    cache = get_cache()
    # Cache key for public settings
    cache_key = "platform:settings:public"
    
    cached_settings = cache.get(cache_key)
    if cached_settings:
        return cached_settings

    try:
        supabase = get_supabase_client()
        result = supabase.table('platform_settings').select('*').single().execute()
        
        if not result.data:
            return {}
            
        settings = result.data
        
        # Filter only public fields
        public_settings = {
            'platform_name': settings.get('platform_name'),
            'platform_name_en': settings.get('platform_name_en'),
            'platform_description': settings.get('platform_description'),
            'platform_logo_url': settings.get('platform_logo_url'),
            'platform_favicon_url': settings.get('platform_favicon_url'),
            'footer_copyright_text': settings.get('footer_copyright_text'),
            'footer_powered_by': settings.get('footer_powered_by'),
            'footer_links': settings.get('footer_links'),
            'contact_email': settings.get('contact_email'),
            'contact_phone': settings.get('contact_phone'),
            'contact_whatsapp': settings.get('contact_whatsapp'),
            'support_hours': settings.get('support_hours'),
            'default_language': settings.get('default_language'),
            'currency': settings.get('currency')
        }
        
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, public_settings, ttl=3600)
        
        return public_settings
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch public settings: {e}")
        # Return empty/default rather than failing for public endpoint
        return {}
