from typing import Dict, Any
from .base import BaseSkill
from ..tools.db_tool_factory import DatabaseToolGenerator

class TaskOps(BaseSkill):
    name = "TaskOps"
    description = "إدارة المهام الإدارية (تذكيرات، مهام مكتبية) - Task Management"

    def get_tools(self) -> Dict[str, Any]:
        factory = DatabaseToolGenerator(lawyer_id=self.lawyer_id, current_user=self.current_user)
        all_tools = factory.generated_tools
        
        task_tools = {
            k: v for k, v in all_tools.items() 
            if "task" in k or "reminder" in k or "todo" in k
        }
        
        return task_tools
