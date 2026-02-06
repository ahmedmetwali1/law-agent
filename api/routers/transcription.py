from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import httpx
import os
import logging
from api.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["transcription"])

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Secure proxy for speech-to-text transcription
    """
    try:
        stt_url = os.getenv("STT_API_URL")
        stt_key = os.getenv("STT_API_KEY")
        
        if not stt_url or not stt_key:
            raise HTTPException(
                status_code=500,
                detail="STT service not configured"
            )
        
        MAX_AUDIO_SIZE = 10 * 1024 * 1024
        audio_content = await file.read()
        
        if len(audio_content) > MAX_AUDIO_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"حجم الملف يتجاوز الحد الأقصى ({MAX_AUDIO_SIZE // 1024 // 1024} ميجابايت)"
            )
        
        if len(audio_content) < 100:
            raise HTTPException(
                status_code=400,
                detail="الملف الصوتي فارغ أو تالف"
            )
        
        logger.info(f"🎤 STT Request - URL: {stt_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                stt_url,
                headers={"Authorization": f"Bearer {stt_key}", "X-Custom-Auth-Key": stt_key},
                files={"file": (file.filename, audio_content, file.content_type)},
                data={"model": "whisper-1", "language": "ar"}
            )
            
            if response.status_code != 200:
                logger.error(f"STT API error: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail="فشل في تحويل الصوت إلى نص. يرجى المحاولة مرة أخرى."
                )
            
            result = response.json()
            from api.utils.text_normalizer import ArabicTextNormalizer
            
            raw_text = result.get('text', '')
            cleaned_text = ArabicTextNormalizer.validate_and_clean(raw_text, min_length=1)
            
            if not cleaned_text:
                if raw_text and raw_text.strip():
                     cleaned_text = raw_text.strip()
                else:
                     raise HTTPException(status_code=400, detail="لم يتم التعرف على أي كلام في التسجيل. تأكد من التحدث بوضوح.")
            
            return {"text": cleaned_text}
            
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail="حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
        )
