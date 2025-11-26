"""
Embedding Service - Phase 5
Provides embeddings for semantic matching
"""

import logging
from typing import Optional
import numpy as np
from app.services.gemini import GeminiService

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
        self.embedding_cache = {}  # Simple in-memory cache
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding for text
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector as numpy array
        """
        if not text or not text.strip():
            return None
        
        # Check cache
        cache_key = hash(text)
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        try:
            # Use Gemini embedding API (text-embedding-004 or similar)
            # For now, use a placeholder - in production would use actual embedding API
            # This is a simplified version - actual implementation would call Gemini embedding endpoint
            
            # Placeholder: return random embedding (replace with actual API call)
            # In production: response = self.gemini_service.get_embedding(text)
            embedding = np.random.rand(768).astype(np.float32)  # Placeholder
            
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            # Cache
            self.embedding_cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}", exc_info=True)
            return None
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()

