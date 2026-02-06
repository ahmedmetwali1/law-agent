"""
Clients API Router
روابط API لإدارة الموكلين
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
import logging

from api.auth_middleware import get_current_user
from api.guards import verify_subscription_active
from api.database import get_supabase_client
from agents.storage.client_storage import client_storage

def get_effective_lawyer_id(user: Dict[str, Any]) -> str:
    """Helper to get lawyer ID"""
    if user.get('role') == 'assistant':
        return user.get('office_id', user['id'])
    return user['id']

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== Request/Response Models =====

class CreateClientRequest(BaseModel):
    """Create client request"""
    full_name: str = Field(..., min_length=2, description="الاسم الكامل")
    national_id: Optional[str] = Field(None, description="رقم الهوية")
    phone: Optional[str] = Field(None, description="رقم الهاتف")
    email: Optional[EmailStr] = Field(None, description="البريد الإلكتروني")
    address: Optional[str] = Field(None, description="العنوان")
    notes: Optional[str] = Field(None, description="ملاحظات")
    has_power_of_attorney: bool = Field(False, description="هل لديه وكالة؟")
    power_of_attorney_number: Optional[str] = Field(None, description="رقم الوكالة")
    power_of_attorney_image_url: Optional[str] = Field(None, description="رابط صورة الوكالة")


class UpdateClientRequest(BaseModel):
    """Update client request"""
    full_name: Optional[str] = None
    national_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    has_power_of_attorney: Optional[bool] = None
    power_of_attorney_number: Optional[str] = None
    power_of_attorney_image_url: Optional[str] = None


# ===== API Endpoints =====

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_client(
    request: CreateClientRequest,
    current_user: Dict = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
):
    """
    إنشاء موكل جديد
    
    Requires authentication
    """
    try:
        client = client_storage.create_client(
            lawyer_id=current_user["id"],  # ⚠️ فلتر تلقائي
            full_name=request.full_name,
            national_id=request.national_id,
            phone=request.phone,
            email=request.email,
            address=request.address,
            notes=request.notes,
            has_power_of_attorney=request.has_power_of_attorney,
            power_of_attorney_number=request.power_of_attorney_number,
            power_of_attorney_image_url=request.power_of_attorney_image_url
        )
        
        return {
            "success": True,
            "client": client,
            "message": f"تم إضافة الموكل {request.full_name} بنجاح"
        }
    except Exception as e:
        logger.error(f"Failed to create client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"فشل في إضافة الموكل: {str(e)}"
        )


@router.get("")
async def get_clients(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for name, phone, email, or national ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get paginated clients with search support.
    """
    lawyer_id = get_effective_lawyer_id(current_user)

    # Calculate offset
    start = (page - 1) * limit
    end = start + limit - 1
    
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table('clients').select('*', count='exact').eq('lawyer_id', lawyer_id).order('created_at', desc=True)
        
        # Search
        if search:
            # Search across multiple columns using OR logic: name, phone, email, national_id
            search_filter = f"full_name.ilike.%{search}%,phone.ilike.%{search}%,email.ilike.%{search}%,national_id.ilike.%{search}%"
            query = query.or_(search_filter)
            
        # Pagination
        query = query.range(start, end)
        
        result = query.execute()
        
        return {
            "success": True,
            "data": result.data or [],
            "total": result.count or 0,
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_clients(
    q: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    البحث في الموكلين
    
    Query params:
        - q: search query
    """
    try:
        clients = client_storage.search_clients(
            lawyer_id=current_user["id"],
            query=q
        )
        
        return {
            "success": True,
            "count": len(clients),
            "clients": clients,
            "query": q
        }
    except Exception as e:
        logger.error(f"Failed to search clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{client_id}")
async def get_client(
    client_id: str,
    current_user: Dict = Depends(get_current_user),
    include_cases: bool = False
):
    """
    الحصول على تفاصيل موكل
    
    Path params:
        - client_id: UUID
    Query params:
        - include_cases: include client's cases (default: False)
    """
    try:
        if include_cases:
            client = client_storage.get_client_with_cases(
                client_id=client_id,
                lawyer_id=current_user["id"]
            )
        else:
            client = client_storage.get_client(
                client_id=client_id,
                lawyer_id=current_user["id"]
            )
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="الموكل غير موجود"
            )
        
        return {
            "success": True,
            "client": client
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{client_id}")
async def update_client(
    client_id: str,
    request: UpdateClientRequest,
    current_user: Dict = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
):
    """
    تعديل بيانات موكل
    """
    try:
        # Create updates dict (exclude None values)
        updates = request.dict(exclude_none=True)
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="لا توجد حقول للتحديث"
            )
        
        client = client_storage.update_client(
            client_id=client_id,
            lawyer_id=current_user["id"],
            updates=updates
        )
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="الموكل غير موجود"
            )
        
        return {
            "success": True,
            "client": client,
            "message": "تم تحديث بيانات الموكل بنجاح"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    current_user: Dict = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
):
    """
    حذف موكل
    """
    try:
        success = client_storage.delete_client(
            client_id=client_id,
            lawyer_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="الموكل غير موجود"
            )
        
        return {
            "success": True,
            "message": "تم حذف الموكل بنجاح"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Export router
__all__ = ["router"]
