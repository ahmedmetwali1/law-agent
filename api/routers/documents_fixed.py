"""
Documents API Router
API للتعامل مع المستندات، الرفع، OCR، والتلخيص
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import os
import shutil
import uuid
from datetime import datetime
from supabase import create_client
from ..services.ocr_service import get_ocr_service
from ..services.llm_service import get_llm_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Lazy Supabase client initialization
_supabase_client = None

def get_supabase():
    """Get or create Supabase client"""
    global _supabase_client
    if _supabase_client is None:
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supabase_client

# Upload directory
UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    case_id: str = None,
    client_id: str = None,
    lawyer_id: str = None,
    document_type: str = "other",
    enable_ocr: bool = False
):
    """
    Upload a document and optionally enable OCR extraction
    
    Args:
        file: Document file (PDF, PNG, JPG, JPEG)
        case_id: ID of the case
        client_id: ID of the client
        lawyer_id: ID of the lawyer
        document_type: Type of document
        enable_ocr: Whether to enable OCR extraction
    """
    try:
        # Validate file type
        allowed_extensions = ['pdf', 'png', 'jpg', 'jpeg']
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"نوع الملف غير مدعوم. الأنواع المدعومة: {', '.join(allowed_extensions)}"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save file locally
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        logger.info(f"File uploaded: {filename}, size: {file_size} bytes")
        
        # Upload to Supabase Storage (optional - for now using local storage)
        # You can implement Supabase Storage upload here if needed
        file_url = f"/uploads/documents/{filename}"
        
        # Create document record in database
        document_data = {
            "id": file_id,
            "case_id": case_id,
            "client_id": client_id,
            "lawyer_id": lawyer_id,
            "file_name": file.filename,
            "file_url": file_url,
            "file_type": file_extension,
            "file_size": file_size,
            "document_type": document_type,
            "ocr_enabled": enable_ocr,
            "ocr_status": "pending" if enable_ocr else "disabled",
            "summary_status": "pending" if enable_ocr else "disabled",
            "uploaded_by": lawyer_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase = get_supabase()
        result = = get_supabase(); supabase.table("documents").insert(document_data).execute()
        
        # If OCR is enabled, trigger extraction
        if enable_ocr:
            # Call OCR endpoint asynchronously (in background)
            # For now, we'll return success and OCR will be processed separately
            logger.info(f"OCR extraction queued for document: {file_id}")
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "تم رفع المستند بنجاح",
                "document": result.data[0] if result.data else document_data
            }
        )
        
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        # Clean up file if database insert failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"فشل رفع المستند: {str(e)}")


@router.post("/{document_id}/extract")
async def extract_text(document_id: str):
    """
    Extract text from document using OCR
    
    Args:
        document_id: ID of the document
    """
    try:
        # Get document from database
        supabase = get_supabase()
        result = = get_supabase(); supabase.table("documents").select("*").eq("id", document_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="المستند غيرموجود")
        
        document = result.data[0]
        file_path = os.path.join(UPLOAD_DIR, document["file_url"].split("/")[-1])
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="الملف غير موجود")
        
        # Update status to processing
        supabase = get_supabase()
 = get_supabase(); supabase.table("documents").update({
            "ocr_status": "processing",
            "ocr_enabled": True
        }).eq("id", document_id).execute()
        
        # Extract text using OCR
        logger.info(f"Starting OCR for document: {document_id}")
        ocr = get_ocr_service()
        extraction_result = await ocr.extract_text_from_file(file_path)
        
        if extraction_result["success"]:
            # Update document with extracted text
 = get_supabase(); supabase.table("documents").update({
                "raw_text": extraction_result["text"],
                "word_count": extraction_result["word_count"],
                "ocr_status": "completed",
                "extraction_error": None,
                "is_analyzed": True
            }).eq("id", document_id).execute()
            
            logger.info(f"OCR completed: {extraction_result['word_count']} words")
            
            return JSONResponse(content={
                "success": True,
                "message": "تم استخراج النص بنجاح",
                "word_count": extraction_result["word_count"],
                "text_preview": extraction_result["text"][:200] + "..." if len(extraction_result["text"]) > 200 else extraction_result["text"]
            })
        else:
            # Update with error
 = get_supabase(); supabase.table("documents").update({
                "ocr_status": "failed",
                "extraction_error": extraction_result["error"]
            }).eq("id", document_id).execute()
            
            raise HTTPException(status_code=400, detail=extraction_result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text extraction failed: {str(e)}")
 = get_supabase(); supabase.table("documents").update({
            "ocr_status": "failed",
            "extraction_error": str(e)
        }).eq("id", document_id).execute()
        raise HTTPException(status_code=500, detail=f"فشل استخراج النص: {str(e)}")


@router.post("/{document_id}/summarize")
async def summarize_document(document_id: str):
    """
    Summarize document using LLM
    Handles large documents by chunking (max 3000 words per chunk)
    
    Args:
        document_id: ID of the document
    """
    try:
        # Get document from database
        result = = get_supabase(); supabase.table("documents").select("*").eq("id", document_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="المستند غير موجود")
        
        document = result.data[0]
        
        if not document.get("raw_text"):
            raise HTTPException(
                status_code=400,
                detail="يجب استخراج النص أولاً قبل التلخيص"
            )
        
        # Update status to processing
        supabase = get_supabase()
 = get_supabase(); supabase.table("documents").update({
            "summary_status": "processing"
        }).eq("id", document_id).execute()
        
        # Chunk text if needed
        text = document["raw_text"]
        ocr = get_ocr_service()
        word_count = ocr.count_words(text)
        
        if word_count <= 3000:
            # Single chunk - summarize directly
            logger.info(f"Summarizing document ({word_count} words)")
            llm = get_llm_service()
            summary_result = await llm.summarize_chunk(text, 1, 1, True)
            
            if summary_result["success"]:
 = get_supabase(); supabase.table("documents").update({
                    "ai_summary": summary_result["summary"],
                    "summary_status": "completed",
                    "is_complete": True,
                    "total_chunks": 1,
                    "chunk_number": 1
                }).eq("id", document_id).execute()
                
                return JSONResponse(content={
                    "success": True,
                    "message": "تم تلخيص المستند بنجاح",
                    "summary": summary_result["summary"],
                    "chunks": 1
                })
            else:
                raise HTTPException(status_code=400, detail=summary_result["error"])
        
        else:
            # Multiple chunks - process in batches
            ocr = get_ocr_service()
            chunks = ocr.chunk_text(text, max_words=3000)
            total_chunks = len(chunks)
            
            logger.info(f"Document split into {total_chunks} chunks")
            
            summaries = []
            llm = get_llm_service()
            for i, chunk in enumerate(chunks, 1):
                is_final = (i == total_chunks)
                
                logger.info(f"Processing chunk {i}/{total_chunks}")
                summary_result = await llm.summarize_chunk(
                    chunk, i, total_chunks, is_final
                )
                
                if not summary_result["success"]:
                    raise HTTPException(status_code=400, detail=summary_result["error"])
                
                summaries.append(summary_result["summary"])
                
                # Update progress
 = get_supabase(); supabase.table("documents").update({
                    "chunk_number": i,
                    "total_chunks": total_chunks
                }).eq("id", document_id).execute()
            
            # Save final summary (only the last one which is comprehensive)
            final_summary = summaries[-1]  # The last chunk contains the complete summary
            
 = get_supabase(); supabase.table("documents").update({
                "ai_summary": final_summary,
                "summary_status": "completed",
                "is_complete": True,
                "chunk_number": total_chunks,
                "total_chunks": total_chunks
            }).eq("id", document_id).execute()
            
            return JSONResponse(content={
                "success": True,
                "message": f"تم تلخيص المستند بنجاح ({total_chunks} أجزاء)",
                "summary": final_summary,
                "chunks": total_chunks
            })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarization failed: {str(e)}")
 = get_supabase(); supabase.table("documents").update({
            "summary_status": "failed"
        }).eq("id", document_id).execute()
        raise HTTPException(status_code=500, detail=f"فشل التلخيص: {str(e)}")


@router.get("/case/{case_id}")
async def get_case_documents(case_id: str):
    """
    Get all documents for a specific case
    
    Args:
        case_id: ID of the case
    """
    try:
        supabase = get_supabase()
        result = = get_supabase(); supabase.table("documents")\
            .select("*")\
            .eq("case_id", case_id)\
            .order("created_at", desc=True)\
            .execute()
        
        return JSONResponse(content={
            "success": True,
            "documents": result.data,
            "count": len(result.data)
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"فشل جلب المستندات: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document
    
    Args:
        document_id: ID of the document
    """
    try:
        # Get document to find file path
        supabase = get_supabase()
        result = = get_supabase(); supabase.table("documents").select("*").eq("id", document_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="المستند غير موجود")
        
        document = result.data[0]
        file_path = os.path.join(UPLOAD_DIR, document["file_url"].split("/")[-1])
        
        # Delete file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
 = get_supabase(); supabase.table("documents").delete().eq("id", document_id).execute()
        
        return JSONResponse(content={
            "success": True,
            "message": "تم حذف المستند بنجاح"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"فشل حذف المستند: {str(e)}")
