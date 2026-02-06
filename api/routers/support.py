from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from api.auth_middleware import get_current_user_id, get_current_manager
from agents.config.settings import settings
from supabase import create_client, Client

router = APIRouter()

# Supabase Client
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)

# --- Pydantic Models ---
class TicketCreate(BaseModel):
    subject: str
    description: str
    priority: str = "normal"  # low, normal, high, urgent

class MessageCreate(BaseModel):
    message: str
    attachments: List[str] = []

class TicketResponse(BaseModel):
    id: str
    subject: str
    status: str
    priority: str
    created_at: str
    updated_at: str
    last_message: Optional[str] = None
    users: Optional[dict] = None

class MessageResponse(BaseModel):
    id: str
    sender_id: str
    message: str
    is_staff: bool
    attachments: List[str]
    created_at: str

class TicketDetailResponse(TicketResponse):
    messages: List[MessageResponse]

from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
import shutil
import uuid
import os

# Ensure upload directory exists
UPLOAD_DIR = "uploads/support"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ... (rest of imports)

# --- Endpoints ---

@router.post("/upload")
async def upload_attachment(file: UploadFile = File(...)):
    """Upload an attachment for a ticket"""
    try:
        file_ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"url": f"/uploads/support/{filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=TicketResponse)
async def create_ticket(
    ticket: TicketCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new support ticket"""
    try:
        # Create Ticket
        ticket_data = {
            "user_id": user_id,
            "subject": ticket.subject,
            "description": ticket.description,
            "priority": ticket.priority,
            "status": "open"
        }
        res = supabase.table("support_tickets").insert(ticket_data).execute()
        new_ticket = res.data[0]

        # Create Initial Message from Description
        message_data = {
            "ticket_id": new_ticket["id"],
            "sender_id": user_id,
            "message": ticket.description,
            "is_staff": False
        }
        supabase.table("ticket_messages").insert(message_data).execute()

        # TODO: Notify Admin (email or system notification)

        return new_ticket
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[TicketResponse])
async def list_tickets(user_id: str = Depends(get_current_user_id)):
    """List all tickets for the user"""
    try:
        # Get tickets sorted by updated_at
        res = supabase.table("support_tickets")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("updated_at", desc=True)\
            .execute()
        
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket_details(
    ticket_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get ticket details and messages"""
    try:
        # Get ticket to verify ownership
        ticket_res = supabase.table("support_tickets")\
            .select("*")\
            .eq("id", ticket_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        if not ticket_res.data:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Get messages
        messages_res = supabase.table("ticket_messages")\
            .select("*")\
            .eq("ticket_id", ticket_id)\
            .order("created_at")\
            .execute()

        ticket = ticket_res.data
        ticket["messages"] = messages_res.data
        
        return ticket
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{ticket_id}/messages", response_model=MessageResponse)
async def send_message(
    ticket_id: str,
    message: MessageCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Reply to a ticket"""
    try:
        # Verify ticket ownership
        ticket_res = supabase.table("support_tickets")\
            .select("id")\
            .eq("id", ticket_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
            
        if not ticket_res.data:
             raise HTTPException(status_code=404, detail="Ticket not found")

        # Create Message
        msg_data = {
            "ticket_id": ticket_id,
            "sender_id": user_id,
            "message": message.message,
            "attachments": message.attachments,
            "is_staff": False
        }
        res = supabase.table("ticket_messages").insert(msg_data).execute()
        new_msg = res.data[0]

        # Update Ticket Timestamp and Status if needed
        supabase.table("support_tickets")\
            .update({"updated_at": "now()", "status": "open"})\
            .eq("id", ticket_id)\
            .execute()

        return new_msg
    except HTTPException:
        return new_msg
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/tickets/{ticket_id}", response_model=TicketDetailResponse)
async def admin_get_ticket_details(
    ticket_id: str,
    manager: dict = Depends(get_current_manager)
):
    """Admin: Get ticket details and messages"""
    try:
        # Get ticket simple
        ticket_res = supabase.table("support_tickets")\
            .select("*")\
            .eq("id", ticket_id)\
            .single()\
            .execute()
        
        if not ticket_res.data:
            raise HTTPException(status_code=404, detail="Ticket not found")

        ticket = ticket_res.data

        # Get user info manually
        user_res = supabase.table("users").select("full_name, email").eq("id", ticket['user_id']).single().execute()
        if user_res.data:
             ticket['users'] = user_res.data
        else:
             ticket['users'] = {'full_name': 'Unknown', 'email': ''}

        # Get messages
        messages_res = supabase.table("ticket_messages")\
            .select("*")\
            .eq("ticket_id", ticket_id)\
            .order("created_at")\
            .execute()

        ticket["messages"] = messages_res.data
        
        return ticket
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Admin Endpoints ---

@router.get("/admin/tickets", response_model=List[TicketResponse])
async def admin_list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    manager: dict = Depends(get_current_manager)
):
    """Admin: List all tickets"""
    try:
        query = supabase.table("support_tickets").select("*")
        
        if status and status != 'all':
            query = query.eq("status", status)
        if priority and priority != 'all':
            query = query.eq("priority", priority)
            
        res = query.order("updated_at", desc=True).execute()
        
        # Manually fetch user details for each ticket (simple N+1 for now or just return without user name to fix crash)
        # To fix the immediate crash, let's return data. 
        # Ideally we fetch user names. 
        # Let's try to get user info from 'users' table if possible.
        tickets = res.data
        if tickets:
            user_ids = list(set([t['user_id'] for t in tickets]))
            users_res = supabase.table("users").select("id, full_name, email").in_("id", user_ids).execute()
            users_map = {u['id']: u for u in users_res.data}
            
            for t in tickets:
                if t['user_id'] in users_map:
                    t['users'] = users_map[t['user_id']]
                else:
                    t['users'] = {'full_name': 'Unknown', 'email': ''}
                    
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/admin/tickets/{ticket_id}/status")
async def admin_update_ticket_status(
    ticket_id: str,
    status: str = Body(..., embed=True),
    manager: dict = Depends(get_current_manager)
):
    """Admin: Update ticket status"""
    try:
        res = supabase.table("support_tickets")\
            .update({"status": status, "updated_at": "now()"})\
            .eq("id", ticket_id)\
            .execute()
            
        if not res.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
            
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/tickets/{ticket_id}/reply")
async def admin_reply_ticket(
    ticket_id: str,
    message: MessageCreate,
    manager: dict = Depends(get_current_manager)
):
    """Admin: Reply to a ticket"""
    try:
        # Create Message
        msg_data = {
            "ticket_id": ticket_id,
            "sender_id": manager['id'],
            "message": message.message,
            "attachments": message.attachments,
            "is_staff": True
        }
        res = supabase.table("ticket_messages").insert(msg_data).execute()
        new_msg = res.data[0]

        # Update Ticket Status to 'resolved' or keep 'open' (maybe 'pending' on user?)
        # For now, let's keep it 'open' or set to 'resolved' if admin chooses (separate call).
        # Usually admin reply might imply 'pending' user response.
        supabase.table("support_tickets")\
            .update({"updated_at": "now()", "status": "resolved"})\
            .eq("id", ticket_id)\
            .execute()

        return new_msg
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
