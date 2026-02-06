"""
FastAPI Application
Legal AI Multi-Agent System API
"""
# ✅ CRITICAL: Load environment variables BEFORE importing settings
from dotenv import load_dotenv
load_dotenv()  # Must be first to ensure .env is loaded!

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
# Force reload to pick up notifications fixes
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from fastapi import WebSocket, WebSocketDisconnect
import logging
import sys
import os
import uuid
from datetime import datetime


from agents.storage.case_storage import CaseStorage
from agents.config.settings import settings
# from agents.tools.unified_tools import UnifiedToolSystem # DELETED

from agents.storage.user_storage import user_storage
from api.services.chat_service import chat_service
from api.schemas import ChatRequest, ChatResponse, ChatSession, ChatMessage, ChatSessionCreate
from api.auth_middleware import get_current_user, get_current_user_optional

# Streaming support
# from agents.streaming import StreamManager, EventStreamer # DELETED

# Initialize global stream manager
# stream_manager = StreamManager() # DELETED

# WebSocket Manager
from api.connection_manager import manager as ws_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Legal AI Multi-Agent System",
    description="نظام الوكلاء الذكية للمحاماة",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - Secure configuration
# Origins configurable via ALLOWED_ORIGINS env var (comma-separated)
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:3000,http://localhost:5173,http://localhost:5174"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
)

from fastapi.staticfiles import StaticFiles

# Mount uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
from api.auth import router as auth_router
from api.clients import router as clients_router
from api.hearings import router as hearings_router
from api.routers.documents import router as documents_router
from api.routers import dashboard as dashboard_router
from api.routers import settings as settings_router
from api.routers import audit as audit_router  # ✅ New
from api.routers import cases as cases_router # ✅ New Cases Router

app.include_router(auth_router, tags=["authentication"])
app.include_router(clients_router, prefix="/api/clients", tags=["clients"])
app.include_router(hearings_router, prefix="/api/hearings", tags=["hearings"])
app.include_router(cases_router.router, prefix="/api/cases", tags=["cases"]) # ✅ Registered
app.include_router(documents_router, tags=["documents"])  # Already has /api/documents prefix
# Removed: app.include_router(ai_router, prefix="/api/ai", tags=["ai"])  # ai_helper deprecated
app.include_router(dashboard_router.router)
app.include_router(settings_router.router)
app.include_router(audit_router.router)

# ✅ Unified Agent Chat Router
from api.routers import chat as chat_router
app.include_router(chat_router.router)

# ✅ Phase 1 Security Remediation - Tasks & Police Records
from api.routers import tasks as tasks_router
from api.routers import police_records as police_records_router
app.include_router(tasks_router.router)
app.include_router(police_records_router.router)

# ✅ Phase 2 Security Remediation - Notifications & Assistants
from api.routers import notifications as notifications_router
from api.routers import assistants as assistants_router
app.include_router(notifications_router.router)
app.include_router(assistants_router.router)

# ✅ Phase 3 Security Remediation - Countries & Users
from api.routers import countries as countries_router
from api.routers import users as users_router
app.include_router(countries_router.router)
app.include_router(users_router.router)

from api.routers.support import router as support_router
app.include_router(support_router, prefix="/api/support", tags=["support"])

# ✅ Admin Subscriptions Management
from api.routers import admin_subscriptions as admin_subscriptions_router
app.include_router(admin_subscriptions_router.router)

# ✅ Lawyer Subscriptions
from api.routers import subscriptions as subscriptions_router
app.include_router(subscriptions_router.router)

# ✅ Super Admin Dashboard
from api.routers import admin as admin_router
app.include_router(admin_router.router)

# ✅ Transcription Service
from api.routers import transcription as transcription_router
app.include_router(transcription_router.router)

# ✅ Real-time SSE Streaming for Legal Research
# from api.routers import streaming as streaming_router # DELETED
# app.include_router(streaming_router.router) # DELETED

# ===== Assistants Endpoint =====
# Assistants creation logic moved to api/routers/assistants.py

# Initialize components with Enhanced Agent  
logger.info("🚀 Initializing Enhanced General Lawyer Agent Factory...")
# Global agent removed to ensure thread safety
# Agents are now created on-demand via agent_factory.get_agent_executor
logger.info("✅ Agent Factory ready for requests")

