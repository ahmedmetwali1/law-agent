"""
Lookup Principle Tool
أداة البحث عن المبادئ القانونية في جدول thought_templates
"""

import time
import logging
from typing import List, Optional, Dict, Any, Type
# Use standard pydantic, usually compatible. If issues, try langchain_core.pydantic_v1
from pydantic import BaseModel, Field

from .base_tool import BaseTool, ToolResult
from ..config.database import db
from ..knowledge.embeddings import create_query_embedding

# Explicitly import StructuredTool for the override
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

class LookupPrincipleInput(BaseModel):
    """Input for lookup_principle tool."""
    query: str = Field(..., description="The search query for the legal principle.")
    limit: int = Field(5, description="Maximum number of results to return.")
    principle_type: Optional[str] = Field(None, description="Filter by principle type (e.g. شرعي قطعي).")
    min_confidence: float = Field(0.5, description="Minimum confidence score.")

    class Config:
        extra = "forbid"


class LookupPrincipleTool(BaseTool):
    """
    Tool to search for legal principles in the thought_templates table.
    
    This table contains extracted legal axioms and rules like:
    - "البينة على من ادعى" (The burden of proof is on the claimant)
    - "الأصل براءة الذمة" (The presumption of innocence)
    """
    
    def __init__(self):
        super().__init__(
            name="lookup_principle",
            description="البحث عن المبادئ والقواعد القانونية الثابتة"
        )
        self.args_schema = LookupPrincipleInput # Attach strict schema
        
        # Keywords that indicate principle lookup
        self.principle_keywords = [
            "مبدأ", "قاعدة", "أصل", "حكم شرعي", "قاعدة فقهية",
            "ما حكم", "ما هو الأصل", "البينة", "الضمان"
        ]
    
    def to_langchain_tool(self) -> StructuredTool:
        """Override to ensure arguments schema is strictly applied."""
        return StructuredTool.from_function(
            func=self.run,
            name=self.name,
            description=self.description,
            args_schema=LookupPrincipleInput, # Explicit binding
            strict=True # REQUIRED for auto-parsing in stricter LLM environments
        )

    def run(
        self,
        query: str,
        limit: int = 5,
        principle_type: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> ToolResult:
        """
        Search for legal principles.
        
        Args:
            query: Search query.
            limit: Maximum results.
            principle_type: Filter by type (شرعي قطعي, فقهي إجمالي, نظامي عام, منطقي).
            min_confidence: Minimum confidence score.
            
        Returns:
            ToolResult with matching principles.
        """
        self._track_usage()
        start_time = time.time()
        
        try:
            logger.info(f"🔍 LookupPrinciple: Searching for '{query[:50]}...'")
            
            # Use keyword search (template_embedding is currently NULL in DB)
            results = self._keyword_search_principles(query, limit, principle_type)
            
            elapsed = (time.time() - start_time) * 1000
            
            logger.info(f"✅ LookupPrinciple: Found {len(results)} principles in {elapsed:.0f}ms")
            
            return ToolResult(
                success=True,
                data=results,
                metadata={"query": query, "result_count": len(results)},
                execution_time_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"❌ LookupPrinciple failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _vector_search_principles(
        self,
        query: str,
        limit: int,
        principle_type: Optional[str],
        min_confidence: float
    ) -> List[Dict[str, Any]]:
        """Search principles using vector similarity"""
        try:
            # Generate embedding for query
            query_embedding = create_query_embedding(query)
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Use RPC for vector search if available
            response = db.client.rpc(
                "match_thought_templates",
                {
                    "query_embedding": embedding_str,
                    "match_threshold": min_confidence,
                    "match_count": limit
                }
            ).execute()
            
            results = []
            for row in response.data:
                # Apply type filter if specified
                if principle_type and row.get("principle_type") != principle_type:
                    continue
                    
                results.append({
                    "id": row["id"],
                    "principle_text": row.get("template_text"),
                    "type": row.get("principle_type"),
                    "confidence": row.get("confidence_score"),
                    "is_absolute": row.get("is_absolute"),
                    "exceptions": row.get("exceptions"),
                    "occurrence_count": row.get("occurrence_count"),
                    "similarity": row.get("similarity", 0.0)
                })
            
            return results
            
        except Exception as e:
            logger.warning(f"Vector search failed, falling back to keyword: {e}")
            return []
    
    def _keyword_search_principles(
        self,
        query: str,
        limit: int,
        principle_type: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Search principles using keyword matching"""
        try:
            query_builder = db.thought_templates.select(
                "id, template_text, principle_type, confidence_score, is_absolute, exceptions, occurrence_count, keywords"
            )
            
            # Apply type filter if specified
            if principle_type:
                query_builder = query_builder.eq("principle_type", principle_type)
            
            # Extract important words from query (skip short words)
            words = [w for w in query.split() if len(w) > 2][:5]
            
            if words:
                # Build OR conditions for each word
                conditions = []
                for word in words:
                    conditions.append(f"template_text.ilike.%{word}%")
                
                query_builder = query_builder.or_(",".join(conditions))
            
            response = query_builder.limit(limit).execute()
            
            results = []
            for row in response.data:
                results.append({
                    "id": row["id"],
                    "principle_text": row.get("template_text"),
                    "type": row.get("principle_type"),
                    "confidence": row.get("confidence_score"),
                    "is_absolute": row.get("is_absolute"),
                    "exceptions": row.get("exceptions"),
                    "occurrence_count": row.get("occurrence_count"),
                    "keywords": row.get("keywords")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def can_handle(self, query: str) -> float:
        """Check if this tool can handle the query"""
        query_lower = query.lower()
        
        # Check for principle-related keywords
        matches = sum(1 for kw in self.principle_keywords if kw in query_lower)
        
        if matches >= 2:
            return 0.9
        elif matches == 1:
            return 0.7
        
        # Check for question patterns about rules
        if any(pattern in query_lower for pattern in ["ما هو حكم", "ما حكم", "هل يجوز"]):
            return 0.6
        
        return 0.2


class LegalSourceTool(BaseTool):
    """
    Tool to search the legal_sources table for full legal documents.
    
    Use this when you need:
    - The full text of a law or regulation
    - Official reference to a legal source
    - Verification of a legal citation
    """
    
    def __init__(self):
        super().__init__(
            name="legal_source",
            description="البحث عن النصوص القانونية الكاملة (الأنظمة، اللوائح، الأحكام)"
        )
    
    def run(
        self,
        query: str,
        source_type: Optional[str] = None,
        limit: int = 3
    ) -> ToolResult:
        """
        Search for legal sources.
        
        Args:
            query: Search query (title or content).
            source_type: Filter by type (نظام, لائحة, حكم قضائي, فتوى, قرار).
            limit: Maximum results.
            
        Returns:
            ToolResult with matching sources.
        """
        self._track_usage()
        start_time = time.time()
        
        try:
            logger.info(f"📚 LegalSource: Searching for '{query[:50]}...'")
            
            query_builder = db.legal_sources.select(
                "id, title, source_type, authority, is_verified, metadata, reference_url"
            )
            
            # Apply type filter
            if source_type:
                query_builder = query_builder.eq("source_type", source_type)
            
            # Search in title
            query_builder = query_builder.ilike("title", f"%{query}%")
            
            response = query_builder.limit(limit).execute()
            
            results = []
            for row in response.data:
                results.append({
                    "id": row["id"],
                    "title": row.get("title"),
                    "type": row.get("source_type"),
                    "authority": row.get("authority"),
                    "is_verified": row.get("is_verified"),
                    "reference_url": row.get("reference_url"),
                    "metadata": row.get("metadata")
                })
            
            elapsed = (time.time() - start_time) * 1000
            
            logger.info(f"✅ LegalSource: Found {len(results)} sources in {elapsed:.0f}ms")
            
            return ToolResult(
                success=True,
                data=results,
                metadata={"query": query, "source_type": source_type},
                execution_time_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"❌ LegalSource failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def can_handle(self, query: str) -> float:
        """Check if query is about legal sources"""
        query_lower = query.lower()
        
        source_keywords = ["نظام", "لائحة", "قانون", "مادة", "نص", "تشريع", "حكم قضائي"]
        matches = sum(1 for kw in source_keywords if kw in query_lower)
        
        if matches >= 2:
            return 0.8
        elif matches == 1:
            return 0.5
        
        return 0.2


__all__ = ["LookupPrincipleTool", "LegalSourceTool"]
