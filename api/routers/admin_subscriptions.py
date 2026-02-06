from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from api.auth import get_current_user
from api.auth_middleware import require_role
from api.database import get_supabase_client
from pydantic import BaseModel

# Setup Logger
logger = logging.getLogger(__name__)

# Create Router
router = APIRouter(tags=["admin_subscriptions"])

# Models
class SubscriptionAdminView(BaseModel):
    id: str
    lawyer_id: str
    lawyer_name: str
    package_name: str
    status: str
    start_date: str
    end_date: str
    auto_renew: bool
    amount_paid: Optional[float] = 0
    payment_method: Optional[str] = None
    requested_assistants: Optional[int] = 0
    requested_storage: Optional[int] = 0
    requested_ai_words: Optional[int] = 0
    # Usage Stats
    words_used: Optional[int] = 0
    storage_used: Optional[float] = 0
    assistants_count: Optional[int] = 0
    # Current Limits (Base + Active Extra)
    max_words: Optional[int] = 0
    max_storage: Optional[float] = 0
    max_assistants: Optional[int] = 0
    is_flagged: Optional[bool] = False
    last_login: Optional[str] = None
    updated_at: Optional[str] = None

class ActionRequest(BaseModel):
    duration_months: Optional[int] = 1
    days: Optional[int] = 30

# Dependencies
# Require Admin Role (using role ID for super admin or 'admin' role name)
async def check_admin_access(current_user: dict = Depends(get_current_user)):
    user_role = current_user.get("role")
    user_role_id = current_user.get("role_id")
    # Admin Role ID from previous context: e2d8b2c0-7b8d-4b46-88e8-cb0071467901
    if user_role != 'admin' and user_role_id != 'e2d8b2c0-7b8d-4b46-88e8-cb0071467901':
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return current_user

@router.get("/api/admin/packages/default")
async def get_default_package(current_user: dict = Depends(check_admin_access)):
    """Fetch the default (Starter) package"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("subscription_packages")\
            .select("*")\
            .eq("is_default", True)\
            .order("created_at", desc=True)\
            .limit(1).execute()
        
        if not result.data:
            # Fallback: look for smallest package or any starter
            result = supabase.table("subscription_packages")\
                .select("*")\
                .ilike("name", "%starter%")\
                .limit(1).execute()
                
        if not result.data:
             raise HTTPException(status_code=404, detail="Default package not found")
             
        return result.data[0]
    except Exception as e:
        logger.error(f"Failed to fetch default package: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/api/admin/packages/{package_id}")
async def update_package(
    package_id: str,
    update_data: dict,
    current_user: dict = Depends(check_admin_access)
):
    """Update package limits and details"""
    try:
        supabase = get_supabase_client()
        
        # Safe fields to update from admin UI
        allowed_fields = ["max_assistants", "storage_mb", "ai_words_monthly", "is_active", "name_ar", "description_ar", "max_clients", "max_cases"]
        payload = {k: v for k, v in update_data.items() if k in allowed_fields}
        payload["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("subscription_packages").update(payload).eq("id", package_id).execute()
        
        if not result.data:
             raise HTTPException(status_code=404, detail="Package not found")
             
        return result.data[0]
    except Exception as e:
        logger.error(f"Failed to update package: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/admin/pricing/country")
async def get_country_pricing_admin(current_user: dict = Depends(check_admin_access)):
    """Fetch all country-specific pricing rules"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("country_pricing")\
            .select("*, country:countries(name_ar, flag_emoji, code)")\
            .order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        logger.error(f"Failed to fetch country pricing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/api/admin/pricing/country/{pricing_id}")
