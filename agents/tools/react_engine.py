"""
ReAct Reasoning Engine - Enhanced
محرك التفكير التفاعلي المحسّن - مع دعم كامل للأدوات الجديدة

This implements an enhanced ReAct (Reasoning + Acting) paradigm:
1. THINK: Analyze the question using deep thinking
2. ACT: Use multiple tools with fallback chain
3. OBSERVE: Evaluate and detect contradictions
4. CONTINUE: Request continuation if needed
5. RECOVER: Handle errors gracefully
6. ANSWER: Only when confident
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .base_tool import BaseTool, ToolResult
from .search_tool import SearchKnowledgeTool
from .lookup_tools import LookupPrincipleTool, LegalSourceTool
from .deep_thinking import DeepThinkingTool
from .fetch_tools import FetchByIdTool, FlexibleSearchTool, GetRelatedDocumentTool
from .continuation_tools import (
    ContinueThinkingTool, 
    WaitTool, 
    ErrorRecoveryTool,
    CheckpointTool,
    ThinkingState
)
from ..config.openwebui import openwebui_client

logger = logging.getLogger(__name__)


@dataclass
class ThinkingStep:
    """A single step in the reasoning process"""
    step_number: int
    step_type: str  # THINK, ACT, OBSERVE, RECOVER, CONCLUDE
    content: str
    tool_used: Optional[str] = None
    tool_result: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "type": self.step_type,
            "content": self.content,
            "tool": self.tool_used,
            "result_count": len(self.tool_result.get("data", [])) if self.tool_result else 0,
            "time": self.timestamp.isoformat()
        }


class ReActEngine:
    """
    Enhanced ReAct Reasoning Engine
    
    Features:
    - Multiple search tools with fallback chain
    - Deep thinking with brainstorming and contradiction detection
    - Pagination for large results
    - Error recovery with suggestions
    - Continuation support for long reasoning
    - Checkpoint saving
    """
    
    MAX_ITERATIONS = 5
    MIN_SOURCES = 2
    MAX_RESULTS_PER_SEARCH = 10
    
    def __init__(self):
        # Search Tools (with fallback chain)
        self.search_tool = SearchKnowledgeTool()
        self.flexible_search = FlexibleSearchTool()
        self.principle_tool = LookupPrincipleTool()
        self.source_tool = LegalSourceTool()
        
        # Fetch Tools
        self.fetch_by_id = FetchByIdTool()
        self.get_related = GetRelatedDocumentTool()
        
        # Thinking Tools
        self.deep_thinking = DeepThinkingTool()
        
        # Control Tools
        self.continue_thinking = ContinueThinkingTool()
        self.wait_tool = WaitTool()
        self.error_recovery = ErrorRecoveryTool()
        self.checkpoint = CheckpointTool()
        
        # LLM Client
        self.llm_client = openwebui_client
        
        # Reasoning State
        self.steps: List[ThinkingStep] = []
        self.gathered_info: List[Dict[str, Any]] = []
        self.verified_facts: List[str] = []
        self.errors_encountered: List[Dict[str, Any]] = []
        self.session_id: Optional[str] = None
        
        # Tool registry for dynamic access
        self.tools = {
            "search_knowledge": self.search_tool,
            "flexible_search": self.flexible_search,
            "lookup_principle": self.principle_tool,
            "legal_source": self.source_tool,
            "fetch_by_id": self.fetch_by_id,
            "get_related_document": self.get_related,
            "deep_thinking": self.deep_thinking
        }
        
        logger.info("🧠 Enhanced ReAct Engine initialized with all tools")
    
    def reason(self, question: str, context: str = "") -> Dict[str, Any]:
        """
        Main reasoning loop with enhanced error handling and tool usage.
        """
        start_time = time.time()
        self._reset_state()
        self.session_id = f"session_{int(time.time())}"
        
        logger.info("="*60)
        logger.info("🧠 STARTING ENHANCED REACT REASONING")
        logger.info(f"📝 Question: {question[:100]}...")
        logger.info("="*60)
        
        try:
            # Create initial checkpoint
            self._create_checkpoint("initial")
            
            # Step 1: Deep Analysis with brainstorming
            self._think(f"تحليل السؤال: {question}")
            decomposition = self._deep_analyze_question(question)
            
            # Step 2: Iterative search with multiple strategies
            iteration = 0
            while iteration < self.MAX_ITERATIONS:
                iteration += 1
                logger.info(f"\n🔄 ITERATION {iteration}/{self.MAX_ITERATIONS}")
                
                # Create checkpoint at each iteration
                self._create_checkpoint(f"iteration_{iteration}")
                
                # Plan next search with multiple tool options
                search_plan = self._plan_next_search(question, decomposition)
                
                if search_plan.get("ready_to_answer"):
                    logger.info("✅ Agent decided: Ready to answer")
                    break
                
                # Execute searches with fallback chain
                for query_plan in search_plan.get("queries", []):
                    self._execute_search_with_fallback(query_plan)
                
                # Check for contradictions in gathered info
                if len(self.gathered_info) >= 3:
                    self._check_contradictions(question)
                
                # Verify information sufficiency
                verification = self._verify_information(question)
                
                if verification.get("is_sufficient"):
                    logger.info("✅ Verification: Information is sufficient")
                    break
                else:
                    missing = verification.get('missing', 'Unknown')
                    logger.info(f"⚠️ Need more info: {missing}")
            
            # Step 3: Challenge assumptions before final answer
            if self.verified_facts:
                self._challenge_conclusions(question)
            
            # Step 4: Generate final answer
            answer = self._generate_final_answer(question, context)
            
            elapsed = time.time() - start_time
            
            logger.info("="*60)
            logger.info(f"🏁 REASONING COMPLETE in {elapsed:.2f}s")
            logger.info(f"📊 Steps: {len(self.steps)}, Sources: {len(self.gathered_info)}")
            logger.info("="*60)
            
            return {
                "answer": answer,
                "reasoning_steps": [s.to_dict() for s in self.steps],
                "sources_used": len(self.gathered_info),
                "verified_facts": self.verified_facts,
                "iterations": iteration,
                "errors_recovered": len(self.errors_encountered),
                "elapsed_seconds": elapsed,
                "session_id": self.session_id
            }
            
        except Exception as e:
            logger.error(f"❌ Reasoning failed: {e}")
            # Try to recover
            recovery = self._handle_critical_error(str(e), question)
            return {
                "answer": recovery.get("fallback_answer", f"عذراً، حدث خطأ: {str(e)}"),
                "error": str(e),
                "reasoning_steps": [s.to_dict() for s in self.steps],
                "recovery_attempted": True
            }
    
    def _reset_state(self):
        """Reset all state for new reasoning session"""
        self.steps = []
        self.gathered_info = []
        self.verified_facts = []
        self.errors_encountered = []
    
    def _think(self, thought: str):
        """Log a thinking step"""
        step = ThinkingStep(
            step_number=len(self.steps) + 1,
            step_type="THINK",
            content=thought
        )
        self.steps.append(step)
        logger.info(f"💭 THINK: {thought[:100]}...")
    
    def _act(self, action: str, tool_name: str, result: ToolResult):
        """Log an action step"""
        step = ThinkingStep(
            step_number=len(self.steps) + 1,
            step_type="ACT",
            content=action,
            tool_used=tool_name,
            tool_result=result.to_dict() if hasattr(result, 'to_dict') else {"data": result.data}
        )
        self.steps.append(step)
        
        result_count = len(result.data) if isinstance(result.data, list) else (1 if result.data else 0)
        logger.info(f"🔧 ACT: {action}")
        logger.info(f"   Tool: {tool_name} -> {result_count} results")
        
        # Store results
        if result.success and result.data:
            if isinstance(result.data, list):
                self.gathered_info.extend(result.data)
            else:
                self.gathered_info.append(result.data)
    
    def _observe(self, observation: str):
        """Log an observation step"""
        step = ThinkingStep(
            step_number=len(self.steps) + 1,
            step_type="OBSERVE",
            content=observation
        )
        self.steps.append(step)
        logger.info(f"👁️ OBSERVE: {observation[:100]}...")
    
    def _recover(self, error: str, recovery_action: str):
        """Log a recovery step"""
        step = ThinkingStep(
            step_number=len(self.steps) + 1,
            step_type="RECOVER",
            content=f"خطأ: {error}\nاستعادة: {recovery_action}"
        )
        self.steps.append(step)
        logger.info(f"🔄 RECOVER: {recovery_action}")
    
    def _create_checkpoint(self, label: str):
        """Create a checkpoint for recovery"""
        self.checkpoint.run(
            action="create",
            checkpoint_id=f"{self.session_id}_{label}",
            data={
                "gathered_info_count": len(self.gathered_info),
                "verified_facts": self.verified_facts.copy(),
                "step_count": len(self.steps)
            },
            label=label
        )
    
    def _deep_analyze_question(self, question: str) -> Dict[str, Any]:
        """Deep analysis using multiple thinking modes"""
        self._think("تفكيك السؤال وتحليله بالعصف الذهني")
        
        # Decompose
        result = self.deep_thinking.run(question=question, mode="decompose")
        decomposition = result.data if result.success else {}
        
        sub_questions = decomposition.get("sub_questions", [])
        self._observe(f"تم تحديد {len(sub_questions)} سؤال فرعي")
        
        # Brainstorm for additional insights
        brainstorm_result = self.deep_thinking.run(question=question, mode="brainstorm")
        if brainstorm_result.success:
            ideas = brainstorm_result.data.get("ideas", [])
            decomposition["brainstorm_ideas"] = ideas[:5]
            self._observe(f"تم توليد {len(ideas)} فكرة من العصف الذهني")
        
        return decomposition
    
    def _plan_next_search(self, question: str, decomposition: Dict[str, Any]) -> Dict[str, Any]:
        """Plan next search with tool recommendations"""
        prompt = f"""أنت وكيل قانوني ذكي. خطط للبحث التالي.

