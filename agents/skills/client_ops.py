from typing import Dict, Any
from .base import BaseSkill
from ..tools.db_tool_factory import DatabaseToolGenerator

class ClientOps(BaseSkill):
    name = "ClientOps"
    description = "إدارة العملاء (إضافة، بحث، تعديل، حذف) - Client Management"

    def get_tools(self) -> Dict[str, Any]:
        # We reuse the robust generation logic from the factory for now,
        # but scoped to only Client tables.
        # Ideally, we would move the _generate_X code here, but for Refactor Phase 1,
        # we will instantiate the factory and picky-back off it to ensure 100% compatibility.
        
        factory = DatabaseToolGenerator(lawyer_id=self.lawyer_id, current_user=self.current_user)
        all_tools = factory.generated_tools
        
        # Filter for Client tools
        client_tools = {
            k: v for k, v in all_tools.items() 
            if "client" in k and "case" not in k # Exclude client_cases relation tools if any
        }
        
        # Add 'safe_delete_client' if available
        if "safe_delete_client" in all_tools:
            client_tools["safe_delete_client"] = all_tools["safe_delete_client"]
            
        return client_tools
