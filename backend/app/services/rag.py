"""
Lightweight RAG (Retrieval-Augmented Generation) service using text-based similarity.
No numpy/sklearn dependencies - uses pure Python for keyword extraction and text matching.
"""
import logging
from typing import List, Dict, Any, Optional
import re
from collections import Counter

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. RAG service will use keyword-based matching only.")

# Import settings separately (always available)
from app.config import settings


class RAGService:
    """
    RAG service for retrieving relevant policy snippets based on transcript context.
    Uses keyword-based text similarity matching with optional Gemini embeddings fallback.
    """
    
    def __init__(self):
        self.use_embeddings = False
        if GEMINI_AVAILABLE and settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                # Try to use embeddings if available
                # Note: Gemini embeddings may not be available in all regions/versions
                self.use_embeddings = True
                logger.info("RAG service initialized with Gemini embeddings support")
            except Exception as e:
                logger.warning(f"Gemini embeddings not available, using keyword-based matching: {e}")
                self.use_embeddings = False
        else:
            logger.info("RAG service initialized with keyword-based matching only")
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> set:
        """
        Extract keywords from text using simple word frequency analysis.
        
        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            Set of keywords (normalized to lowercase)
        """
        # Remove punctuation and convert to lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Split into words
        words = text.split()
        
        # Common stop words to filter out
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me',
            'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our',
            'their', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when',
            'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'just', 'now'
        }
        
        # Filter out stop words and short words
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Count word frequency
        word_freq = Counter(keywords)
        
        # Get top keywords
        top_keywords = [word for word, _ in word_freq.most_common(max_keywords)]
        
        return set(top_keywords)
    
    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """
        Calculate Jaccard similarity between two sets.
        
        Args:
            set1: First set
            set2: Second set
            
        Returns:
            Jaccard similarity score (0-1)
        """
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding vector for text using Gemini embeddings API (if available).
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector, or None if unavailable
        """
        if not self.use_embeddings:
            return None
        
        try:
            # Try Gemini embeddings API
            # Note: This may not be available in all Gemini API versions
            result = genai.embed_content(
                model='models/embedding-001',
                content=text[:8000],  # Limit text length
                task_type='retrieval_document'
            )
            return result.get('embedding')
        except Exception as e:
            logger.debug(f"Embeddings not available, using keyword matching: {e}")
            return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors using pure Python.
        No numpy/sklearn dependencies.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        if len(vec1) != len(vec2):
            return 0.0
        
        # Dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Magnitudes
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(a * a for a in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Cosine similarity
        return dot_product / (magnitude1 * magnitude2)
    
