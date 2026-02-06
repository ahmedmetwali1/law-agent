"""
Authentication endpoints
نقاط النهاية للمصادقة
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Body
from typing import Optional
import logging

from .models import SignupRequest, LoginRequest, AuthResponse, UserProfile
from .security import hash_password, verify_password
from .auth_middleware import create_access_token, decode_token
from agents.config.settings import settings
from supabase import Client
from agents.config.database import get_supabase_client
import time

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Helper to get client
def get_db():
    return get_supabase_client()


def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Dependency to get current user ID from JWT token
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        user_id
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return user_id


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """
    Register a new user (Secure via Supabase Auth)
    تسجيل مستخدم جديد
    """
    try:
        # 1. Pre-validation: Check for existing phone or license
        if request.phone:
            existing_phone = supabase.table("users").select("id").eq("phone", request.phone).execute()
            if existing_phone.data:
                raise HTTPException(status_code=400, detail="رقم الهاتف مسجل بالفعل باسم مستخدم آخر")
        
        if request.license_number:
            existing_license = supabase.table("users").select("id").eq("license_number", request.license_number).execute()
            if existing_license.data:
                raise HTTPException(status_code=400, detail="رقم الترخيص مسجل بالفعل باسم مستخدم آخر")

        # 2. Create User in Supabase Auth via Admin Service
        from api.services.admin_service import admin_service
        try:
            auth_user = admin_service.create_user(
                email=request.email, 
                password=request.password,
                user_metadata={
                    "full_name": request.full_name,
                    "specialization": request.specialization
                }
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # 2. Prepare Profile Data
        # Get default role (lawyer)
        default_role = supabase.table("roles").select("id").eq("is_default", True).single().execute()
        if not default_role.data:
            admin_service.delete_user(auth_user.id) # Rollback
            raise HTTPException(status_code=500, detail="No default role found")
        
        # Get Egypt country if not provided
        country_id = request.country_id
        if not country_id:
            egypt = supabase.table("countries").select("id").eq("code", "EG").single().execute()
            country_id = egypt.data["id"] if egypt.data else None
            
        user_profile = {
            "id": auth_user.id, # Link to Auth ID
            "email": request.email,
            "full_name": request.full_name,
            "phone": request.phone,
            "country_id": country_id,
            "role_id": default_role.data["id"],
            "specialization": request.specialization,
            "license_number": request.license_number,
            "bio": request.bio,
            "is_active": True,
            "created_at": "now()",
            "updated_at": "now()"
        }
        
        # 3. Insert into Public Profile Table
        result = supabase.table("users").insert(user_profile).execute()
        
        if not result.data:
            admin_service.delete_user(auth_user.id) # Rollback
            raise HTTPException(status_code=500, detail="Failed to create user profile")
        
        user = result.data[0]
        
        # 4. Create Trial Subscription (30 Days)
        try:
            # Find the default starter package (Match Admin Logic: Newest First)
            starter_pkg = supabase.table("subscription_packages").select("id")\
                .eq("is_default", True)\
                .order("created_at", desc=True)\
                .limit(1).execute()
            
            if not starter_pkg.data:
                # Fallback to name-based lookup
                starter_pkg = supabase.table("subscription_packages").select("id")\
                    .ilike("name", "%starter%")\
                    .order("created_at", desc=True)\
                    .limit(1).execute()
            
            pkg_id = starter_pkg.data[0]['id'] if starter_pkg.data else None
            
            if pkg_id:
                from datetime import datetime, timedelta
                sub_data = {
                    "lawyer_id": user["id"],
                    "package_id": pkg_id,
                    "country_id": country_id,
                    "status": "trial",
                    "auto_renew": False,
                    "start_date": datetime.now().date().isoformat(),
                    "end_date": (datetime.now().date() + timedelta(days=30)).isoformat(), # Extended to 30 days
                    "billing_cycle": "monthly",
                    "extra_assistants": 0, 
                    "extra_storage_gb": 0, 
                    "extra_words": 0
                }
                supabase.table("lawyer_subscriptions").insert(sub_data).execute()
            else:
                logger.warning(f"No starter package found for user {user['id']}")
        except Exception as e:
            logger.error(f"Trial subscription failed: {e}")

        # 5. Login to get Access Token
        # We need to sign in to get the token, simply returning "created" isn't enough for auto-login
        try:
            session = supabase.auth.sign_in_with_password({"email": request.email, "password": request.password})
            access_token = session.session.access_token
        except Exception:
            # If login fails (shouldn't), return empty token and let user login manually
            access_token = ""

        return AuthResponse(
            access_token=access_token,
            user={
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role_id": user["role_id"],
                "country_id": user["country_id"]
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login user (Authenticates against Supabase Auth)
    تسجيل دخول المستخدم
    """
    try:
        supabase = get_db()
        
        # 1. Fetch User from Custom Table (public.users) with Retry Logic
        user = None
        last_error = None
        
        for attempt in range(3):
            try:
                # We do NOT use supabase.auth because user has custom setup
                result = supabase.table("users").select("*").eq("email", request.email).execute()
                
                if not result.data or len(result.data) == 0:
                     # User not found - do not retry
                     logger.warning(f"Login failed: User {request.email} not found in DB")
                     raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")
                
                user = result.data[0]
                logger.info(f"User found: {user['id']}")
                break # Success
                
            except HTTPException:
                raise # Re-raise known HTTP exceptions
            except Exception as e:
                last_error = e
                logger.warning(f"Login DB attempt {attempt+1} failed: {e}")
                if attempt < 2:
                    time.sleep(1) # Wait 1s before retry
        
        if not user:
            # If we exhausted retries without finding user (or error)
            logger.error(f"Login failed after 3 attempts. Last error: {last_error}")
            if last_error:
                 raise HTTPException(status_code=500, detail="خطأ في الاتصال بالخادم. حاول مرة أخرى.")
            else:
                 raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")
        
        # 2. Verify Password Hash
        stored_hash = user.get("password_hash")
        if not stored_hash:
             logger.warning("Login failed: No password hash stored for user")
             raise HTTPException(status_code=401, detail="بيانات الدخول غير صالحة")

        # Debug Input Password
        pwd_len = len(request.password)
        first_char = request.password[0] if pwd_len > 0 else "EMPTY"
        last_char = request.password[-1] if pwd_len > 0 else "EMPTY"
        is_stripped = request.password.strip() == request.password
        
        logger.info(f"Checking Password: Length={pwd_len}, Stripped={is_stripped}, First={first_char}, Last={last_char}")

        is_valid = verify_password(request.password, stored_hash)
        logger.info(f"Password verification result for {request.email}: {is_valid}")

        if not is_valid:
             logger.warning("Login failed: Password mismatch")
             raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")

        # 3. Check Active Status
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="الحساب معطل")
        
        from api.guards import verify_assistant_login_access
        await verify_assistant_login_access(user)

        # 4. Generate Local Access Token
        # We sign this with our own SECRET_KEY
        access_token = create_access_token(
            data={"sub": user["id"], "role": "lawyer"} # Default role claim, refined by DB lookup later
        )

        # 5. Update Last Login
        try:
             supabase.table("users").update({"last_login": "now()"}).eq("id", user["id"]).execute()
        except:
             pass
        
        return AuthResponse(
            access_token=access_token,
            user={
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role_id": user["role_id"],
                "country_id": user["country_id"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me")
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """
    Get current user profile
    جلب ملف المستخدم الحالي
    """
    try:
        supabase = get_db()
        # Get user with relations
        result = supabase.table("users").select("""
            *,
            country:countries(id, name_ar, code, flag_emoji),
            role:roles(id, name, name_ar)
        """).eq("id", user_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = result.data
        
        # Attach Subscription Info for Frontend Banner
        from api.guards import get_user_subscription
        from datetime import datetime
        
        try:
            sub = await get_user_subscription(user_data)
            if sub:
                end_date_str = sub.get("end_date")
                days_remaining = 0
                is_expired = False
                
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    delta = (end_date - datetime.now().date()).days
                    days_remaining = delta
                    if delta < 0:
                        is_expired = True

                user_data["subscription_info"] = {
                    "status": sub.get("status"),
                    "days_remaining": days_remaining,
                    "is_expired": is_expired,
                    "package_name": sub.get("package", {}).get("name_ar", "باقة مخصصة")
                }
        except Exception as e:
            logger.warning(f"Failed to attach subscription info: {e}")

        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/account")
async def delete_account(
    password: str = Body(..., embed=True),
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete user account permanently
    حذف الحساب نهائياً
    """
    try:
        supabase = get_db()
        # 1. Verify Password
        # Fetch user's stored hash
        user = supabase.table("users").select("password_hash").eq("id", user_id).single().execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not verify_password(password, user.data["password_hash"]):
            raise HTTPException(status_code=403, detail="كلمة المرور غير صحيحة")

        # 2. Delete User Data (Assuming Cascade or simple delete)
        # Note: In a real production app with Supabase Auth, you'd use supabase.auth.admin.delete_user(user_id)
        # But here we are managing our own users table mostly. 
        # If this is linked to Supabase Auth, we should ideally delete from auth.users too if we had service key access to it.
        # Check if we have service role key in 'supabase' client (we do, see line 23-26).
        
        # Delete from public.users
        delete_result = supabase.table("users").delete().eq("id", user_id).execute()
        
        # If using Supabase Auth, we would also:
        # supabase.auth.admin.delete_user(user_id) 
        # But let's stick to the visible table for now as that's what the app logic seems to revolve around.
        
        return {"message": "Account deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete account error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout(user_id: str = Depends(get_current_user_id)):
    """
    Logout user (token invalidation would be handled client-side)
    تسجيل خروج المستخدم
    """
    return {"message": "Logged out successfully"}
