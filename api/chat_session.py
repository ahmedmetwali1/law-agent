"""
Chat Session Manager
إدارة جلسات المحادثة لجمع معلومات القضية

This module manages conversational sessions where the agent
asks questions to collect case information step-by-step.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
from datetime import datetime
import logging
import json

# Import tools
from agents.tools.quick_answer_tool import QuickAnswerTool
from agents.reasoning import IntelligentQueryGenerator, QuestionComplexity, LegalDomain

logger = logging.getLogger(__name__)


class ResponseType(str, Enum):
    """أنواع الاستجابة"""
    QUICK_ANSWER = "quick_answer"      # إجابة سريعة مباشرة
    DEEP_SEARCH = "deep_search"        # بحث عميق + إجابة موثقة
    CASE_STUDY = "case_study"          # دراسة قانونية كاملة (خطة)


class ConversationStage(str, Enum):
    """مراحل جمع المعلومات"""
    GREETING = "greeting"
    CASE_TYPE = "case_type"
    PARTIES = "parties"
    FACTS = "facts"
    ADDITIONAL_INFO = "additional_info"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"
    GENERAL_QA = "general_qa"


class SessionMemory:
    """
    Enhanced memory for chat sessions.
    Tracks confirmed facts and extracts entities.
    """
    
    def __init__(self):
        # Confirmed facts extracted from conversation
        self.confirmed_facts: Dict[str, Any] = {
            "case_type": None,
            "client_role": None,  # متهم، مدعي، شاهد
            "incident_date": None,
            "incident_location": None,
            "parties": [],
            "key_facts": [],
            "evidence": [],
            "client_situation": None,  # محتجز، مُفرج عنه بكفالة
            "has_lawyer": None,
            "prior_record": None
        }
        
        # Entities mentioned in conversation
        self.entities: Dict[str, List[str]] = {
            "names": [],
            "dates": [],
            "locations": [],
            "amounts": [],
            "documents": []
        }
        
        # Summary of conversation so far
        self.running_summary: str = ""
        
        # Questions already asked (to avoid repetition)
        self.asked_questions: List[str] = []
    
    def update_from_intake_result(self, intake_result: Dict[str, Any]):
        """Update memory from agent's intake result"""
        extracted = intake_result.get("extracted_data", {})
        
        # Merge new facts
        for key, value in extracted.items():
            if value and key in self.confirmed_facts:
                if isinstance(self.confirmed_facts[key], list):
                    if isinstance(value, list):
                        self.confirmed_facts[key].extend(value)
                    else:
                        self.confirmed_facts[key].append(value)
                else:
                    self.confirmed_facts[key] = value
    
    def get_context_for_llm(self, max_messages: int = 8) -> str:
        """Get context summary for LLM prompt"""
        facts_summary = []
        for key, value in self.confirmed_facts.items():
            if value:
                if isinstance(value, list) and value:
                    facts_summary.append(f"- {key}: {', '.join(str(v) for v in value)}")
                else:
                    facts_summary.append(f"- {key}: {value}")
        
        if facts_summary:
            return "**الحقائق المؤكدة:**\n" + "\n".join(facts_summary)
        return ""
    
    def get_missing_info(self) -> List[str]:
        """Get list of missing critical information"""
        missing = []
        critical_fields = ["case_type", "client_role", "incident_date", "key_facts"]
        
        for field in critical_fields:
            value = self.confirmed_facts.get(field)
            if not value or (isinstance(value, list) and len(value) == 0):
                missing.append(field)
        
        return missing
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "confirmed_facts": self.confirmed_facts,
            "entities": self.entities,
            "running_summary": self.running_summary,
            "asked_questions_count": len(self.asked_questions)
        }


