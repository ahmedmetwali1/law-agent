"""
Fetch Tools - أدوات الاسترجاع المتقدمة
Tools for fetching specific documents and flexible searching
"""

import time
import logging
from typing import List, Optional, Dict, Any, Literal
from dataclasses import dataclass

from .base_tool import BaseTool, ToolResult
from ..config.database import db

logger = logging.getLogger(__name__)


# Supported tables for fetching
# Note: keywords and exceptions are text[] arrays, ilike doesn't work on them
SUPPORTED_TABLES = {
    "document_chunks": {
        "fields": ["id", "source_id", "content", "embedding", "hierarchy_path", 
                   "ai_summary", "legal_logic", "keywords", "extracted_principles",
                   "thinking_trace", "sequence_number"],
        "searchable": ["content", "ai_summary", "legal_logic"]  # keywords is text[], skip it
    },
    "legal_sources": {
        "fields": ["id", "title", "doc_type", "full_content_md", "drive_link",
                   "metadata", "country_id", "total_word_count"],
        "searchable": ["title", "full_content_md"]
    },
    "thought_templates": {
        "fields": ["id", "template_text", "principle_type", "confidence_score",
                   "is_absolute", "exceptions", "keywords", "occurrence_count"],
        "searchable": ["template_text"]  # keywords and exceptions are text[], skip them
    }
}


@dataclass
class PaginationInfo:
    """Pagination metadata"""
    total_count: int
    current_page: int
    page_size: int
    has_more: bool
    next_offset: int


class FetchByIdTool(BaseTool):
    """
    أداة جلب مستند محدد بالـ ID
    
    Fetch a specific document by its ID from any table.
    Useful when the agent saw a principle and wants the full document.
    """
    
    def __init__(self):
        super().__init__(
            name="fetch_by_id",
            description="جلب مستند محدد بالـ ID من أي جدول"
        )
    
    def run(
        self,
        table: str,
        record_id: str,
        fields: Optional[List[str]] = None
    ) -> ToolResult:
        """
        Fetch a specific record by ID.
        
        Args:
            table: Table name (document_chunks, legal_sources, thought_templates)
            record_id: The UUID of the record
            fields: Specific fields to return (None = all fields)
            
        Returns:
            ToolResult with the record data
        """
        self._track_usage()
        start_time = time.time()
        
        try:
            # Validate table name
            if table not in SUPPORTED_TABLES:
                return ToolResult(
                    success=False,
                    error=f"جدول غير معروف: {table}",
                    metadata={
                        "supported_tables": list(SUPPORTED_TABLES.keys()),
                        "error_code": "INVALID_TABLE"
                    }
                )
            
            logger.info(f"📥 FetchById: Fetching from {table} with ID {record_id[:8]}...")
            
            # Build field selection
            if fields:
                # Validate fields
                valid_fields = SUPPORTED_TABLES[table]["fields"]
                invalid = [f for f in fields if f not in valid_fields]
                if invalid:
                    return ToolResult(
                        success=False,
                        error=f"حقول غير موجودة: {invalid}",
                        metadata={
                            "valid_fields": valid_fields,
                            "error_code": "INVALID_FIELDS"
                        }
                    )
                select_str = ",".join(fields)
            else:
                select_str = "*"
            
            # Execute query
            response = db.client.from_(table).select(select_str).eq("id", record_id).execute()
            
            elapsed = (time.time() - start_time) * 1000
            
            if not response.data:
                return ToolResult(
                    success=False,
                    error=f"لم يتم العثور على سجل بالـ ID: {record_id}",
                    metadata={"error_code": "NOT_FOUND"},
                    execution_time_ms=elapsed
                )
            
            record = response.data[0]
            
            logger.info(f"✅ FetchById: Found record with {len(record)} fields in {elapsed:.0f}ms")
            
            return ToolResult(
                success=True,
                data=record,
                metadata={
                    "table": table,
                    "record_id": record_id,
                    "fields_returned": list(record.keys())
                },
                execution_time_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"❌ FetchById failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={
                    "error_code": "FETCH_ERROR",
                    "suggestions": ["تحقق من صحة الـ ID", "جرب جدول آخر"]
                },
                execution_time_ms=(time.time() - start_time) * 1000
            )


