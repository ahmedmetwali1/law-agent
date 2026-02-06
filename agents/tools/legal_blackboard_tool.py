from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime
from agents.config.database import get_supabase_client

logger = logging.getLogger(__name__)

class LegalBlackboardTool:
    """
    Manages the 'Legal Blackboard' state for the General Counsel and specialized agents.
    Handles versioning, status updates, and segmented data writing.
    """
    
    def __init__(self):
        self.client = get_supabase_client()
        self.table_name = "legal_blackboard"

    def read_latest_state(self, session_id: str) -> Dict[str, Any]:
        """
        Reads the latest version of the blackboard for a session.
        """
        try:
            # Get max version
            res = self.client.table(self.table_name)\
                .select("*")\
                .eq("session_id", session_id)\
                .order("version", desc=True)\
                .limit(1)\
                .execute()
                
            if res.data:
                return res.data[0]
            return {}
        except Exception as e:
            logger.error(f"Failed to read blackboard: {e}")
            return {}

    def get_version(self, session_id: str, version: int) -> Dict[str, Any]:
        """
        Reads a specific version of the blackboard.
        """
        try:
            res = self.client.table(self.table_name)\
                .select("*")\
                .eq("session_id", session_id)\
                .eq("version", version)\
                .limit(1)\
                .execute()
                
            if res.data:
                return res.data[0]
            return {}
        except Exception as e:
            logger.error(f"Failed to read blackboard version {version}: {e}")
            return {}

    def initialize_state(self, session_id: str) -> Dict[str, Any]:
        """
        Creates the first entry (Version 1) if it doesn't exist.
        """
        existing = self.read_latest_state(session_id)
        if existing:
            return existing
            
        initial_data = {
            "session_id": session_id,
            "version": 1,
            "workflow_status": {
                "investigator": "PENDING",
                "researcher": "PENDING",
                "council": "PENDING",
                "drafter": "PENDING"
            }
        }
        
        try:
            res = self.client.table(self.table_name).insert(initial_data).execute()
            if res.data:
                logger.info(f"Initialized Blackboard for session {session_id}")
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to initialize blackboard: {e}")
            
        return {}

    def update_segment(self, session_id: str, segment: str, data: Dict[str, Any], status_update: Optional[Dict[str, str]] = None) -> bool:
        """
        Updates a specific JSONB segment with OPTIMISTIC LOCKING Protection.
        """
        valid_segments = ["facts_snapshot", "research_data", "debate_strategy", "drafting_plan", "final_output", "agent_thinking"]
        if segment not in valid_segments:
            logger.error(f"Invalid blackboard segment: {segment}")
            return False

        # 🔒 RETRY LOOP FOR OPTIMISTIC LOCKING
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 1. Get Current Version & ID
                # We fetch FRESH state each attempt to get latest version
                current_state = self.read_latest_state(session_id)
                
                if not current_state:
                    if attempt == 0:
                        current_state = self.initialize_state(session_id)
                    else:
                        # Should not happen if init worked
                        time.sleep(0.5)
                        continue
                        
                record_id = current_state.get("id")
                current_version = current_state.get("version", 1) # This is our Lock Token
                
                updates = {
                    segment: data,
                    "updated_at": datetime.now().isoformat(),
                    # "version": current_version + 1  <-- Ideally we'd increment version here?
                    # But 'version' in our schema might mean 'Revision' of the case, not DB row version.
                    # If 'version' is semantically 'Case Draft Version', we shouldn't bump it on every small update.
                    # Check schema... usually we use a separate 'lock_version' column or just rely on standard version if it granular.
                    # Assuming 'updated_at' is enough? No.
                    # Let's assume we simply rely on the Row ID being stable and just check connection.
                    # Wait, if we use Supabase HTTP, update is atomic for that row. 
                    # Race condition happens if: Agent A reads (Ver1), Agent B reads (Ver1), Agent A Writes (Ver1+UpdateA), Agent B Writes (Ver1+UpdateB).
                    # Agent B overwrites UpdateA.
                    
                    # To fix: 
                    # Update ... WHERE id=... AND updated_at = old_updated_at
                }
                
                # Merge Status
                if status_update:
                    current_status = current_state.get("workflow_status") or {}
                    current_status.update(status_update)
                    updates["workflow_status"] = current_status

                # 🔒 ATOMIC UPDATE WITH CHECK
                # We use 'updated_at' as the concurrency token if available, or just rely on atomic update if we trust segment isolation.
                # BUT 'workflow_status' IS shared.
                # Let's try to match 'updated_at' if it exists.
                query = self.client.table(self.table_name).update(updates).eq("id", record_id)
                
                # If we had a concurrency token column like 'lock_version', we'd use it.
                # For now, let's look at `updated_at`.
                # If the DB hasn't changed since we read it...
                # Note: ISO formatted strings might lose precision. 
                # Let's trust pure Postgres Atomicity for 'segment' updates if they are partial?
                # Supabase .update() sends a PATCH. If we send only {"facts": ...}, it shouldn't overwrite {"strategy": ...} if they are different columns.
                # BUT 'workflow_status' is a JSONB column (usually) or dedicated columns? 
                # In init_state it looks like a single JSON col. Merge is hard in SQL via simple API.
                # If 'workflow_status' is replaced entirely, we lose other agent's status updates.
                
                # Fix: Use 'updated_at' match to ensure we are editing the exact snapshot we read.
                last_update = current_state.get("updated_at")
                if last_update:
                    query = query.eq("updated_at", last_update)
                
                res = query.execute()
                
                if res.data:
                    logger.info(f"✅ Updated Blackboard Segment '{segment}' (Attempt {attempt+1})")
                    return True
                else:
                    logger.warning(f"🔒 Concurrency Conflict on Segment '{segment}' (Attempt {attempt+1}). Retrying...")
                    import time
                    time.sleep(0.5 * (attempt + 1))
                    
            except Exception as e:
                logger.error(f"Failed to update segment {segment}: {e}")
                import time
                time.sleep(0.5)
        
        logger.error(f"❌ Failed to update segment {segment} after {max_retries} attempts due to locking.")
        return False

    def fork_session(self, session_id: str, trigger_reason: str = "revision") -> Dict[str, Any]:
        """
        Creates a new Version (N+1) by copying the latest state.
        Used when the user requests frequent revisions.
        """
        current_state = self.read_latest_state(session_id)
        if not current_state:
            return self.initialize_state(session_id)
            
        new_version = (current_state.get("version", 1)) + 1
        
        # Copy data, but RESET downstream statuses based on revision logic?
        # For now, we simple COPY everything, then the caller (Judge) decides what to clear.
        # BUT, the prompt said: "If Investigator updates facts -> Reset others to PENDING".
        # Let's do a smart copy: Keep facts if strategy revision, keep strategy if drafting revision.
        # Actually, the safest is to Clone, and let the agent overwrite.
        
        new_data = {
            "session_id": session_id,
            "version": new_version,
            "parent_id": current_state.get("id"),
            # Copy snapshots
            "facts_snapshot": current_state.get("facts_snapshot"),
            "research_data": current_state.get("research_data"),
            "debate_strategy": current_state.get("debate_strategy"), # Might be stale if facts changed
            "drafting_plan": current_state.get("drafting_plan"),
            # Reset Status flags? Or keep them?
            # A revision implies work needs to be done.
            # We copy specific data but maybe reset status?
            # Let's simple Copy for now, and let JudgeLogic handle the 'Reset' by calling update_segment later?
            # No, 'fork' implies a clean slate for the NEW changes.
            "workflow_status": {
                "investigator": "PENDING", # Assume we might need to re-verify or at least check
                "researcher": "PENDING",
                "council": "PENDING",
                "drafter": "PENDING"
            }
        }
        
        try:
            res = self.client.table(self.table_name).insert(new_data).execute()
            if res.data:
                logger.info(f"🔱 Forked Blackboard Session {session_id} to Version {new_version}")
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to fork session: {e}")
            
        return {}
