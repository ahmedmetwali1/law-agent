from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, date

from api.auth import get_current_user_id
from api.database import get_supabase_client

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])

@router.get("/me")
async def get_my_subscription(user_id: str = Depends(get_current_user_id)):
    """
    Get current user's subscription details
    جلب تفاصيل اشتراك المستخدم الحالي
    """
    try:
        supabase = get_supabase_client()
        
        # Get subscription with package details
        result = supabase.table("lawyer_subscriptions")\
            .select("""
                *,
                package:subscription_packages(*),
                country:countries(*)
            """)\
            .eq("lawyer_id", user_id)\
            .order("created_at", desc=True)\
            .limit(1).execute()
        
        if not result.data:
            # Auto-create trial for existing users if missing
            logger.info(f"No subscription found for user {user_id}. Creating default trial.")
            
            # 1. Get default package (is_default = TRUE)
            pkg_res = supabase.table("subscription_packages").select("id").eq("is_default", True).limit(1).execute()
            if not pkg_res.data:
                pkg_res = supabase.table("subscription_packages").select("id").eq("is_flexible", True).limit(1).execute()
            
            # 2. Get user country
            user_res = supabase.table("users").select("country_id").eq("id", user_id).single().execute()
            country_id = user_res.data.get("country_id") if user_res.data else None
            
            if not country_id:
                # Fallback to default country
                country_res = supabase.table("countries").select("id").eq("is_default", True).limit(1).execute()
                country_id = country_res.data[0].get("id") if country_res.data else None
            
            if pkg_res.data:
                package_id = pkg_res.data[0]["id"]
                
                # Create One-Time Free Trial (50MB, 5000 words, 0 assistants)
                from datetime import timedelta
                trial_end_date = (datetime.now().date() + timedelta(days=30)).isoformat()
                
                new_sub = {
                    "lawyer_id": user_id,
                    "package_id": package_id,
                    "country_id": country_id,
                    "status": "trial",
                    "start_date": datetime.now().date().isoformat(),
                    "end_date": trial_end_date,
                    "auto_renew": False,
                    "extra_assistants": 0,
                    "extra_storage_gb": 0,
                    "extra_words": 0
                }
                
                create_res = supabase.table("lawyer_subscriptions").insert(new_sub).execute()
                
                # Fetch again with relations
                if create_res.data:
                    result = supabase.table("lawyer_subscriptions")\
                        .select("""
                            *,
                            package:subscription_packages(*),
                            country:countries(*)
                        """)\
                        .eq("lawyer_id", user_id)\
                        .limit(1).execute()
            
            if not result.data:
                 return None # Should not happen if creation succeeded
        
        sub = result.data[0]
        
        # Calculate days remaining
        days_remaining = 0
        status_message = ""
        
        if sub.get('end_date'):
            try:
                end_date_str = sub['end_date']
                if 'T' in end_date_str: end_date_str = end_date_str.split('T')[0]
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                today = datetime.now().date()
                days_remaining = (end_date - today).days
                
                if days_remaining < 0:
                    status_message = "منتهي الصلاحية"
                elif sub.get('status') == 'trial':
                    status_message = f"فترة تجريبية ({days_remaining} يوم متبقي)"
                else:
                    status_message = f"نشط ({days_remaining} يوم متبقي)"
            except Exception as date_err:
                logger.error(f"Date parsing error: {date_err}")
                status_message = sub.get('status', 'unknown')
        
        # Calculate Live Usage
        # 1. Real Assistants Count (users where office_id = user_id and role = assistant)
        assistants_count_res = supabase.table("users")\
            .select("id", count="exact")\
            .eq("office_id", user_id)\
            .eq("role", "assistant")\
            .execute()
        live_assistants = assistants_count_res.count if assistants_count_res.count is not None else 0
        
        # 2. Real Storage Count (sum of file_size in documents for this lawyer)
        storage_res = supabase.table("documents")\
            .select("file_size")\
            .eq("lawyer_id", user_id)\
            .execute()
        total_bytes = sum([d.get('file_size', 0) for d in storage_res.data if d.get('file_size')]) if storage_res.data else 0
        live_storage_mb = round(total_bytes / (1024 * 1024), 2)
        
        # 3. Synchronize Extra Resources (Map GB to MB for frontend calculation)
        # Match Admin logic: Extra resources only apply if status is active or trial
        is_active = sub.get('status') in ['active', 'trial']
        
        extra_storage_gb = sub.get('extra_storage_gb', 0) if is_active else 0
        sub['extra_storage_mb'] = extra_storage_gb * 1024
        
        if not is_active:
            sub['extra_assistants'] = 0
            sub['extra_words'] = 0
        
        return {
            **sub,
            "assistants_count": live_assistants,
            "storage_used_mb": live_storage_mb,
            "days_remaining": days_remaining,
            "status_display": status_message
        }
        
    except Exception as e:
        logger.error(f"Error fetching subscription: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/packages")
