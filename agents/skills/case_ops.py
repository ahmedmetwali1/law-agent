from typing import Dict, Any
from .base import BaseSkill
from ..tools.db_tool_factory import DatabaseToolGenerator

class CaseOps(BaseSkill):
    name = "CaseOps"
    description = "إدارة القضايا والجلسات (إضافة، بحث، تعديل) - Case & Hearing Management"

    def get_tools(self) -> Dict[str, Any]:
        factory = DatabaseToolGenerator(lawyer_id=self.lawyer_id, current_user=self.current_user)
        all_tools = factory.generated_tools
        
        # Filter for Case and Hearing tools
        case_tools = {
            k: v for k, v in all_tools.items() 
            if "case" in k or "hearing" in k or "court" in k or "opponent" in k
        }
        
        return case_tools
