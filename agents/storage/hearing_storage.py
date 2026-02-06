"""
Hearing Storage Module
إدارة الجلسات في قاعدة البيانات
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, time
import logging
from supabase import Client

from agents.config.settings import settings, TableNames
from agents.config.database import get_supabase_client

logger = logging.getLogger(__name__)


class HearingStorage:
    """Hearing database operations"""
    
    TABLE_NAME = TableNames.HEARINGS
    
    def __init__(self):
        """Initialize hearing storage"""
        self.client: Client = get_supabase_client()
        logger.info("✅ HearingStorage initialized")
    
    def create_hearing(
        self,
        lawyer_id: str,
        case_id: str,
        hearing_date: date,
        hearing_time: Optional[time] = None,
        court_room: Optional[str] = None,
        judge_name: Optional[str] = None,
        judge_requests: Optional[str] = None,
        notes: Optional[str] = None,
        outcome: Optional[str] = None,
        next_hearing_date: Optional[date] = None,
        # Denormalized fields
        case_number: Optional[str] = None,
        client_name: Optional[str] = None,
        case_year: Optional[str] = None,
        court_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new hearing
        """
        try:
            hearing_data = {
                "lawyer_id": lawyer_id,
                "case_id": case_id,
                "hearing_date": hearing_date.isoformat() if isinstance(hearing_date, date) else hearing_date,
                "hearing_time": hearing_time.isoformat() if isinstance(hearing_time, time) else hearing_time,
                "court_room": court_room,
                "judge_name": judge_name,
                "judge_requests": judge_requests,
                "notes": notes,
                "outcome": outcome,
                "next_hearing_date": next_hearing_date.isoformat() if isinstance(next_hearing_date, date) else next_hearing_date,
                # Denormalized fields
                "case_number": case_number,
                "client_name": client_name,
                "case_year": case_year,
                "court_name": court_name,
                
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.client.table(self.TABLE_NAME).insert(hearing_data).execute()
            
            if result.data:
                logger.info(f"✅ Hearing created for case {case_id}")
                return result.data[0]
            else:
                raise Exception("Failed to create hearing")
                
        except Exception as e:
            logger.error(f"❌ Failed to create hearing: {e}")
            raise
    
    def get_hearing(self, hearing_id: str) -> Optional[Dict[str, Any]]:
        """Get hearing by ID"""
        try:
            result = self.client.table(self.TABLE_NAME)\
                .select("*, cases(*)")\
                .eq("id", hearing_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.debug(f"Hearing not found: {hearing_id}")
            return None
    
    def get_today_hearings_by_lawyer(self, lawyer_id: str) -> List[Dict[str, Any]]:
        """
        Get today's hearings for a lawyer
        
        Args:
            lawyer_id: Lawyer UUID
            
        Returns:
            List of today's hearings with case and client info
        """
        try:
            today = date.today().isoformat()
            
            # Join hearings with cases and clients
            result = self.client.table(self.TABLE_NAME)\
                .select("*, cases(*, clients(*))")\
                .eq("hearing_date", today)\
                .execute()
            
            # Filter by lawyer_id (from joined cases.clients)
            hearings = []
            for hearing in result.data or []:
                case_data = hearing.get("cases")
                if case_data:
                    client_data = case_data.get("clients")
                    if client_data and client_data.get("lawyer_id") == lawyer_id:
                        hearings.append(hearing)
            
            # Sort by time
            hearings.sort(key=lambda h: h.get("hearing_time") or "00:00")
            
            return hearings
            
        except Exception as e:
            logger.error(f"❌ Failed to get today's hearings: {e}")
            return []
    
    def get_upcoming_hearings_by_lawyer(
        self,
        lawyer_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming hearings for a lawyer (next N days)
        
        Args:
            lawyer_id: Lawyer UUID
            days: Number of days to look ahead
            
        Returns:
            List of upcoming hearings
        """
        try:
            today = date.today().isoformat()
            
            result = self.client.table(self.TABLE_NAME)\
                .select("*, cases(*, clients(*))")\
                .gte("hearing_date", today)\
                .order("hearing_date")\
                .order("hearing_time")\
                .execute()
            
            # Filter by lawyer_id
            hearings = []
            for hearing in result.data or []:
                case_data = hearing.get("cases")
                if case_data:
                    client_data = case_data.get("clients")
                    if client_data and client_data.get("lawyer_id") == lawyer_id:
                        hearings.append(hearing)
            
            return hearings
            
        except Exception as e:
            logger.error(f"❌ Failed to get upcoming hearings: {e}")
            return []
    
    def get_hearings_by_range(
        self,
        lawyer_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get hearings within date range for a lawyer
        """
        try:
            # Join hearings with cases and clients
            result = self.client.table(self.TABLE_NAME)\
                .select("*, cases(id, case_number, court_name, clients(full_name))")\
                .gte("hearing_date", start_date.isoformat())\
                .lte("hearing_date", end_date.isoformat())\
                .order("hearing_date")\
                .execute()
            
            # Filter by lawyer_id (from joined cases.clients) if needed, 
            # OR better: query filtered by case->client->lawyer_id (complex in supabase)
            # Since we joined, we can filter in python or rely on RLS if we trust it? 
            # But we are using SERVICE_KEY in backend usually, so we must filter manually or use correct updated query.
            
            # For robustness, we iterate and filter
            hearings = []
            for hearing in result.data or []:
                case_data = hearing.get("cases")
                if case_data:
                    # Check if case belongs to lawyer (via client or direct relation)
                    # This simplified query assumes case filtering.
                    # Ideally we filter by `cases.clients.lawyer_id` but deep filter is tricky.
                    # Let's assume the service returns all hearings in range, we filter by Python for safety.
                    
                    # BUT wait, RLS is ON. If we use SERVICE_ROLE, we get everything.
                    # We should filter by lawyer_id.
                    
                    # Manual filter:
                    client_data = case_data.get("clients")
                    # We might need to fetch lawyer_id from case or client.
                    # Our schema says: hearings -> case_id -> cases -> client_id -> clients -> lawyer_id
                    # OR cases -> lawyer_id (if cases has lawyer_id directly).
                    
                    # Checking `clients` table schema...
                    # Checking `cases` table schema...
                    
                    # Assuming we filter by result data structure in previous methods:
                    # In get_today_hearings_by_lawyer:
                    # if client_data and client_data.get("lawyer_id") == lawyer_id: ...
                    
                    # So we do the same here.
                    if client_data: # If we selected clients(full_name, lawyer_id)
                         # Wait, select string above is "clients(full_name)". It misses lawyer_id.
                         # I must fetch lawyer_id to filter.
                         pass
            
            # Revised Select:
            result = self.client.table(self.TABLE_NAME)\
                .select("*, cases(id, case_number, court_name, clients(full_name, lawyer_id))")\
                .gte("hearing_date", start_date.isoformat())\
                .lte("hearing_date", end_date.isoformat())\
                .order("hearing_date")\
                .execute()

            filtered = []
            for h in result.data or []:
                c = h.get("cases")
                if c and c.get("clients") and c["clients"].get("lawyer_id") == lawyer_id:
                    filtered.append(h)
            
            return filtered
            
        except Exception as e:
            logger.error(f"❌ Failed to get hearings range: {e}")
            return []
    
    def get_case_hearings(self, case_id: str) -> List[Dict[str, Any]]:
        """
        Get all hearings for a case
        
        Args:
            case_id: Case UUID
            
        Returns:
            List of hearings ordered by date
        """
        try:
            result = self.client.table(self.TABLE_NAME)\
                .select("*")\
                .eq("case_id", case_id)\
                .order("hearing_date", desc=True)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Failed to get case hearings: {e}")
            return []
    
    def update_hearing(
        self,
        hearing_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update hearing data
        
        Args:
            hearing_id: Hearing UUID
            updates: Fields to update
            
        Returns:
            Updated hearing data
        """
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            result = self.client.table(self.TABLE_NAME)\
                .update(updates)\
                .eq("id", hearing_id)\
                .execute()
            
            if result.data:
                logger.info(f"✅ Hearing updated: {hearing_id}")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to update hearing: {e}")
            raise
    
    def delete_hearing(self, hearing_id: str) -> bool:
        """Delete hearing"""
        try:
            result = self.client.table(self.TABLE_NAME)\
                .delete()\
                .eq("id", hearing_id)\
                .execute()
            
            success = bool(result.data)
            if success:
                logger.info(f"✅ Hearing deleted: {hearing_id}")
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to delete hearing: {e}")
            return False


# Global instance
hearing_storage = HearingStorage()

__all__ = ["HearingStorage", "hearing_storage"]