async def update_country_pricing_admin(
    pricing_id: str,
    update_data: dict,
    current_user: dict = Depends(check_admin_access)
):
    """Update country-specific pricing rules"""
    try:
        supabase = get_supabase_client()
        allowed = ["price_per_assistant", "price_per_gb_monthly", "price_per_1000_words", "yearly_discount_percent", "free_storage_gb", "free_words_monthly", "is_active", "base_platform_fee"]
        payload = {k: v for k, v in update_data.items() if k in allowed}
        payload["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("country_pricing").update(payload).eq("id", pricing_id).execute()
        return result.data[0]
    except Exception as e:
        logger.error(f"Failed to update country pricing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/admin/pricing/global")
async def get_global_pricing_admin(current_user: dict = Depends(check_admin_access)):
    """Fetch global default pricing rules"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("subscription_pricing").select("*").eq("is_active", True).limit(1).execute()
        if not result.data:
            result = supabase.table("subscription_pricing").select("*").limit(1).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        logger.error(f"Failed to fetch global pricing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/api/admin/pricing/global/{pricing_id}")
async def update_global_pricing_admin(
    pricing_id: str,
    update_data: dict,
    current_user: dict = Depends(check_admin_access)
):
    """Update global pricing rules"""
    try:
        supabase = get_supabase_client()
        allowed = ["base_platform_fee", "price_per_assistant", "price_per_gb_monthly", "price_per_1000_words", "yearly_discount_percent", "free_storage_gb", "free_words_monthly", "is_active"]
        payload = {k: v for k, v in update_data.items() if k in allowed}
        payload["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("subscription_pricing").update(payload).eq("id", pricing_id).execute()
        return result.data[0]
    except Exception as e:
        logger.error(f"Failed to update global pricing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/admin/default-package")
async def get_default_package_admin(current_user: dict = Depends(check_admin_access)):
    """Fetch the default (Starter) package"""
    return await get_default_package(current_user)

@router.patch("/api/admin/default-package")
async def update_default_package_admin(update_data: dict, current_user: dict = Depends(check_admin_access)):
    """Update the default package directly"""
    pkg = await get_default_package(current_user)
    return await update_package(pkg['id'], update_data, current_user)

# Endpoints

@router.get("/api/admin/subscriptions", response_model=List[SubscriptionAdminView])
async def list_all_subscriptions(
    status: Optional[str] = None,
    current_user: dict = Depends(check_admin_access)
):
    """
    List all lawyers and their subscription status.
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("users")\
            .select("id, full_name, last_login, role, lawyer_subscriptions(*, package:subscription_packages(*))")\
            .in_("role", ["lawyer", "manager", "admin"])\
            .order("created_at", desc=True)
            
        result = query.execute()
        
        if not result.data:
            return []

        # Optimization: Pre-fetch live usage stats to avoid N+1 queries
        # 1. Fetch Real Assistants Counts
        assistants_res = supabase.table("users").select("office_id").eq("role", "assistant").execute()
        assistant_map = {}
        if assistants_res.data:
            for u in assistants_res.data:
                oid = u.get("office_id")
                if oid:
                    assistant_map[oid] = assistant_map.get(oid, 0) + 1

        # 2. Fetch Real Storage Usage
        # Note: Fetching all file_sizes might be heavy eventually, but efficient for <10k docs. 
        # Ideally meaningful aggregation should happen in DB (View/RPC).
        docs_res = supabase.table("documents").select("lawyer_id, file_size").execute()
        storage_map = {}
        if docs_res.data:
            for d in docs_res.data:
                lid = d.get("lawyer_id")
                size = d.get("file_size", 0)
                if lid and size:
                    storage_map[lid] = storage_map.get(lid, 0) + size

        subscriptions = []
        for user in result.data:
            try:
                sub_list = user.get('lawyer_subscriptions', [])
                # Ensure we have a list
                if not isinstance(sub_list, list):
                    logger.warning(f"lawyer_subscriptions for user {user['id']} is not a list: {type(sub_list)}")
                    sub_list = [sub_list] if sub_list else []
                
                # Sort by created_at desc to get the latest
                sub_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                
                item = sub_list[0] if sub_list else None
                
                # Filter by status if requested
                if status and status != 'all':
                    current_status = item['status'] if item else 'none'
                    if status == 'none' and item is not None: continue
                    if status != 'none' and (not item or item['status'] != status): continue

                # Calculate Limits
                pkg = item.get('package', {}) if item else {}
                curr_status = item['status'] if item else 'none'
                is_active = (curr_status == 'active' or curr_status == 'trial')
                
                base_words = pkg.get('ai_words_monthly', 0) if pkg else 0
                extra_words = item.get('extra_words', 0) if (item and is_active) else 0
                max_words = int(base_words) + int(extra_words)
                
                base_storage = pkg.get('storage_mb', 0) if pkg else 0
                extra_storage_gb = item.get('extra_storage_gb', 0) if (item and is_active) else 0
                extra_storage_mb = extra_storage_gb * 1024
                max_storage = float(base_storage) + float(extra_storage_mb)
                
                base_assistants = pkg.get('max_assistants', 0) if pkg else 0
                extra_assistants = item.get('extra_assistants', 0) if (item and is_active) else 0
                max_assistants = int(base_assistants) + int(extra_assistants)

                # Real-Time Usage Data (Source of Truth)
                # Words: From DB (updated by usage events)
                words_used = item.get('words_used_this_month', 0) if item else 0
                
                # Storage: Calculated live from documents
                total_bytes = storage_map.get(user['id'], 0)
                storage_used = round(total_bytes / (1024 * 1024), 2)
                
                # Assistants: Calculated live from users table
                assistants_count = assistant_map.get(user['id'], 0)

                # Flagging Logic
                is_flagged = False
                if max_words > 0 and words_used > max_words: is_flagged = True
                if max_storage > 0 and storage_used > max_storage: is_flagged = True

                subscriptions.append({
                    "id": str(item['id']) if (item and 'id' in item) else f"no-sub-{user['id']}",
                    "lawyer_id": user['id'],
                    "lawyer_name": user['full_name'] or "Unknown",
                    "package_name": pkg.get('name_ar') or pkg.get('name') or 'Default',
                    "status": curr_status,
                    "start_date": str(item['start_date']) if (item and item.get('start_date')) else "-",
                    "end_date": str(item['end_date']) if (item and item.get('end_date')) else "-",
                    "auto_renew": bool(item['auto_renew']) if item else False,
                    "amount_paid": 0.0,
                    "payment_method": "bank_transfer",
                    "requested_assistants": int(item.get('extra_assistants', 0)) if item else 0,
                    "requested_storage": int(item.get('extra_storage_gb', 0) * 1024) if item else 0,
                    "requested_ai_words": int(item.get('extra_words', 0)) if item else 0,
                    "words_used": int(words_used),
                    "storage_used": float(storage_used),
                    "assistants_count": int(assistants_count),
                    "max_words": int(max_words),
                    "max_storage": float(max_storage),
                    "max_assistants": int(max_assistants),
                    "is_flagged": is_flagged,
                    "last_login": user.get('last_login'),
                    "updated_at": str(item.get('updated_at')) if (item and item.get('updated_at')) else "-"
                })
            except Exception as item_err:
                logger.error(f"Error processing user {user.get('id')}: {item_err}")
                continue
                
        return subscriptions
        
    except Exception as e:
        logger.error(f"Failed to list subscriptions: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/admin/subscriptions/{sub_id}/activate")
async def activate_subscription(
    sub_id: str,
    action: ActionRequest,
    current_user: dict = Depends(check_admin_access)
):
    """
    Activate a renewal request:
    - Update status to 'active'
    - Extend end_date by duration_months
    """
    try:
        supabase = get_supabase_client()
        
        # Get current subscription
        existing = supabase.table("lawyer_subscriptions").select("*").eq("id", sub_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        sub = existing.data
        
        # Calculate new dates
        current_end_date = datetime.strptime(sub['end_date'], '%Y-%m-%d').date()
        today = datetime.now().date()
        
        # If expired, start from today. If active, add to end date.
        start_basis = max(current_end_date, today)
        new_end_date = start_basis + timedelta(days=30 * (action.duration_months or 1))
        
        # Update
        update_data = {
            "status": "active",
            "start_date": today.isoformat(),
            "end_date": new_end_date.isoformat(),
            "words_used_this_month": 0, # Reset AI usage on activation
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("lawyer_subscriptions").update(update_data).eq("id", sub_id).execute()
        
        return {"message": "Subscription activated for 30 days", "new_end_date": new_end_date}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/admin/subscriptions/{sub_id}/extend")
async def extend_subscription(
    sub_id: str,
    action: ActionRequest,
    current_user: dict = Depends(check_admin_access)
):
    """
    Manually extend subscription days
    """
    try:
        supabase = get_supabase_client()
        
        # Get current subscription
        existing = supabase.table("lawyer_subscriptions").select("*").eq("id", sub_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        sub = existing.data
        current_end_date = datetime.strptime(sub['end_date'], '%Y-%m-%d').date()
        
        # Extend
        new_end_date = current_end_date + timedelta(days=(action.days or 30))
        
        update_data = {
            "end_date": new_end_date.isoformat(),
            "status": "active", # Ensure it's active if extended
            "updated_at": datetime.now().isoformat()
        }
        
        supabase.table("lawyer_subscriptions").update(update_data).eq("id", sub_id).execute()
        
        return {"message": "Subscription extended successfully", "new_end_date": new_end_date}
        
    except Exception as e:
        logger.error(f"Extension failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/admin/subscriptions/{sub_id}/change-package")
async def change_subscription_package(
    sub_id: str,
    action: dict, # Expecting {"package_id": "..."}
    current_user: dict = Depends(check_admin_access)
):
    """
    Change lawyer's subscription package
    """
    try:
        package_id = action.get("package_id")
        if not package_id:
            raise HTTPException(status_code=400, detail="Package ID is required")
            
        supabase = get_supabase_client()
        
        # Verify package exists
        package = supabase.table("subscription_packages").select("*").eq("id", package_id).single().execute()
        if not package.data:
            raise HTTPException(status_code=404, detail="Package not found")
            
        # Update subscription
        update_data = {
            "package_id": package_id,
            "updated_at": datetime.now().isoformat()
        }
        
        supabase.table("lawyer_subscriptions").update(update_data).eq("id", sub_id).execute()
        
        return {"message": "Package changed successfully", "package_name": package.data['name']}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change package failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/admin/lawyers/{lawyer_id}/activate-trial")
async def activate_trial_for_lawyer(
    lawyer_id: str,
    current_user: dict = Depends(check_admin_access)
):
    """
    Manually activate a trial for a lawyer who has no subscription record.
    """
    try:
        supabase = get_supabase_client()
        
        # 1. Get default package
        pkg_res = supabase.table("subscription_packages").select("*").eq("is_default", True).limit(1).execute()
        if not pkg_res.data:
            pkg_res = supabase.table("subscription_packages").select("*").eq("is_flexible", True).limit(1).execute()
        
        if not pkg_res.data:
             raise HTTPException(status_code=404, detail="Default package configuration not found")
             
        pkg = pkg_res.data[0]
        
        # 2. Get user country
        user_res = supabase.table("users").select("country_id").eq("id", lawyer_id).single().execute()
        country_id = user_res.data.get("country_id") if user_res.data else None
        
        # 3. Create Subscription
        new_sub = {
            "lawyer_id": lawyer_id,
            "package_id": pkg["id"],
            "country_id": country_id,
            "status": "trial",
            "start_date": datetime.now().date().isoformat(),
            "end_date": (datetime.now().date() + timedelta(days=30)).isoformat(),
            "auto_renew": False,
            "extra_assistants": 0,
            "extra_storage_mb": 0, # Rely on package defaults
            "extra_words": 0,
            "words_used_this_month": 0,
            "storage_used_mb": 0
        }
        
        result = supabase.table("lawyer_subscriptions").insert(new_sub).execute()
        
        return {"message": "Trial activated successfully", "data": result.data[0] if result.data else None}
        
    except Exception as e:
        logger.error(f"Trial activation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/api/admin/subscriptions/{sub_id}/resources")
async def update_lawyer_resources(
    sub_id: str,
    resources: dict,
    current_user: dict = Depends(check_admin_access)
):
    """
    Directly override or update extra resources for a lawyer.
    Helpful for professional management and fixing discrepancies.
    """
    try:
        supabase = get_supabase_client()
        
        # Mapping from frontend 'extra_storage_mb' to backend 'extra_storage_gb'
        payload = {}
        if "extra_assistants" in resources: payload["extra_assistants"] = int(resources["extra_assistants"])
        if "extra_words" in resources: payload["extra_words"] = int(resources["extra_words"])
        if "status" in resources: payload["status"] = resources["status"]
        if "end_date" in resources: payload["end_date"] = resources["end_date"]
        
        # Unit Conversion for Storage
        if "extra_storage_mb" in resources:
            payload["extra_storage_gb"] = round(float(resources["extra_storage_mb"]) / 1024, 4)
            
        payload["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("lawyer_subscriptions").update(payload).eq("id", sub_id).execute()
        
        if not result.data:
             raise HTTPException(status_code=404, detail="Subscription not found")
             
        return {"message": "Resources updated successfully", "data": result.data[0]}
    except Exception as e:
        logger.error(f"Failed to update lawyer resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/admin/subscriptions/{sub_id}/reset-usage")
async def reset_subscription_usage(
    sub_id: str,
    current_user: dict = Depends(check_admin_access)
):
    """
    Reset AI word usage for the current month.
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("lawyer_subscriptions").update({"words_used_this_month": 0, "updated_at": datetime.now().isoformat()}).eq("id", sub_id).execute()
        return {"message": "Usage reset successfully"}
    except Exception as e:
        logger.error(f"Failed to reset usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

