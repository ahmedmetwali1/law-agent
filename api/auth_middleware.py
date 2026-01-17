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


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token
    
    This is a FastAPI dependency that:
    1. Extracts the Bearer token from Authorization header
    2. Decodes and verifies the token
    3. Fetches the user from database
    4. Returns user data
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User data dict
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    user = user_storage.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Remove sensitive data
    user.pop("password_hash", None)
    
    return user


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