class ChatSession:
    """
    Manages a conversational session for case intake
    إدارة جلسة محادثة لجمع معلومات القضية
    """
    
    def __init__(self, session_id: str = None, user_data: Optional[Dict[str, Any]] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.stage = ConversationStage.GREETING 
        self.messages: List[Dict[str, Any]] = []
        
        # User context (lawyer info)
        self.user_data = user_data or {}
        self.lawyer_id = self.user_data.get("id")
        self.lawyer_name = self.user_data.get("full_name", "المحامي")
        
        # Enhanced memory
        self.memory = SessionMemory()
        
        # 🆕 Conversation context for entity tracking
        from agents.memory.conversation_context import ConversationContext
        self.context = ConversationContext(ttl_minutes=30)
        
        # Legacy case_data for compatibility
        self.case_data = {
            "case_type": None,
            "parties": [],
            "facts": "",
            "additional_info": {},
            "client_name": None
        }
        
        # Tools
        self.quick_answer_tool = QuickAnswerTool()
        
        logger.info(f"📝 Created new chat session: {self.session_id} for {self.lawyer_name}")

    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(msg)
        return msg
    
    def get_next_question(self) -> Optional[str]:
        """Deprecated: Logic now handled by agent"""
        return "كيف يمكنني مساعدتك اليوم؟"
    
    def _classify_request(self, user_input: str) -> ResponseType:
        """
        Simplified request classification
        
        Removed QuickAnswerTool path - delegate to intelligent agent instead
        This provides better quality responses and reduces search overhead
        """
        user_input_lower = user_input.strip().lower()
        
        # Exception list: Identity and capability questions
        # These should go to agent, not search
        identity_keywords = ["من أنا", "من انا", "تعرفني", "هل تعرف من", "من انت", "من أنت"]
        capability_keywords = ["ما قدراتك", "ماذا تستطيع", "ما تقدر", "ماذا يمكنك", "ما مهمتك"]
        agent_questions = identity_keywords + capability_keywords
        
        if any(kw in user_input_lower for kw in agent_questions):
            logger.info(f"🎯 Agent-specific question -> DEEP_SEARCH")
            return ResponseType.DEEP_SEARCH
        
        # Case indicators - needs full analysis
        case_indicators = [
            "قضية", "قضيتي", "مشكلة", "نزاع", "خلاف", "دعوى",
            "محكمة", "متهم", "مدعى", "طعن"
        ]
        
        if any(ind in user_input for ind in case_indicators):
            logger.info(f"🏛️ Case-related query -> CASE_STUDY")
            return ResponseType.CASE_STUDY
        
        # Everything else: Let intelligent agent handle it
        # Agent with function calling is better than QuickAnswerTool
        logger.info(f"🔍 Default -> DEEP_SEARCH (intelligent agent)")
        return ResponseType.DEEP_SEARCH
    
    def process_response(self, user_input: str) -> Dict[str, Any]:
        """
        Process user response with intelligent routing
        
        All requests go to intelligent agent with function calling
        No more QuickAnswerTool - agent handles everything better
        """
        logger.info(f"Processing response... {user_input[:50]}")
        
        # Store user response
        self.add_message("user", user_input)
        
        # Smart classification (for logging purposes only)
        response_type = self._classify_request(user_input)
        
        # ✅ SIMPLIFIED: ALL requests go to intelligent agent
        # Agent with orchestrator can handle everything
        logger.info(f"📤 Sending to intelligent agent (response_type: {response_type.value})")
        
        # Get General Agent (Orchestrator)
        from api.main import general_agent
        
        # ⚠️ CRITICAL: Set lawyer context before using agent
        if self.lawyer_id:
            general_agent.set_lawyer_context(
                lawyer_id=self.lawyer_id,
                lawyer_name=self.lawyer_name
            )
            
            # 🧠 AUTO-LOAD: Load lawyer's profile into memory
            # 🧠 Note: Profile is already loaded in general_agent.lawyer_info
            # No need to store separately in session memory
            pass
        
        # Prepare context with memory
        memory_context = self.memory.get_context_for_llm()
        
        # Let the agent think (Intake Phase)
        intake_result = general_agent.conduct_intake(
            self.messages,
            memory_context=memory_context
        )
        
        # Update memory from result
        self.memory.update_from_intake_result(intake_result)
        
        # Update session with finding
        response_text = intake_result.get("response_text", "عذراً، حدث خطأ ما.")
        internal_state = intake_result.get("internal_state", "COLLECTING")
        
        # Handle states
        completed = False
        final_data = None
        
        if internal_state == "CONFIRMED":
            # 1. User confirmed -> Orchestrator starts work
            logger.info("🔒 Case confirmed. Starting Orchestration...")
            self.add_message("assistant", "شكراً لك. جاري تحليل القضية وإعداد الخطة...")
            
            try:
                # 2. Receive Case formally - use memory facts
                facts_text = json.dumps(self.memory.confirmed_facts, ensure_ascii=False, indent=2)
                conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in self.messages])
                
                case_id = general_agent.receive_case(
                    facts=f"الوقائع المستخرجة:\n{facts_text}\n\nنص المحادثة:\n{conversation_text}", 
                    client_name=self.memory.confirmed_facts.get("client_name", "Client")
                )
                
                # 3. Analyze
                analysis = general_agent.analyze_case()
                
                # 4. Plan
                plan = general_agent.create_plan()
                
                # Ensure plan is valid
                if not plan:
                    logger.warning("⚠️ Plan is None, using default")
                    plan = {"required_agents": []}
                
                # 5. Execute Plan (using general_agent's built-in executor)
                case_data_obj = general_agent.current_case
                
                # Execute using general_agent
                execution_result = general_agent.execute_plan_simple(
                    case_data=case_data_obj,
                    plan=plan
                )
                
                # 6. Final Result
                final_rec = execution_result.get("final_recommendation", {}) or {}
                response_text = final_rec.get("recommendation_text", "تم اكتمال التحليل.")
                
                completed = True
                final_data = case_data_obj
                
            except Exception as e:
                logger.error(f"❌ Case processing error: {e}")
                response_text = f"حدث خطأ أثناء تحليل القضية: {str(e)}\n\nيرجى المحاولة مرة أخرى لاحقاً."
                completed = False
            
            # Add final response to history
            self.add_message("assistant", response_text)
            
        else:
            # Just add the agent response (Intake continues)
            self.add_message("assistant", response_text)
            
        return {
            "message": response_text,
            "stage": internal_state,
            "completed": completed,
            "case_data": final_data,
            "memory": self.memory.to_dict()
        }
    
    def _generate_summary(self) -> str:
        """Legacy summary generation"""
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "stage": self.stage.value,
            "messages": self.messages,
            "case_data": self.case_data,
            "memory": self.memory.to_dict()
        }


class SessionManager:
    """Manages multiple chat sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        logger.info("✅ Session Manager initialized")
    
    def create_session(self, user_data: Optional[Dict[str, Any]] = None) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(user_data=user_data)
        self.sessions[session.session_id] = session
        
        # Send greeting with lawyer name
        lawyer_name = user_data.get("full_name", "المحامي") if user_data else "المحامي"
        greeting = f"مرحباً {lawyer_name}! 👋 أنا مساعدك الشخصي الذكي. كيف يمكنني مساعدتك؟"
        session.add_message("assistant", greeting)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get existing session"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"🗑️ Deleted session: {session_id}")


# Global session manager
session_manager = SessionManager()

__all__ = ["ChatSession", "SessionManager", "session_manager", "ConversationStage", "SessionMemory"]