**السؤال:** {question}

**المعلومات المجموعة:** {len(self.gathered_info)} مصدر

**الأدوات المتاحة:**
1. search_knowledge - بحث في النصوص القانونية
2. flexible_search - بحث مرن بأساليب متعددة
3. lookup_principle - بحث في المبادئ القانونية
4. fetch_by_id - جلب مستند بالـ ID
5. get_related_document - جلب المستند الأصلي

**أجب بـ JSON:**
{{
  "ready_to_answer": true/false,
  "reason": "السبب",
  "queries": [
    {{"query": "استعلام", "tool": "search_knowledge", "priority": "high/medium/low"}}
  ]
}}"""

        try:
            response = self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "أنت وكيل قانوني. أجب بـ JSON فقط."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            plan = self._parse_json(response)
            self._think(plan.get("reason", "تخطيط البحث"))
            return plan
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return {"queries": [{"query": question, "tool": "flexible_search"}], "ready_to_answer": False}
    
    def _execute_search_with_fallback(self, query_plan: Dict[str, Any]):
        """Execute search with fallback chain"""
        query = query_plan.get("query") if isinstance(query_plan, dict) else str(query_plan)
        preferred_tool = query_plan.get("tool", "flexible_search") if isinstance(query_plan, dict) else "flexible_search"
        
        logger.info(f"\n🔍 SEARCHING: {query[:50]}...")
        
        # Fallback chain
        fallback_chain = [
            ("flexible_search", self._search_flexible),
            ("search_knowledge", self._search_knowledge),
            ("lookup_principle", self._search_principles)
        ]
        
        # Move preferred tool to front
        for i, (name, _) in enumerate(fallback_chain):
            if name == preferred_tool:
                fallback_chain.insert(0, fallback_chain.pop(i))
                break
        
        # Try each tool in chain
        for tool_name, search_func in fallback_chain:
            try:
                result = search_func(query)
                if result.success and result.data:
                    self._act(f"البحث عن: {query[:30]}...", tool_name, result)
                    return  # Success, stop fallback
                else:
                    logger.warning(f"⚠️ {tool_name} returned no results")
            except Exception as e:
                logger.error(f"❌ {tool_name} failed: {e}")
                self.errors_encountered.append({"tool": tool_name, "error": str(e)})
                continue
        
        # All failed - try error recovery
        self._recover(
            f"جميع أدوات البحث فشلت للاستعلام: {query}",
            "سيتم الاستمرار بالمعلومات المتوفرة"
        )
    
    def _search_flexible(self, query: str) -> ToolResult:
        """Search using FlexibleSearchTool"""
        return self.flexible_search.run(
            query=query,
            tables=["document_chunks", "thought_templates"],
            method="any",
            limit=self.MAX_RESULTS_PER_SEARCH
        )
    
    def _search_knowledge(self, query: str) -> ToolResult:
        """Search using SearchKnowledgeTool"""
        return self.search_tool.run(query=query, limit=5)
    
    def _search_principles(self, query: str) -> ToolResult:
        """Search using LookupPrincipleTool"""
        return self.principle_tool.run(query=query, limit=5)
    
    def _check_contradictions(self, question: str):
        """Check for contradictions in gathered information"""
        self._think("فحص المعلومات للبحث عن تناقضات")
        
        result = self.deep_thinking.run(
            question=question,
            mode="contradictions",
            gathered_info=self.gathered_info[:10]
        )
        
        if result.success and result.data.get("contradictions_found"):
            contradictions = result.data.get("contradictions", [])
            self._observe(f"⚠️ تم اكتشاف {len(contradictions)} تناقض")
            
            # Log contradictions for final answer
            for c in contradictions[:2]:
                logger.warning(f"   ⚡ {c.get('explanation', str(c))[:100]}")
    
    def _challenge_conclusions(self, question: str):
        """Challenge assumptions before final answer"""
        self._think("تحدي الاستنتاجات كمحامي شيطان")
        
        result = self.deep_thinking.run(
            question=question,
            mode="challenge",
            previous_conclusions=self.verified_facts[:5]
        )
        
        if result.success:
            challenges = result.data.get("challenges", [])
            hidden = result.data.get("hidden_assumptions", [])
            
            if challenges or hidden:
                self._observe(f"تم تحديد {len(challenges)} تحدي و {len(hidden)} افتراض ضمني")
    
    def _verify_information(self, question: str) -> Dict[str, Any]:
        """Verify if gathered information is sufficient"""
        self._think("التحقق من كفاية المعلومات")
        
        info_summary = []
        for item in self.gathered_info[:5]:
            if isinstance(item, dict):
                content = item.get("content") or item.get("principle_text") or item.get("template_text") or str(item)
                info_summary.append(content[:200])
        
        prompt = f"""أنت مدقق قانوني. راجع المعلومات وقرر كفايتها.

