from typing import List, Dict, Optional, Any
from agents.config.database import db
import logging
import json

logger = logging.getLogger(__name__)

class DeliberationService:
    """
    Manages the 'Blackboard' persistence for the Legal Cognitive Engine.
    Handles storing and retrieving agent thoughts and opinions.
    """
    
    @staticmethod
    def post_opinion(
        session_id: str,
        round_number: int,
        agent_role: str,
        internal_monologue: str,
        public_opinion: str,
        cited_evidence: List[Dict[str, Any]],
        step_type: str = "opinion",
        reasoning_chain: Dict[str, Any] = {}
    ) -> bool:
        """
        Writes an agent's contribution to the blackboard.
        """
        try:
            data = {
                "session_id": session_id,
                "round_number": round_number,
                "agent_role": agent_role,
                "internal_monologue": internal_monologue,
                "public_opinion": public_opinion,
                "cited_evidence": cited_evidence,
                "step_type": step_type,
                "reasoning_chain": reasoning_chain
            }
            
            res = db.client.from_("agent_deliberations").insert(data).execute()
            if res.data:
                logger.info(f"✅ Posted opinion for {agent_role} (Round {round_number})")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to post opinion for {agent_role}: {e}")
            return False

    @staticmethod
    def fetch_round(session_id: str, round_number: int) -> List[Dict]:
        """
        Retrieves all opinions for a specific round.
        Used by agents in subsequent rounds to challenge peers.
        """
        try:
            res = db.client.from_("agent_deliberations")\
                .select("*")\
                .eq("session_id", session_id)\
                .eq("round_number", round_number)\
                .execute()
            
            return res.data if res.data else []
            
        except Exception as e:
            logger.error(f"Failed to fetch round {round_number}: {e}")
            return []

    @staticmethod
    def get_deliberation_history(session_id: str) -> str:
        """
        Formats the full history for the Judge or final report.
        Strictly formats 'Public Opinion' only, keeping monologues private.
        """
        try:
            # Fetch all rounds ordered
            res = db.client.from_("agent_deliberations")\
                .select("round_number, agent_role, public_opinion, cited_evidence")\
                .eq("session_id", session_id)\
                .order("round_number")\
                .execute()
            
            if not res.data:
                return "No deliberation history found."
                
            history_text = ""
            current_round = 0
            
            for item in res.data:
                rnd = item['round_number']
                if rnd != current_round:
                    history_text += f"\n\n--- Round {rnd} ---\n"
                    current_round = rnd
                
                history_text += f"\n📢 {item['agent_role'].upper()}:\n{item['public_opinion']}\n"
                
                # Format evidence compactly
                if item.get('cited_evidence'):
                    evidence_list = [f"Ref: {ev.get('ref', 'N/A')}" for ev in item['cited_evidence']]
                    history_text += f"   🔍 Evidence: {', '.join(evidence_list)}\n"
            
            return history_text
            
        except Exception as e:
            logger.error(f"Failed to format history: {e}")
            return "Error retrieving history."
