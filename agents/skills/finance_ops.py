from typing import Dict, Any
from .base import BaseSkill
from ..tools.db_tool_factory import DatabaseToolGenerator

class FinanceOps(BaseSkill):
    name = "FinanceOps"
    description = "الإدارة المالية (مدفوعات، فواتير، عقود) - Financial Management"

    def get_tools(self) -> Dict[str, Any]:
        factory = DatabaseToolGenerator(lawyer_id=self.lawyer_id, current_user=self.current_user)
        all_tools = factory.generated_tools
        
        finance_tools = {
            k: v for k, v in all_tools.items() 
            if "payment" in k or "invoice" in k or "contract" in k or "deal" in k
        }
        
        return finance_tools
