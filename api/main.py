"""
FastAPI Application
Legal AI Multi-Agent System API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import sys
import os
from datetime import datetime

from agents.core.enhanced_general_lawyer_agent import EnhancedGeneralLawyerAgent
from agents.storage.case_storage import CaseStorage
from agents.config.settings import settings
from agents.tools.unified_tools import UnifiedToolSystem

from agents.storage.user_storage import user_storage
from api.chat_session import session_manager
from api.ai_helper import router as ai_router
from api.auth_middleware import get_current_user

# Streaming support
from agents.streaming import StreamManager, EventStreamer

# Initialize global stream manager
stream_manager = StreamManager()

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

app.include_router(auth_router, tags=["authentication"])
app.include_router(clients_router, prefix="/api/clients", tags=["clients"])
app.include_router(hearings_router, prefix="/api/hearings", tags=["hearings"])
app.include_router(documents_router, tags=["documents"])  # Already has /api/documents prefix
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])

from api.routers.support import router as support_router
app.include_router(support_router, prefix="/api/support", tags=["support"])

# ===== Assistants Endpoint =====
from pydantic import EmailStr
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CreateAssistantRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    office_id: str

@app.post("/api/assistants/create")
async def create_assistant(request: CreateAssistantRequest):
    """إنشاء مساعد جديد"""
    try:
        # التحقق من أن الإيميل غير مستخدم
        if user_storage.check_email_exists(request.email):
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # جلب بيانات المحامي لنسخ البيانات المشتركة
        lawyer = user_storage.get_user_by_id(request.office_id)
        if not lawyer:
            raise HTTPException(status_code=404, detail="Lawyer not found")
        
        # Hash password
        password_hash = pwd_context.hash(request.password)
        
        # إنشاء المساعد مباشرة في Supabase بجميع البيانات
        from agents.config.database import get_supabase_client
        supabase = get_supabase_client()
        
        new_assistant = {
            'email': request.email,
            'password_hash': password_hash,
            'full_name': request.full_name,
            'phone': request.phone,
            'role': 'assistant',
            'office_id': request.office_id,  # ✅ RESTORED: الآن يشير لـ users.id
            'role_id': 'e3fedef1-5387-4d6d-a90b-6bb8ed45e5f2',  # المساعد
            'is_active': True,
            # نسخ البيانات المشتركة من المحامي
            'country_id': lawyer.get('country_id'),
            'office_address': lawyer.get('office_address'),
            'office_city': lawyer.get('office_city'),
            'office_postal_code': lawyer.get('office_postal_code'),
            'timezone': lawyer.get('timezone', 'Africa/Cairo'),
            'business_hours': lawyer.get('business_hours'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = supabase.table('users').insert(new_assistant).execute()
        
        if not result.data:
            raise Exception("Failed to create assistant")
        
        return {"message": "تم إنشاء المساعد بنجاح", "assistant_id": result.data[0]['id']}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Initialize components with Enhanced Agent  
logger.info("🚀 Initializing Enhanced General Lawyer Agent...")
try:
    # Initialize agent (will be set per session with lawyer context)
    general_agent = EnhancedGeneralLawyerAgent()
    logger.info("✅ EnhancedGeneralLawyerAgent initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize agent: {e}")
    raise

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


@app.get("/api/health", response_model=HealthResponse)
async def api_health_check():
    """API Health check endpoint (alias for SystemFooter)"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


# =============================================================================
# Speech-to-Text Proxy Endpoint (Security: Hide Cloudflare credentials)
# =============================================================================

from fastapi import UploadFile, File
import httpx

