
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
from agents.core.base_agent import LLMAgent
from pydantic import BaseModel, Field
from agents.common.structured_output import parse_structured_output
import logging
import json

logger = logging.getLogger(__name__)

class DEPARTState(str, Enum):
    DIVIDE = "divide"
    EVALUATE = "evaluate"
    PLAN = "plan"
    ACT = "act"
    REFLECT = "reflect"
    TRACK = "track"

@dataclass
class DEPARTTask:
    task_id: int
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None

# --- Structured Models ---
class DivideTaskResponse(BaseModel):
    sub_tasks: List[str] = Field(..., description="قائمة المهام الفرعية")

class ReflectionResponse(BaseModel):
    is_valid: bool = Field(..., description="هل الرد صالح ودقيق؟")
    critique: str = Field(..., description="الملاحظات والنقد")
    improved_response: Optional[str] = Field(None, description="الرد المحسن إذا لزم الأمر")

class DEPARTEngine:
    """
    Implements the DEPART Framework:
    D - Divide: Break down complex tasks
    E - Evaluate: Assess current state
    P - Plan: Determine next steps
    A - Act: Execute actions (tools/response)
    R - Reflect: Critique and verify
    T - Track: Monitor progress
    """
    
    def __init__(self, agent: LLMAgent):
        self.agent = agent
        self.current_state = DEPARTState.EVALUATE
        self.tasks: List[DEPARTTask] = []
    
    def divide_task(self, main_objective: str) -> List[DEPARTTask]:
        """
        Divide the main objective into smaller sub-tasks using LLM.
        """
        logger.info(f"➗ Dividing task: {main_objective}")
        
        prompt = f"""
        الهدف الرئيسي: {main_objective}
        
        قم بتقسيم هذا الهدف إلى مهام فرعية صغيرة وقابلة للتنفيذ (Sub-tasks).
        يجب أن تكون المهام متسلسلة ومنطقية.
        
        أعد الإجابة بصيغة JSON فقط:
        {{
            "sub_tasks": [
                "مهمة 1",
                "مهمة 2",
                ...
            ]
        }}
        """
        
        response = self.agent.generate_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        # Parse using Structured Output Utility
        parsed_model = parse_structured_output(response, DivideTaskResponse)
        
        if parsed_model:
            sub_tasks = parsed_model.sub_tasks
            new_tasks = []
            for i, desc in enumerate(sub_tasks):
                task = DEPARTTask(task_id=i+1, description=desc)
                new_tasks.append(task)
            
            self.tasks = new_tasks
            logger.info(f"✅ Created {len(new_tasks)} sub-tasks")
            return new_tasks
            
        else:
            logger.error(f"❌ Failed to divide task via structured output")
            # Fallback: Treat as one single task
            fallback_task = DEPARTTask(task_id=1, description=main_objective)
            self.tasks = [fallback_task]
            return [fallback_task]

    def evaluate_state(self, context: Dict[str, Any]) -> str:
        """
        Evaluate the current context to determine needs.
        Returns a short assessment string.
        """
        logger.info("⚖️ Evaluating state...")
        
        # Simple heuristic or LLM based evaluation
        missing_info = []
        if not context.get("facts"): missing_info.append("facts")
        if not context.get("client_name"): missing_info.append("client_name")
        
        if missing_info:
            assessment = f"Missing core information: {', '.join(missing_info)}"
        else:
            assessment = "Sufficient information available for analysis."
            
        logger.info(f"📊 Assessment: {assessment}")
        return assessment

    def reflect_on_response(self, proposed_response: str, context: str) -> Dict[str, Any]:
        """
        Reflect on the proposed response to catch hallucinations or missing info.
        """
        logger.info("🪞 Reflecting on response...")
        
        prompt = f"""
        سياق المحادثة:
        {context}
        
        الرد المقترح:
        {proposed_response}
        
        قم بنقد هذا الرد. هل هو:
        1. دقيق قانونياً؟
        2. يجيب على سؤال المستخدم؟
        3. هل يحتوي على هلوسة أو معلومات غير مؤكدة؟
        
        أعد الإجابة بصيغة JSON:
        {{
            "is_valid": true/false,
            "critique": "ملاحظاتك",
            "improved_response": "الرد المحسن (اختياري)"
        }}
        """
        
        # Parse using Structured Output Utility
        parsed_model = parse_structured_output(reflection, ReflectionResponse)
        
        if parsed_model:
            result = parsed_model.model_dump()
            logger.info(f"✅ Reflexion result: Valid={result.get('is_valid')}")
            return result
        else:
            logger.warning(f"⚠️ Structured reflection parsing failed")
            return {"is_valid": True, "critique": "Failed to reflect"} # Fail open

    def run_loop(self, main_objective: str, context_data: Dict[str, Any]):
        """
        Main execution method (simplified for now)
        """
        # 1. Divide
        self.divide_task(main_objective)
        
        # 2. Evaluate
        assessment = self.evaluate_state(context_data)
        
        # 3. Plan & Act (Iterate through tasks)
        results = []
        for task in self.tasks:
            # Plan/Act would be here - for now we just return the tasks structure
            task.status = "completed"
            results.append(task)
            
        # 4. Reflect (Not implemented in this basic loop, used ad-hoc)
        
        # 5. Track
        return {"assessment": assessment, "tasks": [t.__dict__ for t in results]}