async def get_packages(user_id: str = Depends(get_current_user_id)):
    """
    Get all available subscription packages with local pricing
    جلب جميع الباقات المتاحة مع الأسعار المحلية
    """
    try:
        supabase = get_supabase_client()
        
        # 1. Get user country
        user_res = supabase.table("users").select("country_id").eq("id", user_id).single().execute()
        country_id = user_res.data.get("country_id") if user_res.data else None
        
        # 2. Get packages
        packages = supabase.table("subscription_packages")\
            .select("*")\
            .eq("is_active", True)\
            .order("sort_order")\
            .execute()
            
        packages_data = packages.data
        
        # 3. Get prices for this country if available
        if country_id:
            prices = supabase.table("package_country_prices")\
                .select("*")\
                .eq("country_id", country_id)\
                .execute()
                
            price_map = {p['package_id']: p for p in prices.data}
            
            # Merge price info
            for pkg in packages_data:
                price_info = price_map.get(pkg['id'])
                if price_info:
                    pkg['price_monthly'] = price_info['price_monthly']
                    pkg['price_yearly'] = price_info['price_yearly']
                else:
                    # Fallback or indicate unavailable
                    pkg['price_monthly'] = None
                    pkg['price_yearly'] = None
                    
        return packages_data
        
    except Exception as e:
        logger.error(f"Error fetching packages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-price")
async def calculate_subscription_price(
    config: dict, # {assistants: int, storage_mb: int, ai_words: int, cycle: 'monthly'|'yearly'}
    user_id: str = Depends(get_current_user_id)
):
    """
    Calculate price for flexible package based on user's country
    حساب سعر الباقة المرنة
    """
    try:
        supabase = get_supabase_client()
        
        # 1. Get User Country
        user_res = supabase.table("users").select("country_id").eq("id", user_id).single().execute()
        country_id = user_res.data.get("country_id") if user_res.data else None
        
        if not country_id:
             # Fallback to default
             country_res = supabase.table("countries").select("id").eq("is_default", True).limit(1).execute()
             country_id = country_res.data[0].get("id") if country_res.data else None

            
        # 2. Get Pricing for Country
        pricing = None
        currency_info = {"currency": "USD", "currency_symbol": "$"}
        
        if country_id:
            # Get pricing and currency info
            pricing_res = supabase.table("country_pricing").select("*").eq("country_id", country_id).single().execute()
            pricing = pricing_res.data
            
            country_res = supabase.table("countries").select("currency, currency_symbol").eq("id", country_id).single().execute()
            if country_res.data:
                currency_info["currency"] = country_res.data.get("currency", "USD")
                currency_info["currency_symbol"] = country_res.data.get("currency_symbol", "$")
            
        if not pricing:
            # Fallback to global defaults if no country specific pricing
            pricing_res = supabase.table("subscription_pricing").select("*").limit(1).single().execute()
            pricing = pricing_res.data
            if pricing:
                currency_info["currency"] = pricing.get("currency", "USD")
                currency_info["currency_symbol"] = pricing.get("currency_symbol", "$")
            
        if not pricing:
            raise HTTPException(status_code=404, detail="Pricing configuration not found")

        # 3. Calculate
        assistants = max(0, int(config.get('assistants', 0)))
        
        # Base Fee
        base_fee = float(pricing.get('base_platform_fee', 0))
        
        # Assistants Cost
        assistants_cost = assistants * float(pricing.get('price_per_assistant', 0))
        
        # Storage Cost (Converted from price_per_gb_monthly)
        storage_mb = max(0, int(config.get('storage_mb', 0)))
        free_storage_gb = float(pricing.get('free_storage_gb', 0))
        billable_storage_gb = max(0, (storage_mb / 1024) - free_storage_gb)
        storage_cost = billable_storage_gb * float(pricing.get('price_per_gb_monthly', 0))
        
        # AI Cost
        ai_words = max(0, int(config.get('ai_words', 0)))
        free_words = float(pricing.get('free_words_monthly', 0))
        billable_words = max(0, ai_words - free_words)
        ai_cost = (billable_words / 1000) * float(pricing.get('price_per_1000_words', 0))
        
        total_monthly = base_fee + assistants_cost + storage_cost + ai_cost
        
        # Cycle Discount
        cycle = config.get('cycle', 'monthly')
        
        final_price = total_monthly
        if cycle == 'yearly':
            final_price = total_monthly * 12
            discount_percent = float(pricing.get('yearly_discount_percent', 0))
            discount_amount = final_price * (discount_percent / 100)
            final_price -= discount_amount
            
        return {
            "currency": currency_info["currency"],
            "currency_symbol": currency_info["currency_symbol"],
            "base_fee": base_fee,
            "assistants_cost": assistants_cost,
            "storage_cost": storage_cost,
            "ai_cost": ai_cost,
            "total_monthly": total_monthly,
            "final_price": round(final_price, 2),
            "cycle": cycle,
            "breakdown": {
                "assistants": assistants,
                "storage_mb": storage_mb,
                "ai_words": ai_words
            }
        }

    except Exception as e:
        logger.error(f"Error calculating price: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/request-renewal")
