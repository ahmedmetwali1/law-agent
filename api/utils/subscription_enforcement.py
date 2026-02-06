from fastapi import HTTPException, Depends
from api.auth import get_current_user_id
# from api.auth_middleware import get_supabase_client # Incorrect
from agents.config.database import get_supabase_client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def get_lawyer_subscription(user_id: str):
    """Fetch detailed subscription with package for a lawyer"""
    supabase = get_supabase_client()
    result = supabase.table("lawyer_subscriptions")\
        .select("*, package:subscription_packages(*)")\
        .eq("lawyer_id", user_id)\
        .limit(1).execute()
    
    if not result.data:
        return None
    return result.data[0]

async def check_subscription_active(user_id: str = Depends(get_current_user_id), require_ai: bool = False):
    """
    Dependency to check if user has an active subscription.
    Checks date expiry and basic status.
    """
    try:
        supabase = get_supabase_client()
        
        # Get user's subscription
        # Also join package to check features/limits if needed (optimization: cache this)
        result = supabase.table("lawyer_subscriptions")\
            .select("*, package:subscription_packages(ai_words_monthly)")\
            .eq("lawyer_id", user_id)\
            .limit(1).execute()
        
        if not result.data:
            # No subscription found - restrict access
            # Or allow limited free tier if defined? Requirement says "15 days trial for new account", implies mandatory sub.
            raise HTTPException(status_code=403, detail="لا يوجد اشتراك فعال. يرجى الاشتراك للمتابعة.")
        
        sub = result.data[0]
        
        # Check Status
        if sub.get('status') == 'expired':
            raise HTTPException(status_code=403, detail="انتهت صلاحية اشتراكك. يرجى التجديد للمتابعة.")
            
        # Check Date
        if sub.get('end_date'):
            end_date = datetime.strptime(sub['end_date'], '%Y-%m-%d').date()
            today = datetime.now().date()
            
            if today > end_date:
                # Expired based on date
                # Ideally we should update status to expired in BG, but here we just block.
                # Auto-update status for better UX next time
                try:
                    supabase.table("lawyer_subscriptions").update({"status": "expired"}).eq("id", sub['id']).execute()
                except:
                    pass
                raise HTTPException(status_code=403, detail="انتهت صلاحية اشتراكك. يرجى التجديد للمتابعة.")

        # Check AI Limits if required
        if require_ai:
            words_used = sub.get('words_used_this_month', 0)
            base_limit = sub.get('package', {}).get('ai_words_monthly', 0)
            
            # Only include extra words if status is 'active'
            extra_words = sub.get('extra_words', 0) if sub.get('status') == 'active' else 0
            total_limit = base_limit + extra_words
            
            if words_used >= total_limit:
                 raise HTTPException(status_code=403, detail="لقد تجاوزت حد الكلمات المسموح به لهذا الشهر. يرجى الترقية للمتابعة.")

        return sub
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription check error: {e}")
        # In case of system error, fail safe (block) or fail open? 
        # Better fail safe for business logic.
        raise HTTPException(status_code=500, detail="خطأ في التحقق من الاشتراك")

async def check_assistant_limit(user_id: str):
    """
    Check if user can add more assistants
    """
    sub = await get_lawyer_subscription(user_id)
    if not sub:
        raise HTTPException(status_code=403, detail="No subscription found")
        
    current_count = sub.get('assistants_count', 0)
    base_limit = sub.get('package', {}).get('max_assistants', 0) if sub.get('package') else 0
    
    # Only include extra resources if status is 'active'
    # Prevent using requested resources before approval
    extra = sub.get('extra_assistants', 0) if sub.get('status') == 'active' else 0
    
    if current_count >= (base_limit + extra):
        raise HTTPException(status_code=403, detail="لقد وصلت للحد الأقصى من المساعدين المسموح به في باقتك.")
    
    return True

async def check_storage_limit(user_id: str, new_file_size_bytes: int = 0):
    """
    Check if user has enough storage space
    """
    sub = await get_lawyer_subscription(user_id)
    if not sub:
        raise HTTPException(status_code=403, detail="No subscription found")
    
    # Get current storage usage from DB
    current_usage_mb = sub.get('storage_used_mb', 0)
    
    # Limit from package
    base_limit_mb = sub.get('package', {}).get('storage_mb', 0) if sub.get('package') else 0
    
    # Only include extra resources if status is 'active'
    # Prevent using requested resources before approval
    extra_mb = sub.get('extra_storage_mb', 0) if sub.get('status') == 'active' else 0
    total_limit_mb = base_limit_mb + extra_mb
    
    new_usage_mb = current_usage_mb + (new_file_size_bytes / (1024 * 1024))
    
    if new_usage_mb > total_limit_mb:
        raise HTTPException(
            status_code=403, 
            detail=f"لا توجد مساحة تخزين كافية. المتبقي: {max(0, total_limit_mb - current_usage_mb):.2f} ميجابايت"
        )
    
    return True
