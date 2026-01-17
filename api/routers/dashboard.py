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
        
        upcoming_hearings = supabase.table('hearings')\
            .select('id', count='exact')\
            .eq('lawyer_id', lawyer_id)\
            .gte('date', now.isoformat())\
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
            .gte('date', now.isoformat())\
            .order('date', desc=False)\
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
