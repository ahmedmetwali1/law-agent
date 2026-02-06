"""
Police Records API Router
Secure backend access for police records management
Replaces direct Supabase access from Frontend (PoliceRecordsPage.tsx)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from api.auth_middleware import get_current_user
from api.database import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/police-records", tags=["police-records"])


# --- Models ---

class PoliceRecordCreate(BaseModel):
    record_number: str
    record_year: Optional[str] = None
    record_type: Optional[str] = None
    police_station: Optional[str] = None
    complainant_name: Optional[str] = None
    accused_name: Optional[str] = None
    subject: Optional[str] = None
    decision: Optional[str] = None
    case_id: Optional[str] = None


class PoliceRecordUpdate(BaseModel):
    record_number: Optional[str] = None
    record_year: Optional[str] = None
    record_type: Optional[str] = None
    police_station: Optional[str] = None
    complainant_name: Optional[str] = None
    accused_name: Optional[str] = None
    subject: Optional[str] = None
    decision: Optional[str] = None


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

@router.get("")
async def get_police_records(
    search: Optional[str] = Query(None, description="Search query"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get all police records for current lawyer.
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)

        # Build query with case relation
        query = supabase.table('police_records')\
            .select('*, case:cases(case_number)')\
            .eq('user_id', lawyer_id)\
            .order('created_at', desc=True)

        result = query.execute()
        records = result.data or []

        # Apply search filter if provided (done client-side for flexibility)
        if search:
            search_lower = search.lower()
            records = [r for r in records if
                       search_lower in (r.get('record_number', '') or '').lower() or
                       search_lower in (r.get('police_station', '') or '').lower() or
                       search_lower in (r.get('complainant_name', '') or '').lower() or
                       search_lower in (r.get('accused_name', '') or '').lower()]

        return records

    except Exception as e:
        logger.error(f"❌ Failed to fetch police records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_police_record(
    record: PoliceRecordCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new police record"""
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)

        # Build record data - user_id from JWT, not frontend!
        record_data = {
            'record_number': record.record_number,
            'record_year': record.record_year or str(datetime.now().year),
            'record_type': record.record_type,
            'police_station': record.police_station,
            'complainant_name': record.complainant_name,
            'accused_name': record.accused_name,
            'subject': record.subject,
            'decision': record.decision,
            'case_id': record.case_id,
            'user_id': lawyer_id,  # Enforced from JWT
            'created_at': datetime.now().isoformat()
        }

        result = supabase.table('police_records').insert(record_data).execute()

        if not result.data:
            raise Exception("Failed to create police record")

        new_record = result.data[0]

        # Log audit
        log_audit(
            supabase, 'create', 'police_records', new_record['id'],
            current_user, lawyer_id,
            new_values=record_data,
            description='إضافة محضر شرطة'
        )

        logger.info(f"✅ Police record created: {new_record['id']} by {current_user['full_name']}")
        return new_record

    except Exception as e:
        logger.error(f"❌ Failed to create police record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{record_id}")
async def update_police_record(
    record_id: str,
    record: PoliceRecordUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update an existing police record"""
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)

        # Verify ownership
        existing = supabase.table('police_records')\
            .select('*')\
            .eq('id', record_id)\
            .eq('user_id', lawyer_id)\
            .execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Record not found or access denied")

        old_record = existing.data[0]

        # Build update data (only non-None fields)
        update_data = {k: v for k, v in record.dict().items() if v is not None}

        if not update_data:
            return old_record  # Nothing to update

        result = supabase.table('police_records')\
            .update(update_data)\
            .eq('id', record_id)\
            .execute()

        if not result.data:
            raise Exception("Failed to update police record")

        updated_record = result.data[0]

        # Log audit
        log_audit(
            supabase, 'update', 'police_records', record_id,
            current_user, lawyer_id,
            old_values=old_record,
            new_values=updated_record,
            description='تعديل محضر شرطة'
        )

        return updated_record

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update police record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{record_id}")
async def delete_police_record(
    record_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, bool]:
    """Delete a police record"""
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)

        # Verify ownership
        existing = supabase.table('police_records')\
            .select('*')\
            .eq('id', record_id)\
            .eq('user_id', lawyer_id)\
            .execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Record not found or access denied")

        old_record = existing.data[0]

        # Delete
        supabase.table('police_records').delete().eq('id', record_id).execute()

        # Log audit
        log_audit(
            supabase, 'delete', 'police_records', record_id,
            current_user, lawyer_id,
            old_values=old_record,
            description='حذف محضر شرطة'
        )

        logger.info(f"✅ Police record deleted: {record_id} by {current_user['full_name']}")
        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete police record: {e}")
        raise HTTPException(status_code=500, detail=str(e))
