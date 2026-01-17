"""
Hearings API Router
روابط API لإدارة الجلسات
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date
import logging

from api.auth_middleware import get_current_user
from agents.storage.hearing_storage import hearing_storage

logger = logging.getLogger(__name__)

router = APIRouter()


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
    
    Most important endpoint - shows today's schedule
    """
    try:
        hearings = hearing_storage.get_today_hearings_by_lawyer(
            lawyer_id=current_user["id"]
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
    
    Query params:
        - days: number of days to look ahead (default: 7)
    """
    try:
        hearings = hearing_storage.get_upcoming_hearings_by_lawyer(
            lawyer_id=current_user["id"],
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


@router.get("/case/{case_id}")
async def get_case_hearings(
    case_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    جلسات قضية معينة
    
    Path params:
        - case_id: UUID
    """
    try:
        # TODO: Verify case belongs to lawyer
        hearings = hearing_storage.get_case_hearings(case_id)
        
        return {
            "success": True,
            "count": len(hearings),
            "case_id": case_id,
            "hearings": hearings
        }
    except Exception as e:
        logger.error(f"Failed to get case hearings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_hearing(
    request: CreateHearingRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    إنشاء جلسة جديدة
    """
    try:
        # TODO: Verify case belongs to lawyer
        
        from datetime import datetime
        time_obj = None
        if request.hearing_time:
            time_obj = datetime.strptime(request.hearing_time, "%H:%M").time()
        
        hearing = hearing_storage.create_hearing(
            case_id=request.case_id,
            hearing_date=request.hearing_date,
            hearing_time=time_obj,
            court_room=request.court_room,
            judge_name=request.judge_name,
            judge_requests=request.judge_requests,
            notes=request.notes
        )
        
        return {
            "success": True,
            "hearing": hearing,
            "message": f"تم إضافة جلسة بتاريخ {request.hearing_date}"
        }
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
    current_user: Dict = Depends(get_current_user)
):
    """
    تعديل جلسة
    """
    try:
        updates = request.dict(exclude_none=True)
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="لا توجد حقول للتحديث"
            )
        
        # Convert time string if provided
        if "hearing_time" in updates and updates["hearing_time"]:
            from datetime import datetime
            updates["hearing_time"] = datetime.strptime(updates["hearing_time"], "%H:%M").time()
        
        hearing = hearing_storage.update_hearing(hearing_id, updates)
        
        if not hearing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="الجلسة غير موجودة"
            )
        
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
    current_user: Dict = Depends(get_current_user)
):
    """
    حذف جلسة
    """
    try:
        success = hearing_storage.delete_hearing(hearing_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="الجلسة غير موجودة"
            )
        
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
