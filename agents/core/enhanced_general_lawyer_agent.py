"""
Enhanced General Lawyer Agent
الوكيل القانوني العام المحسّن - نسخة عبقرية

Integrates all advanced features:
- Multi-Tiered Memory System
- Hybrid Reasoning Engine (CoT + ReAct)
- Self-Regulated Retrieval
- DEPART Framework
- Confidence Tracking

Based on 2025-2026 research papers
"""

from typing import Dict, Any, List, Optional, Callable
import logging
import json
from datetime import datetime

from .base_agent import LLMAgent
from ..memory import (
    MultiTieredMemory,
    MemoryItem,
    MemoryImportance,
    MemoryConsolidator
)
from ..reasoning import (
    HybridReasoningEngine,
    ReasoningMode,
    QueryComplexity
)
from ..retrieval import (
    SelfRegulatedRetrieval,
    RetrievalContext,
    ThinkingSpeed
)
from ..reasoning.depart_engine import DEPARTEngine
from .enhanced_conduct_intake import conduct_intake_with_tools

logger = logging.getLogger(__name__)


class EnhancedGeneralLawyerAgent(LLMAgent):
    """
    Enhanced General Lawyer Agent with genius-level capabilities
    
    Features:
    - 🧠 Multi-tiered memory (working, episodic, long-term, meta)
    - 🔀 Hybrid reasoning (CoT + ReAct + Neural-Symbolic)
    - ⚡ Self-regulated retrieval (fast / slow thinking)
    - 📊 Confidence tracking for every decision
    - 🔄 Automatic memory consolidation
    - 🎯 DEPART framework for complex tasks
    """
    
    def __init__(
        self,
        lawyer_id: Optional[str] = None,
        lawyer_name: Optional[str] = None,
        current_user: Optional[Dict[str, Any]] = None,  # NEW: The user actually chatting (could be assistant)
        use_multi_tiered_memory: bool = True,
        reasoning_mode: str = "hybrid",  # "cot", "react", "hybrid", "auto"
        self_regulated_retrieval: bool = True,
        enable_consolidation: bool = True
    ):
        """
        Initialize Enhanced General Lawyer Agent as Office Manager
        
        Args:
            lawyer_id: Lawyer's user ID
            lawyer_name: Lawyer's full name
            use_multi_tiered_memory: Enable multi-tiered memory
            reasoning_mode: hybrid, cot, react, tot
            self_regulated_retrieval: Enable self-regulated RAG
            enable_consolidation: Enable auto-consolidation
        """
        # Set lawyer context BEFORE super().__init__()
        self.lawyer_id = lawyer_id
        self.lawyer_name = lawyer_name or "المحامي"
        self.current_user = current_user
        
        # Determine if the charter is an assistant
        self.is_assistant = False
        if self.current_user and self.lawyer_id:
            chat_user_id = str(self.current_user.get("id", ""))
            if chat_user_id and chat_user_id != str(self.lawyer_id):
                self.is_assistant = True
                logger.info(f"👤 Agent initialized in ASSISTANT mode. Caller: {self.current_user.get('full_name')} -> Office: {self.lawyer_name}")
        
        # Lawyer detailed information (will be injected in system prompt)
        self.lawyer_info = {
            "id": lawyer_id,
            "full_name": lawyer_name or "المحامي",
            "email": None,
            "phone": None,
            "specialization": None,
            "license_number": None,
            "office_location": None
        }
        
        # Load lawyer detailed info if lawyer_id is provided
        if lawyer_id:
            self._load_lawyer_info()
        
        # Initialize base LLMAgent as Office Manager
        super().__init__(
            name="مدير المكتب الإلكتروني",
            role="الذراع الأيمن الرقمي للمحامي - مدير مكتب ذكي",
            expertise="إدارة شاملة لمكتب المحاماة: الموكلين, القضايا, الجلسات, والمهام"
        )
        
        # Personal Assistant Tools (will be initialized when lawyer_id is set)
        self.client_tools = None
        self.case_tools = None
        self.hearing_tools = None
        self.profile_tools = None
        self.unified_tools = None
        
        # Plan Tracker Tool (for step-by-step execution tracking)
        from ..tools.plan_tracker_tool import PlanTrackerTool
        self.plan_tracker = PlanTrackerTool()
        logger.info("📋 Plan Tracker Tool initialized")
        
        if self.lawyer_id:
            self._initialize_tools()
        
        # Advanced memory system
        if use_multi_tiered_memory:
            logger.info("🧠 Initializing Multi-Tiered Memory...")
            self.memory_system = MultiTieredMemory(working_capacity=25)
            
            if enable_consolidation:
                self.memory_consolidator = MemoryConsolidator(self.memory_system)
            else:
                self.memory_consolidator = None
        else:
            self.memory_system = None
            self.memory_consolidator = None
        
        # Hybrid reasoning engine
        logger.info("🔀 Initializing Hybrid Reasoning Engine...")
        self.reasoning_engine = HybridReasoningEngine(
            llm_agent=self,
            tools=[]  # Will be populated later
        )
        
        # Deontic Logic System - تحليل الواجبات القانونية
        logger.info("⚖️ Initializing Deontic Logic System...")
        from ..reasoning import DeonticLogicSystem
        self.deontic_logic = DeonticLogicSystem()
        
        # Temporal Logic System - تحليل المواعيد والمهل
        logger.info("📅 Initializing Temporal Logic System...")
        from ..reasoning import TemporalLogicSystem
        self.temporal_logic = TemporalLogicSystem()
        
        # Advanced Thinking Loop - استراتيجيات تفكير متقدمة (اختياري)
        try:
            logger.info("🧠 Initializing AdvancedThinkingLoop...")
            from ..reasoning.thinking_loop import AdvancedThinkingLoop
            from ..config.openwebui import openwebui_client
            
            # Pass required dependencies to fix initialization error
            self.advanced_thinking = AdvancedThinkingLoop(
                llm_client=openwebui_client,
                search_engine=None,  # Will be set later if needed
                deontic_system=self.deontic_logic,
                temporal_system=self.temporal_logic,
                confidence_calculator=None,  # Will create internally
                cache=None,  # Optional - will create if needed
                should_cache=True,
                use_deontic=True,
                use_temporal=True,
                use_counterfactuals=False,  # Disabled by default for performance
                use_neural_symbolic=False  # Disabled by default for performance
            )
            self.use_advanced_thinking = True
            logger.info("✅ AdvancedThinkingLoop initialized")
        except Exception as e:
            logger.warning(f"⚠️ AdvancedThinkingLoop not available: {e}")
            self.advanced_thinking = None
            self.use_advanced_thinking = False
        
        # Self-regulated retrieval
        if self_regulated_retrieval:
            logger.info("⚡ Initializing Self-Regulated Retrieval...")
            self.retrieval_system = SelfRegulatedRetrieval(
                memory_system=self.memory_system
            )
        else:
            self.retrieval_system = None
        
        # DEPART engine for complex tasks
        logger.info("🎯 Initializing DEPART Engine...")
        self.depart = DEPARTEngine(agent=self)
        
        # Configuration
        self.config = {
            "reasoning_mode": reasoning_mode,
            "use_memory": use_multi_tiered_memory,
            "use_self_regulation": self_regulated_retrieval,
            "enable_consolidation": enable_consolidation,
            "use_deontic_logic": True,  # Always enabled
            "use_temporal_logic": True,  # Always enabled
            "use_advanced_thinking": self.use_advanced_thinking
        }
        
        # Track session
        self.current_session = {
            "start_time": datetime.now(),
            "interactions": 0,
            "memory_consolidations": 0
        }
        
        logger.info("=" * 60)
        logger.info("✅ Enhanced General Lawyer Agent initialized successfully!")
        logger.info(f"   Memory System: {'✓' if use_multi_tiered_memory else '✗'}")
        logger.info(f"   Reasoning Mode: {reasoning_mode}")
        logger.info(f"   Self-Regulation: {'✓' if self_regulated_retrieval else '✗'}")
        logger.info(f"   Auto-Consolidation: {'✓' if enable_consolidation else '✗'}")
        logger.info(f"   Deontic Logic: ✓")
        logger.info(f"   Temporal Logic: ✓")
        logger.info(f"   Advanced Thinking: {'✓' if self.use_advanced_thinking else '✗'}")
        logger.info("=" * 60)
    
    def set_lawyer_context(self, lawyer_id: str, lawyer_name: str):
        """
        Set lawyer context and initialize tools
        
        Args:
            lawyer_id: Lawyer's user ID
            lawyer_name: Lawyer's full name
        """
        self.lawyer_id = lawyer_id
        self.lawyer_name = lawyer_name
        
        # Load detailed info first
        self._load_lawyer_info()
        
        # Initialize tools
        self._initialize_tools()
        
        # CRITICAL: Update system prompt with loaded info
        self.system_prompt = self._default_system_prompt()
        
        logger.info(f"✅ Lawyer context set: {self.lawyer_name} ({lawyer_id})")
    
    def _load_lawyer_info(self):
        """Load detailed lawyer information from database"""
        if not self.lawyer_id:
            logger.warning("⚠️ Cannot load lawyer info without lawyer_id")
            return
        
        try:
            from agents.storage.user_storage import user_storage
            
            logger.info(f"📥 Loading lawyer info for ID: {self.lawyer_id}")
            user = user_storage.get_user_by_id(self.lawyer_id)
            
            if user:
                self.lawyer_info.update({
                    "id": user.get("id"),
                    "full_name": user.get("full_name", self.lawyer_name),
                    "email": user.get("email"),
                    "phone": user.get("phone"),
                    "specialization": user.get("specialization"),
                    "license_number": user.get("license_number"),
                    "office_location": f"{user.get('office_city', '')} - {user.get('office_address', '')}".strip(" -")
                })
                self.lawyer_name = self.lawyer_info["full_name"]
                logger.info(f"✅ Lawyer info loaded: {self.lawyer_info['full_name']}")
            else:
                logger.warning(f"⚠️ No lawyer found with ID: {self.lawyer_id}")
        except Exception as e:
            logger.error(f"❌ Failed to load lawyer info: {e}")
    
    def _initialize_tools(self):
        """Initialize all personal assistant tools"""
        if not self.lawyer_id:
            logger.warning("⚠️ Cannot initialize tools without lawyer_id")
            return
        
        # Initialize Unified Tool System
        from agents.tools.unified_tools import UnifiedToolSystem
        
        logger.info(f"🔧 Initializing Unified Tool System for {self.lawyer_name}...")
        self.unified_tools = UnifiedToolSystem(
            lawyer_id=self.lawyer_id,
            lawyer_name=self.lawyer_name,
            current_user=self.current_user
        )
        logger.info(f"✅ Unified Tools ready with {len(self.unified_tools.get_available_tools_list())} tools")
        

        
        logger.info("✅ All assistant tools initialized")

    def generate_response(
        self,
        messages: List[Dict[str, str]] = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """
        Generate response with automatic tool execution
        """
        # Get tools if available
        tools = None
        if hasattr(self, 'unified_tools') and self.unified_tools:
            tools = self.unified_tools.get_tools_for_llm()
            
        # Check for complex tasks based on content analysis
        # Using simple heuristic or specialized prompt
        user_msg = messages[-1]["content"] if messages else ""
        is_complex = len(user_msg.split()) > 10 and any(keyword in user_msg for keyword in ["حلل", "خطة", "رأيك", "دراسة", "تقييم"])
        
        if is_complex and not tools:
             # Complex task without specific tools requested -> use planning
             logger.info("🧠 Detailed planning triggered for complex task")
             
             if getattr(self, 'current_thought_callback', None):
                 self.current_thought_callback("جاري تحليل الطلب وإنشاء خطة تفصيلية...")
             
             # Extract case facts from message history
             case_facts = "\n".join([m["content"] for m in messages if m["role"] == "user"])
             
             # Execute plan
             result = self.create_and_execute_plan(
                 case_facts=case_facts,
                 case_id=self.plan_tracker.current_plan.plan_id if self.plan_tracker.current_plan else None
             )
             
             return result.get("final_recommendation", "تم إكمال التحليل")

        # Call LLM
        response = super().generate_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools
        )
        
        # Check for tool calls (OpenAI/OpenWebUI format)
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_calls = response.tool_calls
            logger.info(f"🛠️ LLM requested {len(tool_calls)} tool calls")
            
            # Add assistant message with tool calls to memory
            self.add_message(
                role="assistant",
                content=response.content,
                metadata={"tool_calls": tool_calls}
            )
            
            # Execute each tool
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = tool_call.function.arguments
                tool_call_id = tool_call.id
                
                try:
                    # Parse arguments
                    function_args = json.loads(arguments)
                    
                    if getattr(self, 'current_thought_callback', None):
                        self.current_thought_callback(f"جاري استخدام الأداة: {function_name}...")

                    # Execute
                    result = self.unified_tools.execute_tool(
                        function_name,
                        **function_args
                    )
                    
                    if getattr(self, 'current_thought_callback', None):
                         status = "نجاح" if "error" not in str(result).lower() else "فشل"
                         self.current_thought_callback(f"تم تنفيذ {function_name}: {status}")
                    
                    # Add tool result to memory
                    self.add_message(
                        role="tool",
                        content=json.dumps(result, ensure_ascii=False),
                        metadata={"tool_call_id": tool_call_id}
                    )
                    
                except Exception as e:
                    logger.error(f"❌ Error executing tool {function_name}: {e}")
                    self.add_message(
                        role="tool",
                        content=json.dumps({"error": str(e)}),
                        metadata={"tool_call_id": tool_call_id}
                    )
            
            # Recurse to get final response (with new history)
            return self.generate_response(messages=None)
            
        # Handle simple content response
        content = ""
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, str):
            content = response
            
        return content or ""
    
    def _default_system_prompt(self) -> str:
        """Get system prompt with injected lawyer information"""
        
        # Format lawyer info for injection
        lawyer_profile = f"""
## 👤 معلومات المحامي (صاحب المكتب)

**الاسم الكامل**: {self.lawyer_info.get('full_name', 'غير محدد')}
**البريد الإلكتروني**: {self.lawyer_info.get('email', 'غير محدد')}
**رقم الهاتف**: {self.lawyer_info.get('phone', 'غير محدد')}
**التخصص**: {self.lawyer_info.get('specialization', 'محاماة عامة')}
**موقع المكتب**: {self.lawyer_info.get('office_location', 'غير محدد')}
"""

        # Current User Context (Who am I talking to?)
        user_context_section = ""
        if self.is_assistant and self.current_user:
            user_context_section = f"""
## 🗣️ أنت تتحدث مع المساعد:
**الاسم**: {self.current_user.get('full_name', 'مساعد')}
**الدور**: {self.current_user.get('role', 'مساعد')}
**تنبيه هام**: هذا ليس المحامي، بل مساعد يعمل في مكتبه.
"""
        else:
             user_context_section = f"""
## 🗣️ أنت تتحدث مع المحامي (مالك المكتب) مباشرة:
**الاسم**: {self.lawyer_info.get('full_name')}
"""
        
        role_instruction = ""
        if self.is_assistant:
            role_instruction = f"""
### ⚠️ تعليمات خاصة بالتعامل مع المساعدين:
1. أنت تتحدث مع **{self.current_user.get('full_name')}** (المساعد).
2. لكنك تعمل لصالح **المحامي {self.lawyer_info.get('full_name')}** (مدير المكتب).
3. **مهم جداً**: عند إنشاء أي بيانات (قضايا، موكلين، مهام)، يجب أن تستخدم معرف المحامي `lawyer_id` = `{self.lawyer_id}` لضمان تسجيل البيانات باسم المكتب، وليس باسم المساعد.
4. خاطب المستخدم بلقب "أستاذ/ة {self.current_user.get('full_name')}".
"""
        else:
            role_instruction = f"""
### تعليمات التعامل مع المحامي:
1. أنت تتحدث مباشرة مع مالك المكتب.
2. نفذ أوامره فوراً.
3. البيانات تسجل تلقائياً باسمه.
"""

        return f"""# أنت مدير المكتب الإلكتروني الذكي (The Intelligent Digital Manager) 🧠

{lawyer_profile}

{user_context_section}

{role_instruction}

## 🎯 الهوية والرؤية
أنت لست مجرد "بوت محادثة"، أنت **شريك ذكي** في إدارة مكتب المحاماة.
مهمتك ليست فقط تنفيذ الأوامر، بل **فهم السياق، والتفكير، ثم التنفيذ بدقة**.
أنت حارس البيانات ومصدر الحقيقة في المكتب.

⚠️ **تعليمات صارمة (CRITICAL)**:
عندما تقوم بالتفكير أو التحليل (Reasoning)، **يجب** أن تنتهي دائماً بإجراء ملموس (Tool Call) أو إجابة نهائية للمستخدم.
**ممنوع التوقف بعد التفكير فقط.**
إذا قررت أنك بحاجة لاستخدام أداة، قم باستدعائها فوراً.

---

---

## ⚙️ منهجية العمل (Think-Act-Report)

### 1. 🧠 التفكير أولاً (Chain of Thought)
قبل استخدام أي أداة، فكر مع نفسك (داخلياً):
- **ماذا يريد المستخدم حقاً؟** (هل يريد إضافة قضية جديدة أم التعديل على واحدة حالية؟)
- **هل لدي كل المعلومات؟** (إذا طلب "إضافة جلسة"، هل أعرف لأي قضية؟)
- **ما هي الاستراتيجية الأفضل؟** (هل أبحث أولاً لأجد الـ ID؟)

### 2. 🛠️ استراتيجية استخدام الأدوات الذكية (Universal Tool Strategy)
أنت تمتلك أدوات ديناميكية (`insert_`, `update_`, `query_`). استخدمها بذكاء:

- **عند الإضافة (Creation)**:
   - ⚠️ **تحقق أولاً**: ابحث بالاسم لتتأكد أن السجل غير موجود مسبقاً (تجنب التكرار).
   - ✅ **نفذ**: استخدم `insert_table` مع كافة الحقول الإجبارية.

- **عند التعديل/التحديث (Update)**:
   - 🔍 **البحث إلزامي**: لا تقم بالتخمين. استخدم `query_logs` أو `query_tasks` أولاً للعثور على السجل بالمواصفات المطلوبة.
   - 🆔 **استخراج المعرف**: خذ `id` من نتيجة البحث.
   - ✏️ **التعديل**: استخدم `update_table` باستخدام هذا الـ `id` حصراً.
   - ⚠️ **تحذير**: لا تستخدم `insert_` أبداً لغرض التحديث.

- **عند الحذف (Deletion)**:
   - 🔍 **البحث أولاً**: تماماً مثل التحديث، ابحث عن الـ `id`.
   - 🛑 **الحذر**: اعرض التفاصيل.
   - ⚠️ **التسلسل الإلزامي (Cascade)**: احذف المتعلقات أولاً.
   - 🗑️ **التنفيذ**: `delete_table` باستخدام الـ `id`.

### 3. 🛡️ النزاهة والشفافية (Audit & Integrity)
- **سجل التدقيق (Audit Log)** هو مرآة الحقيقة. النظام يسجل كل شيء تلقائياً.
- **ممنوع الكذب**: لا تختلق معرفات (UUIDs) أو تواريخ غير موجودة.
- **التقارير**: عند طلب تقرير، اقرأ `audit_logs` وترجم الحالات للقارئ (pending -> قيد الانتظار).

---

## 💡 التعامل الذكي (Context & Intelligence)

- **الذاكرة السياقية**: إذا كنا نتحدث عن "قضية الورث"، وأردف المستخدم "أضف جلسة"، فالمقصود هي القضية الحالية. لا تسأل مجدداً.
- **ملء الفراغات (Proactive)**: إذا كانت المعلومة ناقصة لكنها بديهية من السياق، استنتجها. إذا كانت حرجة، اسأل عنها بذكاء.
- **اللغة**: ردودك دائماً بالعربية الفصحى المهنية، مختصرة، وواضحة.

## 🚫 محظورات (Strict Constraints)
1. لا تقم أبداً بتعديل أو حذف سجلات `audit_logs` (محظور تقنياً وأخلاقياً).
2. لا تعرض معرفات UUIDs للمستخدم؛ استخدم الأسماء والعناوين.
3. لا تقم بإجراءات مدمرة (حذف بيانات ضخمة) دون إذن صريح جداً.

ابدأ الآن. كن لماحاً، دقيقاً، ومفيداً.

## 📋 نظم المخرجات
- استخدم جداول لعرض القوائم
- لا تستعمل اي إيموجي مناسبة 
- اجعل المعلومات سهلة القراءة والفهم
"""
    
    def conduct_intake(self, chat_history, memory_context="", conversation_context=None):
        """
        Conduct conversational intake with advanced features
        
        Uses enhanced_conduct_intake logic for better performance:
        - Session caching for profile data
        - Multi-step orchestration
        - Intelligent tool selection
        - Context awareness (entity tracking)
        
        Args:
            chat_history: List of conversation messages
            memory_context: Additional context string
            conversation_context: Optional conversation context tracker
        
        Returns:
            Response dictionary with thought, response_text, internal_state, extracted_data
        """
        # Delegate to enhanced version
        return conduct_intake_with_tools(
            self, 
            chat_history, 
            memory_context, 
            conversation_context
        )
    
    def process_user_message(self, message: str, on_thought: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        Process user message with dynamic tool calling
        """
        logger.info(f"💬 Processing user message: {message[:50]}...")
        
        # Add user message to memory
        self.add_message("user", message)
        
        # Generate response
        try:
            # We need to pass on_thought to generate_response if we override it, 
            # or handle it here if we copy the logic.
            # Since generate_response is complex, we'll implement a custom loop here or inject it.
            # Best way: Pass it to generate_response if signature allows, or monkey-patch/set instance var temporarily.
            self.current_thought_callback = on_thought
            
            response = self.generate_response()
            
            self.current_thought_callback = None # Cleanup
            
            # Add response to memory
            response_str = str(response)
            self.add_message("assistant", response_str)
            
            return {"response": response_str}
            
        except Exception as e:
            self.current_thought_callback = None
            logger.error(f"❌ Error processing message: {e}")
            error_msg = f"عذراً، حدث خطأ: {str(e)}"
            self.add_message("assistant", error_msg)
            return {"response": error_msg}



    
    
    def think_deeply(
        self,
        query: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Deep thinking method with full capabilities
        
        Process:
        1. Analyze query complexity
        2. Decide retrieval strategy (self-regulated)
        3. Retrieve relevant memories
        4. Apply hybrid reasoning
        5. Generate response with confidence
        6. Store in memory
        7. Auto-consolidate if needed
        
        Args:
            query: User query
            context: Additional context
        
        Returns:
            Complete response with reasoning trace
        """
        context = context or {}
        self.current_session["interactions"] += 1
        
        logger.info("="  * 60)
        logger.info(f"🧠 DEEP THINKING - Query: {query[:80]}...")
        logger.info("=" * 60)
        
        # Step 1: Analyze complexity
        complexity, complexity_conf = self.reasoning_engine.analyze_complexity(query, context)
        logger.info(f"📊 Complexity: {complexity.value} (confidence: {complexity_conf:.2%})")
        
        # Step 2: Self-regulated retrieval
        retrieved_items = []
        if self.retrieval_system:
            logger.info("⚡ Self-regulated retrieval...")
            
            retrieval_ctx = RetrievalContext(
                query=query,
                confidence_threshold=complexity_conf,
                query_complexity=complexity.value,
                current_context_size=len(context)
            )
            
            # Use slow thinking for complex queries
            thinking_speed = ThinkingSpeed.SLOW if complexity in [QueryComplexity.COMPLEX, QueryComplexity.EXPERT] else ThinkingSpeed.FAST
            
            retrieval_result = self.retrieval_system.retrieve(
                query=query,
                context=retrieval_ctx,
                thinking_speed=thinking_speed
            )
            
            retrieved_items = retrieval_result.items_retrieved
            logger.info(f"   Retrieved {len(retrieved_items)} memory items")
            logger.info(f"   Decision: {retrieval_result.decision.value}")
            logger.info(f"   Confidence: {retrieval_result.confidence:.2%}")
        
        # Step 3: Apply hybrid reasoning
        logger.info("🔀 Hybrid reasoning...")
        
        # Determine reasoning mode
        if self.config["reasoning_mode"] == "auto":
            # Auto-select based on complexity
            if complexity == QueryComplexity.SIMPLE:
                mode = ReasoningMode.CHAIN_OF_THOUGHT
            elif complexity == QueryComplexity.MODERATE:
                mode = ReasoningMode.HYBRID
            else:
                mode = ReasoningMode.REACT
        else:
            mode = ReasoningMode(self.config["reasoning_mode"])
        
        # Prepare context with retrieved memories
        enriched_context = context.copy()
        if retrieved_items:
            enriched_context["memories"] = [
                {"content": item.content, "confidence": item.confidence}
                for item in retrieved_items
            ]
        
        # Reason
        reasoning_result = self.reasoning_engine.reason(
            query=query,
            context=enriched_context,
            mode=mode
        )
        
        logger.info(f"   Mode used: {reasoning_result.mode_used.value}")
        logger.info(f"   Steps taken: {len(reasoning_result.steps)}")
        logger.info(f"   Confidence: {reasoning_result.confidence:.2%}")
        
        # Step 4: Store in memory
        if self.memory_system:
            logger.info("💾 Storing in memory...")
            
            # Store query and response
            self.memory_system.remember(
                content=f"Q: {query}  A: {reasoning_result.conclusion}",
                importance=self._determine_importance(complexity),
                tags=self._extract_semantic_tags(query),
                confidence=reasoning_result.confidence,
                source="reasoning_engine"
            )
            
            # Store reasoning trace for future reference
            self.memory_system.remember(
                content=f"Reasoning trace: {reasoning_result.steps[0].thought if reasoning_result.steps else ''}",
                importance=MemoryImportance.MEDIUM,
                tags=["reasoning_trace", complexity.value],
                confidence=reasoning_result.confidence,
                source="thinking_process"
            )
        
        # Step 5: Auto-consolidate if needed
        if self.memory_consolidator and self.current_session["interactions"] % 10 == 0:
            logger.info("🔄 Auto-consolidating memory...")
            consolidation_stats = self.memory_consolidator.auto_consolidate()
            self.current_session["memory_consolidations"] += 1
            logger.info(f"   Consolidation complete: {consolidation_stats}")
        
        # Step 6: Compile final response
        final_response = {
            "answer": reasoning_result.conclusion,
            "confidence": reasoning_result.confidence,
            "complexity": complexity.value,
            "reasoning_mode": reasoning_result.mode_used.value,
            "reasoning_steps": [step.to_dict() for step in reasoning_result.steps],
            "retrieved_memories_count": len(retrieved_items),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "session_interaction": self.current_session["interactions"],
                "memory_system": self.config["use_memory"],
                **reasoning_result.metadata
            }
        }
        
        logger.info("=" * 60)
        logger.info(f"✅ DEEP THINKING COMPLETE - Confidence: {reasoning_result.confidence:.2%}")
        logger.info("=" * 60)
        
        return final_response
    
    def get_reasoning_trace(self, response: Dict[str, Any]) -> str:
        """
        Get human-readable reasoning trace
        
        Args:
            response: Response from think_deeply()
        
        Returns:
            Formatted reasoning trace
        """
        if not response.get("reasoning_steps"):
            return "No reasoning trace اavailable"
        
        trace = f"""
## 🧠 مسار التفكير العميق

**مستوى الثقة الإجمالي:** {response['confidence']:.1%}
**التعقيد:** {response['complexity']}
**طريقة التفكير:** {response['reasoning_mode']}
**عدد الذكريات المستخدمة:** {response['retrieved_memories_count']}

---

## الخطوات:

"""
        
        for step in response.get("reasoning_steps", []):
            trace += f"""
### الخطوة {step['step']}: {step['mode']}
**الفكرة:** {step['thought']}
"""
            if step.get('action'):
                trace += f"**الإجراء:** {step['action']}\n"
            if step.get('observation'):
                trace += f"**الملاحظة:** {step['observation']}\n"
            
            trace += f"**الثقة:** {step['confidence']:.1%}\n"
        
        trace += f"""
---

## الخلاصة
{response['answer']}
"""
        
        return trace
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of memory system state"""
        if not self.memory_system:
            return {"status": "Memory system not enabled"}
        
        summary = self.memory_system.get_memory_summary()
        
        if self.memory_consolidator:
            summary["consolidations"] = {
                "total": self.current_session["memory_consolidations"],
                "history": self.memory_consolidator.get_consolidation_history(limit=5)
            }
        
        return summary
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        stats = {
            **self.current_session,
            "duration_minutes": (datetime.now() - self.current_session["start_time"]).total_seconds() / 60
        }
        
        if self.retrieval_system:
            stats["retrieval_stats"] = self.retrieval_system.get_stats()
        
        if self.memory_system:
            stats["memory_summary"] = self.get_memory_summary()
        
        return stats
    
    # ===== Case Planning & Execution (Merged from CasePlanner + ExecutorAgent) =====
    
    def create_and_execute_plan(
        self,
        case_facts: str,
        initial_analysis: Dict[str, Any] = None,
        case_type: str = None,
        case_id: str = None
    ) -> Dict[str, Any]:
        """
        Combined method: Create plan AND execute it with tracking
        دمج من CasePlanner و ExecutorAgent مع تتبع الخطوات
        
        Args:
            case_facts: Case facts
            initial_analysis: Initial analysis results
            case_type: Type of case
            case_id: Case ID
            
        Returns:
            Complete execution results with plan and reports
        """
        logger.info("📋 Creating and executing case plan with tracking...")
        
        # Step 1: Create Plan
        plan = self.create_plan(case_facts, initial_analysis, case_type)
        
        # Step 2: Initialize Plan Tracker
        plan_id = case_id or f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # تحويل الخطة إلى خطوات للـ tracker
        tracker_steps = []
        for area in plan.get('analysis_areas', []):
            tracker_steps.append({
                "title": area.get('area'),
                "description": area.get('description', '')
            })
        
        # إضافة خطوة نهائية للتوصية
        tracker_steps.append({
            "title": "التوصية النهائية",
            "description": "تجميع التحاليل وإعداد التوصية الشاملة"
        })
        
        # إنشاء خطة في الـ tracker
        plan_json = self.plan_tracker.create_plan(
            plan_id=plan_id,
            title=f"معالجة القضية: {case_type or 'عام'}",
            description=case_facts[:200] + "..." if len(case_facts) > 200 else case_facts,
            steps=tracker_steps
        )
        
        logger.info(f"📊 Plan Tracker initialized with {len(tracker_steps)} steps")
        
        # Step 3: Execute Plan with tracking
        case_data = {
            "case_id": case_id,
            "facts": case_facts,
            "general_agent_analysis": initial_analysis,
            "suggested_case_type": case_type,
            "plan": plan
        }
        
        execution_results = self.execute_plan_with_tracking(case_data, plan)
        
        # Mark plan as completed
        final_plan_json = self.plan_tracker.mark_plan_completed()
        
        return {
            "plan": plan,
            "plan_tracker_json": final_plan_json,
            **execution_results
        }
    
    def execute_plan_with_tracking(
        self,
        case_data: Dict[str, Any],
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute plan with step-by-step tracking and streaming
        تنفيذ الخطة مع تتبع كل خطوة وبث الأحداث
        """
        logger.info("🚀 Executing plan with tracking...")
        
        # Initialize streaming
        from ..streaming.events import EventType, StepStatus
        from ..streaming.manager import stream_manager
        
        # Use plan_tracker ID or case_id
        plan_id = self.plan_tracker.current_plan.plan_id if self.plan_tracker.current_plan else case_data.get("case_id", "unknown")
        
        # Register streamer
        streamer = stream_manager.register(plan_id)
        
        # Notify plan started
        streamer.push_plan_event(
            EventType.PLAN_CREATED, 
            {"title": plan.get("title", "Processing Case"), "steps_count": len(plan.get("analysis_areas", []))}
        )
        
        case_id = case_data.get("case_id")
        case_facts = case_data.get("facts")
        
        analysis_results = []
        analysis_areas = plan.get("analysis_areas", [])
        total_steps = len(analysis_areas) + 1  # +1 for final recommendation
        
        step_num = 1
        for area_spec in analysis_areas:
            area_name = area_spec.get("area")
            description = area_spec.get("description", "")
            
            # Start step in tracker
            self.plan_tracker.start_step(step_num)
            logger.info(f"▶️ [{step_num}/{total_steps}] Analyzing: {area_name}")
            
            # Stream: Step Started
            streamer.push_step_event(
                step_id=step_num,
                status=StepStatus.IN_PROGRESS,
                message=f"جاري تحليل: {area_name}",
                progress=int((step_num / total_steps) * 100)
            )
            
            try:
                # Use deep thinking for this area
                query = (
                    f"بصفتك محامٍ expert في {area_name}, قم بالتالي:\n\n"
                    f"**الوقائع:**\n{case_facts}\n\n"
                    f"**التركيز المطلوب:**\n{description}\n\n"
                    f"قدم تحليلاً قانونياً متخصصاً."
                )
                
                result = self.think_deeply(query, context={"case_id": case_id, "area": area_name})
                
                analysis_results.append({
                    "area": area_name,
                    "analysis": result.get("answer"),
                    "confidence": result.get("confidence"),
                    "complexity": result.get("complexity")
                })
                
                # Complete step in tracker
                self.plan_tracker.complete_step(
                    step_num,
                    f"اكتمل التحليل - الثقة: {result.get('confidence', 0):.1%}"
                )
                logger.info(f"✅ [{step_num}] {area_name} completed")
                
                # Stream: Step Completed
                streamer.push_step_event(
                    step_id=step_num,
                    status=StepStatus.COMPLETED,
                    message=f"تم تحليل {area_name} بنجاح",
                    progress=int((step_num / total_steps) * 100)
                )
                
            except Exception as e:
                logger.error(f"❌ Error in step {step_num}: {e}")
                self.plan_tracker.fail_step(step_num, str(e))
                
                # Stream: Step Failed
                streamer.push_step_event(
                    step_id=step_num,
                    status=StepStatus.FAILED,
                    message=f"خطأ في تحليل {area_name}: {str(e)}",
                    error=str(e)
                )
            
            step_num += 1
        
        # Final recommendation step
        self.plan_tracker.start_step(step_num)
        logger.info(f"▶️ [{step_num}] Compiling final recommendation...")
        
        # Stream: Final Step Started
        streamer.push_step_event(
            step_id=step_num,
            status=StepStatus.IN_PROGRESS,
            message="جاري إعداد التوصية النهائية...",
            progress=95
        )
        
        try:
            final_recommendation = self._compile_final_recommendation_simple(
                case_facts=case_facts,
                analysis_results=analysis_results
            )
            
            self.plan_tracker.complete_step(step_num, "تم إعداد التوصية النهائية")
            logger.info(f"✅ [{step_num}] Final recommendation completed")
            
            # Stream: Final Step Completed
            streamer.push_step_event(
                step_id=step_num,
                status=StepStatus.COMPLETED,
                message="تم إعداد التوصية النهائية",
                progress=100
            )
            
            # Stream: Plan Completed
            streamer.push_plan_event(
                EventType.PLAN_COMPLETED,
                {"result": final_recommendation}
            )
            
        except Exception as e:
            logger.error(f"❌ Error in final recommendation: {e}")
            self.plan_tracker.fail_step(step_num, str(e))
            final_recommendation = {"error": str(e)}
            
            # Stream: Plan Failed
            streamer.push_plan_event(
                EventType.PLAN_FAILED,
                {"error": str(e)}
            )
        
        return {
            "analysis_results": analysis_results,
            "final_recommendation": final_recommendation,
            "completed_at": datetime.now().isoformat()
        }

    def create_plan(
        self,
        case_facts: str,
        initial_analysis: Dict[str, Any] = None,
        case_type: str = None
    ) -> Dict[str, Any]:
        """
        Create execution plan (from CasePlanner)
        
        Instead of creating separate specialist agents we use
        the main agent capabilities with different focus areas
        """
        from ..config.settings import AgentTypes
        
        logger.info("📝 Creating execution plan...")
        
        # Simplified planning - no separate agents needed
        # The EnhancedGeneralLawyerAgent handles everything
        
        analysis_text = json.dumps(initial_analysis, ensure_ascii=False, indent=2) if initial_analysis else "لا يوجد"
        
        planning_prompt = (
            f"بصفتك محامٍ expert, ضع خطة تحليل للقضية التالية.\n\n"
            f"**الوقائع:**\n{case_facts}\n\n"
            f"**التحليل الأولي:**\n{analysis_text}\n\n"
            f"**نوع القضية:** {case_type or 'غير محدد'}\n\n"
            f"---\n\n"
            f"قدم خطة تحليل متكاملة تشمل المجالات التالية (JSON):\n"
            f'{{"analysis_areas": [\n'
            f'  {{"area": "التحليل القانوني", "priority": 1, "description": "..."}},\n'
            f'  {{"area": "تحليل الأدلة", "priority": 2, "description": "..."}}\n'
            f'],\n'
            f'"execution_strategy": "sequential",\n'
            f'"estimated_complexity": "simple/medium/complex",\n'
            f'"key_points": ["نقطة 1", "نقطة 2"]\n'
            f'}}\n\n'
            f"أعد JSON فقط:"
        )
        
        try:
            self.add_message("user", planning_prompt)
            plan_response = self.generate_response()
            self.add_message("assistant", plan_response)
            
            # Parse JSON
            import json
            if "{" in plan_response:
                start = plan_response.find("{")
                end = plan_response.rfind("}") + 1
                json_str = plan_response[start:end]
                plan = json.loads(json_str)
            else:
                plan = self._create_default_plan_simple(case_type)
                
        except Exception as e:
            logger.warning(f"⚠️ Plan creation failed: {e}, using default")
            plan = self._create_default_plan_simple(case_type)
        
        logger.info(f"✅ Plan created with {len(plan.get('analysis_areas', []))} areas")
        return plan
    
    def _create_default_plan_simple(self, case_type: str = None) -> Dict[str, Any]:
        """Create default plan when LLM fails"""
        return {
            "analysis_areas": [
                {
                    "area": "التحليل القانوني العام",
                    "priority": 1,
                    "description": "تحليل شامل للقضية"
                }
            ],
            "execution_strategy": "sequential",
            "estimated_complexity": "medium",
            "key_points": ["تحليل الوقائع", "البحث القانوني"]
        }
    
    def execute_plan_simple(
        self,
        case_data: Dict[str, Any],
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the legal plan (simplified - without dynamic agents)
        
        Instead of creating separate specialist agents we use
        the general agent deep thinking for each area
        """
        logger.info("🚀 Executing legal plan (simplified mode)...")
        
        case_id = case_data.get("case_id")
        case_facts = case_data.get("facts")
        
        analysis_results = []
        analysis_areas = plan.get("analysis_areas", [])
        
        for area_spec in analysis_areas:
            area_name = area_spec.get("area")
            description = area_spec.get("description", "")
            
            logger.info(f"▶️ Analyzing: {area_name}")
            
            # Use deep thinking for this area
            query = (
                f"بصفتك محامٍ expert في {area_name}, قم بالتالي:\n\n"
                f"**الوقائع:**\n{case_facts}\n\n"
                f"**التركيز المطلوب:**\n{description}\n\n"
                f"قدم تحليلاً قانونياً متخصصاً."
            )
            
            result = self.think_deeply(query, context={"case_id": case_id, "area": area_name})
            
            analysis_results.append({
                "area": area_name,
                "analysis": result.get("answer"),
                "confidence": result.get("confidence"),
                "complexity": result.get("complexity")
            })
            
            logger.info(f"✅ {area_name} completed (confidence: {result.get('confidence', 0):.1%})")
        
        # Compile final recommendation
        final_recommendation = self._compile_final_recommendation_simple(
            case_facts=case_facts,
            analysis_results=analysis_results
        )
        
        return {
            "analysis_results": analysis_results,
            "final_recommendation": final_recommendation,
            "completed_at": datetime.now().isoformat()
        }
    
    def _compile_final_recommendation_simple(
        self,
        case_facts: str,
        analysis_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compile final recommendation from all analyses"""
        logger.info("📊 Compiling final recommendation...")
        
        
        all_analyses = "\n\n".join([
            f"## {res['area']}\n{res['analysis']}\n(ثقة: {res['confidence']:.1%})"
            for res in analysis_results
        ])
        
        compilation_prompt = (
            f"بصفتك المحامي الرئيسي, اجمع التحاليل التالية في توصية نهائية متكاملة:\n\n"
            f"**الوقائع:**\n{case_facts}\n\n"
            f"**التحاليل المتخصصة:**\n{all_analyses}\n\n"
            f"---\n\n"
            f"قدم توصية نهائية شاملة تتضمن:\n"
            f"1. الملخص التنفيذي\n"
            f"2. الرأي القانوني\n"
            f"3. الاستراتيجية المقترحة\n"
            f"4. التوصيات"
        )
        
        self.add_message("user", compilation_prompt)
        final_response = self.generate_response()
        self.add_message("assistant", final_response)
        
        return {
            "recommendation_text": final_response,
            "compiled_at": datetime.now().isoformat(),
            "based_on_analyses": len(analysis_results),
            "average_confidence": sum(r["confidence"] for r in analysis_results) / len(analysis_results) if analysis_results else 0
        }
    
    # ===== Helper Methods =====
    
    def _determine_importance(self, complexity: QueryComplexity) -> MemoryImportance:
        """Determine memory importance based on query complexity"""
        if complexity == QueryComplexity.EXPERT:
            return MemoryImportance.CRITICAL
        elif complexity == QueryComplexity.COMPLEX:
            return MemoryImportance.HIGH
        elif complexity == QueryComplexity.MODERATE:
            return MemoryImportance.MEDIUM
        else:
            return MemoryImportance.LOW
    
    def _extract_semantic_tags(self, text: str) -> List[str]:
        """Extract semantic tags from text"""
        # Simple keyword extraction (can be enhanced)
        keywords = []
        
        # Legal domain keywords
        legal_terms = ["عقد", "قانون", "محكمة", "قضية", "دعوى", "حكم", "نظام"]
        
        for term in legal_terms:
            if term in text:
                keywords.append(term)
        
        return keywords[:5]  # Limit to 5 tags


__all__ = ["EnhancedGeneralLawyerAgent"]
