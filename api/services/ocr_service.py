"""
OCR Service using Mistral AI for document text extraction
استخدام Mistral AI لاستخراج النص من المستندات
"""
import os
from typing import Optional, Dict
from mistralai import Mistral
import logging

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self):
        """Initialize Mistral OCR client"""
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")
        
        self.client = Mistral(api_key=api_key)
        self.model = "pixtral-12b-2409"  # Mistral's vision model
    
    async def extract_text_from_file(self, file_path: str) -> Dict[str, any]:
        """
        Extract text from document using Mistral OCR
        
        Args:
            file_path: Path to the document file
            
        Returns:
            dict with:
                - success: bool
                - text: extracted text (if successful)
                - error: error message (if failed)
                - word_count: number of words
        """
        try:
            # Read file as base64
            import base64
            with open(file_path, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Determine MIME type
            file_extension = file_path.lower().split('.')[-1]
            mime_types = {
                'pdf': 'application/pdf',
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
            }
            mime_type = mime_types.get(file_extension, 'application/octet-stream')
            
            # Call Mistral OCR
            logger.info(f"Starting OCR extraction for: {file_path}")
            
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "استخرج جميع النصوص من هذا المستند بدقة. إذا كان النص غير واضح أو لا يمكن قراءته، اكتب 'لا يمكن الاستخراج'."
                            },
                            {
                                "type": "image_url",
                                "image_url": f"data:{mime_type};base64,{file_data}"
                            }
                        ]
                    }
                ]
            )
            
            # Extract text from response
            extracted_text = response.choices[0].message.content.strip()
            
            # Check if extraction failed
            if "لا يمكن الاستخراج" in extracted_text or len(extracted_text) < 10:
                return {
                    "success": False,
                    "text": None,
                    "error": "لا يمكن استخراج النص من المستند",
                    "word_count": 0
                }
            
            # Count words
            word_count = len(extracted_text.split())
            
            logger.info(f"OCR successful: {word_count} words extracted")
            
            return {
                "success": True,
                "text": extracted_text,
                "error": None,
                "word_count": word_count
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return {
                "success": False,
                "text": None,
                "error": f"خطأ في استخراج النص: {str(e)}",
                "word_count": 0
            }
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text"""
        if not text:
            return 0
        return len(text.split())
    
    @staticmethod
    def chunk_text(text: str, max_words: int = 3000) -> list[str]:
        """
        Split text into chunks of max_words
        
        Args:
            text: Text to split
            max_words: Maximum words per chunk (default: 3000)
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i + max_words])
            chunks.append(chunk)
        
        return chunks


# Lazy singleton instance
_ocr_service_instance = None

def get_ocr_service():
    """Get or create OCR service instance"""
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService()
    return _ocr_service_instance