async def request_renewal(
    request: dict,
    user_id: str = Depends(get_current_user_id)
):
    """
    Submit a renewal request
    """
    try:
        logger.info(f"Renewal request from user {user_id}: {request}")
        supabase = get_supabase_client()
        package_id = request.get("package_id")
        custom_config = request.get("custom_config")
        
        # If package_id is 'flexible' (string), find the real UUID
        if package_id == 'flexible' or not package_id:
             pkg_res = supabase.table("subscription_packages").select("id").eq("is_flexible", True).single().execute()
             if pkg_res.data:
                 package_id = pkg_res.data['id']
        
        update_data = {
            "status": "renewal_requested",
            "updated_at": datetime.now().isoformat()
        }
        
        if package_id:
             update_data["package_id"] = package_id
             
        if custom_config:
            if 'assistants' in custom_config:
                update_data['extra_assistants'] = int(custom_config['assistants'])
            
            if 'storage_mb' in custom_config:
                  # Important: Convert MB from frontend to GB for DB storage
                  update_data['extra_storage_gb'] = round(float(custom_config['storage_mb']) / 1024, 4)
                 
            if 'ai_words' in custom_config:
                  update_data['extra_words'] = int(custom_config['ai_words'])

        logger.info(f"Updating lawyer_subscriptions with: {update_data}")
        
        result = supabase.table("lawyer_subscriptions")\
            .update(update_data)\
            .eq("lawyer_id", user_id)\
            .execute()
            
        if hasattr(result, 'error') and result.error:
            logger.error(f"Supabase error updating subscription: {result.error}")
            raise Exception(str(result.error))
            
        return {"message": "تم إرسال طلب التجديد بنجاح. سيقوم المسؤول بمراجعة طلبك وتفعيل الباقة."}
        
    except Exception as e:
        logger.error(f"Error requesting renewal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/payment-info")
async def get_payment_info(user_id: str = Depends(get_current_user_id)):
    """
    Get bank transfer information from platform settings
    جلب معلومات التحويل البنكي
    """
    try:
        supabase = get_supabase_client()
        
        # Get payment info from platform_settings
        settings = supabase.table("platform_settings").select("contact_phone, contact_email").limit(1).execute()
        contact = settings.data[0] if settings.data else {}
        
        return {
            "bank_name": "البنك الأهلي",  # Placeholder
            "account_number": "SA00000000000000000000", # Placeholder
            "iban": "SA00000000000000000000",
            "account_name": "شركة المحاماة الذكية",
            "contact_phone": contact.get('contact_phone', ''),
            "instructions": "يرجى تحويل المبلغ المستحق وإرسال إيصال التحويل عبر الواتساب أو البريد الإلكتروني مع ذكر اسم المكتب."
        }
        
    except Exception as e:
        logger.error(f"Error fetching payment info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
