import logging
from typing import Dict, Any, Optional
from supabase import Client
from gotrue.errors import AuthApiError

from agents.config.database import get_supabase_client
from agents.config.settings import settings

logger = logging.getLogger(__name__)

class SupabaseAdminService:
    """
    Secure Admin Service for managing Supabase Auth identities.
    Uses the SERVICE_ROLE_KEY to perform privileged actions (creating users, deleting users).
    """

    def __init__(self):
        # We need the service role client which is already initialized in database.py
        # assuming settings.supabase_service_role_key is used there.
        self.client: Client = get_supabase_client()
        self.auth = self.client.auth.admin

    def create_user(self, email: str, password: str, user_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a user in Supabase Auth (auth.users).
        
        Args:
            email: User email
            password: User password (will be hashed by Supabase)
            user_metadata: Optional metadata (full_name, role, etc.)
            
        Returns:
            Created user object (properties: id, email, ...)
        """
        try:
            logger.info(f"Creating Supabase Auth user: {email}")
            user_metadata = user_metadata or {}
            
            # auto_confirm_email=True to skip email verification for manually created assistants
            attributes = {
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": user_metadata
            }
            
            user = self.auth.create_user(attributes)
            logger.info(f"✅ Successfully created Auth user: {user.user.id}")
            return user.user
            
        except AuthApiError as e:
            logger.error(f"❌ Supabase Auth Error: {e.message}")
            raise ValueError(f"Auth Error: {e.message}")
        except Exception as e:
            logger.error(f"❌ Unexpected Error creating user: {str(e)}")
            raise e

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user from Supabase Auth.
        """
        try:
            self.auth.delete_user(user_id)
            logger.info(f"✅ Deleted Auth user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete auth user: {e}")
            return False

# Singleton
admin_service = SupabaseAdminService()
