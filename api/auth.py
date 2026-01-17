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
from supabase import create_client, Client

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Supabase client with SERVICE ROLE KEY (bypasses RLS for auth operations)
supabase: Client = create_client(
    settings.supabase_url, 
    settings.supabase_service_role_key  # Use service role for auth
)


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
    Register a new user
    تسجيل مستخدم جديد
    """
    try:
        # Check if email already exists
        existing = supabase.table("users").select("id").eq("email", request.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم بالفعل")
        
        # Get default role (lawyer)
        default_role = supabase.table("roles").select("id").eq("is_default", True).single().execute()
        if not default_role.data:
            raise HTTPException(status_code=500, detail="No default role found")
        
        # Get Egypt country if not provided
        country_id = request.country_id
        if not country_id:
            egypt = supabase.table("countries").select("id").eq("code", "EG").single().execute()
            country_id = egypt.data["id"] if egypt.data else None
        
        # Hash password
        password_hash = hash_password(request.password)
        
        # Create user
        user_data = {
            "email": request.email,
            "password_hash": password_hash,
            "full_name": request.full_name,
            "phone": request.phone,
            "country_id": country_id,
            "role_id": default_role.data["id"],
            "specialization": request.specialization,
            "license_number": request.license_number,
            "bio": request.bio,
            "is_active": True
        }
        
        result = supabase.table("users").insert(user_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        user = result.data[0]
        
        # Create JWT token
        access_token = create_access_token({"sub": user["id"]})
        
        # Return response
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
    Login user
    تسجيل دخول المستخدم
    """
    try:
        # Get user by email
        result = supabase.table("users").select("*").eq("email", request.email).execute()
        
        if not result.data:
            raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")
        
        user = result.data[0]
        
        # Verify password
        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="الحساب معطل")
        
        # Create JWT token
        access_token = create_access_token({"sub": user["id"]})
        
        # Update last_login
        supabase.table("users").update({"last_login": "now()"}).eq("id", user["id"]).execute()
        
        # Return response
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
        # Get user with relations
        result = supabase.table("users").select("""
            *,
            country:countries(id, name_ar, code, flag_emoji),
            role:roles(id, name, name_ar)
        """).eq("id", user_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return result.data
        
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
