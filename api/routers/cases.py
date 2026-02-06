"""
Cases API Router
روابط API لإدارة القضايا

Enhanced with:
- Audit logging (matching tasks.py pattern)
- Efficient single-case lookup
- Update and Delete endpoints
- Redis caching for list operations
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from api.auth_middleware import get_current_user
from api.guards import verify_subscription_active
from api.database import get_supabase_client
from agents.storage.case_storage import CaseStorage

logger = logging.getLogger(__name__)

router = APIRouter()
case_storage = CaseStorage(use_supabase=True)


# ===== Helper Functions =====

def get_effective_lawyer_id(user: Dict[str, Any]) -> str:
    """
    Get the effective lawyer_id from user context.
    For lawyers: their own ID
    For assistants: their office_id (the lawyer they work for)
    """
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


# ===== Request/Response Models =====

class CreateCaseRequest(BaseModel):
    """Create case request"""
    client_id: str = Field(..., description="معرف الموكل")
    case_number: str = Field(..., description="رقم القضية")
    court_name: Optional[str] = None
    court_circuit: Optional[str] = None
    case_type: Optional[str] = None
    subject: Optional[str] = None
    status: str = "active"
    summary: Optional[str] = None
    case_year: Optional[str] = None
    case_date: Optional[str] = None
    client_capacity: Optional[str] = None
    verdict_number: Optional[str] = None
    verdict_year: Optional[str] = None
    verdict_date: Optional[str] = None
    client_name: Optional[str] = Field(None, description="اسم الموكل (للتخزين فقط)")


class UpdateCaseRequest(BaseModel):
    """Update case request"""
    case_number: Optional[str] = None
    court_name: Optional[str] = None
    court_circuit: Optional[str] = None
    case_type: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None
    case_year: Optional[str] = None
    case_date: Optional[str] = None
    client_capacity: Optional[str] = None
    verdict_number: Optional[str] = None
    verdict_year: Optional[str] = None
    verdict_date: Optional[str] = None



class CreateOpponentRequest(BaseModel):
    """Create opponent request"""
    full_name: str = Field(..., min_length=2, description="اسم الخصم")
    national_id: Optional[str] = None
    capacity: Optional[str] = None


# ===== API Endpoints =====

@router.get("/")
async def list_cases(
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = Query(None, alias="status")
):
    """
    عرض جميع القضايا للمحامي
    """
    try:
        lawyer_id = get_effective_lawyer_id(current_user)
        cases = case_storage.get_cases_by_lawyer(
            lawyer_id=lawyer_id,
            limit=limit
        )
        
        # Apply status filter if provided
        if status_filter and status_filter != 'all':
            cases = [c for c in cases if c.get('status') == status_filter]
        
        return {
            "success": True,
            "count": len(cases),
            "cases": cases
        }
    except Exception as e:
        logger.error(f"Failed to list cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/search")
async def search_cases(
    q: str = Query(..., min_length=1),
    current_user: Dict = Depends(get_current_user)
):
    """
    البحث في القضايا
    """
    try:
        lawyer_id = get_effective_lawyer_id(current_user)
        cases = case_storage.search_cases(
            lawyer_id=lawyer_id,
            query=q
        )
        
        return {
            "success": True,
            "count": len(cases),
            "cases": cases,
            "query": q
        }
    except Exception as e:
        logger.error(f"Failed to search cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_case(
    request: CreateCaseRequest,
    current_user: Dict = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
):
    """
    إنشاء قضية جديدة
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        case_data = request.dict(exclude_none=True)
        case_data["lawyer_id"] = lawyer_id
        case_data["created_at"] = datetime.now().isoformat()
        
        # ✅ Fetch client name for denormalization
        client_name = None
        try:
            from agents.config.settings import TableNames
            from agents.config.database import db
            client_resp = db.client.table(TableNames.CLIENTS)\
                .select("full_name")\
                .eq("id", case_data["client_id"])\
                .single()\
                .execute()
            if client_resp.data:
                client_name = client_resp.data.get("full_name")
                case_data["client_name"] = client_name
        except Exception as e:
            logger.warning(f"Failed to fetch client name for denormalization: {e}")

        created_case = case_storage.create_case_in_db(case_data)
        
        # Log audit
        log_audit(
            supabase, 'create', 'cases', created_case.get('id', ''),
            current_user, lawyer_id,
            new_values=case_data,
            description=f'إنشاء قضية جديدة للموكل {client_name}' if client_name else 'إنشاء قضية جديدة'
        )
        
        logger.info(f"✅ Case created: {created_case.get('id')}")
        
        return {
            "success": True,
            "case": created_case,
            "message": "تم إنشاء القضية بنجاح"
        }
    except Exception as e:
        logger.error(f"Failed to create case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"فشل في إنشاء القضية: {str(e)}"
        )