**السؤال:** {question}

**المعلومات ({len(self.gathered_info)} مصدر):**
{chr(10).join(info_summary) if info_summary else "لا توجد معلومات"}

**أجب بـ JSON:**
{{
  "is_sufficient": true/false,
  "missing": "ما الناقص",
  "verified_facts": ["حقيقة 1"],
  "confidence": 0.0-1.0
}}"""

        try:
            response = self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "أنت مدقق قانوني. أجب بـ JSON فقط."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=400
            )
            
            verification = self._parse_json(response)
            self.verified_facts.extend(verification.get("verified_facts", []))
            self._observe(f"الثقة: {verification.get('confidence', 0)}")
            
            return verification
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {"is_sufficient": len(self.gathered_info) >= self.MIN_SOURCES}
    
    def _generate_final_answer(self, question: str, context: str) -> str:
        """Generate final answer"""
        self._think("إعداد الإجابة النهائية")
        
        sources_text = []
        for i, item in enumerate(self.gathered_info[:10], 1):
            if isinstance(item, dict):
                content = item.get("content") or item.get("principle_text") or item.get("template_text") or str(item)
                sources_text.append(f"[{i}] {content[:300]}")
        
        prompt = f"""أنت محامي خبير. أجب على السؤال بناءً على المصادر.

