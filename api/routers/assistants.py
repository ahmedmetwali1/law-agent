"""
Assistants API Router
Manage assistant accounts (lawyer-owned)
Replaces direct Supabase access from Frontend (AssistantsPage.tsx)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from api.auth_middleware import get_current_user
from api.database import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assistants", tags=["assistants"])


# --- Models ---

class AssistantLimitResponse(BaseModel):
    current_count: int
    max_limit: int
    remaining: int

class AssistantResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    created_at: str
    last_login: Optional[str] = None


class ToggleStatusRequest(BaseModel):
    is_active: bool

from pydantic import EmailStr
class CreateAssistantRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    office_id: str


# --- Helper Functions ---

def get_effective_lawyer_id(user: Dict[str, Any]) -> str:
    """Get effective lawyer_id from user context"""
    if user.get('role') == 'assistant':
        return user.get('office_id', user['id'])
    return user['id']


def log_audit(supabase, action: str, table: str, record_id: str,
              user: Dict[str, Any], lawyer_id: str,
              old_values: Any = None, new_values: Any = None,
              description: str = None):
    """Log action to audit_logs table"""
    try:
        changes = None
        if old_values and new_values and action == 'update':
            changes = {}
            for key in new_values:
                if key in old_values and old_values[key] != new_values[key]:
                    changes[key] = {'old': old_values[key], 'new': new_values[key]}

        audit_data = {
            'action': action,
            'table_name': table,
            'record_id': record_id,
            'user_id': user['id'],
            'user_name': user.get('full_name'),
            'user_role': user.get('role', 'lawyer'),
            'old_values': old_values,
            'new_values': new_values,
            'changes': changes,
            'description': description,
            'lawyer_id': lawyer_id,
            'created_at': datetime.now().isoformat()
        }

        supabase.table('audit_logs').insert(audit_data).execute()
    except Exception as e:
        logger.warning(f"Failed to log audit: {e}")


# --- Endpoints ---

@router.get("", response_model=List[AssistantResponse])
async def get_assistants(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[AssistantResponse]:
    """
    Get list of assistants for current lawyer.
    Only lawyers can access this endpoint.
    """
    try:
        # Only lawyers can view their assistants
        user_role = current_user.get('role_name') or (current_user.get('role') or {}).get('name')
        if user_role not in ['lawyer', 'admin']:
            raise HTTPException(status_code=403, detail="Only lawyers and admins can view assistants")
        
        supabase = get_supabase_client()
        lawyer_id = current_user['id']
        
        result = supabase.table('users')\
            .select('id, email, full_name, phone, is_active, created_at, last_login')\
            .eq('office_id', lawyer_id)\
            .eq('role', 'assistant')\
            .order('created_at', desc=True)\
            .execute()
        
        assistants = result.data or []
        
        return [AssistantResponse(**assistant) for assistant in assistants]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch assistants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(
    assistant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AssistantResponse:
    """Get details of a specific assistant"""
    try:
        # Only lawyers can view assistant details
        user_role = current_user.get('role_name') or (current_user.get('role') or {}).get('name')
        if user_role not in ['lawyer', 'admin']:
            raise HTTPException(status_code=403, detail="Only lawyers and admins can view assistant details")
        
        supabase = get_supabase_client()
        lawyer_id = current_user['id']
        
        # Verify ownership
        result = supabase.table('users')\
            .select('id, email, full_name, phone, is_active, created_at, last_login')\
            .eq('id', assistant_id)\
            .eq('office_id', lawyer_id)\
            .eq('role', 'assistant')\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Assistant not found or access denied")
        
        return AssistantResponse(**result.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{assistant_id}/toggle-status", response_model=AssistantResponse)
async def toggle_assistant_status(
    assistant_id: str,
    status_update: ToggleStatusRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AssistantResponse:
    """
    Toggle assistant account active status.
    Only lawyers can toggle their assistants' status.
    """
    try:
        # Only lawyers can toggle assistant status
        user_role = current_user.get('role_name') or (current_user.get('role') or {}).get('name')
        if user_role not in ['lawyer', 'admin']:
            raise HTTPException(status_code=403, detail="Only lawyers and admins can toggle assistant status")
        
        supabase = get_supabase_client()
        lawyer_id = current_user['id']
        
        # Verify ownership
        existing = supabase.table('users')\
            .select('*')\
            .eq('id', assistant_id)\
            .eq('office_id', lawyer_id)\
            .eq('role', 'assistant')\
            .single()\
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Assistant not found or access denied")
        
        old_assistant = existing.data
        
        # Update status
        update_data = {'is_active': status_update.is_active}
        
        result = supabase.table('users')\
            .update(update_data)\
            .eq('id', assistant_id)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update assistant status")
        
        updated_assistant = result.data[0]
        
        # Log audit
        log_audit(
            supabase, 'update', 'users', assistant_id,
            current_user, lawyer_id,
            old_values=old_assistant,
            new_values=updated_assistant,
            description=f"تغيير حالة المساعد إلى {'مفعّل' if status_update.is_active else 'معطّل'}"
        )
        
        logger.info(f"✅ Assistant status toggled: {assistant_id} -> {status_update.is_active}")
        
        return AssistantResponse(**updated_assistant)
        
    except Exception as e:
        logger.error(f"❌ Failed to toggle assistant status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_assistant(request: CreateAssistantRequest):
    """إنشاء مساعد جديد (Secure via Supabase Auth)"""
    try:
        # 1. Check Subscription Limits
        from api.utils.subscription_enforcement import check_assistant_limit
        await check_assistant_limit(request.office_id)
        
        # 2. Get Lawyer Data
        from agents.storage.user_storage import user_storage
        lawyer = user_storage.get_user_by_id(request.office_id)
        if not lawyer:
            raise HTTPException(status_code=404, detail="Lawyer not found")

        # 3. Create User in Supabase Auth (Identity Provider)
        from api.services.admin_service import admin_service
        try:
            auth_user = admin_service.create_user(
                email=request.email,
                password=request.password,
                user_metadata={
                    "full_name": request.full_name,
                    "role": "assistant",
                    "office_id": request.office_id
                }
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # 4. Create Profile in Public Schema (Linked by ID)
        supabase = get_supabase_client()
        
        new_assistant_profile = {
            'id': auth_user.id, # Link to Auth User
            'email': request.email,
            'full_name': request.full_name,
            'phone': request.phone,
            'role': 'assistant',
            'office_id': request.office_id,
            'role_id': 'e3fedef1-5387-4d6d-a90b-6bb8ed45e5f2',
            'is_active': True,
            # Inherit Office Settings
            'country_id': lawyer.get('country_id'),
            'office_address': lawyer.get('office_address'),
            'office_city': lawyer.get('office_city'),
            'office_postal_code': lawyer.get('office_postal_code'),
            'timezone': lawyer.get('timezone', 'Africa/Cairo'),
            'business_hours': lawyer.get('business_hours'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Insert profile
        result = supabase.table('users').insert(new_assistant_profile).execute()
        
        # 5. Update Statistics
        try:
             supabase.table("lawyer_subscriptions")\
                 .update({"assistants_count": supabase.table("users").select("count").eq("office_id", request.office_id).count().data or 1})\
                 .eq("lawyer_id", request.office_id)\
                 .execute()
        except Exception:
             pass 

        if not result.data:
            # Rollback
            admin_service.delete_user(auth_user.id)
            raise Exception("Failed to create assistant profile")
        
        return {"message": "تم إنشاء المساعد بنجاح", "assistant_id": result.data[0]['id']}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/limit", response_model=AssistantLimitResponse)
async def get_assistants_limit(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AssistantLimitResponse:
    """
    Get the current assistant count and maximum allowed for the lawyer.
    """
    try:
        lawyer_id = get_effective_lawyer_id(current_user)
        supabase = get_supabase_client()
        
        result = supabase.table("lawyer_subscriptions")\
            .select("assistants_count, package:subscription_packages(max_assistants), extra_assistants")\
            .eq("lawyer_id", lawyer_id)\
            .single().execute()
            
        if not result.data:
            raise HTTPException(status_code=403, detail="No subscription found")
            
        sub = result.data
        current_count = sub.get('assistants_count', 0)
        base_limit = sub.get('package', {}).get('max_assistants', 0)
        extra = sub.get('extra_assistants', 0)
        max_limit = base_limit + extra
        
        return AssistantLimitResponse(
            current_count=current_count,
            max_limit=max_limit,
            remaining=max(0, max_limit - current_count)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assistant limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete an assistant (Profile + Auth Identity).
    Only lawyers can delete their assistants.
    """
    try:
        # Only lawyers can delete assistants
        user_role = current_user.get('role_name') or (current_user.get('role') or {}).get('name')
        if user_role not in ['lawyer', 'admin']:
            raise HTTPException(status_code=403, detail="Only lawyers and admins can delete assistants")
        
        supabase = get_supabase_client()
        lawyer_id = current_user['id']
        
        # 1. Verify ownership and get data for audit
        existing = supabase.table('users')\
            .select('*')\
            .eq('id', assistant_id)\
            .eq('office_id', lawyer_id)\
            .eq('role', 'assistant')\
            .single()\
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Assistant not found or access denied")
        
        old_assistant = existing.data
        
        # 2. Delete from Supabase Auth
        from api.services.admin_service import admin_service
        auth_deleted = admin_service.delete_user(assistant_id)
        if not auth_deleted:
            # We continue even if auth delete fails? 
            # Or block? Better to block if it's a security/identity risk.
            # But sometimes auth user is already gone. 
            logger.warning(f"Auth deletion failed for {assistant_id}, proceeding with profile deletion.")
        
        # 3. Delete from Public Schema
        supabase.table('users').delete().eq('id', assistant_id).execute()
        
        # 4. Update Statistics in lawyer_subscriptions
        try:
             count_result = supabase.table("users")\
                 .select("id", count="exact")\
                 .eq("office_id", lawyer_id)\
                 .eq("role", "assistant")\
                 .execute()
             
             new_count = count_result.count if count_result.count is not None else 0
             
             supabase.table("lawyer_subscriptions")\
                 .update({"assistants_count": new_count})\
                 .eq("lawyer_id", lawyer_id)\
                 .execute()
        except Exception as e:
             logger.warning(f"Failed to update assistants_count: {e}")

        # 5. Log audit
        log_audit(
            supabase, 'delete', 'users', assistant_id,
            current_user, lawyer_id,
            old_values=old_assistant,
            description=f"حذف المساعد: {old_assistant.get('full_name')}"
        )
        
        logger.info(f"✅ Assistant deleted: {assistant_id}")
        
        return {"message": "تم حذف المساعد بنجاح"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))
