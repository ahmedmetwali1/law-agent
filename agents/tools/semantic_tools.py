from typing import Dict, Any, List, Optional
import logging
import re
from pydantic import BaseModel, Field

from .base_tool import BaseTool, ToolResult
from ..config.database import db

# Explicitly import StructuredTool for the override
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

# --- Pydantic Schemas ---

class LegalEntityExtractorInput(BaseModel):
    """Input for extracting legal entities."""
    text: str = Field(..., description="The raw text to extract legal entities from.")
    
    class Config:
        extra = "forbid"

class TermVerificationInput(BaseModel):
    """Input for verifying legal terms."""
    term: str = Field(..., description="The legal term to verify.")
    context: Optional[str] = Field(None, description="Optional context for the term.")

    class Config:
        extra = "forbid"


class LegalEntityExtractorTool(BaseTool):
    """
    🧠 Semantic Layer: Legal Entity Extractor
    
    Extracts structured legal entities from raw text.
    - Courts (Degree, Type)
    - Persons (Clients, Judges)
    - Laws (Articles, Regulations)
    """
    
    # ========================================
    # Generic Universal Patterns (Multi-Country)
    # Works for Egypt, Saudi Arabia, UAE, and any other country
    # ========================================
    
    COURT_PATTERNS = [
        # Arabic patterns (generic)
        r"محكمة\s+[\w\s]{2,30}",     # محكمة + any words
        r"المحكمة\s+[\w\s]{2,30}",   # المحكمة + any words
        r"محكمه\s+[\w\s]{2,30}",     # Typo variant
        
        # English patterns
        r"[\w\s]{2,20}\s*[Cc]ourt",  # Any Court
        r"[Cc]ourt\s+of\s+[\w\s]{2,20}",
        
        # Abbreviated forms
        r"م\.\s*[\w\s]+",            # م.النقض، م.الاستئناف
    ]
    
    ARTICLE_PATTERNS = [
        # Arabic
        r"(المادة|مادة|م)\s*([\d\u0660-\u0669]+)",
        
        # English
        r"[Aa]rticle\s*(\d+)",
        
        # French (for some countries)
        r"[Aa]rt\.?\s*(\d+)",
    ]
    
    LAW_PATTERNS = [
        # Arabic
        r"(نظام|قانون|تشريع)\s+([\w\s]{2,50})",
        r"(اللوائح|اللائحة)\s+([\w\s]{2,50})",
        
        # English
        r"(Law|Act|Code|Regulation)\s+[\w\s]{2,50}",
    ]
    
    def __init__(self):
        super().__init__(
            name="extract_legal_entities",
            description="استخراج الكيانات القانونية (محاكم، أشخاص، مواد) من النص لتحديد الاختصاص."
        )
        self.args_schema = LegalEntityExtractorInput

    def to_langchain_tool(self) -> StructuredTool:
        """Override to ensure arguments schema is strictly applied."""
        return StructuredTool.from_function(
            func=self.run,
            name=self.name,
            description=self.description,
            args_schema=LegalEntityExtractorInput
        )

    def run(self, text: str) -> ToolResult:
        self._track_usage()
        try:
            entities = {
                "courts": [],
                "laws": [],
                "persons": [] # Basic heuristic
            }
            
            # 1. Extract Courts (Generic - works for any country)
            for pattern in self.COURT_PATTERNS:
                matches = re.findall(pattern, text)
                for match in matches:
                    if match.strip():  # Skip empty matches
                        entities["courts"].append({
                            "text": match.strip(),
                            "type": "court"  # Generic type
                        })
            
            # 2. Extract Laws/Articles (Regex)
            # Matches: مادة 77، نظام العمل، اللائحة التنفيذية
            # 2. Extract Articles (Generic)
            for pattern in self.ARTICLE_PATTERNS:
                matches = re.findall(pattern, text)
                for match in matches:
                    if match:
                        # Extract article number from tuple or string
                        article_num = match[-1] if isinstance(match, tuple) else match
                        entities["laws"].append({
                            "type": "article",
                            "number": article_num.strip() if article_num else "",
                            "text": " ".join(match) if isinstance(match, tuple) else match
                        })
            
            # 3. Extract Laws/Regulations (Generic)
            for pattern in self.LAW_PATTERNS:
                matches = re.findall(pattern, text)
                for match in matches:
                    if match:
                        law_name = " ".join(match) if isinstance(match, tuple) else match
                        entities["laws"].append({
                            "type": "law",
                            "name": law_name.strip()
                        })
                
            # 4. Simple Person Extraction (Universal)
            # Arabic: "ضد"
            if "ضد" in text:
                parts = text.split("ضد")
                if len(parts) > 1:
                    entities["persons"].append({
                        "role": "adversary",
                        "name": parts[1].strip().split()[0]
                    })
            
            # English: "vs" or "v."
            if " vs " in text.lower() or " v. " in text.lower():
                parts = re.split(r"\s+vs?\.?\s+", text, flags=re.IGNORECASE)
                if len(parts) > 1:
                    entities["persons"].append({
                        "role": "defendant",
                        "name": parts[1].strip().split()[0]
                    })
            
            return ToolResult(
                success=True,
                data=entities,
                message=f"تم استخراج {len(entities['courts'])} محاكم و {len(entities['laws'])} مواد."
            )

        except Exception as e:
            logger.error(f"Entity Extraction Failed: {e}")
            return ToolResult(success=False, error=str(e))


class TermVerificationTool(BaseTool):
    """
    🔍 Semantic Layer: Term Verification
    
    Validates if a legal term exists in the Knowledge Base.
    Useful for checking if "المادة 33" exists in "نظام المرافعات" or finding the correct name of a law.
    """
    
    def __init__(self):
        super().__init__(
            name="lookup_legal_term",
            description="التحقق من صحة المصطلح القانوني أو رقم المادة في قاعدة المعرفة."
        )
        self.args_schema = TermVerificationInput

    def to_langchain_tool(self) -> StructuredTool:
        """Override to ensure arguments schema is strictly applied."""
        return StructuredTool.from_function(
            func=self.run,
            name=self.name,
            description=self.description,
            args_schema=TermVerificationInput
        )

    def run(self, term: str, context: Optional[str] = None) -> ToolResult:
        self._track_usage()
        try:
            # 1. Search in Legal Sources (Titles)
            res = db.client.from_("legal_sources")\
                .select("id, title, source_type")\
                .ilike("title", f"%{term}%")\
                .limit(3).execute()
                
            sources = res.data if res.data else []
            
            # 2. Search in Document Chunks (Content - strictly for Articles)
            # If term looks like "Article X", we search chunks
            articles = []
            if any(x in term for x in ["مادة", "المادة"]):
                # Try to fuzzy match content in chunks
                # This is heavy, so we limit strictness
                res_chunk = db.client.from_("document_chunks")\
                    .select("id, source_id, sequence_number")\
                    .ilike("content", f"%{term}%")\
                    .limit(3).execute()
                articles = res_chunk.data if res_chunk.data else []

            found = len(sources) > 0 or len(articles) > 0
            
            return ToolResult(
                success=True,
                data={
                    "term": term,
                    "found": found,
                    "matches": {
                        "sources": [s["title"] for s in sources],
                        "fragments": len(articles)
                    }
                },
                message=f"المصطلح '{term}': {'موجود ✅' if found else 'غير مؤكد ❓'}"
            )

        except Exception as e:
            logger.error(f"Term Verification Failed: {e}")
            return ToolResult(success=False, error=str(e))