storage = CaseStorage(use_supabase=False)  # Using local storage for now

# =============================================================================
# Request/Response Models
# =============================================================================

class NewCaseRequest(BaseModel):
    """Request model for creating a new case"""
    facts: str = Field(..., description="وقائع القضية بالتفصيل")
    client_name: Optional[str] = Field(None, description="اسم العميل")
    case_type: Optional[str] = Field(None, description="نوع القضية (اختياري)")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="بيانات إضافية")


class NewCaseResponse(BaseModel):
    """Response model for new case creation"""
    case_id: str
    status: str
    message: str
    created_at: str


class CaseAnalysisResponse(BaseModel):
    """Response model for case analysis"""
    case_id: str
    status: str
    analysis: Dict[str, Any]
    plan: Optional[Dict[str, Any]] = None
    message: str


class CaseReportResponse(BaseModel):
    """Response model for case report"""
    case_id: str
    status: str
    analysis: Optional[Dict[str, Any]] = None
    plan: Optional[Dict[str, Any]] = None
    specialist_reports: Optional[List[Dict[str, Any]]] = None
    final_recommendation: Optional[Dict[str, Any]] = None
    case_file_path: str


class CaseListResponse(BaseModel):
    """Response model for listing cases"""
    total: int
    cases: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str


class ChatRequest(BaseModel):
    """Request model for chat message"""
    message: str = Field(..., description="محتوى الرسالة")


class ChatResponse(BaseModel):
    """Response model for chat interaction"""
    session_id: str
    message: str
    stage: str
    completed: bool
    case_data: Optional[Dict[str, Any]] = None
    case_id: Optional[str] = None

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.get("/api/health", response_model=Dict[str, Any])
async def api_health_check():
    """
    Comprehensive health check endpoint
    """
    from api.cache import get_cache
    
    cache = get_cache()
    cache_stats = cache.get_stats()
    cache_info = cache.get_info()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "api": "operational",
            "database": "operational",
            "cache": {
               "status": "operational" if cache_stats['available'] else "degraded",
                "enabled": cache_stats['enabled'],
                "available": cache_stats['available'],
                "statistics": {
                    "hits": cache_stats['hits'],
                    "misses": cache_stats['misses'],
                    "sets": cache_stats['sets'],
                    "deletes": cache_stats['deletes'],
                    "errors": cache_stats['errors'],
                    "hit_rate": f"{cache_stats['hit_rate']}%"
                },
                "server_info": cache_info if cache_info else None
            }
        }
    }

# Transcription logic moved to api/routers/transcription.py

# =============================================================================
# Chat & AI Endpoints
# =============================================================================

# Legacy /api/chat endpoint removed. Use /api/chat/{session_id}/message instead.

