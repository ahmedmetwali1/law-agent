"""
Dashboard API Router
Provides aggregated statistics for lawyer dashboard
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from api.auth_middleware import get_current_user
from api.database import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> dict:
    """
    Get dashboard statistics for current lawyer
    
    Returns:
        - Total cases (active and pending)
        - Total hearings
        - Total tasks (pending and in-progress)
        - Total clients
        - New clients this month
    """
    try:
        lawyer_id = current_user['id']
        supabase = get_supabase_client()
        
        logger.info(f"📊 Fetching dashboard stats for lawyer: {lawyer_id}")
        
        # Calculate start of current month
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        
        # Fetch all statistics in parallel
        # Cases
        active_cases = supabase.table('cases')\
            .select('id', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .eq('status', 'active')\
            .execute()
        
        pending_cases = supabase.table('cases')\
            .select('id', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .eq('status', 'pending')\
            .execute()
        
        total_cases = supabase.table('cases')\
            .select('id', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .execute()
        
        # Hearings
        total_hearings = supabase.table('hearings')\
            .select('id', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .execute()
          # Upcoming hearings (next 7 days)
        upcoming_hearings = supabase.table('hearings')\
            .select('id', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .gte('hearing_date', now.isoformat())\
            .execute()
        
        # Tasks
        total_tasks = supabase.table('tasks')\
            .select('id', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .in_('status', ['pending', 'in_progress'])\
            .execute()
        
        in_progress_tasks = supabase.table('tasks')\
            .select('id', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .eq('status', 'in_progress')\
            .execute()
        
        overdue_tasks = supabase.table('tasks')\
            .select('id', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .lt('execution_date', now.isoformat())\
            .neq('status', 'completed')\
            .execute()
        
        # Clients
        total_clients = supabase.table('clients')\
            .select('id', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .execute()
        
        new_clients = supabase.table('clients')\
            .select('id', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .gte('created_at', start_of_month.isoformat())\
            .execute()
        
        stats = {
            'cases': {
                'total': total_cases.count or 0,
                'active': active_cases.count or 0,
                'pending': pending_cases.count or 0
            },
            'hearings': {
                'total': total_hearings.count or 0,
                'upcoming': upcoming_hearings.count or 0
            },
            'tasks': {
                'total': total_tasks.count or 0,
                'in_progress': in_progress_tasks.count or 0,
                'overdue': overdue_tasks.count or 0
            },
            'clients': {
                'total': total_clients.count or 0,
                'new_this_month': new_clients.count or 0
            }
        }
        
        logger.info(f"✅ Dashboard stats fetched successfully: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch dashboard stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard statistics: {str(e)}"
        )


@router.get("/recent-cases")
async def get_recent_cases(
    limit: int = 5,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> dict:
    """
    Get recent cases for current lawyer
    
    Args:
        limit: Number of cases to return (default 5)
    """
    try:
        lawyer_id = current_user['id']
        supabase = get_supabase_client()
        
        result = supabase.table('cases')\
            .select('*')\
            .eq('lawyer_id', lawyer_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            'cases': result.data,
            'count': len(result.data)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch recent cases: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch recent cases: {str(e)}"
        )


@router.get("/upcoming-hearings")
async def get_upcoming_hearings(
    limit: int = 5,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> dict:
    """
    Get upcoming hearings for current lawyer
    
    Args:
        limit: Number of hearings to return (default 5)
    """
    try:
        lawyer_id = current_user['id']
        supabase = get_supabase_client()
        now = datetime.now()
        
        result = supabase.table('hearings')\
            .select('*')\
            .eq('lawyer_id', lawyer_id)\
            .gte('hearing_date', now.isoformat())\
            .order('hearing_date', desc=False)\
            .limit(limit)\
            .execute()
        
        return {
            'hearings': result.data,
            'count': len(result.data)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch upcoming hearings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch upcoming hearings: {str(e)}"
        )


@router.get("/calendar-events")
async def get_calendar_events(
    start_date: str,
    end_date: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> dict:
    """
    Get calendar events (hearings + tasks) for date range
    
    Args:
        start_date: Start of range (ISO 8601 format)
        end_date: End of range (ISO 8601 format)
        
    Returns:
        Dictionary with events list containing hearings and tasks
    """
    try:
        lawyer_id = current_user['id']
        supabase = get_supabase_client()
        
        logger.info(f"📅 Fetching calendar events from {start_date} to {end_date}")
        
        # 1. Fetch cases for lookup
        cases_result = supabase.table('cases')\
            .select('id, subject, case_number, court_name, clients(full_name)')\
            .eq('lawyer_id', lawyer_id)\
            .execute()
        
        # Create lookup map
        cases_map = {}
        if cases_result.data:
            for case in cases_result.data:
                client_name = None
                if case.get('clients'):
                    if isinstance(case['clients'], list) and len(case['clients']) > 0:
                        client_name = case['clients'][0].get('full_name')
                    elif isinstance(case['clients'], dict):
                        client_name = case['clients'].get('full_name')
                
                cases_map[case['id']] = {
                    'subject': case.get('subject'),
                    'case_number': case.get('case_number'),
                    'court_name': case.get('court_name'),
                    'client_name': client_name
                }
        
        # 2. Fetch hearings
        hearings_result = supabase.table('hearings')\
            .select('id, hearing_date, hearing_time, case_id')\
            .eq('lawyer_id', lawyer_id)\
            .gte('hearing_date', start_date)\
            .lte('hearing_date', end_date)\
            .execute()
        
        # 3. Fetch tasks
        tasks_result = supabase.table('tasks')\
            .select('id, title, execution_date, priority, case_id')\
            .eq('lawyer_id', lawyer_id)\
            .gte('execution_date', start_date)\
            .lte('execution_date', end_date)\
            .execute()
        
        # 4. Format events
        events = []
        
        # Format hearings
        if hearings_result.data:
            for h in hearings_result.data:
                case_info = cases_map.get(h.get('case_id'), {})
                title = 'جلسة'
                if h.get('hearing_time'):
                    title += f" الساعة {h['hearing_time']}"
                if case_info.get('client_name'):
                    title += f" للعميل {case_info['client_name']}"
                if case_info.get('case_number'):
                    title += f" - قضية رقم {case_info['case_number']}"
                if case_info.get('court_name'):
                    title += f" - {case_info['court_name']}"
                
                if not case_info:
                    title = 'جلسة (بدون تفاصيل)'
                
                events.append({
                    'id': h['id'],
                    'type': 'hearing',
                    'date': h['hearing_date'],
                    'title': title,
                    'time': h.get('hearing_time'),
                    'case_id': h.get('case_id'),
                    'case_title': case_info.get('subject'),
                    'client_name': case_info.get('client_name')
                })
        
        # Format tasks
        if tasks_result.data:
            for t in tasks_result.data:
                case_info = cases_map.get(t.get('case_id'), {})
                events.append({
                    'id': t['id'],
                    'type': 'task',
                    'date': t['execution_date'],
                    'title': t.get('title'),
                    'priority': t.get('priority'),
                    'case_id': t.get('case_id'),
                    'case_title': case_info.get('subject'),
                    'client_name': case_info.get('client_name')
                })
        
        logger.info(f"✅ Found {len(events)} calendar events")
        return {'events': events}
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch calendar events: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch calendar events: {str(e)}"
        )
