from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel

class BaseSkill(ABC):
    """
    Abstract Base Class for Legal Skills.
    Follows the 'Progressive Disclosure' pattern.
    """
    
    name: str = "base_skill"
    description: str = "Base skill description"
    
    def __init__(self, lawyer_id: Optional[str] = None, current_user: Optional[Dict[str, Any]] = None):
        self.lawyer_id = lawyer_id
        self.current_user = current_user

    @abstractmethod
    def get_tools(self) -> Dict[str, Any]:
        """
        Returns a dictionary of tool functions provided by this skill.
        Format: {"tool_name": tool_function}
        """
        pass

    def get_definition(self) -> str:
        """
        Returns a concise string definition for the System Prompt.
        Example: "ClientOps: Manage clients (add, update, query)."
        """
        return f"{self.name}: {self.description}"