@router.get("/{case_id}")
async def get_case_details(
    case_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    تفاصيل القضية - O(1) lookup with ownership verification
    """
    try:
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Use efficient direct lookup
        target_case = case_storage.get_case_by_id(case_id, lawyer_id)
        
        if not target_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="القضية غير موجودة"
            )
            
        return {
            "success": True,
            "case": target_case
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get case details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{case_id}")
async def update_case(
    case_id: str,
    request: UpdateCaseRequest,
    current_user: Dict = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
):
    """
    تعديل قضية
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Verify ownership
        existing_case = case_storage.get_case_by_id(case_id, lawyer_id)
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="القضية غير موجودة أو لا تملك صلاحية التعديل"
            )
        
        # Build update data (only non-None fields)
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            return {"success": True, "case": existing_case, "message": "لا توجد تعديلات"}
        
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Update in DB
        from agents.config.settings import TableNames
        from agents.config.database import db
        
        result = db.client.table(TableNames.CASES)\
            .update(update_data)\
            .eq("id", case_id)\
            .eq("lawyer_id", lawyer_id)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update case")
        
        updated_case = result.data[0]
        
        # Log audit
        log_audit(
            supabase, 'update', 'cases', case_id,
            current_user, lawyer_id,
            old_values=existing_case,
            new_values=updated_case,
            description='تعديل قضية'
        )
        
        logger.info(f"✅ Case updated: {case_id}")
        
        return {
            "success": True,
            "case": updated_case,
            "message": "تم تعديل القضية بنجاح"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{case_id}")
async def delete_case(
    case_id: str,
    current_user: Dict = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
):
    """
    حذف قضية (للمحامي فقط)
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Only lawyers can delete (not assistants)
        if current_user.get('role') == 'assistant':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="المساعدون لا يملكون صلاحية حذف القضايا"
            )
        
        # Verify ownership
        existing_case = case_storage.get_case_by_id(case_id, lawyer_id)
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="القضية غير موجودة"
            )
        
        # Delete from DB
        from agents.config.settings import TableNames
        from agents.config.database import db
        
        db.client.table(TableNames.CASES)\
            .delete()\
            .eq("id", case_id)\
            .eq("lawyer_id", lawyer_id)\
            .execute()
        
        # Log audit
        log_audit(
            supabase, 'delete', 'cases', case_id,
            current_user, lawyer_id,
            old_values=existing_case,
            description='حذف قضية'
        )
        
        logger.info(f"✅ Case deleted: {case_id}")
        
        return {
            "success": True,
            "message": "تم حذف القضية بنجاح"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{case_id}/opponents")
async def get_case_opponents(
    case_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    خصوم القضية - with ownership verification
    """
    try:
        from agents.config.database import db
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Verify case ownership first
        existing_case = case_storage.get_case_by_id(case_id, lawyer_id)
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="القضية غير موجودة"
            )
        
        response = db.client.table("opponents")\
            .select("*")\
            .eq("case_id", case_id)\
            .execute()
            
        return {
            "success": True,
            "opponents": response.data if response.data else []
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get opponents: {e}")
        return {
            "success": False,
            "opponents": [],
            "error": str(e)
        }



@router.post("/{case_id}/opponents", status_code=status.HTTP_201_CREATED)
async def create_opponent(
    case_id: str,
    request: CreateOpponentRequest,
    current_user: Dict = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
):
    """
    إضافة خصم للقضية
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Verify ownership
        existing_case = case_storage.get_case_by_id(case_id, lawyer_id)
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="القضية غير موجودة أو لا تملك صلاحية التعديل"
            )
            
        opponent_data = request.dict(exclude_none=True)
        opponent_data["case_id"] = case_id
        
        # Insert into DB
        from agents.config.database import db
        result = db.client.table("opponents").insert(opponent_data).execute()
        
        if not result.data:
            raise Exception("Failed to create opponent")
            
        created_opponent = result.data[0]
        
        # Log audit
        log_audit(
            supabase, 'create', 'opponents', created_opponent['id'],
            current_user, lawyer_id,
            new_values=created_opponent,
            description=f"إضافة خصم: {created_opponent.get('full_name')}"
        )
        
        return {
            "success": True,
            "opponent": created_opponent,
            "message": "تمت إضافة الخصم بنجاح"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create opponent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{case_id}/opponents/{opponent_id}")
async def delete_opponent(
    case_id: str,
    opponent_id: str,
    current_user: Dict = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
):
    """
    حذف خصم من القضية
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Verify ownership of case
        existing_case = case_storage.get_case_by_id(case_id, lawyer_id)
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="القضية غير موجودة أو لا تملك صلاحية التعديل"
            )
            
        # Verify opponent exists and belongs to case
        from agents.config.database import db
        opp_result = db.client.table("opponents").select("*").eq("id", opponent_id).eq("case_id", case_id).execute()
        
        if not opp_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="الخصم غير موجود في هذه القضية"
            )
            
        opponent = opp_result.data[0]
        
        # Delete
        db.client.table("opponents").delete().eq("id", opponent_id).execute()
        
        # Log audit
        log_audit(
            supabase, 'delete', 'opponents', opponent_id,
            current_user, lawyer_id,
            old_values=opponent,
            description=f"حذف خصم: {opponent.get('full_name')}"
        )
        
        return {
            "success": True,
            "message": "تم حذف الخصم بنجاح"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete opponent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


__all__ = ["router"]
