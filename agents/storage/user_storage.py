"""
User Storage Module
إدارة المستخدمين في قاعدة البيانات
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging
from supabase import Client

from agents.config.settings import settings, TableNames
from agents.config.database import get_supabase_client

logger = logging.getLogger(__name__)


class UserStorage:
    """User database operations"""
    
    TABLE_NAME = TableNames.USERS
    
    def __init__(self):
        """Initialize user storage"""
        self.client: Client = get_supabase_client()
        logger.info("✅ UserStorage initialized")
    
    def create_user(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        phone: Optional[str] = None,
        role: str = "assistant"
    ) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            email: User email (unique)
            password_hash: Hashed password
            full_name: User's full name
            phone: Phone number (optional)
            role: User role (default: assistant)
            
        Returns:
            Created user data
        """
        try:
            user_data = {
                "email": email,
                "password_hash": password_hash,
                "full_name": full_name,
                "phone": phone,
                "role": role,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.client.table(self.TABLE_NAME).insert(user_data).execute()
            
            if result.data:
                logger.info(f"✅ User created: {email}")
                return result.data[0]
            else:
                raise Exception("Failed to create user")
                
        except Exception as e:
            logger.error(f"❌ Failed to create user: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email
        
        Args:
            email: User email
            
        Returns:
            User data or None
        """
        try:
            result = self.client.table(self.TABLE_NAME)\
                .select("*")\
                .eq("email", email)\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.debug(f"User not found: {email}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID with role information
        
        Args:
            user_id: User UUID
            
        Returns:
            User data with role or None
        """
        try:
            # ✅ Include role relation for authentication checks
            result = self.client.table(self.TABLE_NAME)\
                .select("*, role:roles(id, name, name_ar, permissions)")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if result.data:
                # Flatten role for easier access
                user = result.data
                if user.get('role') and isinstance(user['role'], dict):
                    # Add role name directly to user dict for easier access
                    user['role_name'] = user['role'].get('name')
                return user
            return None
            
        except Exception as e:
            logger.debug(f"User not found: {user_id}")
            return None
    
    def update_last_login(self, user_id: str) -> bool:
        """
        Update user's last login timestamp
        
        Args:
            user_id: User UUID
            
        Returns:
            Success status
        """
        try:
            result = self.client.table(self.TABLE_NAME)\
                .update({"last_login": datetime.now().isoformat()})\
                .eq("id", user_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"❌ Failed to update last login: {e}")
            return False
    
    def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update user data
        
        Args:
            user_id: User UUID
            updates: Fields to update
            
        Returns:
            Updated user data
        """
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.now().isoformat()
            
            result = self.client.table(self.TABLE_NAME)\
                .update(updates)\
                .eq("id", user_id)\
                .execute()
            
            if result.data:
                logger.info(f"✅ User updated: {user_id}")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to update user: {e}")
            raise
    
    def check_email_exists(self, email: str) -> bool:
        """
        Check if email already exists
        
        Args:
            email: Email to check
            
        Returns:
            True if exists
        """
        user = self.get_user_by_email(email)
        return user is not None
    
    def check_phone_exists(self, phone: str) -> bool:
        """
        Check if phone already exists
        
        Args:
            phone: Phone to check
            
        Returns:
            True if exists
        """
        try:
            result = self.client.table(self.TABLE_NAME)\
                .select("id")\
                .eq("phone", phone)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            return False


# Global instance
user_storage = UserStorage()


__all__ = ["UserStorage", "user_storage"]
