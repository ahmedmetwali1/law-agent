from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class AdminToolCall(BaseModel):
    """Represents a single tool execution request."""
    name: str = Field(..., description="The precise name of the tool to call (e.g., 'insert_clients', 'query_cases').")
    args: Dict[str, Any] = Field(..., description="The arguments to pass to the tool. Must match the tool's schema.")
    reasoning: str = Field(..., description="Brief explaination of why this tool is needed.")

class AdminPlan(BaseModel):
    """The structured execution plan for the Admin Agent."""
    plan_overview: str = Field(..., description="A short summary of the overall strategy (in Arabic).")
    steps: List[AdminToolCall] = Field(default_factory=list, description="An ordered list of tool calls to execute.")
    clarification_needed: Optional[str] = Field(None, description="If the request is ambiguous, put your question here instead of tools.")

    def is_executable(self) -> bool:
        """Check if the plan has executable steps."""
        return len(self.steps) > 0

    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """Convert to basic list of dicts for the specialized executor."""
        return [
            {
                "name": step.name,
                "args": step.args,
                "id": f"call_{i}",
                "type": "tool_call"
            } 
            for i, step in enumerate(self.steps)
        ]
