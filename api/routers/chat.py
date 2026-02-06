"""
Chat API Router
Secure backend access for AI chat sessions and messages
Replaces direct Supabase access from Frontend
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import uuid
import requests

from api.auth_middleware import get_current_user
from api.database import get_supabase_client
from agents.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# --- Models ---

class ChatSessionCreate(BaseModel):
    title: str = "محادثة جديدة"
    session_type: str = "main"

from typing import Dict, Any, List, Optional, Literal

class ChatMessageCreate(BaseModel):
    session_id: Optional[str] = None
    message: str  # Renamed from content to match Frontend ChatRequest
    generate_title: bool = False
    mode: Literal["auto", "admin_assistant", "legal_researcher", "n8n"] = "auto"
    context_summary: Optional[str] = None  # ✅ Kilo Evolution: Context Injection

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None

# --- Endpoints ---

@router.get("/search")
async def search_chats(
    q: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search sessions (title) and messages (content).
    Returns { sessions: [], messages: [] }
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = current_user['id']
        
        # 1. Search Sessions
        sessions_res = supabase.table('ai_chat_sessions')\
            .select('*')\
            .eq('lawyer_id', lawyer_id)\
            .ilike('title', f'%{q}%')\
            .limit(5)\
            .execute()
            
        # 2. Search Messages (Join with sessions to get context if feasible, or just return raw)
        # Note: Supabase-py might not support complex joins easily in one go used this way,
        # so we fetch messages and maybe enrich them.
        messages_res = supabase.table('ai_chat_messages')\
            .select('*, ai_chat_sessions!inner(title, lawyer_id)')\
            .eq('ai_chat_sessions.lawyer_id', lawyer_id)\
            .ilike('content', f'%{q}%')\
            .limit(10)\
            .execute()
            
        return {
            "sessions": sessions_res.data,
            "messages": messages_res.data
        }
        
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        # Return empty on error to avoid breaking UI
        return {"sessions": [], "messages": []}

@router.get("/sessions")
async def get_sessions(
    session_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get all chat sessions for current user.
    Optional: Filter by session_type (e.g. 'sidebar', 'main')
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = current_user['id']
        
        query = supabase.table('ai_chat_sessions')\
            .select('*')\
            .eq('lawyer_id', lawyer_id)
            
        if session_type:
            query = query.eq('session_type', session_type)
            
        result = query\
            .order('last_message_at', desc=True)\
            .order('created_at', desc=True)\
            .execute()
            
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions")
async def create_session(
    session: ChatSessionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create new chat session"""
    try:
        supabase = get_supabase_client()
        lawyer_id = current_user['id']
        
        data = {
            'lawyer_id': lawyer_id,
            'title': session.title,
            'session_type': session.session_type,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_message_at': datetime.now().isoformat()
        }
        
        result = supabase.table('ai_chat_sessions')\
            .insert(data)\
            .execute()
            
        if not result.data:
            raise Exception("Failed to create session")
            
        return result.data[0]
        
    except Exception as e:
        logger.error(f"❌ Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{id_param}")
