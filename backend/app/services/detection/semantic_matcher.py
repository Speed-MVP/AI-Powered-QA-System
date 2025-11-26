"""
Semantic Match Engine - Phase 5
Embedding-based similarity matching for behaviors
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SemanticMatcher:
    """Semantic matching using embeddings"""
    
    def __init__(self, similarity_threshold: float = 0.78):
        self.similarity_threshold = similarity_threshold
        self.embedding_cache = {}  # Cache embeddings for performance
    
    def match(
        self,
        utterance_text: str,
        behavior_description: str,
        behavior_phrases: Optional[List[str]] = None,
        embedding_service = None  # Will be injected
    ) -> Optional[Dict[str, Any]]:
        """
        Match utterance semantically against behavior
        
        Args:
            utterance_text: Agent utterance to check
            behavior_description: Behavior description
            behavior_phrases: Optional list of example phrases
            embedding_service: Service to get embeddings
        
        Returns:
            Match result with confidence, or None
        """
        if not embedding_service:
            logger.warning("Embedding service not provided, semantic matching disabled")
            return None
        
        try:
            # Create behavior semantic representation
            behavior_semantic = self._get_behavior_embedding(
                behavior_description,
                behavior_phrases,
                embedding_service
            )
            
            # Get utterance embedding
            utterance_embedding = self._get_utterance_embedding(
                utterance_text,
                embedding_service
            )
            
            if behavior_semantic is None or utterance_embedding is None:
                return None
            
            # Calculate cosine similarity
            similarity = cosine_similarity(
                [behavior_semantic],
                [utterance_embedding]
            )[0][0]
            
            if similarity >= self.similarity_threshold:
                # Ensure matched_text is a string
                matched_text = utterance_text
                if isinstance(matched_text, (list, tuple)):
                    matched_text = " ".join(str(item) for item in matched_text)
                elif not isinstance(matched_text, str):
                    matched_text = str(matched_text) if matched_text is not None else ""
                
                return {
                    "detected": True,
                    "match_type": "semantic",
                    "confidence": float(similarity),
                    "matched_text": matched_text,
                    "similarity_score": float(similarity)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Semantic matching failed: {e}", exc_info=True)
            return None
    
    def _get_behavior_embedding(
        self,
        description: str,
        phrases: Optional[List[str]],
        embedding_service
    ) -> Optional[np.ndarray]:
        """Get embedding for behavior"""
        # Combine description and phrases
        text = description
        if phrases:
            text += " " + " ".join(phrases)
        
        cache_key = f"behavior:{hash(text)}"
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        try:
            embedding = embedding_service.get_embedding(text)
            self.embedding_cache[cache_key] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Failed to get behavior embedding: {e}")
            return None
    
    def _get_utterance_embedding(
        self,
        utterance: str,
        embedding_service
    ) -> Optional[np.ndarray]:
        """Get embedding for utterance"""
        # Handle cases where utterance might be a list, tuple, or other non-string type
        if isinstance(utterance, (list, tuple)):
            # Join list/tuple elements with spaces
            utterance_str = " ".join(str(item) for item in utterance)
        elif not isinstance(utterance, str):
            # Convert other types to string
            utterance_str = str(utterance) if utterance is not None else ""
        else:
            utterance_str = utterance
        
        # Create cache key from string representation
        cache_key = f"utterance:{hash(utterance_str)}"
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        try:
            embedding = embedding_service.get_embedding(utterance_str)
            self.embedding_cache[cache_key] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Failed to get utterance embedding: {e}")
            return None

