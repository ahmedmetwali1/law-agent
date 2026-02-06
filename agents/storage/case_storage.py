"""
Case Storage Module
إدارة حفظ وتحميل ملفات القضايا

Handles saving and loading case files to/from Supabase Storage or local filesystem
"""

from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime
from pathlib import Path
import os

from ..config.database import db
from ..config.settings import settings

logger = logging.getLogger(__name__)


class CaseStorage:
    """
    Case Storage Manager (Database Only)
    إدارة حفظ ملفات القضايا (قاعدة البيانات فقط)
    """
    
    def __init__(self, use_supabase: bool = True):
        """
        Initialize case storage
        """
        self.use_supabase = use_supabase
        self.client = db.client # Use global client
        
        # Setup local storage path if needed
        self.local_storage_dir = Path("data/cases")
        if not self.use_supabase:
             self.local_storage_dir.mkdir(parents=True, exist_ok=True)
             
        # Setup supabase config
        self.bucket_name = settings.cases_bucket
        self.storage_path = "cases/"
             
        logger.info(f"✅ CaseStorage initialized (Mode: {'Supabase' if use_supabase else 'Local'})")
    
    def save_case(self, case_data: Dict[str, Any]) -> str:
        """
        Save case to Database (Upsert)
        
        Args:
            case_data: Complete case data dictionary
            
        Returns:
            Case ID
        """
        case_id = case_data.get("case_id") or case_data.get("id")
        if not case_id:
            raise ValueError("Case data must include 'case_id'")
        
        # Ensure updated_at
        case_data["updated_at"] = datetime.now().isoformat()
        if "created_at" not in case_data:
             case_data["created_at"] = datetime.now().isoformat()

        # Prepare DB Payload (Map fields if necessary)
        # Assuming case_data structure matches DB schema or is a superset
        # We need to extract columns that exist in the table
        
        db_data = {
            "id": case_id,
            "client_id": case_data.get("client_id"),
            "lawyer_id": case_data.get("lawyer_id"),
            "case_number": case_data.get("case_number"),
            "court_name": case_data.get("court_name"),
            "case_type": case_data.get("case_type"),
            "status": case_data.get("status", "pending"),
            "subject": case_data.get("subject"),
            "description": case_data.get("description") or case_data.get("facts"), # Map 'facts' to description if needed
            "metadata": case_data.get("metadata", {}), # Store extra fields in JSONB
            "updated_at": case_data["updated_at"]
        }
        
        # If 'facts' is passed and not description, ensure it's saved
        if not db_data["description"] and "facts" in case_data:
             db_data["description"] = case_data["facts"]

        try:
            from ..config.settings import TableNames
            
            # Upsert into cases table
            result = self.client.table(TableNames.CASES).upsert(db_data).execute()
            
            if result.data:
                logger.info(f"✅ Saved case to DB: {case_id}")
                return case_id
            
            raise Exception("No data returned from upsert")
            
        except Exception as e:
            logger.error(f"❌ Failed to save case to DB: {e}")
            raise e
    
    def load_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Load case from Database
        """
        try:
            from ..config.settings import TableNames
            
            response = self.client.table(TableNames.CASES)\
                .select("*, clients(full_name)")\
                .eq("id", case_id)\
                .single()\
                .execute()
                
            if response.data:
                # Normalize data structure to match expected "Case Data" format
                data = response.data
                data["case_id"] = data["id"]
                data["client_name"] = data.get("clients", {}).get("full_name")
                logger.info(f"✅ Loaded case from DB: {case_id}")
                return data
                
            logger.warning(f"⚠️ Case not found: {case_id}")
            return None
                
        except Exception as e:
            logger.error(f"❌ Failed to load case from DB: {e}")
            return None

    # Legacy methods for compatibility (Redirect to DB methods)
    def _save_to_supabase(self, *args): pass
    def _save_to_local(self, *args): pass
    def _load_from_supabase(self, *args): return None
    def _load_from_local(self, *args): return None
    
    def update_case_status(self, case_id: str, status: str) -> bool:
        """
        Update case status
        
        Args:
            case_id: Case ID
            status: New status
            
        Returns:
            True if successful
        """
        case_data = self.load_case(case_id)
        if not case_data:
            logger.error(f"❌ Cannot update status - case not found: {case_id}")
            return False
        
        case_data["status"] = status
        case_data["status_updated_at"] = datetime.now().isoformat()
        
        self.save_case(case_data)
        logger.info(f"✅ Updated case status: {case_id} -> {status}")
        return True

    def update_case(self, case_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update generic case fields
        
        Args:
            case_id: Case ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated case data or None
        """
        case_data = self.load_case(case_id)
        if not case_data:
            logger.error(f"❌ Cannot update case - not found: {case_id}")
            return None
            
        # Apply updates
        case_data.update(updates)
        case_data["updated_at"] = datetime.now().isoformat()
        
        # Save (this will also sync to DB)
        self.save_case(case_data)
        logger.info(f"✅ Updated case fields for: {case_id}")
        return case_data
    
    def list_cases(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all cases
        
        Args:
            limit: Maximum number of cases to return
            
        Returns:
            List of case metadata
        """
        if self.use_supabase:
            return self._list_supabase_cases(limit)
        else:
            return self._list_local_cases(limit)
    
    def _list_supabase_cases(self, limit: int) -> List[Dict[str, Any]]:
        """List cases from Supabase"""
        try:
            bucket = db.get_bucket(self.bucket_name)
            files = bucket.list(self.storage_path)
            
            cases = []
            for file in files[:limit]:
                if file['name'].endswith('.json'):
                    case_id = file['name'].replace('.json', '')
                    cases.append({
                        "case_id": case_id,
                        "file_name": file['name'],
                        "created_at": file.get('created_at'),
                        "updated_at": file.get('updated_at'),
                        "size": file.get('size')
                    })
            
            logger.info(f"✅ Listed {len(cases)} cases from Supabase")
            return cases
            
        except Exception as e:
            logger.error(f"❌ Failed to list Supabase cases: {e}")
            return []
    
    def _list_local_cases(self, limit: int) -> List[Dict[str, Any]]:
        """List cases from local filesystem"""
        try:
            cases = []
            
            for file_path in self.local_storage_dir.glob("*.json"):
                case_id = file_path.stem
                stat = file_path.stat()
                
                cases.append({
                    "case_id": case_id,
                    "file_name": file_path.name,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size": stat.st_size
                })
                
                if len(cases) >= limit:
                    break
            
            logger.info(f"✅ Listed {len(cases)} cases from local storage")
            return cases
            
        except Exception as e:
            logger.error(f"❌ Failed to list local cases: {e}")
            return []
    
    def delete_case(self, case_id: str) -> bool:
        """
        Delete a case
        
        Args:
            case_id: Case ID to delete
            
        Returns:
            True if successful
        """
        if self.use_supabase:
            success = self._delete_from_supabase(case_id)
        else:
            success = self._delete_from_local(case_id)
        
        if success:
            logger.info(f"✅ Deleted case: {case_id}")
        else:
            logger.error(f"❌ Failed to delete case: {case_id}")
        
        return success
    
    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Alias for load_case to match tool expectations"""
        return self.load_case(case_id)

    def get_case_by_id(self, case_id: str, lawyer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific case by ID with ownership verification
        
        Args:
            case_id: Case ID
            lawyer_id: Lawyer ID for ownership check
            
        Returns:
            Case data or None if not found/unauthorized
        """
        if self.use_supabase:
            try:
                from ..config.settings import TableNames
                
                response = db.client.table(TableNames.CASES)\
                    .select("*, clients(full_name)")\
                    .eq("id", case_id)\
                    .eq("lawyer_id", lawyer_id)\
                    .single()\
                    .execute()
                    
                return response.data if response.data else None
            except Exception as e:
                logger.error(f"❌ Failed to get case by ID: {e}")
                return None
        else:
            # Local fallback - load and verify
            case = self.load_case(case_id)
            if case and case.get("lawyer_id") == lawyer_id:
                return case
            return None

    def get_cases_by_client(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Get all cases for a specific client
        
        Args:
            client_id: Client UUID
            
        Returns:
            List of cases
        """
        if self.use_supabase:
            return self._get_cases_by_client_supabase(client_id)
        else:
            return self._get_cases_by_client_local(client_id)

    def _get_cases_by_client_supabase(self, client_id: str) -> List[Dict[str, Any]]:
        """Get client cases from Supabase"""
        try:
            # Note: storage doesn't support querying by content easily
            # We rely on DB table 'cases' for queries, but here we are using Storage bucket??
            # Wait, if we use Supabase *Storage* (files), we can't query by client_id easily without metadata.
            # But normally we should use Supabase *Database* for queries.
            
            # Let's try to query the 'cases' table directly if available
            try:
                from ..config.settings import TableNames
                response = db.client.table(TableNames.CASES).select("*").eq("client_id", client_id).execute()
                return response.data if response.data else []
            except:
                # Fallback to listing all files (slow)
                all_cases = self.list_cases(limit=100)
                client_cases = []
                for meta in all_cases:
                    case = self.load_case(meta['case_id'])
                    if case and case.get('client_id') == client_id:
                        client_cases.append(case)
                return client_cases
                
        except Exception as e:
            logger.error(f"❌ Failed to get client cases from Supabase: {e}")
            return []

    def _get_cases_by_client_local(self, client_id: str) -> List[Dict[str, Any]]:
        """Get client cases from local storage"""
        try:
            client_cases = []
            for file_path in self.local_storage_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        case_data = json.load(f)
                        if case_data.get("client_id") == client_id:
                            client_cases.append(case_data)
                except:
                    continue
            return client_cases
        except Exception as e:
            logger.error(f"❌ Failed to get client cases locally: {e}")
            return []

    def _delete_from_supabase(self, case_id: str) -> bool:
        """Delete from Supabase storage"""
        try:
            file_path = f"{self.storage_path}{case_id}.json"
            bucket = db.get_bucket(self.bucket_name)
            bucket.remove([file_path])
            return True
        except Exception as e:
            logger.error(f"❌ Supabase delete failed: {e}")
            return False
    
    def _delete_from_local(self, case_id: str) -> bool:
        """Delete from local filesystem"""
        try:
            file_path = self.local_storage_dir / f"{case_id}.json"
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Local delete failed: {e}")
            return False
    
    def get_case_file_path(self, case_id: str) -> str:
        """Get the file path/URL for a case"""
        if self.use_supabase:
            return f"supabase://{self.bucket_name}/{self.storage_path}{case_id}.json"
        else:
            return str(self.local_storage_dir / f"{case_id}.json")



    def get_cases_by_lawyer(self, lawyer_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all cases for a specific lawyer from DB
        
        Args:
            lawyer_id: Lawyer UUID
            limit: Max results
            
        Returns:
            List of cases with client details
        """
        if self.use_supabase:
            try:
                from ..config.settings import TableNames
                
                # Query DB table directly for relational data
                response = db.client.table(TableNames.CASES)\
                    .select("*, clients(full_name)")\
                    .eq("lawyer_id", lawyer_id)\
                    .order("created_at", desc=True)\
                    .limit(limit)\
                    .execute()
                    
                return response.data if response.data else []
            except Exception as e:
                logger.error(f"❌ Failed to get lawyer cases from DB: {e}")
                return []
        else:
            # Local storage fallback (no lawyer_id filtering really possible efficiently without metadata index)
            # Just return all local cases
            return self.list_cases(limit)

    def create_case_in_db(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a case directly in the DB
        
        Args:
            case_data: Case data dictionary
            
        Returns:
            Created case data
        """
        if self.use_supabase:
            try:
                from ..config.settings import TableNames
                
                # Ensure updated_at is set
                if "updated_at" not in case_data:
                    case_data["updated_at"] = datetime.now().isoformat()
                    
                response = db.client.table(TableNames.CASES)\
                    .insert(case_data)\
                    .select()\
                    .single()\
                    .execute()
                    
                if response.data:
                    logger.info(f"✅ Created case in DB: {response.data.get('id')}")
                    return response.data
                raise Exception("No data returned from insert")
                
            except Exception as e:
                logger.error(f"❌ Failed to create case in DB: {e}")
                raise e
        else:
            # Local fallback - creates JSON file
            self.save_case(case_data)
            return case_data

    def search_cases(self, lawyer_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search cases for a lawyer
        """
        if self.use_supabase:
            try:
                from ..config.settings import TableNames
                
                # Search case_number, subject, court_name
                # Note: Supabase 'or' syntax: "col1.ilike.%q%,col2.ilike.%q%"
                or_query = f"case_number.ilike.%{query}%,subject.ilike.%{query}%,court_name.ilike.%{query}%"
                
                response = db.client.table(TableNames.CASES)\
                    .select("*, clients(full_name)")\
                    .eq("lawyer_id", lawyer_id)\
                    .or_(or_query)\
                    .limit(limit)\
                    .execute()
                    
                return response.data if response.data else []
            except Exception as e:
                logger.error(f"❌ Failed to search cases: {e}")
                return []
        return []

__all__ = ["CaseStorage"]