@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Secure proxy for speech-to-text transcription
    Hides Cloudflare Worker credentials from frontend
    """
    try:
        # Read STT credentials from environment (secure)
        stt_url = os.getenv("STT_API_URL")
        stt_key = os.getenv("STT_API_KEY")
        
        if not stt_url or not stt_key:
            raise HTTPException(
                status_code=500,
                detail="STT service not configured"
            )
        
        # ✅ Validate file size BEFORE processing
        MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10 MB
        audio_content = await file.read()
        
        if len(audio_content) > MAX_AUDIO_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"حجم الملف يتجاوز الحد الأقصى ({MAX_AUDIO_SIZE // 1024 // 1024} ميجابايت)"
            )
        
        # ✅ Validate audio content is not empty
        if len(audio_content) < 100:  # Too small to be valid audio
            raise HTTPException(
                status_code=400,
                detail="الملف الصوتي فارغ أو تالف"
            )
        
        logger.info(f"🎤 STT Request - URL: {stt_url}")
        logger.info(f"🎤 STT Request - File: {file.filename}, Size: {len(audio_content)} bytes")
        logger.info(f"🎤 STT Request - Content-Type: {file.content_type}")
        
        # Forward to Cloudflare Worker with credentials
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                stt_url,
                headers={
                    "Authorization": f"Bearer {stt_key}",
                    "X-Custom-Auth-Key": stt_key,
                },
                files={"file": (file.filename, audio_content, file.content_type)},
                data={"model": "whisper-1", "language": "ar"}
            )
            
            logger.info(f"🎤 STT Response - Status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"STT API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail="فشل في تحويل الصوت إلى نص. يرجى المحاولة مرة أخرى."
                )
            
            result = response.json()
            
            # ✅ Apply text normalization (but be lenient)
            from api.utils.text_normalizer import ArabicTextNormalizer
            
            raw_text = result.get('text', '')
            
            # Log the raw transcription
            logger.info(f"📝 Raw transcription: '{raw_text}'")
            
            # Try to clean, but if cleaning fails, use original
            cleaned_text = ArabicTextNormalizer.validate_and_clean(raw_text, min_length=1)
            
            if not cleaned_text:
                # If cleaning removed everything, check if original had content
                if raw_text and raw_text.strip():
                    logger.warning(f"⚠️ Cleaning removed all content, using original: '{raw_text}'")
                    cleaned_text = raw_text.strip()
                else:
                    logger.error(f"❌ No transcription detected - raw: '{raw_text}'")
                    raise HTTPException(
                        status_code=400,
                        detail="لم يتم التعرف على أي كلام في التسجيل. تأكد من التحدث بوضوح."
                    )
            
            logger.info(f"✅ Transcription successful for user {current_user.get('id')}")
            logger.info(f"📝 Cleaned: '{cleaned_text}'")
            
            return {"text": cleaned_text}
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504, 
            detail="انتهت مهلة خدمة تحويل الصوت. يرجى المحاولة مرة أخرى."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail="حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
        )



# =============================================================================
# Chat & AI Endpoints
# =============================================================================

# Simple Chat Endpoint (Non-Streaming)
class SimpleChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    lawyer_id: Optional[str] = None


@app.post("/api/chat")
async def simple_chat(request: SimpleChatRequest):
    """
    Chat endpoint using EnhancedGeneralLawyerAgent with Streaming Thinking Steps
    """
    from api.streaming_chat import generate_ai_response
    
    return StreamingResponse(
        generate_ai_response(
            message=request.message,
            history=request.history,
            lawyer_id=request.lawyer_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/chat/start", response_model=ChatResponse)
async def start_chat_session():
    """Start a new chat session - no auth required initially"""
    try:
        # Create session without user context initially
        # User context will be set when first message is sent
        session = session_manager.create_session(user_data=None)
        
        logger.info(f"📝 New anonymous chat session created: {session.session_id}")
        
        # Get greeting message
        greeting = session.messages[-1]["content"] if session.messages else "مرحباً! سجل دخولك لتتمكن من استخدام الوكيل بالكامل."
        
        return ChatResponse(
            session_id=session.session_id,
            message=greeting,
            stage=session.stage.value,
            completed=False
        )
    except Exception as e:
        logger.error(f"❌ Failed to start chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/{session_id}/message", response_model=ChatResponse)
async def send_chat_message(
    session_id: str, 
    request: ChatRequest,
    authorization: Optional[str] = Header(None)
):
    """Send a message to the chat session"""
    try:
        # Get user from token if provided
        current_user = None
        logger.info(f"📨 Received message for session {session_id}")
        logger.info(f"🔑 Authorization header: {authorization[:50] if authorization else 'None'}...")
        
        if authorization:
            try:
                from api.auth_middleware import decode_token
                token = authorization.replace('Bearer ', '')
                payload = decode_token(token)
                
                if payload:
                    user_id = payload.get("sub")
                    if user_id:
                        # Get complete user data from database
                        user = user_storage.get_user_by_id(user_id)
                        if user:
                            # Remove sensitive data
                            user.pop("password_hash", None)
                            current_user = user
                            logger.info(f"✅ Authenticated user: {current_user.get('full_name', 'Unknown')}")
                        else:
                            logger.warning(f"⚠️ User {user_id} not found in database")
                    else:
                        logger.warning("⚠️ No user ID in token payload")
                else:
                    logger.warning("⚠️ Invalid token payload")
            except Exception as e:
                logger.warning(f"Invalid token: {e}")
        else:
            logger.warning("⚠️ No authorization header provided!")
        
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Set user context if available and not set
        if current_user and not session.lawyer_id:
            session.user_data = current_user
            session.lawyer_id = current_user.get("id")
            session.lawyer_name = current_user.get("full_name", "المحامي")
            logger.info(f"✅ User context set for session {session_id}: {session.lawyer_name}")
        elif session.lawyer_id:
            logger.info(f"ℹ️ Session already has lawyer_id: {session.lawyer_id}")
        else:
            logger.warning(f"⚠️ No user context available for session {session_id}")
        
        # Process user message
        result = session.process_response(request.message)
        
        response_data = {
            "session_id": session_id,
            "message": result.get("message", ""),
            "stage": result.get("stage"),
            "completed": result.get("completed", False),
            "case_data": result.get("case_data") if result.get("completed") else session.case_data
        }
        
        # If conversation is completed, create the case automatically
        if result.get("completed"):
            case_data = result.get("case_data")
            logger.info("🎉 Information collection complete. Creating case...")
            
            try:
                # Create case using collected data
                case_id = general_agent.receive_case(
                    facts=case_data.get("facts", ""),
                    client_name=case_data.get("client_name") or "عميل جديد",
                    case_type=case_data.get("case_type"),
                    additional_data=case_data.get("additional_info")
                )
                
                response_data["case_id"] = case_id
                response_data["message"] += f"\n\nتم إنشاء القضية بنجاح! رقم القضية: {case_id}"
                
                # Clean up session
                session_manager.delete_session(session_id)
                
            except Exception as e:
                logger.error(f"❌ Failed to create case after chat: {e}")
                response_data["message"] += f"\n\nحدث خطأ أثناء إنشاء القضية: {str(e)}"
        
        return ChatResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cases/new", response_model=NewCaseResponse)
async def create_new_case(request: NewCaseRequest):
    """
    Create a new case
    
    This endpoint receives case facts and creates a new case file.
    The case is saved to storage with a unique ID.
    """
    try:
        logger.info("📋 Received new case request")
        logger.info(f"   Client: {request.client_name}")
        logger.info(f"   Facts length: {len(request.facts)} chars")
        logger.info(f"   Case type: {request.case_type}")
        
        # Create case using general agent
        logger.info("🔄 Calling general_agent.receive_case()...")
        case_id = general_agent.receive_case(
            facts=request.facts,
            client_name=request.client_name,
            case_type=request.case_type,
            additional_data=request.additional_data
        )
        
        logger.info(f"✅ Case created successfully: {case_id}")
        
        return NewCaseResponse(
            case_id=case_id,
            status="pending",
            message="تم إنشاء القضية بنجاح",
            created_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to create case: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"فشل في إنشاء القضية: {str(e)}"
        )


@app.post("/api/cases/{case_id}/analyze", response_model=CaseAnalysisResponse)
async def analyze_case(case_id: str, background_tasks: BackgroundTasks):
    """
    Analyze a case and create execution plan
    
    This performs:
    1. Initial analysis by the General Lawyer Agent
    2. Plan creation by the Case Planner
    
    For full processing, use /api/cases/{case_id}/process
    """
    try:
        logger.info(f"🔍 Analyzing case: {case_id}")
        
        # Load case
        case_data = storage.load_case(case_id)
        if not case_data:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Perform analysis
        analysis = general_agent.analyze_case(case_id)
        
        # Create plan
        plan = general_agent.create_plan()
        
        return CaseAnalysisResponse(
            case_id=case_id,
            status="analyzed",
            analysis=analysis,
            plan=plan,
            message="تم تحليل القضية وإنشاء الخطة"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to analyze case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cases/{case_id}/process")
async def process_case_complete(case_id: str, background_tasks: BackgroundTasks):
    """
    Complete end-to-end case processing
    
    This performs all steps:
    1. Analysis
    2. Planning
    3. Specialist agent execution (via Executor)
    4. Final recommendation compilation
    
    This may take several minutes depending on case complexity.
    """
    try:
        logger.info(f"🚀 Starting complete processing for case: {case_id}")
        
        # Load case
        case_data = storage.load_case(case_id)
        if not case_data:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Analyze
        analysis = general_agent.analyze_case(case_id)
        
        # Create plan
        plan = general_agent.create_plan()
        
        # Execute plan using general_agent's built-in executor
        case_data = general_agent.current_case
        
        execution_result = general_agent.execute_plan_simple(
            case_data=case_data,
            plan=plan
        )
        
        # Extract results
        reports = execution_result.get("specialist_reports", [])
        final_recommendation = execution_result.get("final_recommendation", {})
        
        return {
            "case_id": case_id,
            "status": "completed",
            "analysis": analysis,
            "plan": plan,
            "specialist_reports": reports,
            "final_recommendation": final_recommendation,
            "message": "تم معالجة القضية بالكامل",
            "case_file": storage.get_case_file_path(case_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases/{case_id}", response_model=CaseReportResponse)
async def get_case(case_id: str):
    """
    Get case details and current status
    """
    try:
        case_data = storage.load_case(case_id)
        
        if not case_data:
            raise HTTPException(status_code=404, detail="Case not found")
        
        return CaseReportResponse(
            case_id= case_id,
            status=case_data.get("status", "unknown"),
            analysis=case_data.get("general_agent_analysis"),
            plan=case_data.get("plan"),
            specialist_reports=case_data.get("specialist_reports"),
            final_recommendation=case_data.get("final_recommendation"),
            case_file_path=storage.get_case_file_path(case_id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases", response_model=CaseListResponse)
async def list_cases(limit: int = 100):
    """
    List all cases
    """
    try:
        cases = storage.list_cases(limit=limit)
        
        return CaseListResponse(
            total=len(cases),
            cases=cases
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to list cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: str):
    """
    Delete a case
    """
    try:
        success = storage.delete_case(case_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Case not found or deletion failed")
        
        return {
            "case_id": case_id,
            "message": "تم حذف القضية بنجاح",
            "deleted": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases/{case_id}/stream")
async def stream_case_progress(case_id: str):
    """
    SSE endpoint لبث تحديثات معالجة القضية في الوقت الفعلي
    
    الواجهة تتصل بهذا الـ endpoint للحصول على:
    - تحديثات الخطوات (step_update)
    - تحديثات التقدم (progress_update)  
    - إكمال الخطة (plan_completed)
    
    Example (Frontend):
    ```javascript
    const eventSource = new EventSource('/api/cases/case_001/stream');
    
    eventSource.addEventListener('step_update', (e) => {
        const data = JSON.parse(e.data);
        console.log(`Step ${data.step_id}: ${data.status}`);
    });
    
    eventSource.addEventListener('progress_update', (e) => {
        const data = JSON.parse(e.data);
        console.log(`Progress: ${data.percentage}%`);
    });
    ```
    """
    logger.info(f"📡 SSE connection requested for case: {case_id}")
    
    # الحصول على streamer من المدير
    streamer = stream_manager.get(case_id)
    
    if not streamer:
        # إذا لم يكن موجود، إنشاؤه (في حالة reconnection)
        logger.info(f"Creating new streamer for case: {case_id}")
        streamer = stream_manager.register(case_id)
    
    return StreamingResponse(
        streamer.stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # لـ nginx
        }
    )


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
    logger.info("=" * 60)
    logger.info("🚀 Legal AI Multi-Agent System Starting...")
    logger.info("=" * 60)
    
    # Create cases directory
    import os
    os.makedirs(settings.storage_path, exist_ok=True)
    logger.info(f"✅ Cases directory ready: {settings.storage_path}")
    
    # Test agent initialization
    logger.info("Testing agent initialization...")
    logger.info(f"✅ Agent initialized: {general_agent.name}")
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

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
