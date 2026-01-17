"""
System Settings and Configuration
إعدادات النظام العامة
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env
    )
    
    # Supabase Configuration
    supabase_url: str = Field(default="", env="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", env="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", env="SUPABASE_SERVICE_ROLE_KEY")
    
    # Open WebUI Configuration
    openwebui_api_url: str = Field(default="http://localhost:11434", env="OPENWEBUI_API_URL") 
    openwebui_api_key: str = Field(default="", env="OPENWEBUI_API_KEY")
    openwebui_model: str = Field(default="llama3.1:latest", env="OPENWEBUI_MODEL")
    
    # Backward compatibility
    ai_provider: str = Field(default="openwebui", env="AI_PROVIDER")
    
    # Embedding Configuration
    embedding_provider: str = Field(default="openwebui", env="EMBEDDING_PROVIDER")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")  # For embeddings only if needed
    embedding_model: str = Field(default="bge-m3-embeddings", env="EMBEDDING_MODEL")
    openwebui_embedding_model: str = Field(default="bge-m3-embeddings", env="OPENWEBUI_EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=1024, env="EMBEDDING_DIMENSIONS")  # bge-m3 = 1024
    
    # Search Configuration
    keyword_weight: float = Field(default=0.5, env="KEYWORD_WEIGHT")
    vector_weight: float = Field(default=0.5, env="VECTOR_WEIGHT")
    top_k_results: int = Field(default=10, env="TOP_K_RESULTS")
    
    # LLM Configuration
    max_tokens: int = Field(default=2000, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    
    # Storage Configuration
    cases_bucket: str = Field(default="legal-cases", env="CASES_BUCKET")
    storage_path: str = Field(default="./cases", env="STORAGE_PATH")
    use_supabase_storage: bool = Field(default=False, env="USE_SUPABASE_STORAGE")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=True, env="DEBUG")


# Global settings instance
settings = Settings()


# Database table names
class TableNames:
    """Supabase table names - Complete Registry"""
    
    # === Operational Tables (مستخدمة في storage/) ===
    USERS = "users"
    CLIENTS = "clients"
    CASES = "cases"
    HEARINGS = "hearings"
    
    # === Knowledge Base Tables (مستخدمة في knowledge/) ===
    LEGAL_SOURCES = "legal_sources"
    DOCUMENT_CHUNKS = "document_chunks"
    THOUGHT_TEMPLATES = "thought_templates"
    
    @classmethod
    def get_all_tables(cls):
        """Get all table names"""
        return [
            cls.USERS,
            cls.CLIENTS,
            cls.CASES,
            cls.HEARINGS,
            cls.LEGAL_SOURCES,
            cls.DOCUMENT_CHUNKS,
            cls.THOUGHT_TEMPLATES
        ]
    
    @classmethod
    def get_operational_tables(cls):
        """Tables for day-to-day operations"""
        return [cls.USERS, cls.CLIENTS, cls.CASES, cls.HEARINGS]
    
    @classmethod
    def get_knowledge_tables(cls):
        """Tables for legal knowledge base"""
        return [cls.LEGAL_SOURCES, cls.DOCUMENT_CHUNKS, cls.THOUGHT_TEMPLATES]



# Agent types
class AgentTypes:
    """Available specialist agent types"""
    CRIMINAL_LAW = "criminal_law"
    CIVIL_LAW = "civil_law"
    COMMERCIAL_LAW = "commercial_law"
    EVIDENCE_ANALYSIS = "evidence_analysis"
    PRECEDENT_RESEARCH = "precedent_research"
    
    @classmethod
    def all_types(cls):
        """Get all available agent types"""
        return [
            cls.CRIMINAL_LAW,
            cls.CIVIL_LAW,
            cls.COMMERCIAL_LAW,
            cls.EVIDENCE_ANALYSIS,
            cls.PRECEDENT_RESEARCH
        ]


# Case status
class CaseStatus:
    """Case processing status"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Export main objects
__all__ = [
    "settings",
    "Settings",
    "TableNames",
    "AgentTypes",
    "CaseStatus"
]
