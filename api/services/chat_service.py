import logging
import re
import uuid
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from fastapi import HTTPException

from agents.core.graph_agent import create_graph_agent
import requests
from api.schemas import ChatResponse, ChatSession, ChatMessage, ChatSessionCreate
from api.database import get_supabase_client

logger = logging.getLogger(__name__)

# --- Helper: JSON Datetime Encoder ---
def datetime_encoder(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class ChatService:
    """
    Stateless Service handling Chat via LangGraph + Supabase Persistence.
    Secured against IDOR and Data Inconsistencies.
    """

    def _get_db(self):
        return get_supabase_client()

    def _map_db_row_to_langchain_message(self, row: Dict[str, Any]) -> BaseMessage:
        """Map a Supabase DB row to a LangChain BaseMessage."""
        role = row.get("role")
        content = row.get("content") or ""
        metadata = row.get("metadata") or {}

        if role == "user":
            return HumanMessage(content=content)
        elif role == "assistant":
            tool_calls = metadata.get("tool_calls", [])
            return AIMessage(content=content, tool_calls=tool_calls)
        elif role == "tool":
            tool_call_id = metadata.get("tool_call_id") or "unknown_call_id"
            return ToolMessage(content=content, tool_call_id=tool_call_id)
        else:
            return HumanMessage(content=content)

    async def fetch_session_history(self, session_id: str, limit: int = 30) -> List[BaseMessage]:
        """Hydrate LangChain History from SQL Table."""
        try:
            db = self._get_db()
            response = db.table("ai_chat_messages") \
                .select("*") \
                .eq("session_id", session_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            rows = sorted(response.data, key=lambda x: x['created_at'])
            return [self._map_db_row_to_langchain_message(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Failed to fetch session history: {e}")
            return []
    
    async def _verify_ownership(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Verify session ownership."""
        try:
            db = self._get_db()
            response = db.table("ai_chat_sessions") \
                .select("*") \
                .eq("id", session_id) \
                .eq("lawyer_id", user_id) \
                .single() \
                .execute()
            
            if not response.data:
                raise HTTPException(status_code=403, detail="Unauthorized access to this session")
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying session ownership: {e}")
            raise HTTPException(status_code=500, detail="Internal Service Error")
    
    async def _enrich_full_user_context(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch full user profile including Country Name and Role Name (Arabic).
        Used for injecting rich context into Agent Prompts.
        """
        lawyer_id = user_context.get("id")
        if not lawyer_id:
            return user_context
        
        # Strategy: Anti-Fragile Fetching
        # 1. Try fetching User first (Critical)
        try:
            db = self._get_db()
            response = db.table("users").select("*").eq("id", lawyer_id).single().execute()
            
            if response.data:
                data = response.data
                user_context["full_name"] = data.get("full_name")
                user_context["email"] = data.get("email")
                
                # 2. Try fetching Country (Bonus) - Separate query to avoid 400 if relation broken
                if data.get("country_id"):
                    try:
                        # 🛑 SAFETY: Use select("*") to avoid "column does not exist" errors if schema drifts
                        c_res = db.table("countries").select("*").eq("id", data["country_id"]).single().execute()
                        if c_res.data:
                            user_context["country_name"] = c_res.data.get("name_en")
                            user_context["country_name_ar"] = c_res.data.get("name_ar")
                    except Exception as ce:
                        logger.warning(f"Feature degradation: Could not fetch country details: {ce}")

                # 3. Try fetching Role (Bonus)
                if data.get("role_id"):
                    try:
                        # 🛑 SAFETY: Use select("*") for robustness
                        r_res = db.table("roles").select("*").eq("id", data["role_id"]).single().execute()
                        if r_res.data:
                            user_context["role_name"] = r_res.data.get("name")
                            user_context["role_name_ar"] = r_res.data.get("name_ar")
                    except Exception as re:
                        logger.warning(f"Feature degradation: Could not fetch role details: {re}")

                logger.info(f"✅ Enriched full user context: {user_context.get('full_name')} ({user_context.get('role_name_ar')})")
        except Exception as e:
            logger.error(f"❌ Failed to fetch user profile for {lawyer_id}: {e}")
        except Exception as e:
            logger.warning(f"Failed to fetch full context for lawyer {lawyer_id}: {e}")
        
        return user_context

    async def process_message(
        self, 
        session_id: str, 
        message_text: str, 
        user_context: Dict[str, Any], 
        generate_title: bool = False
    ) -> ChatResponse:
        """
        Process message via Recovery Queue (ARQ).
        1. Enqueue Job to Redis.
        2. Wait for Result (Sync Façade).
        3. Return Result.
        """
        from api.queue.config import redis_settings, QUEUE_NAME
        from arq import create_pool
        from arq.connections import RedisSettings
        
        # Create ephemeral pool (in production, use a global pool from app.state)
        # For now, creating per request is safe for low load but not optimal.
        # We will assume global pool 'app.state.arq_pool' is available or create one.
        # Let's try to get it from a global variable if we set it in main.py, 
        # but for safety here we create one or use a singleton helper.
        
        # Quick singleton pattern for this file scope could be better, but let's instantiate.
        redis = RedisSettings(
            host=redis_settings.host,
            port=redis_settings.port,
            database=redis_settings.database
        )
        pool = await create_pool(redis)
        
        try:
            # Enqueue
            job = await pool.enqueue_job(
                "run_agent_task",
                session_id=session_id,
                message_text=message_text,
                user_context=user_context,
                generate_title=generate_title,
                _queue_name=QUEUE_NAME
            )
            
            if not job:
                raise Exception("Failed to enqueue job")
                
            # Wait for result (Simulating Sync API for Frontend)
            # Timeout 120s (Legal reasoning takes time)
            # poll_delay 0.5s
            result_dict = await job.result(timeout=120, poll_delay=0.5)
            
            return ChatResponse(**result_dict)
            
        finally:
            await pool.close()

    async def process_message_internal(
        self,
        session_id: str,
        message_text: str,
        user_context: Dict[str, Any],
        generate_title: bool = False
    ) -> ChatResponse:
        """
        The ACTUAL logic (Executed by Worker).
        """
        user_context = user_context or {}
        lawyer_id = user_context.get("id")
        lawyer_name = user_context.get("full_name", "User")
        
        if not lawyer_id:
             raise Exception("User Identity Missing")

        # 1. Security Check
        await self._verify_ownership(session_id, lawyer_id)
        db = self._get_db()
        
        # 🆕 Enrich user_context with country_id
        user_context = await self._enrich_full_user_context(user_context)
        
        # 2. Save User Message
        db.table("ai_chat_messages").insert({
            "session_id": session_id,
            "role": "user",
            "content": message_text
        }).execute()

        # 3. Initialize Graph
        graph = create_graph_agent(
            lawyer_id=lawyer_id,
            lawyer_name=lawyer_name,
            current_user=user_context,
            session_id=session_id
        )
        config = {"configurable": {"thread_id": session_id}}
        
        # 4. Prepare State
        history = await self.fetch_session_history(session_id, limit=20)
        
        input_state = {
            "input": message_text,
            "chat_history": history,
            "user_id": lawyer_id,
            "lawyer_id": lawyer_id,
            "session_id": session_id,
            "context": {"user_context": user_context},
            "conversation_stage": "GATHERING" 
        }
        
        # 5. Execute Graph (Sync Invoke)
        # We use ainvoke for full execution
        final_state = await graph.ainvoke(input_state, config=config)
        
        # 6. Extract Result
        # The graph likely doesn't return the text directly in 'final_state' output keys heavily
        # We rely on what the last node produced or the 'final_response' key.
        # Based on report analysis: 'judge' node returns 'final_response'.
        
        ai_response_text = final_state.get("final_response", "عذراً، لم أتمكن من استخلاص الرد.")
        if isinstance(ai_response_text, dict):
             ai_response_text = ai_response_text.get("message") or str(ai_response_text)
             
        # 7. Save AI Message
        # (The graph MIGHT have saved it if using atomic memory? 
        # No, memory_manager saves intermediate steps. The final output needs saving?)
        # Let's save it to be sure.
        
        db.table("ai_chat_messages").insert({
            "session_id": session_id,
            "role": "assistant",
            "content": ai_response_text,
            "metadata": {"worker_processed": True}
        }).execute()
        
        # 8. Return ChatResponse
        return ChatResponse(
            session_id=session_id,
            message=ai_response_text,
            stage="completed",
            completed=True,
            case_data=final_state.get("case_state")
        ) 

    # --- THE NEW STREAMING LOGIC (Viva Protocol) ---
    async def stream_processing(
        self,
        session_id: str,
        message_text: str,
        user_context: Dict[str, Any],
        mode: str = "auto",
        context_summary: Optional[str] = None
    ):
        """
        Stream message response using Strict SSE (Server-Sent Events).
        Protocol: 'step_update' | 'reasoning_chunk' | 'token' | 'error' | 'done'
        """
        user_context = user_context or {}
        lawyer_id = user_context.get("id")
        lawyer_name = user_context.get("full_name", "User")
        
        if not lawyer_id:
            yield f"data: {json.dumps({'type': 'error', 'content': 'User Identity Missing'})}\n\n"
            return

        # 1. Security Check
        await self._verify_ownership(session_id, lawyer_id)
        db = self._get_db()
        
        # 🆕 Enrich user_context with country_id
        user_context = await self._enrich_full_user_context(user_context)
        
        # 2. Save User Message
        try:
            db.table("ai_chat_messages").insert({
                "session_id": session_id,
                "role": "user",
                "content": message_text
            }).execute()
            # Notify frontend that user message is confirmed saved
            yield f"data: {json.dumps({'type': 'user_message_saved', 'message': {'content': message_text, 'role': 'user'}})}\n\n"
        except Exception as e:
            logger.error(f"⚠️ Failed to save user message: {e}")

        # 3. Initialize Graph
        if mode == "n8n":
             yield f"data: {json.dumps({'type': 'error', 'content': 'N8N Mode not supported in Alive Stream'})}\n\n"
             return

        graph = create_graph_agent(
            lawyer_id=lawyer_id,
            lawyer_name=lawyer_name,
            current_user=user_context,
            session_id=session_id
        )
        
        config = {"configurable": {"thread_id": session_id}}
        
        # 4. Prepare State
        try:
            history = await self.fetch_session_history(session_id, limit=10)
        except Exception as e:
            logger.warning(f"Failed to fetch history: {e}")
            history = []

        input_state = {
            "input": message_text,
            "chat_history": history,
            "user_id": lawyer_id,
            "lawyer_id": lawyer_id,
            "session_id": session_id,
            "context": {"user_context": user_context, "summary": context_summary},
            "conversation_stage": "GATHERING" 
        }
        
            # 5. Execute Graph with Strict Event Routing
        ai_content = "" # Accumulator for final DB save
        council_log = [] # Capture Council Monologues for DB
        hcf_log = [] # Capture HCF Decisions for DB
        
        try:
            async for event in graph.astream_events(input_state, config=config, version="v1"):
                if not event or not isinstance(event, dict):
                    continue
                    
                kind = event.get("event")
                name = event.get("name", "")
                data = event.get("data", {})
                
                # --- DEBUG LOGGING ---
                if kind == "on_chain_end":
                    logger.info(f"🔍 Event: {kind} | Name: {name} | Keys: {list(data.keys()) if data else 'None'}")
                    if data and "output" in data:
                        output = data["output"]
                        if isinstance(output, dict):
                             logger.info(f"   -> Output Keys: {list(output.keys())}")
                             if "final_response" in output:
                                 logger.info(f"   -> FOUND FINAL RESPONSE (Length: {len(str(output['final_response']))})")
                # ---------------------

                # --- A. STAGE CHANGE & STEP UPDATES ---
                if kind == "on_chain_start":
                    if name == "judge":
                        yield f"data: {json.dumps({'type': 'step_update', 'payload': {'stage': 'GATHERING', 'message': 'Chief Justice is reviewing...'}})}\n\n"
                    elif name == "council":
                         yield f"data: {json.dumps({'type': 'step_update', 'payload': {'stage': 'DELIBERATING', 'message': 'Council is meeting...'}})}\n\n"
                    elif name == "deep_research":
                        yield f"data: {json.dumps({'type': 'step_update', 'payload': {'stage': 'INVESTIGATING', 'message': 'Scout is searching...'}})}\n\n"
                    elif name == "admin_ops" or name == "admin_distributor":
                        yield f"data: {json.dumps({'type': 'step_update', 'payload': {'stage': 'EXECUTING', 'message': 'Office Manager is working...'}})}\n\n"

                # --- B. NODE COMPLETION (Unified Block) ---
                elif kind == "on_chain_end":
                    event_data = event.get("data")
                    
                    # 🛡️ Safety: Ensure event_data is a dictionary
                    if event_data is None or not isinstance(event_data, dict):
                        continue

                    output = event_data.get("output")
                    
                    if output and isinstance(output, dict):
                        
                        # 1. COUNCIL THOUGHTS (Reasoning)
                        if "council_opinions" in output:
                            opinions = output["council_opinions"]
                            if opinions and isinstance(opinions, dict):
                                for agent, text in opinions.items():
                                    # CAPTURE FOR DB
                                    council_log.append({"agent": agent, "content": text, "timestamp": datetime.now().isoformat()})
                                    yield f"data: {json.dumps({'type': 'reasoning_chunk', 'content': f'[{agent.upper()}]: {text}\n'})}\n\n"

                        # 2. JUDGE (The Voice)
                        if name == "judge":
                            # Extract PUBLIC content
                            final_res = output.get("final_response")
                            
                            # Extract PRIVATE reasoning
                            reasoning = output.get("reasoning") or output.get("internal_log")
                            if reasoning:
                                yield f"data: {json.dumps({'type': 'reasoning_chunk', 'content': f'>> {reasoning}\n'})}\n\n"

                            if final_res:
                                if not isinstance(final_res, str):
                                    final_res = str(final_res)
                                
                                logger.info(f"⚖️ Yielding Final Response: {final_res[:50]}...")
                                ai_content = final_res
                                yield f"data: {json.dumps({'type': 'token', 'content': final_res})}\n\n"

                        # 3. ADMIN (The Action)
                        elif name == "admin_ops":
                            final_res = output.get("final_response")
                            if final_res:
                                if isinstance(final_res, dict):
                                    final_res = final_res.get("message") or str(final_res)
                                
                                logger.info(f"⚡ Admin Finished: {final_res[:50]}...")
                                ai_content = final_res
                                logger.info(f"⚡ Admin Finished: {final_res[:50]}...")
                                ai_content = final_res
                                yield f"data: {json.dumps({'type': 'token', 'content': final_res})}\n\n"

                        # 4. DEEP RESEARCH (The Scout Speaking Directly)
                        elif name == "deep_research":
                            # Stream HCF Verification Data First
                            hcf_details = output.get("hcf_details")
                            if hcf_details and isinstance(hcf_details, dict):
                                # CAPTURE FOR DB
                                hcf_log.append(hcf_details)
                                yield f"data: {json.dumps({'type': 'hcf_decision', 'payload': hcf_details})}\n\n"

                            final_res = output.get("final_response")
                            if final_res:
                                if isinstance(final_res, dict):
                                    final_res = final_res.get("message") or str(final_res)
                                
                                logger.info(f"📚 Researcher Speaking: {final_res[:50]}...")
                                ai_content = final_res
                                yield f"data: {json.dumps({'type': 'token', 'content': final_res})}\n\n"

                        # 5. FAST TRACK (The Express Lane)
                        elif name == "fast_track":
                             final_res = output.get("final_response")
                             if final_res:
                                 logger.info(f"🚀 Yielding Fast Track Response: {final_res[:50]}...")
                                 ai_content = final_res
                                 yield f"data: {json.dumps({'type': 'token', 'content': final_res})}\n\n"

                # --- C. STREAMING TOKENS (Native LLM) ---
                elif kind == "on_chat_model_stream":
                    pass

            # 6. Finalization
            if not ai_content:
                # Fallback if graph ended without speaking (rare)
                ai_content = "تمت العملية."
                yield f"data: {json.dumps({'type': 'token', 'content': ai_content})}\n\n"

            # Save to DB
            try:
                db.table("ai_chat_messages").insert({
                    "session_id": session_id,
                    "role": "assistant",
                    "content": ai_content,
                    "metadata": {
                        "streamed": True, 
                        "protocol": "viva_v1",
                        "council_log": council_log,
                        "hcf_log": hcf_log
                    }
                }).execute()
                yield f"data: {json.dumps({'type': 'ai_message_saved', 'message': {'content': ai_content}})}\n\n"
            except Exception as e:
                logger.error(f"Failed to save AI message: {e}")

            # End Stream
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"❌ Graph Streaming Error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': 'System Error: ' + str(e)})}\n\n"

chat_service = ChatService()