class FlexibleSearchTool(BaseTool):
    """
    أداة بحث مرنة متعددة الأساليب
    
    Flexible search tool supporting multiple search methods:
    - keyword: Simple word matching
    - phrase: Exact phrase matching
    - multi: Multiple words (any or all)
    
    With pagination support for large result sets.
    """
    
    def __init__(self):
        super().__init__(
            name="flexible_search",
            description="بحث مرن في قاعدة البيانات بأساليب متعددة"
        )
    
    def run(
        self,
        query: str,
        tables: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        method: Literal["keyword", "phrase", "any", "all"] = "any",
        limit: int = 10,
        offset: int = 0,
        min_word_length: int = 2
    ) -> ToolResult:
        """
        Flexible search across tables.
        
        Args:
            query: Search query (word, phrase, or multiple words)
            tables: Tables to search (default: document_chunks)
            fields: Fields to search in (default: content)
            method: 
                - "keyword": Single word match
                - "phrase": Exact phrase match
                - "any": Any word matches (OR)
                - "all": All words must match (AND)
            limit: Results per page (max 50)
            offset: Starting offset for pagination
            min_word_length: Minimum word length to consider
            
        Returns:
            ToolResult with search results and pagination info
        """
        self._track_usage()
        start_time = time.time()
        
        try:
            # Defaults
            tables = tables or ["document_chunks"]
            limit = min(limit, 50)  # Cap at 50
            
            logger.info(f"🔍 FlexibleSearch: '{query[:30]}...' in {tables} using {method}")
            
            all_results = []
            
            for table in tables:
                if table not in SUPPORTED_TABLES:
                    logger.warning(f"Skipping unknown table: {table}")
                    continue
                
                # Determine searchable fields
                search_fields = fields or SUPPORTED_TABLES[table]["searchable"][:2]
                
                # Execute search based on method
                results = self._search_table(
                    table=table,
                    query=query,
                    fields=search_fields,
                    method=method,
                    limit=limit,
                    offset=offset,
                    min_word_length=min_word_length
                )
                
                all_results.extend(results)
            
            elapsed = (time.time() - start_time) * 1000
            
            # Build pagination info
            has_more = len(all_results) >= limit
            pagination = PaginationInfo(
                total_count=len(all_results),
                current_page=offset // limit + 1,
                page_size=limit,
                has_more=has_more,
                next_offset=offset + limit if has_more else -1
            )
            
            logger.info(f"✅ FlexibleSearch: Found {len(all_results)} results in {elapsed:.0f}ms")
            
            return ToolResult(
                success=True,
                data=all_results[:limit],
                metadata={
                    "query": query,
                    "method": method,
                    "tables_searched": tables,
                    "pagination": {
                        "total": pagination.total_count,
                        "page": pagination.current_page,
                        "has_more": pagination.has_more,
                        "next_offset": pagination.next_offset
                    }
                },
                execution_time_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"❌ FlexibleSearch failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={
                    "error_code": "SEARCH_ERROR",
                    "suggestions": [
                        "جرب كلمات أقل",
                        "استخدم method='any' للبحث الأوسع",
                        "قلل الـ limit"
                    ]
                },
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _search_table(
        self,
        table: str,
        query: str,
        fields: List[str],
        method: str,
        limit: int,
        offset: int,
        min_word_length: int
    ) -> List[Dict[str, Any]]:
        """Execute search on a single table"""
        
        # Parse query into words
        words = [w.strip() for w in query.split() if len(w.strip()) >= min_word_length]
        
        if not words:
            words = [query]  # Use full query if no valid words
        
        # Build query based on method
        query_builder = db.client.from_(table).select("*")
        
        if method == "phrase":
            # Exact phrase match
            conditions = [f"{field}.ilike.%{query}%" for field in fields]
            query_builder = query_builder.or_(",".join(conditions))
            
        elif method == "keyword" or method == "any":
            # Any word matches (OR)
            conditions = []
            for word in words[:5]:  # Limit to 5 words
                for field in fields:
                    conditions.append(f"{field}.ilike.%{word}%")
            query_builder = query_builder.or_(",".join(conditions))
            
        elif method == "all":
            # All words must match (AND) - apply filters sequentially
            for word in words[:5]:
                word_conditions = [f"{field}.ilike.%{word}%" for field in fields]
                query_builder = query_builder.or_(",".join(word_conditions))
        
        # Apply pagination
        query_builder = query_builder.range(offset, offset + limit - 1)
        
        response = query_builder.execute()
        
        # Format results
        results = []
        for row in response.data:
            results.append({
                "table": table,
                "id": row.get("id"),
                "content": row.get("content") or row.get("template_text") or row.get("title"),
                "summary": row.get("ai_summary"),
                "source_id": row.get("source_id"),
                "raw": row  # Keep raw data for further processing
            })
        
        return results
    
    def can_handle(self, query: str) -> float:
        """Determine confidence for handling this query"""
        # This tool is very flexible, so it can handle most queries
        if len(query.split()) > 1:
            return 0.8  # Multiple words = flexible search is good
        return 0.6