**السؤال:** {question}

**المصادر ({len(self.gathered_info)}):**
{chr(10).join(sources_text)}

**الحقائق المحققة:**
{json.dumps(self.verified_facts, ensure_ascii=False) if self.verified_facts else "لا يوجد"}

**التعليمات:**
1. أجب بشكل شامل ومفصل
2. اذكر الأساس القانوني
3. اذكر الاستثناءات
4. إذا المعلومات ناقصة أوضح ذلك

**الإجابة:**"""

        try:
            answer = self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "أنت محامي سعودي خبير. قدم إجابات قانونية دقيقة."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            
            step = ThinkingStep(
                step_number=len(self.steps) + 1,
                step_type="CONCLUDE",
                content="تم إعداد الإجابة النهائية"
            )
            self.steps.append(step)
            logger.info(f"📝 CONCLUDE: Answer generated ({len(answer)} chars)")
            
            return answer
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return f"عذراً، حدث خطأ أثناء إعداد الإجابة: {str(e)}"
    
    def _handle_critical_error(self, error: str, question: str) -> Dict[str, Any]:
        """Handle critical errors with recovery"""
        recovery_result = self.error_recovery.run(
            error_code="CRITICAL_ERROR",
            error_message=error,
            context={"question": question, "gathered_count": len(self.gathered_info)}
        )
        
        if recovery_result.success:
            suggestions = recovery_result.data.get("suggestions", [])
            self._recover(error, "; ".join(suggestions[:2]))
        
        # Try to generate partial answer
        if self.gathered_info:
            return {"fallback_answer": self._generate_final_answer(question, "")}
        
        return {"fallback_answer": None}
    
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
            elif text.strip().startswith("{"):
                json_str = text.strip()
            else:
                start = text.find("{")
                end = text.rfind("}") + 1
                json_str = text[start:end] if start != -1 else "{}"
            
            return json.loads(json_str)
        except:
            return {}
    
    def fetch_related_document(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the full document related to a chunk"""
        result = self.get_related.run(chunk_id=chunk_id, include_siblings=True)
        if result.success:
            return result.data
        return None
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self.tools.get(tool_name)


__all__ = ["ReActEngine", "ThinkingStep"]
