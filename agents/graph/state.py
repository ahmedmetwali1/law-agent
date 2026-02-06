from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    Global State for the Legal AI Graph.
    Tracks conversation history, planning, and execution results.
    """
    # --- Input & History ---
    input: str
    chat_history: Annotated[List[BaseMessage], operator.add]
    
    # --- Context & Config ---
    user_id: str
    lawyer_id: str
    session_id: str
    context: Dict[str, Any]  # User details, Case details, Current Time
    
    # --- Planning & Reasoning ---
    intent: Optional[str]        # Classified intent (Greeting, Admin, Legal)
    plan: Optional[Any]          # Structured Plan (Dict) or List[str]
    complexity_score: Optional[str] # 'low', 'medium', 'high', 'critical'
    current_step: int            # Index of current step
    
    # --- Execution Data ---
    case_state: Optional[Dict[str, Any]] # Structured collected case data (The "Clean Facts")
    research_results: List[Dict[str, Any]] # Collected legal sources/facts
    draft: Optional[str]         # Generated content draft
    critique: Optional[str]      # Reviewer feedback
    council_opinions: Optional[Dict[str, str]] # Opinions from the 4 consultants
    
    # --- Orchestration (Judicial Control) ---
    next_agent: Optional[str]    # Judge decides: 'admin_ops', 'council', 'user'
    conversation_stage: Optional[str] # 'GATHERING', 'DELIBERATING', 'VERDICT'
    judge_directives: Optional[List[str]] # Instructions from Judge to Council
    
    # --- Final Output ---
    final_response: Optional[str] # The answer to stream back
