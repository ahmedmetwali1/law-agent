"""
Authentication Middleware
JWT Token Verification and User Authentication
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging
import os

from agents.storage.user_storage import user_storage

logger = logging.getLogger(__name__)

# --- Performance: User Cache ---
class UserCache:
    """Simple in-memory cache for user data to prevent N+1 DB calls"""
    def __init__(self, ttl_minutes: int = 5):
        self._cache = {}
        self._ttl = timedelta(minutes=ttl_minutes)
    
    def get(self, user_id: str) -> Optional[Dict[str, Any]]:
        if user_id in self._cache:
            data, timestamp = self._cache[user_id]
            if datetime.utcnow() - timestamp < self._ttl:
                return data
            else:
                del self._cache[user_id] # Expired
        return None
    
    def set(self, user_id: str, data: Dict[str, Any]):
        self._cache[user_id] = (data, datetime.utcnow())
        
    def invalidate(self, user_id: str):
        if user_id in self._cache:
            del self._cache[user_id]

# Global user cache instance
user_cache = UserCache()

# Security configurations
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production-min-32-chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload data (user_id, email, role, etc.)
        expires_delta: Token expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


from agents.config.database import get_supabase_client

# ... (Previous imports kept)

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Local decode mainly for extracting claims without verification,
    or we can verify if we have the Supabase JWT Secret.
    However, the Source of Truth is Supabase Auth.
    """
    try:
        # Try to decode unverified just to get the 'sub' if needed quickly, 
        # BUT for security we will rely on supabase.auth.get_user() in the dependency.
        # If strict local validation is needed, we need SUPABASE_JWT_SECRET env var.
        
        # NOTE: Assuming SECRET_KEY in env is now the SUPABASE_JWT_SECRET
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": True})
        return payload
    except JWTError:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current authenticated user via Supabase Auth.
    Verifies the token with Supabase and fetches the profile.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    supabase = get_supabase_client()
    
    try:
        # 1. OPTIMIZED: Try Local Decode First (Faster & Supports Custom Auth)
        # Using verify_token=True ensures we trust the signature if it matches our SECRET_KEY
        payload = decode_token(token)
        
        user_id = None
        
        if payload and payload.get("sub"):
            # Valid Local Token found
            user_id = payload.get("sub")
            # Check expiration manually if decode_token doesn't throw
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                 user_id = None # Expired

        # 2. Fallback: Verify Token with Supabase Auth (If local decode failed or external token)
        if not user_id:
            try:
                user_response = supabase.auth.get_user(token)
                if user_response.user:
                    user_id = user_response.user.id
            except Exception:
                pass # Supabase check failed
        
        if not user_id:
             raise credentials_exception

        # 3. Check Cache
        cached_user = user_cache.get(user_id)
        if cached_user:
            return cached_user

        # 4. Get Full Profile from Database
        # Verify user exists in our profile table and get their Role
        user = user_storage.get_user_by_id(user_id)
        if user is None:
            # Maybe user exists in auth but not public table
            raise credentials_exception
            
        # 5. Cache and Return
        user_cache.set(user_id, user)
        
        if not user.get("is_active", False):
            raise HTTPException(status_code=403, detail="User account is inactive")
            
        return user
        
    except Exception as e:
        logger.warning(f"Auth verification failed: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current active user (alias for get_current_user)
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        User data
    """
    return current_user


def require_role(allowed_roles: list):
    """
    Dependency factory to require specific roles
    
    Usage:
        @app.get("/admin")
        async def admin_route(user: dict = Depends(require_role(["admin"]))):
            ...
    
    Args:
        allowed_roles: List of allowed role names
        \n    Returns:
        Dependency function
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user_role}' is not authorized for this action"
            )
        return current_user
    
    return role_checker


async def get_current_manager(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user and verify Admin role via role_id
    
    This dependency ensures that only users with admin role_id can access
    the Super Admin Dashboard endpoints.
    
    Admin role_id: e2d8b2c0-7b8d-4b46-88e8-cb0071467901
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User data if user is Admin
        
    Raises:
        HTTPException 403: If user is not Admin
    """
    # Admin role_id from roles table
    ADMIN_ROLE_ID = "e2d8b2c0-7b8d-4b46-88e8-cb0071467901"
    
    user_role_id = current_user.get("role_id")
    user_role = current_user.get("role")
    
    # Check by role_id first (preferred), then fallback to role name
    is_admin = (user_role_id == ADMIN_ROLE_ID) or (user_role == "admin")
    
    if not is_admin:
        logger.warning(
            f"❌ Unauthorized Admin access attempt by {current_user.get('full_name')} "
            f"(role_id: {user_role_id}, role: {user_role})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required for this action."
        )
    
    logger.info(f"✅ Admin access granted: {current_user.get('full_name')}")
    return current_user



async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, otherwise return None
    
    This allows endpoints to support both authenticated and non-authenticated access.
    Useful for chat endpoints that should work for both logged-in users and guests.
    
    Args:
        credentials: HTTP Bearer credentials (optional)
        
    Returns:
        User data dict if authenticated, None otherwise
    """
    if credentials is None:
        # No credentials provided - anonymous access
        logger.info("Anonymous access - no authentication token provided")
        return None
    
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    if payload is None:
        # Invalid token - treat as anonymous
        logger.warning("Invalid token - treating as anonymous")
        return None
    
    user_id: str = payload.get("sub")
    if user_id is None:
        return None
    
    # Get user from database
    user = user_storage.get_user_by_id(user_id)
    if user is None:
        logger.warning(f"User {user_id} not found in database")
        return None
    
    # Check if user is active
    if not user.get("is_active", False):
        logger.warning(f"User {user_id} account is inactive")
        return None
    
    # Remove sensitive data
    user.pop("password_hash", None)
    
    logger.info(f"Authenticated user: {user.get('full_name')} ({user_id})")
    return user


__all__ = [
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_token",
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    "get_current_manager",
    "require_role",
    "get_current_user_id"
]

async def get_current_user_id(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    Get current user ID directly
    """
    return current_user["id"]
