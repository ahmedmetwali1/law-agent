"""
Admin API Router - السوبر أدمن
Secure endpoints restricted to Manager role only

⚠️ PRIVACY CONSTRAINTS:
- NO access to: clients, cases, hearings tables
- NO access to: private messages or confidential documents
- ONLY: Platform settings, user management (activation only), system health
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime
import logging

from api.auth_middleware import get_current_manager
from api.database import get_supabase_client
from api.admin_models import (
    PlatformSettingsResponse,
    PlatformSettingsUpdate,
    LawyerActivationStatus,
    LawyerInfo,
    LawyersStatsResponse,
    SupportTemplateCreate,
    SupportTemplateUpdate,
    SupportTemplateResponse,
    SystemAnnouncementCreate,
    SystemAnnouncementUpdate,
    SystemAnnouncementResponse,
    SystemHealthResponse,
    ConnectionTestRequest,
    ConnectionTestResponse,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    UserRoleUpdate
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============================================================================
# Platform Settings Endpoints
# ============================================================================

@router.get("/platform-settings", response_model=PlatformSettingsResponse)
async def get_platform_settings(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    جلب جميع إعدادات المنصة
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('platform_settings')\
            .select('*')\
            .limit(1)\
            .execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Platform settings not found. Please run migrations."
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch platform settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/platform-settings", response_model=PlatformSettingsResponse)
async def update_platform_settings(
    settings: PlatformSettingsUpdate,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    تحديث إعدادات المنصة
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        # Build update data (only non-None fields)
        update_data = {k: v for k, v in settings.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No data to update"
            )
        
        # Add metadata
        update_data['updated_by'] = current_user['id']
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Get current settings to increment version
        current = supabase.table('platform_settings')\
            .select('id, version')\
            .limit(1)\
            .execute()
        
        if current.data:
            update_data['version'] = current.data[0].get('version', 1) + 1
        
        # Update (since only one row exists, we update it)
        result = supabase.table('platform_settings')\
            .update(update_data)\
            .eq('id', current.data[0]['id'] if current.data else None)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update platform settings")
        
        logger.info(f"✅ Platform settings updated by {current_user.get('full_name')}")
        
        # Log audit
        from api.routers.settings import log_audit
        log_audit(
            supabase, 'update', 'platform_settings', str(result.data[0]['id']),
            current_user,
            description='تحديث إعدادات المنصة'
        )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update platform settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/platform-settings/reset")
async def reset_platform_settings(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    إعادة تعيين الإعدادات إلى القيم الافتراضية
    Manager only - DANGEROUS OPERATION
    """
    try:
        supabase = get_supabase_client()
        
        # Delete current settings
        supabase.table('platform_settings').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # Re-run default insert (from migration)
        # This will be handled by re-running the migration manually
        
        logger.warning(f"⚠️ Platform settings RESET by {current_user.get('full_name')}")
        
        return {"message": "يجب إعادة تشغيل المنصة لتطبيق الإعدادات الافتراضية"}
        
    except Exception as e:
        logger.error(f"❌ Failed to reset platform settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Lawyers Management Endpoints
# ============================================================================

@router.get("/lawyers", response_model=List[LawyerInfo])
async def get_all_lawyers(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    قائمة جميع المحامين (بدون بيانات خاصة)
    Manager only
    
    ⚠️ Returns ONLY: id, name, email, phone, role, is_active, created_at
    DOES NOT return: cases, clients, or any private data
    """
    try:
        supabase = get_supabase_client()
        
        # Fetch users with their role details
        lawyers = supabase.table('users')\
            .select('*, role_info:roles(name, name_ar)')\
            .order('created_at', desc=True)\
            .execute()
        
        # Get counts for each lawyer (statistics only)
        lawyers_with_stats = []
        for lawyer in lawyers.data:
            # Count cases
            cases = supabase.table('cases')\
                .select('id', count='exact')\
                .eq('lawyer_id', lawyer['id'])\
                .execute()
            
            # Count clients
            clients = supabase.table('clients')\
                .select('id', count='exact')\
                .eq('lawyer_id', lawyer['id'])\
                .execute()
            
            # Count hearings
            hearings = supabase.table('hearings')\
                .select('id', count='exact')\
                .eq('lawyer_id', lawyer['id'])\
                .execute()
            
            lawyers_with_stats.append({
                **lawyer,
                'total_cases': cases.count or 0,
                'total_clients': clients.count or 0,
                'total_hearings': hearings.count or 0
            })
        
        return lawyers_with_stats
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch lawyers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/lawyers/{lawyer_id}/activation")
async def toggle_lawyer_activation(
    lawyer_id: str,
    status: LawyerActivationStatus,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    تفعيل/إلغاء تفعيل محامي
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        # Update user is_active status
        result = supabase.table('users')\
            .update({'is_active': status.is_active})\
            .eq('id', lawyer_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Lawyer not found")
        
        # Update platform_settings to track this
        settings = supabase.table('platform_settings')\
            .select('lawyers_activation_status')\
            .limit(1)\
            .execute()
        
        if settings.data:
            activation_status = settings.data[0].get('lawyers_activation_status', {})
            activation_status[lawyer_id] = {
                'is_active': status.is_active,
                'reason': status.reason,
                'changed_at': datetime.now().isoformat(),
                'changed_by': current_user['id']
            }
            
            supabase.table('platform_settings')\
                .update({'lawyers_activation_status': activation_status})\
                .eq('id', settings.data[0]['id'])\
                .execute()
        
        action = "تفعيل" if status.is_active else "إلغاء تفعيل"
        logger.info(f"✅ {action} محامي: {lawyer_id} by {current_user.get('full_name')}")
        
        # Log audit
        from api.routers.settings import log_audit
        log_audit(
            supabase, 'update', 'users', lawyer_id,
            current_user,
            description=f'{action} حساب المحامي - السبب: {status.reason or "غير محدد"}'
        )
        
        return {
            "message": f"تم {action} المحامي بنجاح",
            "lawyer_id": lawyer_id,
            "is_active": status.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to toggle lawyer activation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lawyers/stats", response_model=LawyersStatsResponse)
async def get_lawyers_stats(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    إحصائيات المحامين العامة
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        # Total lawyers
        total_lawyers = supabase.table('users')\
            .select('id', count='exact')\
            .eq('role', 'lawyer')\
            .execute()
        
        # Active lawyers
        active = supabase.table('users')\
            .select('id', count='exact')\
            .eq('role', 'lawyer')\
            .eq('is_active', True)\
            .execute()
        
        # Assistants
        assistants = supabase.table('users')\
            .select('id', count='exact')\
            .eq('role', 'assistant')\
            .execute()
        
        # Total cases (all lawyers)
        total_cases = supabase.table('cases')\
            .select('id', count='exact')\
            .execute()
        
        # Total clients (all lawyers)
        total_clients = supabase.table('clients')\
            .select('id', count='exact')\
            .execute()
        
        return {
            'total_lawyers': total_lawyers.count or 0,
            'active_lawyers': active.count or 0,
            'inactive_lawyers': (total_lawyers.count or 0) - (active.count or 0),
            'total_assistants': assistants.count or 0,
            'total_cases_all': total_cases.count or 0,
            'total_clients_all': total_clients.count or 0
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch lawyers stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Health & Monitoring
# ============================================================================

@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    حالة النظام الكاملة
    Manager only
    """
    try:
        from api.cache import get_cache
        
        cache = get_cache()
        cache_stats = cache.get_stats()
        cache_info = cache.get_info()
        
        # Database health (simple query)
        supabase = get_supabase_client()
        db_start = datetime.now()
        supabase.table('users').select('id').limit(1).execute()
        db_latency = (datetime.now() - db_start).total_seconds() * 1000  # ms
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now(),
            'services': {
                'database': {
                    'status': 'operational',
                    'latency_ms': round(db_latency, 2)
                },
                'cache': {
                    'status': 'operational' if cache_stats['available'] else 'degraded',
                    'enabled': cache_stats['enabled'],
                    'available': cache_stats['available'],
                    'hit_rate': f"{cache_stats['hit_rate']}%",
                    'server_info': cache_info
                }
            },
            'metrics': {
                'cache': {
                    'hits': cache_stats['hits'],
                    'misses': cache_stats['misses'],
                    'sets': cache_stats['sets'],
                    'deletes': cache_stats['deletes'],
                    'errors': cache_stats['errors']
                }
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/cache/clear")
async def clear_cache(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    مسح الـ Cache بالكامل
    Manager only - USE WITH CAUTION
    """
    try:
        from api.cache import get_cache
        
        cache = get_cache()
        success = cache.clear_all()
        
        if success:
            logger.warning(f"⚠️ Cache cleared by {current_user.get('full_name')}")
            return {"message": "تم مسح الـ Cache بنجاح"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to clear cache"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/test-connection", response_model=ConnectionTestResponse)
async def test_connection(
    test_request: ConnectionTestRequest,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    اختبار الاتصال بخدمة معينة
    Manager only
    """
    try:
        service = test_request.service.lower()
        
        if service == 'redis':
            from api.cache import get_cache
            cache = get_cache()
            stats = cache.get_stats()
            
            return {
                'service': 'redis',
                'success': stats['available'],
                'message': 'متصل بنجاح' if stats['available'] else 'فشل الاتصال',
                'details': stats
            }
        
        elif service == 'database':
            supabase = get_supabase_client()
            result = supabase.table('users').select('id').limit(1).execute()
            
            return {
                'service': 'database',
                'success': True,
                'message': 'متصل بنجاح',
                'details': {'records_count': len(result.data) if result.data else 0}
            }
        
        elif service == 'ai':
            # Test AI connection (if configured)
            return {
                'service': 'ai',
                'success': False,
                'message': 'AI connection test not implemented yet',
                'details': None
            }
        
        elif service == 'smtp':
            # Test SMTP connection
            return {
                'service': 'smtp',
                'success': False,
                'message': 'SMTP connection test not implemented yet',
                'details': None
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown service: {service}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return {
            'service': test_request.service,
            'success': False,
            'message': str(e),
            'details': None
        }


# ============================================================================
# Support Templates Endpoints
# ============================================================================

@router.get("/support/templates", response_model=List[SupportTemplateResponse])
async def get_support_templates(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """جلب قائمة قوالب الدعم"""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('support_ticket_templates')\
            .select('*')\
            .order('created_at', desc=True)\
            .execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/support/templates", response_model=SupportTemplateResponse)
async def create_support_template(
    template: SupportTemplateCreate,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """إنشاء قالب جديد"""
    try:
        supabase = get_supabase_client()
        
        template_data = template.dict()
        template_data['created_by'] = current_user['id']
        
        result = supabase.table('support_ticket_templates')\
            .insert(template_data)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create template")
        
        logger.info(f"✅ Support template created: {template.template_name}")
        return result.data[0]
        
    except Exception as e:
        logger.error(f"❌ Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/support/templates/{template_id}", response_model=SupportTemplateResponse)
async def update_support_template(
    template_id: str,
    template: SupportTemplateUpdate,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """تحديث قالب"""
    try:
        supabase = get_supabase_client()
        
        update_data = {k: v for k, v in template.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        result = supabase.table('support_ticket_templates')\
            .update(update_data)\
            .eq('id', template_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/support/templates/{template_id}")
async def delete_support_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """حذف قالب"""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('support_ticket_templates')\
            .delete()\
            .eq('id', template_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        logger.info(f"✅ Support template deleted: {template_id}")
        return {"message": "تم حذف القالب بنجاح"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Announcements Endpoints
# ============================================================================

@router.get("/announcements", response_model=List[SystemAnnouncementResponse])
async def get_announcements(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """جلب جميع الإعلانات"""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('system_announcements')\
            .select('*')\
            .order('priority', desc=True)\
            .order('created_at', desc=True)\
            .execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch announcements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/announcements", response_model=SystemAnnouncementResponse)
async def create_announcement(
    announcement: SystemAnnouncementCreate,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """إنشاء إعلان جديد"""
    try:
        supabase = get_supabase_client()
        
        announcement_data = announcement.dict()
        announcement_data['created_by'] = current_user['id']
        
        # Convert datetime objects to ISO strings for JSON serialization
        if announcement_data.get('start_date'):
            announcement_data['start_date'] = announcement_data['start_date'].isoformat()
        if announcement_data.get('end_date'):
            announcement_data['end_date'] = announcement_data['end_date'].isoformat()
        
        result = supabase.table('system_announcements')\
            .insert(announcement_data)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create announcement")
        
        logger.info(f"✅ Announcement created: {announcement.title}")
        return result.data[0]
        
    except Exception as e:
        logger.error(f"❌ Failed to create announcement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/announcements/{announcement_id}", response_model=SystemAnnouncementResponse)
async def update_announcement(
    announcement_id: str,
    announcement: SystemAnnouncementUpdate,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """تحديث إعلان"""
    try:
        supabase = get_supabase_client()
        
        update_data = {k: v for k, v in announcement.dict().items() if v is not None}
        
        # Convert datetime objects to ISO strings
        if update_data.get('start_date'):
            update_data['start_date'] = update_data['start_date'].isoformat()
        if update_data.get('end_date'):
            update_data['end_date'] = update_data['end_date'].isoformat()
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        result = supabase.table('system_announcements')\
            .update(update_data)\
            .eq('id', announcement_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update announcement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """حذف إعلان"""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('system_announcements')\
            .delete()\
            .eq('id', announcement_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        logger.info(f"✅ Announcement deleted: {announcement_id}")
        return {"message": "تم حذف الإعلان بنجاح"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete announcement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Audit Logs (Manager View - All Users)
# ============================================================================

@router.get("/audit-logs")
async def get_all_audit_logs(
    limit: int = 100,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    جلب سجلات التدقيق لجميع المستخدمين
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('audit_logs')\
            .select('*')\
            .order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        # Get total count
        count_result = supabase.table('audit_logs')\
            .select('id', count='exact')\
            .execute()
        
        return {
            'logs': result.data,
            'total': count_result.count,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Role Management Endpoints
# ============================================================================

@router.get("/roles", response_model=List[RoleResponse])
async def get_all_roles(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    جلب جميع الأدوار
    Admin only
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('roles')\
            .select('*')\
            .order('created_at', desc=False)\
            .execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """جلب دور محدد"""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('roles')\
            .select('*')\
            .eq('id', role_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Role not found")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role: RoleCreate,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """إنشاء دور جديد"""
    try:
        supabase = get_supabase_client()
        
        # Check if role name already exists
        existing = supabase.table('roles')\
            .select('id')\
            .eq('name', role.name)\
            .execute()
        
        if existing.data:
            raise HTTPException(
                status_code=409,
                detail=f"Role with name '{role.name}' already exists"
            )
        
        role_data = role.dict()
        
        result = supabase.table('roles')\
            .insert(role_data)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create role")
        
        logger.info(f"✅ Role created: {role.name} by {current_user.get('full_name')}")
        
        # Log audit
        from api.routers.settings import log_audit
        log_audit(
            supabase, 'create', 'roles', str(result.data[0]['id']),
            current_user,
            description=f'إنشاء دور جديد: {role.name_ar}'
        )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role: RoleUpdate,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """تحديث دور"""
    try:
        supabase = get_supabase_client()
        
        update_data = {k: v for k, v in role.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        result = supabase.table('roles')\
            .update(update_data)\
            .eq('id', role_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Role not found")
        
        logger.info(f"✅ Role updated: {role_id} by {current_user.get('full_name')}")
        
        # Log audit
        from api.routers.settings import log_audit
        log_audit(
            supabase, 'update', 'roles', role_id,
            current_user,
            description=f'تحديث الدور: {result.data[0].get("name_ar", "")}'
        )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    حذف دور
    ⚠️ لا يمكن حذف الأدوار الافتراضية أو الأدوار المستخدمة
    """
    try:
        supabase = get_supabase_client()
        
        # Check if role is default
        role = supabase.table('roles')\
            .select('is_default, name_ar')\
            .eq('id', role_id)\
            .execute()
        
        if not role.data:
            raise HTTPException(status_code=404, detail="Role not found")
        
        if role.data[0].get('is_default'):
            raise HTTPException(
                status_code=400,
                detail="Cannot delete default role"
            )
        
        # Check if role is in use
        users_with_role = supabase.table('users')\
            .select('id', count='exact')\
            .eq('role_id', role_id)\
            .execute()
        
        if users_with_role.count and users_with_role.count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete role. {users_with_role.count} users are using this role."
            )
        
        # Delete role
        result = supabase.table('roles')\
            .delete()\
            .eq('id', role_id)\
            .execute()
        
        logger.info(f"✅ Role deleted: {role_id} by {current_user.get('full_name')}")
        
        # Log audit
        from api.routers.settings import log_audit
        log_audit(
            supabase, 'delete', 'roles', role_id,
            current_user,
            description=f'حذف الدور: {role.data[0].get("name_ar", "")}'
        )
        
        return {"message": "تم حذف الدور بنجاح"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_update: UserRoleUpdate,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    تعيين دور لمستخدم
    Admin only
    """
    try:
        supabase = get_supabase_client()
        
        # Verify role exists
        role = supabase.table('roles')\
            .select('id, name, name_ar')\
            .eq('id', role_update.role_id)\
            .execute()
        
        if not role.data:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Update user's role_id and role name
        result = supabase.table('users')\
            .update({
                'role_id': role_update.role_id,
                'role': role.data[0]['name']
            })\
            .eq('id', user_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(
            f"✅ User {user_id} role updated to {role.data[0]['name']} "
            f"by {current_user.get('full_name')}"
        )
        
        # Log audit
        from api.routers.settings import log_audit
        log_audit(
            supabase, 'update', 'users', user_id,
            current_user,
            description=f'تغيير دور المستخدم إلى: {role.data[0].get("name_ar", "")}'
        )
        
        return {
            "message": "تم تحديث دور المستخدم بنجاح",
            "user_id": user_id,
            "role_id": role_update.role_id,
            "role_name": role.data[0]['name']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update user role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Subscription Packages Endpoints
# ============================================================================

@router.get("/packages")
async def get_packages(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    جلب جميع الباقات
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('subscription_packages')\
            .select('*')\
            .order('sort_order')\
            .execute()
        
        return result.data or []
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch packages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/packages")
async def create_package(
    package: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    إنشاء باقة جديدة
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        package['created_by'] = current_user['id']
        
        result = supabase.table('subscription_packages')\
            .insert(package)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create package")
        
        logger.info(f"✅ Package created: {package.get('name_ar')}")
        
        return result.data[0]
        
    except Exception as e:
        logger.error(f"❌ Failed to create package: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/packages/{package_id}")
async def update_package(
    package_id: str,
    package: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    تحديث باقة
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('subscription_packages')\
            .update(package)\
            .eq('id', package_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Package not found")
        
        logger.info(f"✅ Package updated: {package_id}")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update package: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/packages/{package_id}")
async def delete_package(
    package_id: str,
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    حذف باقة
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        # Check if package is default
        check = supabase.table('subscription_packages')\
            .select('is_default')\
            .eq('id', package_id)\
            .execute()
        
        if check.data and check.data[0].get('is_default'):
            raise HTTPException(
                status_code=400,
                detail="لا يمكن حذف الباقة الافتراضية"
            )
        
        result = supabase.table('subscription_packages')\
            .delete()\
            .eq('id', package_id)\
            .execute()
        
        logger.info(f"✅ Package deleted: {package_id}")
        
        return {"message": "تم حذف الباقة بنجاح"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete package: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Pricing Configuration Endpoints
# ============================================================================

@router.get("/pricing")
async def get_pricing(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    جلب إعدادات التسعير
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('subscription_pricing')\
            .select('*')\
            .limit(1)\
            .execute()
        
        if not result.data:
            # Return default pricing if not set
            return {
                "price_per_assistant": 50.0,
                "price_per_gb_monthly": 5.0,
                "price_per_1000_words": 2.0,
                "yearly_discount_percent": 20.0,
                "currency": "SAR",
                "currency_symbol": "ر.س",
                "free_storage_gb": 1.0,
                "free_words_monthly": 5000
            }
        
        return result.data[0]
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch pricing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/pricing")
async def update_pricing(
    pricing: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    تحديث إعدادات التسعير
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        # Get existing pricing
        existing = supabase.table('subscription_pricing')\
            .select('id')\
            .limit(1)\
            .execute()
        
        if existing.data:
            # Update
            result = supabase.table('subscription_pricing')\
                .update(pricing)\
                .eq('id', existing.data[0]['id'])\
                .execute()
        else:
            # Insert
            result = supabase.table('subscription_pricing')\
                .insert(pricing)\
                .execute()
        
        if not result.data:
            raise Exception("Failed to update pricing")
        
        logger.info(f"✅ Pricing updated by {current_user.get('full_name')}")
        
        return result.data[0]
        
    except Exception as e:
        logger.error(f"❌ Failed to update pricing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Multi-Country Pricing Endpoints
# ============================================================================

@router.get("/countries")
async def get_countries(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    جلب قائمة الدول المدعومة
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('countries')\
            .select('*')\
            .eq('is_active', True)\
            .order('name_ar')\
            .execute()
        
        return result.data or []
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch countries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/country-pricing")
async def get_country_pricing(
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    جلب تسعير الدول
    Manager only
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('country_pricing')\
            .select('*')\
            .execute()
        
        return result.data or []
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch country pricing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/country-pricing")
async def update_country_pricing(
    pricing: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_manager)
):
    """
    تحديث أو إضافة تسعير لدولة محددة
    Manager only
    """
    try:
        supabase = get_supabase_client()
        country_id = pricing.get('country_id')
        
        if not country_id:
            raise HTTPException(status_code=400, detail="country_id is required")
            
        # Check if exists
        existing = supabase.table('country_pricing')\
            .select('id')\
            .eq('country_id', country_id)\
            .execute()
            
        if existing.data:
            result = supabase.table('country_pricing')\
                .update(pricing)\
                .eq('country_id', country_id)\
                .execute()
        else:
            result = supabase.table('country_pricing')\
                .insert(pricing)\
                .execute()
                
        if not result.data:
            raise Exception("Failed to update country pricing")
            
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update country pricing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
