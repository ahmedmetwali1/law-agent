"""
Audit Log API Router
Audit trail tracking for user actions
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from api.auth_middleware import get_current_user
from api.database import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])


class AuditLogCreate(BaseModel):
    """Request model for creating audit log entry"""
    action: str  # create, update, delete
    table_name: str
    record_id: str
    old_values: Optional[Dict] = None
    new_values: Optional[Dict] = None
    changes: Optional[Dict] = None
    description: str = ""


@router.post("/log")
async def create_audit_log(
    log: AuditLogCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> dict:
    """
    Create audit log entry
    
    Args:
        log: Audit log data including action, table, record_id, and changes
        
    Returns:
        Success status and log ID
    """
    try:
        supabase = get_supabase_client()
        
        logger.info(f"📝 Creating audit log: {log.action} on {log.table_name}/{log.record_id}")
        
        # Prepare log entry
        log_entry = {
            'action': log.action,
            'table_name': log.table_name,
            'record_id': log.record_id,
            'user_id': current_user['id'],
            'user_name': current_user.get('full_name'),
            'user_role': current_user.get('role'),
            'old_values': log.old_values,
            'new_values': log.new_values,
            'changes': log.changes,
            'lawyer_id': current_user['id'],
            'description': log.description or f"{log.action} on {log.table_name}"
        }
        
        # Insert into audit_logs table
        result = supabase.table('audit_logs')\
            .insert(log_entry)\
            .execute()
        
        if result.data:
            logger.info(f"✅ Audit log created: {result.data[0]['id']}")
            return {
                'success': True,
                'log_id': result.data[0]['id']
            }
        else:
            raise Exception("Failed to insert audit log")
        
    except Exception as e:
        logger.error(f"❌ Failed to create audit log: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create audit log: {str(e)}"
        )


@router.get("/logs")
async def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> dict:
    """
    Get audit logs for current lawyer
    
    Args:
        limit: Number of logs to return (default 50)
        offset: Pagination offset (default 0)
        
    Returns:
        List of audit log entries
    """
    try:
        lawyer_id = current_user['id']
        supabase = get_supabase_client()
        
        result = supabase.table('audit_logs')\
            .select('*')\
            .eq('lawyer_id', lawyer_id)\
            .order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return {
            'logs': result.data,
            'count': len(result.data)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch audit logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch audit logs: {str(e)}"
        )
