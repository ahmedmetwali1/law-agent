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
        case_id: str,
        hearing_date: date,
        hearing_time: Optional[time] = None,
        court_room: Optional[str] = None,
        judge_name: Optional[str] = None,
        judge_requests: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new hearing
        
        Args:
            case_id: Case UUID
            hearing_date: Date of hearing
            hearing_time: Time of hearing
            ... other fields
            
        Returns:
            Created hearing data
        """
        try:
            hearing_data = {
                "case_id": case_id,
                "hearing_date": hearing_date.isoformat() if isinstance(hearing_date, date) else hearing_date,
                "hearing_time": hearing_time.isoformat() if isinstance(hearing_time, time) else hearing_time,
                "court_room": court_room,
                "judge_name": judge_name,
                "judge_requests": judge_requests,
                "notes": notes,
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
