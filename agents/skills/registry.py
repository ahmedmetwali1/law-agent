from typing import Dict, Any, List
from .base import BaseSkill
from .client_ops import ClientOps
from .case_ops import CaseOps
from .finance_ops import FinanceOps
from .task_ops import TaskOps

class SkillRegistry:
    """
    Central registry for all available skills.
    Allows dynamic loading based on user context.
    """
    
    def __init__(self, lawyer_id: str, current_user: Dict[str, Any]):
        self.skills: List[BaseSkill] = [
            ClientOps(lawyer_id, current_user),
            CaseOps(lawyer_id, current_user),
            FinanceOps(lawyer_id, current_user),
            TaskOps(lawyer_id, current_user)
        ]
        
    def get_all_skill_definitions(self) -> str:
        """Returns a string list of available skills for the prompt."""
        return "\n".join([f"- {s.get_definition()}" for s in self.skills])

    def get_all_tools(self) -> Dict[str, Any]:
        """
        Aggregates ALL tools from ALL skills.
        Used for the 'Execute' node to have access to everything.
        """
        all_tools = {}
        for skill in self.skills:
            all_tools.update(skill.get_tools())
        return all_tools
    
    def get_skill(self, skill_name: str) -> BaseSkill:
        for s in self.skills:
            if s.name.lower() == skill_name.lower():
                return s
        return None
