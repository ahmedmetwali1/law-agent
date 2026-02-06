"""
Notifications API Router
Provides unified notifications from hearings and tasks
Replaces direct Supabase access from Frontend (notificationStore.ts)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from api.auth_middleware import get_current_user
from api.database import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# --- Models ---

class Notification(BaseModel):
    id: str
    type: str  # hearing, task, case
    title: str
    message: str
    timestamp: str
    read: bool
    link: Optional[str] = None


class NotificationsResponse(BaseModel):
    notifications: List[Notification]
    unreadCount: int


# --- Helper Functions ---

def get_effective_lawyer_id(user: Dict[str, Any]) -> str:
    """Get effective lawyer_id from user context"""
    if user.get('role') == 'assistant':
        return user.get('office_id', user['id'])
    return user['id']


# --- Endpoints ---

@router.get("", response_model=NotificationsResponse)
async def get_notifications(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> NotificationsResponse:
    """
    Get unified notifications for current user.
    Includes:
    - Upcoming hearings (next 7 days)
    - Pending/in-progress tasks
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = get_effective_lawyer_id(current_user)
        is_assistant = current_user.get('role') == 'assistant'
        
        notifications: List[Notification] = []
        
        # 1. Fetch upcoming hearings (next 7 days)
        today = datetime.now()
        seven_days_later = today + timedelta(days=7)
        
        hearings_query = supabase.table('hearings')\
            .select('id, hearing_date, hearing_time, case_id')\
            .eq('lawyer_id', lawyer_id)\
            .gte('hearing_date', today.date().isoformat())\
            .lte('hearing_date', seven_days_later.date().isoformat())\
            .order('hearing_date', desc=False)\
            .limit(5)
        
        hearings_result = hearings_query.execute()
        
        if hearings_result.data:
            for h in hearings_result.data:
                try:
                    hearing_date_str = f"{h['hearing_date']}T{h.get('hearing_time') or '00:00'}"
                    hearing_date = datetime.fromisoformat(hearing_date_str)
                    
                    days_until = (hearing_date.date() - today.date()).days
                    
                    if days_until == 0:
                        time_text = 'اليوم'
                        title = '⚖️ جلسة اليوم'
                    elif days_until == 1:
                        time_text = 'غداً'
                        title = '⚖️ جلسة غداً'
                    else:
                        time_text = f'بعد {days_until} أيام'
                        title = '⚖️ جلسة قادمة'
                    
                    notifications.append(Notification(
                        id=f"hearing-{h['id']}",
                        type='hearing',
                        title=title,
                        message=f'جلسة - {time_text}',
                        timestamp=hearing_date.isoformat(),
                        read=False,
                        link=f"/hearings?highlight={h['id']}"
                    ))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse hearing date: {e}")
                    continue
        
        # 2. Fetch pending/in-progress tasks
        tasks_query = supabase.table('tasks')\
            .select('id, title, execution_date, status')\
            .eq('lawyer_id', lawyer_id)\
            .in_('status', ['pending', 'in_progress'])\
            .order('execution_date', desc=False)\
            .limit(10)
        
        # For assistants: filter to their assigned tasks
        if is_assistant:
            user_id = current_user['id']
            tasks_query = tasks_query.or_(f'assigned_to.eq.{user_id},assign_to_all.eq.true')
        
        tasks_result = tasks_query.execute()
        
        if tasks_result.data:
            for t in tasks_result.data:
                try:
                    # Parse execution_date if exists
                    due_date = None
                    if t.get('execution_date'):
                        due_date = datetime.fromisoformat(t['execution_date'])
                        timestamp = due_date.isoformat()
                    else:
                        # Use current time if no execution date
                        timestamp = datetime.now().isoformat()
                    
                    is_today = due_date and due_date.date() == today.date()
                    is_overdue = due_date and due_date.date() < today.date()
                    
                    status_emoji = '⏳' if t['status'] == 'in_progress' else '📋'
                    status_text = 'قيد التنفيذ' if t['status'] == 'in_progress' else 'معلقة'
                    
                    if is_today:
                        title = f'{status_emoji} مهمة اليوم'
                    elif is_overdue:
                        title = f'{status_emoji} مهمة متأخرة ⚠️'
                    else:
                        title = f'{status_emoji} مهمة {status_text}'
                    
                    notifications.append(Notification(
                        id=f"task-{t['id']}",
                        type='task',
                        title=title,
                        message=t['title'][:50],  # Truncate to 50 chars
                        timestamp=timestamp,
                        read=False,
                        link=f"/tasks?highlight={t['id']}"
                    ))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse task date: {e}")
                    continue
        
        # 3. Sort by timestamp (most recent first)
        notifications.sort(key=lambda n: n.timestamp, reverse=True)
        
        # 4. Calculate unread count (all notifications are unread for now)
        # In future, we can add a 'read_notifications' table to track this
        unread_count = len(notifications)
        
        return NotificationsResponse(
            notifications=notifications,
            unreadCount=unread_count
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/announcements")
async def get_active_announcements(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get active system announcements for the current user.
    """
    try:
        supabase = get_supabase_client()
        today = datetime.now().isoformat()
        
        user_role = current_user.get('role', 'lawyer')
        
        # Build query
        query = supabase.table('system_announcements')\
            .select('*')\
            .eq('is_active', True)\
            .order('priority', desc=True)\
            .order('created_at', desc=True)
            
        # Filter by date (start_date <= now OR null)
        # Note: Supabase JS client handles complex ORs easier, but for simple REST:
        # We'll fetch active ones and filter in python for now to handle complex date logic easily
        # or use simple filters if possible.
        # Let's try to filter by audience first
        
        # Audience filter: 'all' OR user's role
        # query = query.in_('target_audience', ['all', user_role]) # Supabase doesn't support IN with OR logic easily in one go without raw sql or RPC
        
        result = query.execute()
        
        logger.info(f"🔍 Checking announcements for user role: {user_role}. Found {len(result.data)} candidates.")
        
        valid_announcements = []
        if result.data:
            for ann in result.data:
                # 1. Audience Check
                if ann['target_audience'] != 'all' and ann['target_audience'] != user_role:
                    logger.info(f"Skipping announcement '{ann['title']}': audience '{ann['target_audience']}' != '{user_role}'")
                    continue
                
                # 2. Date Check
                start_date = datetime.fromisoformat(ann['start_date']) if ann.get('start_date') else None
                end_date = datetime.fromisoformat(ann['end_date']) if ann.get('end_date') else None
                
                # Determine 'now' compatible with the dates
                # If parsed date is aware, use aware 'now'. If naive, use naive 'now'.
                # We use start_date or end_date to determine preference, defaulting to naive local if no dates (though dates are null then so it doesn't matter)
                check_tz = start_date.tzinfo if start_date else (end_date.tzinfo if end_date else None)
                
                if check_tz:
                    now = datetime.now(check_tz)
                else:
                    now = datetime.now()
                
                if start_date and start_date > now:
                    logger.info(f"Skipping announcement '{ann['title']}': not started yet (Start: {start_date})")
                    continue
                if end_date and end_date < now:
                    logger.info(f"Skipping announcement '{ann['title']}': expired (End: {end_date})")
                    continue
                    
                valid_announcements.append(ann)
        
        logger.info(f"✅ Returning {len(valid_announcements)} valid announcements.")
        return valid_announcements
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch announcements: {e}")
        raise HTTPException(status_code=500, detail=str(e))
