import logging
import time
from typing import Optional, Dict, Any, List
from .base_tool import BaseTool, ToolResult
from ..config.database import db

logger = logging.getLogger(__name__)

class ReadDocumentTool(BaseTool):
    """
    📖 Enhanced Read Document Tool
    
    Features:
    - Smart pagination with article detection
    - Context-aware chunking (respects article boundaries)
    - Search within document
    - Arabic text optimization
    """

# Explicitly import StructuredTool for the override
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# --- Pydantic Schema ---
class ReadDocumentInput(BaseModel):
    """Input for read_document tool."""
    doc_id: Optional[str] = Field(None, description="The UUID of the specific document or chunk to read.")
    source_id: Optional[str] = Field(None, description="(Book Mode) The ID of the legal source/book.")
    sequence_number: Optional[int] = Field(None, description="(Book Mode) The page/sentence number to navigate to.")
    start_line: int = Field(0, description="Starting line number (0-indexed).")
    limit: int = Field(50, description="Number of lines to read.")
    table: str = Field("document_chunks", description="Target table: 'legal_sources' (full text) or 'document_chunks' (pages).")
    search_term: Optional[str] = Field(None, description="Term to search for within the document.")

    class Config:
        extra = "forbid"

class ReadDocumentTool(BaseTool):
    """
    📖 Enhanced Read Document Tool
    
    Features:
    - Smart pagination with article detection
    - Context-aware chunking (respects article boundaries)
    - Search within document
    - Arabic text optimization
    """
    
    def __init__(self):
        super().__init__(
            name="read_document",
            description="اقرأ مستند قانوني مع دعم البحث داخل المستند واكتشاف حدود المواد"
        )
        self.args_schema = ReadDocumentInput
        self._article_pattern = r'(?:المادة|مادة|Article)\s*(\d+)'
    
    def to_langchain_tool(self) -> StructuredTool:
        """Override to ensure arguments schema is strictly applied."""
        return StructuredTool.from_function(
            func=self.run,
            name=self.name,
            description=self.description,
            args_schema=ReadDocumentInput, # Explicit binding
            strict=True # REQUIRED for auto-parsing in stricter LLM environments
        )

    def _find_article_boundaries(self, lines: List[str]) -> Dict[str, List[int]]:
        """Find line numbers where articles start"""
        import re
        boundaries = {}
        for i, line in enumerate(lines):
            match = re.search(self._article_pattern, line)
            if match:
                article_num = match.group(1)
                if article_num not in boundaries:
                    boundaries[article_num] = []
                boundaries[article_num].append(i)
        return boundaries
    
    def _extract_article(self, lines: List[str], article_num: str, boundaries: Dict) -> Optional[str]:
        """Extract complete article text"""
        if article_num not in boundaries:
            return None
        
        start_line = boundaries[article_num][0]
        
        # Find next article or end
        next_starts = [pos for art_positions in boundaries.values() 
                       for pos in art_positions if pos > start_line]
        end_line = min(next_starts) if next_starts else len(lines)
        
        return "\n".join(lines[start_line:end_line])
    
    def run(
        self,
        doc_id: Optional[str] = None,
        source_id: Optional[str] = None,
        sequence_number: Optional[int] = None,
        start_line: int = 0,
        limit: int = 50,
        table: str = "document_chunks", # Default to chunks now as per user instruction logic
        search_term: Optional[str] = None,
        # Legacy/Unused in schema but kept for safety if internally called
        article_num: Optional[str] = None,
        context_lines: int = 5
    ) -> ToolResult:
        """
        Execute read logic.
        """
        self._track_usage()
        start_time = time.time()
        
        try:
            limit = min(limit, 100)
            
            # --- Navigation Logic (Book Mode) ---
            if source_id and sequence_number is not None:
                # User wants a specific "Page"
                table = "document_chunks" # Valid by definition
                res = db.client.from_(table)\
                    .select("id, content, sequence_number, source_id")\
                    .eq("source_id", source_id)\
                    .eq("sequence_number", sequence_number)\
                    .maybe_single().execute()
                
                if not res.data:
                    return ToolResult(success=False, error=f"Page {sequence_number} not found for source {source_id}")
                
                # Update doc_id to match what we found
                doc_id = res.data["id"]
                # data is already fetched
            
            elif doc_id:
                # Standard ID lookup
                field = "full_content_md" if table == "legal_sources" else "content, source_id, sequence_number" 
                res = db.client.from_(table).select(field).eq("id", doc_id).single().execute()
            else:
                return ToolResult(success=False, error="Must provide doc_id OR (source_id + sequence_number)")
            
            if not res or not res.data:
                return ToolResult(success=False, error=f"Document not found")
            
            # Extract content
            if table == "legal_sources":
                 full_text = res.data.get("full_content_md") or ""
                 current_seq = None
                 current_source = res.data.get("id")
            else:
                 full_text = res.data.get("content") or ""
                 current_seq = res.data.get("sequence_number")
                 current_source = res.data.get("source_id")

            lines = full_text.split('\n')
            total_lines = len(lines)

            # Mode 1: Search
            if search_term:
                # Basic search implementation
                matches = []
                for i, line in enumerate(lines):
                    if search_term in line:
                         matches.append(f"L{i}: {line.strip()}")
                
                if matches:
                     content_chunk = "\n".join(matches[:10]) # Limit matches
                     metadata = {"matches_found": len(matches)}
                else:
                     content_chunk = f"No matches found for '{search_term}'"
                     metadata = {"matches_found": 0}
            else:
                # Mode 2: Pagination (Default)
                selected_lines = lines[start_line:start_line+limit]
                content_chunk = "\n".join(selected_lines)
            
            # 🛡️ Safety: Truncate if massive (Timeout/Memory protection)
            MAX_CHARS = 8000 # ~2000 tokens
            if len(content_chunk) > MAX_CHARS:
                content_chunk = content_chunk[:MAX_CHARS] + "\n... [TRUNCATED DUE TO SIZE]"
                logger.warning(f"⚠️ Document content truncated to {MAX_CHARS} chars.")
            
            # Smart Metadata
            metadata = {
                "source_id": current_source,
                "current_page": current_seq,
                "total_lines_in_page": total_lines,
                "preview": "This is a single page (Check sequence_number to read next).",
            }
            
            if current_source and current_seq is not None:
                metadata["navigation"] = {
                    "prev_page_cmd": f"read_document(source_id='{current_source}', sequence_number={current_seq - 1})",
                    "next_page_cmd": f"read_document(source_id='{current_source}', sequence_number={current_seq + 1})",
                    "hint": "Use source_id + sequence_number to flip pages."
                }

            return ToolResult(
                success=True,
                data={
                    "content": content_chunk,
                    "metadata": metadata
                },
                execution_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            logger.error(f"ReadDocumentTool failed: {e}")
            return ToolResult(success=False, error=str(e))