async def get_session_or_list(
    id_param: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any: # Returns List or Dict
    """
    Hybrid Endpoint to support Legacy Frontend (List by User ID) 
    AND Modern Frontend (Get Session by ID).
    """
    try:
        supabase = get_supabase_client()
        user_id = current_user['id']
        
        # 1. Compatibility Check: Is the param the User's ID? -> List Sessions
        if id_param == user_id:
            query = supabase.table('ai_chat_sessions')\
                .select('*')\
                .eq('lawyer_id', user_id)\
                .order('last_message_at', desc=True)\
                .execute()
            return query.data

        # 2. Otherwise assume it is a Session ID -> Get Session Details
        result = supabase.table('ai_chat_sessions')\
            .select('*')\
            .eq('id', id_param)\
            .eq('lawyer_id', user_id)\
            .execute()
            
        if not result.data:
            # Fallback: It might be a session ID needed by legacy "messages" route? 
            # No, that has its own route.
            raise HTTPException(status_code=404, detail="Session not found")
            
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch session/list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, bool]:
    """Delete chat session"""
    try:
        supabase = get_supabase_client()
        lawyer_id = current_user['id']
        
        # Verify ownership (RLS simulation)
        # Service Key bypasses RLS, so we must check manually
        check = supabase.table('ai_chat_sessions')\
            .select('id')\
            .eq('id', session_id)\
            .eq('lawyer_id', lawyer_id)\
            .execute()
            
        if not check.data:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
            
        result = supabase.table('ai_chat_sessions')\
            .delete()\
            .eq('id', session_id)\
            .execute()
            
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: str,
    update_data: ChatSessionUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update session details (e.g. title)"""
    try:
        supabase = get_supabase_client()
        lawyer_id = current_user['id']
        
        # Verify ownership
        check = supabase.table('ai_chat_sessions')\
            .select('*')\
            .eq('id', session_id)\
            .eq('lawyer_id', lawyer_id)\
            .execute()
            
        if not check.data:
            raise HTTPException(status_code=404, detail="Session not found")
            
        # Prepare update payload
        updates = {}
        if update_data.title is not None:
            updates['title'] = update_data.title
        if update_data.is_pinned is not None:
            updates['is_pinned'] = update_data.is_pinned
            
        updates['updated_at'] = datetime.now().isoformat()
        
        result = supabase.table('ai_chat_sessions')\
            .update(updates)\
            .eq('id', session_id)\
            .execute()
            
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get messages for a session"""
    try:
        supabase = get_supabase_client()
        lawyer_id = current_user['id']
        
        # Verify ownership
        check = supabase.table('ai_chat_sessions')\
            .select('id')\
            .eq('id', session_id)\
            .eq('lawyer_id', lawyer_id)\
            .execute()
            
        if not check.data:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
            
        result = supabase.table('ai_chat_messages')\
            .select('*')\
            .eq('session_id', session_id)\
            .order('created_at', desc=False)\
            .execute()
            
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send")
async def send_message(
    msg: ChatMessageCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Send message, save to DB, get AI response, save AI response.
    Replaces client-side chain of requests.
    """
    try:
        supabase = get_supabase_client()
        lawyer_id = current_user['id']
        session_id = msg.session_id
        
        if session_id:
            # 1. Verify session ownership
            check = supabase.table('ai_chat_sessions')\
                .select('*')\
                .eq('id', session_id)\
                .eq('lawyer_id', lawyer_id)\
                .execute()
                
            if not check.data:
                # Robustness: If session ID provided but not found (e.g. deleted or sync issue), 
                # auto-create it using the provided ID to keep frontend in sync.
                logger.warning(f"⚠️ Session {session_id} not found in DB. Auto-creating...")
                session = None # Fallthrough to creation logic
            else:
                session = check.data[0]
        else:
            session = None
            
        if not session:
            # Lazy Creation / Recreation
            title = " ".join(msg.message.split()[:5]) + ("..." if len(msg.message.split()) > 5 else "")
            
            # Use provided ID if valid, else gen new
            new_id = session_id if session_id else str(uuid.uuid4())
            
            new_session_data = {
                'id': new_id, # explicit ID
                'lawyer_id': lawyer_id,
                'title': title,
                'session_type': 'main',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'last_message_at': datetime.now().isoformat()
            }
            
            session_res = supabase.table('ai_chat_sessions').insert(new_session_data).execute()
            if not session_res.data:
                raise Exception("Failed to auto-create session")
            
            session = session_res.data[0]
            session_id = session['id']
            msg.generate_title = True
        

        # 2. Call AI Agent using ChatService (It will save the user message)
        from api.services.chat_service import chat_service
        
        # Initialize variables
        saved_user_msg = None # Will attempt to fetch from service response or query

        # Use the proper chat service instead of the old ai_helper logic
        from api.services.chat_service import chat_service
        
        # Initialize variables
        ai_content = ""
        suggested_title = None
        ai_msg = None
        
        try:
            # Process the message through the chat service
            ai_result = await chat_service.process_message(
                session_id=session_id,
                message_text=msg.message,
                user_context=current_user,
                generate_title=msg.generate_title,
                mode=msg.mode,
                context_summary=msg.context_summary
            )
            
            ai_content = ai_result.message
            suggested_title = ai_result.suggested_title if hasattr(ai_result, 'suggested_title') else None
            
            # Retrieve the user message that was saved by process_message
            saved_user_msg_res = supabase.table('ai_chat_messages')\
                .select('*')\
                .eq('session_id', session_id)\
                .eq('role', 'user')\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            saved_user_msg = saved_user_msg_res.data[0] if saved_user_msg_res.data else None

            # The AI message is already saved by chat_service, so we get it from the result
            ai_msg = ai_result.ai_message if hasattr(ai_result, 'ai_message') else None
            
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            # Fallback response
            ai_content = "عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى."
            
            # Save fallback AI message
            ai_msg_data = {
                'session_id': session_id,
                'role': 'assistant',
                'content': ai_content,
                'created_at': datetime.now().isoformat(),
                'metadata': {'error': True}
            }
            ai_res = supabase.table('ai_chat_messages').insert(ai_msg_data).execute()
            ai_msg = ai_res.data[0] if ai_res.data else None
            
            # Attempt to recover user message if it was saved before error
            if not saved_user_msg:
                 saved_user_msg_res = supabase.table('ai_chat_messages').select('*').eq('session_id', session_id).eq('role', 'user').order('created_at', desc=True).limit(1).execute()
                 saved_user_msg = saved_user_msg_res.data[0] if saved_user_msg_res.data else {'content': msg.message, 'role': 'user', 'id': 'temp-error'}
        
        # 4. Update session timestamp and title
        update_data = {
            'last_message_at': datetime.now().isoformat(),
            'message_count': (session.get('message_count', 0) or 0) + 2
        }
        
        if suggested_title:
            update_data['title'] = suggested_title
            
        supabase.table('ai_chat_sessions').update(update_data).eq('id', session_id).execute()
        
        # Return both messages
        return {
            "user_message": saved_user_msg,
            "ai_message": ai_msg,
            "suggested_title": suggested_title
        }

    except HTTPException:
        raise

@router.post("/stream")
async def stream_message(
    msg: ChatMessageCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Stream message response using SSE (Server-Sent Events).
    """
    from fastapi.responses import StreamingResponse
    from api.services.chat_service import chat_service
    
    # 1. Handle Session Creation if needed
    supabase = get_supabase_client()
    session_id = msg.session_id
    lawyer_id = current_user['id']
    
    if not session_id:
         # Auto-create session
         title = " ".join(msg.message.split()[:5]) + ("..." if len(msg.message.split()) > 5 else "")
         new_session_data = {
                'lawyer_id': lawyer_id,
                'title': title,
                'session_type': 'main',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'last_message_at': datetime.now().isoformat()
         }
         res = supabase.table('ai_chat_sessions').insert(new_session_data).execute()
         if res.data:
             session_id = res.data[0]['id']
    
    return StreamingResponse(
        chat_service.stream_processing(
            session_id=session_id,
            message_text=msg.message,
            user_context=current_user,
            mode=msg.mode,
            context_summary=msg.context_summary
        ),
        media_type="text/event-stream"
    )
