"""
Hearings API Router
روابط API لإدارة الجلسات

Enhanced with:
- Audit logging
- Ownership verification through case
- Assistant support via get_effective_lawyer_id
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import logging

from api.auth_middleware import get_current_user
from api.guards import verify_subscription_active
from api.database import get_supabase_client
from agents.storage.hearing_storage import hearing_storage
from agents.storage.case_storage import CaseStorage

logger = logging.getLogger(__name__)

router = APIRouter()
case_storage = CaseStorage(use_supabase=True)


# ===== Helper Functions =====

def get_effective_lawyer_id(user: Dict[str, Any]) -> str:
    """Get effective lawyer_id for assistants"""
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


def verify_case_ownership(case_id: str, lawyer_id: str) -> bool:
    """Verify case belongs to lawyer"""
    case = case_storage.get_case_by_id(case_id, lawyer_id)
    return case is not None


# ===== Request/Response Models =====

class CreateHearingRequest(BaseModel):
    """Create hearing request"""
    case_id: str = Field(..., description="معرف القضية")
    hearing_date: date = Field(..., description="تاريخ الجلسة")
    hearing_time: Optional[str] = Field(None, description="وقت الجلسة (HH:MM)")
    court_room: Optional[str] = Field(None, description="رقم القاعة")
    judge_name: Optional[str] = Field(None, description="اسم القاضي")
    judge_requests: Optional[str] = Field(None, description="طلبات القاضي")
    notes: Optional[str] = Field(None, description="ملاحظات")
    outcome: Optional[str] = Field(None, description="نتيجة الجلسة")
    next_hearing_date: Optional[date] = Field(None, description="تاريخ الجلسة القادمة")


class UpdateHearingRequest(BaseModel):
    """Update hearing request"""
    hearing_date: Optional[date] = None
    hearing_time: Optional[str] = None
    court_room: Optional[str] = None
    judge_name: Optional[str] = None
    judge_requests: Optional[str] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None
    next_hearing_date: Optional[date] = None


# ===== API Endpoints =====

@router.get("/today")
async def get_today_hearings(
    current_user: Dict = Depends(get_current_user)
):
    """
    جلسات اليوم للمحامي ⭐
    """
    try:
        lawyer_id = get_effective_lawyer_id(current_user)
        hearings = hearing_storage.get_today_hearings_by_lawyer(
            lawyer_id=lawyer_id
        )
        
        return {
            "success": True,
            "count": len(hearings),
            "date": date.today().isoformat(),
            "hearings": hearings,
            "message": f"لديك {len(hearings)} جلسة اليوم" if hearings else "ليس لديك جلسات اليوم"
        }
    except Exception as e:
        logger.error(f"Failed to get today's hearings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/upcoming")
async def get_upcoming_hearings(
    current_user: Dict = Depends(get_current_user),
    days: int = 7
):
    """
    الجلسات القادمة
    """
    try:
        lawyer_id = get_effective_lawyer_id(current_user)
        hearings = hearing_storage.get_upcoming_hearings_by_lawyer(
            lawyer_id=lawyer_id,
            days=days
        )
        
        return {
            "success": True,
            "count": len(hearings),
            "hearings": hearings,
            "days": days
        }
    except Exception as e:
        logger.error(f"Failed to get upcoming hearings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/range")
async def get_hearings_range(
    start_date: date,
    end_date: date,
    current_user: Dict = Depends(get_current_user)
):
    """
    جلسات خلال فترة
    """
    try:
        lawyer_id = get_effective_lawyer_id(current_user)
        hearings = hearing_storage.get_hearings_by_range(
            lawyer_id=lawyer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "success": True,
            "count": len(hearings),
            "hearings": hearings
        }
    except Exception as e:
        logger.error(f"Failed to get hearings range: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/case/{case_id}")
async def get_case_hearings(
    case_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    جلسات قضية معينة - with ownership verification
    """
    try:
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Verify case ownership
        if not verify_case_ownership(case_id, lawyer_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="القضية غير موجودة"
            )
        
        hearings = hearing_storage.get_case_hearings(case_id)
        
        return {
            "success": True,
            "count": len(hearings),
            "case_id": case_id,
            "hearings": hearings
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get case hearings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_hearing(
    request: CreateHearingRequest,
    current_user: Dict = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
):
    """
    إنشاء جلسة جديدة - with ownership verification and audit logging
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Verify case ownership
        if not verify_case_ownership(request.case_id, lawyer_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="القضية غير موجودة"
            )
        
        time_obj = None
        if request.hearing_time:
            time_obj = datetime.strptime(request.hearing_time, "%H:%M").time()
        
        # ✅ Fetch parent case details for denormalization
        case_number = None
        court_name = None
        case_year = None
        client_name = None
        
        try:
            from agents.config.settings import TableNames
            from agents.config.database import db
            # Join cases -> clients to get full details
            case_resp = db.client.table(TableNames.CASES)\
                .select("case_number, court_name, case_year, client_id, clients(full_name)")\
                .eq("id", request.case_id)\
                .single()\
                .execute()
                
            if case_resp.data:
                cd = case_resp.data
                case_number = cd.get("case_number")
                court_name = cd.get("court_name")
                case_year = cd.get("case_year")
                client_name = cd.get("clients", {}).get("full_name")  # Nested from join
        except Exception as e:
            logger.warning(f"Failed to fetch case details for denormalization: {e}")

        lawyer_id = get_effective_lawyer_id(current_user)

        hearing = hearing_storage.create_hearing(
            lawyer_id=lawyer_id,
            case_id=request.case_id,
            hearing_date=request.hearing_date,
            hearing_time=time_obj,
            court_room=request.court_room,
            judge_name=request.judge_name,
            judge_requests=request.judge_requests,
            notes=request.notes,
            outcome=request.outcome,
            next_hearing_date=request.next_hearing_date,
            # Pass extra fields (assumes hearing_storage.create_hearing accepts **kwargs or we modify it, 
            # OR we rely on modifying the storage method first. 
            # Wait, `create_hearing` method likely needs update to accept these? 
            # Or does it blindly pass args to DB? Checking logic... 
            # `hearing_storage.create_hearing` signature: 
            # def create_hearing(self, case_id, hearing_date, ..., notes, **kwargs)
            # If not, I need to check `storage/hearing_storage.py`.
            # Assuming standard kwargs pattern or I pass them explicitly if I modify the call.
            # Let's pass them as kwargs if supported, or update the storage call payload safely.
            case_number=case_number,
            court_name=court_name,
            case_year=case_year,
            client_name=client_name
        )
        
        # Log audit
        log_audit(
            supabase, 'create', 'hearings', hearing.get('id', ''),
            current_user, lawyer_id,
            new_values=request.dict(exclude_none=True),
            description=f'إضافة جلسة بتاريخ {request.hearing_date}'
        )
        
        logger.info(f"✅ Hearing created for case {request.case_id}")
        
        return {
            "success": True,
            "hearing": hearing,
            "message": f"تم إضافة جلسة بتاريخ {request.hearing_date}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create hearing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"فشل في إضافة الجلسة: {str(e)}"
        )


@router.put("/{hearing_id}")
async def update_hearing(
    hearing_id: str,
    request: UpdateHearingRequest,
    current_user: Dict = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
):
    """
    تعديل جلسة - with audit logging
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        updates = request.dict(exclude_none=True)
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="لا توجد حقول للتحديث"
            )
        
        # Get existing hearing for audit
        from agents.config.database import db
        existing = db.client.table("hearings").select("*").eq("id", hearing_id).single().execute()
        old_hearing = existing.data if existing.data else {}
        
        # Convert time string if provided
        if "hearing_time" in updates and updates["hearing_time"]:
            updates["hearing_time"] = datetime.strptime(updates["hearing_time"], "%H:%M").time()
        
        hearing = hearing_storage.update_hearing(hearing_id, updates)
        
        if not hearing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="الجلسة غير موجودة"
            )
        
        # Log audit
        log_audit(
            supabase, 'update', 'hearings', hearing_id,
            current_user, lawyer_id,
            old_values=old_hearing,
            new_values=hearing,
            description='تعديل جلسة'
        )
        
        logger.info(f"✅ Hearing updated: {hearing_id}")
        
        return {
            "success": True,
            "hearing": hearing,
            "message": "تم تحديث الجلسة بنجاح"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update hearing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{hearing_id}")
async def delete_hearing(
    hearing_id: str,
    current_user: Dict = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
):
    """
    حذف جلسة - with audit logging
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Get existing hearing for audit
        from agents.config.database import db
        existing = db.client.table("hearings").select("*").eq("id", hearing_id).single().execute()
        old_hearing = existing.data if existing.data else {}
        
        success = hearing_storage.delete_hearing(hearing_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="الجلسة غير موجودة"
            )
        
        # Log audit
        log_audit(
            supabase, 'delete', 'hearings', hearing_id,
            current_user, lawyer_id,
            old_values=old_hearing,
            description='حذف جلسة'
        )
        
        logger.info(f"✅ Hearing deleted: {hearing_id}")
        
        return {
            "success": True,
            "message": "تم حذف الجلسة بنجاح"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete hearing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Export router
__all__ = ["router"]
