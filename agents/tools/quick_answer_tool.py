"""
Quick Answer Tool
أداة الإجابة السريعة على الأسئلة القانونية البسيطة
"""

import time
import logging
from typing import Optional

from .base_tool import BaseTool, ToolResult
from .search_tool import SearchKnowledgeTool
from ..config.openwebui import openwebui_client
from ..config.settings import settings

logger = logging.getLogger(__name__)


class QuickAnswerTool(BaseTool):
    """
    Tool to quickly answer simple legal questions.
    
    Uses multiple sources to find relevant knowledge:
    1. document_chunks (via SearchKnowledgeTool) - Legal text chunks
    2. thought_templates (via LookupPrincipleTool) - Legal principles
    
    Then uses LLM to synthesize a concise answer.
    """
    
    def __init__(self):
        super().__init__(
            name="quick_answer",
            description="إجابة سريعة على سؤال قانوني بسيط باستخدام قاعدة المعرفة والمبادئ"
        )
        self.search_tool = SearchKnowledgeTool()
        self.llm_client = openwebui_client
        
        # Import principle tool lazily to avoid circular imports
        self._principle_tool = None
        
        # Keywords that indicate a simple question
        self.simple_question_keywords = [
            "عقوبة", "حكم", "ما هو", "ما هي", "كم", "هل", 
            "متى", "أين", "كيف", "لماذا", "ما نص"
        ]
    
    @property
    def principle_tool(self):
        if self._principle_tool is None:
            from .lookup_tools import LookupPrincipleTool
            self._principle_tool = LookupPrincipleTool()
        return self._principle_tool
    
    def run(
        self,
        question: str,
        search_limit: int = 3
    ) -> ToolResult:
        """
        Answer a simple question using knowledge base.
        
        Args:
            question: The question to answer.
            search_limit: Number of KB results to use.
            
        Returns:
            ToolResult with the answer.
        """
        self._track_usage()
        start_time = time.time()
        
        try:
            logger.info(f"❓ QuickAnswer: Processing '{question[:50]}...'")
            
            # Step 1: Search document chunks
            search_result = self.search_tool.run(query=question, limit=search_limit)
            
            # Step 2: Search legal principles
            principle_result = self.principle_tool.run(query=question, limit=2)
            
            # Combine context
            context_parts = []
            
            # Add principles first (higher priority)
            if principle_result.success and principle_result.data:
                context_parts.append("**المبادئ القانونية:**")
                for p in principle_result.data:
                    principle_text = p.get("principle_text", "")
                    if principle_text:
                        context_parts.append(f"• {principle_text}")
            
            # Add document chunks
            if search_result.success and search_result.data:
                context_parts.append("\n**النصوص القانونية:**")
                for i, result in enumerate(search_result.data, 1):
                    context_parts.append(f"[{i}] {result['content']}")
            
            context = "\n\n".join(context_parts)
            
            # Step 3: Generate answer using LLM
            prompt = f"""أنت مساعد قانوني. أجب على السؤال التالي بناءً على المعلومات المتوفرة.

**السؤال:** {question}

**المعلومات المتوفرة:**
{context}

**التعليمات:**
- أجب بإيجاز ووضوح (3-5 جمل).
- إذا كانت المعلومات غير كافية، اذكر ذلك.
- لا تختلق معلومات.
- إذا كان السؤال عن عقوبة، اذكر النص القانوني إن وُجد.

**الإجابة:**"""

            messages = [
                {"role": "system", "content": "أنت مساعد قانوني متخصص في القانون السعودي."},
                {"role": "user", "content": prompt}
            ]
            
            answer = self.llm_client.chat_completion(
                messages=messages,
                temperature=0.3,  # Lower for more factual answers
                max_tokens=500
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            logger.info(f"✅ QuickAnswer: Generated answer in {elapsed:.0f}ms")
            
            return ToolResult(
                success=True,
                data={
                    "answer": answer,
                    "sources_used": len(search_result.data),
                    "confidence": "high" if len(search_result.data) >= 2 else "medium"
                },
                metadata={
                    "question": question,
                    "search_results_count": len(search_result.data)
                },
                execution_time_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"❌ QuickAnswer failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def can_handle(self, query: str) -> float:
        """
        Check if this tool can handle the query.
        
        Returns higher confidence for simple questions.
        """
        query_lower = query.lower()
        
        # Signs of a simple question
        is_short = len(query.split()) <= 15
        has_question_mark = "?" in query or "؟" in query
        has_keywords = any(kw in query_lower for kw in self.simple_question_keywords)
        
        # Signs this is NOT a simple question (case intake)
        is_long_narrative = len(query.split()) > 30
        has_case_indicators = any(kw in query_lower for kw in ["قضيتي", "حصل معي", "انا متهم", "عندي مشكلة"])
        
        if is_long_narrative or has_case_indicators:
            return 0.1  # Not a simple question
        
        if has_question_mark and has_keywords and is_short:
            return 0.95  # Very likely a simple question
        elif has_keywords and is_short:
            return 0.7
        elif has_question_mark:
            return 0.5
        
        return 0.2


__all__ = ["QuickAnswerTool"]