class GetRelatedDocumentTool(BaseTool):
    """
    أداة جلب المستند الأصلي المرتبط
    
    When the agent sees a chunk or principle, it can fetch the full source document.
    """
    
    def __init__(self):
        super().__init__(
            name="get_related_document",
            description="جلب المستند الأصلي الكامل من chunk أو مبدأ"
        )
    
    def run(
        self,
        chunk_id: Optional[str] = None,
        source_id: Optional[str] = None,
        include_siblings: bool = False,
        sibling_limit: int = 3
    ) -> ToolResult:
        """
        Get the full source document related to a chunk.
        
        Args:
            chunk_id: ID of a document_chunk (will fetch its source)
            source_id: Direct ID of legal_source
            include_siblings: Also fetch nearby chunks from same source
            sibling_limit: Number of sibling chunks to include
            
        Returns:
            ToolResult with source document and optionally sibling chunks
        """
        self._track_usage()
        start_time = time.time()
        
        try:
            # If chunk_id provided, first get the source_id
            if chunk_id and not source_id:
                chunk_response = db.document_chunks.select("source_id").eq("id", chunk_id).execute()
                if chunk_response.data:
                    source_id = chunk_response.data[0].get("source_id")
                else:
                    return ToolResult(
                        success=False,
                        error=f"Chunk not found: {chunk_id}",
                        metadata={"error_code": "CHUNK_NOT_FOUND"}
                    )
            
            if not source_id:
                return ToolResult(
                    success=False,
                    error="يجب توفير chunk_id أو source_id",
                    metadata={"error_code": "MISSING_ID"}
                )
            
            logger.info(f"📚 GetRelatedDoc: Fetching source {source_id[:8]}...")
            
            # Fetch the source document
            source_response = db.legal_sources.select(
                "id, title, doc_type, full_content_md, drive_link, metadata"
            ).eq("id", source_id).execute()
            
            if not source_response.data:
                return ToolResult(
                    success=False,
                    error=f"Source document not found: {source_id}",
                    metadata={"error_code": "SOURCE_NOT_FOUND"}
                )
            
            source_doc = source_response.data[0]
            
            result_data = {
                "source": source_doc,
                "siblings": []
            }
            
            # Optionally fetch sibling chunks
            if include_siblings:
                siblings_response = db.document_chunks.select(
                    "id, content, sequence_number, ai_summary"
                ).eq("source_id", source_id).order(
                    "sequence_number"
                ).limit(sibling_limit).execute()
                
                result_data["siblings"] = siblings_response.data
            
            elapsed = (time.time() - start_time) * 1000
            
            logger.info(f"✅ GetRelatedDoc: Found source with {len(result_data.get('siblings', []))} siblings in {elapsed:.0f}ms")
            
            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "source_id": source_id,
                    "title": source_doc.get("title"),
                    "has_siblings": len(result_data.get("siblings", [])) > 0
                },
                execution_time_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"❌ GetRelatedDoc failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"error_code": "FETCH_ERROR"},
                execution_time_ms=(time.time() - start_time) * 1000
            )


__all__ = [
    "FetchByIdTool",
    "FlexibleSearchTool", 
    "GetRelatedDocumentTool",
    "SUPPORTED_TABLES",
    "PaginationInfo"
]
