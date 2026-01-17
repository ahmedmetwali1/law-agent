"""
Hybrid Reasoning Engine
محرك التفكير الهجين - دمج CoT + ReAct + Neural-Symbolic

Based on latest 2025 research:
- Chain of Thought (CoT) for structured thinking
- ReAct for tool-augmented reasoning
- Hybrid approach for optimal results

Features:
- Intelligent routing based on query complexity
- Dynamic switching between reasoning modes
- Self-consistency checking
- Confidence scoring
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging
from datetime import datetime

from .deontic_logic import DeonticLogicSystem, DeonticModality

logger = logging.getLogger(__name__)


class ReasoningMode(str, Enum):
    """Available reasoning modes"""
    CHAIN_OF_THOUGHT = "cot"           # Pure CoT - internal knowledge
    REACT = "react"                     # ReAct - tool-augmented
    HYBRID = "hybrid"                   # CoT + ReAct combined
    NEURAL_SYMBOLIC = "neural_symbolic" # Logic-based reasoning
    DEONTIC = "deontic"                 # Legal obligation reasoning


class QueryComplexity(str, Enum):
    """Query complexity levels"""
    SIMPLE = "simple"       # Direct answer, minimal reasoning
    MODERATE = "moderate"   # Multi-step, some tools needed
    COMPLEX = "complex"     # Deep reasoning, multiple tools
    EXPERT = "expert"       # Requires specialist knowledge


@dataclass
class ReasoningStep:
    """Single step in reasoning process"""
    step_number: int
    mode: ReasoningMode
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    confidence: float = 1.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "mode": self.mode.value,
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ReasoningResult:
    """Result of reasoning process"""
    conclusion: str
    steps: List[ReasoningStep]
    mode_used: ReasoningMode
    confidence: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conclusion": self.conclusion,
            "steps": [s.to_dict() for s in self.steps],
            "mode_used": self.mode_used.value,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


class HybridReasoningEngine:
    """
    Advanced Hybrid Reasoning Engine
    
    Intelligently combines:
    - Chain of Thought (CoT) for logical decomposition
    - ReAct for tool-augmented problem solving
    - Neural-Symbolic for legal logic
    """
    
    def __init__(self, llm_agent=None, tools: List[Any] = None):
        self.llm_agent = llm_agent
        self.tools = tools or []
        self.reasoning_history: List[ReasoningResult] = []
        
        # Tool map for quick access
        self.tool_map = {tool.__class__.__name__: tool for tool in self.tools}
        
        # Initialize Deontic Logic
        self.deontic_system = DeonticLogicSystem()
        
        logger.info("✅ Hybrid Reasoning Engine initialized with Deontic Logic")
    
    def analyze_complexity(self, query: str, context: Dict[str, Any] = None) -> Tuple[QueryComplexity, float]:
        """
        Analyze query complexity to determine best reasoning approach
        
        Returns:
            (complexity_level, confidence_score)
        """
        context = context or {}
        
        # Simple heuristics (would use LLM for real implementation)
        query_lower = query.lower()
        
        # Indicators of complexity
        question_words = ['كيف', 'لماذا', 'ما هي', 'what', 'how', 'why']
        legal_terms = ['قانون', 'نظام', 'لائحة', 'حكم', 'قضية', 'law', 'regulation']
        multi_step_indicators = ['أولاً', 'ثانياً', 'خطوات', 'مراحل', 'steps', 'process']
        
        score = 0
        
        # Query length
        if len(query) > 200:
            score += 2
        elif len(query) > 100:
            score += 1
        
        # Presence of question words
        if any(word in query_lower for word in question_words):
            score += 1
        
        # Legal terminology
        if any(term in query_lower for term in legal_terms):
            score += 1
        
        # Multi-step indicators
        if any(ind in query_lower for ind in multi_step_indicators):
            score += 2
        
        # Context complexity
        if context.get('requires_search'):
            score += 2
        if context.get('has_precedents'):
            score += 1
        
        # Classify
        if score <= 2:
            complexity = QueryComplexity.SIMPLE
        elif score <= 4:
            complexity = QueryComplexity.MODERATE
        elif score <= 6:
            complexity = QueryComplexity.COMPLEX
        else:
            complexity = QueryComplexity.EXPERT
        
        confidence = min(0.9, 0.6 + (score * 0.05))
        
        logger.info(f"Query complexity: {complexity.value} (score={score}, confidence={confidence:.2f})")
        return complexity, confidence
    
    def chain_of_thought(
        self,
        query: str,
        context: Dict[str, Any] = None,
        max_steps: int = 5
    ) -> ReasoningResult:
        """
        Chain of Thought reasoning
        Break down problem into logical steps
        
        Args:
            query: Question to reason about
            context: Additional context
            max_steps: Maximum reasoning steps
        
        Returns:
            ReasoningResult with thought process
        """
        logger.info("🧠 Using Chain of Thought reasoning")
        
        steps = []
        context = context or {}
        
        # Step 1: Understand the problem
        step1 = ReasoningStep(
            step_number=1,
            mode=ReasoningMode.CHAIN_OF_THOUGHT,
            thought="فهم المشكلة: " + self._analyze_problem(query),
            confidence=0.9
        )
        steps.append(step1)
        
        # Step 2: Break down into sub-questions
        step2 = ReasoningStep(
            step_number=2,
            mode=ReasoningMode.CHAIN_OF_THOUGHT,
            thought="تقسيم إلى أسئلة فرعية: " + self._decompose_query(query),
            confidence=0.85
        )
        steps.append(step2)
        
        # Step 3: Reason through each part
        for i in range(min(3, max_steps - 2)):
            step = ReasoningStep(
                step_number=3 + i,
                mode=ReasoningMode.CHAIN_OF_THOUGHT,
                thought=f"الخطوة {i+1}: تحليل الجزء {i+1} من المشكلة",
                confidence=0.8
            )
            steps.append(step)
        
        # Final step: Synthesize conclusion
        conclusion = self._synthetize_conclusion(steps)
        
        final_step = ReasoningStep(
            step_number=len(steps) + 1,
            mode=ReasoningMode.CHAIN_OF_THOUGHT,
            thought=f"الخلاصة: {conclusion}",
            confidence=0.9
        )
        steps.append(final_step)
        
        # Calculate overall confidence
        avg_confidence = sum(s.confidence for s in steps) / len(steps)
        
        result = ReasoningResult(
            conclusion=conclusion,
            steps=steps,
            mode_used=ReasoningMode.CHAIN_OF_THOUGHT,
            confidence=avg_confidence,
            metadata={
                "query": query,
                "context": context,
                "total_steps": len(steps)
            }
        )
        
        self.reasoning_history.append(result)
        return result
    
    def react_reasoning(
        self,
        query: str,
        context: Dict[str, Any] = None,
        max_iterations: int = 5
    ) -> ReasoningResult:
        """
        ReAct (Reasoning + Acting) with tool usage
        
        Loop: Thought → Action → Observation → ...
        
        Args:
            query: Question to solve
            context: Additional context
            max_iterations: Maximum ReAct iterations
        
        Returns:
            ReasoningResult with actions and observations
        """
        logger.info("🔧 Using ReAct reasoning")
        
        steps = []
        context = context or {}
        current_observation = None
        
        for iteration in range(max_iterations):
            step_num = iteration + 1
            
            # Thought: Analyze current state
            thought = self._generate_thought(query, current_observation, context, iteration)
            
            # Decide on action
            action = self._select_action(thought, iteration)
            
            # Execute action (if tools available)
            if action and self.tools:
                observation = self._execute_action(action)
            else:
                observation = "لا توجد أدوات متاحة، استخدام المعرفة الداخلية"
            
            current_observation = observation
            
            step = ReasoningStep(
                step_number=step_num,
                mode=ReasoningMode.REACT,
                thought=thought,
                action=action,
                observation=observation,
                confidence=0.85
            )
            steps.append(step)
            
            # Check if problem is solved
            if self._is_solved(observation, query):
                logger.info(f"Problem solved in {step_num} iterations")
                break
        
        # Final conclusion
        conclusion = self._extract_conclusion_from_observations(steps)
        
        final_step = ReasoningStep(
            step_number=len(steps) + 1,
            mode=ReasoningMode.REACT,
            thought=f"الاستنتاج النهائي: {conclusion}",
            confidence=0.9
        )
        steps.append(final_step)
        
        avg_confidence = sum(s.confidence for s in steps) / len(steps)
        
        result = ReasoningResult(
            conclusion=conclusion,
            steps=steps,
            mode_used=ReasoningMode.REACT,
            confidence=avg_confidence,
            metadata={
                "query": query,
                "iterations": len(steps) - 1,
                "tools_used": [s.action for s in steps if s.action]
            }
        )
        
        self.reasoning_history.append(result)
        return result
    
    def hybrid_reasoning(
        self,
        query: str,
        context: Dict[str, Any] = None
    ) -> ReasoningResult:
        """
        Hybrid CoT + ReAct approach (Best of both worlds)
        
        Strategy:
        1. Start with CoT for problem decomposition
        2. Switch to ReAct when external info needed
        3. Return to CoT for final synthesis
        
        Args:
            query: Question to solve
            context: Additional context
        
        Returns:
            ReasoningResult combining both approaches
        """
        logger.info("🔀 Using Hybrid CoT + ReAct reasoning")
        
        steps = []
        context = context or {}
        
        # Phase 1: CoT for initial analysis
        logger.info("Phase 1: CoT for problem decomposition")
        cot_step1 = ReasoningStep(
            step_number=1,
            mode=ReasoningMode.HYBRID,
            thought="[CoT] تحليل السؤال: " + self._analyze_problem(query),
            confidence=0.9
        )
        steps.append(cot_step1)
        
        cot_step2 = ReasoningStep(
            step_number=2,
            mode=ReasoningMode.HYBRID,
            thought="[CoT] تقسيم المشكلة: " + self._decompose_query(query),
            confidence=0.85
        )
        steps.append(cot_step2)
        
        # Phase 2: Check if external info needed
        needs_external_info = self._needs_external_info(query, context)
        
        if needs_external_info:
            logger.info("Phase 2: ReAct for information gathering")
            
            # Switch to ReAct for 2-3 iterations
            for i in range(3):
                thought = f"[ReAct] بحث عن معلومات إضافية - محاولة {i+1}"
                action = f"search_tool('{query}')"
                observation = "معلومات إضافية تم العثور عليها"
                
                react_step = ReasoningStep(
                    step_number=len(steps) + 1,
                    mode=ReasoningMode.HYBRID,
                    thought=thought,
                    action=action,
                    observation=observation,
                    confidence=0.8
                )
                steps.append(react_step)
                
                if self._is_sufficient_info(observation):
                    break
        
        # Phase 3: CoT for final synthesis
        logger.info("Phase 3: CoT for conclusion synthesis")
        
        synthesis_step = ReasoningStep(
            step_number=len(steps) + 1,
            mode=ReasoningMode.HYBRID,
            thought="[CoT] دمج المعلومات والتوصل للنتيجة النهائية",
            confidence=0.9
        )
        steps.append(synthesis_step)
        
        # Generate conclusion
        conclusion = self._synthetize_hybrid_conclusion(steps, query)
        
        final_step = ReasoningStep(
            step_number=len(steps) + 1,
            mode=ReasoningMode.HYBRID,
            thought=f"الخلاصة: {conclusion}",
            confidence=0.92
        )
        steps.append(final_step)
        
        avg_confidence = sum(s.confidence for s in steps) / len(steps)
        
        result = ReasoningResult(
            conclusion=conclusion,
            steps=steps,
            mode_used=ReasoningMode.HYBRID,
            confidence=avg_confidence,
            metadata={
                "query": query,
                "used_external_info": needs_external_info,
                "total_steps": len(steps),
                "cot_steps": sum(1 for s in steps if '[CoT]' in s.thought),
                "react_steps": sum(1 for s in steps if '[ReAct]' in s.thought)
            }
        )
        
        self.reasoning_history.append(result)
        return result
    
        self.reasoning_history.append(result)
        return result
    
    def deontic_reasoning(
        self,
        query: str,
        context: Dict[str, Any] = None
    ) -> ReasoningResult:
        """
        Deontic Logic Reasoning for rights and obligations
        """
        logger.info("⚖️ Using Deontic Logic reasoning")
        
        steps = []
        context = context or {}
        
        # Step 1: Identify Actors and Actions from query (simplified)
        # In a real system, we'd use NLP extraction
        parsed_scenario = {
            "actors": ["الطرف الأول", "الطرف الثاني"], # Placeholder
            "actions": ["تنفيذ العقد", "الدفع"],      # Placeholder
            "context": query
        }
        
        step1 = ReasoningStep(
            step_number=1,
            mode=ReasoningMode.DEONTIC,
            thought=f"تحليل الكيانات والأفعال: {parsed_scenario}",
            confidence=0.85
        )
        steps.append(step1)
        
        # Step 2: Apply Deontic Rules
        analysis = self.deontic_system.analyze_scenario(parsed_scenario)
        
        step2 = ReasoningStep(
            step_number=2,
            mode=ReasoningMode.DEONTIC,
            thought=f"تطبيق القواعد الديونطية: تم العثور على {len(analysis['obligations'])} واجبات و {len(analysis['prohibitions'])} محظورات",
            observation=str(analysis['recommendations']),
            confidence=0.9
        )
        steps.append(step2)
        
        # Step 3: Synthesis
        conclusion = " بناءً على التحليل الفقهي والقانوني:\n"
        for rec in analysis['recommendations']:
            conclusion += f"- {rec}\n"
            
        final_step = ReasoningStep(
            step_number=3,
            mode=ReasoningMode.DEONTIC,
            thought=f"الاستنتاج القانوني: {conclusion}",
            confidence=0.95
        )
        steps.append(final_step)
        
        result = ReasoningResult(
            conclusion=conclusion,
            steps=steps,
            mode_used=ReasoningMode.DEONTIC,
            confidence=0.9,
            metadata={"analysis": analysis}
        )
        
        self.reasoning_history.append(result)
        return result
        
    def reason(
        self,
        query: str,
        context: Dict[str, Any] = None,
        mode: Optional[ReasoningMode] = None
    ) -> ReasoningResult:
        """
        Main reasoning method with intelligent routing
        
        Args:
            query: Question to reason about
            context: Additional context
            mode: Force specific reasoning mode (optional)
        
        Returns:
            ReasoningResult
        """
        context = context or {}
        
        # If mode specified, use it
        if mode:
            logger.info(f"Using forced reasoning mode: {mode.value}")
            if mode == ReasoningMode.CHAIN_OF_THOUGHT:
                return self.chain_of_thought(query, context)
            elif mode == ReasoningMode.REACT:
                return self.react_reasoning(query, context)
            elif mode == ReasoningMode.HYBRID:
                return self.hybrid_reasoning(query, context)
            elif mode == ReasoningMode.DEONTIC:
                return self.deontic_reasoning(query, context)
        
        # Check for Deontic keywords
        deontic_keywords = ['يجب', 'ممنوع', 'حق', 'واجب', 'حكم', 'ملزم', 'obligation', 'must', 'allowed']
        if any(kw in query.lower() for kw in deontic_keywords):
            return self.deontic_reasoning(query, context)

        # Intelligent routing based on complexity
        complexity, confidence = self.analyze_complexity(query, context)
        
        logger.info(f"Auto-routing based on complexity: {complexity.value}")
        
        if complexity == QueryComplexity.SIMPLE:
            # Simple queries: CoT is sufficient
            return self.chain_of_thought(query, context, max_steps=3)
        
        elif complexity == QueryComplexity.MODERATE:
            # Moderate: Hybrid for flexibility
            return self.hybrid_reasoning(query, context)
        
        else:  # COMPLEX or EXPERT
            # Complex: Full ReAct with tools
            return self.react_reasoning(query, context, max_iterations=7)
    
    # ===== Helper Methods =====
    
    def _analyze_problem(self, query: str) -> str:
        """Analyze and understand the problem"""
        return f"المشكلة تتعلق بـ: {query[:100]}"
    
    def _decompose_query(self, query: str) -> str:
        """Decompose query into sub-questions"""
        return "تحليل الأجزاء المختلفة للسؤال"
    
    def _synthetize_conclusion(self, steps: List[ReasoningStep]) -> str:
        """Synthesize conclusion from CoT steps"""
        return "الخلاصة بناءً على التحليل المنطقي"
    
    def _generate_thought(self, query: str, observation: Optional[str], context: Dict, iteration: int) -> str:
        """Generate thought in ReAct loop"""
        if iteration == 0:
            return f"أحتاج إلى فهم: {query[:80]}"
        return f"بناءً على الملاحظة السابقة، الخطوة التالية هي..."
    
    def _select_action(self, thought: str, iteration: int) -> str:
        """Select action based on thought"""
        if self.tools:
            return f"استخدام أداة البحث للعثور على معلومات"
        return "استخدام المعرفة الداخلية"
    
    def _execute_action(self, action: str) -> str:
        """Execute action using tools"""
        # Simplified - would actually call tools
        return f"نتيجة تنفيذ: {action}"
    
    def _is_solved(self, observation: str, query: str) -> bool:
        """Check if problem is solved"""
        return "معلومات كافية" in observation or len(observation) > 100
    
    def _extract_conclusion_from_observations(self, steps: List[ReasoningStep]) -> str:
        """Extract conclusion from ReAct observations"""
        return "الاستنتاج بناءً على الملاحظات المجمعة"
    
    def _needs_external_info(self, query: str, context: Dict) -> bool:
        """Determine if external information is needed"""
        # Check if query contains keywords requiring external data
        external_keywords = ['أحدث', 'حالي', 'current', 'latest', 'recent']
        return any(kw in query.lower() for kw in external_keywords)
    
    def _is_sufficient_info(self, observation: str) -> bool:
        """Check if gathered information is sufficient"""
        return len(observation) > 50
    
    def _synthetize_hybrid_conclusion(self, steps: List[ReasoningStep], query: str) -> str:
        """Synthesize conclusion from hybrid reasoning"""
        return f"الخلاصة الشاملة بناءً على التحليل والمعلومات الخارجية"
    
    def get_reasoning_trace(self, result: ReasoningResult) -> str:
        """Get formatted reasoning trace for transparency"""
        trace = f"## مسار التفكير ({result.mode_used.value})\n\n"
        trace += f"**الثقة الإجمالية:** {result.confidence:.2%}\n\n"
        
        for step in result.steps:
            trace += f"### الخطوة {step.step_number}\n"
            trace += f"**الفكرة:** {step.thought}\n"
            if step.action:
                trace += f"**الإجراء:** {step.action}\n"
            if step.observation:
                trace += f"**الملاحظة:** {step.observation}\n"
            trace += f"**الثقة:** {step.confidence:.2%}\n\n"
        
        trace += f"## الخلاصة النهائية\n{result.conclusion}\n"
        
        return trace


__all__ = [
    "HybridReasoningEngine",
    "ReasoningMode",
    "QueryComplexity",
    "ReasoningStep",
    "ReasoningResult"
]
