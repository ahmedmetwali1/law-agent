"""
LLM Service for document summarization
خدمة تلخيص المستندات باستخدام نموذج اللغة
"""
import os
from typing import Optional, Dict
from mistralai import Mistral
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        """Initialize LLM client"""
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")
        
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-large-latest"
        
        # System prompt for legal document summarization
        self.system_prompt = """أنت مساعد قانوني متخصص في تلخيص المستندات القانونية.

مهمتك:
1. قراءة النص المستخرج من المستند القانوني
2. تلخيصه بشكل واضح ومفيد للمحامي
3. التركيز على النقاط القانونية المهمة
4. الحفاظ على الدقة والموضوعية

إذا كان النص غير مفهوم أو غير واضح، اكتب: "لا يمكن التلخيص - النص غير واضح"

إذا كانت هذه جزء من مستند طويل (أكثر من 3000 كلمة):
- لخص الجزء الحالي فقط
- لا تضيف استنتاجات نهائية
- انتظر رسالة "انتهى المستند كامل" قبل الملخص النهائي
"""
    
    async def summarize_chunk(
        self, 
        text: str, 
        chunk_number: int = 1,
        total_chunks: int = 1,
        is_final: bool = False
    ) -> Dict[str, any]:
        """
        Summarize a chunk of document text
        
        Args:
            text: Text to summarize
            chunk_number: Current chunk number
            total_chunks: Total number of chunks
            is_final: Whether this is the final chunk
            
        Returns:
            dict with:
                - success: bool
                - summary: summary text (if successful)
                - error: error message (if failed)
                - should_save: whether to save this summary to DB
        """
        try:
            # Build user message
            if total_chunks == 1:
                user_message = f"لخص المستند التالي:\n\n{text}"
            elif is_final:
                user_message = f"هذا هو الجزء الأخير ({chunk_number}/{total_chunks}).\n\n{text}\n\nانتهى المستند كامل. يُرجى تقديم الملخص النهائي الشامل."
            else:
                user_message = f"هذا جزء ({chunk_number}/{total_chunks}) من مستند طويل. لخص هذا الجزء فقط:\n\n{text}"
            
            logger.info(f"Starting summarization for chunk {chunk_number}/{total_chunks}")
            
            # Call LLM
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,  # Lower temperature for more factual summaries
                max_tokens=1000
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Check if summarization failed
            if "لا يمكن التلخيص" in summary:
                return {
                    "success": False,
                    "summary": None,
                    "error": "لا يمكن تلخيص المستند - النص غير واضح",
                    "should_save": False
                }
            
            # Only save to DB if it's a single chunk OR the final chunk
            should_save = (total_chunks == 1) or is_final
            
            logger.info(f"Summarization successful. Should save: {should_save}")
            
            return {
                "success": True,
                "summary": summary,
                "error": None,
                "should_save": should_save
            }
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            return {
                "success": False,
                "summary": None,
                "error": f"خطأ في التلخيص: {str(e)}",
                "should_save": False
            }


# Lazy singleton instance
_llm_service_instance = None

def get_llm_service():
    """Get or create LLM service instance"""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance
