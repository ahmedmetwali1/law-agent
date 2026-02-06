from typing import Any, Dict, List, Optional
from uuid import UUID
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

class StatusCallbackHandler(BaseCallbackHandler):
    """
    Updates the 'current_action' field AND appends to 'execution_logs' 
    in Supabase ai_chat_sessions table to provide real-time status feedback.
    """
    
    def __init__(self, supabase_client, session_id: str):
        self.supabase = supabase_client
        self.session_id = session_id
        
    def _update_status(self, status: Optional[str], log_entry: Optional[Dict] = None):
        """Helper to write status and append log to DB"""
        try:
            update_data = {}
            
            # 1. Update Legacy Status
            if status is not None:
                update_data["current_action"] = status
            
            # 2. Append to Execution Logs (RPC would be better for atomicity, but simple fetch-update for now)
            # Actually, we can use a raw SQL query or just assume low contention.
            # Ideally, we should use a Postgres function `append_log`.
            # For now, we will just update `current_action` accurately. 
            # Appending to a JSON array via standard Update is risky without a specific RPC.
            
            # Let's try to fetch current logs first? No, too slow.
            # Let's just update `current_action` for the spinner, 
            # AND if we have a log_entry, we might need a custom RPC.
            # However, for this environment, let's stick to just updating `current_action` 
            # BUT we will assume the frontend polls `current_action`.
            
            # WAIT. The requirements said "step-by-step execution flow".
            # If we don't save the logs, the frontend can't show the checklist.
            # We MUST save the logs.
            
            if log_entry:
                # We need to use a stored procedure to append to JSONB to avoid race conditions?
                # Or just overwrite. Since this is single user per session usually, overwrite is "okay".
                
                # Fetch current logs
                # res = self.supabase.table("ai_chat_sessions").select("execution_logs").eq("id", self.session_id).single().execute()
                # logs = res.data.get("execution_logs") or []
                # logs.append(log_entry)
                # update_data["execution_logs"] = logs
                
                # OPTIMIZATION: We can't do a Read-Modify-Write safely in a callback.
                # Let's just update `current_action` for now, and maybe the Agent logic 
                # handles the "Plan" which is saved at the END.
                
                # RE-READING PLAN: "Append structured events to the session's execution log"
                # To do this efficiently without RPC:
                # We can't. But we can cheat: 
                # Let's simple write to a SEPARATE table `ai_execution_steps`? 
                # No, the plan said column.
                
                # Implementation: We will use a trusted RPC or just read-modify-write (accepting risk).
                pass
                
            # If we just update `current_action`, the "ThinkingPulse" component works.
            # To get the "Checklist", we need the history.
            
            # Let's try to implement a simple Read-Write. 
            if log_entry:
                 # Fetch
                 res = self.supabase.table("ai_chat_sessions").select("execution_logs").eq("id", self.session_id).execute()
                 if res.data:
                     logs = res.data[0].get("execution_logs") or []
                     logs.append(log_entry)
                     update_data["execution_logs"] = logs
            
            if update_data:
                self.supabase.table("ai_chat_sessions").update(update_data).eq("id", self.session_id).execute()
                
        except Exception as e:
            print(f"Failed to update status: {e}")

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""
        tool_name = serialized.get("name", "tool")
        
        # User-friendly mapping
        status_map = {
            "legal_search": "جاري البحث في المصادر القانونية...",
            "case_search": "البحث في ملفات القضايا...",
            "search_cases": "البحث في ملفات القضايا...",
            "create_client": "إضافة موكل جديد...",
            "create_case": "إنشاء ملف قضية...",
            "get_today_hearings": "جلب الجلسات...",
            "calculator": "إجراء حسابات...",
            "tavily_search_results_json": "البحث في الإنترنت..."
        }
        
        friendly_status = status_map.get(tool_name, f"استخدام الأداة: {tool_name}...")
        
        # Create Log Entry
        import time
        log_entry = {
            "id": f"step-{time.time()}",
            "status": "running",
            "message": friendly_status,
            "tool": tool_name,
            "timestamp": time.time()
        }
        
        self._update_status(friendly_status, log_entry)

    def on_chat_model_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when LLM finishes generation (Message Creation)."""
        try:
            # Extract the generated message
            # outputs is LLMResult. generations=[[ChatGeneration(message=...)]]
            generations = outputs.get('generations', [])
            if not generations:
                return
                
            first_generation = generations[0][0]
            message = first_generation.message
            
            # Prepare metadata
            metadata = {
                "source": "realtime_callback",
                "tool_calls": getattr(message, 'tool_calls', [])
            }
            
            # Insert into DB
            self.supabase.table("ai_chat_messages").insert({
                "session_id": self.session_id,
                "role": "assistant",
                "content": message.content or "", # Content might be empty if purely tool call (but we enforced narrative)
                "metadata": metadata
            }).execute()
            
        except Exception as e:
            print(f"Failed to save AIMessage in callback: {e}")

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Run when tool ends running."""
        # 1. Update Execution Log (Success)
        try:
             res = self.supabase.table("ai_chat_sessions").select("execution_logs").eq("id", self.session_id).execute()
             if res.data:
                 logs = res.data[0].get("execution_logs") or []
                 if logs and logs[-1]["status"] == "running":
                     logs[-1]["status"] = "success"
                     logs[-1]["message"] = logs[-1]["message"].replace("جاري", "تم").replace("...", "")
                     
                     self.supabase.table("ai_chat_sessions").update({
                         "execution_logs": logs,
                         "current_action": None 
                     }).eq("id", self.session_id).execute()
        except Exception as e:
            print(f"Error updating logs on tool end: {e}")

        # 2. Save Tool Message to DB (So it appears in history)
        try:
            tool_name = kwargs.get('name', 'tool')
            # Check if this tool output should be hidden or shown?
            # User said "Hide raw Data". But we need it in history for the Agent to see it next turn.
            # We save it, and Frontend Hides it.
            
            self.supabase.table("ai_chat_messages").insert({
                "session_id": self.session_id,
                "role": "tool",
                "content": str(output), # Ensure string
                "metadata": {
                    "tool_name": tool_name,
                    "hidden": False # Frontend decides rendering
                }
            }).execute()
        except Exception as e:
            print(f"Failed to save ToolMessage in callback: {e}")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when chain ends running."""
        self._update_status(None)

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> Any:
        """Run when chain errors."""
        self._update_status(None)
