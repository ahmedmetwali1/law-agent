"""
Client Storage Module
إدارة الموكلين في قاعدة البيانات
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from supabase import Client

from agents.config.settings import settings, TableNames
from agents.config.database import get_supabase_client

logger = logging.getLogger(__name__)


class ClientStorage:
    """Client database operations with lawyer_id filtering"""
    
    TABLE_NAME = TableNames.CLIENTS
    
    def __init__(self):
        """Initialize client storage"""
        self.client: Client = get_supabase_client()
        logger.info("✅ ClientStorage initialized")
    
    def create_client(
        self,
        lawyer_id: str,
        full_name: str,
        national_id: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
        notes: Optional[str] = None,
        has_power_of_attorney: bool = False,
        power_of_attorney_number: Optional[str] = None,
        power_of_attorney_image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new client
        
        Args:
            lawyer_id: Lawyer's user ID (REQUIRED - security filter)
            full_name: Client's full name
            ... other fields
            
        Returns:
            Created client data
        """
        try:
            client_data = {
                "lawyer_id": lawyer_id,  # ⚠️ Always set
                "full_name": full_name,
                "national_id": national_id,
                "phone": phone,
                "email": email,
                "address": address,
                "notes": notes,
                "has_power_of_attorney": has_power_of_attorney,
                "power_of_attorney_number": power_of_attorney_number,
                "power_of_attorney_image_url": power_of_attorney_image_url,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.client.table(self.TABLE_NAME).insert(client_data).execute()
            
            if result.data:
                logger.info(f"✅ Client created: {full_name} for lawyer {lawyer_id}")
                return result.data[0]
            else:
                raise Exception("Failed to create client")
                
        except Exception as e:
            logger.error(f"❌ Failed to create client: {e}")
            raise
    
    def get_client(self, client_id: str, lawyer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get client by ID (with lawyer_id filter for security)
        
        Args:
            client_id: Client UUID
            lawyer_id: Lawyer UUID (security filter)
            
        Returns:
            Client data or None
        """
        try:
            result = self.client.table(self.TABLE_NAME)\
                .select("*")\
                .eq("id", client_id)\
                .eq("lawyer_id", lawyer_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.debug(f"Client not found: {client_id}")
            return None
    
    def get_clients_by_lawyer(self, lawyer_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all clients for a lawyer
        
        Args:
            lawyer_id: Lawyer UUID
            limit: Maximum results
            
        Returns:
            List of clients
        """
        try:
            result = self.client.table(self.TABLE_NAME)\
                .select("*")\
                .eq("lawyer_id", lawyer_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Failed to get clients: {e}")
            return []
    
    def search_clients(
        self,
        lawyer_id: str,
        query: str,
        search_fields: List[str] = ["full_name", "phone", "national_id", "email"]
    ) -> List[Dict[str, Any]]:
        """
        🔍 SMART MULTI-FIELD SEARCH with FLEXIBLE ARABIC MATCHING
        
        Features:
        - Searches: name, phone, email, address
        - Handles Arabic variations: أ/إ/ا, ة/ه, ى/ي
        - Fuzzy matching for typos
        - "Did you mean?" suggestions
        
        Args:
            lawyer_id: Lawyer UUID (security filter)
            query: Search query
            search_fields: Fields to search in
            
        Returns:
            List with:
            - exact_matches: Perfect matches
            - fuzzy_matches: Similar matches (normalized)
            - suggestions: "Did you mean?" list
        """
        try:
            from agents.utils.arabic_utils import normalize_arabic, find_similar_matches
            
            logger.info(f"🔍 Smart searching: '{query}' across multiple fields")
            
            # Normalize query for flexible matching
            normalized_query = normalize_arabic(query)
            
            # Try exact search first
            result = self.client.table(self.TABLE_NAME) \
                .select("*") \
                .eq("lawyer_id", lawyer_id) \
                .or_(
                    f"full_name.ilike.%{query}%,"
                    f"phone.ilike.%{query}%,"
                    f"email.ilike.%{query}%,"
                    f"address.ilike.%{query}%"
                ) \
                .order("created_at", desc=True) \
                .execute()
            
            exact_matches = result.data if result.data else []
            
            # If no exact matches, try fuzzy search
            fuzzy_matches = []
            if not exact_matches:
                logger.info("❌ No exact matches, trying fuzzy search...")
                
                # Get all clients for fuzzy matching
                all_clients = self.client.table(self.TABLE_NAME) \
                    .select("*") \
                    .eq("lawyer_id", lawyer_id) \
                    .order("created_at", desc=True) \
                    .execute()
                
                all_clients_data = all_clients.data if all_clients.data else []
                
                # Find similar names using fuzzy matching
                if all_clients_data:
                    client_names = [c.get('full_name', '') for c in all_clients_data if c.get('full_name')]
                    
                    similar = find_similar_matches(query, client_names, threshold=0.6)
                    
                    if similar:
                        logger.info(f"✅ Found {len(similar)} similar matches (fuzzy)")
                        
                        # Get clients with similar names
                        similar_names = [name for name, score in similar]
                        fuzzy_matches = [
                            c for c in all_clients_data 
                            if c.get('full_name') in similar_names
                        ]
            
            # Build response
            total_matches = exact_matches + fuzzy_matches
            
            if total_matches:
                logger.info(f"✅ Found {len(total_matches)} client(s) (exact: {len(exact_matches)}, fuzzy: {len(fuzzy_matches)})")
            else:
                logger.info(f"❌ No clients found matching: {query}")
            
            return total_matches
            
        except Exception as e:
            logger.error(f"❌ Failed to search clients: {e}")
            return []
    
    def update_client(
        self,
        client_id: str,
        lawyer_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update client data
        
        Args:
            client_id: Client UUID
            lawyer_id: Lawyer UUID (security filter)
            updates: Fields to update
            
        Returns:
            Updated client data
        """
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.now().isoformat()
            
            result = self.client.table(self.TABLE_NAME)\
                .update(updates)\
                .eq("id", client_id)\
                .eq("lawyer_id", lawyer_id)\
                .execute()
            
            if result.data:
                logger.info(f"✅ Client updated: {client_id}")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to update client: {e}")
            raise
    
    def delete_client(self, client_id: str, lawyer_id: str) -> bool:
        """
        Delete client
        
        Args:
            client_id: Client UUID
            lawyer_id: Lawyer UUID (security filter)
            
        Returns:
            Success status
        """
        try:
            result = self.client.table(self.TABLE_NAME)\
                .delete()\
                .eq("id", client_id)\
                .eq("lawyer_id", lawyer_id)\
                .execute()
            
            success = bool(result.data)
            if success:
                logger.info(f"✅ Client deleted: {client_id}")
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to delete client: {e}")
            return False
    
    def get_client_with_cases(self, client_id: str, lawyer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get client with their cases
        
        Args:
            client_id: Client UUID
            lawyer_id: Lawyer UUID
            
        Returns:
            Client data with cases list
        """
        try:
            # Get client
            client = self.get_client(client_id, lawyer_id)
            if not client:
                return None
            
            # Get cases for this client
            cases_result = self.client.table("cases")\
                .select("*")\
                .eq("client_id", client_id)\
                .execute()
            
            client["cases"] = cases_result.data if cases_result.data else []
            return client
            
        except Exception as e:
            logger.error(f"❌ Failed to get client with cases: {e}")
            return None


# Global instance
client_storage = ClientStorage()

__all__ = ["ClientStorage", "client_storage"]