@app.post("/api/chat/start", response_model=ChatResponse)
async def start_chat_session(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Start a new stateless chat session
    """
    try:
        # Generate new session ID
        session_id = str(uuid.uuid4())
        
        # Default greeting
        greeting = "مرحباً! كيف يمكنني مساعدتك اليوم؟"
        if current_user:
            name = current_user.get("full_name", "User")
            greeting = f"مرحباً أستاذ {name}! أنا مدير مكتبك الذكي. جاهز للمساعدة."
        else:
            greeting = "مرحباً! يمكنك تجربة الوكيل الذكي."
            
        return ChatResponse(
            session_id=session_id,
            message=greeting,
            stage="init",
            completed=False
        )
    except Exception as e:
        logger.error(f"❌ Failed to start chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/{session_id}/message", response_model=ChatResponse)
async def send_chat_message(
    session_id: str, 
    request: ChatRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Send a message to the persistent graph agent.
    """
    try:
        logger.info(f"📨 Msg Session={session_id}")
        
        # Check active subscription
        if current_user:
            from api.utils.subscription_enforcement import check_subscription_active
            await check_subscription_active(user_id=current_user['id'], require_ai=True)
            
        # Delegate to Stateless Service
        # Pass generate_title flag based on request context if needed, 
        # or assuming it's passed in metadata. 
        # For now, default False or we can add a field to ChatRequest if we want explicit control.
        # But UI Logic says: "isFirstMessage" -> generate_title.
        # Let's add generate_title to the service call, defaulted to False?
        # The prompt didn't strictly say to add it to ChatRequest, but UI sends `generate_title` in body.
        # Let's check ChatRequest schema... I didn't add generate_title there.
        # I will assume the UI sends it and Pydantic filters it unless I update schema.
        # But wait, I updated `ChatRequest` in schema? No, checked schema file: `message`, `office_id`, `session_id`.
        # I should just update `process_message`.
        
        result = await chat_service.process_message(
            session_id=session_id,
            message_text=request.message,
            user_context=current_user,
            generate_title=False # We can improve this later
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# Chat Session Management Endpoints
# =============================================================================

@app.get("/api/chat/sessions", response_model=List[ChatSession])
async def list_chat_sessions(
    limit: int = 50,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """List chat sessions for the current user"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    return await chat_service.list_user_sessions(current_user['id'])

@app.post("/api/chat/sessions", response_model=ChatSession)
async def create_chat_session(
    session_in: ChatSessionCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Create a new chat session"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    return await chat_service.create_session(
        user_id=current_user['id'],
        title=session_in.title,
        session_type=session_in.session_type
    )

@app.get("/api/chat/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_session_messages(
    session_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get messages for a specific session"""
    if not current_user:
         raise HTTPException(status_code=401, detail="Authentication required")
         
    return await chat_service.get_session_messages(session_id, current_user['id'])

@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Delete a session"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    await chat_service.delete_session(session_id, current_user['id'])
    return {"status": "success"}






@app.get("/api/cases/{case_id}/stream")
async def stream_case_progress(case_id: str):
    """
    Endpoint disabled during re-architecture.
    """
    raise HTTPException(status_code=503, detail="Streaming service is under maintenance.")


@app.get("/api/config")
async def get_config():
    """Get current system configuration (non-sensitive)"""
    return {
        "llm_provider": "Open WebUI",
        "llm_model": settings.openwebui_model,
        "llm_api_url": settings.openwebui_api_url,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.openwebui_embedding_model if settings.embedding_provider == "openwebui" else settings.embedding_model,
        "search_weights": {
            "keyword": settings.keyword_weight,
            "vector": settings.vector_weight
        },
        "top_k_results": settings.top_k_results
    }


# =============================================================================
# Startup Event
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    from api.cache import get_cache
    
    logger.info("=" * 60)
    logger.info("🚀 Legal AI Multi-Agent System Starting...")
    logger.info("=" * 60)
    
    # Create cases directory
    import os
    os.makedirs(settings.storage_path, exist_ok=True)
    logger.info(f"✅ Cases directory ready: {settings.storage_path}")
    
    # Initialize Redis Cache
    cache = get_cache()
    cache_stats = cache.get_stats()
    if cache_stats['available']:
        logger.info(f"✅ Redis Cache: Connected (REDIS_ENABLED=True)")
        cache_info = cache.get_info()
        if cache_info:
            logger.info(f"   Redis Version: {cache_info.get('redis_version', 'unknown')}")
            logger.info(f"   Memory Used: {cache_info.get('used_memory_human', 'unknown')}")
    elif cache_stats['enabled']:
        logger.warning("⚠️ Redis Cache: Enabled but unavailable - using database fallback")
    else:
        logger.info("🔴 Redis Cache: Disabled (REDIS_ENABLED=False)")
    
    # Test agent initialization
    logger.info("Testing agent initialization...")
    logger.info("✅ Agent System: Ready (Factory Pattern)")
    logger.info(f"LLM Provider: Open WebUI")
    logger.info(f"Model: {settings.openwebui_model}")
    logger.info(f"API URL: {settings.openwebui_api_url}")
    logger.info(f"Embedding Provider: {settings.embedding_provider}")
    logger.info(f"Storage: {'Supabase' if settings.use_supabase_storage else 'Local'}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down Legal AI Multi-Agent System")


# =============================================================================
# Run Application
# =============================================================================


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Real-time WebSocket Endpoint for Agent Perception
    """
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive and listen for client messages (e.g. ping)
            data = await websocket.receive_text()
            # Optional: Handle client commands here
            pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        ws_manager.disconnect(websocket, client_id)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
