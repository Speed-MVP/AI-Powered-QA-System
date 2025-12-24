"""
Embedding Service - Phase 5
Provides embeddings for semantic matching using Gemini text-embedding-004 model
"""

import logging
import os
from typing import Optional
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

# Import Google GenAI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Embedding service will use fallback.")


class EmbeddingService:
    """Service for generating text embeddings using Gemini API"""
    
    # Embedding model to use
    EMBEDDING_MODEL = "text-embedding-004"
    EMBEDDING_DIM = 768
    
    def __init__(self):
        self.embedding_cache = {}  # Simple in-memory cache
        self._initialized = False
        self._api_available = False
        
        # Initialize Gemini API
        if GEMINI_AVAILABLE and settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self._api_available = True
                self._initialized = True
                logger.info(f"EmbeddingService initialized with model: {self.EMBEDDING_MODEL}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API for embeddings: {e}")
                self._api_available = False
        else:
            logger.warning("Gemini API not available for embeddings. Using fallback keyword-based matching.")
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding for text using Gemini text-embedding-004 model
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector as numpy array (768 dimensions)
        """
        if not text or not text.strip():
            return None
        
        # Normalize text for consistent caching
        text = text.strip()
        
        # Check cache first
        cache_key = hash(text)
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        # Try to get real embedding from API
        if self._api_available:
            try:
                embedding = self._get_gemini_embedding(text)
                if embedding is not None:
                    # Cache the result
                    self.embedding_cache[cache_key] = embedding
                    return embedding
            except Exception as e:
                logger.warning(f"Gemini embedding API failed, using fallback: {e}")
        
        # Fallback: Use deterministic hash-based embedding
        # This ensures consistent results when API is unavailable
        embedding = self._get_fallback_embedding(text)
        self.embedding_cache[cache_key] = embedding
        return embedding
    
    def _get_gemini_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding from Gemini API
        
        Args:
            text: Text to embed
            
        Returns:
            Normalized embedding vector
        """
        try:
            # Truncate text if too long (model has input limits)
            max_chars = 8000  # Safe limit for embedding model
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.debug(f"Text truncated to {max_chars} chars for embedding")
            
            # Call Gemini embedding API
            result = genai.embed_content(
                model=f"models/{self.EMBEDDING_MODEL}",
                content=text,
                task_type="retrieval_document"  # Best for semantic similarity
            )
            
            # Extract embedding from response
            if result and 'embedding' in result:
                embedding = np.array(result['embedding'], dtype=np.float32)
                
                # Normalize for cosine similarity
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                
                logger.debug(f"Got embedding of dim {len(embedding)} for text: {text[:50]}...")
                return embedding
            else:
                logger.warning(f"Unexpected embedding response format: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Gemini embedding API call failed: {e}")
            return None
    
    def _get_fallback_embedding(self, text: str) -> np.ndarray:
        """
        Generate a deterministic fallback embedding based on text features.
        This ensures consistent results when API is unavailable.
        
        Uses a combination of:
        - Word frequency features
        - Character n-gram hashing
        - Text statistics
        
        Args:
            text: Text to embed
            
        Returns:
            Normalized embedding vector (768 dimensions)
        """
        # Initialize embedding vector
        embedding = np.zeros(self.EMBEDDING_DIM, dtype=np.float32)
        
        # Normalize text
        text_lower = text.lower()
        words = text_lower.split()
        
        if not words:
            return embedding
        
        # Feature 1: Word-based hashing (first 256 dims)
        for word in words:
            # Use deterministic hash
            word_hash = hash(word) % 256
            embedding[word_hash] += 1.0
        
        # Feature 2: Character bigram hashing (dims 256-512)
        for i in range(len(text_lower) - 1):
            bigram = text_lower[i:i+2]
            bigram_hash = hash(bigram) % 256 + 256
            embedding[bigram_hash] += 0.5
        
        # Feature 3: Character trigram hashing (dims 512-768)
        for i in range(len(text_lower) - 2):
            trigram = text_lower[i:i+3]
            trigram_hash = hash(trigram) % 256 + 512
            embedding[trigram_hash] += 0.3
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        logger.debug(f"Generated fallback embedding for text: {text[:50]}...")
        return embedding
    
    def get_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        
        if emb1 is None or emb2 is None:
            return 0.0
        
        # Cosine similarity (embeddings are already normalized)
        similarity = float(np.dot(emb1, emb2))
        return max(0.0, min(1.0, similarity))
    
    def clear_cache(self):
        """Clear embedding cache"""
        cache_size = len(self.embedding_cache)
        self.embedding_cache.clear()
        logger.debug(f"Cleared embedding cache ({cache_size} entries)")
    
    def is_api_available(self) -> bool:
        """Check if Gemini embedding API is available"""
        return self._api_available

