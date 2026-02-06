from fastapi import Depends, HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from api.auth_middleware import get_current_user
from agents.config.database import get_supabase_client

logger = logging.getLogger(__name__)

async def get_user_subscription(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Helper to fetch subscription for the relevant lawyer.
    If user is assistant, fetch parent's subscription via office_id.
    """
    supabase = get_supabase_client()
    
    # Determine Lawyer ID
    lawyer_id = None
    role_raw = user.get("role")
    
    # Normalize role name
    role_name = ""
    if isinstance(role_raw, dict):
        role_name = role_raw.get("name", "")
    elif isinstance(role_raw, str):
        role_name = role_raw
    else:
        # Fallback if role is ID or not loaded properly, though we expect 'role' key
        role_name = str(role_raw)
        
    if role_name in ["lawyer", "admin", "manager"]:
        lawyer_id = user["id"]
    elif role_name == "assistant":
        lawyer_id = user.get("office_id")
        
    if not lawyer_id:
        return None

    # Fetch Subscription with Package details
    # We sort by created_at desc to get the latest one
    res = supabase.table("lawyer_subscriptions")\
        .select("*, package:subscription_packages(*)")\
        .eq("lawyer_id", lawyer_id)\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()
        
    if res.data:
        return res.data[0]
    return None

async def verify_subscription_active(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to enforce Active Subscription for WRITES (Mutation).
    Allows Read-Only if expired.
    Usage: .post("/", dependencies=[Depends(verify_subscription_active)])
    """
    # 1. Skip exemption - Apply to everyone except maybe Super Admin if exists?
    # Assuming 'admin' here is Office Manager/Lawyer Admin.
    # if user.get("role") in ["super_admin"]: return user
    
    # We enforce for lawyer, assistant, admin, manager.
    pass

    # 2. Get Subscription
    sub = await get_user_subscription(user)
    
    if not sub:
        # If no subscription record exists at all, we might want to allow basic access or block.
        # Usually checking dates is safer. If None, assume no rights?
        # Let's assume valid users always have at least a trial/expired record.
        # If absolutely nothing, block writes.
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا يوجد اشتراك مفعل. (View Only Mode)"
        )

    # 3. Check Expiry
    end_date_str = sub.get("end_date")
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            # If end_date < today -> Expired
            if end_date < datetime.now().date():
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="اشتراكك منتهي. يرجى التجديد لإجراء أي تعديلات. (View Only Mode)"
                )
        except ValueError:
            pass # Invalid date format fallback
    
    return user

async def verify_assistant_login_access(user: Dict[str, Any]):
    """
    Called manually inside Login flow or via Dependency.
    Blocks login if:
    1. Parent Subscription is Expired.
    2. Active Assistants Count > Max Allowed.
    """
    if user.get("role") != "assistant":
        return user

    lawyer_id = user.get("office_id")
    if not lawyer_id:
        # Orphaned assistant?
        raise HTTPException(status_code=403, detail="حساب مساعد غير مرتبط بمكتب محاماة")

    # 1. Fetch Subscription
    # We re-use helper but we need to await it carefully if called from sync context? 
    # FastAPI handles async execution.
    sub = await get_user_subscription(user)
    
    if not sub:
        raise HTTPException(status_code=403, detail="لم يتم العثور على باقة اشتراك للمكتب")

    # 2. Check Parent Expiry
    end_date_str = sub.get("end_date")
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        if end_date < datetime.now().date():
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="اشتراك المكتب منتهي. تم إيقاف دخول المساعدين مؤقتاً."
            )

    # 3. Check Assistant Limits (Downgrade Enforcement)
    # Total Allowed = Package Base + Extra Purchased
    package_ctx = sub.get("package") or {}
    base_assistants = package_ctx.get("max_assistants", 0)
    extra_assistants = sub.get("extra_assistants", 0)
    max_allowed = base_assistants + extra_assistants
    
    current_active_count = sub.get("assistants_count", 0)
    
    # Determine rank? Or just block ALL if over limit?
    # User said: "prevent assistants from entering OR ... show message he has higher number".
    # Blocking access is the safest "Enforcement".
    # The LAWYER must login to fix it (delete assistants).
    
    if current_active_count > max_allowed:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"تجاوز المكتب الحد المسموح للمساعدين ({max_allowed}). يرجى من مدير المكتب تعديل الباقة أو تقليل العدد."
        )

    return user
