"""
Users API Router
User-related endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging

from api.auth_middleware import get_current_user
from api.database import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


# --- Models ---

class OfficeLawyerResponse(BaseModel):
    id: str
    full_name: str
    email: str


# --- Endpoints ---

@router.get("/office-lawyer", response_model=OfficeLawyerResponse)
async def get_office_lawyer(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> OfficeLawyerResponse:
    """
    Get office lawyer information for current assistant.
    Only assistants can access this endpoint.
    """
    try:
        # Only assistants can access this
        user_role = current_user.get('role_name') or (current_user.get('role') or {}).get('name')
        if user_role != 'assistant':
            raise HTTPException(status_code=403, detail="Only assistants can access this endpoint")
        
        office_id = current_user.get('office_id')
        if not office_id:
            raise HTTPException(status_code=404, detail="Office lawyer not found")
        
        supabase = get_supabase_client()
        
        result = supabase.table('users')\
            .select('id, full_name, email')\
            .eq('id', office_id)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Office lawyer not found")
        
        return OfficeLawyerResponse(**result.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch office lawyer: {e}")
        raise HTTPException(status_code=500, detail=str(e))
