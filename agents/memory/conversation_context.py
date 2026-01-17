"""
Conversation Context Manager
إدارة سياق المحادثة والذاكرة المؤقتة
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConversationContext:
    """
    Manages conversation context and entity references
    يدير سياق المحادثة والإشارات للكيانات
    """
    
    def __init__(self, ttl_minutes: int = 30):
        """
        Initialize conversation context
        
        Args:
            ttl_minutes: Time-to-live for context items in minutes
        """
        self.ttl_minutes = ttl_minutes
        
        # Entity tracking
        self.mentioned_clients: Dict[str, Dict[str, Any]] = {}
        self.mentioned_cases: Dict[str, Dict[str, Any]] = {}
        self.mentioned_hearings: Dict[str, Dict[str, Any]] = {}
        
        # Recent actions
        self.last_action: Optional[str] = None
        self.last_action_time: Optional[datetime] = None
        self.last_entity_type: Optional[str] = None
        self.last_entity_id: Optional[str] = None
        
        # Conversation flow
        self.topic: Optional[str] = None
        self.intent: Optional[str] = None
        
        logger.info(f"✅ ConversationContext initialized (TTL: {ttl_minutes}min)")
    
    def remember_client(self, client_data: Dict[str, Any]):
        """
        Remember a client mentioned in conversation
        
        Args:
            client_data: Client information with at least 'id' and 'full_name'
        """
        client_id = client_data.get('id')
        client_name = client_data.get('full_name', 'Unknown')
        
        if client_id:
            self.mentioned_clients[client_name] = {
                'id': client_id,
                'data': client_data,
                'timestamp': datetime.now()
            }
            
            # Update last entity
            self.last_entity_type = 'client'
            self.last_entity_id = client_id
            
            logger.info(f"💭 Remembered client: {client_name} ({client_id})")
    
    def remember_case(self, case_data: Dict[str, Any]):
        """Remember a case mentioned in conversation"""
        case_id = case_data.get('id')
        case_number = case_data.get('case_number', 'Unknown')
        
        if case_id:
            self.mentioned_cases[case_number] = {
                'id': case_id,
                'data': case_data,
                'timestamp': datetime.now()
            }
            
            self.last_entity_type = 'case'
            self.last_entity_id = case_id
            
            logger.info(f"💭 Remembered case: {case_number} ({case_id})")
    
    def remember_hearing(self, hearing_data: Dict[str, Any]):
        """Remember a hearing mentioned in conversation"""
        hearing_id = hearing_data.get('id')
        
        if hearing_id:
            key = f"hearing_{hearing_id}"
            self.mentioned_hearings[key] = {
                'id': hearing_id,
                'data': hearing_data,
                'timestamp': datetime.now()
            }
            
            self.last_entity_type = 'hearing'
            self.last_entity_id = hearing_id
            
            logger.info(f"💭 Remembered hearing: {hearing_id}")
    
    def set_last_action(self, action: str):
        """Record the last action performed"""
        self.last_action = action
        self.last_action_time = datetime.now()
        logger.debug(f"📝 Last action: {action}")
    
    def resolve_reference(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Resolve pronouns and references to entities
        
        Examples:
            "له" → last mentioned client
            "لها" → last mentioned client (female)
            "للقضية" → last mentioned case
            
        Args:
            text: User input text
            
        Returns:
            Referenced entity data or None
        """
        text_lower = text.lower()
        
        # Client references
        client_refs = ['له', 'لها', 'للموكل', 'للعميل', 'لهذا الموكل', 'لهذا العميل']
        if any(ref in text_lower for ref in client_refs):
            if self.last_entity_type == 'client' and self.last_entity_id:
                logger.info(f"✅ Resolved reference → client: {self.last_entity_id}")
                return {
                    'type': 'client',
                    'id': self.last_entity_id
                }
            
            # Fallback: get last mentioned client
            if self.mentioned_clients:
                last_client = list(self.mentioned_clients.values())[-1]
                logger.info(f"✅ Resolved reference → client: {last_client['id']}")
                return {
                    'type': 'client',
                    'id': last_client['id'],
                    'data': last_client['data']
                }
        
        # Case references
        case_refs = ['للقضية', 'لهذه القضية', 'فيها']
        if any(ref in text_lower for ref in case_refs):
            if self.last_entity_type == 'case' and self.last_entity_id:
                logger.info(f"✅ Resolved reference → case: {self.last_entity_id}")
                return {
                    'type': 'case',
                    'id': self.last_entity_id
                }
        
        logger.debug("❌ Could not resolve reference")
        return None
    
    def get_last_entity(self) -> Optional[Dict[str, Any]]:
        """Get the last mentioned entity"""
        if self.last_entity_id and self.last_entity_type:
            return {
                'type': self.last_entity_type,
                'id': self.last_entity_id
            }
        return None
    
    def cleanup_old_items(self):
        """Remove items older than TTL"""
        cutoff_time = datetime.now() - timedelta(minutes=self.ttl_minutes)
        
        # Cleanup clients
        self.mentioned_clients = {
            name: data for name, data in self.mentioned_clients.items()
            if data['timestamp'] > cutoff_time
        }
        
        # Cleanup cases
        self.mentioned_cases = {
            num: data for num, data in self.mentioned_cases.items()
            if data['timestamp'] > cutoff_time
        }
        
        # Cleanup hearings
        self.mentioned_hearings = {
            key: data for key, data in self.mentioned_hearings.items()
            if data['timestamp'] > cutoff_time
        }
    
    def get_context_summary(self) -> str:
        """Get summary of current context for LLM"""
        parts = []
        
        if self.mentioned_clients:
            client_list = ', '.join(self.mentioned_clients.keys())
            parts.append(f"Mentioned clients: {client_list}")
        
        if self.mentioned_cases:
            case_list = ', '.join(self.mentioned_cases.keys())
            parts.append(f"Mentioned cases: {case_list}")
        
        if self.last_action:
            parts.append(f"Last action: {self.last_action}")
        
        if self.topic:
            parts.append(f"Current topic: {self.topic}")
        
        return "\n".join(parts) if parts else "No active context"
    
    def clear(self):
        """Clear all context"""
        self.mentioned_clients.clear()
        self.mentioned_cases.clear()
        self.mentioned_hearings.clear()
        self.last_action = None
        self.last_entity_type = None
        self.last_entity_id = None
        self.topic = None
        logger.info("🧹 Context cleared")


__all__ = ['ConversationContext']
