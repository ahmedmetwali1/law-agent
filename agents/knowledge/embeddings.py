"""
Embeddings Generation Module
توليد ال embeddings للنصوص

Updated to use Open WebUI for embeddings generation.
"""

from typing import List, Union, Optional
import logging

from ..config.openwebui import openwebui_client
from ..config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text using Open WebUI"""
    
    def __init__(self):
        """Initialize embedding generator using Open WebUI"""
        self.client = openwebui_client
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        
        logger.info(f"🔧 EmbeddingGenerator initialized with model: {self.model}")
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            embedding = self.client.generate_embedding(text)
            logger.debug(f"✅ Generated embedding of dimension {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            raise
    
    def create_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Create embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        all_embeddings = []
        
        try:
            for i, text in enumerate(texts):
                embedding = self.create_embedding(text)
                all_embeddings.append(embedding)
                
                if (i + 1) % 10 == 0:
                    logger.debug(f"✅ Processed {i + 1}/{len(texts)} texts")
            
            logger.info(f"✅ Generated {len(all_embeddings)} embeddings")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"❌ Failed to generate batch embeddings: {e}")
            raise
    
    def create_query_embedding(self, query: str) -> List[float]:
        """
        Create embedding optimized for query/search
        
        Args:
            query: Search query text
            
        Returns:
            Query embedding vector
        """
        return self.create_embedding(query)


# Global embedding generator instance
embedding_generator = EmbeddingGenerator()


def create_embedding(text: str) -> List[float]:
    """Convenience function to create a single embedding"""
    return embedding_generator.create_embedding(text)


def create_embeddings(texts: List[str]) -> List[List[float]]:
    """Convenience function to create multiple embeddings"""
    return embedding_generator.create_embeddings_batch(texts)


def create_query_embedding(query: str) -> List[float]:
    """Convenience function to create a query embedding"""
    return embedding_generator.create_query_embedding(query)


__all__ = [
    "EmbeddingGenerator",
    "embedding_generator",
    "create_embedding",
    "create_embeddings",
    "create_query_embedding"
]
