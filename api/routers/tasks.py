"""
Tasks API Router
Secure backend access for task management with Redis caching
Replaces direct Supabase access from Frontend (TasksPage.tsx)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from api.auth_middleware import get_current_user
from api.guards import verify_subscription_active
from api.database import get_supabase_client
from api.cache import get_cache, CacheKeys, CacheTTL
from api.cache.invalidation import invalidate_after_task_change

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# --- Models ---

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    execution_date: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    assigned_to: Optional[str] = None
    assign_to_all: bool = False
    case_id: Optional[str] = None
    client_id: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    execution_date: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    assign_to_all: Optional[bool] = None


class TaskStatusUpdate(BaseModel):
    status: str  # pending, in_progress, completed


# --- Helper Functions ---

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
        # Calculate changes for updates
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
async def get_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search term"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get paginated tasks with search and filtering.
    """
    lawyer_id = get_effective_lawyer_id(current_user)
    
    # Calculate offset
    start = (page - 1) * limit
    end = start + limit - 1

    try:
        supabase = get_supabase_client()
        is_assistant = current_user.get('role') == 'assistant'
        
        # Build query
        # Fetch data with count
        query = supabase.table('tasks')\
            .select('''
                *,
                assigned_user:users!tasks_assigned_to_fkey(full_name),
                completed_user:users!tasks_completed_by_fkey(full_name)
            ''', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .order('created_at', desc=True)
            
        # Assistant filter
        if is_assistant:
            user_id = current_user['id']
            query = query.or_(f'assigned_to.eq.{user_id},assign_to_all.eq.true')
        
        # Filters
        if status and status != 'all':
            query = query.eq('status', status)
        if priority and priority != 'all':
            query = query.eq('priority', priority)
        
        # Search (Title or Description)
        if search:
            # Note: or_ syntax for search across columns needs careful formatting in Supabase-py
            # "title.ilike.%q%,description.ilike.%q%"
            search_filter = f"title.ilike.%{search}%,description.ilike.%{search}%"
            query = query.or_(search_filter)

        # Pagination
        query = query.range(start, end)
        
        result = query.execute()
        
        return {
            "data": result.data or [],
            "total": result.count or 0,
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_task(
    task: TaskCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
) -> Dict[str, Any]:
    """Create a new task"""
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Build task data - lawyer_id from JWT, not from frontend!
        task_data = {
            'title': task.title,
            'description': task.description,
            'execution_date': task.execution_date,
            'priority': task.priority,
            'status': 'pending',
            'lawyer_id': lawyer_id,  # Enforced from JWT
            'created_by': current_user['id'],
            'assigned_to': None if task.assign_to_all else task.assigned_to,
            'assign_to_all': task.assign_to_all,
            'case_id': task.case_id,
            'client_id': task.client_id,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('tasks').insert(task_data).execute()
        
        if not result.data:
            raise Exception("Failed to create task")
        
        new_task = result.data[0]
        
        # Log audit
        log_audit(
            supabase, 'create', 'tasks', new_task['id'],
            current_user, lawyer_id,
            new_values=task_data,
            description='إنشاء مهمة جديدة'
        )
        
        # ✅ إبطال Caches المتأثرة
        invalidate_after_task_change(lawyer_id)
        
        logger.info(f"✅ Task created: {new_task['id']}") 
        return new_task
        
    except Exception as e:
        logger.error(f"❌ Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    task: TaskUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
) -> Dict[str, Any]:
    """Update an existing task"""
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Verify ownership
        existing = supabase.table('tasks')\
            .select('*')\
            .eq('id', task_id)\
            .eq('lawyer_id', lawyer_id)\
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Task not found or access denied")
        
        old_task = existing.data[0]
        
        # Build update data (only non-None fields)
        update_data = {k: v for k, v in task.dict().items() if v is not None}
        
        # Handle assign_to_all logic
        if task.assign_to_all:
            update_data['assigned_to'] = None
        
        if not update_data:
            return old_task  # Nothing to update
        
        result = supabase.table('tasks')\
            .update(update_data)\
            .eq('id', task_id)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update task")
        
        updated_task = result.data[0]
        
        # Log audit
        log_audit(
            supabase, 'update', 'tasks', task_id,
            current_user, lawyer_id,
            old_values=old_task,
            new_values=updated_task,
            description='تعديل مهمة'
        )
        
        # ✅ إبطال Caches
        invalidate_after_task_change(lawyer_id)
        
        return updated_task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{task_id}/status")
async def update_task_status(
    task_id: str,
    status_update: TaskStatusUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
) -> Dict[str, Any]:
    """Update task status (allows assistants to complete tasks)"""
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        is_assistant = current_user.get('role') == 'assistant'
        
        # Build query - assistants need different permission check
        query = supabase.table('tasks').select('*').eq('id', task_id)
        
        if is_assistant:
            # Assistants can update tasks assigned to them or to all
            user_id = current_user['id']
            query = query.eq('lawyer_id', lawyer_id)\
                .or_(f'assigned_to.eq.{user_id},assign_to_all.eq.true')
        else:
            query = query.eq('lawyer_id', lawyer_id)
        
        existing = query.execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Task not found or access denied")
        
        old_task = existing.data[0]
        
        # Build update data
        update_data = {'status': status_update.status}
        
        if status_update.status == 'completed':
            update_data['completed_by'] = current_user['id']
            update_data['completed_at'] = datetime.now().isoformat()
        else:
            update_data['completed_by'] = None
            update_data['completed_at'] = None
        
        result = supabase.table('tasks')\
            .update(update_data)\
            .eq('id', task_id)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update task status")
        
        updated_task = result.data[0]
        
        # Log audit
        log_audit(
            supabase, 'update', 'tasks', task_id,
            current_user, lawyer_id,
            old_values=old_task,
            new_values=updated_task,
            description='تحديث حالة المهمة'
        )
        
        # ✅ إبطال Caches
        invalidate_after_task_change(lawyer_id)
        
        return updated_task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: Dict = Depends(verify_subscription_active)
) -> Dict[str, bool]:
    """Delete a task (lawyers only)"""
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        # Only lawyers can delete (not assistants)
        if current_user.get('role') == 'assistant':
            raise HTTPException(status_code=403, detail="Assistants cannot delete tasks")
        
        # Verify ownership
        existing = supabase.table('tasks')\
            .select('*')\
            .eq('id', task_id)\
            .eq('lawyer_id', lawyer_id)\
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Task not found or access denied")
        
        old_task = existing.data[0]
        
        # Delete
        supabase.table('tasks').delete().eq('id', task_id).execute()
        
        # Log audit
        log_audit(
            supabase, 'delete', 'tasks', task_id,
            current_user, lawyer_id,
            old_values=old_task,
            description='حذف مهمة'
        )
        
        # ✅ إبطال Caches
        invalidate_after_task_change(lawyer_id)
        
        logger.info(f"✅ Task deleted: {task_id}")
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistants")
async def get_assistants(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get list of assistants for task assignment"""
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        
        result = supabase.table('users')\
            .select('id, full_name, email')\
            .eq('office_id', lawyer_id)\
            .eq('role', 'assistant')\
            .eq('is_active', True)\
            .execute()
        
        return result.data or []
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch assistants: {e}")
        raise HTTPException(status_code=500, detail=str(e))
