from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    tool_name: str = Field(description="The name of the tool to call")
    arguments: dict = Field(description="The arguments for the tool")

class JudgeDecision(BaseModel):
    """
    Structured Output for the Chief Justice Node.
    Decides the Intent, Routing, and potential Tool Calls.
    """
    intent: Literal["ADMIN_ACTION", "ADMIN_QUERY", "LEGAL_TASK", "LEGAL_SIMPLE", "LEGAL_COMPLEX", "REVISION", "GREETING", "CLARIFICATION_NEEDED", "REPORTING_BACK", "FINAL_DELIVERY", "CHIT_CHAT"] = Field(
        description="The classification of the user's request."
    )
    next_agent: Literal["admin_ops", "council", "user", "fast_track", "judge", "deep_research", "end"] = Field(
        description="The next agent to route to. 'deep_research' for investigator/researcher."
    )
    complexity: Literal["low", "medium", "high"] = Field(
        description="Estimated complexity of the task."
    )
    reasoning: str = Field(
        description="Brief explanation of why this decision was made."
    )
    plan_description: str = Field(
        description="A one-sentence plan for the next agent."
    )
    final_response: str = Field(
        description="A diplomatic, polite response to the user (e.g., 'Understood, I am checking the database...'). In Arabic."
    )
    tool_calls: Optional[List[ToolCall]] = Field(
        default=[],
        description="Optional list of tools to call directly (if Judge acts as Coordinator)."
    )
