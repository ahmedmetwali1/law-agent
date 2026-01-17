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
    Case Storage Manager
    إدارة حفظ ملفات القضايا
    """
    
    def __init__(self, use_supabase: bool = None):
        """
        Initialize case storage
        
        Args:
            use_supabase: Use Supabase storage if True, local filesystem if False.
                         If None, uses settings.use_supabase_storage
        """
        # Use setting if not explicitly specified
        if use_supabase is None:
            self.use_supabase = settings.use_supabase_storage
        else:
            self.use_supabase = use_supabase
            
        self.bucket_name = settings.cases_bucket
        self.storage_path = settings.storage_path
        
        # Always initialize local storage dir for fallback
        self.local_storage_dir = Path("e:/law/cases")
        self.local_storage_dir.mkdir(parents=True, exist_ok=True)
        
        if self.use_supabase:
            logger.info(f"☁️ Using Supabase storage: {self.bucket_name} (with local fallback)")
        else:
            logger.info(f"📁 Using local storage: {self.local_storage_dir}")
    
    def save_case(self, case_data: Dict[str, Any]) -> str:
        """
        Save case to storage
        
        Args:
            case_data: Complete case data dictionary
            
        Returns:
            File path or URL
        """
        case_id = case_data.get("case_id")
        if not case_id:
            raise ValueError("Case data must include 'case_id'")
        
        # Add timestamp
        case_data["last_updated"] = datetime.now().isoformat()
        
        # Convert to JSON
        json_data = json.dumps(case_data, ensure_ascii=False, indent=2)
        
        # Save based on storage type
        if self.use_supabase:
            result = self._save_to_supabase(case_id, json_data)
        else:
            result = self._save_to_local(case_id, json_data)
            
        # ALWAYS try to sync metadata to DB for relational integrity (Hearings keys)
        try:
            self._sync_to_db(case_data)
        except Exception as e:
            logger.error(f"⚠️ Failed to sync case to DB: {e}")
            
        return result
    
    def _sync_to_db(self, case_data: Dict[str, Any]):
        """Sync case metadata to Supabase DB table"""
        try:
            from ..config.database import db
            from ..config.settings import TableNames
            
            db_data = {
                "id": case_data.get("case_id"),
                "client_id": case_data.get("client_id"),
                "case_number": case_data.get("case_number"),
                "court_name": case_data.get("court_name"),
                "case_type": case_data.get("case_type"),
                "status": case_data.get("status"),
                "updated_at": datetime.now().isoformat()
            }
            
            # Upsert into cases table
            db.client.table(TableNames.CASES).upsert(db_data).execute()
            logger.info(f"✅ Synced case metadata to DB: {case_data.get('case_id')}")
            
        except ImportError:
            pass
        except Exception as e:
            raise e

    def _save_to_supabase(self, case_id: str, json_data: str) -> str:
        """Save to Supabase storage"""
        try:
            file_path = f"{self.storage_path}{case_id}.json"
            
            # Upload to Supabase
            bucket = db.get_bucket(self.bucket_name)
            
            # Check if file exists and update or create
            try:
                # Try to update existing file
                bucket.update(
                    path=file_path,
                    file=json_data.encode('utf-8'),
                    file_options={"content-type": "application/json"}
                )
                logger.info(f"✅ Updated case in Supabase: {file_path}")
            except:
                # File doesn't exist, create it
                bucket.upload(
                    path=file_path,
                    file=json_data.encode('utf-8'),
                    file_options={"content-type": "application/json"}
                )
                logger.info(f"✅ Created case in Supabase: {file_path}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"❌ Failed to save to Supabase: {e}")
            # Fallback to local
            logger.warning("⚠️ Falling back to local storage")
            return self._save_to_local(case_id, json_data)
    
    def _save_to_local(self, case_id: str, json_data: str) -> str:
        """Save to local filesystem"""
        try:
            file_path = self.local_storage_dir / f"{case_id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_data)
            
            logger.info(f"✅ Saved case locally: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to save locally: {e}")
            raise
    
    def load_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Load case from storage
        
        Args:
            case_id: Case ID to load
            
        Returns:
            Case data dictionary or None if not found
        """
        if self.use_supabase:
            case_data = self._load_from_supabase(case_id)
            if case_data:
                return case_data
            # Fallback to local
            logger.warning("⚠️ Not found in Supabase, trying local...")
        
        return self._load_from_local(case_id)
    
    def _load_from_supabase(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Load from Supabase storage"""
        try:
            file_path = f"{self.storage_path}{case_id}.json"
            
            bucket = db.get_bucket(self.bucket_name)
            response = bucket.download(file_path)
            
            if response:
                json_data = response.decode('utf-8')
                case_data = json.loads(json_data)
                logger.info(f"✅ Loaded case from Supabase: {case_id}")
                return case_data
            else:
                logger.warning(f"⚠️ Case not found in Supabase: {case_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to load from Supabase: {e}")
            return None
    
    def _load_from_local(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Load from local filesystem"""
        try:
            file_path = self.local_storage_dir / f"{case_id}.json"
            
            if not file_path.exists():
                logger.warning(f"⚠️ Case not found locally: {case_id}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
            
            logger.info(f"✅ Loaded case from local: {case_id}")
            return case_data
            
        except Exception as e:
            logger.error(f"❌ Failed to load locally: {e}")
            return None
    
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


__all__ = ["CaseStorage"]
