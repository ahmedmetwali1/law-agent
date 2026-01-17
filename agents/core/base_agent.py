"""
Base Agent Class
الفئة الأساسية لجميع الوكلاء
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

from ..knowledge.hybrid_search import search_engine, SearchResult
from ..config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Message structure for agent communication"""
    role: str  # 'system', 'user', 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentThought:
    """Represents agent's thinking process"""
    step: int
    description: str
    reasoning: str
    confidence: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents
    
    All agents inherit from this class and must implement:
    - think() method for processing information
    - report() method for generating output
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        expertise: str,
        system_prompt: str = None
    ):
        """
        Initialize base agent
        
        Args:
            name: Agent name/identifier
            role: Agent role description
            expertise: Area of expertise
            system_prompt: Custom system prompt for this agent
        """
        self.name = name
        self.role = role
        self.expertise = expertise
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        # Memory and context
        self.memory: List[AgentMessage] = []
        self.thoughts: List[AgentThought] = []
        self.context: Dict[str, Any] = {}
        
        # Knowledge retrieval
        self.search_engine = search_engine
        self.knowledge_cache: List[SearchResult] = []
        
        # Agent state
        self.status = "initialized"
        self.created_at = datetime.now()
        
        logger.info(f"✅ Initialized agent: {self.name} ({self.role})")
    
    def _default_system_prompt(self) -> str:
        """Generate default system prompt"""
        return f"""أنت {self.name}، وكيل ذكاء اصطناعي متخصص في {self.expertise}.
دورك: {self.role}

قم بتحليل المعلومات بدقة وبناء استنتاجات قانونية سليمة.
استخدم قاعدة المعرفة القانونية للبحث عن المواد والأحكام ذات الصلة.
قدم توصيات واضحة ومنطقية مع الاستناد إلى المصادر القانونية."""
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add message to agent's memory
        
        Args:
            role: Message role (system/user/assistant)
            content: Message content
            metadata: Additional metadata
        """
        message = AgentMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.memory.append(message)
        logger.debug(f"📝 Added {role} message to {self.name}")
    
    def add_thought(self, description: str, reasoning: str, confidence: float = 0.8):
        """
        Add a thinking step to agent's thought process
        
        Args:
            description: What the agent is thinking about
            reasoning: The reasoning behind this thought
            confidence: Confidence level (0-1)
        """
        thought = AgentThought(
            step=len(self.thoughts) + 1,
            description=description,
            reasoning=reasoning,
            confidence=confidence
        )
        self.thoughts.append(thought)
        logger.debug(f"💭 {self.name} thought: {description}")
    
    def search_knowledge(
        self,
        query: str,
        limit: int = None,
        method: str = "hybrid"
    ) -> List[SearchResult]:
        """
        Search the knowledge base
        
        Args:
            query: Search query
            limit: Maximum number of results
            method: Search method ('keyword', 'vector', 'hybrid')
            
        Returns:
            List of search results
        """
        logger.info(f"🔍 {self.name} searching for: {query[:100]}...")
        
        limit = limit or settings.top_k_results
        
        if method == "keyword":
            results = self.search_engine.keyword_search(query, limit)
        elif method == "vector":
            results = self.search_engine.vector_search(query, limit=limit)
        else:  # hybrid
            results = self.search_engine.hybrid_search(query, limit)
        
        # Cache results
        self.knowledge_cache.extend(results)
        
        logger.info(f"✅ {self.name} found {len(results)} results")
        return results
    
    def clear_memory(self):
        """Clear agent's memory"""
        self.memory.clear()
        self.thoughts.clear()
        self.knowledge_cache.clear()
        logger.info(f"🧹 Cleared memory for {self.name}")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get conversation history in format suitable for LLM
        
        Returns:
            List of message dictionaries
        """
        history = []
        for msg in self.memory:
            message_dict = {"role": msg.role, "content": msg.content}
            
            # Add tool_calls if present in metadata (for assistant messages)
            if msg.role == "assistant" and msg.metadata.get("tool_calls"):
                message_dict["tool_calls"] = msg.metadata["tool_calls"]
            
            # Add tool_call_id if present in metadata (for tool messages)
            if msg.role == "tool" and msg.metadata.get("tool_call_id"):
                message_dict["tool_call_id"] = msg.metadata["tool_call_id"]
                
            history.append(message_dict)
            
        return history
    
    def get_thinking_trace(self) -> str:
        """
        Get formatted thinking trace
        
        Returns:
            Formatted string of agent's thoughts
        """
        trace = f"# {self.name} - سلسلة التفكير\n\n"
        
        for thought in self.thoughts:
            trace += f"## خطوة {thought.step}: {thought.description}\n"
            trace += f"**التفكير:** {thought.reasoning}\n"
            trace += f"**الثقة:** {thought.confidence:.2%}\n\n"
        
        return trace
    
    @abstractmethod
    def think(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and perform reasoning
        
        This is the main processing method that each agent must implement.
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            Processed output dictionary
        """
        pass
    
    @abstractmethod
    def report(self) -> Dict[str, Any]:
        """
        Generate final report/output
        
        Returns:
            Agent's final report dictionary
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize agent to dictionary
        
        Returns:
            Dictionary representation of agent
        """
        return {
            "name": self.name,
            "role": self.role,
            "expertise": self.expertise,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "memory_size": len(self.memory),
            "thoughts_count": len(self.thoughts),
            "knowledge_cache_size": len(self.knowledge_cache)
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', role='{self.role}')>"


class LLMAgent(BaseAgent):
    """
    Base agent with LLM capabilities
    
    Extends BaseAgent with methods for interacting with language models
    """
    
    def __init__(self, name: str, role: str, expertise: str, system_prompt: str = None):
        super().__init__(name, role, expertise, system_prompt)
        
        # Initialize LLM client based on provider
        self.llm_provider = settings.ai_provider
        self._init_llm_client()
    
    def _init_llm_client(self):
        """Initialize LLM client using Open WebUI"""
        from agents.config.openwebui import openwebui_client
        self.llm_client = openwebui_client
        self.model = settings.openwebui_model
        logger.debug(f"Initialized OpenWebUI client for {self.name}")
    
    def generate_response(
        self,
        messages: List[Dict[str, str]] = None,
        temperature: float = None,
        max_tokens: int = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> Any:
        """
        Generate response using Open WebUI
        
        Args:
            messages: Conversation messages (uses memory if not provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of tools definition
            tool_choice: Optional tool choice
            
        Returns:
            Generated response text or message object (if tools used)
        """
        messages = messages or self.get_conversation_history()
        temperature = temperature or settings.temperature
        max_tokens = max_tokens or settings.max_tokens
        
        # Add system prompt if not already in messages
        if not any(msg['role'] == 'system' for msg in messages):
            messages.insert(0, {"role": "system", "content": self.system_prompt})
        
        try:
            # Use Open WebUI client
            response = self.llm_client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                tool_choice=tool_choice
            )
            return response
                
        except Exception as e:
            logger.error(f"❌ LLM generation failed: {e}")
            raise
    
    def think(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced think() using ReAct reasoning engine for deep analysis
        
        Uses tools and multi-step reasoning for comprehensive analysis
        """
        from ..tools.react_engine import ReActEngine
        
        # Extract key information from input
        case_facts = input_data.get("case_facts", "")
        focus_area = input_data.get("focus_area", "")
        initial_analysis = input_data.get("initial_analysis", {})
        
        # Build comprehensive question for ReAct
        question = f"""
بصفتك {self.name} ({self.role})، قم بتحليل القضية التالية:

**الوقائع:**
{case_facts}

**مجال التركيز:**
{focus_area}

**التحليل الأولي:**
{json.dumps(initial_analysis, ensure_ascii=False, indent=2) if initial_analysis else 'لا يوجد'}

**المطلوب:**
1. ابحث في قاعدة المعرفة عن المواد القانونية ذات الصلة
2. حلل الموقف القانوني من منظور {self.expertise}
3. قدم توصيات واضحة مع الاستناد للمصادر
"""
        
        # Use ReAct for reasoning
        try:
            react_engine = ReActEngine()
            result = react_engine.reason(question, context=f"الوكيل: {self.name}")
            
            # Add thinking steps from ReAct
            for step in react_engine.steps:
                self.add_thought(
                    description=step.content[:100],
                    reasoning=step.step_type,
                    confidence=0.8
                )
            
            # Store final answer
            final_answer = result.get("answer", "")
            self.add_message("assistant", final_answer)
            
            return {
                "response": final_answer,
                "thinking_steps": len(react_engine.steps),
                "tools_used": [s.tool_used for s in react_engine.steps if s.tool_used],
                "sources": result.get("sources", [])
            }
            
        except Exception as e:
            logger.warning(f"⚠️ ReAct failed, falling back to simple LLM: {e}")
            # Fallback to simple LLM
            input_text = json.dumps(input_data, ensure_ascii=False, indent=2)
            self.add_message("user", f"قم بتحليل البيانات التالية:\n\n{input_text}")
            response = self.generate_response()
            self.add_message("assistant", response)
            return {"response": response}
    
    def report(self) -> Dict[str, Any]:
        """Generate default report"""
        return {
            "agent": self.name,
            "role": self.role,
            "expertise": self.expertise,
            "thoughts": [
                {
                    "step": t.step,
                    "description": t.description,
                    "reasoning": t.reasoning,
                    "confidence": t.confidence
                }
                for t in self.thoughts
            ],
            "knowledge_used": len(self.knowledge_cache),
            "final_output": self.memory[-1].content if self.memory else None
        }


__all__ = [
    "BaseAgent",
    "LLMAgent",
    "AgentMessage",
    "AgentThought"
]
