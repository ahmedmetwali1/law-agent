"""
Supabase Database Configuration and Connection
إعدادات والاتصال بقاعدة البيانات
"""

from supabase import create_client, Client
from typing import Optional
import logging

from .settings import settings, TableNames

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase client wrapper"""
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Supabase client"""
        if self._client is None:
            try:
                self._client = create_client(
                    settings.supabase_url,
                    settings.supabase_service_role_key  # Use service role for full access
                )
                logger.info("✅ Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Supabase client: {e}")
                raise
    
    @property
    def client(self) -> Client:
        """Get Supabase client instance"""
        if self._client is None:
            raise RuntimeError("Supabase client not initialized")
        return self._client
    
    # Convenient table accessors
    @property
    def legal_sources(self):
        """Access legal_sources table"""
        return self.client.table(TableNames.LEGAL_SOURCES)
    
    @property
    def document_chunks(self):
        """Access document_chunks table"""
        return self.client.table(TableNames.DOCUMENT_CHUNKS)
    
    @property
    def thought_templates(self):
        """Access thought_templates table"""
        return self.client.table(TableNames.THOUGHT_TEMPLATES)
    
    @property
    def storage(self):
        """Access Supabase storage"""
        return self.client.storage
    
    def get_bucket(self, bucket_name: str = None):
        """Get storage bucket"""
        bucket = bucket_name or settings.cases_bucket
        return self.storage.from_(bucket)


# Global database instance
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance
    
    Returns:
        Supabase Client instance
    """
    global _supabase_client
    
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError("Supabase credentials not configured in environment")
        
        try:
            _supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
            logger.info("✅ Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise
    
    return _supabase_client


# Database schema information (for reference)
SCHEMA_INFO = {
    "legal_sources": {
        "description": "Full legal source documents",
        "columns": {
            "id": "uuid - Primary key",
            "country_id": "uuid - Country reference",
            "title": "text - Document title",
            "doc_type": "text - Document type (قانون، لائحة، حكم)",
            "full_content_md": "text - Full content in Markdown",
            "total_word_count": "int4 - Total word count",
            "drive_link": "text - Google Drive link",
            "is_enriched": "bool - AI enrichment status",
            "metadata": "jsonb - Additional metadata",
            "created_at": "timestamptz - Creation timestamp",
            "updated_at": "timestamptz - Last update timestamp",
            "drive_file_id": "text - Google Drive file ID"
        }
    },
    "document_chunks": {
        "description": "Chunked document segments (~1500 words) with embeddings",
        "columns": {
            "id": "uuid - Primary key",
            "source_id": "uuid - Foreign key to legal_sources",
            "content": "text - Chunk content",
            "embedding": "vector - Vector embedding for semantic search",
            "sequence_number": "int4 - Order in source document",
            "hierarchy_path": "text - Hierarchical path (باب/فصل/مادة)",
            "chunk_word_count": "int4 - Word count in chunk",
            "status": "text - Processing status",
            "ai_summary": "text - AI-generated summary",
            "legal_logic": "text - Extracted legal logic",
            "legal_strength": "text - Legal argument strength",
            "keywords": "jsonb - Extracted keywords",
            "fts_tokens": "tsvector - Full-text search tokens",
            "created_at": "timestamptz - Creation timestamp",
            "retry_count": "int4 - Processing retry count",
            "locked_at": "timestamp - Lock timestamp",
            "last_error": "text - Last error message",
            "processed_at": "timestamp - Processing completion timestamp",
            "thinking_trace": "text - Chain of thought trace",
            "extracted_principles": "jsonb - Extracted legal principles"
        }
    },
    "thought_templates": {
        "description": "Fixed legal reasoning templates",
        "columns": {
            "id": "uuid - Primary key",
            "template_text": "text - Template content",
            "template_embedding": "vector - Vector embedding (currently unused)",
            "occurrence_count": "int4 - Usage count",
            "confidence_score": "float8 - Confidence score (0-1)",
            "domain_tag": "text - Legal domain tag",
            "source_doc_ids": "uuid[] - Related source document IDs",
            "created_at": "timestamptz - Creation timestamp",
            "updated_at": "timestamptz - Last update timestamp",
            "source_chunk_ids": "uuid[] - Related chunk IDs",
            "principle_type": "varchar - Type of legal principle",
            "is_absolute": "bool - Is principle absolute",
            "exceptions": "text - Exceptions to the principle",
            "related_templates": "uuid[] - Related template IDs",
            "keywords": "text - Keywords"
        }
    }
}

# Legacy db instance for backward compatibility
db = SupabaseClient()


__all__ = [
    "db",
    "SupabaseClient",
    "get_supabase_client",
    "SCHEMA_INFO"
]
