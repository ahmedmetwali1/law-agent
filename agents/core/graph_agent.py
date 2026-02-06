from typing import Dict, Any, Optional
from ..graph.graph import define_graph

def create_graph_agent(
    lawyer_id: str,
    lawyer_name: str,
    current_user: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    case_summary: Optional[str] = None
):
    """
    Factory to create the LangGraph compiled runnable.
    """
    return define_graph()
